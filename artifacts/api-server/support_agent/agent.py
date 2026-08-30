"""Bounded Support Agent: knowledge + this-user tools → answer or human handoff."""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

from support_agent.escalation import (
    handoff_reply,
    out_of_scope_reply,
    redirect_ask_reply,
    off_app_reply,
)
from support_agent.intent import (
    classify_relation,
    is_ai_product_ask,
    is_ask_tab_question,
    is_off_app_question,
    last_user_and_bot,
    not_ai_engine_reply,
    reply_lang,
    reply_overlaps_previous_bot,
)
from support_agent.knowledge import load_knowledge
from support_agent.response_guard import guard
from support_agent.retrieve import clear_index_cache, format_retrieved, retrieve_chunks
from support_agent.system_prompt import SYSTEM_PROMPT
from support_agent.tools import snapshot

log = logging.getLogger("support_agent")

# Admin / analytics / other-customers — never answer from knowledge (LLM often drifts).
_INTERNAL_ASK = re.compile(
    r"(?i)("
    r"\binternal\b|"
    r"how\s+many\s+(clients?|users?|customers?|people|buyers?)|"
    r"(clients?|users?|customers?)\s+(buy|bought|purchased|buyed)|"
    r"(buy|bought|buyed|purchase|order).{0,40}(today|aaj)|"
    r"sales\s+(today|data|report|count)|orders?\s+today|"
    r"revenue|admin\s+(panel|login|mpin|token|unlock)|other\s+users?|all\s+users?|"
    r"database|system\s+prompt|api[\s_-]?keys?|server\s+logs?|"
    r"kitne\s+(clients?|users?|log|logon|ne kharid)|"
    r"aaj\s+kitne|total\s+(sales|orders|customers)|"
    r"give\s+me\s+internal|show\s+me\s+(admin|sales|stats)|"
    r"source\s+code|gunicorn|nginx|\bpm2\b|\bvps\b|\.env\b|"
    r"openai|which\s+model|model\s+name|gpt-|"
    r"firebase\s+(key|secret|service)|service.?account|"
    r"how\s+(do\s+you|we|does\s+the\s+app)\s+calculate|"
    r"engine\s+(code|formula|internals)|prompt\s+injection|"
    r"enroll.?code|admin.?secret"
    r")"
)

_DEVANAGARI = re.compile(r"[\u0900-\u097f]")

_HARD_ESCALATE = re.compile(
    r"(?i)\b(refund|chargeback|fraud|legal|lawyer|screenshot|"
    r"paid.*(missing|nahi)|money\s+cut|payment\s+failed)\b"
)

_PRICE_ASK = re.compile(
    r"(?i)\b(price|pricing|prices|cost|costly|charge|fee|rate|kitne|kitna|kitni|"
    r"sasta|sasti|cheapest|mehnga|mehngi|rupee|rs\.?|inr|padta|padega)\b|₹"
)


def is_internal_or_admin_ask(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    return bool(_INTERNAL_ASK.search(t))


def _pick_price_line(body: str, question: str) -> str:
    """Prefer the sentence/line that answers the asked duration or product price."""
    q = (question or "").lower()
    lines = [ln.strip() for ln in (body or "").splitlines() if ln.strip() and "₹" in ln]
    if not lines:
        return ""
    prefer: list[str] = []
    if re.search(r"(?i)\b(15\s*min|15\s*minute)", q):
        prefer = [ln for ln in lines if re.search(r"15\s*min|15\s*minute", ln, re.I)]
    elif re.search(r"(?i)\b(half\s*(an?\s*)?hour|30\s*min)", q):
        prefer = [ln for ln in lines if re.search(r"half|30\s*min", ln, re.I)]
    elif re.search(r"(?i)\b(1\s*hour|one\s*hour|60\s*min|poora\s*1)", q):
        prefer = [ln for ln in lines if re.search(r"60\s*min|1\s*hour|one\s*hour", ln, re.I)]
    elif re.search(r"(?i)\b(sasta|cheapest|starter)\b", q):
        prefer = [ln for ln in lines if re.search(r"starter|sasta|cheapest|₹49", ln, re.I)]
    elif re.search(r"(?i)\bpopular\b", q):
        prefer = [ln for ln in lines if re.search(r"popular|₹99", ln, re.I)]
    elif re.search(r"(?i)\bpower\b", q):
        prefer = [ln for ln in lines if re.search(r"power|₹299", ln, re.I)]
    elif re.search(r"(?i)\bshop\b", q) and re.search(r"(?i)vastu", q):
        prefer = [ln for ln in lines if re.search(r"shop", ln, re.I)]
    elif re.search(r"(?i)\bpalm", q):
        prefer = [ln for ln in lines if re.search(r"1499|palm", ln, re.I)]
    elif re.search(r"(?i)\brectif", q):
        prefer = [ln for ln in lines if re.search(r"999|rectif", ln, re.I)]
    elif re.search(r"(?i)\b(video)\b", q) and re.search(r"(?i)\b(milan|love|numerology|palm)", q):
        prefer = [ln for ln in lines if re.search(r"video", ln, re.I)]
    chosen = prefer[0] if prefer else lines[0]
    return re.sub(r"\s+", " ", chosen).strip()


def _short_from_chunks(chunks: list[Any], question: str = "") -> str:
    """1–2 line product answer from retrieved knowledge — no per-topic hardcoding."""
    if not chunks:
        return ""
    pay_q = bool(
        re.search(
            r"(?i)\b(wallet|transaction|payment|refund|pack|credit|paid|order)\b",
            question or "",
        )
    )
    price_q = bool(_PRICE_ASK.search(question or ""))
    ordered = list(chunks)
    if not pay_q:
        non_pay = [
            c
            for c in chunks
            if not str(getattr(c, "source", "")).endswith("payments.md")
        ]
        if non_pay:
            ordered = non_pay
    if price_q:
        priced = [
            c
            for c in ordered
            if "₹" in str(getattr(c, "text", "") or "")
            or "price" in str(getattr(c, "title", "") or "").lower()
        ]
        if priced:
            priced.sort(
                key=lambda c: (
                    0 if "price" in str(getattr(c, "title", "") or "").lower() else 1,
                    0 if "₹" in str(getattr(c, "text", "") or "") else 1,
                )
            )
            ordered = priced

    top = ordered[0]
    body = str(getattr(top, "text", "") or "").strip()
    if not body:
        return ""
    if price_q:
        price_line = _pick_price_line(body, question)
        if price_line:
            return price_line[:320].strip()
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if len(lines) >= 2 and len(lines[0]) < 80:
        body = " ".join(lines[1:])
    else:
        body = " ".join(lines)
    body = re.sub(r"\s+", " ", body).strip()
    parts = re.split(r"(?<=[.。!?।])\s+", body)
    short = " ".join(p for p in parts[:2] if p).strip()
    if len(short) < 48:
        short = body
    return short[:320].strip()


def _model() -> str:
    name = (os.environ.get("SUPPORT_AI_MODEL") or "").strip()
    if name and name.lower() not in ("gpt-4.1-nano", "gpt-3.5-turbo-instruct"):
        return name
    return "gpt-4.1-mini"


def _as_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    return str(val or "").strip().lower() in ("1", "true", "yes")


def _parse_llm_text(raw: str) -> dict[str, Any] | None:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", (raw or "").strip(), flags=re.I).strip()
    if not text:
        return None
    data: Any = None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError:
                data = None
    if isinstance(data, dict):
        reply = str(data.get("reply") or "").strip()[:1200]
        if reply:
            rel = str(data.get("relation") or data.get("kind") or "").strip().lower()
            if rel not in ("follow_up", "new"):
                rel = "new"
            return {
                "escalate": _as_bool(data.get("escalate")),
                "reply": reply,
                "relation": rel,
                "source": "llm",
            }
    # Non-JSON prose is not a valid Cosmic Help answer
    return None


def _llm(
    text: str,
    lang: str,
    history: list[dict[str, Any]],
    tool_text: str,
    retrieved: str,
    *,
    has_image: bool,
) -> dict[str, Any] | None:
    try:
        from openai_helper import _get_client
    except Exception:
        log.warning("[support_agent] openai_helper import failed")
        return None
    client = _get_client()
    if client is None:
        log.warning("[support_agent] OpenAI client missing")
        return None
    lang_name = "English" if reply_lang(lang) == "en" else "Hinglish (Roman script, not Hindi Devanagari)"
    hist_lines: list[str] = []
    for m in history[-6:]:
        if not isinstance(m, dict):
            continue
        who = str(m.get("sender") or "")
        if who not in ("user", "bot", "admin"):
            continue
        body = str(m.get("text") or "").strip()
        if body:
            hist_lines.append(f"{who}: {body[:180]}")
    extra = "User attached a screenshot. Escalate.\n" if has_image else ""
    retrieved_block = retrieved.strip() or "(none — do not invent product facts; escalate if tools do not answer)"
    prompt = (
        f"{extra}"
        f"Reply language: {lang_name}. Never use Hindi Devanagari.\n"
        "JSON only: "
        '{"relation":"follow_up"|"new","escalate":false,"reply":"..."}\n\n'
        "STEP 1: Set relation (follow_up|new).\n"
        "STEP 2: Answer ONLY from RETRIEVED KNOWLEDGE + TOOL RESULTS. "
        "Default reply length: 1–2 short lines. Longer only if user asked for details.\n"
        "If retrieved knowledge is (none) and tools do not answer → escalate=true.\n"
        "Never invent prices/features. Chat history is not product truth.\n\n"
        f"RETRIEVED KNOWLEDGE CHUNKS:\n{retrieved_block}\n\n"
        f"TOOL RESULTS (this customer only):\n{tool_text}\n\n"
        f"RECENT CHAT:\n" + ("\n".join(hist_lines) or "(none)") + "\n\n"
        f"USER (latest):\n{(text or '')[:800]}"
    )
    timeout_s = min(12.0, max(6.0, float(os.environ.get("SUPPORT_AI_TIMEOUT") or "10")))
    model = _model()
    t0 = time.monotonic()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=160,
            temperature=0.1,
            timeout=timeout_s,
        )
        raw = (resp.choices[0].message.content or "").strip()
        ms = int((time.monotonic() - t0) * 1000)
        parsed = _parse_llm_text(raw)
        log.info(
            "[support_agent] openai ok model=%s ms=%s id=%s chars=%s relation=%s retrieved=%s",
            model,
            ms,
            getattr(resp, "id", "") or "",
            len(raw),
            (parsed or {}).get("relation") or "",
            len(retrieved_block),
        )
        return parsed
    except Exception as exc:
        ms = int((time.monotonic() - t0) * 1000)
        log.warning("[support_agent] llm failed model=%s ms=%s: %s", model, ms, exc)
        return None


def run(
    text: str,
    *,
    lang: str | None = None,
    has_image: bool = False,
    history: list[dict[str, Any]] | None = None,
    user: Any = None,
    account_card: str = "",
    cosmo_user_id: str = "",
) -> dict[str, Any]:
    """Tools first, then knowledge, then answer or escalate. Never guess account facts."""
    from support_agent.intent import detect_lang

    history = history if isinstance(history, list) else []
    L = reply_lang(detect_lang(text, lang))

    tools = snapshot(user)
    tool_text = str(tools.get("text") or "")
    if (account_card or "").strip():
        tool_text = f"{tool_text}\nACCOUNT_CARD:\n{account_card.strip()[:1200]}"

    if has_image:
        reply, _ = guard(handoff_reply(L), L)
        return {
            "escalate": True,
            "reply": reply,
            "source": "screenshot",
            "relation": "new",
            "agent_state": "waiting_for_human",
            "tools": tools,
        }

    if is_ai_product_ask(text):
        reply, _ = guard(not_ai_engine_reply(text, L), L, text)
        return {
            "escalate": False,
            "reply": reply,
            "source": "not_ai_engine",
            "relation": "new",
            "agent_state": "answered",
            "tools": tools,
        }

    if is_internal_or_admin_ask(text):
        reply, _ = guard(out_of_scope_reply(L), L, text)
        return {
            "escalate": True,
            "reply": reply,
            "source": "internal_refuse",
            "relation": "new",
            "agent_state": "waiting_for_human",
            "tools": tools,
        }

    if is_off_app_question(text):
        reply, _ = guard(off_app_reply(L), L, text)
        return {
            "escalate": False,
            "reply": reply,
            "source": "off_app",
            "relation": "new",
            "agent_state": "answered",
            "tools": tools,
        }

    if is_ask_tab_question(text):
        reply, _ = guard(redirect_ask_reply(L), L, text)
        return {
            "escalate": False,
            "reply": reply,
            "source": "redirect_ask",
            "relation": "new",
            "agent_state": "answered",
            "tools": tools,
        }

    forced_relation = classify_relation(text, history)
    prev_user, prev_bot = last_user_and_bot(history)

    # Retrieve only relevant chunks (follow-ups include prior topic terms)
    retrieve_q = text
    if forced_relation == "follow_up" and prev_user:
        retrieve_q = f"{prev_user}\n{text}"
    chunks = retrieve_chunks(retrieve_q, top_k=5, max_chars=2200)
    retrieved = format_retrieved(chunks)
    log.info(
        "[support_agent] retrieve q_chars=%s chunks=%s sources=%s",
        len(retrieve_q),
        len(chunks),
        ",".join(sorted({c.source for c in chunks})) if chunks else "-",
    )

    # No verified product chunks and not clearly an account-tool question → escalate.
    # Do not use TOOL FAILED here: snapshot(None) always marks txs/reports failed,
    # which would incorrectly force the LLM path for nonsense product questions.
    accountish = bool(
        re.search(
            r"(?i)\b(cosmo|transaction|transactions|my report|my reports|"
            r"pack left|credits? left|subscription|plan|paid|payment|order|"
            r"wallet)\b",
            text or "",
        )
    )
    if not chunks and not accountish:
        msg = (
            "Verified information for that isn’t in Cosmic Help yet. A team member will join shortly."
            if L == "en"
            else "Is sawaal ki verified info Cosmic Help me nahi mili. Team member jaldi join karega."
        )
        reply, _ = guard(msg, L, text)
        return {
            "escalate": True,
            "reply": reply,
            "source": "no_retrieval",
            "relation": forced_relation,
            "agent_state": "waiting_for_human",
            "tools": tools,
            "retrieved_sources": [],
        }

    def _kb_answer() -> dict[str, Any] | None:
        short = _short_from_chunks(chunks, text)
        if not short:
            return None
        reply, leaked = guard(short, L, text)
        if leaked or not reply.strip():
            return None
        return {
            "escalate": False,
            "reply": reply,
            "source": "knowledge_retrieve",
            "relation": forced_relation,
            "agent_state": "answered",
            "tools": tools,
            "retrieved_sources": [c.source for c in chunks],
        }

    llm = _llm(text, L, history, tool_text, retrieved, has_image=False)
    if llm:
        relation = str(llm.get("relation") or forced_relation)
        if forced_relation == "new" and relation == "follow_up":
            relation = "new"
        if forced_relation == "follow_up":
            relation = "follow_up"

        reply, leaked = guard(str(llm.get("reply") or ""), L, text)
        if _DEVANAGARI.search(reply or ""):
            kb = _kb_answer()
            if kb:
                return kb
            reply = (
                "I can answer in English or Hinglish only. Ask again in English or Hinglish."
                if L == "en"
                else "Main English ya Hinglish me hi jawab deta hoon. English ya Hinglish me dobara likho."
            )
            leaked = False
        escalate = _as_bool(llm.get("escalate")) or leaked
        if leaked:
            reply, _ = guard(handoff_reply(L), L, text)
            escalate = True
        elif reply_overlaps_previous_bot(reply, prev_bot, relation=relation):
            reply, _ = guard(
                "That looks like a new question. Tell me the app issue again in one short line "
                "(payment, PDF, price, or how-to) — I won’t repeat the previous topic."
                if L == "en"
                else "Yeh naya sawaal lagta hai. Ek short line mein issue batao "
                "(payment, PDF, price, ya how-to) — pehle wala topic dobara nahi dunga.",
                L,
                text,
            )
            escalate = False
            relation = "new"
        # Product how-to with verified chunks: don't escalate away if LLM flaked
        if (
            escalate
            and chunks
            and not accountish
            and not _HARD_ESCALATE.search(text or "")
        ):
            kb = _kb_answer()
            if kb:
                return kb
        return {
            "escalate": escalate,
            "reply": reply,
            "source": "llm",
            "relation": relation,
            "agent_state": "waiting_for_human" if escalate else "answered",
            "tools": tools,
            "retrieved_sources": [c.source for c in chunks],
        }

    # LLM down — still answer from retrieved knowledge (scalable, no per-topic hacks)
    if chunks and not _HARD_ESCALATE.search(text or ""):
        kb = _kb_answer()
        if kb:
            return kb

    reply, _ = guard(handoff_reply(L), L, text)
    return {
        "escalate": True,
        "reply": reply,
        "source": "ai_unavailable",
        "relation": forced_relation,
        "agent_state": "waiting_for_human",
        "tools": tools,
        "retrieved_sources": [c.source for c in chunks],
    }


def load_rules() -> str:
    clear_index_cache()
    return load_knowledge()


def apply_check_delay(*_a, **_k) -> None:
    return None


def check_seconds() -> float:
    return 0.0

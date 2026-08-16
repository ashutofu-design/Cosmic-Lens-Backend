"""Bounded Support Agent — scope check, allowed knowledge, narrow tools, guard, handoff."""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from support_agent.escalation import (
    handoff_reply,
    help_first_reply,
    off_app_reply,
    out_of_scope_reply,
    redirect_ask_reply,
)
from support_agent.intent import (
    ASK_HUMAN,
    IN_SCOPE,
    MUST_HANDOFF,
    OFF_APP,
    OUT_OF_SCOPE,
    REDIRECT_ASK,
    classify,
    detect_lang,
)
from support_agent.knowledge import ALLOWED_KNOWLEDGE, lookup_knowledge
from support_agent.response_guard import guard
from support_agent.system_prompt import SYSTEM_PROMPT
from support_agent.tools import customer_facts, format_transactions
from support_agent.understand import normalize, topic

log = logging.getLogger("support_agent")

_ACCOUNT_Q = re.compile(
    r"(wallet|transaction|payment|order).{0,50}(not showing|isn'?t showing|missing|not\s+in)|"
    r"(not showing|missing|nahi\s*dikh).{0,40}(wallet|transaction|payment|order)|"
    r"done\s+(a\s+|one\s+)?transaction|"
    r"payment\s*(fail|failed|failure)|pay\s*fail",
    re.I,
)


def _llm(
    text: str,
    lang: str,
    history: list[dict[str, Any]],
    account_card: str,
    *,
    category: str,
    normalized: str,
) -> dict[str, Any] | None:
    try:
        from openai_helper import _get_client
    except Exception:
        return None
    client = _get_client()
    if client is None:
        return None
    lang_name = {"en": "English", "hi": "Hindi (Devanagari)", "hn": "Hinglish"}[lang]
    hist_lines: list[str] = []
    for m in history[-6:]:
        if not isinstance(m, dict):
            continue
        who = str(m.get("sender") or "")
        if who not in ("user", "bot", "admin"):
            continue
        body = str(m.get("text") or "").strip()
        if body:
            hist_lines.append(f"{who}: {body[:240]}")
    prompt = (
        f"User language: {lang_name}. Reply in that language only.\n"
        "JSON only: {\"escalate\": true|false, \"reply\": \"...\"}\n"
        f"CATEGORY: {category}\n"
        "Understand the question first (typos ok), then answer that category from knowledge.\n\n"
        f"ALLOWED KNOWLEDGE:\n{ALLOWED_KNOWLEDGE}\n\n"
        f"THIS CUSTOMER ACCOUNT:\n{(account_card or '').strip() or '(none)'}\n\n"
        f"RECENT CHAT:\n" + ("\n".join(hist_lines) or "(none)") + "\n\n"
        f"USER (original): {(text or '')[:1200]}\n"
        f"USER (normalized): {(normalized or text or '')[:1200]}"
    )
    model = (os.environ.get("SUPPORT_AI_MODEL") or "gpt-4.1-nano").strip()
    timeout_s = min(10.0, max(4.0, float(os.environ.get("SUPPORT_AI_TIMEOUT") or "8")))
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=180,
            temperature=0.1,
            timeout=timeout_s,
        )
        raw = (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        log.warning("[support_agent] llm failed: %s", exc)
        return None
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    if not isinstance(data, dict):
        return None
    reply = str(data.get("reply") or "").strip()[:1200]
    if not reply:
        return None
    return {"escalate": bool(data.get("escalate")), "reply": reply, "source": "llm"}


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
    """Understand → category → allowed knowledge/tools → guard."""
    history = history if isinstance(history, list) else []
    cleaned = normalize(text)
    L = detect_lang(cleaned or text, lang)
    kind = classify(cleaned or text, has_image=has_image, history=history)
    category = topic(cleaned or text)

    if kind == OUT_OF_SCOPE:
        reply, _ = guard(out_of_scope_reply(L), L)
        return {"escalate": False, "reply": reply, "source": "out_of_scope", "intent": kind}

    if kind == OFF_APP:
        reply, _ = guard(off_app_reply(L), L)
        return {"escalate": False, "reply": reply, "source": "off_app", "intent": kind}

    if kind == MUST_HANDOFF:
        reply, _ = guard(handoff_reply(L), L)
        return {"escalate": True, "reply": reply, "source": "handoff", "intent": kind}

    if kind == ASK_HUMAN:
        reply, _ = guard(help_first_reply(L), L)
        return {"escalate": False, "reply": reply, "source": "help_first", "intent": kind}

    if kind == REDIRECT_ASK:
        reply, _ = guard(redirect_ask_reply(L), L)
        return {"escalate": False, "reply": reply, "source": "redirect_ask", "intent": kind}

    facts = customer_facts(user, account_card, cosmo_user_id)
    card = str(facts.get("card") or account_card or "")
    if facts.get("cosmo") and not card:
        card = f"User ID: {facts.get('cosmo')}"

    if category == "payment" and _ACCOUNT_Q.search(cleaned or text or ""):
        body = format_transactions(facts, L)
        reply, leaked = guard(body, L)
        return {
            "escalate": True,
            "reply": reply,
            "source": "tool_transactions",
            "intent": kind,
        }

    llm = _llm(text, L, history, card, category=category, normalized=cleaned)
    if llm:
        reply, leaked = guard(str(llm.get("reply") or ""), L)
        esc = bool(llm.get("escalate")) or leaked
        return {
            "escalate": esc,
            "reply": reply,
            "source": "llm",
            "intent": kind,
            "category": category,
        }

    hit = lookup_knowledge(cleaned or text, L)
    if hit:
        body = str(hit["reply"])
        cid = str(facts.get("cosmo") or cosmo_user_id or "").strip()
        if cid and category == "identity":
            if L == "en":
                body = f"Your User ID on Profile is {cid}. It is assigned at signup and cannot be changed."
            else:
                body = f"Aapka User ID Profile pe {cid} hai. Signup pe milta hai, change nahi hota."
        reply, leaked = guard(body, L)
        return {
            "escalate": False,
            "reply": reply,
            "source": hit.get("source") or "knowledge",
            "intent": kind,
            "category": category,
        }

    reply, _ = guard(handoff_reply(L), L)
    return {
        "escalate": True,
        "reply": reply,
        "source": "unsolved",
        "intent": kind,
        "category": category,
    }


# Back-compat for older imports
def load_rules() -> str:
    return ALLOWED_KNOWLEDGE


def apply_check_delay(*_a, **_k) -> None:
    return None


def check_seconds() -> float:
    return 0.0

"""Bounded Support Agent: knowledge + this-user tools → answer or human handoff."""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from support_agent.escalation import handoff_reply
from support_agent.knowledge import ALLOWED_KNOWLEDGE, load_knowledge
from support_agent.response_guard import guard
from support_agent.system_prompt import SYSTEM_PROMPT
from support_agent.tools import snapshot

log = logging.getLogger("support_agent")


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
            return {
                "escalate": _as_bool(data.get("escalate")),
                "reply": reply,
                "source": "llm",
            }
    if len(text) >= 12:
        return {"escalate": False, "reply": text[:1200], "source": "llm"}
    return None


def _llm(
    text: str,
    lang: str,
    history: list[dict[str, Any]],
    tool_text: str,
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
    lang_name = {"en": "English", "hi": "Hindi (Devanagari)", "hn": "Hinglish"}.get(
        lang, "Hinglish"
    )
    hist_lines: list[str] = []
    for m in history[-8:]:
        if not isinstance(m, dict):
            continue
        who = str(m.get("sender") or "")
        if who not in ("user", "bot", "admin"):
            continue
        body = str(m.get("text") or "").strip()
        if body:
            hist_lines.append(f"{who}: {body[:240]}")
    extra = "User attached a screenshot. Escalate.\n" if has_image else ""
    prompt = (
        f"{extra}"
        f"Reply language: {lang_name}.\n"
        "JSON only: {\"escalate\": false, \"reply\": \"...\"}\n"
        "Use TOOL RESULTS for this account. Do not invent orders. "
        "If a tool failed and they asked about that topic, escalate=true.\n\n"
        f"ALLOWED KNOWLEDGE:\n{ALLOWED_KNOWLEDGE}\n\n"
        f"TOOL RESULTS (this customer only):\n{tool_text}\n\n"
        f"RECENT CHAT:\n" + ("\n".join(hist_lines) or "(none)") + "\n\n"
        f"USER: {(text or '')[:1200]}"
    )
    timeout_s = min(12.0, max(6.0, float(os.environ.get("SUPPORT_AI_TIMEOUT") or "10")))
    model = _model()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=280,
            temperature=0.2,
            timeout=timeout_s,
        )
        raw = (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        log.warning("[support_agent] llm failed model=%s: %s", model, exc)
        return None
    return _parse_llm_text(raw)


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
    history = history if isinstance(history, list) else []
    L = (lang or "").strip().lower()
    if L not in ("en", "hn", "hi"):
        L = "en" if (text or "")[:1].isascii() else "hn"

    tools = snapshot(user)
    if has_image:
        reply, _ = guard(handoff_reply(L), L)
        return {
            "escalate": True,
            "reply": reply,
            "source": "screenshot",
            "agent_state": "waiting_for_human",
            "tools": tools,
        }

    llm = _llm(text, L, history, str(tools.get("text") or ""), has_image=False)
    if llm:
        reply, leaked = guard(str(llm.get("reply") or ""), L)
        escalate = bool(llm.get("escalate")) or leaked
        if leaked:
            reply, _ = guard(handoff_reply(L), L)
            escalate = True
        return {
            "escalate": escalate,
            "reply": reply,
            "source": "llm",
            "agent_state": "waiting_for_human" if escalate else "answered",
            "tools": tools,
        }

    reply, _ = guard(handoff_reply(L), L)
    return {
        "escalate": True,
        "reply": reply,
        "source": "ai_unavailable",
        "agent_state": "waiting_for_human",
        "tools": tools,
    }


def load_rules() -> str:
    return load_knowledge() or ALLOWED_KNOWLEDGE


def apply_check_delay(*_a, **_k) -> None:
    return None


def check_seconds() -> float:
    return 0.0

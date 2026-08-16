"""Support Agent — the model understands the question and answers from allowed knowledge."""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from support_agent.escalation import handoff_reply
from support_agent.knowledge import ALLOWED_KNOWLEDGE
from support_agent.response_guard import guard
from support_agent.system_prompt import SYSTEM_PROMPT
from support_agent.tools import customer_facts

log = logging.getLogger("support_agent")


def _models() -> list[str]:
    out: list[str] = []
    for raw in (
        os.environ.get("SUPPORT_AI_MODEL"),
        os.environ.get("OPENAI_MODEL"),
        "gpt-4.1-mini",
        "gpt-4o-mini",
    ):
        name = (raw or "").strip()
        if name and name not in out:
            out.append(name)
    return out or ["gpt-4.1-mini"]


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
                "escalate": bool(data.get("escalate")),
                "reply": reply,
                "source": "llm",
            }
    # Model answered in plain text — still use it.
    if len(text) >= 12:
        return {"escalate": False, "reply": text[:1200], "source": "llm"}
    return None


def _llm(
    text: str,
    lang: str,
    history: list[dict[str, Any]],
    account_card: str,
    *,
    has_image: bool,
) -> dict[str, Any] | None:
    try:
        from openai_helper import _get_client
    except Exception:
        return None
    client = _get_client()
    if client is None:
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
    extra = "User attached a screenshot.\n" if has_image else ""
    prompt = (
        f"{extra}"
        f"Reply language: {lang_name} (match the user).\n"
        "JSON only: {\"escalate\": true|false, \"reply\": \"...\"}\n\n"
        f"ALLOWED KNOWLEDGE:\n{ALLOWED_KNOWLEDGE}\n\n"
        f"THIS CUSTOMER ACCOUNT:\n{(account_card or '').strip() or '(none)'}\n\n"
        f"RECENT CHAT:\n" + ("\n".join(hist_lines) or "(none)") + "\n\n"
        f"USER: {(text or '')[:1200]}"
    )
    timeout_s = min(12.0, max(4.0, float(os.environ.get("SUPPORT_AI_TIMEOUT") or "8")))
    last_err: Exception | None = None
    for model in _models():
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 280,
            "temperature": 0.2,
            "timeout": timeout_s,
        }
        try:
            resp = client.chat.completions.create(
                **kwargs,
                response_format={"type": "json_object"},
            )
        except Exception:
            try:
                resp = client.chat.completions.create(**kwargs)
            except Exception as exc:
                last_err = exc
                log.warning("[support_agent] llm failed model=%s: %s", model, exc)
                continue
        raw = (resp.choices[0].message.content or "").strip()
        parsed = _parse_llm_text(raw)
        if parsed:
            return parsed
    if last_err:
        log.warning("[support_agent] llm unavailable: %s", last_err)
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
    """AI reads the question, then answers from allowed knowledge + this account."""
    history = history if isinstance(history, list) else []
    L = (lang or "").strip().lower()
    if L not in ("en", "hn", "hi"):
        L = "en" if (text or "")[:1].isascii() else "hn"
    facts = customer_facts(user, account_card, cosmo_user_id)
    card = str(facts.get("card") or account_card or "")
    cid = str(facts.get("cosmo") or cosmo_user_id or "").strip()
    if cid and "User ID" not in card:
        card = f"User ID: {cid}\n{card}".strip()

    llm = _llm(text, L, history, card, has_image=has_image)
    if llm:
        reply, leaked = guard(str(llm.get("reply") or ""), L)
        return {
            "escalate": bool(llm.get("escalate")) or leaked,
            "reply": reply,
            "source": "llm",
        }

    reply, _ = guard(handoff_reply(L), L)
    return {"escalate": True, "reply": reply, "source": "ai_unavailable"}


def load_rules() -> str:
    return ALLOWED_KNOWLEDGE


def apply_check_delay(*_a, **_k) -> None:
    return None


def check_seconds() -> float:
    return 0.0

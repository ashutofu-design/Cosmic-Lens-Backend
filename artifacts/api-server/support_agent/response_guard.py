"""Strip anything that must never reach the customer."""
from __future__ import annotations

import re

from support_agent.escalation import handoff_reply

_LEAK = re.compile(
    r"(api[_-]?key|openai|gpt-4|gpt-3|SUPPORT_AI|OPENAI_|TELEGRAM_|FOUNDER_|"
    r"\bpm2\b|\bvps\b|flask_app|\.env\b|postgres|sqlalchemy|webhook|"
    r"admin\s*(panel|token|key)|thread_id|support_threads|razorpay.?secret|"
    r"cashfree.?secret|localhost:\d+|127\.0\.0\.1|"
    r"system\s*prompt|calculation\s*code|numerology\s*engine|"
    r"telegram|database\s+(id|dump)|prompt\s+injection)",
    re.I,
)

_POLITE_OK = re.compile(
    r"^(ji[, ]|sure\b|happy to help|of course|please\b|namaste|"
    r"sorry|bilkul|zaroor|thank)",
    re.I,
)


def polite(reply: str, lang: str) -> str:
    r = (reply or "").strip()
    if not r:
        return r
    if lang == "en":
        r = re.sub(r"^Ji,\s*", "", r, flags=re.I).strip()
        if _POLITE_OK.match(r) and not re.match(r"^ji[, ]", r, re.I):
            return r
        return f"Happy to help. {r}"
    if _POLITE_OK.match(r):
        return r
    if lang == "hi":
        return f"जी, {r}"
    return f"Ji, {r}"


def guard(reply: str, lang: str) -> tuple[str, bool]:
    """Return (safe_reply, leaked). If leaked, replace with handoff text."""
    text = (reply or "").strip()
    if not text:
        return polite(handoff_reply(lang), lang), True
    if _LEAK.search(text):
        return polite(handoff_reply(lang), lang), True
    return polite(text, lang), False

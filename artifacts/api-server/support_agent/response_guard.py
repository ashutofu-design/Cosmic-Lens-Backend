"""Strip anything that must never reach the customer."""
from __future__ import annotations

import re

from support_agent.escalation import handoff_reply

# Do not match the word "AI" / "OpenAI" — customers ask if a Pro PDF is AI-generated.
_LEAK = re.compile(
    r"(api[_-]?key|TELEGRAM_|FOUNDER_|"
    r"\bpm2\b|\bvps\b|flask_app|\.env\b|postgres|sqlalchemy|webhook|"
    r"admin\s*(panel|token|key|secret|mpin)|thread_id|support_threads|razorpay.?secret|"
    r"cashfree.?secret|localhost:\d+|127\.0\.0\.1|"
    r"system\s*prompt|calculation\s*code|numerology\s*engine|"
    r"gunicorn|nginx|openai_helper|service.?account|"
    r"telegram|database\s+(id|dump)|prompt\s+injection)",
    re.I,
)

_PAYMENT_ASK = re.compile(
    r"\b(wallet|transaction|transactions|payment|paid|pay|refund|order|orders|"
    r"paise|paisa|credit|credits|pack|packs|kharid|payment)\b",
    re.I,
)

_HAPPY = re.compile(r"^Happy to help\.?\s*", re.I)
_JI = re.compile(r"^Ji,\s*", re.I)

# Canned block the model copies from knowledge/tools into unrelated answers.
_WALLET_BOILER = re.compile(
    r"(?:Happy to help\.?\s*)?"
    r"(?:Cosmic Lens (?:has no wallet|mein wallet nahi hota)[^.।]*[.।]\s*)"
    r"(?:Paid orders (?:show on|Help)[^.।]*Transactions[^.।]*[.।]\s*)?"
    r"(?:Ask credits[^.।]*(?:Cosmic Packs|Profile)[^.।]*[.।]\s*)?"
    r"(?:Pro PDFs?[^.।]*(?:My Reports|instant auto|expert)[^.।]*[.।]\s*)?",
    re.I,
)
_WALLET_BOILER_HI = re.compile(
    r"(?:जी,?\s*)?"
    r"(?:Cosmic Lens में वॉलेट नहीं होता[^.।]*[.।]\s*)"
    r"(?:पेड ऑर्डर[^.।]*ट्रांजैक्शन्स[^.।]*[.।]\s*)?"
    r"(?:Ask क्रेडिट[^.।]*पैक्स[^.।]*[.।]\s*)?"
    r"(?:प्रो PDF[^.।]*रिपोर्ट्स[^.।]*[.।]\s*)?",
    re.I,
)


def asked_about_payment(user_text: str) -> bool:
    return bool(_PAYMENT_ASK.search(user_text or ""))


def strip_unsolicited_wallet(reply: str, user_text: str = "") -> str:
    """Drop the wallet/Transactions canned intro unless they asked about money."""
    text = (reply or "").strip()
    if not text:
        return text
    text = _HAPPY.sub("", text).strip()
    if asked_about_payment(user_text):
        return text
    cleaned = _WALLET_BOILER.sub("", text)
    cleaned = _WALLET_BOILER_HI.sub("", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -,")
    # Never wipe a real product answer to empty (that becomes a fake handoff).
    if not cleaned and text:
        return text
    return cleaned


_MODEL_BRAND = re.compile(
    r"(?i)\b(chatgpt|chat\s*gpt|openai|gemini|\bllm\b|gpt-?\d+)\b"
)
_INSTANT_AI = re.compile(r"(?i)\binstant\s+AI\b")


def scrub_model_names(reply: str) -> str:
    """Never name ChatGPT / OpenAI / Gemini. Keep a clear 'not AI' deny if present."""
    t = _INSTANT_AI.sub("instant auto file", reply or "")
    return _MODEL_BRAND.sub("the special engine", t)


def polite(reply: str, lang: str) -> str:
    r = (reply or "").strip()
    if not r:
        return r
    r = _HAPPY.sub("", r).strip()
    if lang == "en":
        return _JI.sub("", r).strip()
    return r


def guard(reply: str, lang: str, user_text: str = "") -> tuple[str, bool]:
    """Return (safe_reply, leaked). If leaked, replace with handoff text."""
    text = (reply or "").strip()
    if not text:
        return polite(handoff_reply(lang), lang), True
    if _LEAK.search(text):
        return polite(handoff_reply(lang), lang), True
    cleaned = polite(scrub_model_names(strip_unsolicited_wallet(text, user_text)), lang)
    if not cleaned.strip():
        # Prefer original (minus Happy) over empty → wait-for-team spam
        cleaned = polite(_HAPPY.sub("", text).strip(), lang)
    return cleaned, False

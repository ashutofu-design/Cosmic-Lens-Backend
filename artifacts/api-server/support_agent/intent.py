"""Language + cheap intent gates for Cosmic Help (before / with LLM)."""
from __future__ import annotations

import re
from typing import Any

_FOLLOW_SHORT = re.compile(
    r"(?i)^(price|prices|cost|kitna|kitne|aur|and\??|uska|iski|uski|yeh|ye|"
    r"ok|okay|haan|han|yes|no|nahi|kya|what about|priority|pdf|video|"
    r"same|aur batao|phir|then)\b"
)
_FOLLOW_PRONOUN = re.compile(
    r"(?i)\b(uska|iski|uski|usko|iske|that|it|this|same|bhi|also)\b"
)
_ASK_KUNDLI = re.compile(
    r"(?i)\b("
    r"horoscope|rashifal|prediction|"
    r"meri\s+kundli\s+(batao|padho|dekho)|"
    r"read\s+my\s+(kundli|chart)|"
    r"what\s+does\s+my\s+(dasha|mahadasha)|"
    r"my\s+birth\s+chart\s+(mean|say)"
    r")\b"
)
_AI_WORD = re.compile(
    r"(?i)\b(ai|artificial\s+intelligence|chatgpt|chat\s*gpt|openai|gemini|"
    r"llm|gpt-?\d*|machine\s+learning)\b"
)
_AI_SECRET = re.compile(r"(?i)(api\s*key|system\s*prompt|source\s*code|secret|\.env)")
_PDF_AI = re.compile(
    r"(?i)\b(pdf|report|pro|love\s+reality|milan|numerology|palmistry)\b"
)
_V1V3 = re.compile(r"(?i)\b(v1|v3|ask|live|pack|engine|bot|answer|chart)\b")

_OFF_APP = re.compile(
    r"(?i)\b(weather|cricket|\bipl\b|stock market|bitcoin|recipe|homework|politics|"
    r"who is the prime minister|write code for me)\b"
)
_PRODUCTS = (
    "astrovastu",
    "business vastu",
    "numerology",
    "love reality",
    "milan",
    "palmistry",
    "face reading",
    "birth time",
    "cosmo",
    "transaction",
    "payment",
    "report",
    "pdf",
    "pack",
    "v3",
    "radar",
    "energy",
    "today",
    "forecast",
    "dosh",
    "subscription",
    "pro plan",
    "basic",
    "refund",
    "panchang",
    "muhurat",
    "gemstone",
    "career",
    "personalization",
    "quota",
    "health",
    "finance",
    "rashifal",
    "remedies",
    "login",
    "otp",
    "theme",
    "welcome",
    "gift",
    "instagram",
    "notification",
)


def reply_lang(lang: str | None) -> str:
    """Cosmic Help replies: English or Hinglish only — never Devanagari Hindi."""
    v = (lang or "").strip().lower()
    if v == "en":
        return "en"
    return "hn"


def detect_lang(text: str, preferred: str | None = None) -> str:
    """Detect question language, then map to a allowed reply language (en | hn).

    Devanagari Hindi questions still get a Hinglish answer (roman script).
    """
    blob = text or ""
    if any("\u0900" <= ch <= "\u097f" for ch in blob):
        return "hn"
    letters = "".join(ch for ch in blob if ch.isalpha())
    if len(letters) >= 8 and letters.isascii():
        hinglish = (
            " kya ",
            " hai ",
            " nahi ",
            " kaise ",
            " kahan ",
            " meri ",
            " kitna ",
            " chahiye ",
            " batao ",
            " karun ",
            " karo ",
        )
        low = f" {blob.lower()} "
        if any(w in low for w in hinglish):
            return "hn"
        return "en"
    return reply_lang(preferred)


def prior_user_texts(history: list[dict[str, Any]] | None) -> list[str]:
    return [
        str(m.get("text") or "").strip()
        for m in (history or [])
        if isinstance(m, dict) and m.get("sender") == "user"
    ][:-1]


def last_user_and_bot(history: list[dict[str, Any]] | None) -> tuple[str, str]:
    last_user = ""
    last_bot = ""
    for m in reversed(history or []):
        if not isinstance(m, dict):
            continue
        who = str(m.get("sender") or "")
        body = str(m.get("text") or "").strip()
        if not body:
            continue
        if who == "bot" and not last_bot:
            last_bot = body
        elif who == "user" and not last_user:
            last_user = body
        if last_user and last_bot:
            break
    return last_user, last_bot


def classify_relation(text: str, history: list[dict[str, Any]] | None) -> str:
    """Deterministic follow_up vs new — LLM may refine, code is the floor."""
    t = (text or "").strip()
    if not t:
        return "new"
    prev_user, prev_bot = last_user_and_bot(history)
    if not prev_user and not prev_bot:
        return "new"
    # Very short or pronoun-heavy → follow_up
    words = t.split()
    if len(words) <= 4 and (_FOLLOW_SHORT.search(t) or _FOLLOW_PRONOUN.search(t)):
        return "follow_up"
    if _FOLLOW_PRONOUN.search(t) and len(words) <= 8:
        return "follow_up"
    # Same product noun as previous user/bot
    blob = f"{prev_user} {prev_bot}".lower()
    low = t.lower()
    for p in _PRODUCTS:
        if p in low and p in blob:
            return "follow_up"
    # Clearly different product vs previous
    prev_hits = [p for p in _PRODUCTS if p in blob]
    cur_hits = [p for p in _PRODUCTS if p in low]
    if cur_hits and prev_hits and set(cur_hits).isdisjoint(set(prev_hits)):
        return "new"
    if len(words) >= 6 and not _FOLLOW_PRONOUN.search(t):
        return "new"
    return "new"


def is_ask_tab_question(text: str) -> bool:
    return bool(_ASK_KUNDLI.search(text or ""))


def is_off_app_question(text: str) -> bool:
    return bool(_OFF_APP.search(text or ""))


_GENERIC_ANS = re.compile(
    r"(?i)("
    r"\bgeneric\b|"
    r"sahi se nahi|sahi nahi aa|sahi nahi lag|"
    r"not (correct|accurate|right)|"
    r"wrong answer|galat jawab|jawab galat|"
    r"hamesha (same|generic|ek jaisa)|"
    r"always (generic|same|wrong)|"
    r"answers? (are |is )?(generic|wrong|same|not)"
    r")"
)
_NOT_CHART_COMPLAINT = re.compile(
    r"(?i)\b(otp|pdf|login|wallet|connect|queue|transaction|payment failed)\b"
)


def is_generic_or_wrong_answer_ask(text: str) -> bool:
    """V1/Ask answers feel generic or wrong → steer to V3 (3-dimension engine)."""
    t = text or ""
    if not _GENERIC_ANS.search(t):
        return False
    if _NOT_CHART_COMPLAINT.search(t):
        return False
    return True


def v3_power_engine_reply(lang: str) -> str:
    L = reply_lang(lang)
    if L == "en":
        return (
            "If answers feel generic or not right, use V3 Live. "
            "It is a super powerful special advanced engine — not AI. "
            "It verifies your chart with a 3-dimension rule: KP, BNN, and Vedic. "
            "That is why V3 is super accurate and very powerful. "
            "Book on Ask → language → Cosmic Packs (V3)."
        )
    return (
        "Agar answers generic ya sahi nahi aa rahe, V3 Live use karo. "
        "Woh super powerful special advanced engine hai — AI nahi. "
        "Chart ko 3-dimension rule se verify karta hai: KP, BNN, aur Vedic. "
        "Isliye V3 super accurate aur bahut zyada powerful hai. "
        "Book: Ask → language → Cosmic Packs (V3)."
    )


_HELP_SELF = re.compile(
    r"(?i)("
    r"cosmic\s*help|"
    r"\b(tum|aap|you|your)\b|"
    r"\bare you\b"
    r")"
)
_ASK_V1V3_SUBJECT = re.compile(r"(?i)\b(v1|v3|ask\s+bot|ask\s+tab|ask\s+v1|ask\s+v3)\b")


def is_ai_product_ask(text: str) -> bool:
    """User asking if V1 / V3 / Help / reports / the app is AI — not asking for secrets."""
    t = text or ""
    if not _AI_WORD.search(t):
        return False
    if _AI_SECRET.search(t):
        return False
    return True


def _is_help_self_ai_ask(text: str) -> bool:
    """'Are you / is Cosmic Help AI?' — not 'is V1/V3/Ask AI?'."""
    t = text or ""
    if _ASK_V1V3_SUBJECT.search(t):
        return False
    return bool(_HELP_SELF.search(t))


def not_ai_engine_reply(text: str, lang: str) -> str:
    """Clear deny: not AI. Help = support. V1/V3 = chart engine. PDF = expert."""
    L = reply_lang(lang)
    t = text or ""
    if _is_help_self_ai_ask(t):
        if L == "en":
            return (
                "No — Cosmic Help is not AI. "
                "I am in-app support: app how-to, payments, this account. "
                "Personal kundli questions go to the Ask tab."
            )
        return (
            "Nahi — Cosmic Help AI nahi hai. "
            "Main in-app support hoon: app kaise use kare, payments, yeh account. "
            "Personal kundli ke liye Ask tab use karo."
        )
    pdf_only = bool(_PDF_AI.search(t)) and not _V1V3.search(t)
    if pdf_only:
        if L == "en":
            return (
                "No — it is not AI. The Pro PDF is written by our expert after you pay. "
                "It is not an instant auto file."
            )
        return (
            "Nahi — yeh AI nahi hai. Pro PDF pay ke baad expert likhte hain. "
            "Instant auto file nahi hoti."
        )
    if L == "en":
        return (
            "No — it is not AI. Ask V1 and V3 use a special advanced engine "
            "that reads your chart and then answers."
        )
    return (
        "Nahi — yeh AI nahi hai. Ask V1 aur V3 ek special advanced engine use karte hain "
        "jo aapka chart padhkar jawab deta hai."
    )


def reply_overlaps_previous_bot(reply: str, prev_bot: str, *, relation: str) -> bool:
    """True when a 'new' answer looks like a paste of the previous bot message."""
    if relation != "new":
        return False
    a = re.sub(r"\s+", " ", (reply or "").strip().lower())
    b = re.sub(r"\s+", " ", (prev_bot or "").strip().lower())
    if len(a) < 40 or len(b) < 40:
        return False
    # Substantial shared substring
    if a[:80] in b or b[:80] in a:
        return True
    # Same product FAQ keywords dense overlap
    keys = ("astrovastu", "expert-written", "my reports", "24 hours", "12 hours", "priority")
    hits_a = sum(1 for k in keys if k in a)
    hits_b = sum(1 for k in keys if k in b)
    return hits_a >= 2 and hits_b >= 2 and hits_a == hits_b

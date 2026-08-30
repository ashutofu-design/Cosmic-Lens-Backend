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
_OFF_APP = re.compile(
    r"(?i)\b(weather|cricket|stock market|bitcoin|recipe|homework|politics|"
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

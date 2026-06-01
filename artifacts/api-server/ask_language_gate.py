"""Ask section language gate — Hindi, Hinglish, English only.

Detects unsupported scripts (Tamil, Bengali, Telugu, …) before any LLM call.
Returns one fixed refusal message for blocked questions.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Literal, Optional

AskLang = Literal["en", "hi", "hn"]

# One fixed user-facing reply (per product spec).
REFUSAL_TEXT = (
    "Cosmic Ask sirf Hindi (देवनागरी), Hinglish, ya English mein kaam karta hai. "
    "Kripya apna sawaal in teeno languages mein likh kar dubara bhejein — "
    "doosri language mein abhi jawab nahi diya ja sakta."
)

_HINGLISH_TOKENS = frozenset({
    "kab", "kya", "kyon", "kyun", "kaise", "kaun", "kahan", "kitna", "kitne",
    "hai", "hain", "ho", "hoga", "hogi", "hua", "hui", "tha", "thi", "the",
    "mai", "main", "mei", "mein", "me",
    "mera", "meri", "mere", "mujhe", "mujhko", "humara", "humari", "hamara",
    "aap", "aapka", "aapki", "aapke", "tum", "tera", "teri", "tumhara",
    "shaadi", "shadi", "vivah", "biwi", "pati", "patni", "rishta",
    "naukri", "kaam", "paisa", "paise", "dhan", "santaan", "bachcha",
    "swasthya", "bimari", "batao", "bataiye", "karna", "karu", "karoon",
    "nahi", "nahin", "haan", "han", "kundli", "rashi", "nakshatra", "dasha",
    "abhi", "phir", "pehle", "baad", "se", "tak", "ya", "aur",
})

# Unicode blocks that are NOT allowed in Ask (non Hindi-Devanagari / non Latin).
_UNSUPPORTED_SCRIPT_RANGES: tuple[tuple[int, int, str], ...] = (
    (0x0980, 0x09FF, "bengali"),
    (0x0A00, 0x0A7F, "gurmukhi"),
    (0x0A80, 0x0AFF, "gujarati"),
    (0x0B00, 0x0B7F, "oriya"),
    (0x0B80, 0x0BFF, "tamil"),
    (0x0C00, 0x0C7F, "telugu"),
    (0x0C80, 0x0CFF, "kannada"),
    (0x0D00, 0x0D7F, "malayalam"),
    (0x0600, 0x06FF, "arabic"),
    (0x0750, 0x077F, "arabic"),
    (0x0400, 0x04FF, "cyrillic"),
    (0x0E00, 0x0E7F, "thai"),
    (0x3040, 0x30FF, "japanese"),
    (0x4E00, 0x9FFF, "cjk"),
    (0xAC00, 0xD7AF, "korean"),
)


def _gate_enabled() -> bool:
    return (os.environ.get("ASK_LANGUAGE_GATE") or "on").strip().lower() != "off"


def _unsupported_script_hit(question: str) -> Optional[str]:
    for ch in question:
        o = ord(ch)
        if o < 128 or ch.isspace():
            continue
        if 0x0900 <= o <= 0x097F:
            continue
        for lo, hi, name in _UNSUPPORTED_SCRIPT_RANGES:
            if lo <= o <= hi:
                return name
    return None


def detect_supported_ask_lang(question: str) -> Optional[AskLang]:
    """
    Returns en | hi | hn when allowed, None when unsupported script/language.
    """
    q = (question or "").strip()
    if not q:
        return "en"

    if _unsupported_script_hit(q):
        return None

    for ch in q:
        if "\u0900" <= ch <= "\u097F":
            return "hi"

    tokens = re.findall(r"[a-zA-Z]+", q.lower())
    if not tokens:
        return "en"

    hinglish_hits = sum(1 for t in tokens if t in _HINGLISH_TOKENS)
    if hinglish_hits >= 2:
        return "hn"
    if hinglish_hits >= 1 and (hinglish_hits / max(1, len(tokens))) >= 0.10:
        return "hn"
    return "en"


@dataclass(frozen=True)
class AskLanguageVerdict:
    allowed: bool
    lang: Optional[AskLang] = None
    script_blocked: Optional[str] = None


def assess_ask_language(question: str) -> AskLanguageVerdict:
    if not _gate_enabled():
        lang = detect_supported_ask_lang(question) or "en"
        return AskLanguageVerdict(allowed=True, lang=lang)
    blocked = _unsupported_script_hit(question or "")
    if blocked:
        return AskLanguageVerdict(allowed=False, script_blocked=blocked)
    lang = detect_supported_ask_lang(question)
    if lang is None:
        return AskLanguageVerdict(allowed=False, script_blocked="unknown")
    return AskLanguageVerdict(allowed=True, lang=lang)


def language_refusal_payload() -> dict:
    """JSON body for /api/ask and /api/ask/stream (HTTP 200 soft reject)."""
    return {
        "text": REFUSAL_TEXT,
        "topic": "unsupported_language",
        "question_type": "STATIC",
        "confidence": 1.0,
        "source": "language_gate:unsupported",
        "engine_tag": "ans-cosmo",
        "follow_ups": [],
        "quota": {"used": 0, "limit": 0},
        "plan": "free",
    }

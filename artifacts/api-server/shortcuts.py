"""
Phase 6.2 — Canned replies for greetings / intro / help.
Bypasses classifier + LLM (no quota burn).
"""

from __future__ import annotations

import re
from typing import Any

# Pure greetings & short hellos (voice STT often returns these verbatim).
_GREETING_RE = re.compile(
    r"^("
    r"hi+|hello+|hey+|hlo+|helo+|hallo+|hii+|hy+"
    r"|namaste|namaskar|pranam|ram\s*ram|jai\s*shree\s*ram"
    r"|good\s*(morning|evening|afternoon|night)"
    r"|नमस्ते|नमस्कार|प्रणाम|हैलो|हेलो|हाइ|हाय|हैल्लो"
    r"|kaise\s*ho|kaise\s*hai|kya\s*haal"
    r")(\s+("
    r"hi+|hello+|hey+|namaste|namaskar"
    r"|नमस्ते|हैलो|हेलो"
    r"))?\s*[!?.।,]*$",
    re.IGNORECASE,
)

_HELP_RE = re.compile(
    r"^(help|madad|sahayata|kaise\s*use|how\s*to\s*use|kya\s*kar\s*sakte)\s*[!?.]*$",
    re.IGNORECASE,
)

_WHO_RE = re.compile(
    r"^(who\s*are\s*you|tum\s*kaun|aap\s*kaun|cosmo\s*kya\s*hai|what\s*is\s*cosmo)\s*[!?.]*$",
    re.IGNORECASE,
)


def _reply(lang: str) -> dict[str, str]:
    low = (lang or "en").lower()
    if low.startswith("hi"):
        return {
            "text": (
                "Namaste! Main Cosmo hoon — aapki kundli ke hisaab se career, shaadi, "
                "health, paisa aur timing par seedha jawab deta hoon. "
                "Aaj aap kya janna chahte ho?"
            ),
            "topic": "greeting",
            "source": "shortcut:greeting",
        }
    return {
        "text": (
            "Hello! I'm Cosmo — I read your birth chart and answer career, marriage, "
            "health, money, and timing questions in plain language. "
            "What would you like to know today?"
        ),
        "topic": "greeting",
        "source": "shortcut:greeting",
    }


def _help_reply(lang: str) -> dict[str, str]:
    low = (lang or "en").lower()
    if low.startswith("hi"):
        return {
            "text": (
                "Seedha apna sawaal likho ya bolo — jaise \"Shadi kab hogi?\", "
                "\"Career kaisi rahegi?\", \"Meri rashi kya hai?\". "
                "Main aapki kundli se personalized jawab dunga."
            ),
            "topic": "help",
            "source": "shortcut:help",
        }
    return {
        "text": (
            "Just type or speak your question — e.g. \"When will I marry?\", "
            "\"How is my career?\", \"What is my rashi?\". "
            "I'll answer from your birth chart."
        ),
        "topic": "help",
        "source": "shortcut:help",
    }


_GREETING_WORDS = frozenset({
    "hi", "hii", "hiii", "hello", "hey", "helo", "hlo", "hallo", "hy",
    "namaste", "namaskar", "pranam", "namaskaram",
    "नमस्ते", "नमस्कार", "प्रणाम", "हैलो", "हेलो", "हाइ", "हाय", "हैल्लो",
    "kaise", "ho", "hai", "haal", "kya", "good", "morning", "evening",
    "afternoon", "night", "ram", "jai", "shree", "shri",
})


def _is_greeting(q: str) -> bool:
    if _GREETING_RE.match(q):
        return True
    words = re.findall(r"[\w\u0900-\u097F]+", q, flags=re.IGNORECASE)
    if not words or len(words) > 6:
        return False
    lowered = [w.lower() for w in words]
    if all(w in _GREETING_WORDS for w in lowered):
        return True
    return len(lowered) <= 3 and sum(1 for w in lowered if w in _GREETING_WORDS) >= len(lowered) - 1


def resolve_ask_shortcut(question: str, lang: str = "en") -> dict[str, Any] | None:
    """Canned reply dict ready for jsonify, or None."""
    sc = try_shortcut(question, lang=lang)
    if not sc:
        return None
    sc.setdefault("quota", {"used": 0, "limit": 0})
    sc.setdefault("plan", "free")
    return sc


def try_shortcut(question: str, lang: str = "en") -> dict[str, Any] | None:
    q = " ".join((question or "").strip().split())
    if not q:
        return None

    if _is_greeting(q):
        out = _reply(lang)
        out["confidence"] = 1.0
        out["follow_ups"] = [
            "Meri rashi kya hai?",
            "Career kaisi rahegi?",
            "Shadi kab hogi?",
        ]
        return out

    if _HELP_RE.match(q):
        out = _help_reply(lang)
        out["confidence"] = 1.0
        out["follow_ups"] = []
        return out

    if _WHO_RE.match(q):
        low = (lang or "en").lower()
        text = (
            "Main Cosmo hoon — Cosmic Lens ka Vedic intelligence engine. "
            "Aapki janam kundli se career, rishte, health aur timing par evidence-based jawab deta hoon."
            if low.startswith("hi")
            else
            "I'm Cosmo — Cosmic Lens's Vedic intelligence engine. "
            "I give evidence-based answers on career, relationships, health, and timing from your birth chart."
        )
        return {
            "text": text,
            "topic": "intro",
            "source": "shortcut:intro",
            "confidence": 1.0,
            "follow_ups": [],
        }

    return None

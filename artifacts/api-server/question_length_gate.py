"""
question_length_gate.py — P1.2.9 (A1)
======================================
Hard cap on inbound /api/ask question length to prevent token waste from
multi-paragraph essay-style questions. Per user-rule (P1.2.9):

    "User bahar zyada hi paragraph long send karega token unnesary use hoga."

Default cap = 300 chars / ~50 words.  Killswitch: MAX_QUESTION_CHARS=0 disables.

Public API
----------
    from question_length_gate import check_question_length, MAX_QUESTION_CHARS

    verdict = check_question_length(question, lang="hinglish")
    if verdict.too_long:
        return jsonify(verdict.payload()), 400

Design notes
------------
- Pure stdlib (no flask import) — easy to unit-test.
- Returns a frozen dataclass-ish object so callers don't reach into raw fields.
- Hinglish-default friendly reject message; English/Hindi variants too.
- Telemetry-friendly payload includes char_count + word_count + cap.
- ADD-ONLY: existing routes pre-P1.2.9 had NO input-side length gate (only
  storage truncation at 1000 chars in question_history.py). Killswitch
  MAX_QUESTION_CHARS=0 reverts to legacy unbounded behavior byte-identically.
"""
from __future__ import annotations

import os
import re
from typing import Optional


# ── Configuration ───────────────────────────────────────────────────────────
def _read_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw.strip())
    except (TypeError, ValueError):
        return default


# Hard cap (chars). 0 = killswitch (disabled, legacy unbounded behavior).
MAX_QUESTION_CHARS: int = _read_int_env("MAX_QUESTION_CHARS", 300)

# Soft warn threshold (chars) — currently advisory only, used in telemetry.
SOFT_WARN_CHARS: int = _read_int_env("SOFT_WARN_QUESTION_CHARS", 200)


# ── Reject messages (per language) ──────────────────────────────────────────
# Friendly Hinglish-first tone matching the rest of the product. The cap value
# is interpolated so changing MAX_QUESTION_CHARS auto-updates the message.
_REJECT_MSG = {
    "hinglish": (
        "Bhai thoda short me pucho — 1-2 sentence me, ek baar me ek hi sawal. "
        "Lambha paragraph token-cost zyada karta hai aur jawab dilute ho jaata "
        "hai. (Limit: {cap} characters, aapne {n} bheje.)"
    ),
    "hi": (
        "Kripya prashn chhota rakhein — 1-2 vakya, ek baar me ek prashn. "
        "Lambha paragraph se uttar saaf nahi aata. "
        "(Seema: {cap} akshar, aapne {n} bheje.)"
    ),
    "en": (
        "Please keep your question short — 1–2 sentences, one question at a "
        "time. Long paragraphs make the answer less precise. "
        "(Limit: {cap} characters, you sent {n}.)"
    ),
}


def _resolve_lang(lang: Optional[str]) -> str:
    """Map any lang hint → one of {hinglish, hi, en}. Default = hinglish."""
    if not lang:
        return "hinglish"
    s = str(lang).strip().lower()
    if s in ("hinglish", "hng", "hinen", "hi-en", "en-hi"):
        return "hinglish"
    if s in ("hi", "hindi", "in", "in-hi"):
        return "hi"
    if s.startswith("en"):
        return "en"
    return "hinglish"


# ── Verdict object ──────────────────────────────────────────────────────────
class LengthVerdict:
    """Lightweight result holder. Use .too_long, .payload(), .telemetry()."""

    __slots__ = ("too_long", "char_count", "word_count", "cap", "lang", "soft_warn")

    def __init__(self, too_long: bool, char_count: int, word_count: int,
                 cap: int, lang: str, soft_warn: bool):
        self.too_long = too_long
        self.char_count = char_count
        self.word_count = word_count
        self.cap = cap
        self.lang = lang
        self.soft_warn = soft_warn

    def payload(self) -> dict:
        """JSON-ready 400 response body for over-cap rejects."""
        msg_template = _REJECT_MSG.get(self.lang) or _REJECT_MSG["hinglish"]
        msg = msg_template.format(cap=self.cap, n=self.char_count)
        return {
            "error":      "question_too_long",
            "text":       msg,                 # frontend can surface as-is
            "topic":      "input_rejected",
            "confidence": 1.0,
            "source":     "question_length_gate",
            "follow_ups": [],
            "quota":      {"used": 0, "limit": 0},
            "plan":       "free",
            "limit_info": {
                "char_count": self.char_count,
                "word_count": self.word_count,
                "cap":        self.cap,
                "phase":      "P1.2.9_A1",
            },
        }

    def telemetry(self) -> dict:
        """Compact dict for the [ask] log line."""
        return {
            "char_count": self.char_count,
            "word_count": self.word_count,
            "cap":        self.cap,
            "soft_warn":  self.soft_warn,
            "too_long":   self.too_long,
            "phase":      "P1.2.9_A1",
        }


# ── Word counting (cheap, regex-based) ──────────────────────────────────────
_WORD_RX = re.compile(r"\S+")


def _count_words(s: str) -> int:
    if not s:
        return 0
    return len(_WORD_RX.findall(s))


# ── Public API ──────────────────────────────────────────────────────────────
def check_question_length(question: str,
                          lang: Optional[str] = "hinglish") -> LengthVerdict:
    """
    Inspect `question` and return a LengthVerdict.

    Killswitch: if MAX_QUESTION_CHARS env == 0, always returns too_long=False
    (legacy unbounded behavior).

    Char count is on stripped input (leading/trailing whitespace ignored).
    """
    q = (question or "").strip()
    n_chars = len(q)
    n_words = _count_words(q)
    resolved_lang = _resolve_lang(lang)

    # Killswitch — disabled
    if MAX_QUESTION_CHARS <= 0:
        return LengthVerdict(
            too_long=False, char_count=n_chars, word_count=n_words,
            cap=0, lang=resolved_lang, soft_warn=False,
        )

    too_long = n_chars > MAX_QUESTION_CHARS
    soft_warn = (not too_long) and SOFT_WARN_CHARS > 0 and n_chars > SOFT_WARN_CHARS

    return LengthVerdict(
        too_long=too_long, char_count=n_chars, word_count=n_words,
        cap=MAX_QUESTION_CHARS, lang=resolved_lang, soft_warn=soft_warn,
    )


def is_gate_enabled() -> bool:
    """True if MAX_QUESTION_CHARS > 0 (killswitch off)."""
    return MAX_QUESTION_CHARS > 0

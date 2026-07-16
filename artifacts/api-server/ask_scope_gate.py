"""Ask scope gate — allow all cosmic questions; block only clear off-topic.

Philosophy:
  • Do NOT grow an allowlist one question at a time — that never ends.
  • ALLOW astrology / vastu / numerology / remedies / life domains / "kisi ka" advice.
  • BLOCK only clear off-topic (recipes, coding, sports scores, politics news).
  • Ambiguous asks fail open — DNA + engines + LLM answer them.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Literal, Optional

ScopeReason = Literal[
    "ok",
    "off_topic",
    "general_knowledge",
    "not_personal",
]

SCOPE_REFUSAL_TEXT = (
    "Cosmic Ask sirf jyotish / cosmic life sawaal leta hai — kundli, shaadi, "
    "career, health, paisa, gemstone, remedy, timing, etc. "
    "Coding, recipes, news, sports scores yahan nahi. "
    "Kripya astrology ya apni life se juda sawaal puchiye."
)

# Hard off-topic — only these are refused (no per-question allowlist).
_HARD_OFF_TOPIC_RX = re.compile(
    r"(?ix)\b("
    r"biryani|recipe|cooking|code\s*likho|python\s+function|javascript|"
    r"write\s+a\s+(?:function|program|script)|"
    r"match\s+kaun\s+jeetega|ipl\s+score|weather\s+aaj|"
    r"president\s+of\s+india|prime\s+minister\s+kaun|"
    r"cricket\s+score|football\s+score"
    r")\b"
)

# Broad cosmic/life signal — allow immediately (skip scope LLM latency).
_COSMIC_OR_LIFE_RX = re.compile(
    r"(?ix)\b("
    r"jyotish|astrology|horoscope|kundli|kundali|chart|rashi|lagna|"
    r"nakshatra|dasha|graha|planet|transit|gochar|yog|dosh|manglik|"
    r"gemstone|gem\s*stone|ratna|stone|mani|remedy|upay|upaay|mantra|puja|yantra|"
    r"vastu|vaastu|numerology|tarot|palmistry|hastrekha|"
    r"shaadi|shadi|marriage|vivah|love|pyaar|partner|bf|gf|"
    r"career|naukri|job|business|paisa|money|wealth|finance|"
    r"health|sehat|tabiyat|swasth|child|bachcha|pregnancy|"
    r"property|ghar|flat|visa|abroad|videsh|travel|"
    r"luck|bhagya|future|timing|spiritual|adhyatm|dharma|dharmik|moksha|"
    r"leo|mesh|vrishabh|mithun|kark|singh|kanya|tula|vrishchik|"
    r"dhanu|makar|kumbh|meen|aries|taurus|gemini|cancer|virgo|"
    r"libra|scorpio|sagittarius|capricorn|aquarius|pisces|"
    r"house|bhav|bhaav|sun|moon|mars|venus|saturn|rahu|ketu|jupiter|"
    r"mera|meri|mere|mujhe|main|mein|my|hamari|hamara|"
    r"hoga|hogi|milega|kaisa|kaisi|kab|kaunsa|kaunsi|dharan"
    r")\b|(?:(?<![a-z])me(?![a-z]))"
)

# Short greetings — must pass scope gate AND get canned reply (not LLM).
_GREETING_RX = re.compile(
    r"(?ix)^("
    r"hi+|hello+|hey+|hlo+|helo+|hallo+|hii+|hy+"
    r"|namaste|namaskar|pranam|ram\s*ram|jai\s*shree\s*ram"
    r"|good\s*(morning|evening|afternoon|night)"
    r"|नमस्ते|नमस्कार|प्रणाम|हैलो|हेलो|हाइ|हाय|हैल्लो"
    r"|kaise\s*ho|kaise\s*hai|kya\s*haal"
    r")(\s+("
    r"hi+|hello+|hey+|namaste|namaskar|नमस्ते|हैलो|हेलो"
    r"))?\s*[!?.।,]*$"
)


def _is_short_greeting(q: str) -> bool:
    if _GREETING_RX.match(q):
        return True
    words = re.findall(r"[\w\u0900-\u097F]+", q, flags=re.IGNORECASE)
    if not words or len(words) > 6:
        return False
    greet = {
        "hi", "hii", "hello", "hey", "helo", "namaste", "namaskar", "pranam",
        "नमस्ते", "नमस्कार", "हैलो", "हेलो", "हाइ", "हाय", "kaise", "ho", "hai",
    }
    lowered = [w.lower() for w in words]
    return all(w in greet for w in lowered)


def greeting_shortcut_response(question: str, lang: str = "en") -> Optional[dict]:
    """Canned welcome for hi/hello — no shortcuts.py import required."""
    from ask_question_normalize import prepare_ask_question

    q = prepare_ask_question((question or "").strip())
    if not q or not _is_short_greeting(q):
        return None
    hi = (lang or "en").lower().startswith("hi")
    text = (
        "Namaste! Main Cosmo hoon — aapki kundli ke hisaab se career, shaadi, "
        "health, paisa aur timing par seedha jawab deta hoon. "
        "Aaj aap kya janna chahte ho?"
        if hi
        else
        "Hello! I'm Cosmo — I read your birth chart and answer career, marriage, "
        "health, money, and timing questions in plain language. "
        "What would you like to know today?"
    )
    return {
        "text": text,
        "topic": "greeting",
        "source": "shortcut:greeting",
        "confidence": 1.0,
        "follow_ups": [
            "Meri rashi kya hai?",
            "Career kaisi rahegi?",
            "Shadi kab hogi?",
        ],
        "quota": {"used": 0, "limit": 0},
        "plan": "free",
    }


def _gate_enabled() -> bool:
    return (os.environ.get("ASK_SCOPE_GATE") or "on").strip().lower() != "off"


@dataclass(frozen=True)
class AskScopeVerdict:
    allowed: bool
    reason: ScopeReason
    normalized_question: Optional[str] = None


def _looks_cosmic_or_life(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if _COSMIC_OR_LIFE_RX.search(q):
        return True
    try:
        from ask_routing_policy import is_cosmic_domain_question

        if is_cosmic_domain_question(q):
            return True
    except Exception:
        pass
    return False


def assess_ask_scope(question: str, history: Any = None) -> AskScopeVerdict:
    """Allow all cosmic asks; hard-block only clear off-topic."""
    from ask_question_normalize import prepare_ask_question

    q = prepare_ask_question((question or "").strip())
    if not q:
        return AskScopeVerdict(allowed=False, reason="not_personal")

    if _is_short_greeting(q):
        return AskScopeVerdict(allowed=True, reason="ok")

    if not _gate_enabled():
        return AskScopeVerdict(allowed=True, reason="ok")

    # Fast hard block — recipes/coding/scores (no allowlist needed).
    if _HARD_OFF_TOPIC_RX.search(q):
        return AskScopeVerdict(allowed=False, reason="off_topic")

    # Fast allow — any jyotish/life signal (leo lagna, gemstone, dharmik, shaadi…).
    if _looks_cosmic_or_life(q):
        return AskScopeVerdict(allowed=True, reason="ok")

    # Remaining ambiguous text — ask scope LLM, but ONLY block off_topic.
    try:
        from ask_scope_llm import classify_ask_scope_llm, scope_llm_enabled

        if not scope_llm_enabled():
            return AskScopeVerdict(allowed=True, reason="ok")

        _llm = classify_ask_scope_llm(q, history=history)
        if _llm.get("source") in ("llm", "llm_low_conf"):
            _conf = float(_llm.get("confidence") or 0.0)
            _cleaned = (_llm.get("cleaned_question") or "").strip()
            _norm = prepare_ask_question(_cleaned) if _cleaned else None

            if _llm.get("allowed"):
                return AskScopeVerdict(
                    allowed=True, reason="ok", normalized_question=_norm or None
                )

            # Product rule: never reject GK / not_personal / theory —
            # only clear off_topic is refused. Everything else gets an answer.
            if _conf >= 0.72 and (_llm.get("reason") or "") == "off_topic":
                return AskScopeVerdict(allowed=False, reason="off_topic")
            if _norm and _looks_cosmic_or_life(_norm):
                return AskScopeVerdict(
                    allowed=True, reason="ok", normalized_question=_norm
                )
    except Exception:
        pass

    return AskScopeVerdict(allowed=True, reason="ok")


def scope_refusal_payload(
    reason: Optional[ScopeReason] = None,
    question: str = "",
    lang: str = "en",
) -> dict:
    if question:
        greet = greeting_shortcut_response(question, lang=lang)
        if greet:
            return greet
    return {
        "text": SCOPE_REFUSAL_TEXT,
        "topic": "off_topic",
        "question_type": "STATIC",
        "confidence": 1.0,
        "source": f"scope_gate:{reason or 'blocked'}",
        "engine_tag": "ans-cosmo",
        "follow_ups": [],
        "quota": {"used": 0, "limit": 0},
        "plan": "free",
    }


def astro_scope_refusal(question: str, lang: str = "en", user=None, history: Any = None):
    """Compatibility shim for flask_app (returns None if allowed)."""
    _ = lang, user
    v = assess_ask_scope(question, history)
    if v.allowed:
        return None
    return (v.reason, SCOPE_REFUSAL_TEXT)

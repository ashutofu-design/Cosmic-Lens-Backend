"""Ask scope gate — astrology + personal-life questions only.

Blocks: news, GK, presidents, coding, recipes, and generic questions like
'who invented astrology' that are not about the user's own chart/life.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Literal, Optional

ScopeReason = Literal[
    "ok",
    "off_topic",
    "general_knowledge",
    "not_personal",
]

SCOPE_REFUSAL_TEXT = (
    "Cosmic Ask sirf aapke baare me jyotish sawaal leta hai — aapki kundli, "
    "shaadi, career, health, paisa, bachche, luck, timing, etc. News, coding, "
    "presidents, ya 'astrology kisne banayi' jaisa general GK yahan nahi. "
    "Kripya apni life se juda sawaal puchiye."
)

# Explicit general-knowledge / encyclopedia (even if astrology word appears)
_GK_BLOCK_RX = re.compile(
    r"(?ix)"
    r"\b("
    r"who\s+(is|was|are|were)\s+.{0,40}\b(president|pm|prime\s+minister|"
    r"rashtrapati|chief\s+minister|modi|trump|xi\s+jinping|putin)\b|"
    r"\b(president|pm|prime\s+minister|rashtrapati)\s+of\b|"
    r"\b(who|kisne)\s+(invented|created|developed|discovered|founded|"
    r"started|banayi|banaya|likhi|wrote)\b.{0,30}\b(astrology|jyotish|"
    r"horoscope|kundli|vedic|parashara|bhrigu)\b|"
    r"\b(astrology|jyotish|horoscope|kundli)\s+(was|is|were)\s+"
    r"(developed|invented|created|discovered|founded|written)\s+by\b|"
    r"\bhistory\s+of\s+(astrology|jyotish|vedic|horoscope)\b|"
    r"\bwhat\s+is\s+(astrology|jyotish|horoscope|kundli)\b|"
    r"\b(astrology|jyotish|kundli)\s+(kya\s+hai|matlab|meaning|definition)\b|"
    r"\bdefine\s+(astrology|jyotish|manglik|nakshatra|dasha)\b|"
    r"\b(wikipedia|encyclopedia|general\s+knowledge)\b"
    r")\b"
)

# First-person / own-life anchors (Hindi + English)
_PERSONAL_RX = re.compile(
    r"(?ix)"
    r"\b("
    r"mera|meri|mere|mujhe|mujhko|mujh|main|mein|my|mine|i\s+am|i'll|"
    r"i\s+will|i\s+was|mere\s+liye|meri\s+life|mera\s+future|my\s+career|"
    r"my\s+marriage|my\s+health|my\s+chart|my\s+kundli|my\s+life|"
    r"shaadi\s+hogi|shadi\s+hogi|naukri\s+lagegi|bachcha\s+hoga|lucky\s+hu|manglik\s+hu|"
    r"will\s+i\s+|should\s+i\s+|am\s+i\s+"
    r")\b"
)

# Marriage / career / money timing — personal + kab/hoga (even if "shadi" not "shaadi")
_TIMING_LIFE_RX = re.compile(
    r"(?ix)"
    r"\b(kab|when|kab\s+tak|kis\s+saal|kitne\s+saal)\b.{0,30}\b("
    r"hoga|hogi|hogaa|milega|milegi|lagega|lagegi|aayega|aayegi|ho\s+jaayega"
    r")\b|"
    r"\b(hoga|hogi|milega|milegi)\b.{0,20}\b(kab|when)\b"
)

# Chart placement without mera/meri: "D9 me moon kahan", "8th house me Rahu"
_CHART_PLACEMENT_RX = re.compile(
    r"(?ix)"
    r"\b("
    r"(?:d\d+|navamsa|navamsha|d9|d7|d10|d12)\b.{0,30}\b("
    r"lagna|moon|sun|venus|mars|saturn|rahu|ketu|jupiter|mercury|"
    r"shani|shukra|mangal|surya|chandra|budh|guru"
    r")\b|"
    r"\b(?:1st|2nd|3rd|[4-9]th|1[0-2]th|\d{1,2})\s*(?:house|bhav|bhaav)\b"
    r")\b"
)

_PERSONAL_HOUSE_PLACEMENT_RX = re.compile(
    r"(?ix)"
    r"\b(mera|meri|mere|my|apna|apni|apne)\b"
    r".{0,30}\b("
    r"(?:1st|2nd|3rd|[4-9]th|1[0-2]th|\d{1,2})\s*"
    r"(?:house|bhav|bhaav|ghar|h)\b|"
    r"(?:house|bhav|bhaav|ghar)\s*(?:me|mein|mai|in)?\s*"
    r"(?:1st|2nd|3rd|[4-9]th|1[0-2]th|\d{1,2})"
    r")"
)

# Transparency / "how did you decide this" follow-ups to a prior reading.
# These reference the assistant's previous answer, so they have no astro
# topic word of their own — but they ARE in scope (explain my reading).
# GK ("astrology kaise kaam karta hai") is blocked earlier by _GK_BLOCK_RX.
_TRANSPARENCY_FOLLOWUP_RX = re.compile(
    r"(?ix)\b("
    r"kaise\s+(bataya|bata|pata|kaha|bola|nikala|nikali|samjha|jana|"
    r"jaana|decide|check|maloom|malum)|"
    r"kya\s+(check|dekha|dekhe|aadhar|aadhaar|basis)|check\s+kiya|"
    r"kis\s+(basis|aadhar|aadhaar|cheez|hisaab)\s*(pe|par|se)?|"
    r"pata\s+(chala|chale|kaise)|kaise\s+pata|"
    r"kyun?\s+(bola|kaha|bataya|lagta)|"
    r"proof|saboot|sabut|evidence|"
    r"how\s+(did|do)\s+you\s+(know|say|check|tell|find|figure|"
    r"determine|decide|conclude)|"
    r"what\s+did\s+you\s+(check|see|look)|"
    r"on\s+what\s+basis|why\s+do\s+you\s+say|prove\s+it|"
    r"samjha(?:o|do|iye)"
    r")\b"
)


# Follow-ups after an astrology answer often omit "mera/meri".
_ASTRO_FOLLOWUP_RX = re.compile(
    r"(?ix)"
    r"(?=.*\b("
    r"shaadi|shadi|marriage|vivah|love\s*marriage|arrange(?:d)?|"
    r"relationship|partner|spouse|career|naukri|job|business|paisa|money|"
    r"health|sehat|rahu|ketu|saturn|shani|jupiter|guru|venus|shukra|"
    r"moon|chandra|mars|mangal|sun|surya|mercury|budh|lagna|rashi|"
    r"nakshatra|dasha|kundli|chart|house|bhav|bhaav"
    r")\b)"
    r"(?=.*\b("
    r"kaise|kyun|kyu|why|how|samjha|samjhao|explain|detail|reason|"
    r"kya|kon|kaun|which|where|kahan|kab|when|hoga|hogi|hai|he"
    r")\b)"
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


def assess_ask_scope(question: str) -> AskScopeVerdict:
    from ask_question_normalize import (
        has_question_intent,
        looks_like_implicit_ask,
        looks_like_personal_life_question,
        prepare_ask_question,
    )

    q = prepare_ask_question((question or "").strip())
    if not q:
        return AskScopeVerdict(allowed=False, reason="not_personal")

    if _is_short_greeting(q):
        return AskScopeVerdict(allowed=True, reason="ok")

    if not _gate_enabled():
        return AskScopeVerdict(allowed=True, reason="ok")

    if _GK_BLOCK_RX.search(q):
        return AskScopeVerdict(allowed=False, reason="general_knowledge")

    # "How did you decide this? / kya check kiya?" — transparency follow-up to
    # the previous reading. In scope; the answer layer re-explains the prior
    # question's evidence using conversation history.
    if _TRANSPARENCY_FOLLOWUP_RX.search(q):
        return AskScopeVerdict(allowed=True, reason="ok")

    # Primary path: read topic + intent — mera/meri NOT required in Ask context.
    if looks_like_implicit_ask(q):
        return AskScopeVerdict(allowed=True, reason="ok")

    if _PERSONAL_HOUSE_PLACEMENT_RX.search(q) or _CHART_PLACEMENT_RX.search(q):
        return AskScopeVerdict(allowed=True, reason="ok")

    if _ASTRO_FOLLOWUP_RX.search(q):
        return AskScopeVerdict(allowed=True, reason="ok")

    try:
        from domain_splitter import extract_domains, has_astro_anchor, is_jyotish_anchored_strict

        if extract_domains(q):
            return AskScopeVerdict(allowed=True, reason="ok")
        if has_astro_anchor(q) and has_question_intent(q):
            return AskScopeVerdict(allowed=True, reason="ok")
        if is_jyotish_anchored_strict(q):
            return AskScopeVerdict(allowed=True, reason="ok")
    except Exception:
        pass

    try:
        from openai_helper import _is_brand_unsafe

        if _is_brand_unsafe(q):
            return AskScopeVerdict(allowed=False, reason="off_topic")
    except Exception:
        pass

    try:
        from ask_cosmo import is_personal_chart_question

        if is_personal_chart_question(q):
            return AskScopeVerdict(allowed=True, reason="ok")
    except Exception:
        pass

    if _PERSONAL_RX.search(q):
        if looks_like_personal_life_question(q):
            return AskScopeVerdict(allowed=True, reason="ok")
        if _TIMING_LIFE_RX.search(q):
            return AskScopeVerdict(allowed=True, reason="ok")

    if looks_like_personal_life_question(q):
        return AskScopeVerdict(allowed=True, reason="ok")

    return AskScopeVerdict(allowed=False, reason="not_personal")


def scope_refusal_payload(
    reason: Optional[ScopeReason] = None,
    question: str = "",
    lang: str = "en",
) -> dict:
    # Last-line safety: hi/hello must never get the GK refusal wall.
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


def astro_scope_refusal(question: str, lang: str = "en", user=None):
    """Compatibility shim for flask_app (returns None if allowed)."""
    _ = lang, user
    v = assess_ask_scope(question)
    if v.allowed:
        return None
    return (v.reason, SCOPE_REFUSAL_TEXT)

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

# Short follow-up style asks often omit "mera/meri", e.g.
# "2nd marriage period kab he". These are still personal life-event asks.
_PERSONAL_LIFE_EVENT_RX = re.compile(
    r"(?ix)"
    r"\b("
    r"(?:2nd|second|dusri|doosri|दूसरी)?\s*"
    r"(?:shaadi|shadi|marriage|vivah|विवाह|शादी)|"
    r"career|naukri|job|business|paisa|money|wealth|finance|"
    r"health|sehat|bachcha|child|pregnancy|property|ghar|visa|abroad|videsh"
    r")\b"
    r".{0,40}\b("
    r"kab|when|period|time|timing|kis\s+saal|kitne\s+saal|hoga|hogi|milega|milegi"
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

# Short follow-ups after an astrology answer often omit "mera/meri":
# "kaise love marriage hai samjhao", "delay kyun hai", "career me kaise".
_ASTRO_FOLLOWUP_RX = re.compile(
    r"(?ix)"
    r"(?=.{1,90}$)"
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


def _gate_enabled() -> bool:
    return (os.environ.get("ASK_SCOPE_GATE") or "on").strip().lower() != "off"


@dataclass(frozen=True)
class AskScopeVerdict:
    allowed: bool
    reason: ScopeReason


def assess_ask_scope(question: str) -> AskScopeVerdict:
    from ask_question_normalize import looks_like_personal_life_question, prepare_ask_question

    q = prepare_ask_question((question or "").strip())
    if not q:
        return AskScopeVerdict(allowed=False, reason="not_personal")

    if not _gate_enabled():
        return AskScopeVerdict(allowed=True, reason="ok")

    if _GK_BLOCK_RX.search(q):
        return AskScopeVerdict(allowed=False, reason="general_knowledge")

    if _PERSONAL_LIFE_EVENT_RX.search(q):
        return AskScopeVerdict(allowed=True, reason="ok")

    if _PERSONAL_HOUSE_PLACEMENT_RX.search(q):
        return AskScopeVerdict(allowed=True, reason="ok")

    if _ASTRO_FOLLOWUP_RX.search(q):
        return AskScopeVerdict(allowed=True, reason="ok")

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
        try:
            from domain_splitter import extract_domains, has_astro_anchor, is_jyotish_anchored_strict

            if extract_domains(q):
                return AskScopeVerdict(allowed=True, reason="ok")
            if has_astro_anchor(q) or is_jyotish_anchored_strict(q):
                return AskScopeVerdict(allowed=True, reason="ok")
        except Exception:
            return AskScopeVerdict(allowed=True, reason="ok")

    if looks_like_personal_life_question(q):
        return AskScopeVerdict(allowed=True, reason="ok")

    return AskScopeVerdict(allowed=False, reason="not_personal")


def scope_refusal_payload(reason: Optional[ScopeReason] = None) -> dict:
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

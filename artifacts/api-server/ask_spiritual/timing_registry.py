"""Spiritual growth & occult timing — 8H/9H/12H WHEN questions."""
from __future__ import annotations

import re
from typing import Optional

_EXPLICIT_WHEN_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+se|when|when\s+will|"
    r"kis\s+(?:mahine|saal|year|month|date|turning\s+point)|"
    r"kis\s+dasha|dasha\s+me|gochar|transit|muhurat|kitne\s+mahine|"
    r"trigger\s+hoga|active\s+hoga|active\s+honge|active\s+ho|"
    r"shuru\s+honge|shuru\s+hoga|approve\s+hoga|prapt\s+hogi"
    r")\b|(?:कब|कितना\s+समय)"
)

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+se|when|when\s+will|kis\s+(?:mahine|saal|year|month|date|turning\s+point)|"
    r"milega|milegi|hoga|hogi|honge|aayega|aayegi|banega|banegi|"
    r"shuru\s+hoga|shuru\s+honge|khatam|band\s+hogi|theek\s+hogi|thik\s+hogi|"
    r"seekh\s+paunga|seekh\s+paungi|padh\s+paunga|padh\s+paungi|"
    r"active|trigger|dasha|antardasha|gochar|transit|muhurat|timing|"
    r"turning\s+point|prapt|approve|lagenge|mehsoos|samajh\s+aayega|"
    r"kitne\s+mahine|poora\s+hoga|bhej\s+paunga|bhej\s+paungi"
    r")\b|(?:कब|कितना\s+समय)"
)

from ask_spiritual.spiritual_scope import SPIRITUAL_TOPIC_RX as _SCOPE_RX

_RELIGIOUS_FOREIGN_RX = re.compile(
    r"(?ix)\b("
    r"pavitra\s+sthal|religious\s+tourism|bodh\s+gaya|mecca|vatican|"
    r"teerth|tirth|pilgrim|yatra|dham|mandir|temple|religious|dharmik"
    r")\b",
)

_TRAVEL_GENERIC_RX = re.compile(
    r"(?ix)\b(videsh|foreign|abroad|visa|passport|pr\b|immigration|job\s+abroad)\b",
)

_FINANCE_PRIMARY_RX = re.compile(
    r"(?ix)\b(commercial\s+success|paying\s+customer|paisa|earning|profit)\b",
)

_EDU_INSTITUTE_RX = re.compile(
    r"(?ix)\b(institute|admission|college|university|degree)\b",
)


def is_spiritual_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if re.search(r"(?ix)\bkya\b", q) and not _EXPLICIT_WHEN_RX.search(q):
        return False
    if _FINANCE_PRIMARY_RX.search(q) and not re.search(
        r"(?ix)\b(occult|astrology|jyotish|tarot|prediction|spiritual|guru|dhyan)\b",
        q,
    ):
        return False
    if _EDU_INSTITUTE_RX.search(q) and re.search(
        r"(?ix)\b(astrology|jyotish|occult|tarot|numerology)\b",
        q,
    ):
        pass  # occult institute admission stays spiritual
    elif _EDU_INSTITUTE_RX.search(q) and not re.search(
        r"(?ix)\b(astrology|jyotish|occult|tarot|spiritual)\b",
        q,
    ):
        return False
    if _TRAVEL_GENERIC_RX.search(q):
        if not _RELIGIOUS_FOREIGN_RX.search(q):
            return False
    if isinstance(llm_intent, dict):
        if llm_intent.get("domain") in ("spiritual", "spirituality") and llm_intent.get("is_timing"):
            return True
    if not _SCOPE_RX.search(q):
        return False
    if not _TIMING_RX.search(q) and not _EXPLICIT_WHEN_RX.search(q):
        return False
    return True


def classify_spiritual_timing_bucket(question: str) -> str:
    from event_timing.spiritual.spiritual_timing_v1 import classify_spiritual_timing_bucket as _classify

    return _classify(question)

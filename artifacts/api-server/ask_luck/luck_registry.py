"""Luck / bhagya / kismat topic registry — scope + archetype detection."""

from __future__ import annotations

import re

LUCK_ARCHETYPES = frozenset({
    "overall_luck",
    "luck_strength",
    "career_luck",
    "love_luck",
    "money_luck",
    "lucky_traits",
    "general_luck",
})

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|when\s+will|kis\s+(saal|year|mahine|month)|"
    r"\d{4}\s+me|dasha|antardasha|mahadasha|transit|gochar|muhurat|timing|"
    r"date\s+fix|exact\s+date|kab\s+milega|kab\s+milegi"
    r")\b"
)

_LUCK_CORE_RX = re.compile(
    r"(?ix)\b("
    r"luck|lucky|unlucky|bhagya|bhagy|kismat|qismat|fortune|fortunate|"
    r"misfortune|good\s*fortune|bad\s*fortune|"
    r"saubhagya|subh\s*labh|shubh\s*labh"
    r")\b"
)

_STRENGTH_RX = re.compile(
    r"(?ix)\b("
    r"strong|weak|accha|achi|kharab|kharabi|kamzor|mazboot|"
    r"supportive|favourable|unfavourable|favorable|unfavorable|"
    r"kitna\s+strong|kitni\s+strong|kitna\s+weak"
    r")\b"
)

_CAREER_LUCK_RX = re.compile(
    r"(?ix)\b("
    r"career|naukri|job|business|profession|kaam|office|promotion|"
    r"interview|startup|govt\s*job|sarkari"
    r")\b"
)

_LOVE_LUCK_RX = re.compile(
    r"(?ix)\b("
    r"love|pyaar|prem|shaadi|shadi|marriage|vivah|rishta|partner|"
    r"spouse|bf|gf|biwi|pati|patni|relationship"
    r")\b"
)

_MONEY_LUCK_RX = re.compile(
    r"(?ix)\b("
    r"paisa|paise|money|dhan|wealth|rich|amir|lottery|lottary|"
    r"windfall|sudden\s+gain|inheritance|miras"
    r")\b"
)

_TRAITS_RX = re.compile(
    r"(?ix)\b("
    r"lucky\s+(?:number|no|colour|color|day|stone|gem)|"
    r"shubh\s+(?:ank|number|rang|din|ratn)|"
    r"lucky\s+charm|fortune\s+colour|fortune\s+color|"
    r"kaun\s+sa\s+(?:din|rang|number|ratn)"
    r")\b"
)

# Native overview patterns — not luck engine
_NATIVE_RX = re.compile(
    r"(?ix)\b(mere?\s+(?:bare|baare)|about\s+me|mujhe?\s+baare|personality|swabhav)\b"
)


def is_luck_static_question(question: str) -> bool:
    q = (question or "").strip()
    if not q or _TIMING_RX.search(q):
        return False
    if _NATIVE_RX.search(q) and not _LUCK_CORE_RX.search(q):
        return False
    return bool(_LUCK_CORE_RX.search(q))


def detect_luck_archetype(question: str) -> str | None:
    q = (question or "").strip()
    if not q or not _LUCK_CORE_RX.search(q):
        return None
    if _TRAITS_RX.search(q):
        return "lucky_traits"
    if _CAREER_LUCK_RX.search(q):
        return "career_luck"
    if _LOVE_LUCK_RX.search(q):
        return "love_luck"
    if _MONEY_LUCK_RX.search(q):
        return "money_luck"
    if _STRENGTH_RX.search(q):
        return "luck_strength"
    if re.search(r"(?ix)\b(kaise|kaisa|kaisi|how\s+is|how\s+are)\b", q):
        return "overall_luck"
    return "general_luck"

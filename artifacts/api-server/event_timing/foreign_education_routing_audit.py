"""Audit — 100 foreign edu / visa / PR real-life Q → engine family."""
from __future__ import annotations

import re

from event_timing.timing_router import resolve_timing_domain

_TIMING_HINT = re.compile(
    r"(?ix)\b(kab|kab\s+tak|kis\s+(saal|mahine|month|year|week)|muhurat|mahurat|"
    r"banega|banegi|ban\s+raha|milega|milegi|hoga|hogi|aayega|padega|"
    r"dasha|gochar|transit|active|trigger|deliver|extend|paltega|khatam)\b",
)


def classify_engine_family(question: str) -> str:
    q = question or ""
    dom, _bkt, is_timing = resolve_timing_domain(q)

    if dom == "foreign_education" and is_timing:
        return "foreign_education_timing"
    if dom == "education" and is_timing:
        return "education_timing"
    if dom == "career" and is_timing:
        return "career_timing"
    if dom == "finance" and is_timing:
        return "finance_timing"
    if dom == "travel" and is_timing:
        return "travel_timing"
    if dom == "marriage" and is_timing:
        return "marriage_timing"
    if dom == "property" and is_timing:
        return "property_timing"
    if dom == "health" and is_timing:
        return "health_timing"
    if dom == "litigation" and is_timing:
        return "litigation"

    if _TIMING_HINT.search(q) and re.search(
        r"(?ix)\b(loan|karz|emi)\b", q
    ):
        return "finance_timing"
    if _TIMING_HINT.search(q) and re.search(
        r"(?ix)\b(shaadi|shadi|marriage)\b", q
    ):
        return "marriage_timing"

    return "llm"


def audit_question(question: str, allowed: frozenset[str]) -> tuple[bool, str]:
    got = classify_engine_family(question)
    return got in allowed, got

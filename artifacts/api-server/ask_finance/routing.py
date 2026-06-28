"""Finance archetype routing — question patterns beat LLM mis-routes."""

from __future__ import annotations

import re

from .classifier import classify_finance_archetype
from .finance_registry import (
    FINANCE_ARCHETYPES,
    detect_finance_archetype,
    is_finance_static_question,
)

__all__ = [
    "FINANCE_ARCHETYPES",
    "classify_finance_archetype",
    "detect_finance_archetype",
    "finance_overrides_career",
    "is_finance_static_question",
    "resolve_finance_archetype",
]

_CAREER_WINS_RX = re.compile(
    r"(?ix)\b("
    r"job\s*vs\s*business|naukri\s+ya\s+business|salary\s+karu\s+ya|"
    r"job\s+\w+\s+ya\s+business|salary\s+\w+\s+ya\s+business|"
    r"govt\s*job|sarkari|promotion|interview|job\s*change|"
    r"employee\s+mindset|entrepreneur\s+mindset|"
    r"which\s+(job|field|line)|kaunsi\s+(field|line|naukri)|"
    r"doctor|engineer|pilot|teacher|lawyer|software\s*developer|it\s*job|"
    r"youtuber|actor|singer|electrician|plumber"
    r")\b"
)

_FINANCE_TIMING_MONEY_RX = re.compile(
    r"(?ix)\b("
    r"paisa|paise|money|dhan|wealth|income|kamai|earning|mutual|sip|bachat|"
    r"salary|tankhwah|loan|emi|debt|karz|profit|loss|nuksan"
    r")\b"
)

_TIMING_HINT_RX = re.compile(
    r"(?ix)\b("
    r"kab|when|milega|milegi|aayega|aayegi|lagega|lagegi|hoga|hogi|"
    r"kis\s+(saal|year|mahine|month)"
    r")\b"
)


def finance_overrides_career(question: str) -> bool:
    """Money subdomain Qs beat generic career keyword overlap (paisa/income in career core)."""
    q = (question or "").strip()
    if not q or _CAREER_WINS_RX.search(q):
        return False
    if _FINANCE_TIMING_MONEY_RX.search(q) and _TIMING_HINT_RX.search(q):
        return True
    return bool(detect_finance_archetype(q))

_STOCK_RX = re.compile(
    r"(?ix)\b("
    r"stock|share|equity|nifty|sensex|intraday|trading|trader|"
    r"portfolio|mutual\s*fund|sip|nse|bse|fno|f\s*&\s*o|crypto|bitcoin"
    r")\b"
)


def resolve_finance_archetype(
    question: str,
    *,
    llm_archetype: str | None = None,
    interpretation: str = "",
) -> tuple[str, str]:
    q = (question or "").strip()
    interp = (interpretation or "").strip().lower()
    combined = f"{q} {interp}".strip()

    if _STOCK_RX.search(combined):
        return "general_finance", "stock_keyword_block"

    regex_arch = classify_finance_archetype(q)
    detected = detect_finance_archetype(q) or detect_finance_archetype(interp)

    llm = (llm_archetype or "").strip().lower()
    if llm and llm in FINANCE_ARCHETYPES:
        if detected and detected != llm:
            return detected, f"regex_override_llm:{llm}->{detected}"
        if regex_arch != "general_finance" and regex_arch != llm:
            return regex_arch, f"regex_override_llm:{llm}->{regex_arch}"
        return llm, "llm_archetype"

    if detected:
        return detected, "regex_detect"
    return regex_arch, "regex_classify"

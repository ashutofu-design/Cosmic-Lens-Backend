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
    "is_finance_static_question",
    "resolve_finance_archetype",
]

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

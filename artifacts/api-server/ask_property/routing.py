"""Property archetype routing — question patterns beat LLM mis-routes."""

from __future__ import annotations

from .classifier import classify_property_archetype
from .property_registry import (
    PROPERTY_ARCHETYPES,
    detect_property_archetype,
    is_property_money_only_question,
    is_property_static_question,
)

__all__ = [
    "PROPERTY_ARCHETYPES",
    "classify_property_archetype",
    "detect_property_archetype",
    "is_property_static_question",
    "property_overrides_finance",
    "resolve_property_archetype",
]


def property_overrides_finance(question: str) -> bool:
    """Astrological property Qs beat finance.property_money keyword overlap."""
    q = (question or "").strip()
    if not q or is_property_money_only_question(q):
        return False
    return bool(is_property_static_question(q))


def resolve_property_archetype(
    question: str,
    *,
    llm_archetype: str | None = None,
    interpretation: str = "",
) -> tuple[str, str]:
    q = (question or "").strip()
    interp = (interpretation or "").strip()

    regex_arch = classify_property_archetype(q)
    detected = detect_property_archetype(q) or detect_property_archetype(interp)

    llm = (llm_archetype or "").strip().lower()
    if llm and llm in PROPERTY_ARCHETYPES:
        if detected and detected != llm:
            return detected, f"regex_override_llm:{llm}->{detected}"
        if regex_arch != "general_property" and regex_arch != llm:
            return regex_arch, f"regex_override_llm:{llm}->{regex_arch}"
        return llm, "llm_archetype"

    if detected:
        return detected, "regex_detect"
    return regex_arch, "regex_classify"

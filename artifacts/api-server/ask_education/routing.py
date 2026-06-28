"""Education archetype routing — question patterns beat LLM mis-routes."""

from __future__ import annotations

from .classifier import classify_education_archetype
from .education_registry import (
    EDUCATION_ARCHETYPES,
    detect_education_archetype,
    is_education_static_question,
)

__all__ = [
    "EDUCATION_ARCHETYPES",
    "classify_education_archetype",
    "detect_education_archetype",
    "is_education_static_question",
    "resolve_education_archetype",
]


def resolve_education_archetype(
    question: str,
    *,
    llm_archetype: str | None = None,
    interpretation: str = "",
) -> tuple[str, str]:
    q = (question or "").strip()
    interp = (interpretation or "").strip()

    regex_arch = classify_education_archetype(q)
    detected = detect_education_archetype(q) or detect_education_archetype(interp)

    llm = (llm_archetype or "").strip().lower()
    if llm and llm in EDUCATION_ARCHETYPES:
        if detected and detected != llm:
            return detected, f"regex_override_llm:{llm}->{detected}"
        if regex_arch != "general_education" and regex_arch != llm:
            return regex_arch, f"regex_override_llm:{llm}->{regex_arch}"
        return llm, "llm_archetype"

    if detected:
        return detected, "regex_detect"
    return regex_arch, "regex_classify"

"""Travel archetype routing — question patterns beat LLM mis-routes."""

from __future__ import annotations

from .classifier import classify_travel_archetype
from .travel_registry import (
    TRAVEL_ARCHETYPES,
    detect_travel_archetype,
    is_career_job_abroad_question,
    is_education_study_abroad_question,
    is_travel_static_question,
)

__all__ = [
    "TRAVEL_ARCHETYPES",
    "classify_travel_archetype",
    "detect_travel_archetype",
    "is_travel_static_question",
    "resolve_travel_archetype",
    "travel_overrides_career",
]


def travel_overrides_career(question: str) -> bool:
    q = (question or "").strip()
    if not q or is_career_job_abroad_question(q):
        return False
    return bool(is_travel_static_question(q))


def resolve_travel_archetype(
    question: str,
    *,
    llm_archetype: str | None = None,
    interpretation: str = "",
) -> tuple[str, str]:
    q = (question or "").strip()
    interp = (interpretation or "").strip()

    regex_arch = classify_travel_archetype(q)
    detected = detect_travel_archetype(q) or detect_travel_archetype(interp)

    llm = (llm_archetype or "").strip().lower()
    if llm and llm in TRAVEL_ARCHETYPES:
        if detected and detected != llm:
            return detected, f"regex_override_llm:{llm}->{detected}"
        if regex_arch != "general_travel" and regex_arch != llm:
            return regex_arch, f"regex_override_llm:{llm}->{regex_arch}"
        return llm, "llm_archetype"

    if detected:
        return detected, "regex_detect"
    return regex_arch, "regex_classify"

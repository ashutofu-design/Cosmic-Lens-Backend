"""Litigation archetype routing — question patterns beat LLM mis-routes."""

from __future__ import annotations

from .classifier import classify_litigation_archetype
from .litigation_registry import (
    LITIGATION_ARCHETYPES,
    detect_litigation_archetype,
    is_career_police_job_question,
    is_litigation_static_question,
    is_property_court_question,
)

__all__ = [
    "LITIGATION_ARCHETYPES",
    "classify_litigation_archetype",
    "detect_litigation_archetype",
    "is_litigation_static_question",
    "litigation_overrides_career",
    "resolve_litigation_archetype",
]


def litigation_overrides_career(question: str) -> bool:
    q = (question or "").strip()
    if not q or is_career_police_job_question(q):
        return False
    return bool(is_litigation_static_question(q))


def litigation_overrides_property(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if not is_property_court_question(q):
        return False
    return bool(is_litigation_static_question(q))


def resolve_litigation_archetype(
    question: str,
    *,
    llm_archetype: str | None = None,
    interpretation: str = "",
) -> tuple[str, str]:
    q = (question or "").strip()
    interp = (interpretation or "").strip()

    regex_arch = classify_litigation_archetype(q)
    detected = detect_litigation_archetype(q) or detect_litigation_archetype(interp)

    llm = (llm_archetype or "").strip().lower()
    if llm and llm in LITIGATION_ARCHETYPES:
        if detected and detected != llm:
            return detected, f"regex_override_llm:{llm}->{detected}"
        if regex_arch != "general_litigation" and regex_arch != llm:
            return regex_arch, f"regex_override_llm:{llm}->{regex_arch}"
        return llm, "llm_archetype"

    if detected:
        return detected, "regex_detect"
    return regex_arch, "regex_classify"

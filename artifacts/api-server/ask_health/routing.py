"""Health archetype routing — question patterns beat LLM mis-routes."""

from __future__ import annotations

from .classifier import classify_health_archetype
from .health_registry import (
    HEALTH_ARCHETYPES,
    detect_health_archetype,
    is_health_static_question,
)

__all__ = [
    "HEALTH_ARCHETYPES",
    "classify_health_archetype",
    "detect_health_archetype",
    "is_health_static_question",
    "resolve_health_archetype",
]


def resolve_health_archetype(
    question: str,
    *,
    llm_archetype: str | None = None,
    interpretation: str = "",
) -> tuple[str, str]:
    q = (question or "").strip()
    interp = (interpretation or "").strip().lower()
    combined = f"{q} {interp}".strip()

    regex_arch = classify_health_archetype(q)
    detected = detect_health_archetype(q) or detect_health_archetype(interp)

    llm = (llm_archetype or "").strip().lower()
    if llm and llm in HEALTH_ARCHETYPES:
        if detected and detected != llm:
            return detected, f"regex_override_llm:{llm}->{detected}"
        if regex_arch != "general_health" and regex_arch != llm:
            return regex_arch, f"regex_override_llm:{llm}->{regex_arch}"
        return llm, "llm_archetype"

    if detected:
        return detected, "regex_detect"
    return regex_arch, "regex_classify"

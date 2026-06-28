"""Children archetype routing — question patterns beat LLM mis-routes."""

from __future__ import annotations

from .classifier import classify_children_archetype
from .children_registry import (
    CHILDREN_ARCHETYPES,
    detect_children_archetype,
    is_children_static_question,
)

__all__ = [
    "CHILDREN_ARCHETYPES",
    "classify_children_archetype",
    "detect_children_archetype",
    "is_children_static_question",
    "resolve_children_archetype",
]


def resolve_children_archetype(
    question: str,
    *,
    llm_archetype: str | None = None,
    interpretation: str = "",
) -> tuple[str, str]:
    q = (question or "").strip()
    interp = (interpretation or "").strip()

    regex_arch = classify_children_archetype(q)
    detected = detect_children_archetype(q) or detect_children_archetype(interp)

    llm = (llm_archetype or "").strip().lower()
    if llm and llm in CHILDREN_ARCHETYPES:
        if detected and detected != llm:
            return detected, f"regex_override_llm:{llm}->{detected}"
        if regex_arch != "general_children" and regex_arch != llm:
            return regex_arch, f"regex_override_llm:{llm}->{regex_arch}"
        return llm, "llm_archetype"

    if detected:
        return detected, "regex_detect"
    return regex_arch, "regex_classify"

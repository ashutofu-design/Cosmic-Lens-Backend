"""Luck archetype routing — question patterns beat LLM mis-routes."""

from __future__ import annotations

from .classifier import classify_luck_archetype
from .luck_registry import LUCK_ARCHETYPES, detect_luck_archetype, is_luck_static_question

__all__ = [
    "LUCK_ARCHETYPES",
    "classify_luck_archetype",
    "detect_luck_archetype",
    "is_luck_static_question",
    "resolve_luck_archetype",
]


def resolve_luck_archetype(
    question: str,
    *,
    llm_archetype: str | None = None,
    interpretation: str = "",
) -> tuple[str, str]:
    q = (question or "").strip()
    detected = detect_luck_archetype(q) or detect_luck_archetype(interpretation)
    regex_arch = classify_luck_archetype(q)

    llm = (llm_archetype or "").strip().lower()
    if llm and llm in LUCK_ARCHETYPES:
        if detected and detected != llm:
            return detected, f"regex_override_llm:{llm}->{detected}"
        if regex_arch != "general_luck" and regex_arch != llm:
            return regex_arch, f"regex_override_llm:{llm}->{regex_arch}"
        return llm, "llm_archetype"

    if detected:
        return detected, "regex_detect"
    return regex_arch, "regex_classify"

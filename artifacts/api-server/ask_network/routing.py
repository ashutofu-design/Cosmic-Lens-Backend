"""Network archetype routing — regex beats LLM general mis-route."""

from __future__ import annotations

from .classifier import classify_network_archetype
from .network_registry import NETWORK_ARCHETYPES, detect_network_archetype, is_network_static_question

__all__ = [
    "NETWORK_ARCHETYPES",
    "classify_network_archetype",
    "detect_network_archetype",
    "is_network_static_question",
    "resolve_network_archetype",
]


def resolve_network_archetype(
    question: str,
    *,
    llm_archetype: str | None = None,
    interpretation: str = "",
) -> tuple[str, str]:
    q = (question or "").strip()
    detected = detect_network_archetype(q) or detect_network_archetype(interpretation)
    regex_arch = classify_network_archetype(q)

    llm = (llm_archetype or "").strip().lower()
    if llm and llm in NETWORK_ARCHETYPES:
        if detected and detected != llm:
            return detected, f"regex_override_llm:{llm}->{detected}"
        if regex_arch != "general_network" and regex_arch != llm:
            return regex_arch, f"regex_override_llm:{llm}->{regex_arch}"
        return llm, "llm_archetype"

    if detected:
        return detected, "regex_detect"
    return regex_arch, "regex_classify"

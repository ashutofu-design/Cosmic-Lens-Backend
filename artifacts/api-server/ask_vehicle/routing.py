"""Vehicle archetype routing — question patterns beat LLM mis-routes."""
from __future__ import annotations

from .classifier import classify_vehicle_archetype
from .vehicle_registry import VEHICLE_ARCHETYPES, detect_vehicle_archetype, is_vehicle_static_question

__all__ = [
    "VEHICLE_ARCHETYPES",
    "classify_vehicle_archetype",
    "detect_vehicle_archetype",
    "is_vehicle_static_question",
    "resolve_vehicle_archetype",
    "vehicle_overrides_property",
]


def vehicle_overrides_property(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    return bool(is_vehicle_static_question(q))


def resolve_vehicle_archetype(
    question: str,
    *,
    llm_archetype: str | None = None,
    interpretation: str = "",
) -> tuple[str, str]:
    q = (question or "").strip()
    interp = (interpretation or "").strip()
    regex_arch = classify_vehicle_archetype(q)
    detected = detect_vehicle_archetype(q) or detect_vehicle_archetype(interp)
    llm = (llm_archetype or "").strip().lower()
    if llm and llm in VEHICLE_ARCHETYPES:
        if detected and detected != llm:
            return detected, f"regex_override_llm:{llm}->{detected}"
        if regex_arch != "general_vehicle" and regex_arch != llm:
            return regex_arch, f"regex_override_llm:{llm}->{regex_arch}"
        return llm, "llm_archetype"
    if detected:
        return detected, "regex_detected"
    return regex_arch, "regex_default"

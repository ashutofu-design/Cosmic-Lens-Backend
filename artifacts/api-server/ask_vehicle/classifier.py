from __future__ import annotations

from .vehicle_registry import (
    VEHICLE_ARCHETYPES,
    detect_vehicle_archetype,
    is_vehicle_static_question,
)

__all__ = [
    "classify_vehicle_archetype",
    "is_vehicle_static_question",
]


def classify_vehicle_archetype(question: str) -> str:
    q = (question or "").strip().lower()
    if not q:
        return "general_vehicle"
    found = detect_vehicle_archetype(q)
    if found:
        return found
    return "general_vehicle"

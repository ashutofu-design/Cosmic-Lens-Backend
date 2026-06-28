from __future__ import annotations

from .travel_registry import (
    TRAVEL_ARCHETYPES,
    detect_travel_archetype,
    is_travel_static_question,
)

__all__ = [
    "classify_travel_archetype",
    "is_travel_static_question",
]


def classify_travel_archetype(question: str) -> str:
    q = (question or "").strip().lower()
    if not q:
        return "general_travel"

    found = detect_travel_archetype(q)
    if found:
        return found
    return "general_travel"

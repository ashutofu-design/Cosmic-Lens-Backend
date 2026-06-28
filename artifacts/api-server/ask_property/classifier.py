from __future__ import annotations

from .property_registry import (
    PROPERTY_ARCHETYPES,
    detect_property_archetype,
    is_property_static_question,
)

__all__ = [
    "classify_property_archetype",
    "is_property_static_question",
]


def classify_property_archetype(question: str) -> str:
    q = (question or "").strip().lower()
    if not q:
        return "general_property"

    found = detect_property_archetype(q)
    if found:
        return found
    return "general_property"

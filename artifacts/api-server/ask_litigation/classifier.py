from __future__ import annotations

from .litigation_registry import (
    LITIGATION_ARCHETYPES,
    detect_litigation_archetype,
    is_litigation_static_question,
)

__all__ = [
    "classify_litigation_archetype",
    "is_litigation_static_question",
]


def classify_litigation_archetype(question: str) -> str:
    q = (question or "").strip().lower()
    if not q:
        return "general_litigation"

    found = detect_litigation_archetype(q)
    if found:
        return found
    return "general_litigation"

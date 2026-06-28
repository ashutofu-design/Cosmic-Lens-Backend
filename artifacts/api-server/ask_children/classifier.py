from __future__ import annotations

from .children_registry import (
    CHILDREN_ARCHETYPES,
    detect_children_archetype,
    is_children_static_question,
)

__all__ = [
    "classify_children_archetype",
    "is_children_static_question",
]


def classify_children_archetype(question: str) -> str:
    q = (question or "").strip().lower()
    if not q:
        return "general_children"

    found = detect_children_archetype(q)
    if found:
        return found
    return "general_children"

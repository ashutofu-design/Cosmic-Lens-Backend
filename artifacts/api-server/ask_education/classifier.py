from __future__ import annotations

import re

from .education_registry import (
    EDUCATION_ARCHETYPES,
    detect_education_archetype,
    is_education_static_question,
)

__all__ = [
    "classify_education_archetype",
    "is_education_static_question",
]


def classify_education_archetype(question: str) -> str:
    q = (question or "").strip().lower()
    if not q:
        return "general_education"

    found = detect_education_archetype(q)
    if found:
        return found

    if re.search(
        r"(?ix)\b(padhai|education|study|exam|school|college|degree)\b",
        q,
    ):
        return "general_education"
    return "general_education"

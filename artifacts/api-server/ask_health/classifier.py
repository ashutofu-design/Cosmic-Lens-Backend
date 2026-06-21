from __future__ import annotations

import re

from .health_registry import (
    detect_health_archetype,
    is_health_static_question,
)

__all__ = [
    "classify_health_archetype",
    "is_health_static_question",
]


def classify_health_archetype(question: str) -> str:
    q = (question or "").strip().lower()
    if not q:
        return "general_health"

    found = detect_health_archetype(q)
    if found:
        return found

    if re.search(
        r"(?ix)\b(health|sehat|swasthya|tabiyat|bimari|beemar|body|sharir)\b",
        q,
    ):
        return "general_health"
    return "general_health"

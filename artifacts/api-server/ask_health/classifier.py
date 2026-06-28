from __future__ import annotations

import re

from health_focus_routing import detect_hard_guard

from .health_registry import (
    _HARD_GUARD_ARCH,
    detect_health_archetype,
    is_health_static_question,
)

__all__ = [
    "classify_health_archetype",
    "is_health_static_question",
]


def classify_health_archetype(question: str) -> str:
    q_raw = (question or "").strip()
    if not q_raw:
        return "general_health"
    q = q_raw.lower()

    hard = detect_hard_guard(q_raw)
    if hard:
        return _HARD_GUARD_ARCH.get(hard, "refuse_diagnosis")

    found = detect_health_archetype(q_raw)
    if found:
        return found

    if re.search(
        r"(?ix)\b(health|sehat|swasthya|tabiyat|bimari|beemar|body|sharir)\b",
        q,
    ):
        return "general_health"
    return "general_health"

from __future__ import annotations

from .luck_registry import detect_luck_archetype, is_luck_static_question

__all__ = ["classify_luck_archetype", "is_luck_static_question"]


def classify_luck_archetype(question: str) -> str:
    return detect_luck_archetype(question) or "general_luck"

from __future__ import annotations

from .network_registry import detect_network_archetype, is_network_static_question

__all__ = ["classify_network_archetype", "is_network_static_question"]


def classify_network_archetype(question: str) -> str:
    return detect_network_archetype(question) or "general_network"

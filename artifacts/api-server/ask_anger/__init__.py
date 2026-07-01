from __future__ import annotations

from .anger_registry import detect_anger_archetype, is_anger_static_question
from .engine import run_anger_static_engine

__all__ = [
    "detect_anger_archetype",
    "is_anger_static_question",
    "run_anger_static_engine",
]

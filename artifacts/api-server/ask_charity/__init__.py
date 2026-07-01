from __future__ import annotations

from .charity_registry import detect_charity_archetype, is_charity_static_question
from .engine import run_charity_static_engine

__all__ = [
    "detect_charity_archetype",
    "is_charity_static_question",
    "run_charity_static_engine",
]

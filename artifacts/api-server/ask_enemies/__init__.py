from __future__ import annotations

from .engine import run_enemies_static_engine
from .enemies_registry import detect_enemies_archetype, is_enemies_static_question

__all__ = [
    "detect_enemies_archetype",
    "is_enemies_static_question",
    "run_enemies_static_engine",
]

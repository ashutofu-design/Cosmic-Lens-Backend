from __future__ import annotations

from .engine import run_pets_static_engine
from .pets_registry import detect_pets_archetype, is_pets_static_question

__all__ = [
    "detect_pets_archetype",
    "is_pets_static_question",
    "run_pets_static_engine",
]

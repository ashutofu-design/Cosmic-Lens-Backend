from __future__ import annotations

from .dreams_registry import detect_dreams_archetype, is_dreams_static_question
from .engine import run_dreams_static_engine

__all__ = [
    "detect_dreams_archetype",
    "is_dreams_static_question",
    "run_dreams_static_engine",
]

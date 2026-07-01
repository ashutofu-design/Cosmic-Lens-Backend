from __future__ import annotations

from .engine import run_vastu_static_engine
from .vastu_registry import detect_vastu_archetype, is_vastu_static_question

__all__ = [
    "detect_vastu_archetype",
    "is_vastu_static_question",
    "run_vastu_static_engine",
]

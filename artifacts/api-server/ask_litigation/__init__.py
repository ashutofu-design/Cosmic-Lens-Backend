from __future__ import annotations

from .classifier import classify_litigation_archetype, is_litigation_static_question
from .engine import run_litigation_static_engine
from .types import EngineResult

__all__ = [
    "EngineResult",
    "classify_litigation_archetype",
    "is_litigation_static_question",
    "run_litigation_static_engine",
]

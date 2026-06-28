from __future__ import annotations

from .classifier import classify_property_archetype, is_property_static_question
from .engine import run_property_static_engine
from .types import EngineResult

__all__ = [
    "EngineResult",
    "classify_property_archetype",
    "is_property_static_question",
    "run_property_static_engine",
]

"""Ask: Friends / social circle / network static engine."""

from __future__ import annotations

from .classifier import classify_network_archetype, is_network_static_question
from .engine import run_network_static_engine
from .routing import resolve_network_archetype
from .timing_registry import classify_network_timing_bucket, is_network_timing_question
from .types import EngineResult

__all__ = [
    "EngineResult",
    "classify_network_archetype",
    "classify_network_timing_bucket",
    "is_network_static_question",
    "is_network_timing_question",
    "resolve_network_archetype",
    "run_network_static_engine",
]

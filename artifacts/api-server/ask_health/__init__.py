"""Ask: Health non-timing engine — deterministic evidence + LLM narrator."""

from .engine import run_health_static_engine
from .timing_registry import classify_health_timing_bucket, is_health_timing_question
from .types import EngineResult

__all__ = [
    "EngineResult",
    "classify_health_timing_bucket",
    "is_health_timing_question",
    "run_health_static_engine",
]

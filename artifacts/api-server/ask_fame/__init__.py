from __future__ import annotations



from .engine import run_fame_static_engine

from .fame_registry import detect_fame_archetype, is_fame_static_question

from .timing_registry import classify_fame_timing_bucket, is_fame_timing_question



__all__ = [

    "classify_fame_timing_bucket",

    "detect_fame_archetype",

    "is_fame_static_question",

    "is_fame_timing_question",

    "run_fame_static_engine",

]



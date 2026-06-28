"""
event_timing.career package
===========================
Career event timing — answers career/profession/job questions across
8 buckets (govt_job, promotion, resignation, transfer, career_setback,
job_change, career_field_choice, general_career).

Phase 2.8.35 (May 2 2026) — moved from `career_engine.py` (api-server
root) to `event_timing/career/` per user direction:
  "career engine me jo sab buckets he, woh pura move karo,
   event timing ke andar career ke andar"

Phase 2.8.36 (May 2 2026) — renamed `career_engine.py` → `career_timing.py`
per user direction (matches marriage_timing.py naming pattern):
  "career engine nehi career timing rename karo, uske andar jo
   buckets he all good"

Architecture mirrors `event_timing/marriage/` pattern:
  - career_timing.py   : full engine (4429 lines — 8 buckets, 5 conditionals,
                         32 layers, 3 triggers, 7 modifiers, dispatch tables,
                         orchestrator)

This __init__.py re-exports the 3 PUBLIC FUNCTIONS that openai_helper.py
imports, so backward compatibility is fully preserved:
  - assess_career(kundli, intel, kp, birth, question, ...)  -> dict
  - format_verdict_for_prompt(v, question)                  -> str
  - classify_career_question(text, pre_classified_bucket)   -> str

Usage from openai_helper:
  from event_timing.career import (
      assess_career,
      format_verdict_for_prompt,
      classify_career_question,
  )
"""

from .career_timing import (
    assess_career,
    build_career_timing_engine_trace,
    build_career_timing_step_audit,
    classify_career_question,
    format_verdict_for_prompt,
)
from .govt_job_engine_v1 import (
    assess_govt_job,
    assess_govt_job_promise,
    format_govt_job_block_for_prompt,
)
from .promotion_engine_v1 import (
    assess_promotion,
    assess_promotion_promise,
    format_promotion_block_for_prompt,
)
from .resignation_engine_v1 import (
    assess_resignation,
    assess_resignation_viability,
    format_resignation_block_for_prompt,
)
from .field_choice_engine_v1 import (
    assess_field_choice,
    format_field_choice_block_for_prompt,
)
from .general_career_engine_v1 import (
    assess_general_career,
    format_general_career_block_for_prompt,
)
from .job_change_engine_v1 import (
    assess_job_change,
    format_job_change_block_for_prompt,
)
from .setback_engine_v1 import (
    assess_setback,
    format_setback_block_for_prompt,
)
from .transfer_engine_v1 import (
    assess_transfer,
    format_transfer_block_for_prompt,
)

__all__ = [
    "assess_career",
    "assess_field_choice",
    "assess_general_career",
    "assess_govt_job",
    "assess_govt_job_promise",
    "assess_job_change",
    "assess_promotion",
    "assess_promotion_promise",
    "assess_resignation",
    "assess_resignation_viability",
    "assess_setback",
    "assess_transfer",
    "build_career_timing_engine_trace",
    "build_career_timing_step_audit",
    "format_field_choice_block_for_prompt",
    "format_general_career_block_for_prompt",
    "format_govt_job_block_for_prompt",
    "format_job_change_block_for_prompt",
    "format_promotion_block_for_prompt",
    "format_resignation_block_for_prompt",
    "format_setback_block_for_prompt",
    "format_transfer_block_for_prompt",
    "format_verdict_for_prompt",
    "classify_career_question",
]

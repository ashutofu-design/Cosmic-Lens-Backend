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

Architecture mirrors `event_timing/marriage/` pattern:
  - career_engine.py   : full engine (4429 lines — 8 buckets, 5 conditionals,
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

from .career_engine import (
    assess_career,
    format_verdict_for_prompt,
    classify_career_question,
)

__all__ = [
    "assess_career",
    "format_verdict_for_prompt",
    "classify_career_question",
]

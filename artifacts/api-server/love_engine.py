"""
love_engine.py — delegates to love_static_engine_v1 + love_timing_engine_v1.

Preserves openai_helper imports: assess_love, format_verdict_for_prompt,
extract_window_str, classify_love_question, LOVE_TONE_RULES.
"""
from __future__ import annotations

from typing import Any, Optional

from event_timing.love.love_static_engine_v1 import (
    LOVE_TONE_RULES,
    assess_love_static,
    classify_love_static_bucket,
    format_love_static_for_prompt,
)
from event_timing.love.love_timing_engine_v1 import classify_love_timing_bucket


def classify_love_question(text: str, *args: Any, **kwargs: Any) -> str:
    pre = kwargs.get("pre_classified_bucket")
    return classify_love_static_bucket(text, pre)


def assess_love(
    kundli: dict,
    intel: dict,
    kp: dict,
    birth: Any,
    question: str = "",
    *args: Any,
    **kwargs: Any,
) -> dict:
    pre = kwargs.get("pre_classified_bucket")
    return assess_love_static(
        kundli, intel, kp, birth, question,
        pre_classified_bucket=pre,
    )


def format_verdict_for_prompt(verdict: dict, *args: Any, **kwargs: Any) -> str:
    if not verdict:
        return ""
    if verdict.get("timing_engine"):
        from event_timing.love.love_timing_engine_v1 import format_love_timing_for_prompt
        te = verdict.get("timing_engine")
        if isinstance(te, dict):
            return format_love_timing_for_prompt(te)
    return format_love_static_for_prompt(verdict)


def extract_window_str(verdict: dict, *args: Any, **kwargs: Any) -> str:
    if not isinstance(verdict, dict):
        return ""
    w = verdict.get("window") or ""
    if w:
        return str(w)
    te = verdict.get("timing_engine") or {}
    t = te.get("timing") or {}
    rec = t.get("recommended_window") or {}
    if rec.get("start_label") and rec.get("end_label"):
        return f"{rec['start_label']} → {rec['end_label']}"
    return ""


__all__ = [
    "LOVE_TONE_RULES",
    "classify_love_question",
    "assess_love",
    "format_verdict_for_prompt",
    "extract_window_str",
]

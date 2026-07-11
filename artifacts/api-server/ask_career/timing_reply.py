"""Career timing locked replies — delegates to shared timing_window_pick."""
from __future__ import annotations

from typing import Any

from event_timing._shared.timing_window_pick import (
    compose_timing_locked_reply as _compose_generic,
    detect_next_timing_window_question,
    pick_timing_answer_window,
    promotion_locked_window_label,
    window_dates_present_in_text,
)

# Back-compat alias
detect_career_timing_constraint = detect_next_timing_window_question


def pick_promotion_answer_window(
    verdict: dict[str, Any],
    question: str = "",
    history: Any = None,
) -> dict[str, Any] | None:
    return pick_timing_answer_window(verdict, question, history)


def compose_promotion_timing_reply(
    verdict: dict[str, Any],
    question: str = "",
    *,
    lang: str = "hn",
    history: Any = None,
) -> str:
    text = _compose_generic(
        verdict, question, topic="promotion", lang=lang, history=history,
    )
    if text:
        return text
    pw = str(verdict.get("primary_window") or "").strip()
    if pw:
        return f"Promotion ka strong window {pw} ke beech dikhta hai."
    return "Abhi chart se promotion ka clear timing window nahi dikh raha."


def try_promotion_timing_deterministic_reply(
    verdict: dict[str, Any],
    question: str = "",
    *,
    lang: str = "hn",
    history: Any = None,
) -> str | None:
    if str(verdict.get("bucket") or "").strip().lower() != "promotion":
        return None
    w = pick_timing_answer_window(verdict, question, history)
    if not w and not str(verdict.get("primary_window") or "").strip():
        return None
    return compose_promotion_timing_reply(verdict, question, lang=lang, history=history)


__all__ = [
    "detect_career_timing_constraint",
    "pick_promotion_answer_window",
    "promotion_locked_window_label",
    "compose_promotion_timing_reply",
    "try_promotion_timing_deterministic_reply",
    "window_dates_present_in_text",
]

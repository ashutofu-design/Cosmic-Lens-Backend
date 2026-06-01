"""TIMING vs STATIC gate — AI-only (ask_cosmo.understand_question).

No regex classification. On AI failure → STATIC (conservative).
"""

from __future__ import annotations

from typing import Any, Literal

_QType = Literal["TIMING", "STATIC"]

_LAST_DECISION_REASON: str = "init"


def _gate_enabled() -> bool:
    """Kept for callers; always uses AI when this module classifies."""
    return True


def timing_from_understanding(u: dict | None) -> bool:
    if not isinstance(u, dict):
        return False
    intent = str(u.get("intent") or "").lower().strip()
    archetype = str(u.get("archetype") or "").upper().strip()
    ranked = [str(x).lower() for x in (u.get("intents_ranked") or []) if x]
    timeframe = str(u.get("timeframe") or "none").lower().strip()

    if intent == "timing":
        return True
    if archetype == "TIMING":
        return True
    if ranked and ranked[0] == "timing":
        return True
    if ranked[:2] and "timing" in ranked[:2] and timeframe in ("near", "mid", "far"):
        return True
    return False


def classify_question_type(
    question: str,
    *,
    client: Any = None,
    understanding: dict | None = None,
) -> _QType:
    global _LAST_DECISION_REASON

    u = understanding
    if u is None:
        if not isinstance(question, str) or not question.strip():
            _LAST_DECISION_REASON = "empty_or_non_str"
            return "STATIC"
        try:
            from ask_cosmo import understand_question

            u = understand_question(question, client=client)
        except Exception as exc:
            _LAST_DECISION_REASON = f"ai_unavailable:{exc.__class__.__name__}"
            return "STATIC"

    if timing_from_understanding(u):
        _LAST_DECISION_REASON = (
            f"ai:{u.get('intent')}:{u.get('source', 'ai')}"
        )
        return "TIMING"

    _LAST_DECISION_REASON = f"ai_static:{u.get('intent')}:{u.get('source', 'ai')}"
    return "STATIC"


def is_timing(question: str, **kwargs: Any) -> bool:
    return classify_question_type(question, **kwargs) == "TIMING"


def slim_understanding_payload(u: dict | None) -> dict | None:
    if not isinstance(u, dict):
        return None
    return {
        "intent": u.get("intent"),
        "topic": u.get("topic"),
        "archetype": u.get("archetype"),
        "intents_ranked": u.get("intents_ranked"),
        "timeframe": u.get("timeframe"),
        "cleaned_q": u.get("cleaned_q"),
        "source": u.get("source"),
        "confidence": u.get("confidence"),
    }


__all__ = [
    "classify_question_type",
    "timing_from_understanding",
    "is_timing",
    "slim_understanding_payload",
    "_gate_enabled",
    "_LAST_DECISION_REASON",
]

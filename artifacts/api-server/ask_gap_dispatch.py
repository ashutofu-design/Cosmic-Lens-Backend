"""Ordered dispatch for small Ask gap static engines."""

from __future__ import annotations

from typing import Any, Callable, Optional

from ask_mr.types import EngineResult

# First match wins — more specific domains before broad ones.
_GAP_ORDER: list[tuple[str, str, Callable, Callable, str, str]] = [
    # key, slice, is_fn, run_fn, topic, check_flag
    ("siblings", "siblings_engine_v1", None, None, "siblings", "is_siblings_static"),
    ("spiritual", "spiritual_engine_v1", None, None, "spiritual", "is_spiritual_static"),
    ("parents", "parents_engine_v1", None, None, "parents", "is_parents_static"),
    ("enemies", "enemies_engine_v1", None, None, "enemies", "is_enemies_static"),
    ("fame", "fame_engine_v1", None, None, "fame", "is_fame_static"),
    ("personality", "personality_engine_v1", None, None, "personality", "is_personality_static"),
    ("dreams", "dreams_engine_v1", None, None, "dreams", "is_dreams_static"),
    ("anger", "anger_engine_v1", None, None, "anger", "is_anger_static"),
    ("remedy", "remedy_engine_v1", None, None, "remedy", "is_remedy_static"),
    ("charity", "charity_engine_v1", None, None, "charity", "is_charity_static"),
    ("settlement", "settlement_engine_v1", None, None, "settlement", "is_settlement_static"),
    ("vastu", "vastu_engine_v1", None, None, "vastu", "is_vastu_static"),
    ("pets", "pets_engine_v1", None, None, "pets", "is_pets_static"),
    ("wellness", "wellness_engine_v1", None, None, "wellness", "is_wellness_static"),
]


def _lazy_imports() -> list[tuple[str, str, Callable, Callable, str, str]]:
    from ask_anger import is_anger_static_question, run_anger_static_engine
    from ask_charity import is_charity_static_question, run_charity_static_engine
    from ask_dreams import is_dreams_static_question, run_dreams_static_engine
    from ask_enemies import is_enemies_static_question, run_enemies_static_engine
    from ask_fame.fame_registry import is_fame_static_question
    from ask_fame.engine import run_fame_static_engine
    from ask_parents import is_parents_static_question, run_parents_static_engine
    from ask_personality import is_personality_static_question, run_personality_static_engine
    from ask_pets import is_pets_static_question, run_pets_static_engine
    from ask_remedy import is_remedy_static_question, run_remedy_static_engine
    from ask_settlement import is_settlement_static_question, run_settlement_static_engine
    from ask_siblings import is_siblings_static_question, run_siblings_static_engine
    from ask_spiritual.spiritual_registry import is_spiritual_static_question
    from ask_spiritual.engine import run_spiritual_static_engine
    from ask_vastu import is_vastu_static_question, run_vastu_static_engine
    from ask_wellness import is_wellness_static_question, run_wellness_static_engine

    return [
        ("siblings", "siblings_engine_v1", is_siblings_static_question, run_siblings_static_engine, "siblings", "is_siblings_static"),
        ("spiritual", "spiritual_engine_v1", is_spiritual_static_question, run_spiritual_static_engine, "spiritual", "is_spiritual_static"),
        ("parents", "parents_engine_v1", is_parents_static_question, run_parents_static_engine, "parents", "is_parents_static"),
        ("enemies", "enemies_engine_v1", is_enemies_static_question, run_enemies_static_engine, "enemies", "is_enemies_static"),
        ("fame", "fame_engine_v1", is_fame_static_question, run_fame_static_engine, "fame", "is_fame_static"),
        ("personality", "personality_engine_v1", is_personality_static_question, run_personality_static_engine, "personality", "is_personality_static"),
        ("dreams", "dreams_engine_v1", is_dreams_static_question, run_dreams_static_engine, "dreams", "is_dreams_static"),
        ("anger", "anger_engine_v1", is_anger_static_question, run_anger_static_engine, "anger", "is_anger_static"),
        ("charity", "charity_engine_v1", is_charity_static_question, run_charity_static_engine, "charity", "is_charity_static"),
        ("remedy", "remedy_engine_v1", is_remedy_static_question, run_remedy_static_engine, "remedy", "is_remedy_static"),
        ("settlement", "settlement_engine_v1", is_settlement_static_question, run_settlement_static_engine, "settlement", "is_settlement_static"),
        ("vastu", "vastu_engine_v1", is_vastu_static_question, run_vastu_static_engine, "vastu", "is_vastu_static"),
        ("pets", "pets_engine_v1", is_pets_static_question, run_pets_static_engine, "pets", "is_pets_static"),
        ("wellness", "wellness_engine_v1", is_wellness_static_question, run_wellness_static_engine, "wellness", "is_wellness_static"),
    ]


def detect_gap_static_key(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> Optional[str]:
    for key, _, is_fn, _, _, _ in _lazy_imports():
        try:
            if is_fn(question or "", llm_intent):
                return key
        except Exception:
            continue
    return None


def is_any_gap_static_question(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> bool:
    return detect_gap_static_key(question, llm_intent) is not None


def run_gap_static_engine(
    kundli: dict,
    question: str,
    *,
    llm_intent: dict[str, Any] | None = None,
    wants_explain: bool = False,
    forced_key: str | None = None,
) -> Optional[tuple[EngineResult, str, str, str]]:
    """Return (result, slice_id, topic, gap_key) or None."""
    for key, slice_id, is_fn, run_fn, topic, _flag in _lazy_imports():
        if forced_key and key != forced_key:
            continue
        if not forced_key:
            try:
                if not is_fn(question or "", llm_intent):
                    continue
            except Exception:
                continue
        try:
            result = run_fn(
                kundli if isinstance(kundli, dict) else {},
                question or "",
                wants_explain=wants_explain,
            )
            return result, slice_id, topic, key
        except Exception:
            continue
    return None


def gap_static_to_meta(
    result: EngineResult,
    *,
    slice_id: str,
    topic: str,
) -> dict[str, Any]:
    from ask_mr.engine import mr_engine_slice_meta

    meta = mr_engine_slice_meta(result)
    meta["slice"] = slice_id
    meta["topic"] = topic
    return meta

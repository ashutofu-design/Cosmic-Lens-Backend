"""Stream ask history + admin context rebuild tests."""
from __future__ import annotations


def test_love_life_static_admin_context():
    from ask_llm_context_debug import build_admin_context_for_ask_save

    ctx = build_admin_context_for_ask_save(
        question="mere love life me issue he kya",
        result={"topic": "general", "text": "test answer", "source": "ai_passthrough_stream"},
    )
    assert ctx.get("question") == "mere love life me issue he kya"
    assert ctx.get("is_timing") is False
    sm = ctx.get("slice_meta") or {}
    assert sm.get("slice") in ("marriage_relationship", "mr_engine_v1")
    assert ctx.get("question") in str(ctx.get("understanding_line") or ctx.get("question"))


def test_fame_static_admin_context():
    from ask_fame.fame_registry import is_fame_static_question
    from ask_fame.timing_registry import is_fame_timing_question
    from ask_llm_context_debug import build_admin_context_for_ask_save

    q = "kya mere life me name fame he"
    assert is_fame_timing_question(q) is False
    assert is_fame_static_question(q) is True

    ctx = build_admin_context_for_ask_save(
        question=q,
        result={"topic": "general", "text": "test", "source": "ai_passthrough_stream"},
    )
    assert ctx.get("question") == q
    assert ctx.get("is_timing") is False
    sm = ctx.get("slice_meta") or {}
    assert sm.get("slice") == "fame_engine_v1"
    assert sm.get("topic") == "fame"


def test_persist_ask_question_result_defined():
    from question_history import persist_ask_question_result, save_stream_ask_question

    assert callable(persist_ask_question_result)
    assert callable(save_stream_ask_question)

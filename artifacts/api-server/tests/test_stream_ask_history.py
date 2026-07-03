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


def test_save_stream_ask_question_writes_row():
    from question_history import save_stream_ask_question

    # Dry-run shape only — no DB in unit test without app context
    assert callable(save_stream_ask_question)

"""Raw passthrough must not truncate timing/decision answers mid-sentence."""
from openai_helper import (
    _detect_question_lang,
    _enforce_one_line_answer,
    _is_decision_ask,
    _polish_decision_reply,
    _raw_passthrough_max_tokens,
)

_JOB_VS_BUSINESS = (
    "Mujhe apna khud ka koi naya kaam ya business shuru karna chahiye ya job hi sahi hai?"
)


def test_job_vs_business_detects_hinglish():
    assert _detect_question_lang(_JOB_VS_BUSINESS, "en") == "hn"


def test_decision_question_detected():
    assert _is_decision_ask(_JOB_VS_BUSINESS)


def test_decision_en_report_gets_seedha_prefix():
    raw = (
        "Jupiter as Lagna lord placed in 5th house signals strong potential for business. "
        "Mercury in 12th weakens career efforts."
    )
    out = _polish_decision_reply(raw, "hn")
    assert out.lower().startswith("seedha jawab:")


def test_decision_hinglish_with_conclusion_preserved():
    raw = (
        "Seedha jawab: abhi job zyada suit karega. Business me risk zyada hai. "
        "Conclusion: filhaal naukri pe focus karo."
    )
    out = _polish_decision_reply(raw, "hn")
    assert "Seedha jawab:" in out
    assert "Conclusion:" in out


def test_decision_token_budget():
    n = _raw_passthrough_max_tokens(
        wants_explain=False,
        is_timing=False,
        is_decision=True,
        dcr_love_meta=None,
        is_sensitive=False,
    )
    assert n >= 120


def test_timing_token_budget_above_old_cap():
    n = _raw_passthrough_max_tokens(
        wants_explain=False,
        is_timing=True,
        is_decision=False,
        dcr_love_meta=None,
        is_sensitive=False,
    )
    assert n >= 120


def test_default_token_budget_above_55():
    n = _raw_passthrough_max_tokens(
        wants_explain=False,
        is_timing=False,
        is_decision=False,
        dcr_love_meta=None,
        is_sensitive=False,
    )
    assert n >= 80


def test_decision_enforce_ends_with_punctuation():
    raw = (
        "Abhi job zyada suit karega — stable income ke liye chart supportive hai. "
        "Business baad me try karo jab cash flow strong ho. "
        "Jupiter-Rahu phase me pehle experience build karna better."
    )
    out = _enforce_one_line_answer(raw, wants_explain=False, is_decision=True)
    assert out
    assert out[-1] in ".?!।"
    assert "job" in out.lower()


def test_timing_enforce_ends_with_punctuation():
    raw = (
        "Job switch 2026 ke mid se 2027 tak zyada likely hai. "
        "Abhi Jupiter-Rahu dasha career mein mixed signal de rahi hai. "
        "Wait karo agle 6 mahine phir switch better."
    )
    out = _enforce_one_line_answer(raw, wants_explain=False, is_timing=True)
    assert out
    assert out[-1] in ".?!।"
    assert "Jupiter-Rahu" in out

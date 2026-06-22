"""Career timing routing tests."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_career.classifier import is_career_static_question
from ask_career.timing_registry import (
    apply_age_context_to_verdict,
    assess_career_age_context,
    classify_career_timing_bucket,
    is_career_question,
    is_career_timing_question,
    parse_age_from_question,
    should_defer_career_timing,
)


def test_job_kab_is_timing_not_static():
    q = "Job kab lagegi?"
    assert is_career_timing_question(q)
    assert is_career_question(q)
    assert not is_career_static_question(q)


def test_promotion_bucket():
    assert classify_career_timing_bucket("Promotion kab hoga?") == "promotion"


def test_age_65_reframe():
    age = parse_age_from_question("Main 65 saal ka hun, job kab lagega?")
    assert age == 65
    ctx = assess_career_age_context(age, "job kab lagega?")
    assert ctx["retirement_phase"] is True
    assert ctx["reframe_bucket"] == "late_career_reemployment"


def test_age_guard_in_verdict():
    v = {"bucket": "general_career", "brand_safety_warnings": ["base"]}
    ctx = assess_career_age_context(65, "naukri kab milegi?")
    out = apply_age_context_to_verdict(v, ctx)
    assert out.get("age_reframe") == "late_career_reemployment"
    assert any("retirement" in w.lower() or "late-career" in w.lower() for w in out["brand_safety_warnings"])


def test_stock_deferred():
    q = "Nifty intraday kab kharidu?"
    assert should_defer_career_timing(q)
    assert not is_career_timing_question(q)


def test_govt_job_timing():
    q = "Sarkari naukri kab milegi?"
    assert is_career_timing_question(q)
    assert classify_career_timing_bucket(q) == "govt_job"


def test_phase59_career_gate_import():
    from openai_helper import _is_career_question, _phase59_format_career_facts_block, _phase59_is_career_question

    assert _phase59_is_career_question("Promotion kab hoga?")
    block = _phase59_format_career_facts_block({
        "bucket": "promotion",
        "tense": "future",
        "verdict": "yellow_wait",
        "score": 42,
        "confidence": 75,
        "strategy": "Manager se baat karein.",
        "brand_safety_warnings": ["No guarantee."],
        "reasons": ["10th lord strong"],
    })
    assert "CAREER_FACTS:" in block
    assert "promotion" in block
    assert _is_career_question("Job kab lagegi?")

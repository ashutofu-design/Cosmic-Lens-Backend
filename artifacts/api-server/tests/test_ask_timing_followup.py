"""Timing follow-up scope + merge tests."""
import pytest

from ask_scope_gate import assess_ask_scope
from ask_timing_followup import (
    is_timing_refine_followup,
    merge_timing_followup_question,
    resolve_timing_followup_question,
)


def test_exact_month_followup_allowed():
    v = assess_ask_scope("Exact month batao kab change hoga")
    assert v.allowed, v.reason


def test_timing_refine_detected():
    assert is_timing_refine_followup("Exact month batao kab change hoga")
    assert is_timing_refine_followup("Kis mahine switch karna sahi hoga")


def test_resolve_merges_prior_career_question():
    history = [
        {"role": "user", "text": "Mera job change kab hoga"},
        {
            "role": "assistant",
            "text": "4-6 mahine ruk jaayein — abhi switch risky hai.",
        },
    ]
    eff, is_fu = resolve_timing_followup_question(
        "Exact month batao kab change hoga",
        history,
    )
    assert is_fu
    assert "job change" in eff.lower()
    assert "exact month" in eff.lower()


def test_merge_preserves_original():
    merged = merge_timing_followup_question(
        "Mera job change kab hoga",
        "Exact month batao",
    )
    assert merged.startswith("Mera job change")
    assert "Exact month" in merged


@pytest.mark.parametrize(
    "question",
    [
        "who invented astrology",
        "biryani recipe batao",
    ],
)
def test_gk_still_blocked(question):
    v = assess_ask_scope(question)
    assert not v.allowed

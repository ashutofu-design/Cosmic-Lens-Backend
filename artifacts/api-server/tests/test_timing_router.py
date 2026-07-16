"""Unified timing router tests."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.domain_specs import DOMAIN_TIMING_SPECS, list_domains_by_status
from event_timing.timing_router import (
    build_timing_demand,
    detect_timing_intent,
    resolve_timing_domain,
)


def test_all_domains_have_spec():
    assert len(DOMAIN_TIMING_SPECS) >= 10
    for dom in ("marriage", "career", "travel", "love", "property"):
        assert dom in DOMAIN_TIMING_SPECS
        assert DOMAIN_TIMING_SPECS[dom].get("houses")


def test_travel_settlement_routing():
    dom, bucket, is_t = resolve_timing_domain("Foreign settlement kab hoga?")
    assert is_t
    assert dom == "travel"


def test_travel_visa_pr_routing():
    for q in ("Videsh kab jaunga?", "Visa kab milega?", "PR kab milega?", "Abroad shift kab hoga?"):
        dom, _, is_t = resolve_timing_domain(q)
        assert is_t, q
        assert dom == "travel", q


def test_education_timing_routing():
    for q in ("Exam result kab aayega?", "Admission kab hogi?"):
        dom, _, is_t = resolve_timing_domain(q)
        assert is_t, q
        assert dom == "education", q


def test_finance_timing_routing():
    dom, _, is_t = resolve_timing_domain("Paisa kab aayega?")
    assert is_t
    assert dom == "finance"
    dom2, _, _ = resolve_timing_domain(
        "Paisa kab aayega?",
        {"domain": "finance", "is_timing": True},
    )
    assert dom2 == "finance"


def test_love_marriage_defer():
    dom, _, is_t = resolve_timing_domain("Love marriage kab hogi?")
    assert is_t
    assert dom == "marriage"


def test_marriage_event_routing():
    for q in ("engagement kab hoga?", "rishta pakka hona kab milega?", "roka kab hogi?"):
        dom, _, is_t = resolve_timing_domain(q)
        assert is_t, q
        assert dom == "marriage", q


def test_career_timing():
    dom, _, is_t = resolve_timing_domain("Promotion kab hoga?")
    assert is_t
    assert dom == "career"


def test_overlapping_timing_topics_use_correct_engine():
    cases = {
        "Teerthyatra kab hoga?": "spiritual",
        "Bade log help kab karenge?": "network",
        "Lottery kab lagegi?": "universal",
        "Pet dog kab adopt karun?": "universal",
    }
    for question, expected in cases.items():
        domain, _, is_timing = resolve_timing_domain(question)
        assert is_timing, question
        assert domain == expected, question


def test_static_not_timing():
    assert not detect_timing_intent("Kaunsi industry best rahegi?")
    assert not detect_timing_intent("Biwi kaisi hogi?")
    assert not detect_timing_intent("Travel yog strong hai?")


def test_static_spouse_not_timing_route():
    dom, _, is_t = resolve_timing_domain("Biwi kaisi hogi?")
    assert not is_t
    assert not detect_timing_intent("Biwi kaisi hogi?")


def test_demand_build():
    d = build_timing_demand("Job kab lagegi?", {"domain": "career", "is_timing": True})
    assert d.is_timing
    assert d.domain == "career"


def test_ready_engines_list():
    ready = list_domains_by_status("ready")
    for dom in ("marriage", "career", "travel", "property", "education", "litigation", "love", "spiritual"):
        assert dom in ready, f"{dom} should be ready"

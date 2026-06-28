"""Tests for vehicle static engine + routing."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_vehicle import classify_vehicle_archetype, is_vehicle_static_question, run_vehicle_static_engine
from event_timing.property_routing_audit import classify_engine_family
from vehicle_static.vehicle_engine import compute_vehicle_facts


_MIN_KUNDLI = {
    "ascendant": "Taurus",
    "planets": [
        {"name": "Sun", "house": 10, "sign": "Aquarius"},
        {"name": "Moon", "house": 4, "sign": "Leo"},
        {"name": "Mars", "house": 7, "sign": "Scorpio"},
        {"name": "Mercury", "house": 9, "sign": "Capricorn"},
        {"name": "Jupiter", "house": 11, "sign": "Pisces"},
        {"name": "Venus", "house": 1, "sign": "Taurus"},
        {"name": "Saturn", "house": 3, "sign": "Cancer"},
        {"name": "Rahu", "house": 6, "sign": "Libra"},
        {"name": "Ketu", "house": 12, "sign": "Aries"},
    ],
}


@pytest.mark.parametrize(
    "question,expected_arch",
    [
        (
            "Mere liye car ka kaun sa colour (safed, kala, lal, silver) sabs shubh rahega?",
            "vehicle_colour",
        ),
        (
            "Kya mujhe brand new car leni chahiye ya shuruat me second-hand gaadi se kaam chalana chahiye?",
            "vehicle_new_used",
        ),
        (
            "Kya mujhe electric vehicle (EV) leni chahiye ya petrol/diesel hi sahi rahegi?",
            "vehicle_ev",
        ),
        (
            "Gaadi ka loan easily pass ho jayega ya down payment zyada deni padegi?",
            "vehicle_loan",
        ),
    ],
)
def test_vehicle_static_routing(question: str, expected_arch: str) -> None:
    assert is_vehicle_static_question(question)
    assert classify_engine_family(question) == "vehicle_static"
    assert classify_vehicle_archetype(question) == expected_arch


def test_vehicle_static_engine_runs() -> None:
    facts = compute_vehicle_facts(_MIN_KUNDLI)
    dims = facts.get("dimensions") or {}
    assert "colour" in dims
    assert dims["colour"].get("best")
    result = run_vehicle_static_engine(
        _MIN_KUNDLI,
        "Mere liye car ka kaun sa colour shubh rahega?",
        archetype="vehicle_colour",
    )
    assert result.archetype == "vehicle_colour"
    assert result.verdict
    assert len(result.evidence) >= 4


def test_vehicle_colour_has_chart_tone_disclaimer() -> None:
    result = run_vehicle_static_engine(
        _MIN_KUNDLI,
        "Mere liye car ka kaun sa colour shubh rahega?",
        archetype="vehicle_colour",
    )
    assert "Chart-tone advisory" in result.verdict or any(
        "Chart-tone" in s for s in (result.summary or [])
    )


def test_property_sale_tax_archetype() -> None:
    from ask_property import classify_property_archetype, run_property_static_engine

    q = "Property bechne ke baad jo paisa aayega, use kahan invest karun taaki income tax na lage?"
    assert classify_property_archetype(q) == "property_sale_tax"
    result = run_property_static_engine(_MIN_KUNDLI, q, archetype="property_sale_tax")
    assert result.archetype == "property_sale_tax"
    assert "CA" in result.verdict or any("CA" in s for s in (result.summary or []))


def test_vehicle_timing_not_static() -> None:
    q = "Main apni pehli car/bike kab tak khareed paunga?"
    assert not is_vehicle_static_question(q)
    assert classify_engine_family(q) == "vehicle_timing"

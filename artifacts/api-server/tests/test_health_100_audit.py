"""100-question health routing audit."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.health.health_engine_v1 import compute_health_window
from event_timing.health_routing_audit import classify_health_routing, family_label
from event_timing.timing_router import resolve_timing_domain
from tests.health_100_cases import QUESTIONS

_MIN_KUNDLI = {
    "ascendant": "Leo",
    "planets": [
        {"name": "Sun", "house": 1, "sign": "Leo"},
        {"name": "Moon", "house": 4, "sign": "Scorpio"},
        {"name": "Mars", "house": 6, "sign": "Capricorn"},
        {"name": "Mercury", "house": 2, "sign": "Virgo"},
        {"name": "Jupiter", "house": 5, "sign": "Sagittarius"},
        {"name": "Venus", "house": 3, "sign": "Libra"},
        {"name": "Saturn", "house": 8, "sign": "Aquarius"},
        {"name": "Rahu", "house": 12, "sign": "Gemini"},
        {"name": "Ketu", "house": 6, "sign": "Sagittarius"},
    ],
    "dashas": [{
        "lord": "Jupiter", "start": "2020-01-01", "end": "2036-01-01",
        "subDashas": [{
            "lord": "Saturn", "start": "2024-01-01", "end": "2027-01-01",
            "pratyantar": [{"lord": "Mars", "start": "2025-01-01", "end": "2025-06-01"}],
        }],
    }],
}

ACCEPTABLE = frozenset({
    "health_timing_v1",
    "health_static",
    "health_hard_guard",
    "health_llm",
    "cross_domain:finance",
    "cross_domain:property",
    "cross_domain:career",
    "cross_domain:children",
    "cross_domain:foreign_education",
    "cross_domain:love",
    "hard_guard:REFUSE_DEATH",
    "hard_guard:REFUSE_DIAGNOSIS",
    "hard_guard:REFUSE_CURE_GUARANTEE",
})


@pytest.mark.parametrize("question,category", QUESTIONS)
def test_health_100_routes(question: str, category: str) -> None:
    lab = family_label(classify_health_routing(question))
    assert lab == "health_timing_v1" or lab in ACCEPTABLE or lab.startswith(
        ("static:", "hard_guard:", "cross_domain:", "health_")
    ), f"{lab}: {question[:70]}"


def test_health_100_coverage() -> None:
    hits = sum(
        1 for q, _ in QUESTIONS
        if family_label(classify_health_routing(q)) == "health_timing_v1"
    )
    static = sum(
        1 for q, _ in QUESTIONS
        if family_label(classify_health_routing(q)).startswith("static:")
    )
    hard = sum(
        1 for q, _ in QUESTIONS
        if family_label(classify_health_routing(q)).startswith("hard_guard:")
    )
    cross = sum(
        1 for q, _ in QUESTIONS
        if family_label(classify_health_routing(q)).startswith("cross_domain:")
    )
    llm = sum(
        1 for q, _ in QUESTIONS
        if family_label(classify_health_routing(q)) == "llm"
    )
    engine_covered = hits + static + hard + cross
    assert hits >= 60, f"timing {hits}/100 (need 60+)"
    assert llm == 0, f"llm {llm}/100 (want 0)"
    assert engine_covered == 100, f"engine coverage {engine_covered}/100"


def test_health_timing_engine_runs() -> None:
    r = compute_health_window(_MIN_KUNDLI)
    assert r.get("verdict")
    assert r.get("engine_version") or r.get("factors")


def test_sample_recovery_routes_timing() -> None:
    q = "Mere pet ki samasya kab tak theek hogi?"
    dom, bkt, is_t = resolve_timing_domain(q)
    assert is_t and dom == "health"

"""100-question litigation routing audit."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.litigation.litigation_timing_v1 import compute_litigation_window
from event_timing.litigation_routing_audit import classify_litigation_routing, family_label
from event_timing.timing_router import resolve_timing_domain
from tests.litigation_100_cases import QUESTIONS

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
        "lord": "Saturn", "start": "2020-01-01", "end": "2039-01-01",
        "subDashas": [{
            "lord": "Mars", "start": "2024-01-01", "end": "2027-01-01",
            "pratyantar": [{"lord": "Mercury", "start": "2025-01-01", "end": "2025-06-01"}],
        }],
    }],
}

ACCEPTABLE = frozenset({
    "litigation_timing_v1",
    "cross_domain:property",
    "cross_domain:marriage",
    "cross_domain:career",
    "cross_domain:finance",
    "hard_guard:REFUSE_DEATH_PENALTY",
})


@pytest.mark.parametrize("question,category", QUESTIONS)
def test_litigation_100_routes(question: str, category: str) -> None:
    lab = family_label(classify_litigation_routing(question))
    assert lab == "litigation_timing_v1" or lab in ACCEPTABLE or lab.startswith(
        ("static:", "hard_guard:", "cross_domain:")
    ), f"{lab}: {question[:70]}"


def test_litigation_100_coverage() -> None:
    hits = sum(
        1 for q, _ in QUESTIONS
        if family_label(classify_litigation_routing(q)) == "litigation_timing_v1"
    )
    static = sum(
        1 for q, _ in QUESTIONS
        if family_label(classify_litigation_routing(q)).startswith("static:")
    )
    cross = sum(
        1 for q, _ in QUESTIONS
        if family_label(classify_litigation_routing(q)).startswith("cross_domain:")
    )
    llm = sum(
        1 for q, _ in QUESTIONS
        if family_label(classify_litigation_routing(q)) == "llm"
    )
    assert hits >= 55, f"timing={hits} static={static} cross={cross} llm={llm}"
    assert llm == 0, f"LLM gaps={llm}"


def test_litigation_timing_engine_smoke() -> None:
    dom, bucket, is_timing = resolve_timing_domain("Bail kab milegi?")
    assert dom == "litigation" and is_timing
    out = compute_litigation_window(_MIN_KUNDLI, question="Bail kab milegi?", bucket=bucket)
    assert out.get("domain") == "litigation"
    assert out.get("bucket") == "bail_theme"

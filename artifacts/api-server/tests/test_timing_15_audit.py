"""Parametrized audit — 15 timing / non-timing questions."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.timing_router import resolve_timing_domain, run_timing_engine

_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Sun", "house": 10, "sign": "Virgo"},
        {"name": "Moon", "house": 5, "sign": "Aries"},
        {"name": "Mars", "house": 8, "sign": "Cancer"},
        {"name": "Mercury", "house": 5, "sign": "Aries"},
        {"name": "Jupiter", "house": 1, "sign": "Sagittarius"},
        {"name": "Venus", "house": 11, "sign": "Libra"},
        {"name": "Saturn", "house": 3, "sign": "Aquarius"},
        {"name": "Rahu", "house": 11, "sign": "Libra"},
        {"name": "Ketu", "house": 5, "sign": "Aries"},
    ],
    "dashas": [
        {
            "lord": "Sun",
            "start": "2020-01-01",
            "end": "2026-01-01",
            "subDashas": [
                {
                    "lord": "Rahu",
                    "start": "2024-06-01",
                    "end": "2027-02-01",
                    "subDashas": [
                        {"lord": "Jupiter", "start": "2025-01-01", "end": "2025-08-01"},
                    ],
                },
            ],
        },
    ],
}

_KP = {
    "cusps": [{"house": 10, "subLord": "Sun"}, {"house": 11, "subLord": "Rahu"}],
    "significations": {
        "Sun": {"pl": [10], "sb_houses": [10]},
        "Rahu": {"pl": [11], "sb_houses": [11]},
    },
}

CASES = [
    ("Shaadi kab hogi?", "marriage", True),
    ("Mera content kab viral hoga?", "fame", True),
    ("Bade log meri help kab karenge?", "network", True),
    ("Guru kab milega?", "spiritual", True),
    ("Promotion kab milega?", "career", True),
    ("Videsh kab jaunga?", "travel", True),
    ("Ghar kab kharidunga?", "property", True),
    ("Bail kab milegi?", "litigation", True),
    ("Bachcha kab hoga?", "children", True),
    ("Lottery kab lagegi?", "universal", True),
    ("Pet dog kab adopt karun?", "universal", True),
    ("Pyaar kab milega?", "love", True),
    ("College admission kab hoga?", "education", True),
    ("Biwi kaisi hogi?", "general", False),
    ("Meri kundli kaisi hai?", "general", False),
]


@pytest.mark.parametrize("question,exp_domain,exp_timing", CASES)
def test_timing_15_routing(question: str, exp_domain: str, exp_timing: bool) -> None:
    dom, _, is_t = resolve_timing_domain(question)
    assert is_t == exp_timing, question
    if exp_timing:
        assert dom == exp_domain, f"{question} got {dom}"


@pytest.mark.parametrize(
    "question,exp_domain",
    [(q, d) for q, d, t in CASES if t],
)
def test_timing_15_engine_ready(question: str, exp_domain: str) -> None:
    ctx = run_timing_engine(question, _KUNDLI, {}, _KP, None)
    assert ctx.demand.domain == exp_domain
    assert ctx.engine_status == "ready", f"{question} status={ctx.engine_status}"
    assert ctx.verdict, f"{question} missing verdict"
    if exp_domain != "marriage":
        assert ctx.raw.get("dual_track"), f"{question} missing dual_track"
        assert ctx.raw.get("promise_check"), f"{question} missing promise_check"

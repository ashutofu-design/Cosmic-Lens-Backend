"""Tests — spiritual growth & occult timing (8H/9H/12H, Ketu/Guru)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_spiritual import classify_spiritual_timing_bucket, is_spiritual_timing_question
from event_timing.spiritual.spiritual_timing_v1 import (
    compute_spiritual_window,
    format_spiritual_timing_for_prompt,
)
from event_timing.timing_router import resolve_timing_domain, run_timing_engine

_MIN_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Sun", "house": 9, "sign": "Leo"},
        {"name": "Moon", "house": 12, "sign": "Scorpio"},
        {"name": "Mars", "house": 8, "sign": "Libra"},
        {"name": "Mercury", "house": 5, "sign": "Aries"},
        {"name": "Jupiter", "house": 1, "sign": "Sagittarius"},
        {"name": "Venus", "house": 11, "sign": "Libra"},
        {"name": "Saturn", "house": 3, "sign": "Aquarius"},
        {"name": "Rahu", "house": 4, "sign": "Pisces"},
        {"name": "Ketu", "house": 10, "sign": "Virgo"},
    ],
    "dashas": [
        {
            "lord": "Jupiter",
            "start": "2020-01-01",
            "end": "2036-01-01",
            "subDashas": [
                {
                    "lord": "Ketu",
                    "start": "2024-06-01",
                    "end": "2027-02-01",
                    "subDashas": [
                        {"lord": "Jupiter", "start": "2025-01-01", "end": "2025-08-01"},
                        {"lord": "Venus", "start": "2025-08-01", "end": "2026-03-01"},
                    ],
                },
            ],
        },
    ],
}

CASES = [
    (
        "Mera sahi guru meri life me kab aayega?",
        "spiritual",
        "guru_deeksha",
    ),
    (
        "Deeksha kab milegi?",
        "spiritual",
        "guru_deeksha",
    ),
    (
        "Astrology aur tarot kab seekh paunga?",
        "spiritual",
        "occult_learning",
    ),
    (
        "Occult sciences kab seekh paungi?",
        "spiritual",
        "occult_learning",
    ),
    (
        "Mera teerthyatra kab hoga?",
        "spiritual",
        "pilgrimage",
    ),
    (
        "Religious travel kab hoga?",
        "spiritual",
        "pilgrimage",
    ),
    (
        "Meditation aur inner peace kab milegi?",
        "spiritual",
        "inner_peace",
    ),
    (
        "Mental restlessness kab khatam hogi?",
        "spiritual",
        "inner_peace",
    ),
    (
        "Mera mukti kab hoga",
        "spiritual",
        "general_spiritual",
    ),
]


@pytest.mark.parametrize("question,domain,bucket", CASES)
def test_spiritual_routing(question: str, domain: str, bucket: str) -> None:
    assert is_spiritual_timing_question(question)
    assert classify_spiritual_timing_bucket(question) == bucket
    dom, bkt, is_timing = resolve_timing_domain(question)
    assert is_timing, question
    assert dom == domain, question
    assert bkt == bucket, question


def test_spiritual_engine_runs() -> None:
    result = compute_spiritual_window(
        _MIN_KUNDLI,
        question="Guru kab milega?",
        bucket="guru_deeksha",
    )
    assert result.get("domain") == "spiritual"
    assert result.get("verdict")
    assert result.get("verdict") != "UNKNOWN"
    factors = " ".join(result.get("factors") or [])
    assert "Ketu" in factors or "Jupiter" in factors or "9L" in factors or "12L" in factors


def test_spiritual_router_engine_wiring() -> None:
    ctx = run_timing_engine(
        "Deeksha kab milegi?",
        _MIN_KUNDLI,
        {},
        {},
        None,
    )
    assert ctx.demand.domain == "spiritual"
    assert ctx.engine_status == "ready"
    block = format_spiritual_timing_for_prompt(ctx.raw or {})
    assert "SPIRITUAL TIMING ENGINE" in block


def test_spiritual_not_foreign_travel() -> None:
    dom, _, is_t = resolve_timing_domain("Videsh kab jaunga?")
    assert is_t
    assert dom == "travel"

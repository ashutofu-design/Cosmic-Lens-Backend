"""Tests — social image, fame & recognition timing (1H/5H/10H, Sun/Rahu)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_fame import classify_fame_timing_bucket, is_fame_timing_question
from event_timing.fame.fame_timing_v1 import (
    compute_fame_window,
    format_fame_timing_for_prompt,
)
from event_timing.timing_router import resolve_timing_domain, run_timing_engine

_MIN_KUNDLI = {
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
                        {"lord": "Sun", "start": "2025-08-01", "end": "2026-03-01"},
                    ],
                },
            ],
        },
    ],
}

CASES = [
    (
        "Mujhe name fame aur social media par recognition kab milega?",
        "fame",
        "social_fame",
    ),
    (
        "Mera content kab viral hoga?",
        "fame",
        "social_fame",
    ),
    (
        "Celebrity yoga kab trigger hoga?",
        "fame",
        "social_fame",
    ),
    (
        "Mujhe national award kab milega?",
        "fame",
        "awards",
    ),
    (
        "International recognition kab milegi?",
        "fame",
        "awards",
    ),
    (
        "Meri khoyi hui reputation kab theek hogi?",
        "fame",
        "reputation_recovery",
    ),
    (
        "Log mere baare me galat sochna kab band karenge?",
        "fame",
        "reputation_recovery",
    ),
    (
        "Defamation se bad name kab theek hoga?",
        "fame",
        "reputation_recovery",
    ),
    (
        "Politics me entry kab hogi?",
        "fame",
        "politics_leadership",
    ),
    (
        "Leadership position kab milegi?",
        "fame",
        "politics_leadership",
    ),
]


@pytest.mark.parametrize("question,domain,bucket", CASES)
def test_fame_routing(question: str, domain: str, bucket: str) -> None:
    assert is_fame_timing_question(question)
    assert classify_fame_timing_bucket(question) == bucket
    dom, bkt, is_timing = resolve_timing_domain(question)
    assert is_timing, question
    assert dom == domain, question
    assert bkt == bucket, question


def test_fame_engine_runs() -> None:
    result = compute_fame_window(
        _MIN_KUNDLI,
        question="Fame kab milega?",
        bucket="social_fame",
    )
    assert result.get("domain") == "fame"
    assert result.get("verdict")
    assert result.get("verdict") != "UNKNOWN"
    assert result.get("moon_tenth_house") == 2  # Moon in 5H → 10th from Moon = 2H
    factors = " ".join(result.get("factors") or [])
    assert "Sun" in factors or "Rahu" in factors or "10L" in factors or "1L" in factors
    assert "10th-from-Moon" in factors


def test_fame_dasha_kp_sync() -> None:
    result = compute_fame_window(_MIN_KUNDLI, bucket="social_fame")
    assert result.get("dasha_running_now")
    assert "kp_dasha_sync" in result


def test_fame_router_engine_wiring() -> None:
    ctx = run_timing_engine(
        "Mera content kab viral hoga?",
        _MIN_KUNDLI,
        {},
        {},
        None,
    )
    assert ctx.demand.domain == "fame"
    assert ctx.engine_status == "ready"
    block = format_fame_timing_for_prompt(ctx.raw or {})
    assert "FAME & RECOGNITION TIMING ENGINE" in block


def test_reputation_not_litigation_without_court() -> None:
    dom, bkt, is_t = resolve_timing_domain(
        "Meri khoyi hui reputation kab theek hogi?",
    )
    assert is_t
    assert dom == "fame"
    assert bkt == "reputation_recovery"


def test_fame_not_career_job() -> None:
    dom, _, is_t = resolve_timing_domain("Promotion kab milega?")
    assert is_t
    assert dom == "career"

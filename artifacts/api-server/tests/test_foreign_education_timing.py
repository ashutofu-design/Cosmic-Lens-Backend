"""Tests — foreign education / travel timing (5H/9H/12H, Rahu/Guru)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_foreign_education import classify_foreign_education_bucket, is_foreign_education_timing_question
from event_timing.foreign_education.foreign_education_timing_v1 import (
    compute_foreign_education_window,
)
from event_timing.timing_router import resolve_timing_domain

_MIN_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Sun", "house": 9, "sign": "Leo"},
        {"name": "Moon", "house": 5, "sign": "Aries"},
        {"name": "Mars", "house": 3, "sign": "Aquarius"},
        {"name": "Mercury", "house": 10, "sign": "Virgo"},
        {"name": "Jupiter", "house": 1, "sign": "Sagittarius"},
        {"name": "Venus", "house": 11, "sign": "Libra"},
        {"name": "Saturn", "house": 12, "sign": "Scorpio"},
        {"name": "Rahu", "house": 12, "sign": "Scorpio"},
        {"name": "Ketu", "house": 6, "sign": "Taurus"},
    ],
    "dashas": [
        {
            "lord": "Jupiter",
            "start": "2020-01-01",
            "end": "2036-01-01",
            "subDashas": [
                {
                    "lord": "Rahu",
                    "start": "2024-06-01",
                    "end": "2027-02-01",
                    "pratyantar": [
                        {
                            "lord": "Jupiter",
                            "start": "2025-01-01",
                            "end": "2025-08-01",
                        }
                    ],
                }
            ],
        }
    ],
}

CASES = [
    (
        "Higher studies (College/Degree) ke liye admission kab milega?",
        "foreign_education",
        "admission",
    ),
    (
        "Competitive exam ka result kab aayega aur selection kab hoga?",
        "foreign_education",
        "exam_selection",
    ),
    (
        "Foreign visa kab approve hoga?",
        "foreign_education",
        "visa",
    ),
    (
        "PR (Permanent Residency) ya green card kab milega?",
        "foreign_education",
        "pr_residency",
    ),
    (
        "Permanent foreign settlement kab hoga?",
        "foreign_education",
        "settlement",
    ),
]


@pytest.mark.parametrize("question,domain,bucket", CASES)
def test_foreign_education_routing(question: str, domain: str, bucket: str) -> None:
    assert is_foreign_education_timing_question(question)
    assert classify_foreign_education_bucket(question) == bucket
    dom, bkt, is_timing = resolve_timing_domain(question)
    assert is_timing
    assert dom == domain
    assert bkt == bucket


def test_foreign_education_engine_runs() -> None:
    result = compute_foreign_education_window(
        _MIN_KUNDLI,
        question="Foreign visa kab approve hoga?",
        bucket="visa",
    )
    assert result.get("domain") == "foreign_education" or result.get("bucket") == "visa"
    assert result.get("verdict")
    factors = " ".join(result.get("factors") or [])
    assert "Rahu" in factors or "Jupiter" in factors or "9H" in factors or "12H" in factors

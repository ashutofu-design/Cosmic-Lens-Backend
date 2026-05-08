"""Tests for kp_marriage_promise."""
from vedic.compat.kp_marriage_promise import (
    compute_kp_marriage_promise, compute_kp_couple_promise,
)

_VALID_BANDS = ("STRONG", "PARTIAL", "WEAK", "UNAVAILABLE")


def _k():
    return {
        "ascendant": "Leo",
        "ascendantLongitude": 130.0,
        "planets": [
            {"name": "Sun", "sign": "Cancer", "longitude": 95.5},
            {"name": "Moon", "sign": "Aries", "longitude": 12.4},
            {"name": "Venus", "sign": "Taurus", "longitude": 45.0},
            {"name": "Jupiter", "sign": "Sagittarius", "longitude": 255.0},
        ],
    }


def test_single_returns_promise_band():
    out = compute_kp_marriage_promise(_k())
    assert out.get("verdict") in _VALID_BANDS


def test_couple_returns_pair_and_couple_verdict():
    out = compute_kp_couple_promise(_k(), _k())
    assert "p1" in out and "p2" in out and "couple_verdict" in out
    assert out["couple_verdict"] in _VALID_BANDS


def test_never_raises_on_empty_input():
    out = compute_kp_marriage_promise({})
    assert out.get("verdict") in _VALID_BANDS

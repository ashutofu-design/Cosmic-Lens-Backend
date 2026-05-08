"""Tests for synastry_7l compute_synastry_7l."""
from vedic.compat.synastry_7l import compute_synastry_7l


def _k(asc, planets):
    return {"ascendant": asc, "planets": planets}


def test_returns_required_shape():
    k1 = _k("Leo", [
        {"name": "Saturn", "sign": "Capricorn", "longitude": 280.0},
        {"name": "Venus", "sign": "Taurus", "longitude": 45.0},
        {"name": "Jupiter", "sign": "Sagittarius", "longitude": 255.0},
    ])
    k2 = _k("Aquarius", [
        {"name": "Sun", "sign": "Pisces", "longitude": 340.0},
        {"name": "Venus", "sign": "Aries", "longitude": 25.0},
        {"name": "Jupiter", "sign": "Leo", "longitude": 140.0},
    ])
    out = compute_synastry_7l(k1, k2)
    assert "score_0_10" in out
    assert 0 <= float(out["score_0_10"]) <= 10


def test_never_raises_on_empty_input():
    out = compute_synastry_7l({}, {})
    assert "score_0_10" in out

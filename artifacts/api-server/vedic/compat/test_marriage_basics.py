"""Tests for deterministic marriage_basics engine."""
from __future__ import annotations

from vedic.compat.marriage_basics import compute_marriage_basics, normalize_gender


def _sample_kundli(name: str, asc: str, moon_h: int = 4) -> dict:
    """Minimal kundli-shaped dict for unit tests."""
    asc_idx = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ].index(asc)
    planets = []
    for nm, sign_idx, house in [
        ("Sun", (asc_idx + 4) % 12, 5),
        ("Moon", (asc_idx + moon_h - 1) % 12, moon_h),
        ("Mars", asc_idx, 1),
        ("Mercury", (asc_idx + 2) % 12, 3),
        ("Jupiter", (asc_idx + 8) % 12, 9),
        ("Venus", (asc_idx + 6) % 12, 7),
        ("Saturn", (asc_idx + 9) % 12, 10),
    ]:
        planets.append({
            "name": nm,
            "sign": [
                "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
            ][sign_idx],
            "signIndex": sign_idx,
            "house": house,
            "longitude": sign_idx * 30.0 + 15.0,
            "degree_in_sign": 15.0,
        })
    d9_planets = []
    for p in planets:
        d9_planets.append({**p, "house": ((p["signIndex"] - asc_idx) % 12) + 1})
    return {
        "name": name,
        "ascendant": asc,
        "moonSign": planets[1]["sign"],
        "nakshatra": "Rohini",
        "planets": planets,
        "divisionalCharts": {
            "D9": {
                "ascendant": asc,
                "ascendantSignIndex": asc_idx,
                "planets": d9_planets,
            },
        },
    }


def test_normalize_gender():
    assert normalize_gender("Male") == "male"
    assert normalize_gender("female") == "female"
    assert normalize_gender("") == "unknown"


def test_compute_marriage_basics_shape():
    k1 = _sample_kundli("Rahul", "Leo")
    k2 = _sample_kundli("Priya", "Cancer", moon_h=5)
    out = compute_marriage_basics(
        k1, k2,
        p1_name="Rahul", p2_name="Priya",
        p1_gender="Male", p2_gender="Female",
    )
    assert out["engine"] == "marriage_basics_v1"
    assert out["couple"]["structural_band"] in ("Promising", "Workable", "High Effort")
    assert "readiness_score" in out["p1"]
    assert "d1" in out["p1"]
    assert out["p1"]["d1"]["seventh_house_sign"]
    assert out["p1"]["karaka"]["primary"] == "Venus"
    assert out["p2"]["karaka"]["primary"] == "Jupiter"
    assert "friction" in out["p1"]
    assert "remedy" in out["p1"]
    assert out["p1"]["kp"]["verdict"] in ("STRONG", "PARTIAL", "WEAK", "UNAVAILABLE")

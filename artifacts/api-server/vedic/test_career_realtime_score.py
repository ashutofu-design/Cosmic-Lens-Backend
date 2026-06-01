"""Tests for career realtime score (natal + dasha + transits)."""
from vedic.career_realtime_score import (
    _dasha_component,
    _natal_component,
    apply_commercial_bonus,
    compute_career_realtime_score,
)


def _sample_planets_sag_asc():
    """Sagittarius ascendant — 10th is Virgo (Mercury lord)."""
    return [
        {"name": "Sun", "sign": "Leo", "house": 9},
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Mercury", "sign": "Virgo", "house": 10},
        {"name": "Jupiter", "sign": "Cancer", "house": 8},
        {"name": "Saturn", "sign": "Libra", "house": 11},
    ]


def test_dasha_includes_pratyantar():
    cd = {"maha": "Jupiter", "antar": "Mercury", "pratyantar": "Venus"}
    delta, reasons, breakdown = _dasha_component(cd)
    assert breakdown["pd_pts"] == 0  # Venus // 3
    assert breakdown["md_pts"] == 8
    assert breakdown["ad_pts"] == 3  # Mercury 6 // 2
    assert any("Pratyantar" in r for r in reasons)


def test_natal_mercury_in_10th_boosts():
    score, reasons = _natal_component(_sample_planets_sag_asc(), 8)
    assert score > 50
    assert any("10th" in r for r in reasons)


def test_commercial_bonus():
    s, note = apply_commercial_bonus(45, 22)
    assert s == 50
    assert note is not None
    s2, note2 = apply_commercial_bonus(45, 10)
    assert s2 == 45
    assert note2 is None


def test_compute_returns_score_context():
    kundli = {
        "currentDasha": {
            "maha": "Saturn",
            "antar": "Mercury",
            "pratyantar": "Mars",
            "endDate": "2027-03-01",
        },
        "divisionalCharts": {"D10": {"planets": []}},
    }
    out = compute_career_realtime_score(_sample_planets_sag_asc(), 8, kundli)
    assert 20 <= out["score"] <= 95
    assert out["trend"] in ("Good", "Average", "Risk")
    assert "score_context" in out
    assert "Saturn" in out["score_context"]
    assert out["dasha_breakdown"]["pd_pts"] == 1  # Mars 3 // 3

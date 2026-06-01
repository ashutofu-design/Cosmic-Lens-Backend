"""Wellness sensitivities — plain issues only."""
from vedic.life_specifics import _build_wellness_sensitivities_from_chart


def test_plain_issues_no_house_jargon():
    asc = 5  # Virgo → 6th Aquarius
    planets = [
        {"name": "Mars", "sign": "Aquarius", "house": 6},
        {"name": "Saturn", "sign": "Capricorn", "house": 3},
    ]
    lines = _build_wellness_sensitivities_from_chart(planets, asc)
    blob = " ".join(lines).lower()
    assert lines
    assert "6th house" not in blob
    assert "aspects" not in blob
    assert "lord" not in blob
    assert "inflamm" in blob or "mars" not in blob  # planet name not in output


def test_taurus_sixth_ketu_style():
    # Sagittarius asc → 6th Taurus, Ketu in 6, Venus lord in 1
    planets = [
        {"name": "Ketu", "sign": "Taurus", "house": 6},
        {"name": "Venus", "sign": "Sagittarius", "house": 1},
        {"name": "Sun", "sign": "Leo", "house": 9},
        {"name": "Mercury", "sign": "Aquarius", "house": 3},
        {"name": "Jupiter", "sign": "Gemini", "house": 7},
        {"name": "Rahu", "sign": "Scorpio", "house": 12},
    ]
    lines = _build_wellness_sensitivities_from_chart(planets, 8)
    assert any("throat" in x.lower() for x in lines)
    assert any("hidden" in x.lower() or "unexplained" in x.lower() for x in lines)
    assert all("6th" not in x.lower() for x in lines)

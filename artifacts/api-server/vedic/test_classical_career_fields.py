"""Classical career top-fields — D1 + D10 + AmK."""
from vedic.classical_career_fields import compute_classical_top_careers
from vedic.career_inclination_engine import ensure_planet_houses


def _sample_planets_sag_asc():
    asc = 8  # Sagittarius → 10th = Virgo, lord Mercury
    raw = [
        {"name": "Sun", "sign": "Capricorn", "house": 2, "degree": 12},
        {"name": "Moon", "sign": "Pisces", "house": 4, "degree": 8},
        {"name": "Mars", "sign": "Scorpio", "house": 12, "degree": 20},
        {"name": "Mercury", "sign": "Virgo", "house": 10, "degree": 25},
        {"name": "Jupiter", "sign": "Gemini", "house": 7, "degree": 18},
        {"name": "Venus", "sign": "Capricorn", "house": 2, "degree": 5},
        {"name": "Saturn", "sign": "Aquarius", "house": 3, "degree": 15},
    ]
    return ensure_planet_houses(raw, asc), asc


def test_mercury_in_10th_shows_tech_and_finance():
    planets, asc = _sample_planets_sag_asc()
    out = compute_classical_top_careers(planets, asc, None, top_n=4)
    fields = out.get("suitable_fields") or []
    labels = " ".join(f["field"] for f in fields).lower()
    assert "tech" in labels or "software" in labels
    assert "finance" in labels or "banking" in labels
    assert any("10th house" in (f.get("driver") or "").lower() for f in fields)


def test_classical_uses_tenth_lord_meta():
    planets, asc = _sample_planets_sag_asc()
    out = compute_classical_top_careers(planets, asc, None, top_n=3)
    assert out.get("tenth_lord_planet") == "Mercury"
    assert "Mercury" in (out.get("tenth_occupants") or [])


def test_empty_10th_falls_back_to_lord():
    asc = 8
    raw = [
        {"name": "Mercury", "sign": "Aquarius", "house": 3, "degree": 25},
        {"name": "Jupiter", "sign": "Gemini", "house": 7, "degree": 18},
    ]
    planets = ensure_planet_houses(raw, asc)
    out = compute_classical_top_careers(planets, asc, None, top_n=3)
    fields = out.get("suitable_fields") or []
    assert len(fields) >= 1
    assert any("10th lord" in (f.get("driver") or "").lower() for f in fields)


def test_d10_occupant_boosts_tech():
    planets, asc = _sample_planets_sag_asc()
    kundli = {
        "divisionalCharts": {
            "D10": {
                "ascendant": "Capricorn",
                "planets": [
                    {"name": "Mercury", "sign": "Libra", "degree": 18},
                    {"name": "Rahu", "sign": "Gemini", "degree": 10},
                ],
            }
        }
    }
    out = compute_classical_top_careers(planets, asc, kundli, top_n=5)
    summary = (out.get("classical_summary") or "").lower()
    assert "d10" in summary
    drivers = " ".join(f.get("driver", "") for f in out.get("suitable_fields") or []).lower()
    assert "d10" in drivers


def test_amatyakaraka_returned_when_karakas_available():
    planets, asc = _sample_planets_sag_asc()
    out = compute_classical_top_careers(planets, asc, None, top_n=4)
    assert out.get("amatyakaraka")


def test_dual_occupants_weight_primary_higher():
    asc = 8
    raw = [
        {"name": "Mercury", "sign": "Virgo", "house": 10, "degree": 28},
        {"name": "Saturn", "sign": "Virgo", "house": 10, "degree": 5},
        {"name": "Sun", "sign": "Gemini", "house": 7, "degree": 12},
        {"name": "Moon", "sign": "Pisces", "house": 4, "degree": 8},
        {"name": "Mars", "sign": "Scorpio", "house": 12, "degree": 20},
        {"name": "Jupiter", "sign": "Gemini", "house": 7, "degree": 18},
        {"name": "Venus", "sign": "Capricorn", "house": 2, "degree": 5},
    ]
    planets = ensure_planet_houses(raw, asc)
    out = compute_classical_top_careers(planets, asc, None, top_n=6)
    fields = out.get("suitable_fields") or []
    mercury_drivers = [
        f.get("driver", "")
        for f in fields
        if "mercury" in (f.get("driver") or "").lower()
    ]
    assert mercury_drivers
    assert any("primary" in d.lower() for d in mercury_drivers)

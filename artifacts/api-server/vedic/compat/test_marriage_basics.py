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
        "currentDasha": {
            "maha": "Jupiter",
            "antar": "Rahu",
            "startDate": "2025-01-01",
            "endDate": "2026-12-01",
        },
        "dashas": [
            {
                "planet": "Jupiter",
                "subDashas": [
                    {
                        "planet": "Rahu",
                        "startDate": "2025-01-01",
                        "endDate": "2026-12-01",
                    },
                    {
                        "planet": "Jupiter",
                        "startDate": "2026-12-01",
                        "endDate": "2028-06-01",
                    },
                ],
            },
        ],
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
    assert out["engine"] == "marriage_basics_v6"
    assert out["couple"]["structural_band"] in ("Promising", "Workable", "High Effort")
    assert "synastry" in out["couple"]
    assert "d9_sync" in out["couple"]
    assert "graha_maitri" in out["couple"]
    assert "dasha_timeline" in out["couple"]
    assert "manglik" in out["couple"]
    assert "couple_signals" in out["couple"]
    assert "readiness_score" in out["p1"]
    assert "d1" in out["p1"]
    assert out["p1"]["d1"]["seventh_house_sign"]
    assert "seventh_occupant_details" in out["p1"]["d1"]
    assert "manglik" in out["p1"]
    assert "dasha_timeline" in out["p1"]
    assert "critical_alerts" in out["p1"]
    assert "maraka_axis" in out["p1"]["d1"]
    assert "seventh_empty" in out["p1"]["d1"]
    assert "seventh_occupants" in out["p1"]["d9"]
    assert "detail" in out["p1"]["critical_alerts"]
    assert "kp_couple" in out["couple"]
    assert out["p1"]["karaka"]["primary"] == "Venus"
    assert out["p2"]["karaka"]["primary"] == "Jupiter"
    assert "friction" in out["p1"]
    assert "remedy" in out["p1"]
    assert out["p1"]["kp"]["verdict"] in ("STRONG", "PARTIAL", "WEAK", "UNAVAILABLE")


def test_weakened_benefic_when_dusthana_lord_in_seventh():
    """Jupiter in 7th for Capricorn asc rules 3rd + 12th — benefic effect should weaken."""
    k = _sample_kundli("Test", "Capricorn")
    planets = k["planets"]
    for p in planets:
        if p["name"] == "Jupiter":
            p["sign"] = "Cancer"
            p["signIndex"] = 3
            p["house"] = 7
        if p["name"] == "Venus":
            p["sign"] = "Aries"
            p["signIndex"] = 0
            p["house"] = 4
    out = compute_marriage_basics(
        k, _sample_kundli("Other", "Leo"),
        p1_name="Test", p2_name="Other",
        p1_gender="Male", p2_gender="Female",
    )
    occ = out["p1"]["d1"]["seventh_occupant_details"]
    jup = next(d for d in occ if d["planet"] == "Jupiter")
    assert jup["lordship_tier"] == "dusthana_lord"
    assert jup["effect"] == "weakened_benefic"
    assert jup["score_delta"] >= 2
    assert 12 in jup["dusthana_rules"]


def test_mutual_manglik_cancellation_when_both_have_dosh():
    k1 = _sample_kundli("A", "Aries")
    k2 = _sample_kundli("B", "Aries")
    for k in (k1, k2):
        for p in k["planets"]:
            if p["name"] == "Mars":
                p["house"] = 7
                p["sign"] = "Libra"
                p["signIndex"] = 6
    out = compute_marriage_basics(k1, k2, p1_name="A", p2_name="B", p1_gender="Male", p2_gender="Female")
    assert out["couple"]["manglik"]["mutual_cancellation"] is True
    assert out["p1"]["manglik"]["has_dosh"] is True
    assert out["p2"]["manglik"]["has_dosh"] is True


def test_synastry_block_available_for_valid_charts():
    k1 = _sample_kundli("Rahul", "Leo")
    k2 = _sample_kundli("Priya", "Cancer", moon_h=5)
    out = compute_marriage_basics(k1, k2, p1_name="Rahul", p2_name="Priya", p1_gender="Male", p2_gender="Female")
    assert out["couple"]["synastry"]["available"] is True
    assert out["couple"]["synastry"]["score_0_10"] is not None


def test_graha_maitri_in_couple_block():
    k1 = _sample_kundli("A", "Aries", moon_h=1)
    k2 = _sample_kundli("B", "Taurus", moon_h=1)
    out = compute_marriage_basics(k1, k2, p1_name="A", p2_name="B")
    gm = out["couple"]["graha_maitri"]
    assert gm["available"] is True
    assert gm["p1_moon_lord"] == "Mars"
    assert gm["p2_moon_lord"] == "Venus"


def test_dasha_timeline_has_stress_window():
    k1 = _sample_kundli("A", "Leo")
    out = compute_marriage_basics(k1, _sample_kundli("B", "Cancer"), p1_name="A", p2_name="B")
    tl = out["p1"]["dasha_timeline"]
    assert tl["available"] is True
    assert tl["current"]["antar"] == "Rahu"


def test_yogakaraka_saturn_taurus_7th():
    k = _sample_kundli("T", "Taurus", moon_h=1)
    for p in k["planets"]:
        if p["name"] == "Saturn":
            p["house"] = 7
            p["sign"] = "Scorpio"
            p["signIndex"] = 7
        if p["name"] == "Venus":
            p["house"] = 4
            p["sign"] = "Leo"
            p["signIndex"] = 4
    out = compute_marriage_basics(k, _sample_kundli("O", "Leo"), p1_name="T", p2_name="O")
    occ = out["p1"]["d1"]["seventh_occupant_details"]
    sat = next(d for d in occ if d["planet"] == "Saturn")
    assert sat["is_yogakaraka"] is True
    assert sat["effect"] in ("strong_benefic", "functional_benefic")


def test_aspect_orb_degrees_on_seventh():
    """7th aspects carry degree-based orb_weight (not legacy flat 0.55)."""
    k = _sample_kundli("T", "Leo")
    for p in k["planets"]:
        if p["name"] == "Saturn":
            p["house"] = 1
            p["sign"] = "Leo"
            p["signIndex"] = 4
            p["longitude"] = 4 * 30.0 + 14.0
        if p["name"] == "Venus":
            p["house"] = 7
            p["sign"] = "Aquarius"
            p["signIndex"] = 10
            p["longitude"] = 10 * 30.0 + 16.0
    out = compute_marriage_basics(k, _sample_kundli("O", "Cancer"), p1_name="T", p2_name="O")
    asp = [d for d in out["p1"]["d1"]["seventh_aspect_details"] if d["planet"] == "Saturn"]
    assert asp, "Saturn should aspect 7th from Leo asc"
    assert asp[0]["orb_weight"] in (0.5, 1.0)
    assert asp[0]["orb_weight"] != 0.55
    assert asp[0]["orb_degrees"] is not None


def test_maraka_second_eighth_occupants():
    k = _sample_kundli("M", "Aries")
    for p in k["planets"]:
        if p["name"] == "Saturn":
            p["house"] = 2
            p["sign"] = "Taurus"
            p["signIndex"] = 1
    out = compute_marriage_basics(k, _sample_kundli("O", "Leo"), p1_name="M", p2_name="O")
    maraka = out["p1"]["d1"]["maraka_axis"]
    assert "Saturn" in maraka["second_occupants"]
    assert any("2nd house occupied" in n for n in maraka["notes"])


def test_pada_yoni_in_couple_synastry():
    k1 = _sample_kundli("A", "Leo")
    k2 = _sample_kundli("B", "Cancer", moon_h=5)
    out = compute_marriage_basics(k1, k2, p1_name="A", p2_name="B")
    py = out["couple"]["synastry"]["pada_yoni"]
    assert py["available"] is True
    assert "p1_pada" in py
    assert "yoni_score" in py
    assert py["yoni_max"] == 4


def test_darakaraka_depth_fields():
    k1 = _sample_kundli("A", "Leo")
    k2 = _sample_kundli("B", "Cancer")
    out = compute_marriage_basics(k1, k2, p1_name="A", p2_name="B")
    dk = out["p1"]["darakaraka"]
    assert "aspects" in dk
    assert "conjunctions" in dk
    assert "d9" in dk


def test_marriage_signal_skips_structural_overlap():
    """7th-axis afflictions must not penalize twice (structural + signals)."""
    from vedic.compat.marriage_basics import _marriage_signal_adjustment, _signal_readiness_adjustment
    from vedic.love_reality.relationship_signals import PersonSignals

    sig = PersonSignals(
        name="Test",
        affliction_weight=33,
        seventh_lord_dusthana=True,
        saturn_on_7th=True,
        mars_on_7th=True,
    )
    old_adj = _signal_readiness_adjustment(sig)
    new_adj = _marriage_signal_adjustment(sig)
    assert old_adj <= -8
    assert new_adj >= old_adj
    assert new_adj >= -4

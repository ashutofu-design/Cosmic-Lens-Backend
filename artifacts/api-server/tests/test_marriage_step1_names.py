"""STEP 1/2 name-only marriage rules — user Dhanu-lagna chart."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from divisional_charts import compute_d9
from event_timing.marriage.marriage_spec_pipeline import (
    _is_dasha_target_candidate,
    _load_d9,
    _pool_from_step_names,
    _step3_merge,
    _step5_rank,
    marriage_step_names,
)

SIGNS_SHORT = [
    "Mesh", "Vrishabh", "Mithun", "Kark", "Simha", "Kanya",
    "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen",
]
EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
idx = {s: i for i, s in enumerate(SIGNS_SHORT)}

rows = [
    ("Sun", "Tula", 11.5, 11, False),
    ("Moon", "Mithun", 12.1, 7, False),
    ("Mars", "Dhanu", 15.0, 1, False),
    ("Mercury", "Vrishchik", 5.1, 12, False),
    ("Jupiter", "Mesh", 5.3, 5, True),
    ("Venus", "Simha", 25.0, 9, False),
    ("Saturn", "Mesh", 20.5, 5, True),
    ("Rahu", "Kark", 14.6, 8, True),
    ("Ketu", "Makar", 14.6, 2, True),
]

planets = []
for name, sign, deg, house, retro in rows:
    si = idx[sign]
    planets.append({
        "name": name,
        "sign": EN[si],
        "signIndex": si,
        "house": house,
        "longitude": si * 30 + deg,
        "retrograde": retro,
    })

LAGNA_SI = 8  # Dhanu


def test_step1_seventh_lord():
    s = marriage_step_names(planets, LAGNA_SI, "D1")
    assert s["seventh_lord"] == "Mercury"


def test_step1_in_7th_house():
    s = marriage_step_names(planets, LAGNA_SI, "D1")
    assert s["planets_in_7th_house"] == ["Moon"]


def test_step1_aspects_7th_house():
    s = marriage_step_names(planets, LAGNA_SI, "D1")
    assert set(s["planets_aspecting_7th_house"]) == {"Mars", "Saturn"}


def test_step1_with_7th_lord_empty():
    s = marriage_step_names(planets, LAGNA_SI, "D1")
    assert s["planets_conjunct_or_aspecting_7th_lord"] == []


def _kundli():
    return {
        "ascendantDeg": LAGNA_SI * 30 + 15.0,
        "planets": planets,
    }


def test_step2_seventh_lord():
    k = _kundli()
    d9, d9_lagna, d9_7l = _load_d9(k)
    s = marriage_step_names(planets, LAGNA_SI, "D9", d9_chart=d9, d9_lagna_si=d9_lagna)
    assert s["seventh_lord"] == "Mercury"
    assert d9_7l == "Mercury"


def test_step2_in_7th_house():
    k = _kundli()
    d9, d9_lagna, _ = _load_d9(k)
    s = marriage_step_names(planets, LAGNA_SI, "D9", d9_chart=d9, d9_lagna_si=d9_lagna)
    assert s["planets_in_7th_house"] == []


def test_step2_aspects_7th_house():
    k = _kundli()
    d9, d9_lagna, _ = _load_d9(k)
    s = marriage_step_names(planets, LAGNA_SI, "D9", d9_chart=d9, d9_lagna_si=d9_lagna)
    # BPHS D9: no graha aspects Mithun (7H) except universal 7th — none land on Gemini
    assert s["planets_aspecting_7th_house"] == []


def test_step2_with_7th_lord():
    k = _kundli()
    d9, d9_lagna, _ = _load_d9(k)
    s = marriage_step_names(planets, LAGNA_SI, "D9", d9_chart=d9, d9_lagna_si=d9_lagna)
    # Mercury (7L) & Mars both in Simha in D9 → Mars conjunct 7L
    assert s["planets_conjunct_or_aspecting_7th_lord"] == ["Mars"]


def test_step3_with_7l_link_now_gets_real_points():
    step = {
        "division": "D1",
        "seventh_lord": "Venus",
        "planets_in_7th_house": [],
        "planets_aspecting_7th_house": [],
        "planets_conjunct_or_aspecting_7th_lord": ["Mars"],
    }
    ps = [
        {"name": "Sun", "sign": "Aries", "house": 1},
        {"name": "Mars", "sign": "Capricorn", "house": 10},
    ]

    pool = _pool_from_step_names(step, planets=ps, lagna_si=0)

    assert pool["Mars"]["points"] > 0
    assert "conjunct/aspects D1 7th lord" in pool["Mars"]["links"]
    assert any("exalted" in n for n in pool["Mars"]["strength_notes"])


def test_step3_d9_and_overlap_bonus_are_stronger():
    d1_step = {
        "division": "D1",
        "seventh_lord": "Venus",
        "planets_in_7th_house": [],
        "planets_aspecting_7th_house": [],
        "planets_conjunct_or_aspecting_7th_lord": ["Mars"],
    }
    d9_step = {**d1_step, "division": "D9"}
    ps = [
        {"name": "Sun", "sign": "Aries", "house": 1},
        {"name": "Mars", "sign": "Capricorn", "house": 10},
    ]
    d1_pool = _pool_from_step_names(d1_step, planets=ps, lagna_si=0)
    d9_pool = _pool_from_step_names(
        d9_step,
        planets=ps,
        lagna_si=0,
        d9_chart={"Mars": {"sign_idx": 9}},
        d9_lagna_si=0,
    )

    merged = _step3_merge(d1_pool, d9_pool)

    assert d9_pool["Mars"]["points"] > d1_pool["Mars"]["points"]
    assert merged["Mars"]["both_bonus"] == 6
    assert merged["Mars"]["natal_points"] == (
        d1_pool["Mars"]["points"] + d9_pool["Mars"]["points"] + 6
    )


def test_step2_nodes_do_not_use_saturn_style_third_aspect_to_7h():
    step = marriage_step_names(
        planets=[],
        lagna_si=0,
        division="D9",
        d9_chart={"Ketu": {"sign_idx": 4}},  # 5H from Aries D9 lagna
        d9_lagna_si=0,
    )

    assert "Ketu" not in step["planets_aspecting_7th_house"]


def test_step5_kp_authority_can_outrank_raw_natal_points():
    merged = {
        "Mars": {"natal_points": 12, "d9_points": 0},
        "Moon": {"natal_points": 5, "d9_points": 0},
    }
    kp_details = {
        "Mars": {"kp_points": 0, "verdict": "DENIES"},
        "Moon": {"kp_points": 7, "verdict": "CONFIRMS"},
    }

    ranked = _step5_rank(merged, kp_details)

    assert ranked[0]["name"] == "Moon"
    assert ranked[0]["kp_weighted_points"] > ranked[0]["kp_points"]
    assert ranked[1]["kp_deny_penalty"] > 0


def test_step5_d9_priority_and_karaka_bonus_are_exposed():
    merged = {
        "Venus": {"natal_points": 8, "d9_points": 6},
        "Moon": {"natal_points": 8, "d9_points": 0},
    }
    kp_details = {
        "Venus": {"kp_points": 0, "verdict": "UNKNOWN"},
        "Moon": {"kp_points": 0, "verdict": "UNKNOWN"},
    }

    ranked = _step5_rank(merged, kp_details)
    venus = next(r for r in ranked if r["name"] == "Venus")

    assert venus["d9_priority_bonus"] > 0
    assert venus["karaka_bonus"] > 0
    assert ranked[0]["name"] == "Venus"


def test_step5_dasha_target_gate_filters_weak_noisy_planets():
    weak = {
        "name": "Mars",
        "score": 7.5,
        "kp_verdict": "UNKNOWN",
        "kp_points": 0,
        "both_divisions": False,
        "d9_points": 0,
    }
    strong = {
        "name": "Moon",
        "score": 9.0,
        "kp_verdict": "CONFIRMS",
        "kp_points": 4,
        "both_divisions": False,
        "d9_points": 0,
    }
    protected = {
        "name": "Venus",
        "score": 5.5,
        "kp_verdict": "UNKNOWN",
        "kp_points": 0,
        "both_divisions": False,
        "d9_points": 0,
    }
    denied = {
        "name": "Saturn",
        "score": 12.0,
        "kp_verdict": "DENIES",
        "kp_points": 0,
        "both_divisions": False,
        "d9_points": 0,
    }

    assert not _is_dasha_target_candidate(weak, d1_7l="Venus", d9_7l=None)
    assert _is_dasha_target_candidate(strong, d1_7l="Venus", d9_7l=None)
    assert _is_dasha_target_candidate(protected, d1_7l="Venus", d9_7l=None)
    assert not _is_dasha_target_candidate(denied, d1_7l="Venus", d9_7l=None)

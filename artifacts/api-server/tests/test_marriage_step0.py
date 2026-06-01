"""STEP 0 — BCP dual-sign + D1/D9 pace (Dhanu lagna user chart)."""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.marriage.bcp_marriage_ages import (
    _score_merged_bcp_ages,
    compute_bcp_for_division,
    compute_bcp_marriage_ages,
    resolve_late_marriage_bcp_focus,
)
from event_timing.marriage.marriage_step0 import (
    chart_marriage_pace_for_division,
    run_marriage_step0,
)
from event_timing.marriage.marriage_step0a import run_marriage_step0a

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
idx = {s: i for i, s in enumerate([
    "Mesh", "Vrishabh", "Mithun", "Kark", "Simha", "Kanya",
    "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen",
])}

planets = []
for name, sign, house in [
    ("Sun", "Tula", 11),
    ("Moon", "Mithun", 7),
    ("Mars", "Dhanu", 1),
    ("Mercury", "Vrishchik", 12),
    ("Jupiter", "Mesh", 5),
    ("Venus", "Simha", 9),
    ("Saturn", "Mesh", 5),
    ("Rahu", "Kark", 8),
    ("Ketu", "Makar", 2),
]:
    si = idx[sign]
    planets.append({"name": name, "sign": SIGNS[si], "house": house})

KUNDLI = {"ascendant": "Sagittarius", "planets": planets}
LAGNA_SI = 8


def test_mercury_dual_sign_bcp_houses():
    """7L Mercury: Mithun→7H ages + Kanya→10H ages (not only 12H placement)."""
    bcp = compute_bcp_for_division(planets, LAGNA_SI, division="D1", user_age=26)
    assert bcp["seventh_lord"] == "Mercury"
    assert 7 in bcp["dual_sign_houses"]
    assert 10 in bcp["dual_sign_houses"]
    assert 10 in bcp["all_marriage_ages"]
    assert 22 in bcp["all_marriage_ages"] or 34 in bcp["all_marriage_ages"]
    assert 12 in bcp["placement_ages"]


def test_bcp_merged_list_has_placement_and_dual():
    bcp = compute_bcp_marriage_ages(KUNDLI, LAGNA_SI, user_age=26)
    ages = bcp["all_marriage_ages"]
    assert 7 in ages and 12 in ages and 10 in ages
    rules = {r["rule"] for r in bcp["bcp_age_list"]}
    assert "7H BCP" not in rules
    assert "7L placement" in rules
    assert "7L dual-sign house" in rules


def test_bcp_priority_scores_overlap_placement_highest():
    bcp = compute_bcp_marriage_ages(
        KUNDLI,
        LAGNA_SI,
        user_age=26,
        d9_lagna_si=LAGNA_SI,
        d9_planets=planets,
    )
    top = bcp["bcp_age_scores"][0]

    assert top["age"] == 36
    assert top["overlap_d1_d9"]
    assert "7th_lord_placement" in top["rules"]
    assert bcp["future_priority_ages"][0] == 36


def test_bcp_priority_scores_cluster_nearby_ages():
    d1 = {
        "division": "D1",
        "sources": [
            {"source": "7th_lord_placement", "house": 6, "ages": [30]},
            {
                "source": "7th_lord_dual_sign_houses",
                "houses": [{"house": 7, "ages": [31]}],
            },
        ],
    }
    d9 = {
        "division": "D9",
        "sources": [
            {"source": "7th_lord_placement", "house": 8, "ages": [32]},
        ],
    }

    scored = _score_merged_bcp_ages(d1, d9, user_age=26)
    by_age = {r["age"]: r for r in scored}

    assert by_age[30]["cluster_neighbors"] == [31]
    assert by_age[31]["cluster_neighbors"] == [30, 32]
    assert by_age[32]["cluster_neighbors"] == [31]


def test_bcp_no_automatic_7th_house_age_source():
    """Automatic 7H ages (7,19,31...) are removed; only 7L-derived ages remain."""
    lagna_si = 10  # Aquarius; 7L is Sun (single-sign lord)
    ps = [
        {"name": "Sun", "sign": "Aries", "sign_idx": 0, "house": 3},
        {"name": "Moon", "sign": "Taurus", "sign_idx": 1, "house": 4},
        {"name": "Mars", "sign": "Gemini", "sign_idx": 2, "house": 5},
        {"name": "Mercury", "sign": "Cancer", "sign_idx": 3, "house": 6},
        {"name": "Jupiter", "sign": "Virgo", "sign_idx": 5, "house": 8},
        {"name": "Venus", "sign": "Libra", "sign_idx": 6, "house": 9},
        {"name": "Saturn", "sign": "Scorpio", "sign_idx": 7, "house": 10},
        {"name": "Rahu", "sign": "Sagittarius", "sign_idx": 8, "house": 11},
        {"name": "Ketu", "sign": "Gemini", "sign_idx": 2, "house": 5},
    ]
    bcp = compute_bcp_for_division(ps, lagna_si, division="D1", user_age=20)
    rules = {r.get("source") for r in bcp["sources"]}

    assert "7th_house_bcp" not in rules
    assert 7 not in bcp["all_marriage_ages"]
    assert 19 not in bcp["all_marriage_ages"]
    assert 31 not in bcp["all_marriage_ages"]


def test_bcp_no_automatic_7th_house_age_source_in_d9():
    """D9 BCP also must not add standalone 7H activation ages."""
    d9_lagna_si = 10  # Aquarius; D9 7L is Sun
    d9_ps = [
        {"name": "Sun", "sign": "Aries", "sign_idx": 0, "house": 3},
        {"name": "Moon", "sign": "Taurus", "sign_idx": 1, "house": 4},
        {"name": "Mars", "sign": "Gemini", "sign_idx": 2, "house": 5},
        {"name": "Mercury", "sign": "Cancer", "sign_idx": 3, "house": 6},
        {"name": "Jupiter", "sign": "Virgo", "sign_idx": 5, "house": 8},
        {"name": "Venus", "sign": "Libra", "sign_idx": 6, "house": 9},
        {"name": "Saturn", "sign": "Scorpio", "sign_idx": 7, "house": 10},
        {"name": "Rahu", "sign": "Sagittarius", "sign_idx": 8, "house": 11},
        {"name": "Ketu", "sign": "Gemini", "sign_idx": 2, "house": 5},
    ]
    bcp = compute_bcp_for_division(
        d9_ps, d9_lagna_si, division="D9", user_age=20,
    )
    rules = {r.get("source") for r in bcp["sources"]}

    assert "7th_house_bcp" not in rules
    assert 7 not in bcp["all_marriage_ages"]
    assert 19 not in bcp["all_marriage_ages"]
    assert 31 not in bcp["all_marriage_ages"]


def test_step0_d1_d9_pace_and_late_focus():
    s0 = run_marriage_step0(
        KUNDLI, LAGNA_SI, user_age=26, is_female=False, min_practical_age=22,
    )
    s0a = run_marriage_step0a(
        KUNDLI,
        LAGNA_SI,
        combined_pace=s0["marriage_pace"]["combined"]["combined_pace"],
        age_ctx=s0["marriage_age_context"],
        user_age=26,
    )
    assert s0["marriage_pace"]["d1"]["chart_pace"] in ("LATE", "NORMAL", "VERY_LATE")
    assert s0["marriage_pace"]["d1"]["seventh_lord_house"] == 12
    assert "bcp_all_ages_sorted" not in s0
    assert s0a["bcp_all_ages_sorted"]
    focus = s0a["late_bcp_focus"]["focus_ages"]
    assert 31 in focus or s0a["late_bcp_focus"]["primary_age"] == 31
    assert s0["step0_tendency"]["d1_pace"] is not None


def test_late_chart_incidental_bcp_age_26_does_not_anchor_2026():
    """Age 26 in merged list (2H→26) must not beat 7H→31 on late charts."""
    bcp = {
        "all_marriage_ages": [7, 12, 19, 24, 26, 31, 34, 36],
        "past_activation_ages": [7, 12, 19, 24],
        "future_activation_ages": [26, 31, 34, 36],
        "next_activation_age": 31,
    }
    late = resolve_late_marriage_bcp_focus(
        bcp, marriage_pace="LATE", user_age=26, years_ahead=8,
    )
    assert late["primary_age"] == 31
    assert 26 not in (late.get("focus_ages") or [])
    assert 31 in (late.get("focus_ages") or [])


def test_bcp_anchor_guard_demotes_near_term_for_delayed_chart():
    """Age 26 + BCP focus 31 → Apr-2026-style window must not beat 2031 anchor."""
    from event_timing.marriage.marriage_engine_v2 import _apply_bcp_anchor_guard

    birth = datetime(1999, 11, 26)
    near = {
        "start": datetime(2026, 4, 1),
        "end": datetime(2026, 6, 30),
        "score": 15.0,
        "priority": 1,
        "bcp_age_hits": [],
    }
    focus = {
        "start": datetime(2030, 8, 1),
        "end": datetime(2031, 6, 30),
        "score": 8.0,
        "priority": 3,
        "bcp_age_hits": [31],
    }
    cands = [near, focus]
    n = _apply_bcp_anchor_guard(
        cands,
        chart_delayed=True,
        primary_ref_age=31,
        user_age=26,
        focus_bcp_ages={31},
        birth_dt=birth,
    )
    assert n == 1
    assert near.get("suppressed_pre_bcp_focus")
    assert not focus.get("suppressed_pre_bcp_focus")
    assert near["score"] < focus["score"]


def test_step0_early_house_not_enough_when_7l_and_venus_weak():
    """7L in an early house can still become late when dignity/karaka are weak."""
    lagna_si = 4  # Leo; 7L Saturn
    rows = [
        ("Sun", "Leo", 1, {}),
        ("Moon", "Taurus", 10, {}),
        ("Mars", "Scorpio", 4, {}),
        ("Mercury", "Gemini", 11, {}),
        ("Jupiter", "Sagittarius", 5, {}),
        ("Venus", "Virgo", 2, {}),
        ("Saturn", "Aries", 9, {"retrograde": True}),
        ("Rahu", "Aquarius", 7, {}),
        ("Ketu", "Leo", 1, {}),
    ]
    ps = []
    for name, sign, house, extra in rows:
        rec = {"name": name, "sign": sign, "sign_idx": SIGNS.index(sign), "house": house}
        rec.update(extra)
        ps.append(rec)

    pace = chart_marriage_pace_for_division(ps, lagna_si, "D1", is_female=False)

    assert pace["chart_pace"] == "VERY_LATE"
    assert pace["seventh_lord_dignity"] == "debilitated"
    assert any("Venus debilitated" in s for s in pace["chart_pace_signals"])


def test_step0_late_house_can_be_offset_by_strength_and_benefic_support():
    """7L in a delay house is not automatic delay when it is strong and supported."""
    lagna_si = 0  # Aries; 7L Venus
    rows = [
        ("Sun", "Taurus", 2),
        ("Moon", "Cancer", 4),
        ("Mars", "Capricorn", 10),
        ("Mercury", "Aquarius", 11),
        ("Jupiter", "Gemini", 3),
        ("Venus", "Pisces", 12),
        ("Saturn", "Virgo", 6),
        ("Rahu", "Scorpio", 8),
        ("Ketu", "Taurus", 2),
    ]
    ps = [
        {"name": name, "sign": sign, "sign_idx": SIGNS.index(sign), "house": house}
        for name, sign, house in rows
    ]

    pace = chart_marriage_pace_for_division(ps, lagna_si, "D1", is_female=False)

    assert pace["chart_pace"] == "EARLY"
    assert pace["seventh_lord_dignity"] == "exalted"
    assert any("benefic support" in s for s in pace["chart_pace_signals"])

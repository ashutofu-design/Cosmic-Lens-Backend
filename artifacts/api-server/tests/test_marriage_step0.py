"""STEP 0 — BCP dual-sign + D1/D9 pace (Dhanu lagna user chart)."""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.marriage.bcp_marriage_ages import (
    _bcp_7l_linkage_houses,
    _priority_ages_from_shared_houses,
    _score_merged_bcp_ages,
    _shared_d1_d9_linkage_houses,
    compute_bcp_for_division,
    compute_bcp_marriage_ages,
    resolve_late_marriage_bcp_focus,
)
from event_timing.marriage.marriage_step0 import (
    chart_marriage_pace_for_division,
    run_marriage_step0,
)
from event_timing.marriage.marriage_step0a import (
    _late_urgent_after_chart_delay_guard,
    run_marriage_step0a,
)

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


def test_mercury_bcp_placement_and_aspects():
    """7L Mercury in 12H → placement 12H ages + 7L aspect houses."""
    bcp = compute_bcp_for_division(planets, LAGNA_SI, division="D1", user_age=26)
    assert bcp["seventh_lord"] == "Mercury"
    assert bcp["seventh_lord_house"] == 12
    assert 12 in bcp["placement_ages"]
    assert 12 in bcp["all_marriage_ages"]
    aspect_houses = {e["house"] for e in bcp.get("aspect_houses") or []}
    assert aspect_houses  # Mercury 7th aspect from Vrishchik
    assert bcp["future_bcp_ages"][0] >= 26


def test_bcp_conjunct_planet_aspects_with_7l():
    """Planet conjunct 7L → conjunct planet's aspect houses add BCP ages."""
    ps = []
    for p in planets:
        if p["name"] == "Sun":
            ps.append({**p, "house": 12, "sign": "Scorpio"})
        else:
            ps.append(dict(p))
    bcp = compute_bcp_for_division(ps, LAGNA_SI, division="D1", user_age=26)
    rules = {s.get("source") for s in bcp.get("sources") or []}
    assert "7th_lord_conjunct_aspects" in rules
    assert "Sun" in (bcp.get("conjunct_planets") or [])
    conj_houses = {e["house"] for e in bcp.get("conjunct_aspect_houses") or []}
    assert conj_houses
    assert conj_houses & _bcp_7l_linkage_houses(bcp)


def test_bcp_compact_admin_lines_from_current_age():
    bcp = compute_bcp_marriage_ages(
        KUNDLI,
        LAGNA_SI,
        user_age=26,
        d9_lagna_si=LAGNA_SI,
        d9_planets=planets,
    )
    from event_timing.marriage.bcp_marriage_ages import bcp_compact_admin_lines

    lines = bcp_compact_admin_lines(bcp, user_age=26)
    assert len(lines) == 2
    assert lines[0].startswith("D1:")
    assert lines[1].startswith("D9:")
    d1_nums = [int(x) for x in lines[0].split(":")[1].split(",") if x.strip().isdigit()]
    assert d1_nums and d1_nums[0] >= 26
    assert isinstance(bcp.get("d1_future_bcp_ages"), list)
    assert isinstance(bcp.get("d9_future_bcp_ages"), list)


def test_bcp_merged_list_has_placement_and_aspects():
    bcp = compute_bcp_marriage_ages(KUNDLI, LAGNA_SI, user_age=26)
    ages = bcp["all_marriage_ages"]
    assert 12 in ages
    rules = {r["rule"] for r in bcp["bcp_age_list"]}
    assert "7L placement" in rules
    assert "7L aspect" in rules
    assert "7L dual-sign house" not in rules


def test_bcp_shared_d1_d9_linkage_houses_boost_priority():
    d1 = {
        "division": "D1",
        "seventh_lord_house": 12,
        "aspect_houses": [{"house": 4, "ages": [4, 16, 28, 40]}],
        "sources": [
            {"source": "7th_lord_placement", "house": 12, "ages": [12, 24, 36, 48]},
            {
                "source": "7th_lord_aspects",
                "houses": [{"house": 4, "ages": [4, 16, 28, 40]}],
            },
        ],
    }
    d9 = {
        "division": "D9",
        "seventh_lord_house": 5,
        "aspect_houses": [{"house": 4, "ages": [4, 16, 28, 40]}],
        "sources": [
            {"source": "7th_lord_placement", "house": 5, "ages": [5, 17, 29, 41]},
            {
                "source": "7th_lord_aspects",
                "houses": [{"house": 4, "ages": [4, 16, 28, 40]}],
            },
        ],
    }
    shared = _shared_d1_d9_linkage_houses(d1, d9)
    assert shared == [4]

    shared_ages = _priority_ages_from_shared_houses(shared, user_age=26)
    assert shared_ages[0] == 28

    scored = _score_merged_bcp_ages(d1, d9, user_age=26, shared_linkage_houses=shared)
    by_age = {r["age"]: r for r in scored}
    assert by_age[28]["shared_linkage_house"]
    assert by_age[28]["overlap_d1_d9"]


def test_bcp_merged_exports_linkage_houses():
    bcp = compute_bcp_marriage_ages(
        KUNDLI,
        LAGNA_SI,
        user_age=26,
        d9_lagna_si=LAGNA_SI,
        d9_planets=planets,
    )
    assert isinstance(bcp.get("d1_7l_linkage_houses"), list)
    assert isinstance(bcp.get("d9_7l_linkage_houses"), list)
    assert isinstance(bcp.get("shared_7l_linkage_houses"), list)
    if bcp["shared_7l_linkage_houses"]:
        pri = bcp["shared_house_priority_ages"]
        fut = bcp["future_priority_ages"]
        assert pri[0] == fut[0]


def test_bcp_priority_scores_overlap_placement_highest():
    bcp = compute_bcp_marriage_ages(
        KUNDLI,
        LAGNA_SI,
        user_age=26,
        d9_lagna_si=LAGNA_SI,
        d9_planets=planets,
    )
    future_scores = [r for r in bcp["bcp_age_scores"] if r.get("is_future")]
    top = future_scores[0]

    assert top["age"] in (30, 36)
    assert top["overlap_d1_d9"]
    assert "7th_lord_placement" in top["rules"] or "7th_lord_aspects" in top["rules"]
    assert bcp["future_priority_ages"][0] in (30, 36)


def test_bcp_priority_scores_cluster_nearby_ages():
    d1 = {
        "division": "D1",
        "sources": [
            {"source": "7th_lord_placement", "house": 6, "ages": [30]},
            {
                "source": "7th_lord_aspects",
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
    pri = s0a["late_bcp_focus"]["primary_age"]
    assert pri in (30, 31, 36) or any(a in focus for a in (30, 31, 36))
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


def test_bcp_anchor_guard_demotes_pre_activation_age_26_when_next_bcp_27():
    """Delayed chart age 26 + BCP 27 — Oct-2026 before birthday must lose."""
    from event_timing.marriage.marriage_engine_v2 import _apply_bcp_anchor_guard

    birth = datetime(2000, 7, 3)
    near = {
        "start": datetime(2026, 10, 1),
        "end": datetime(2026, 11, 30),
        "score": 20.0,
        "priority": 0,
        "bcp_age_hits": [],
    }
    at_bcp = {
        "start": datetime(2027, 8, 1),
        "end": datetime(2028, 2, 28),
        "score": 12.0,
        "priority": 3,
        "bcp_age_hits": [27],
    }
    cands = [near, at_bcp]
    n = _apply_bcp_anchor_guard(
        cands,
        chart_delayed=True,
        primary_ref_age=27,
        user_age=26,
        focus_bcp_ages={27},
        birth_dt=birth,
    )
    assert n == 1
    assert near.get("suppressed_pre_bcp_focus")
    assert not at_bcp.get("suppressed_pre_bcp_focus")
    assert near["score"] < at_bcp["score"]


def test_bcp_floor_rejects_oct_2026_before_age_27_birthday():
    from event_timing.marriage.marriage_engine_v2 import _enforce_bcp_activation_floor

    birth = datetime(2000, 7, 3)
    early = {
        "start": datetime(2026, 10, 1),
        "end": datetime(2026, 11, 30),
        "score": 30.0,
        "priority": 0,
        "md": "Sun",
        "ad": "Venus",
        "pd": "Jupiter",
    }
    later = {
        "start": datetime(2027, 8, 1),
        "end": datetime(2028, 1, 31),
        "score": 18.0,
        "priority": 3,
        "md": "Sun",
        "ad": "Mars",
        "pd": "Venus",
    }
    pool = [early, later]
    top, notes = _enforce_bcp_activation_floor(
        [early],
        pool,
        chart_delayed=True,
        primary_ref_age=24,
        focus_bcp_ages={27, 29, 31},
        user_age=26,
        birth_dt=birth,
    )
    assert top[0]["start"] == later["start"]
    assert any("BCP_FLOOR" in n for n in notes)


def test_effective_anchor_uses_focus_when_primary_stale():
    from event_timing.marriage.marriage_engine_v2 import _effective_bcp_anchor_age

    assert _effective_bcp_anchor_age(24, {27, 29, 31}, 26) == 27


def test_age_26_uses_upcoming_bcp_27_not_missed_recent():
    from event_timing.marriage.bcp_marriage_ages import resolve_bcp_timing_strategy

    bcp = {
        "all_marriage_ages": [7, 12, 19, 21, 23, 24, 27, 29, 31, 35],
        "last_passed_bcp_age": 24,
        "years_since_last_bcp": 2,
        "next_activation_age": 35,
        "years_to_next_bcp": 9,
        "upcoming_year_bcp_ages": [27],
        "primary_priority_age": 35,
    }
    strat = resolve_bcp_timing_strategy(bcp, 26)
    assert strat["timing_mode"] == "upcoming_bcp"
    assert strat["primary_reference_age"] == 27


def test_missed_bcp_not_for_young_user_just_past_incidental_24():
    from event_timing.marriage.bcp_marriage_ages import resolve_bcp_timing_strategy

    bcp = {
        "all_marriage_ages": [24, 35, 40],
        "last_passed_bcp_age": 24,
        "years_since_last_bcp": 2,
        "next_activation_age": 35,
        "years_to_next_bcp": 9,
        "upcoming_year_bcp_ages": [],
        "primary_priority_age": 35,
    }
    strat = resolve_bcp_timing_strategy(bcp, 26)
    assert strat["timing_mode"] != "missed_bcp_recent"


def test_resolve_next_activation_skips_incidental_in_list_age():
    from event_timing.marriage.bcp_marriage_ages import _resolve_next_activation_age

    ages = [7, 12, 19, 24, 26, 31, 34, 36]
    pri = [31, 34, 36, 26, 24]
    assert _resolve_next_activation_age(ages, pri, 26) == 31
    assert _resolve_next_activation_age(ages, [27, 29, 31], 26) == 27


def test_chart_delay_disables_late_urgent_for_upcoming_bcp_next_year():
    """upcoming_bcp (26→27) + delayed chart must not keep 12mo late-urgent scan."""
    urgent = _late_urgent_after_chart_delay_guard(
        True,
        age_ctx={"delay_vs_late": "chart_delay"},
        user_age=26,
        bcp={"next_activation_age": 27},
        bcp_strategy={"timing_mode": "upcoming_bcp", "late_urgent_scan": True},
        step0_verdict="DELAYED",
    )
    assert urgent is False

    urgent_by_verdict = _late_urgent_after_chart_delay_guard(
        True,
        age_ctx={"delay_vs_late": "none"},
        user_age=26,
        bcp={"next_activation_age": 27},
        bcp_strategy={"timing_mode": "upcoming_bcp", "late_urgent_scan": True},
        step0_verdict="DELAYED",
    )
    assert urgent_by_verdict is False

    # User ON current BCP year — urgent scan should stay on
    still_urgent = _late_urgent_after_chart_delay_guard(
        True,
        age_ctx={"delay_vs_late": "chart_delay"},
        user_age=27,
        bcp={"next_activation_age": 29},
        bcp_strategy={"timing_mode": "current_bcp_year", "late_urgent_scan": True},
    )
    assert still_urgent is True


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


def test_d9_malefic_in_7h_cannot_read_early():
    """D9 7H malefic → pace capped at LATE even if 7L in early house."""
    lagna_si = 0  # Aries; D9 7L = Venus
    rows = [
        ("Sun", "Libra", 7),  # malefic in 7H
        ("Moon", "Cancer", 4),
        ("Mars", "Capricorn", 10),
        ("Mercury", "Aquarius", 11),
        ("Jupiter", "Gemini", 3),
        ("Venus", "Leo", 5),  # 7L in 5H (early house)
        ("Saturn", "Virgo", 6),
        ("Rahu", "Scorpio", 8),
        ("Ketu", "Taurus", 2),
    ]
    ps = []
    for name, sign, house in rows:
        ps.append({
            "name": name,
            "sign": sign,
            "sign_idx": SIGNS.index(sign),
            "house": house,
        })
    pace = chart_marriage_pace_for_division(ps, lagna_si, "D9", is_female=False)
    assert "Sun" in (pace.get("malefics_in_7h") or [])
    assert pace["chart_pace"] in ("LATE", "VERY_LATE", "NORMAL")
    assert pace["chart_pace"] != "EARLY"


def test_d9_malefic_aspects_7l_counts():
    """Saturn aspecting D9 7L sign must count toward delay."""
    lagna_si = 4  # Leo; D9 7L = Saturn (Aquarius)
    rows = [
        ("Sun", "Taurus", 10),
        ("Moon", "Cancer", 12),
        ("Mars", "Aries", 9),
        ("Mercury", "Gemini", 11),
        ("Jupiter", "Sagittarius", 5),
        ("Venus", "Pisces", 8),
        ("Saturn", "Leo", 1),  # aspects Aquarius (7L sign) via 7th aspect
        ("Rahu", "Scorpio", 4),
        ("Ketu", "Taurus", 10),
    ]
    ps = []
    for name, sign, house in rows:
        ps.append({
            "name": name,
            "sign": sign,
            "sign_idx": SIGNS.index(sign),
            "house": house,
        })
    pace = chart_marriage_pace_for_division(ps, lagna_si, "D9", is_female=False)
    assert "Saturn" in (pace.get("malefics_on_7l") or [])


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

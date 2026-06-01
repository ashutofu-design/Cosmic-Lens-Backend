"""Marriage Step 7 — future transit exact-orb verification."""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import event_timing.marriage.marriage_engine_v2 as me  # noqa: E402


class _FakeSwe:
    JUPITER = 5
    SATURN = 6

    @staticmethod
    def julday(year, month, day, hour):
        return (year, month, day, hour)

    @staticmethod
    def calc_ut(jd, planet_id, flags):
        _ = flags
        if planet_id == _FakeSwe.JUPITER:
            return [340.0], 0  # target 100° by Jupiter 5th aspect (120°)
        if planet_id == _FakeSwe.SATURN:
            return [40.0], 0   # target 100° by Saturn 3rd aspect (60°)
        return [0.0], 0


def test_step7_exact_future_orb_double_transit(monkeypatch):
    monkeypatch.setattr(me, "_HAS_SWE", True)
    monkeypatch.setattr(me, "swe", _FakeSwe)

    window = {
        "start": datetime(2036, 11, 1),
        "end": datetime(2036, 11, 30),
    }
    result = me._step6_double_transit(
        window,
        h7_si=3,
        seventh_lord_si=None,
        top_planet_signs=set(),
        transit_targets=[{"label": "7L Venus", "lon": 100.0, "sign_idx": 3}],
    )

    assert result["jup_hit"]
    assert result["sat_hit"]
    assert result["dt"]
    assert result["best_check_at"] == "2036-11-01"
    assert result["samples"][0]["jupiter_hits"][0]["orb"] == 0.0
    assert result["samples"][0]["saturn_hits"][0]["orb"] == 0.0


def test_step7_builds_exact_targets_from_chart_longitudes():
    kundli = {"ascendantDeg": 10.0}
    planets = [
        {"name": "Venus", "longitude": 123.4, "sign": "Leo", "house": 5},
        {"name": "Moon", "longitude": 88.0, "sign": "Gemini", "house": 3},
    ]

    targets = me._build_transit_targets(
        kundli,
        planets,
        h7_si=6,
        seventh_lord="Venus",
        top_planet_names=["Moon"],
        d9_7l="Venus",
    )

    labels = {t["label"] for t in targets}
    assert "7th house" in labels
    assert "7th lord Venus" in labels
    assert "top Moon" not in labels
    assert any(
        t["label"] == "7th house"
        and t["target_type"] == "seventh_house"
        and t["lon"] == 190.0
        for t in targets
    )


def test_step7_sign_hit_to_7th_house_passes_with_exact_targets(monkeypatch):
    class SignSwe:
        JUPITER = 5
        SATURN = 6

        @staticmethod
        def julday(year, month, day, hour):
            return (year, month, day, hour)

        @staticmethod
        def calc_ut(jd, planet_id, flags):
            _ = jd, flags
            if planet_id == SignSwe.JUPITER:
                return [90.0], 0  # Cancer sign: occupies h7_si=3
            if planet_id == SignSwe.SATURN:
                return [0.0], 0
            return [0.0], 0

    monkeypatch.setattr(me, "_HAS_SWE", True)
    monkeypatch.setattr(me, "swe", SignSwe)
    result = me._step6_double_transit(
        {"start": datetime(2030, 1, 1), "end": datetime(2030, 1, 30)},
        h7_si=3,
        seventh_lord_si=None,
        top_planet_signs={8},
        transit_targets=[{
            "label": "top Moon", "lon": 250.0, "sign_idx": 8,
            "target_type": "top_planet",
        }],
    )

    assert result["transit_confirmed"]
    assert result["jup_hit"]
    assert result["samples"][0]["jupiter_hits"][0]["target"] == "7th house"
    assert result["samples"][0]["jupiter_hits"][0]["hit_type"] == "occupies_7th_house"


def test_step7_no_transit_primary_promotes_next_supported(monkeypatch):
    bad = {
        "md": "Venus", "ad": "Mars", "pd": "Mars",
        "start": datetime(2030, 1, 1), "end": datetime(2030, 2, 1),
        "score": 20.0,
    }
    good = {
        "md": "Venus", "ad": "Moon", "pd": "Moon",
        "start": datetime(2030, 4, 1), "end": datetime(2030, 5, 1),
        "score": 15.0,
    }

    def fake_attach(window, *_args, **_kwargs):
        ok = window["ad"] == "Moon"
        window["transit_confirmed"] = ok
        window["jup"] = ok
        window["sat"] = False
        window["dt"] = False
        window["dt_detail"] = "fake hit" if ok else "no transit hit"
        return {"transit_confirmed": ok, "dt": False, "detail": window["dt_detail"]}

    monkeypatch.setattr(me, "_attach_transit_to_window", fake_attach)

    selected, notes = me._ensure_transit_supported_primary(
        [bad],
        [bad, good],
        birth_dt=None,
        focus_bcp_ages=set(),
        h7_si=0,
        seventh_lord_si=None,
        top_planet_signs=set(),
        transit_targets=[],
    )

    assert selected[0] is good
    assert good["promoted_by_transit_support"]
    assert bad["skipped_as_primary_no_transit"]
    assert any("promoted" in n for n in notes)


def test_step7_bcp_year_scan_can_rescue_primary(monkeypatch):
    primary = {
        "md": "Venus", "ad": "Mars", "pd": "Mars",
        "start": datetime(2030, 1, 1), "end": datetime(2030, 2, 1),
        "score": 20.0,
        "bcp_age_hits": [30],
    }
    alternate = {
        "md": "Venus", "ad": "Moon", "pd": "Moon",
        "start": datetime(2030, 4, 1), "end": datetime(2030, 5, 1),
        "score": 15.0,
    }

    def fake_attach(window, *_args, **_kwargs):
        window["transit_confirmed"] = False
        window["dt_detail"] = "no transit hit"
        return {"transit_confirmed": False, "dt": False, "detail": "no transit hit"}

    def fake_bcp_scan(window, **_kwargs):
        if window is primary:
            window["transit_confirmed"] = True
            window["bcp_year_transit_support"] = True
            window["dt_detail"] = "BCP year transit support"
            return {"transit_confirmed": True}
        return None

    monkeypatch.setattr(me, "_attach_transit_to_window", fake_attach)
    monkeypatch.setattr(me, "_try_bcp_year_transit_support", fake_bcp_scan)

    selected, notes = me._ensure_transit_supported_primary(
        [primary],
        [primary, alternate],
        birth_dt=datetime(2000, 1, 1),
        focus_bcp_ages={30},
        h7_si=0,
        seventh_lord_si=None,
        top_planet_signs=set(),
        transit_targets=[],
    )

    assert selected[0] is primary
    assert primary["bcp_year_transit_support"]
    assert notes == []


def test_delayed_anchor_removes_early_focus_ages():
    focus, removed = me._delayed_anchor_focus_ages(
        {27, 30, 31, 33, 34},
        chart_delayed=True,
        primary_ref_age=31,
        user_age=26,
    )

    assert focus == {30, 31, 33, 34}
    assert removed == [27]


def test_delayed_anchor_keeps_focus_ages_when_primary_near():
    focus, removed = me._delayed_anchor_focus_ages(
        {27, 30, 31},
        chart_delayed=True,
        primary_ref_age=27,
        user_age=26,
    )

    assert focus == {27, 30, 31}
    assert removed == []

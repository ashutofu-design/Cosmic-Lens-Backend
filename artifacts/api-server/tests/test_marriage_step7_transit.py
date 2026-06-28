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


def test_transit_type_derived_from_by_month_not_stale_window_flags(monkeypatch):
    """Admin label must match per-month activation (Dhanu: Guru off, Shani on)."""
    by_month = [
        {
            "month": "Jun 2029",
            "jupiter_rashi": "Kanya",
            "jupiter_active": False,
            "jupiter_activation": "7H/7L par nahi",
            "saturn_rashi": "Mesh",
            "saturn_active": True,
            "saturn_activation": "7th ghar drishti",
        },
    ]
    monkeypatch.setattr(
        me,
        "finalize_transit_display",
        lambda **kwargs: ("Jun 2029: detail", ["Jun 2029"], by_month),
    )
    pkg = me._build_step7_transit_package(
        {"jup": True, "sat": True, "dt": True, "transit_confirmed": True},
        None,
    )
    assert pkg["transit_type"] == "single_shani"
    assert pkg["transit_type_label"] == me._TRANSIT_TYPE_LABELS["single_shani"]
    assert pkg["double_transit"] is False
    assert pkg["jupiter_hit"] is False
    assert pkg["saturn_hit"] is True


def test_transit_type_double_only_when_same_month_both_active():
    by_month = [
        {"month": "Jun 2029", "jupiter_active": True, "saturn_active": False},
        {"month": "Sep 2029", "jupiter_active": False, "saturn_active": True},
    ]
    _, _, dt, ttype = me._derive_transit_flags_from_by_month(by_month)
    assert ttype == "split"
    assert dt is False

    by_month_dt = [
        {"month": "Sep 2029", "jupiter_active": True, "saturn_active": True},
    ]
    _, _, dt2, ttype2 = me._derive_transit_flags_from_by_month(by_month_dt)
    assert ttype2 == "double"
    assert dt2 is True


def test_dhanu_lagna_saturn_mesh_aspects_7th_house():
    """Dhanu lagna → 7H Mithun; Shani Mesh = 3rd aspect on 7H (valid single transit)."""
    h7_si = (8 + 6) % 12  # Mithun
    sat_hits = me._collect_sign_hits("Saturn", 0, h7_si, 2)  # 7L in Mithun
    assert any(h.get("hit_type") == "aspects_7th_house" for h in sat_hits)
    jup_hits = me._collect_sign_hits("Jupiter", 5, h7_si, 2)  # Guru Kanya
    assert jup_hits == []


def test_activation_detail_in_compact_sample():
    samples = [
        {
            "date": "2029-06-30",
            "jupiter_rashi": "Kanya",
            "saturn_rashi": "Mesh",
            "jupiter_hits": [],
            "saturn_hits": [{"hit_type": "aspects_7th_house", "target": "7th house"}],
        },
    ]
    detail, months, rows = me._compact_transit_by_month(samples)
    assert "7H/7L par nahi" in detail
    assert "7th ghar drishti" in detail
    assert rows[0]["saturn_active"] is True
    assert rows[0]["jupiter_active"] is False


def test_enrich_dhanu_with_chart_context(monkeypatch):
    """Month-only enrich + chart context → per-planet 7H/7L activation."""
    ctx = {
        "lagna": "Dhanu",
        "seventh_house": "Mithun",
        "seventh_lord": "Mercury",
        "seventh_lord_sign": "Mithun",
    }
    full_ctx = me.transit_ctx_from_public_chart(ctx)
    assert full_ctx is not None

    class Jun2029Swe:
        JUPITER = 5
        SATURN = 6

        @staticmethod
        def julday(year, month, day, hour):
            return (year, month, day, hour)

        @staticmethod
        def calc_ut(jd, planet_id, flags):
            _ = jd, flags
            if planet_id == Jun2029Swe.JUPITER:
                return [165.0], 0  # Kanya
            if planet_id == Jun2029Swe.SATURN:
                return [15.0], 0   # Mesh
            return [0.0], 0

    monkeypatch.setattr(me, "_HAS_SWE", True)
    monkeypatch.setattr(me, "swe", Jun2029Swe)
    detail, months, rows = me._enrich_transit_month_labels(["Jun 2029"], full_ctx)
    assert "Guru Kanya (7H/7L par nahi)" in detail
    assert "Shani Mesh (7th ghar drishti)" in detail
    assert rows[0]["jupiter_active"] is False
    assert rows[0]["saturn_active"] is True


def test_enrich_month_only_labels(monkeypatch):
    monkeypatch.setattr(
        me,
        "_transit_rashis_at_iso",
        lambda iso: ("Singh", "Kark") if "2029-06" in iso else ("Tula", "Makar"),
    )
    detail, months, rows = me._enrich_transit_month_labels(["Jun 2029", "Sep 2029"])
    assert "Guru Singh" in detail and "Shani Kark" in detail
    assert "Guru Tula" in detail and "Shani Makar" in detail
    assert months == ["Jun 2029", "Sep 2029"]
    assert rows[0]["jupiter_rashi"] == "Singh"


def test_finalize_from_month_only_detail(monkeypatch):
    monkeypatch.setattr(
        me,
        "_transit_rashis_at_iso",
        lambda iso: ("Dhanu", "Makar") if iso else (None, None),
    )
    detail, months, rows = me.finalize_transit_display(
        detail="Jun 2029 · Sep 2029",
        months=["Jun 2029", "Sep 2029"],
    )
    assert "Guru Dhanu" in detail
    assert "Shani Makar" in detail
    assert len(rows) == 2


def test_monthify_verbose_transit_detail(monkeypatch):
    monkeypatch.setattr(
        me,
        "_transit_rashis_at_iso",
        lambda iso: ("Singh", "Kark") if iso.startswith("2029-06") else ("Tula", "Makar"),
    )
    verbose = (
        "2029-06-30 Sat→7th house orb 1.97° + "
        "2029-09-07 Jup→7th house + "
        "2029-09-07 Sat→7th house orb 1.82°"
    )
    out = me._monthify_verbose_transit_detail(verbose)
    assert "Jun 2029" in out and "Sep 2029" in out
    assert "Guru Singh" in out and "Shani Kark" in out
    assert "Guru Tula" in out and "Shani Makar" in out
    assert "7th" not in out and "orb" not in out


def test_transit_detail_uses_rashi_labels():
    samples = [
        {
            "date": "2029-06-30",
            "jupiter_lon": 120.0,
            "saturn_lon": 90.0,
            "jupiter_hits": [],
            "saturn_hits": [{"target": "7th house"}],
        },
        {
            "date": "2029-09-07",
            "jupiter_lon": 180.0,
            "saturn_lon": 270.0,
            "jupiter_hits": [{"target": "7th house"}],
            "saturn_hits": [{"target": "7th house"}],
        },
    ]
    detail, months, rows = me._compact_transit_by_month(samples)

    assert months == ["Jun 2029", "Sep 2029"]
    assert "Guru" in detail and "Shani" in detail
    assert "7th" not in detail
    assert rows[0]["jupiter_rashi"] == "Singh"
    assert rows[0]["saturn_rashi"] == "Kark"


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

"""Dasha MD/AD consistency — finest PD row + primary window alignment."""
from __future__ import annotations

from datetime import datetime, timedelta

from event_timing._shared.dasha_kp_sync import _find_running_dasha
from event_timing._shared.generic_timing_engine import (
    _finest_windows_containing_now,
    pick_primary_timing_window,
)


def _demo_kundli() -> dict:
    now = datetime.utcnow()
    md_start = now - timedelta(days=400)
    ad_start = now - timedelta(days=120)
    pd1_end = now + timedelta(days=30)
    pd2_start = pd1_end
    pd2_end = now + timedelta(days=200)
    return {
        "ascendant": "Libra",
        "planets": [
            {"name": "Saturn", "house": 5, "sign": "Aquarius"},
            {"name": "Venus", "house": 7, "sign": "Aries"},
        ],
        "dashas": [
            {
                "planet": "Saturn",
                "startDate": md_start.strftime("%Y-%m-%d"),
                "endDate": (now + timedelta(days=365 * 10)).strftime("%Y-%m-%d"),
                "subDashas": [
                    {
                        "planet": "Saturn",
                        "startDate": ad_start.strftime("%Y-%m-%d"),
                        "endDate": (now + timedelta(days=365)).strftime("%Y-%m-%d"),
                        "subDashas": [
                            {
                                "planet": "Saturn",
                                "startDate": ad_start.strftime("%Y-%m-%d"),
                                "endDate": pd1_end.strftime("%Y-%m-%d"),
                            },
                            {
                                "planet": "Jupiter",
                                "startDate": pd2_start.strftime("%Y-%m-%d"),
                                "endDate": pd2_end.strftime("%Y-%m-%d"),
                            },
                        ],
                    }
                ],
            }
        ],
    }


def test_find_running_dasha_finest_pd_not_coarse_ad() -> None:
    run = _find_running_dasha(_demo_kundli(), datetime.utcnow())
    assert run is not None
    assert run.get("pd") == "Saturn"
    assert run.get("ad") == "Saturn"
    assert run.get("md") == "Saturn"


def test_pick_primary_uses_finest_running_window() -> None:
    now = datetime.utcnow()
    windows = [
        {
            "md": "Saturn", "ad": "Saturn", "pd": None,
            "start": now - timedelta(days=365),
            "end": now + timedelta(days=365),
            "start_iso": "2020-01-01", "end_iso": "2030-01-01",
            "score": 20.0,
        },
        {
            "md": "Saturn", "ad": "Saturn", "pd": "Saturn",
            "start": now - timedelta(days=60),
            "end": now + timedelta(days=30),
            "start_iso": "2025-01-01", "end_iso": "2026-08-01",
            "score": 12.0,
            "lords": "Saturn/Saturn/Saturn",
        },
    ]
    finest = _finest_windows_containing_now(windows, now)
    assert len(finest) == 1
    assert finest[0].get("pd") == "Saturn"
    ranked = [{"name": "Saturn", "score": 18.0}, {"name": "Venus", "score": 16.0}]
    primary, _nxt, src, supports = pick_primary_timing_window(
        windows, ranked, {"Saturn", "Venus"}, now, min_ad_pd=9.0,
    )
    assert src == "current_dasha_active"
    assert supports
    assert primary is not None
    assert primary.get("pd") == "Saturn"
    assert primary.get("lords") == "Saturn/Saturn/Saturn"


def test_no_window_below_nine_becomes_primary():
    """Mandatory gate: activation < 9 → skip period, scan forward; none left → no primary."""
    from datetime import datetime, timedelta

    from event_timing._shared.generic_timing_engine import pick_primary_timing_window

    now = datetime(2026, 6, 28)
    ranked = [
        {"name": "Venus", "score": 12.0},
        {"name": "Mercury", "score": 11.0},
        {"name": "Rahu", "score": 4.0},
    ]
    promote = {"Venus", "Mercury"}
    weak_current = {
        "md": "Rahu", "ad": "Rahu", "pd": "Rahu",
        "start": now - timedelta(days=1),
        "end": now + timedelta(days=120),
        "start_iso": "2026-06-27", "end_iso": "2026-10-25",
        "score": 6.05,
    }
    strong_next = {
        "md": "Venus", "ad": "Venus", "pd": "Mercury",
        "start": now + timedelta(days=120),
        "end": now + timedelta(days=300),
        "start_iso": "2026-10-25", "end_iso": "2027-04-24",
        "score": 12.0,
    }
    primary, nxt, src, supports = pick_primary_timing_window(
        [weak_current, strong_next], ranked, promote, now, min_ad_pd=9.0,
    )
    assert src == "next_dasha_scan"
    assert supports is False
    assert primary is not None
    assert primary.get("pd") == "Mercury"
    assert primary.get("activation_score", 0) >= 9.0

    only_weak = [weak_current]
    primary2, _nxt2, src2, supports2 = pick_primary_timing_window(
        only_weak, ranked, promote, now, min_ad_pd=9.0,
    )
    assert primary2 is None
    assert src2 == "no_qualified_window"
    assert supports2 is False


def test_three_timing_periods_and_house_lord_scores():
    from datetime import datetime, timedelta

    from event_timing._shared.generic_timing_engine import (
        DomainTimingConfig,
        _build_domain_house_lords,
        _build_domain_significator_rank,
        _build_three_timing_periods,
        _pick_primary_significator,
        _step1_filter,
    )

    now = datetime(2026, 6, 28)
    ranked = [
        {"name": "Venus", "score": 18.0, "links": ["Venus love karaka", "occupies 5H"]},
        {"name": "Mercury", "score": 14.0, "links": ["5H romance", "conjunct 5L(Sun)"]},
        {"name": "Jupiter", "score": 12.0, "links": ["7H partnership", "aspects 5H"]},
    ]
    cfg = DomainTimingConfig(
        domain="love",
        concern_houses=[(5, 18.0, "5H"), (7, 18.0, "7H"), (11, 12.0, "11H")],
        occupant_bumps=[(5, 10.0, "occupies 5H")],
        aspect_target_houses=[(5, 8.0, "aspects 5H")],
        karakas=[("Venus", 16.0, "Venus love karaka")],
    )
    kundli = {
        "ascendant": "Aries",
        "planets": [
            {"name": "Sun", "house": 5, "sign": "Leo"},
            {"name": "Venus", "house": 5, "sign": "Leo"},
            {"name": "Mercury", "house": 5, "sign": "Leo"},
            {"name": "Jupiter", "house": 9, "sign": "Sagittarius"},
        ],
    }
    lords = _build_domain_house_lords(0, cfg, ranked)
    assert len(lords) == 3
    sig_rank = _build_domain_significator_rank(0, kundli, cfg, ranked)
    roles = {e.get("role") for e in sig_rank}
    assert "occupant" in roles
    assert "conjunct_lord" in roles
    assert any(e.get("planet") == "Venus" and e.get("role") == "occupant" for e in sig_rank)

    d1 = _step1_filter(kundli, 0, cfg)
    assert d1["Mercury"]["d1"] >= 12.0
    assert any("conjunct 5L" in l for l in d1["Mercury"]["links"])

    sig = _pick_primary_significator(sig_rank, ranked)
    assert sig.get("name") == "Venus"
    assert sig.get("score") == 18.0

    promote = {"Venus", "Mercury", "Jupiter"}
    windows = []
    for i, pd in enumerate(("Venus", "Mercury", "Jupiter")):
        start = now + timedelta(days=60 * i)
        end = start + timedelta(days=120)
        windows.append({
            "md": "Saturn", "ad": "Venus", "pd": pd,
            "start": start, "end": end,
            "start_iso": start.strftime("%Y-%m-%d"),
            "end_iso": end.strftime("%Y-%m-%d"),
            "score": 12.0,
        })
    primary = windows[0]
    periods = _build_three_timing_periods(
        windows, ranked, promote, now, 9.0, primary, sig.get("name"),
    )
    assert len(periods) == 3
    assert periods[0].get("rank") == 1
    assert periods[1].get("rank") == 2
    assert periods[2].get("rank") == 3
    assert periods[0].get("love_via") == "PD"  # Venus is AD+PD — finest PD wins

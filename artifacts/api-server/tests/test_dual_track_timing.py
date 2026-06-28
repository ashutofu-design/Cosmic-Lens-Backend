"""Tests — dual-track timing (promise → Vedic vs KP, marriage excluded)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing._shared.dual_track_timing import enrich_dual_track_timing, format_dual_track_block
from event_timing.fame.fame_timing_v1 import compute_fame_window
from event_timing.timing_router import resolve_timing_domain, run_timing_engine

_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Sun", "house": 10, "sign": "Virgo"},
        {"name": "Moon", "house": 5, "sign": "Aries"},
        {"name": "Mars", "house": 8, "sign": "Cancer"},
        {"name": "Mercury", "house": 5, "sign": "Aries"},
        {"name": "Jupiter", "house": 1, "sign": "Sagittarius"},
        {"name": "Venus", "house": 11, "sign": "Libra"},
        {"name": "Saturn", "house": 3, "sign": "Aquarius"},
        {"name": "Rahu", "house": 11, "sign": "Libra"},
        {"name": "Ketu", "house": 5, "sign": "Aries"},
    ],
    "dashas": [
        {
            "lord": "Sun",
            "start": "2020-01-01",
            "end": "2026-01-01",
            "subDashas": [
                {
                    "lord": "Rahu",
                    "start": "2024-06-01",
                    "end": "2027-02-01",
                    "subDashas": [
                        {"lord": "Jupiter", "start": "2025-01-01", "end": "2025-08-01"},
                        {"lord": "Sun", "start": "2025-08-01", "end": "2026-03-01"},
                    ],
                },
            ],
        },
    ],
}

_KP = {
    "cusps": [
        {"house": 1, "subLord": "Jupiter", "sb": "Jupiter"},
        {"house": 5, "subLord": "Mercury", "sb": "Mercury"},
        {"house": 10, "subLord": "Sun", "sb": "Sun"},
        {"house": 11, "subLord": "Rahu", "sb": "Rahu"},
    ],
    "significations": {
        "Sun": {"pl": [10], "sl": [10], "sb_houses": [1, 10], "ss_houses": [10]},
        "Rahu": {"pl": [11], "sl": [11], "sb_houses": [5, 11], "ss_houses": [11]},
        "Jupiter": {"pl": [1], "sl": [9], "sb_houses": [1, 5], "ss_houses": [1]},
        "Mercury": {"pl": [5], "sl": [5], "sb_houses": [3, 5], "ss_houses": [5]},
    },
}


def test_promise_check_runs_first() -> None:
    raw = compute_fame_window(_KUNDLI, kp=_KP, bucket="social_fame")
    enriched = enrich_dual_track_timing(
        raw, _KUNDLI, _KP, concern_houses=[1, 5, 10, 11], karakas=["Sun", "Rahu"], domain="fame",
    )
    assert "promise_check" in enriched
    assert enriched["promise_check"]["level"] in ("STRONG", "MODERATE", "WEAK", "UNKNOWN")
    factors = " ".join(enriched.get("factors") or [])
    assert "STEP0" in factors


def test_dual_track_separate_scores() -> None:
    raw = compute_fame_window(_KUNDLI, kp=_KP, bucket="social_fame")
    enriched = enrich_dual_track_timing(
        raw, _KUNDLI, _KP, concern_houses=[1, 5, 10, 11], domain="fame",
    )
    dt = enriched.get("dual_track") or {}
    assert "vedic" in dt and "kp" in dt
    assert dt.get("winner") in ("VEDIC", "KP", "CONVERGED", "NONE")
    block = format_dual_track_block(enriched)
    assert "NOT MIXED" in block


def test_fame_router_gets_dual_track() -> None:
    ctx = run_timing_engine("Mera content kab viral hoga?", _KUNDLI, {}, _KP, None)
    assert ctx.demand.domain == "fame"
    assert ctx.raw.get("dual_track")
    assert "DUAL-TRACK" in (ctx.raw.get("_prompt_block") or "")


def test_marriage_skips_dual_track() -> None:
    ctx = run_timing_engine("Shaadi kab hogi?", _KUNDLI, {}, _KP, None)
    assert ctx.demand.domain == "marriage"
    assert not ctx.raw.get("dual_track")


def test_universal_gets_dual_track() -> None:
    ctx = run_timing_engine("Lottery kab lagegi?", _KUNDLI, {}, _KP, None)
    assert ctx.demand.domain == "universal"
    assert ctx.raw.get("dual_track")

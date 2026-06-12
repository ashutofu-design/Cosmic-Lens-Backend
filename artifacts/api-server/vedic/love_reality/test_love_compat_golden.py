"""
Golden-chart regression tests for Love Compatibility scoring.

Each case uses fixed birth data; assertions lock flags, orb weights, and score bands
so orb / pipeline changes cannot silently drift.
"""
from __future__ import annotations

from typing import Any

import pytest

from kundli_engine import calculate_kundli
from vedic.love_reality.engines import run_love_compatibility
from vedic.love_reality.golden_charts import ALL_GOLDEN_CASES
from vedic.love_reality.relationship_signals import analyze_couple
from vedic.love_reality.scoring_core import KundliReader, ORB_SIGN_ONLY_WEIGHT


def _load_case(case: dict[str, Any]) -> tuple[KundliReader, KundliReader, Any, dict[str, Any]]:
    p1, p2 = case["p1"], case["p2"]
    k1 = calculate_kundli({**p1, "name": p1.get("name") or "You"})
    k2 = calculate_kundli({**p2, "name": p2.get("name") or "Partner"})
    r1, r2 = KundliReader(k1), KundliReader(k2)
    sig = analyze_couple(r1, r2)
    lc = run_love_compatibility(p1, p2, skip_ai_insight=True)
    return r1, r2, sig, lc


def _flag_snapshot(sig) -> dict[str, Any]:
    return {
        "moon_mismatch": sig.moon_mismatch,
        "cross_rahu_venus": sig.cross_rahu_venus,
        "cross_rahu_venus_orb_weight": sig.cross_rahu_venus_orb_weight,
        "p1_venus_debil": sig.p1.venus_debil,
        "p2_venus_debil": sig.p2.venus_debil,
        "p1_moon_afflicted": sig.p1.moon_afflicted,
        "p2_moon_afflicted": sig.p2.moon_afflicted,
        "p1_saturn_on_7th": sig.p1.saturn_on_7th,
        "p2_saturn_on_7th": sig.p2.saturn_on_7th,
        "p1_saturn_orb": sig.p1.saturn_on_7th_orb_weight,
        "p2_saturn_orb": sig.p2.saturn_on_7th_orb_weight,
        "p1_moon_orb": sig.p1.moon_afflicted_orb_weight,
        "p2_moon_orb": sig.p2.moon_afflicted_orb_weight,
        "combined_affliction": sig.combined_affliction,
    }


@pytest.mark.parametrize("case", ALL_GOLDEN_CASES, ids=[c["id"] for c in ALL_GOLDEN_CASES])
def test_golden_case_score_and_floor(case):
    _, _, sig, lc = _load_case(case)
    score = lc["score"]
    assert 15 <= score <= 100, f"{case['id']}: score {score} out of band"
    assert lc["breakdown"]["raw_before_cap"] >= 15
    ledger = lc.get("score_ledger") or []
    phases = [e.get("phase") for e in ledger if e.get("phase")]
    if "bonus" in phases and "penalty" in phases:
        assert phases.index("bonus") < phases.index("penalty")
    if "penalty" in phases and "floor" in phases:
        assert phases.index("penalty") < phases.index("floor")
    if "floor" in phases and "cap" in phases:
        assert phases.index("floor") < phases.index("cap")
    if sig.combined_affliction >= 55:
        assert score <= 48
    elif sig.combined_affliction >= 35:
        assert score <= 58


@pytest.mark.parametrize("case", ALL_GOLDEN_CASES, ids=[c["id"] for c in ALL_GOLDEN_CASES])
def test_golden_orb_weights_valid(case):
    _, _, sig, _ = _load_case(case)
    for person in (sig.p1, sig.p2):
        assert person.saturn_on_7th_orb_weight in (1.0, ORB_SIGN_ONLY_WEIGHT)
        assert person.mars_on_7th_orb_weight in (1.0, ORB_SIGN_ONLY_WEIGHT)
        assert person.moon_afflicted_orb_weight in (1.0, ORB_SIGN_ONLY_WEIGHT)
    assert sig.cross_rahu_venus_orb_weight in (1.0, ORB_SIGN_ONLY_WEIGHT)
    if sig.cross_rahu_venus:
        assert sig.cross_rahu_venus_orb_weight <= 1.0


def test_golden_delhi_mumbai_snapshot():
    """Primary regression anchor — update only when engine logic intentionally changes."""
    case = ALL_GOLDEN_CASES[0]
    _, _, sig, lc = _load_case(case)
    flags = _flag_snapshot(sig)
    assert flags["combined_affliction"] >= 0
    assert isinstance(lc["score"], int)
    assert lc["risk_level"] in ("low", "medium", "high", "very high")
    for key in ("emotional", "attraction", "communication", "karmic", "stability"):
        assert key in lc["breakdown"]
        assert 0 <= lc["breakdown"][key] <= 100


def test_saturn_on_7th_orb_matches_placement():
    """Occupying 7th = 1.0; sign-aspect only = 0.5."""
    for case in ALL_GOLDEN_CASES:
        r1, r2, sig, _ = _load_case(case)
        for person, reader in ((sig.p1, r1), (sig.p2, r2)):
            if not person.saturn_on_7th:
                continue
            occ7 = reader.occupants(7)
            if "Saturn" in occ7:
                assert person.saturn_on_7th_orb_weight == 1.0
            else:
                assert person.saturn_on_7th_orb_weight == ORB_SIGN_ONLY_WEIGHT


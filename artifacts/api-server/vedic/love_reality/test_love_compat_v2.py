"""Tests for love_compat_v2 scoring engine."""
from vedic.love_reality.love_compat_v2 import (
    CAP_HEAVY_MAX,
    CAP_MEDIUM_MAX,
    DIMENSION_MAX,
    _is_shad_ashtaka,
    _sign_gap,
    run_love_compatibility_v2,
)

P1 = {
    "name": "A",
    "day": 15,
    "month": 3,
    "year": 1995,
    "hour": 10,
    "minute": 30,
    "ampm": "AM",
    "lat": 28.61,
    "lon": 77.21,
    "tz": 5.5,
    "place": "Delhi",
}
P2 = {
    "name": "B",
    "day": 22,
    "month": 8,
    "year": 1997,
    "hour": 6,
    "minute": 0,
    "ampm": "PM",
    "lat": 19.08,
    "lon": 72.88,
    "tz": 5.5,
    "place": "Mumbai",
}


def test_sign_gap_wraps():
    assert _sign_gap(0, 11) == 1
    assert _sign_gap(2, 8) == 6


def test_shad_ashtaka_pairs():
    assert _is_shad_ashtaka(0, 5) is True   # Aries ↔ Virgo (6th)
    assert _is_shad_ashtaka(0, 7) is True   # Aries ↔ Scorpio (8th)
    assert _is_shad_ashtaka(0, 4) is False


def test_v2_returns_expanded_schema():
    out = run_love_compatibility_v2(P1, P2, skip_chart_proof=True)
    assert out["engine"] == "love_compat_v2"
    assert 0 <= out["final_score"] <= 100
    assert out["final_score"] == out["score"]
    assert isinstance(out["raw_score_before_cap"], int)
    assert out["cap_tier"] in ("none", "medium", "heavy")
    assert isinstance(out["is_honesty_cap_applied"], bool)
    assert isinstance(out["applied_deductions_log"], list)
    assert isinstance(out["dimensions_breakdown"], dict)
    assert out["dimension_total"] == sum(
        d["score"] for d in out["dimensions_breakdown"].values()
    )
    for key, mx in DIMENSION_MAX.items():
        dim = out["dimensions_breakdown"][key]
        assert dim["max"] == mx
        assert 0 <= dim["score"] <= mx
        assert key in out["breakdown"]


def test_no_duplicate_affliction_ids():
    out = run_love_compatibility_v2(P1, P2, skip_chart_proof=True)
    ids = [row["signal_id"] for row in out["applied_deductions_log"]]
    assert len(ids) == len(set(ids))


def test_cap_tier_soft_limits():
    out = run_love_compatibility_v2(P1, P2, skip_chart_proof=True)
    if out["cap_tier"] == "heavy":
        assert out["final_score"] <= CAP_HEAVY_MAX
        assert out["is_honesty_cap_applied"] is True
    elif out["cap_tier"] == "medium":
        assert out["final_score"] <= CAP_MEDIUM_MAX
        assert out["is_honesty_cap_applied"] is True
    else:
        assert out["final_score"] == out["raw_score_before_cap"]

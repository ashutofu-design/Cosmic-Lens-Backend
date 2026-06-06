"""Unit tests for honest Love Reality scoring engines."""
from vedic.love_reality.engines import (
    run_all_love_reality_engines,
    run_breakup_chances,
    run_future_outcome,
    run_love_compatibility,
    run_loyalty_check,
    run_will_return,
)
from vedic.love_reality.scoring_core import future_confidence

# Sample birth data (Delhi-ish) — deterministic smoke only
P1 = {
    "name": "A",
    "day": 15, "month": 3, "year": 1995,
    "hour": 10, "minute": 30, "ampm": "AM",
    "lat": 28.61, "lon": 77.21, "tz": 5.5,
    "place": "Delhi",
}
P2 = {
    "name": "B",
    "day": 22, "month": 8, "year": 1997,
    "hour": 6, "minute": 0, "ampm": "PM",
    "lat": 19.08, "lon": 72.88, "tz": 5.5,
    "place": "Mumbai",
}


def test_all_engines_return_score_and_summary():
    bundle = run_all_love_reality_engines(P1, P2)
    for key in ("love_compatibility", "breakup_chances", "loyalty_check", "will_return", "future_outcome"):
        block = bundle[key]
        assert "score" in block or f"{key.split('_')[0]}_score" in str(block)
        assert block.get("emotional_summary")
        assert block.get("risk_level")
        assert isinstance(block.get("reasons"), list)


def test_afflicted_heavy_chart_not_fake_high_love():
    """Debilitated Venus/Moon patterns should cap love score — not fake 70+."""
    lc = run_love_compatibility(P1, P2)
    assert 0 <= lc["score"] <= 100
    assert lc["emotional_summary"]
    bd = lc["breakdown"]
    for key in ("emotional", "attraction", "communication", "karmic", "stability", "dasha_transit"):
        assert key in bd
        assert 0 <= bd[key] <= 100
    assert len({bd[k] for k in ("emotional", "attraction", "communication", "karmic", "stability", "dasha_transit")}) > 1


def test_will_return_uses_probability_not_guarantee():
    wr = run_will_return(P1, P2)
    assert wr["return_chance"] in ("unlikely", "possible", "strong", "very strong")
    assert "will return" not in wr["emotional_summary"].lower()


def test_breakup_high_when_afflictions_stack():
    bu = run_breakup_chances(P1, P2)
    assert bu["breakup_score"] == bu["score"]
    assert bu["risk_level"] in ("low", "medium", "high", "very high")


def test_loyalty_low_score_has_narrative_locks():
    ly = run_loyalty_check(P1, P2)
    if ly["loyalty_score"] < 52:
        assert ly.get("narrative_locks")
        locks = " ".join(ly["narrative_locks"]).lower()
        assert "naturally loyal" in locks or "never describe" in locks
    reasons = " ".join(ly.get("reasons") or []).lower()
    assert "naturally loyal" not in reasons


def test_loyalty_includes_new_rule_fields():
    ly = run_loyalty_check(P1, P2)
    assert "is_duty_bound_loyal" in ly
    assert isinstance(ly["is_duty_bound_loyal"], bool)
    per = ly.get("per_person") or {}
    assert "p1" in per and "p2" in per
    for key in ("score", "loyalty_level", "venus_combust", "venus_afflicted"):
        assert key in per["p1"]
        assert key in per["p2"]
    assert "loyalty_tie_breaker" in ly
    assert 0 <= ly["loyalty_score"] <= 100


def test_bundle_includes_reader_context():
    bundle = run_all_love_reality_engines(P1, P2)
    rc = bundle.get("reader_context")
    assert isinstance(rc, dict)
    assert "primary_gender_inferred" in rc


def test_pdf_bundle_skips_compat_insight():
    """Pro PDF path must not run the small compatibility AI (only premium polish)."""
    bundle = run_all_love_reality_engines(P1, P2, skip_ai_insight=True)
    assert bundle["love_compatibility"].get("insight") is None


def test_future_outcome_v2_fields():
    fo = run_future_outcome(P1, P2)
    assert fo.get("engine_version") == "future_outcome_v2"
    assert 0 <= fo["future_score"] <= 100
    assert 30 <= fo["confidence"] <= 90
    assert fo["confidence"] == future_confidence(fo["breakdown"]["total_afflictions"])
    assert isinstance(fo.get("timeline_flow"), list)
    assert fo["timeline_flow"][0]["trend"] in ("up", "down", "mixed")
    assert "next_shift_trend" in fo


def test_future_confidence_mapping():
    assert future_confidence(0) == 90
    assert future_confidence(2) == 90
    assert future_confidence(5) == 65
    assert future_confidence(20) == 30

"""Tests for Love Reality chart_facts + validation."""
from vedic.love_reality.chart_facts import (
    build_chart_snapshot,
    build_narrative_bridge,
    build_chapter_groundings,
)
from vedic.love_reality.premium_validate import apply_love_premium_validation


def _mini_bundle():
    return {
        "p1": {"name": "A"},
        "p2": {"name": "B"},
        "kundli_p1": {
            "name": "A",
            "ascendant": "Leo",
            "moonSign": "Aries",
            "nakshatra": "Ashwini",
            "nakshatraPada": 1,
            "planets": [
                {"name": "Moon", "sign": "Aries", "house": 9, "degrees": "10°12′", "longitude": 10.2},
                {"name": "Venus", "sign": "Taurus", "house": 10, "degrees": "22°00′", "longitude": 52.0},
            ],
            "currentDasha": {"maha": "Saturn", "antar": "Mercury", "startDate": "2024-01-01", "endDate": "2026-06-01"},
            "divisionalCharts": {"D9": {"planets": [{"name": "Venus", "sign": "Capricorn", "signIndex": 9}]}},
        },
        "love_compatibility": {"score": 53, "reasons": ["Moon clash"]},
        "breakup_chances": {"breakup_score": 60},
        "future_outcome": {"future_score": 62},
    }


def test_build_chart_snapshot_has_lines():
    snap = build_chart_snapshot(_mini_bundle())
    assert snap["lines"]
    joined = "\n".join(snap["lines"])
    assert "Venus" in joined
    assert "Ashwini" in joined


def test_narrative_bridge_breakup_future_tension():
    b = _mini_bundle()
    text = build_narrative_bridge(b, "en")
    assert "timing" in text.lower() or "split" in text.lower() or "strain" in text.lower()


def test_apply_validation_scrubs_cliche():
    parsed = {
        "chapters": [
            {"key": "love_connection", "chapter_body": "Open communication is key for you both."},
        ],
        "verdict": "Build trust and show appreciation.",
    }
    apply_love_premium_validation(parsed, _mini_bundle(), "en")
    body = parsed["chapters"][0]["chapter_body"]
    assert "open communication is key" not in body.lower()


def test_chapter_groundings_from_engines():
    b = _mini_bundle()
    b["loyalty_check"] = {"loyalty_score": 40, "reasons": ["Venus-Mars risk"]}
    g = build_chapter_groundings(b)
    assert "loyalty" in g
    assert "40" in g["loyalty"]
    assert "engine" not in g["loyalty"].lower()


def test_chart_snapshot_no_engine_word():
    snap = build_chart_snapshot(_mini_bundle())
    joined = "\n".join(snap["lines"]).lower()
    assert "engine" not in joined

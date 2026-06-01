"""Tests for Milan Pro chart_facts + validation."""
from vedic.compat.milan_chart_facts import (
    build_ashtakoot_ledger,
    build_chart_snapshot,
    build_narrative_bridge,
    build_chapter_groundings,
    enrich_milan_bundle_for_pdf,
)


def _milan_payload():
    return {
        "p1": {"name": "A"},
        "p2": {"name": "B"},
        "total": 28,
        "max": 36,
        "koots": [
            {"key": "nadi", "label": "Nadi", "score": 8, "max": 8},
            {"key": "gana", "label": "Gana", "score": 5, "max": 6},
        ],
        "kundli_p1": {
            "name": "A",
            "ascendant": "Leo",
            "moonSign": "Aries",
            "nakshatra": "Ashwini",
            "nakshatraPada": 1,
            "planets": [
                {"name": "Moon", "sign": "Aries", "house": 9, "degrees": "10°12′"},
            ],
            "currentDasha": {"maha": "Saturn", "antar": "Mercury"},
        },
        "chapter_scores": {
            "chapters": {
                "ch1": {"score_0_10": 7.2, "drivers": ["Tara strong"], "cautions": []},
                "ch4": {"score_0_10": 4.0, "drivers": [], "cautions": ["Nadi weak"]},
            },
        },
        "kp_couple_promise": {"verdict": "WEAK"},
    }


def test_ashtakoot_ledger_sums_koots():
    ledger = build_ashtakoot_ledger(_milan_payload())
    assert ledger
    assert ledger[-1].get("base") == 28
    joined = " ".join(str(r) for r in ledger).lower()
    assert "engine" not in joined


def test_enrich_adds_snapshot_and_bridge():
    b = enrich_milan_bundle_for_pdf(_milan_payload(), lang="en")
    assert b.get("chart_snapshot", {}).get("lines")
    assert b.get("narrative_bridge")
    assert b.get("ashtakoot_ledger")


def test_chapter_groundings_use_pdf_keys():
    b = enrich_milan_bundle_for_pdf(_milan_payload(), lang="en")
    g = b.get("chapter_groundings") or {}
    assert "emotional_compatibility" in g
    assert "7.2" in g["emotional_compatibility"]
    assert "engine" not in g["emotional_compatibility"].lower()


def test_narrative_bridge_kp_vs_total():
    text = build_narrative_bridge(_milan_payload(), "en")
    assert "kp" in text.lower() or "guna" in text.lower() or "ashtakoot" in text.lower()

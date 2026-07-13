"""Tests: question-relevant blocks from Engine Execution only (not full dump)."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_health.selected_blocks import (
    build_health_selected_blocks,
    classify_health_question_focus,
    question_relevant_blocks_from_execution,
)

_EXEC = {
    "schema_version": "health_engine_execution_v1",
    "d1": {
        "ascendant": "Leo",
        "planets": [
            {"name": "Sun", "sign": "Leo", "house": 1, "dignity": "own", "strength_score": 2},
            {
                "name": "Saturn",
                "sign": "Aries",
                "house": 6,
                "dignity": "debilitated",
                "strength_score": -2,
                "shadbala": {"strength_pct": 40},
            },
            {"name": "Mars", "sign": "Capricorn", "house": 9, "dignity": "exalted", "strength_score": 3},
            {"name": "Venus", "sign": "Virgo", "house": 2, "dignity": "enemy", "strength_score": -1},
        ],
        "afflictions": ["Malefics in H6: Saturn"],
        "house_lords": {
            "h1": {"lord": "Sun", "lord_house": 1, "lord_dignity": "own", "lord_strength_score": 2},
            "h3": {"lord": "Venus", "lord_house": 2, "lord_dignity": "enemy", "lord_strength_score": -1},
            "h6": {
                "lord": "Saturn",
                "lord_house": 6,
                "lord_dignity": "debilitated",
                "lord_strength_score": -2,
                "lord_in_dusthana": True,
            },
            "h9": {"lord": "Mars", "lord_house": 9, "lord_dignity": "exalted", "lord_strength_score": 3},
            "h12": {"lord": "Moon", "lord_house": 4, "lord_dignity": "?", "lord_strength_score": 0},
        },
        "health_houses": [{"house": 6, "lord": "Saturn"}],
        "dimensions": {
            "overall_vitality": {"verdict": "YELLOW"},
            "preventive_risk": {"verdict": "YELLOW"},
            "surgery_risk_tone": {"verdict": "GREEN"},
            "mental_stress": {"verdict": "YELLOW"},
        },
        "sub_flags": {"immune_weak": False},
        "lagnesh": {"lord": "Sun", "lord_house": 1, "lord_dignity": "own", "lord_strength_score": 2},
    },
    "d9": {
        "ascendant": "Aries",
        "planets": [{"name": "Sun", "sign": "Leo", "house": 5, "dignity": "own", "strength_score": 2}],
    },
}


class HealthQuestionRelevantBlocksTests(unittest.TestCase):
    def test_travel_focus_is_specific_not_full_dump(self):
        q = "me jab bhi travel karta hun koi na koi health issue aa jaata he aisa kyun"
        self.assertEqual(classify_health_question_focus(q), "travel_health")
        focus, _, blocks = question_relevant_blocks_from_execution(q, _EXEC)
        self.assertEqual(focus, "travel_health")
        ids = {b["id"] for b in blocks}
        self.assertIn("d1.house_lords.h6", ids)
        self.assertIn("d1.house_lords.h9", ids)
        self.assertNotIn("d1.shadbala", ids)
        self.assertFalse(any("Venus" in i and "H2" in i for i in ids))

    def test_dignity_strength_in_selected_and_ranked(self):
        q = "travel pe health issue kyun"
        pack = build_health_selected_blocks(q, "", execution=_EXEC)
        self.assertEqual(pack["source"], "health_engine_execution")
        saturn = next(b for b in pack["expected_blocks"] if "Saturn" in (b.get("label") or "") or "h6" in b["id"])
        self.assertIn("dignity=", saturn.get("detail") or "")
        self.assertIn("debilitated", (saturn.get("detail") or "").lower())
        # Weak Saturn / h6 should rank before exalted Mars H9 support
        ranks = {b["id"]: b.get("rank") for b in pack["expected_blocks"]}
        self.assertLess(ranks.get("d1.house_lords.h6", 99), ranks.get("d1.house_lords.h9", 1))
        self.assertIn("QUESTION_PRIORITY_FACTS", pack.get("priority_facts_for_llm") or "")

    def test_source_still_engine_execution(self):
        pack = build_health_selected_blocks(
            "travel pe health issue kyun",
            "Saturn 6th ghar me hai.",
            execution=_EXEC,
        )
        self.assertEqual(pack["source"], "health_engine_execution")
        self.assertEqual(pack["focus"], "travel_health")
        self.assertLessEqual(len(pack["expected_blocks"]), 25)

    def test_invented_planet_not_used(self):
        pack = build_health_selected_blocks(
            "q",
            "Jupiter 9th ghar me strong hai.",
            execution=_EXEC,
        )
        self.assertNotIn("Jupiter H9", pack["used_in_answer"]["planet_house_cites"])


if __name__ == "__main__":
    unittest.main()

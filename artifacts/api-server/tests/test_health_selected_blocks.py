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
            {"name": "Sun", "sign": "Leo", "house": 1},
            {"name": "Saturn", "sign": "Capricorn", "house": 6},
            {"name": "Mars", "sign": "Libra", "house": 9},
            {"name": "Venus", "sign": "Virgo", "house": 2},
        ],
        "afflictions": ["Malefics in H6: Saturn"],
        "house_lords": {
            "h1": {"lord": "Sun", "lord_house": 1},
            "h3": {"lord": "Venus", "lord_house": 2},
            "h6": {"lord": "Saturn", "lord_house": 6},
            "h9": {"lord": "Mars", "lord_house": 9},
            "h12": {"lord": "Moon", "lord_house": 4},
        },
        "health_houses": [{"house": 6, "lord": "Saturn"}],
        "dimensions": {
            "overall_vitality": {"verdict": "YELLOW"},
            "preventive_risk": {"verdict": "YELLOW"},
            "surgery_risk_tone": {"verdict": "GREEN"},
            "mental_stress": {"verdict": "YELLOW"},
        },
        "sub_flags": {"immune_weak": False},
        "shadbala": {"Sun": {"total": 1}},
        "aspects": [{"planet": "Saturn"}],
        "karakas": {"Moon": {}},
    },
    "d9": {
        "ascendant": "Aries",
        "planets": [{"name": "Sun", "sign": "Leo", "house": 5}],
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
        # Full dump keys should NOT all appear
        self.assertNotIn("d1.shadbala", ids)
        self.assertNotIn("d1.aspects", ids)
        self.assertNotIn("d1.karakas", ids)
        # Venus H2 not travel house — should not appear as planet pick
        self.assertFalse(any("Venus" in i and "H2" in i for i in ids))

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

"""Tests: selected blocks come only from Engine Execution."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_health.selected_blocks import (
    available_blocks_from_execution,
    build_health_selected_blocks,
)

_EXEC = {
    "schema_version": "health_engine_execution_v1",
    "d1": {
        "ascendant": "Leo",
        "planets": [
            {"name": "Sun", "sign": "Leo", "house": 1},
            {"name": "Saturn", "sign": "Capricorn", "house": 6},
        ],
        "afflictions": ["Malefics in H6: Saturn"],
        "house_lords": {
            "h1": {"lord": "Sun", "lord_house": 1},
            "h6": {"lord": "Saturn", "lord_house": 6},
            "h9": {"lord": "Mars", "lord_house": 3},
        },
        "health_houses": [{"house": 6, "lord": "Saturn"}],
        "dimensions": {
            "overall_vitality": {"verdict": "YELLOW"},
            "preventive_risk": {"verdict": "YELLOW"},
        },
        "sub_flags": {"immune_weak": False},
    },
    "d9": {
        "ascendant": "Aries",
        "planets": [{"name": "Sun", "sign": "Leo", "house": 5}],
    },
}


class HealthSelectedBlocksFromExecutionTests(unittest.TestCase):
    def test_available_only_from_execution(self):
        blocks = available_blocks_from_execution(_EXEC)
        ids = {b["id"] for b in blocks}
        self.assertIn("d1.planets", ids)
        self.assertIn("d1.house_lords.h6", ids)
        self.assertIn("d1.dimensions.preventive_risk", ids)
        self.assertIn("d9.planets", ids)
        # Hardcoded travel heuristic ids must NOT appear unless in EE
        self.assertNotIn("d1.planets@3,6,9,12", ids)

    def test_used_cites_must_match_execution(self):
        pack = build_health_selected_blocks(
            "travel pe health issue kyun",
            "Saturn 6th ghar me hai, isliye tendency dikhti hai.",
            execution=_EXEC,
        )
        self.assertEqual(pack["source"], "health_engine_execution")
        used = pack["used_in_answer"]
        self.assertIn("Saturn H6", used["planet_house_cites"])
        # Jupiter not in EE planets → cannot invent
        pack2 = build_health_selected_blocks(
            "q",
            "Jupiter 9th ghar me strong hai.",
            execution=_EXEC,
        )
        self.assertNotIn("Jupiter H9", pack2["used_in_answer"]["planet_house_cites"])

    def test_empty_execution(self):
        pack = build_health_selected_blocks("meri sehat", "ok", execution={})
        self.assertEqual(pack["expected_blocks"], [])
        self.assertTrue(any("empty" in n.lower() or "missing" in n.lower() for n in pack["overlap_notes"]))


if __name__ == "__main__":
    unittest.main()

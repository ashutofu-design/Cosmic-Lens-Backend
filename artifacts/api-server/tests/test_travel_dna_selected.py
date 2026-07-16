"""Travel DNA selected blocks / presenter."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_mr.types import EngineResult
from ask_travel.presenter import TRAVEL_ENGINE_EXECUTION_JSON_LABEL, to_travel_llm_payload
from ask_travel.selected_blocks import build_travel_selected_blocks
from travel_static.travel_facts import compute_travel_engine_execution

_KUNDLI = {
    "ascendant": "Sagittarius",
    "ascendantDeg": 255.0,
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7, "longitude": 75.0},
        {"name": "Saturn", "sign": "Virgo", "house": 10, "longitude": 165.0},
        {"name": "Mars", "sign": "Cancer", "house": 8, "longitude": 105.0},
        {"name": "Venus", "sign": "Leo", "house": 9, "longitude": 135.0},
        {"name": "Mercury", "sign": "Aries", "house": 5, "longitude": 15.0},
        {"name": "Jupiter", "sign": "Pisces", "house": 4, "longitude": 345.0},
        {"name": "Rahu", "sign": "Aquarius", "house": 3, "longitude": 315.0},
        {"name": "Ketu", "sign": "Leo", "house": 9, "longitude": 135.0},
        {"name": "Sun", "sign": "Capricorn", "house": 2, "longitude": 285.0},
    ],
}


class TravelDnaSelectedTests(unittest.TestCase):
    def test_selected_blocks_and_presenter(self):
        q = "Visa approve hoga kya?"
        pack = compute_travel_engine_execution(
            _KUNDLI, question=q, routing_label="visa_theme",
        )
        self.assertEqual(pack.get("schema_version"), "travel_engine_execution_v1")
        self.assertIn("foreign_travel", pack.get("dimensions") or {})

        selected = build_travel_selected_blocks(
            q, "", meta={"routing_label": "visa_theme"}, execution=pack,
        )
        self.assertTrue(selected.get("applies"))
        self.assertEqual(selected.get("focus"), "visa_theme")
        self.assertTrue(selected.get("expected_blocks") or selected.get("priority_facts_for_llm"))

        result = EngineResult(
            archetype="visa_theme",
            verdict="",
            confidence="medium",
            word_budget=70,
            answer_plan="",
            summary=[],
            evidence=[],
            ignore=[],
            checks={
                "travel_engine_execution": pack,
                "routing_label": "visa_theme",
                "unified_execution": True,
            },
        )
        text = to_travel_llm_payload(result, question=q)
        self.assertTrue(text.startswith(TRAVEL_ENGINE_EXECUTION_JSON_LABEL))
        self.assertIn("QUESTION_PRIORITY_FACTS", text)


if __name__ == "__main__":
    unittest.main()

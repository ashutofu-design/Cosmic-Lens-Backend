"""Finance DNA selected blocks / presenter."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_finance.presenter import FINANCE_ENGINE_EXECUTION_JSON_LABEL, to_finance_llm_payload
from ask_finance.selected_blocks import build_finance_selected_blocks
from ask_mr.types import EngineResult
from finance_static.finance_facts import compute_finance_engine_execution

_KUNDLI = {
    "ascendant": "Leo",
    "planets": [
        {"name": "Sun", "sign": "Leo", "house": 1},
        {"name": "Moon", "sign": "Taurus", "house": 10},
        {"name": "Mars", "sign": "Capricorn", "house": 6},
        {"name": "Mercury", "sign": "Virgo", "house": 2},
        {"name": "Jupiter", "sign": "Sagittarius", "house": 5},
        {"name": "Venus", "sign": "Libra", "house": 3},
        {"name": "Saturn", "sign": "Aquarius", "house": 7},
        {"name": "Rahu", "sign": "Aries", "house": 9},
        {"name": "Ketu", "sign": "Libra", "house": 3},
    ],
}


class FinanceDnaSelectedTests(unittest.TestCase):
    def test_selected_blocks_and_presenter(self):
        q = "meri savings capacity kaisi hai?"
        pack = compute_finance_engine_execution(
            _KUNDLI, question=q, routing_label="savings_capacity",
        )
        selected = build_finance_selected_blocks(
            q, "", meta={"routing_label": "savings_capacity"}, execution=pack,
        )
        self.assertTrue(selected.get("applies"))
        self.assertEqual(selected.get("focus"), "savings_capacity")
        self.assertTrue(selected.get("expected_blocks") or selected.get("priority_facts_for_llm"))

        result = EngineResult(
            archetype="savings_capacity",
            verdict="",
            confidence="medium",
            word_budget=70,
            answer_plan="",
            summary=[],
            evidence=[],
            ignore=[],
            checks={
                "finance_engine_execution": pack,
                "routing_label": "savings_capacity",
                "unified_execution": True,
            },
        )
        text = to_finance_llm_payload(result, question=q)
        self.assertTrue(text.startswith(FINANCE_ENGINE_EXECUTION_JSON_LABEL))
        self.assertIn("QUESTION_PRIORITY_FACTS", text)


if __name__ == "__main__":
    unittest.main()

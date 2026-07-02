"""LLM path for interpretation/combo — chart_fact only for pure placement."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chart_fact_answer import (
    is_pure_chart_fact_lookup,
    needs_llm_chart_answer,
    try_deterministic_chart_fact,
)

_KUNDLI = {
    "ascendant": "Leo",
    "planets": [{"name": "Sun", "house": 10, "sign": "Taurus"}],
    "divisionalCharts": {
        "D10": {
            "ascendant": "Aries",
            "planets": [{"name": "Sun", "house": 5, "sign": "Capricorn"}],
        },
    },
}


class TestNeedsLlmChartAnswer(unittest.TestCase):
    def test_d10_se_kya_hota_he_needs_llm(self):
        q = "D10 mein Sun Makar rashi mein hai (5th house). se kya hota he"
        self.assertTrue(needs_llm_chart_answer(q))
        self.assertFalse(is_pure_chart_fact_lookup(q))
        self.assertIsNone(try_deterministic_chart_fact(q, _KUNDLI))

    def test_d10_career_effect_needs_llm(self):
        q = "D10 mein Sun mere career par kya effect dalta hai"
        self.assertTrue(needs_llm_chart_answer(q))
        self.assertFalse(is_pure_chart_fact_lookup(q))
        self.assertIsNone(try_deterministic_chart_fact(q, _KUNDLI))

    def test_planet_combo_needs_llm(self):
        q = "Mars aur Saturn ka combination kya karta hai"
        self.assertTrue(needs_llm_chart_answer(q))
        self.assertIsNone(try_deterministic_chart_fact(q, _KUNDLI))

    def test_pure_d10_placement_still_chart_fact(self):
        q = "D10 mein Sun kis house me hai"
        self.assertFalse(needs_llm_chart_answer(q))
        det = try_deterministic_chart_fact(q, _KUNDLI)
        self.assertIsNotNone(det)
        self.assertIn("D10", det.get("text", ""))


if __name__ == "__main__":
    unittest.main()

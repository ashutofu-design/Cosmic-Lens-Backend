"""Chart-fact must not swallow love-style interpretation questions."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_mr.classifier import classify_mr_archetype
from chart_fact_answer import (
    is_chart_lookup_question,
    is_domain_life_area_interpretation_question,
    try_deterministic_chart_fact,
)


class TestChartFactLoveStyle(unittest.TestCase):
    def test_venus_love_style_not_chart_lookup(self):
        q = "Meri kundli me venus ki position mere love style ko kaise affect kar rashi hai"
        self.assertTrue(is_domain_life_area_interpretation_question(q))
        self.assertFalse(is_chart_lookup_question(q))
        self.assertIsNone(
            try_deterministic_chart_fact(
                q,
                {"planets": [{"name": "Venus", "house": 9, "sign": "Leo"}]},
            )
        )

    def test_pure_venus_placement_still_chart_lookup(self):
        q = "Venus kis house me hai"
        self.assertFalse(is_domain_life_area_interpretation_question(q))
        self.assertTrue(is_chart_lookup_question(q))

    def test_love_style_routes_partner_nature(self):
        q = "Meri kundli me venus ki position mere love style ko kaise affect karti hai"
        self.assertEqual(classify_mr_archetype(q), "partner_nature")


if __name__ == "__main__":
    unittest.main()

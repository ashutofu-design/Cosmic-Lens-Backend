"""Route from LLM understanding to specific engines."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_route_from_understanding import (
    apply_understanding_routing,
    is_native_love_chart_question,
)


class TestRouteFromUnderstanding(unittest.TestCase):
    def test_native_true_love_detected(self):
        q = "Kya meri kundli me sacha pyaar true love milne ka yog likha hai"
        self.assertTrue(is_native_love_chart_question(q))

    def test_understanding_routes_love_static_dating(self):
        q = "Kya meri kundli me sacha pyaar true love milne ka yog likha hai"
        understanding = {
            "question_summary": "User wants to know if true love is indicated in their chart",
            "understanding_source": "understand_llm",
        }
        out = apply_understanding_routing(q, understanding, {"domain": "general"})
        self.assertEqual(out.get("domain"), "love")
        self.assertFalse(out.get("is_timing"))
        self.assertEqual(out.get("mr_archetype"), "dating_courtship")

    def test_timing_from_summary(self):
        q = "Prem kab milega"
        understanding = {"question_summary": "User asks when they will find love"}
        out = apply_understanding_routing(q, understanding, {"domain": "general"})
        self.assertTrue(out.get("is_timing"))


if __name__ == "__main__":
    unittest.main()

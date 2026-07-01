"""Venus love-style questions must not route to health/skin_health."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_engine_verification import (
    apply_love_life_area_static_flags,
    apply_pre_route_guards,
    verify_static_engine_selection,
)
from ask_health.health_registry import detect_health_archetype, is_health_static_question
from ask_chart_open_qa import (
    build_question_relevant_chart_facts,
    is_native_self_chart_interpretation_question,
    run_open_chart_qa,
    should_use_open_chart_qa,
)


VENUS_LOVE_STYLE_Q = (
    "Meri kundli me venus ki position mere love style ko kaise affect kar rashi hai"
)


class TestHealthLoveStyleRouting(unittest.TestCase):
    def test_not_health_static(self):
        self.assertFalse(is_health_static_question(VENUS_LOVE_STYLE_Q))

    def test_no_health_archetype(self):
        self.assertIsNone(detect_health_archetype(VENUS_LOVE_STYLE_Q))

    def test_native_self_interpretation(self):
        self.assertTrue(is_native_self_chart_interpretation_question(VENUS_LOVE_STYLE_Q))
        self.assertTrue(should_use_open_chart_qa(VENUS_LOVE_STYLE_Q))

    def test_love_life_flags_open_chart_not_mr(self):
        intent: dict = {"domain": "health", "health_archetype": "skin_health"}
        is_mr, is_health = apply_love_life_area_static_flags(
            VENUS_LOVE_STYLE_Q,
            is_mr_static=False,
            is_health_static=True,
            llm_intent=intent,
        )
        self.assertFalse(is_mr)
        self.assertFalse(is_health)
        self.assertTrue(intent.get("open_chart_qa"))
        self.assertEqual(intent.get("mr_archetype"), "open_chart_qa")

    def test_open_chart_facts_include_venus(self):
        kundli = {
            "ascendant": "Aries",
            "planets": [
                {"name": "Venus", "house": 9, "sign": "Leo"},
                {"name": "Moon", "house": 7, "sign": "Gemini"},
            ],
        }
        facts = build_question_relevant_chart_facts(kundli, VENUS_LOVE_STYLE_Q)
        joined = " ".join(facts).lower()
        self.assertIn("venus", joined)
        self.assertNotIn("7th house sign baseline", joined)

    def test_open_chart_qa_engine(self):
        kundli = {
            "ascendant": "Aries",
            "planets": [{"name": "Venus", "house": 9, "sign": "Leo"}],
        }
        res = run_open_chart_qa(kundli, VENUS_LOVE_STYLE_Q)
        self.assertEqual(res.archetype, "open_chart_qa")
        self.assertTrue(res.checks.get("open_chart_qa"))

    def test_pre_route_guards_suppress_all_engines(self):
        flags = {"health": True, "mr": True, "career": False}
        out, notes = apply_pre_route_guards(flags, VENUS_LOVE_STYLE_Q)
        self.assertFalse(out["health"])
        self.assertFalse(out["mr"])
        self.assertIn("open_chart_qa:native_self_interpretation", notes)

    def test_engine_verification_flags_health_wrong(self):
        result = verify_static_engine_selection(
            VENUS_LOVE_STYLE_Q,
            engine_key="health",
            archetype="skin_health",
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.action, "d1_open_chart")


if __name__ == "__main__":
    unittest.main()

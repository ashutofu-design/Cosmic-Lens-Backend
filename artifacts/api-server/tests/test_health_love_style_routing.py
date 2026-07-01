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
from ask_mr.classifier import classify_mr_archetype


VENUS_LOVE_STYLE_Q = (
    "Meri kundli me venus ki position mere love style ko kaise affect kar rashi hai"
)


class TestHealthLoveStyleRouting(unittest.TestCase):
    def test_not_health_static(self):
        self.assertFalse(is_health_static_question(VENUS_LOVE_STYLE_Q))

    def test_no_health_archetype(self):
        self.assertIsNone(detect_health_archetype(VENUS_LOVE_STYLE_Q))

    def test_mr_partner_nature(self):
        self.assertEqual(classify_mr_archetype(VENUS_LOVE_STYLE_Q), "partner_nature")

    def test_love_life_flags_force_mr(self):
        intent: dict = {"domain": "health", "health_archetype": "skin_health"}
        is_mr, is_health = apply_love_life_area_static_flags(
            VENUS_LOVE_STYLE_Q,
            is_mr_static=False,
            is_health_static=True,
            llm_intent=intent,
        )
        self.assertTrue(is_mr)
        self.assertFalse(is_health)
        self.assertEqual(intent.get("domain"), "love")
        self.assertIsNone(intent.get("health_archetype"))
        self.assertEqual(intent.get("mr_archetype"), "partner_nature")

    def test_pre_route_guards_suppress_health(self):
        flags = {"health": True, "mr": False, "career": False}
        out, notes = apply_pre_route_guards(flags, VENUS_LOVE_STYLE_Q)
        self.assertFalse(out["health"])
        self.assertTrue(out["mr"])
        self.assertIn("mr:love_life_area_interpretation", notes)

    def test_engine_verification_flags_health_wrong(self):
        result = verify_static_engine_selection(
            VENUS_LOVE_STYLE_Q,
            engine_key="health",
            archetype="skin_health",
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.action, "reroute_mr")
        self.assertEqual(result.mr_archetype, "partner_nature")


if __name__ == "__main__":
    unittest.main()

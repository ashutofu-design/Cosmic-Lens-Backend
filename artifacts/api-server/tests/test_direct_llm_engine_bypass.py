"""Static engine bypass — divisional/chart Q must not hit wrong domain engine."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_children.children_registry import is_children_static_question
from ask_engine_resolver import resolve_static_engine_route
from ask_engine_verification import apply_pre_route_guards
from ask_routing_policy import should_bypass_static_engines_for_direct_llm


class TestDirectLlmEngineBypass(unittest.TestCase):
    def test_d10_not_children_engine(self):
        q = "D10 mein Sun Makar rashi mein hai (5th house se kya hota hai"
        self.assertFalse(is_children_static_question(q))

    def test_resolver_no_winner_for_d10(self):
        q = "D10 mein Sun Makar rashi mein hai (5th house se kya hota hai"
        flags = {
            "education": False,
            "children": True,
            "property": False,
            "vehicle": False,
            "travel": False,
            "litigation": False,
            "gap": False,
            "network": False,
            "luck": False,
            "career": False,
            "finance": False,
            "health": False,
            "mr": False,
        }
        guarded, notes = apply_pre_route_guards(flags, q)
        self.assertFalse(any(guarded.values()), notes)
        self.assertTrue(any("direct_llm" in n for n in notes))

        final, route = resolve_static_engine_route(q, flags=flags)
        self.assertIsNone(route.engine_key)
        self.assertIn("divisional", route.reason)

    def test_santan_question_still_children(self):
        q = "Kya mujhe santan hogi?"
        bypass, _ = should_bypass_static_engines_for_direct_llm(q)
        self.assertFalse(bypass)
        self.assertTrue(is_children_static_question(q))


if __name__ == "__main__":
    unittest.main()

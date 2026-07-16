"""answer_mode brain — engine vs LLM vs chart-fact."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_answer_mode import infer_answer_mode, resolve_answer_mode
from ask_master_router import resolve_ask_route
from ask_routing_policy import should_bypass_static_engines_for_direct_llm


class TestAnswerMode(unittest.TestCase):
    def test_theory_dignity_is_llm_knowledge(self):
        q = "6th house me deblited planet acha he ya exalted"
        self.assertEqual(resolve_answer_mode(q), "llm_knowledge")
        bypass, reason = should_bypass_static_engines_for_direct_llm(q)
        self.assertTrue(bypass)
        self.assertIn("llm", reason)
        route = resolve_ask_route(q)
        self.assertEqual(route.path, "chart_llm")

    def test_manglik_concept_llm(self):
        q = "manglik kya hota hai matlab"
        self.assertIn(resolve_answer_mode(q), ("llm_knowledge", "llm_chart"))
        route = resolve_ask_route(q)
        self.assertEqual(route.path, "chart_llm")

    def test_career_personal_stays_engine_path(self):
        q = "Meri career kaisi rahegi"
        # May be engine via classifier, or timing elsewhere — must NOT force llm_knowledge
        mode = resolve_answer_mode(q)
        self.assertEqual(mode, "engine")
        bypass, _ = should_bypass_static_engines_for_direct_llm(q)
        self.assertFalse(bypass)

    def test_pure_house_lookup_chart_fact(self):
        q = "Mere 10th house mein kaun se graha hain"
        # chart_fact path disabled — must not resolve to chart_fact
        mode = resolve_answer_mode(q)
        self.assertNotEqual(mode, "chart_fact")
        self.assertIn(mode, ("llm_chart", "llm_knowledge", "engine"))

    def test_understand_engine_overridden_for_theory(self):
        q = "6th house me debilitated planet accha hai ya exalted"
        intent = {"answer_mode": "engine", "domain": "health"}
        self.assertEqual(resolve_answer_mode(q, intent), "llm_knowledge")

    def test_d10_career_personal_not_bypassed(self):
        q = "D10 chart mein meri career kaisi rahegi"
        bypass, _ = should_bypass_static_engines_for_direct_llm(q)
        self.assertFalse(bypass)
        self.assertEqual(infer_answer_mode(q), "engine")


if __name__ == "__main__":
    unittest.main()

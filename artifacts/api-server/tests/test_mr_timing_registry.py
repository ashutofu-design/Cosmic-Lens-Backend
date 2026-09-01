"""Tests for MR static vs LLM timing override."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_love.timing_registry import is_love_timing_question
from ask_mr.classifier import classify_mr_archetype
from ask_mr.timing_registry import (
    has_explicit_timing_anchor,
    is_marriage_timing_question,
    is_mr_static_question,
    mr_static_overrides_llm_timing,
    repair_llm_intent_mr_static_timing,
)


class TestMrTimingRegistry(unittest.TestCase):
    def test_partner_appearance_is_static_not_timing(self):
        q = "Mera partner dikhne me kaisa hoga. attractive aur good-looking hoga kya"
        self.assertEqual(classify_mr_archetype(q), "spouse_appearance")
        self.assertFalse(has_explicit_timing_anchor(q))
        self.assertTrue(is_mr_static_question(q))
        self.assertTrue(mr_static_overrides_llm_timing(q, {"is_timing": True, "domain": "love"}))
        self.assertFalse(
            is_love_timing_question(q, {"domain": "love", "is_timing": True}),
        )

    def test_partner_kab_milega_stays_timing(self):
        q = "Mera partner kab milega"
        self.assertTrue(has_explicit_timing_anchor(q))
        self.assertFalse(is_mr_static_question(q))

    def test_repair_llm_intent_clears_timing(self):
        q = "Mera partner dikhne me kaisa hoga. attractive aur good-looking hoga kya"
        intent = {"domain": "love", "is_timing": True, "mr_archetype": None}
        self.assertTrue(repair_llm_intent_mr_static_timing(q, intent))
        self.assertFalse(intent["is_timing"])
        self.assertEqual(intent["mr_archetype"], "spouse_appearance")

    def test_apply_understanding_routing_keeps_static(self):
        from ask_route_from_understanding import apply_understanding_routing

        q = "Mera partner dikhne me kaisa hoga. attractive aur good-looking hoga kya"
        out = apply_understanding_routing(
            q,
            {"question_summary": "Partner attractive hoga ya nahi"},
            {"domain": "love", "is_timing": True, "confidence": 0.95, "source": "llm"},
        )
        self.assertFalse(out.get("is_timing"))
        self.assertEqual(out.get("mr_archetype"), "spouse_appearance")

    def test_timing_only_with_kab_when(self):
        from ask_mr.timing_registry import question_requests_timing

        q_static = "Mera partner dikhne me kaisa hoga attractive hoga kya"
        q_when = "Mera partner kab milega"
        self.assertFalse(question_requests_timing(q_static))
        self.assertTrue(question_requests_timing(q_when))
        self.assertFalse(
            __import__("ask_love.timing_registry", fromlist=["is_love_timing_question"]).is_love_timing_question(
                q_static, {"domain": "love", "is_timing": True}
            )
        )

    def test_love_milega_llm_timing_without_kab_is_static(self):
        from ask_mr.timing_registry import question_requests_timing

        q = "Kya mujhe life me true love milega?"
        llm = {"domain": "love", "is_timing": True}
        self.assertFalse(has_explicit_timing_anchor(q))
        self.assertFalse(question_requests_timing(q, llm))
        self.assertTrue(is_mr_static_question(q))

    def test_love_life_stable_chalega_is_static_not_timing(self):
        from ask_mr.timing_registry import question_requests_timing
        from ask_master_router import resolve_ask_route

        q = "kya mere love life stable chalega"
        self.assertFalse(has_explicit_timing_anchor(q))
        self.assertFalse(question_requests_timing(q, {"domain": "love", "is_timing": True}))
        self.assertEqual(classify_mr_archetype(q), "relationship_future")
        admin = {
            "dna_routing_applied": True,
            "domain": "love",
            "mr_archetype": "relationship_future",
            "question_dna": {
                "questions": [{
                    "domain": "love",
                    "bucket": "relationship_future",
                    "engine_archetype": "relationship_future",
                    "timing": False,
                    "confidence": 0.95,
                    "bucket_match_confidence": "high",
                }],
            },
        }
        route = resolve_ask_route(q, llm_intent_admin=admin)
        self.assertFalse(route.is_timing)
        self.assertEqual(route.archetype, "relationship_future")
        self.assertEqual(route.reason, "dna_static_authority")

    def test_kab_tak_chalega_stays_timing(self):
        q = "Humare rishte me stressful phase kab tak chalega"
        self.assertTrue(has_explicit_timing_anchor(q))

    def test_marriage_timing_detected_not_love(self):
        q = "Meri shaadi kab hogi?"
        self.assertTrue(is_marriage_timing_question(q))
        self.assertFalse(
            is_love_timing_question(q, {"domain": "love", "is_timing": True}),
        )

    def test_apply_understanding_routing_repairs_marriage_timing(self):
        from ask_route_from_understanding import apply_understanding_routing

        q = "Meri shaadi kab hogi?"
        out = apply_understanding_routing(
            q,
            {"question_summary": "Marriage timing", "domain": "general"},
            {"domain": "general", "is_timing": False, "confidence": 0.3},
        )
        self.assertEqual(out.get("domain"), "marriage")
        self.assertTrue(out.get("is_timing"))
        self.assertEqual(out.get("mr_archetype"), "marriage_timing")


if __name__ == "__main__":
    unittest.main()

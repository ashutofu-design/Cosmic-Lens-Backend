"""Routing policy — engine first, LLM fallback, off-topic refused."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_routing_policy import (
    is_cosmic_domain_concept_question,
    is_cosmic_domain_question,
    no_engine_llm_fallback_eligible,
)
from ask_scope_gate import assess_ask_scope


class TestRoutingPolicy(unittest.TestCase):
    def test_numerology_in_scope(self):
        q = "numerology me life path 7 kya hota hai"
        self.assertTrue(is_cosmic_domain_question(q))
        self.assertTrue(assess_ask_scope(q).allowed)

    def test_vastu_in_scope(self):
        q = "south kitchen vastu me theek hai kya"
        self.assertTrue(assess_ask_scope(q).allowed)

    def test_biryani_off_topic(self):
        q = "biryani recipe batao"
        self.assertFalse(assess_ask_scope(q).allowed)

    def test_concept_no_engine_llm_ok(self):
        q = "manglik kya hota hai matlab"
        self.assertTrue(is_cosmic_domain_concept_question(q))
        self.assertTrue(no_engine_llm_fallback_eligible(q, qtype="STATIC"))

    def test_career_no_engine_llm_ok(self):
        q = "Meri career kaisi rahegi"
        self.assertTrue(no_engine_llm_fallback_eligible(q, {"domain": "career"}, qtype="STATIC"))

    def test_d10_interpret_no_engine_llm_ok(self):
        q = "D10 mein Sun Makar rashi mein hai (5th house) se kya hota he"
        self.assertTrue(no_engine_llm_fallback_eligible(q, qtype="STATIC"))

    def test_d10_bypasses_static_engines(self):
        from ask_routing_policy import should_bypass_static_engines_for_direct_llm

        q = "D10 mein Sun Makar rashi mein hai (5th house se kya hota hai"
        bypass, reason = should_bypass_static_engines_for_direct_llm(q)
        self.assertTrue(bypass)
        self.assertIn("divisional", reason)

    def test_career_plain_still_uses_engine(self):
        from ask_routing_policy import should_bypass_static_engines_for_direct_llm

        q = "Meri career kaisi rahegi"
        bypass, _ = should_bypass_static_engines_for_direct_llm(q)
        self.assertFalse(bypass)


if __name__ == "__main__":
    unittest.main()

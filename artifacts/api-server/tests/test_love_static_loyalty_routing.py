"""Static love loyalty/betrayal must not route as love timing."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_hard_guards import enforce_engine_only_or_refuse, mandatory_domain_chart_fallback_eligible
from ask_love.timing_registry import (
    is_love_static_loyalty_question,
    is_love_timing_question,
)
from ask_marriage_relationship_slice import is_marriage_relationship_static_question

_BETRAYAL_Q = "Kya mujhse love life me dhoka milega ya dhoka nehi milega"
_TIMING_Q = "Mere jeevan mein pehli baar prem sambandh ka yog kab banega"
_TIMING_BETRAYAL_Q = "Mujhe kab pata chalega ki mera partner dhoka de raha hai"


class TestLoveStaticLoyaltyRouting(unittest.TestCase):
    def test_dhoka_milega_not_love_timing(self):
        self.assertFalse(is_love_timing_question(_BETRAYAL_Q))

    def test_dhoka_milega_is_static_loyalty(self):
        self.assertTrue(is_love_static_loyalty_question(_BETRAYAL_Q))

    def test_dhoka_milega_is_mr_static(self):
        self.assertTrue(is_marriage_relationship_static_question(_BETRAYAL_Q))

    def test_kab_prem_sambandh_still_love_timing(self):
        self.assertTrue(is_love_timing_question(_TIMING_Q))

    def test_kab_dhoka_partner_is_love_timing(self):
        self.assertTrue(is_love_timing_question(_TIMING_BETRAYAL_Q))

    def test_betrayal_fallback_without_summary_when_loyalty_regex(self):
        self.assertTrue(
            mandatory_domain_chart_fallback_eligible(
                _BETRAYAL_Q,
                {"domain": "love", "is_timing": False},
                checks={"is_mr_static": True, "slice_type": "full_compact"},
            )
        )

    def test_betrayal_not_refused_when_understood(self):
        llm = {
            "domain": "love",
            "is_timing": False,
            "question_summary": "User wants to know about betrayal in love life",
        }
        out = enforce_engine_only_or_refuse(
            question=_BETRAYAL_Q,
            qtype="STATIC",
            llm_intent=llm,
            checks={"is_mr_static": True, "slice_type": "full_compact"},
            slice_meta={},
        )
        self.assertIsNone(out)

    def test_betrayal_not_property_engine(self):
        from ask_property.property_registry import (
            detect_property_archetype,
            is_property_static_question,
        )

        self.assertFalse(is_property_static_question(_BETRAYAL_Q))
        self.assertIsNone(detect_property_archetype(_BETRAYAL_Q))

    def test_betrayal_routes_loyalty_trust_not_dating(self):
        from ask_mr.classifier import classify_mr_archetype

        self.assertEqual(classify_mr_archetype(_BETRAYAL_Q), "loyalty_trust")

    def test_broker_property_dhoka_still_property(self):
        from ask_property.property_registry import detect_property_archetype

        q = (
            "Broker mujhe dhoka toh nahi de raha? "
            "Property ke rates sahi hain ya over-priced hain?"
        )
        self.assertEqual(detect_property_archetype(q), "property_risk")


if __name__ == "__main__":
    unittest.main()

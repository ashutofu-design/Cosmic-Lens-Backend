"""Engine match gate — DNA must lock correct engine before answer."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_engine_match_gate import (
    coerce_admin_dna_for_routing,
    ensure_correct_engine_route,
    expected_engine_from_admin,
    verify_engine_match,
)
from ask_execution_gatekeeper import enforce_dna_routing_flags
from ask_understand_phase2 import understand_to_admin


_ALL = (
    "education", "children", "property", "vehicle", "travel",
    "litigation", "gap", "network", "luck", "career", "finance", "health", "mr",
)


class EngineMatchGateTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_ENGINE_MATCH_GATE"] = "1"
        os.environ["ASK_DNA_ROUTING_ENFORCE"] = "1"
        os.environ["ASK_ENGINE_MATCH_DEADLINE_S"] = "8"

    def test_phase2_partner_loyalty_coerces_to_trust_and_mr(self):
        admin = understand_to_admin(
            {
                "branch": "engine",
                "domain": "relationship",
                "archetype": "partner_loyalty",
                "timing": False,
                "question_summary": "User wants to know if partner is loyal",
                "confidence": 0.9,
                "subject": "partner",
                "target": "partner",
                "question_type": "prediction",
            },
            question="Partner loyal hai kya?",
        )
        self.assertEqual(admin["domain"], "love")
        item = admin["question_dna"]["questions"][0]
        self.assertEqual(item["domain"], "love")
        self.assertEqual(item["bucket"], "trust_loyalty")
        self.assertEqual(item.get("engine_archetype"), "loyalty_trust")
        exp = expected_engine_from_admin(admin)
        self.assertTrue(exp["requires_engine"])
        self.assertEqual(exp["engine_key"], "mr")

    def test_gate_opens_only_for_mr_on_loyalty(self):
        admin = understand_to_admin(
            {
                "branch": "engine",
                "domain": "love",
                "archetype": "partner_loyalty",
                "timing": False,
                "question_summary": "Loyalty check for partner",
                "confidence": 0.88,
                "subject": "partner",
                "question_type": "prediction",
            },
            question="Kya wo dhoka degi?",
        )
        wrong = {k: False for k in _ALL}
        wrong["career"] = True
        decision = ensure_correct_engine_route(
            "Kya wo dhoka degi?",
            admin,
            wrong,
            deadline_s=5,
        )
        self.assertTrue(decision.ok)
        self.assertEqual(decision.path, "engine")
        self.assertEqual(decision.engine_key, "mr")
        self.assertTrue(decision.flags.get("mr"))
        self.assertFalse(decision.flags.get("career"))

    def test_knowledge_branch_direct_llm(self):
        admin = understand_to_admin(
            {
                "branch": "knowledge",
                "domain": "remedy",
                "archetype": "gemstone_remedy",
                "timing": False,
                "knowledge": True,
                "question_summary": "Leo lagna gemstone theory",
                "confidence": 0.9,
                "question_type": "remedy",
            },
            question="Leo lagna ke liye kaunsa ratna?",
        )
        decision = ensure_correct_engine_route(
            "Leo lagna ke liye kaunsa ratna?",
            admin,
            {k: False for k in _ALL},
            deadline_s=3,
        )
        self.assertTrue(decision.ok)
        self.assertEqual(decision.path, "direct_llm")
        self.assertIsNone(decision.engine_key)

    def test_enforce_forces_engine_when_all_flags_off(self):
        admin = {
            "dna_routing_applied": True,
            "domain": "finance",
            "question_dna": {
                "source": "llm",
                "questions": [{
                    "domain": "finance",
                    "bucket": "wealth_potential",
                    "confidence": 0.9,
                    "bucket_match_confidence": "high",
                }],
            },
        }
        flags = {k: False for k in _ALL}
        new_flags, note = enforce_dna_routing_flags(
            flags, admin, None, question="mera paisa kab badhega"
        )
        self.assertEqual(note, "dna_force_engine:finance")
        self.assertTrue(new_flags["finance"])

    def test_verify_mismatch(self):
        ok, failed = verify_engine_match(
            expected_engine="health",
            requires_engine=True,
            flags={"health": False, "career": True, "mr": False},
        )
        self.assertFalse(ok)
        self.assertTrue(any("career" in f or "health" in f for f in failed))

    def test_coerce_freeform_bucket(self):
        admin = {
            "domain": "love",
            "routed_domain": "love",
            "question_dna": {
                "source": "understand_phase2",
                "questions": [{
                    "domain": "love",
                    "bucket": "partner_loyalty",
                    "confidence": 0.8,
                    "intent": "is partner loyal",
                    "subject": "partner",
                }],
            },
            "dna_routing_applied": True,
        }
        coerce_admin_dna_for_routing(admin, question="partner loyal hai?")
        item = admin["question_dna"]["questions"][0]
        self.assertEqual(item["bucket"], "trust_loyalty")


if __name__ == "__main__":
    unittest.main()

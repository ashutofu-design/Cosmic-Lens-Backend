"""Tests for MR engine v2 architecture + Commitment reference implementation."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_mr.v2.memory import clear_memory_store, load_memory, save_memory
from ask_mr.v2.orchestrator import orchestrate
from ask_mr.v2.registry import modules_for_engine, plan_orchestration
from ask_mr.v2.engines.commitment import run_commitment_v2
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.engines.commitment import run_commitment

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Jupiter", "sign": "Libra", "house": 11},
        {"name": "Saturn", "sign": "Aries", "house": 5},
    ],
    "dasha": {"mahadasha": "Venus", "antardasha": "Jupiter"},
}


class MrV2ArchitectureTests(unittest.TestCase):
    def setUp(self):
        clear_memory_store()
        os.environ["ASK_MR_ENGINE_V2"] = "1"

    def test_commitment_module_matrix(self):
        static = modules_for_engine("commitment", "Kya partner serious hai?")
        self.assertIn("d1", static)
        self.assertIn("d9", static)
        self.assertIn("dasha", static)
        self.assertNotIn("jaimini", static)

        timing = modules_for_engine("commitment", "Kab partner commit karega?")
        self.assertIn("jaimini", timing)

    def test_compatibility_kp_optional(self):
        mods = modules_for_engine("compatibility", "Hum compatible hain?")
        self.assertIn("kp", mods)

    def test_family_timing_optional(self):
        static = modules_for_engine("family_approval", "Ghar wale maanenge?")
        self.assertNotIn("dasha", static)
        timing = modules_for_engine("family_approval", "Ghar wale kab maanenge?")
        self.assertIn("dasha", timing)
        self.assertIn("transit", timing)

    def test_commitment_v2_json_shape(self):
        out = run_commitment_v2(
            SAMPLE_KUNDLI,
            "Kya mera partner commitment ke liye ready hai?",
            session_id="test-session-1",
        )
        d = out.to_json_ready()
        self.assertEqual(d["engine_id"], "commitment")
        self.assertEqual(d["engine_version"], "v2")
        self.assertIn("scorecard", d)
        self.assertIn("trust", d["scorecard"])
        self.assertIn("commitment", d["scorecard"])
        self.assertIn("rules_fired", d)
        self.assertIn("explanation", d)
        self.assertIn("why", d["explanation"])
        self.assertIn("verdict", d)

    def test_engine_memory_refire(self):
        q = "Kya partner serious relationship chahta hai?"
        run_commitment_v2(SAMPLE_KUNDLI, q, session_id="mem-1")
        out2 = run_commitment_v2(SAMPLE_KUNDLI, q, session_id="mem-1")
        mem = load_memory("mem-1", "commitment")
        self.assertTrue(mem.previously_fired_rules)
        self.assertTrue(out2.memory.previously_fired_rules)

    def test_orchestrator_trust_plus_affair(self):
        plan = plan_orchestration(
            "Should I trust my partner? He is talking to another girl.",
            dna_bucket="trust_loyalty",
        )
        self.assertEqual(plan.primary, "loyalty_trust")
        self.assertIn("secret_relationship", plan.secondary)

        result = orchestrate(
            SAMPLE_KUNDLI,
            "Should I trust my partner? He is talking to another girl.",
            primary_archetype="loyalty_trust",
            session_id="orch-1",
        )
        self.assertEqual(result["orchestrator"]["primary"], "loyalty_trust")
        self.assertIn("secret_relationship", result["orchestrator"]["secondary"])

    def test_commitment_v1_delegates_to_v2(self):
        res = run_commitment(
            SAMPLE_KUNDLI,
            "Kya mera partner serious relationship chahta hai?",
        )
        self.assertEqual(res.archetype, "commitment")
        self.assertEqual(res.checks.get("slice_type"), "mr_engine_v2")
        self.assertIn("scorecard", res.checks)
        self.assertIn("explanation", res.checks)

    def test_adapter_preserves_evidence(self):
        out = run_commitment_v2(SAMPLE_KUNDLI, "Partner long-term intent?")
        res = v2_to_engine_result(out)
        self.assertTrue(res.verdict)
        self.assertTrue(res.evidence_positive or res.evidence_negative or res.evidence)


if __name__ == "__main__":
    unittest.main()

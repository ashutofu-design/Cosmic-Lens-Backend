"""Tests for MR engine v2 architecture + Commitment reference implementation."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_mr.v2.manifest import get_engine_manifest
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
        self.assertEqual(d["engine_version"], "2.0.0")
        self.assertEqual(d["rules_version"], "COM-1.1.0")
        self.assertEqual(d["schema_version"], "2.0")
        self.assertIn("scorecard", d)
        self.assertIn("trust", d["scorecard"])
        self.assertIn("commitment", d["scorecard"])
        self.assertIn("rules_fired", d)
        self.assertIn("explanation", d)
        self.assertIn("why", d["explanation"])
        self.assertIn("verdict", d)

    def test_commitment_manifest_and_health(self):
        manifest = get_engine_manifest("commitment")
        self.assertIsNotNone(manifest)
        self.assertIn("static", manifest.supports)
        self.assertIn("timing", manifest.supports)
        self.assertIn("d1", manifest.needs)
        self.assertIn("d9", manifest.needs)
        self.assertIn("breakup / divorce risk", manifest.health.unsupported_questions)
        self.assertEqual(manifest.health.fallback_engine, "relationship_future")

    def test_rule_registry_centralizes_commitment_rules(self):
        from ask_mr.v2.rules.rule_registry import RULE_REGISTRY, get_registered_rules

        self.assertIn("commitment", RULE_REGISTRY)
        rules = get_registered_rules("commitment")
        self.assertIsNotNone(rules)
        self.assertTrue(all(r.rule_id.startswith("COM-") for r in rules))

    def test_module_registry_is_single_source(self):
        from ask_mr.v2.module_registry import ENGINE_MODULE_MATRIX, modules_for_engine

        self.assertIn("commitment", ENGINE_MODULE_MATRIX)
        mods = modules_for_engine("commitment", "Kya partner serious hai?")
        self.assertEqual(mods, ["d1", "d9", "dasha", "transit", "kp", "ashtakavarga"])
        comm = modules_for_engine("communication", "Hum baat karte hain?")
        self.assertEqual(comm, ["d1", "d9", "ashtakavarga"])
        self.assertNotIn("kp", comm)

    def test_loyalty_rules_are_factor_based_v11(self):
        from ask_mr.v2.rules.trust_rules import RULES_VERSION, trust_rules

        self.assertEqual(RULES_VERSION, "1.1.0")
        rules = trust_rules()
        self.assertGreaterEqual(len(rules), 38)
        ids = {r.rule_id for r in rules}
        for rid in (
            "TRUST-001", "TRUST-004", "TRUST-007", "TRUST-009", "TRUST-013",
            "TRUST-020", "TRUST-026", "TRUST-031", "TRUST-033", "TRUST-043",
        ):
            self.assertIn(rid, ids)

    def test_loyalty_v2_output_versions_and_intent(self):
        from ask_mr.v2 import run_engine_v2

        out = run_engine_v2("loyalty_trust", SAMPLE_KUNDLI, "Kya mera partner loyal hai?")
        self.assertIsNotNone(out)
        self.assertEqual(out.engine_id, "loyalty_trust")
        self.assertEqual(out.rules_version, "TRUST-1.1.0")
        self.assertEqual(out.question_intent, "general_trust")
        self.assertIn("trust_level", out.checks)
        ids = [r["rule_id"] for r in out.rules_fired]
        if ids:
            self.assertTrue(all(rid.startswith("TRUST-") for rid in ids))

    def test_loyalty_v1_delegates_to_v2(self):
        from ask_mr.engines.loyalty_trust import run_loyalty_trust

        res = run_loyalty_trust(SAMPLE_KUNDLI, "Kya partner mujh par loyal hai?")
        self.assertEqual(res.archetype, "loyalty_trust")
        self.assertEqual(res.checks.get("slice_type"), "mr_engine_v2")
        self.assertEqual(res.checks.get("rules_version"), "TRUST-1.1.0")
        self.assertIn("scorecard", res.checks)

    def test_commitment_rules_are_factor_based_v11(self):
        from ask_mr.v2.rules.commitment_rules import RULES_VERSION, commitment_rules

        self.assertEqual(RULES_VERSION, "1.1.0")
        rules = commitment_rules()
        self.assertGreaterEqual(len(rules), 25)
        ids = {r.rule_id for r in rules}
        for rid in (
            "COM-001", "COM-004", "COM-006", "COM-009", "COM-011",
            "COM-014", "COM-017", "COM-020", "COM-022", "COM-024", "COM-026",
        ):
            self.assertIn(rid, ids)

        out = run_commitment_v2(SAMPLE_KUNDLI, "Kya partner serious relationship chahta hai?")
        ids = [r["rule_id"] for r in out.rules_fired]
        self.assertTrue(ids)
        self.assertTrue(all(rule_id.startswith("COM-") for rule_id in ids))
        self.assertTrue(all(rule_id[4:].isdigit() for rule_id in ids))

    def test_engine_spec_versions_on_output(self):
        out = run_commitment_v2(SAMPLE_KUNDLI, "Partner serious hai?")
        self.assertEqual(out.engine_version, "2.0.0")
        self.assertEqual(out.rules_version, "COM-1.1.0")
        self.assertEqual(out.schema_version, "2.0")
        self.assertEqual(out.checks.get("rules_version"), "COM-1.1.0")

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

    def test_all_twenty_engines_share_reference_template(self):
        from ask_mr.v2 import run_engine_v2
        from ask_mr.v2.registry import FROZEN_ENGINE_IDS
        from ask_mr.v2.specs import get_engine_spec

        self.assertEqual(len(FROZEN_ENGINE_IDS), 20)
        for eid in sorted(FROZEN_ENGINE_IDS):
            with self.subTest(engine=eid):
                spec = get_engine_spec(eid)
                self.assertIsNotNone(spec, f"missing EngineSpec for {eid}")
                out = run_engine_v2(eid, SAMPLE_KUNDLI, f"Test question for {eid}?")
                self.assertIsNotNone(out)
                d = out.to_json_ready()
                self.assertEqual(d["engine_id"], eid)
                self.assertEqual(d["engine_version"], "2.0.0")
                self.assertTrue(d.get("rules_version"))
                self.assertEqual(d["schema_version"], "2.0")
                self.assertIn("scorecard", d)
                self.assertIn("explanation", d)
                self.assertIn("rules_fired", d)
                ids = [r["rule_id"] for r in d["rules_fired"]]
                if ids:
                    prefix = spec.rule_prefix
                    self.assertTrue(all(rid.startswith(f"{prefix}-") for rid in ids), ids)

    def test_communication_v2_via_router(self):
        from ask_mr import run_mr_static_engine

        res = run_mr_static_engine(
            SAMPLE_KUNDLI,
            "Kya partner ke saath communication theek hai?",
            archetype="communication",
        )
        self.assertEqual(res.archetype, "communication")
        self.assertEqual(res.checks.get("slice_type"), "mr_engine_v2")
        self.assertIn("scorecard", res.checks)

    def test_phase1_v2_engines_delegate_from_v1_entrypoints(self):
        from ask_mr import run_mr_static_engine

        cases = [
            ("Kya mera partner loyal hai?", "loyalty_trust"),
            ("Kya hum dono compatible hain?", "compatibility"),
            ("Kya breakup ho sakta hai?", "breakup_risk"),
            ("Patchup possible hai?", "patchup"),
        ]
        for q, arch in cases:
            with self.subTest(q=q):
                res = run_mr_static_engine(SAMPLE_KUNDLI, q)
                self.assertEqual(res.archetype, arch)
                self.assertEqual(res.checks.get("slice_type"), "mr_engine_v2")
                self.assertIn("scorecard", res.checks)
                self.assertIn("explanation", res.checks)
                self.assertTrue(res.evidence)


if __name__ == "__main__":
    unittest.main()

"""Tests for Execution Gatekeeper — DNA/engine/narrator pipeline hard stops."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_execution_gatekeeper import (
    check_engine_output_gate,
    check_final_answer_gate,
    check_routing_gate,
    dna_expectation,
    enforce_dna_routing_flags,
    gatekeeper_enabled,
    run_post_engine_gate,
)


class ExecutionGatekeeperTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_EXECUTION_GATEKEEPER"] = "1"

    def test_enabled_by_default(self):
        os.environ.pop("ASK_EXECUTION_GATEKEEPER", None)
        self.assertTrue(gatekeeper_enabled())

    def test_dna_force_health_over_career(self):
        admin = {
            "dna_routing_applied": True,
            "domain": "health",
            "routed_domain": "health",
            "dna_engine_archetype": "heart_blood_pressure",
            "health_archetype": "heart_blood_pressure",
            "question_dna": {
                "source": "llm",
                "questions": [{
                    "domain": "health",
                    "bucket": "heart_blood_pressure",
                    "confidence": 0.9,
                    "bucket_match_confidence": "high",
                }],
            },
        }
        flags = {k: False for k in (
            "education", "children", "property", "vehicle", "travel",
            "litigation", "gap", "network", "luck", "career", "finance", "health", "mr",
        )}
        flags["career"] = True
        new_flags, note = enforce_dna_routing_flags(flags, admin, None)
        self.assertEqual(note, "dna_force_engine:health")
        self.assertTrue(new_flags["health"])
        self.assertFalse(new_flags["career"])

    def test_rule6_health_dna_career_engine_blocked(self):
        admin = {
            "dna_routing_applied": True,
            "domain": "health",
            "dna_engine_archetype": "heart_blood_pressure",
            "question_dna": {
                "source": "llm",
                "questions": [{
                    "domain": "health",
                    "bucket": "heart_blood_pressure",
                    "confidence": 0.88,
                }],
            },
        }
        meta = {
            "slice": "career_engine_v1",
            "archetype": "general_career",
            "verdict": "Mixed career path",
            "evidence": [],
            "checks": {"rules_fired": []},
        }
        res = check_engine_output_gate(admin, slice_meta=meta)
        self.assertFalse(res.ok)
        self.assertEqual(res.rule, "rule_6_health_question_career_engine")

    def test_rule2_zero_evidence_blocked(self):
        meta = {
            "slice": "health_engine_v1",
            "archetype": "heart_blood_pressure",
            "evidence": [],
            "checks": {"rules_fired": []},
        }
        res = check_engine_output_gate(None, slice_meta=meta)
        self.assertFalse(res.ok)
        self.assertEqual(res.reason, "insufficient_evidence")

    def test_health_engine_with_evidence_passes(self):
        meta = {
            "slice": "health_engine_v1",
            "archetype": "heart_blood_pressure",
            "verdict": "BP stress pattern moderate",
            "evidence": ["4th house signal", "Moon stress"],
            "checks": {
                "narrator_input": {
                    "direct_answer": "BP stress pattern moderate",
                    "positive_indicators": ["4th house support"],
                    "risk_indicators": ["Moon stress"],
                    "final_verdict": "BP stress pattern moderate",
                },
            },
        }
        res = run_post_engine_gate(None, slice_meta=meta, chart_text="")
        self.assertTrue(res.ok)

    def test_routing_mismatch_detected(self):
        admin = {
            "dna_routing_applied": True,
            "domain": "health",
            "dna_engine_archetype": "heart_blood_pressure",
            "question_dna": {
                "source": "llm",
                "questions": [{
                    "domain": "health",
                    "bucket": "heart_blood_pressure",
                    "confidence": 0.9,
                }],
            },
        }

        class _Route:
            engine_key = "career"
            archetype = "general_career"

        res = check_routing_gate(admin, engine_route=_Route(), flags={"career": True})
        self.assertFalse(res.ok)
        self.assertEqual(res.retry_engine_key, "health")

    def test_final_verdict_mismatch_blocked(self):
        meta = {
            "slice": "health_engine_v1",
            "archetype": "heart_blood_pressure",
            "verdict": "Heart/BP mixed pattern — stress discipline help karega",
        }
        nj = {
            "direct_answer": "Heart/BP mixed pattern — stress discipline help karega",
            "final_verdict": "Heart/BP mixed pattern — stress discipline help karega",
            "positive_indicators": ["Sun strong"],
        }
        bad_answer = "Aapki career me promotion strong dikhti hai office me growth milegi."
        res = check_final_answer_gate(bad_answer, slice_meta=meta, narrator_json=nj)
        self.assertFalse(res.ok)

    def test_dna_expectation_reads_health_bucket(self):
        admin = {
            "question_dna": {
                "source": "llm",
                "questions": [{
                    "domain": "health",
                    "bucket": "heart_blood_pressure",
                    "confidence": 0.85,
                    "bucket_match_confidence": "high",
                }],
            },
            "dna_routing_applied": True,
        }
        exp = dna_expectation(admin)
        self.assertEqual(exp.archetype, "heart_blood_pressure")
        self.assertEqual(exp.engine_key, "health")


if __name__ == "__main__":
    unittest.main()

"""Tests for Execution Gatekeeper — DNA/engine/narrator pipeline hard stops."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_execution_gatekeeper import (
    GatekeeperResult,
    allow_llm_fallback_on_gate_fail,
    check_engine_output_gate,
    check_final_answer_gate,
    check_routing_gate,
    dna_expectation,
    enforce_dna_routing_flags,
    gatekeeper_enabled,
    run_post_engine_gate,
)

_ALL_FLAGS = (
    "education", "children", "property", "vehicle", "travel",
    "litigation", "gap", "network", "luck", "career", "finance", "health", "mr",
)


class ExecutionGatekeeperTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_EXECUTION_GATEKEEPER"] = "1"
        os.environ.pop("ASK_EXECUTION_GATEKEEPER_HEALTH", None)

    def test_enabled_by_default(self):
        os.environ.pop("ASK_EXECUTION_GATEKEEPER", None)
        self.assertTrue(gatekeeper_enabled())

    def test_health_slice_exempt_from_gatekeeper(self):
        meta = {
            "slice": "health_engine_v1",
            "archetype": "general_health",
            "evidence": [],
            "checks": {"rules_fired": []},
        }
        res = check_engine_output_gate(None, slice_meta=meta)
        self.assertTrue(res.ok)
        self.assertEqual(res.rule, "health_no_gatekeeper")

        post = run_post_engine_gate(None, slice_meta=meta, chart_text="")
        self.assertTrue(post.ok)
        self.assertEqual(post.rule, "health_no_gatekeeper")

        final = check_final_answer_gate(
            "career promotion strong dikhti hai",
            slice_meta=meta,
        )
        self.assertTrue(final.ok)
        self.assertEqual(final.rule, "health_no_gatekeeper")

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
        flags = {k: False for k in _ALL_FLAGS}
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
        # Domain clash may fire rule_1 first; both mean health DNA ≠ career engine.
        self.assertIn(
            res.rule,
            ("rule_6_health_question_career_engine", "rule_1_dna_executed_mismatch"),
        )

    def test_rule2_zero_evidence_blocked_on_career(self):
        meta = {
            "slice": "career_engine_v1",
            "archetype": "general_career",
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
        self.assertEqual(res.rule, "health_no_gatekeeper")

    def test_verified_health_context_payload_exempt(self):
        from ask_health import run_health_static_engine
        from ask_health.presenter import to_health_llm_payload

        kundli = {
            "ascendant": "Leo",
            "planets": [
                {"name": "Sun", "sign": "Leo", "house": 1, "longitude": 120.0},
                {"name": "Moon", "sign": "Scorpio", "house": 4, "longitude": 220.0},
                {"name": "Mars", "sign": "Aries", "house": 9, "longitude": 10.0},
                {"name": "Mercury", "sign": "Virgo", "house": 2, "longitude": 160.0},
                {"name": "Jupiter", "sign": "Sagittarius", "house": 5, "longitude": 250.0},
                {"name": "Venus", "sign": "Libra", "house": 3, "longitude": 190.0},
                {"name": "Saturn", "sign": "Capricorn", "house": 6, "longitude": 290.0},
                {"name": "Rahu", "sign": "Gemini", "house": 11, "longitude": 80.0},
                {"name": "Ketu", "sign": "Sagittarius", "house": 5, "longitude": 260.0},
            ],
        }
        question = "meri sehat kaisi hai"
        result = run_health_static_engine(
            kundli, question, archetype="overall_vitality"
        )
        chart_text = to_health_llm_payload(result, question=question)
        meta = {
            "slice": "health_engine_v1",
            "archetype": result.archetype,
            "verdict": result.verdict,
            "evidence": list(result.evidence or []),
            "checks": dict(result.checks or {}),
            "narrator_mode": "adaptive_d1_health_context",
        }
        res = run_post_engine_gate(
            None,
            slice_meta=meta,
            chart_text=chart_text,
            question=question,
        )
        self.assertTrue(res.ok, res.to_dict())
        self.assertEqual(res.rule, "health_no_gatekeeper")

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

    def test_final_verdict_mismatch_not_blocked_for_health_slice(self):
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
        bad_answer = (
            "Aapki career me promotion strong dikhti hai office me growth milegi."
        )
        res = check_final_answer_gate(bad_answer, slice_meta=meta, narrator_json=nj)
        self.assertTrue(res.ok)
        self.assertEqual(res.rule, "health_no_gatekeeper")

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

    def test_lord_placement_effect_skips_routing_block(self):
        q = (
            "pehele samjhao 6th lord 3rd house me he woh sun he and "
            "deblited he to kya hota he"
        )
        admin = {
            "question_dna": {
                "source": "llm",
                "questions": [{
                    "domain": "health",
                    "bucket": "general_health",
                    "confidence": 0.9,
                    "bucket_match_confidence": "high",
                }],
            },
            "dna_routing_applied": True,
        }

        class _Route:
            engine_key = "career"
            archetype = "general_career"
            domain = "career"
            reason = ""

        res = check_routing_gate(admin, engine_route=_Route(), question=q)
        self.assertTrue(res.ok)
        self.assertIn(res.rule, ("chart_interpretive_llm", "direct_llm_chart_q"))

        flags = {k: False for k in _ALL_FLAGS}
        flags["career"] = True
        out, note = enforce_dna_routing_flags(flags, admin, _Route(), question=q)
        self.assertIsNone(note)
        self.assertTrue(out["career"])  # not forced to health

    def test_routing_error_allows_llm_fallback(self):
        bad = GatekeeperResult(
            ok=False,
            stage="routing",
            reason="routing_error",
            rule="rule_1_routing_mismatch",
        )
        self.assertTrue(
            allow_llm_fallback_on_gate_fail(
                bad,
                "6th lord 3rd house me sun debilitated kya hota hai",
            )
        )
        hallu = GatekeeperResult(
            ok=False,
            stage="final",
            reason="hallucination_detected",
            rule="rule_5",
        )
        self.assertFalse(allow_llm_fallback_on_gate_fail(hallu, "health kaisi"))


if __name__ == "__main__":
    unittest.main()

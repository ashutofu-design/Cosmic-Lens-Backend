"""Tests for admin observability debugger bundle."""
import unittest

from ask_observability_debug import attach_observability_to_context, build_observability_debug


class TestAskObservabilityDebug(unittest.TestCase):
    def test_commitment_routing_warning(self):
        ctx = {
            "slice_meta": {"archetype": "loyalty_trust", "verdict": "Mixed"},
            "llm_intent": {"domain": "love", "mr_archetype": "loyalty_trust"},
            "checks": {
                "scorecard": {"trust": 70, "commitment": 55, "primary": 60},
                "rules_fired": [{"rule_id": "COM-001", "polarity": "positive", "weight": 10, "note": "Strong Venus"}],
                "primary_score": 84,
                "level": "cautious",
            },
            "engine_facts": {
                "evidence_positive": ["Strong 7th Lord +15", "Venus strong +10"],
                "evidence_negative": ["Saturn delay -8"],
            },
            "question": "kya mera partner mujhse genuinely commitment karega ya sirf timepass kar raha hai",
        }
        obs = build_observability_debug(
            ctx,
            question_text=ctx["question"],
            answer_text="Communication strong hai.",
        )
        self.assertTrue(obs["routing_warning"])
        self.assertIn("user_question", obs)
        self.assertIn("routing_decision", obs)
        self.assertIn("astrology_checks", obs)
        self.assertIn("engine_health", obs)
        self.assertIn("rule_decisions", obs)
        self.assertIn("unused_engine_evidence", obs["hallucination_summary"])
        dna_labels = [s["label"] for s in obs["question_dna_pipeline"]]
        self.assertIn("Normalized", dna_labels)
        self.assertIn("Intent", dna_labels)
        self.assertIn("Engine Archetype", dna_labels)
        self.assertIn("Bucket Match", dna_labels)
        self.assertIn("modules_skipped", obs["engine_execution"])
        self.assertIn("neutral", obs["planet_evidence"])
        self.assertIn("hallucination_summary", obs)
        self.assertEqual(obs["engine_execution"]["final_score"], 84)
        self.assertTrue(obs["has_v2_rules"])
        self.assertIn("trust", {k.lower() for k in obs["scorecard"]})

    def test_infidelity_dna_pipeline_matches_mobile_format(self):
        q = "Kya mera partner kisi aur me interested hai?"
        dna_item = {
            "normalized_question": q,
            "domain": "love",
            "bucket": "third_person_infidelity",
            "intent": "partner interest in someone else",
            "subject": "partner",
            "target": "self_relationship",
            "question_type": "current_state",
            "timing": False,
            "tense": "present",
            "emotion": "fear",
            "risk": "high",
            "is_followup": False,
            "engine_archetype": "secret_relationship",
            "required_modules": ["D1", "D9", "DASHA", "TRANSIT"],
            "confidence": 0.97,
            "bucket_match_confidence": "high",
            "bucket_match_score": 0.97,
        }
        ctx = {
            "question": q,
            "question_dna": {"questions": [dna_item], "source": "llm", "latency_ms": 120},
            "llm_intent": {"question_dna": {"questions": [dna_item]}},
            "slice_meta": {"archetype": "secret_relationship"},
        }
        obs = build_observability_debug(ctx, question_text=q, answer_text="Test answer.")
        pipeline = {s["label"]: s["value"] for s in obs["question_dna_pipeline"]}
        self.assertEqual(pipeline["Normalized"], q)
        self.assertIn("Third Person / Infidelity", pipeline["Bucket"])
        self.assertIn("third_person_infidelity", pipeline["Bucket"])
        self.assertEqual(pipeline["Intent"], "partner interest in someone else")
        self.assertIn("Partner (partner)", pipeline["Subject"])
        self.assertEqual(pipeline["Engine Archetype"], "secret relationship")
        self.assertEqual(pipeline["Modules"], "D1, D9, DASHA, TRANSIT")
        self.assertEqual(pipeline["Confidence"], "97%")
        self.assertEqual(pipeline["Bucket Match"], "HIGH (97%)")
        self.assertEqual(pipeline["Timing Required"], "no")
        self.assertEqual(pipeline["Time Context"], "present")

    def test_attach_observability_preserves_question_dna_on_ctx(self):
        q = "Kya mera partner kisi aur me interested hai?"
        dna_item = {
            "normalized_question": q,
            "domain": "love",
            "bucket": "third_person_infidelity",
            "engine_archetype": "secret_relationship",
            "confidence": 0.97,
        }
        ctx = {
            "question": q,
            "question_dna": {"questions": [dna_item], "source": "llm"},
            "slice_meta": {"archetype": "secret_relationship"},
        }
        out = attach_observability_to_context(ctx, question_text=q, answer_text="test")
        self.assertIsInstance(out.get("question_dna"), dict)
        self.assertEqual(
            out["question_dna"]["questions"][0]["bucket"],
            "third_person_infidelity",
        )
        pipeline = {s["label"]: s["value"] for s in out["observability"]["question_dna_pipeline"]}
        self.assertIn("third_person_infidelity", pipeline["Bucket"])


if __name__ == "__main__":
    unittest.main()

"""Tests for admin observability debugger bundle."""
import unittest

from ask_observability_debug import build_observability_debug


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
        self.assertEqual(len(obs["question_dna_pipeline"]), 15)
        self.assertEqual(obs["engine_execution"]["final_score"], 84)
        self.assertTrue(obs["has_v2_rules"])
        self.assertIn("trust", {k.lower() for k in obs["scorecard"]})


if __name__ == "__main__":
    unittest.main()

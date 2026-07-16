"""Speed + routing: spiritual/gap engines must not be bypassed to slow LLM."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_routing_policy import (
    matches_dedicated_static_engine,
    should_bypass_static_engines_for_direct_llm,
)
from ask_gap_dispatch import detect_gap_static_key
from ask_question_normalize import prepare_ask_question
from engine_collision_registry import DOMAIN_PRIMARY_ENGINE


class AskSpeedSpiritualTests(unittest.TestCase):
    def test_normalize_me_dharmik(self):
        q = prepare_ask_question("kya me dharmik hun")
        self.assertIn("main", q)
        self.assertIn("dharmik", q)

    def test_spiritual_gap_detected(self):
        q = prepare_ask_question("kya me dharmik hun")
        self.assertEqual(detect_gap_static_key(q), "spiritual")

    def test_dedicated_engine_match_blocks_bypass(self):
        q = prepare_ask_question("kya me dharmik hun")
        self.assertTrue(matches_dedicated_static_engine(q, {"domain": "spiritual", "answer_mode": "llm_chart"}))
        bypass, reason = should_bypass_static_engines_for_direct_llm(
            q, {"domain": "spiritual", "answer_mode": "llm_chart"}
        )
        self.assertFalse(bypass, reason)

    def test_spiritual_maps_to_gap_primary(self):
        self.assertEqual(DOMAIN_PRIMARY_ENGINE.get("spiritual"), "gap")

    def test_dna_fast_path_skips_intent_llm(self):
        from ask_route_from_understanding import classify_and_route_ask

        dna = {
            "source": "llm",
            "questions": [{
                "normalized_question": "Kya main dharmik hun?",
                "domain": "spiritual",
                "bucket": "general_spiritual",
                "intent": "am I dharmic / spiritual by nature",
                "user_wants": "User wants to know if they are dharmic.",
                "subject": "self",
                "target": "self",
                "question_type": "personality",
                "timing": False,
                "tense": "present",
                "emotion": "curiosity",
                "risk": "low",
                "confidence": 0.95,
                "bucket_match_confidence": "high",
                "engine_archetype": "general_spiritual",
            }],
        }
        with patch("ask_intent_llm.classify_ask_intent") as mock_intent:
            out = classify_and_route_ask(
                "kya me dharmik hun",
                understanding={"question_dna": dna},
            )
            mock_intent.assert_not_called()
        self.assertEqual(out["intent_source"], "question_dna")
        self.assertEqual(out["llm_intent_admin"].get("routed_domain"), "spiritual")

    def test_dna_judge_off_for_spiritual_by_default(self):
        from ask_unified import domain_dna_judge_enabled

        old = os.environ.pop("ASK_UNIFIED_DNA_JUDGE", None)
        old2 = os.environ.pop("ASK_SPIRITUAL_DNA_JUDGE", None)
        try:
            self.assertFalse(domain_dna_judge_enabled("spiritual"))
        finally:
            if old is not None:
                os.environ["ASK_UNIFIED_DNA_JUDGE"] = old
            if old2 is not None:
                os.environ["ASK_SPIRITUAL_DNA_JUDGE"] = old2


if __name__ == "__main__":
    unittest.main()

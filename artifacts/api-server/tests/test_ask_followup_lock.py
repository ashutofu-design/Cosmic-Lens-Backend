"""Follow-up lock — same DNA engine across refine turns."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_followup_chips import derive_follow_up_chips, enrich_ask_result_followups
from ask_followup_lock import apply_followup_lock, extract_prior_thread
from ask_understand_phase2 import understand_to_admin


class FollowupLockTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_FOLLOWUP_LOCK"] = "1"

    def test_extract_prior_with_dna_meta(self):
        history = [
            {"role": "user", "text": "Partner loyal hai kya?"},
            {
                "role": "assistant",
                "text": "Loyalty mixed dikhti hai…",
                "domain": "love",
                "bucket": "trust_loyalty",
                "archetype": "loyalty_trust",
                "subject": "partner",
            },
        ]
        prior = extract_prior_thread(history)
        self.assertEqual(prior["prior_question"], "Partner loyal hai kya?")
        self.assertEqual(prior["domain"], "love")
        self.assertEqual(prior["bucket"], "trust_loyalty")

    def test_lock_keeps_love_on_exact_month_refine(self):
        history = [
            {"role": "user", "text": "Meri shaadi kab hogi?"},
            {
                "role": "assistant",
                "text": "Shaadi 2027 window…",
                "domain": "marriage",
                "bucket": "dating_courtship",
                "topic": "marriage",
            },
        ]
        admin = understand_to_admin(
            {
                "branch": "engine",
                "domain": "career",  # wrong — Phase-2 sometimes drifts
                "archetype": "job_promotion",
                "timing": True,
                "turn_type": "followup",
                "is_followup": True,
                "effective_question": "Exact month batao",
                "question_summary": "User wants exact month for prior ask",
                "confidence": 0.8,
                "question_type": "timing",
            },
            question="Exact month batao",
        )
        result = apply_followup_lock(
            "Exact month batao",
            history,
            phase2={
                "turn_type": "followup",
                "is_followup": True,
                "timing": True,
                "effective_question": "Exact month batao",
                "domain": "career",
            },
            admin=admin,
        )
        self.assertTrue(result["is_followup"])
        locked = result["admin"]
        self.assertEqual(locked.get("domain"), "marriage")
        self.assertIn("shaadi", (result["effective_question"] or "").lower())
        self.assertTrue(locked.get("routed_timing") or locked.get("is_timing"))

    def test_regex_followup_without_phase2(self):
        history = [
            {"role": "user", "text": "Mera BP high kyun rehta hai?"},
            {
                "role": "assistant",
                "text": "Heart/BP pattern…",
                "domain": "health",
                "bucket": "heart_blood_pressure",
            },
        ]
        result = apply_followup_lock(
            "kab improve hogi?",
            history,
            phase2=None,
            admin={},
        )
        self.assertTrue(result["is_followup"])
        self.assertEqual(result["admin"].get("domain"), "health")

    def test_bucket_chips_loyalty(self):
        chips = derive_follow_up_chips(
            domain="love",
            bucket="trust_loyalty",
            lang="hn",
        )
        self.assertEqual(len(chips), 3)
        self.assertTrue(any("vishwas" in c.lower() or "trust" in c.lower() or "loyalty" in c.lower() for c in chips))

    def test_enrich_fills_empty_follow_ups(self):
        out = {"text": "ok", "topic": "static", "follow_ups": []}
        admin = {
            "domain": "finance",
            "routed_domain": "finance",
            "bucket": "wealth_potential",
            "question_dna": {
                "questions": [{
                    "domain": "finance",
                    "bucket": "wealth_potential",
                    "timing": False,
                }],
            },
        }
        enrich_ask_result_followups(out, lang="hn", admin=admin)
        self.assertTrue(out["follow_ups"])
        self.assertEqual(out["domain"], "finance")
        self.assertEqual(out["bucket"], "wealth_potential")


if __name__ == "__main__":
    unittest.main()

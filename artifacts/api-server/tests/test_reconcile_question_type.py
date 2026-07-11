"""Tests — central STATIC vs TIMING reconcile gate."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestReconcileQuestionType(unittest.TestCase):
    def test_mr_yog_static_despite_llm_timing(self):
        from ask_intent_fidelity import reconcile_question_type

        q = "Kya meri life me serious relationship ka yog hai?"
        intent = {"domain": "love", "is_timing": True, "source": "llm"}
        rec = reconcile_question_type(q, intent, mutate=True)
        self.assertFalse(rec["is_timing"])
        self.assertEqual(rec["qtype"], "STATIC")
        self.assertFalse(intent.get("is_timing"))

    def test_true_love_milega_static(self):
        from ask_intent_fidelity import reconcile_question_type

        q = "Kya mujhe life me true love milega?"
        intent = {"domain": "love", "is_timing": True}
        rec = reconcile_question_type(q, intent)
        self.assertFalse(rec["is_timing"])

    def test_kab_stays_timing(self):
        from ask_intent_fidelity import reconcile_question_type

        q = "Mera promotion kab hoga?"
        intent = {"domain": "career", "is_timing": True}
        rec = reconcile_question_type(q, intent)
        self.assertTrue(rec["is_timing"])
        self.assertEqual(rec["qtype"], "TIMING")

    def test_vague_struggle_kab_still_timing(self):
        from ask_intent_fidelity import reconcile_question_type

        q = "Mera life me struggle kab jaayega"
        intent = {"domain": "general", "is_timing": True}
        rec = reconcile_question_type(q, intent)
        self.assertTrue(rec["is_timing"])


if __name__ == "__main__":
    unittest.main()

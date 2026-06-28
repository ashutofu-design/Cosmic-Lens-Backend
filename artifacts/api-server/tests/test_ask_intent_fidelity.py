"""Tests — LLM intent must match the user's exact question."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_intent_fidelity import (
    faithful_interpretation,
    repair_llm_intent,
    resolve_question_understood,
)


class AskIntentFidelityTests(unittest.TestCase):
    def test_faithful_interpretation_quotes_question(self):
        self.assertEqual(
            faithful_interpretation("Mere bare me kuch batao"),
            'User asked: "Mere bare me kuch batao"',
        )

    def test_repairs_inlaw_hallucination_on_vague_ask(self):
        raw = {
            "domain": "marriage",
            "is_timing": False,
            "is_decision": False,
            "wants_explain": False,
            "mr_archetype": "partner_nature",
            "interpretation": "User wants to know about the nature and behavior of their in-laws.",
            "confidence": 0.95,
            "source": "llm",
        }
        fixed = repair_llm_intent("Mere bare me kuch batao", raw)
        self.assertEqual(fixed["domain"], "general")
        self.assertIsNone(fixed["mr_archetype"])
        self.assertIn("Mere bare me kuch batao", fixed["interpretation"])
        self.assertNotIn("in-law", fixed["interpretation"].lower())

    def test_keeps_valid_marriage_question(self):
        raw = {
            "domain": "marriage",
            "is_timing": True,
            "mr_archetype": "general_mr",
            "interpretation": "User wants shaadi timing",
            "confidence": 0.9,
            "source": "llm",
        }
        fixed = repair_llm_intent("Meri shaadi kab hogi?", raw)
        self.assertEqual(fixed["domain"], "marriage")
        self.assertIn("shaadi kab hogi", fixed["interpretation"].lower())

    def test_repairs_interpretation_hallucination_only(self):
        raw = {
            "domain": "general",
            "mr_archetype": None,
            "interpretation": "User wants to know about in-laws.",
            "confidence": 0.8,
            "source": "llm",
        }
        fixed = repair_llm_intent("Career kaisi rahegi?", raw)
        self.assertIn("Career kaisi rahegi", fixed["interpretation"])
        self.assertNotIn("in-law", fixed["interpretation"].lower())

    def test_upgrades_finance_from_paisa_question(self):
        raw = {
            "domain": "general",
            "mr_archetype": None,
            "interpretation": "User asked something",
            "confidence": 0.9,
            "source": "llm",
        }
        fixed = repair_llm_intent("Mere paas paisa kitna hoga", raw)
        self.assertEqual(fixed["domain"], "finance")
        self.assertEqual(fixed.get("finance_archetype"), "wealth_potential")
        self.assertEqual(fixed.get("understanding_line"), "Yes")

    def test_finance_engine_required_still_understood_yes(self):
        li = {
            "domain": "finance",
            "finance_archetype": "wealth_potential",
            "confidence": 0.95,
            "source": "llm",
        }
        self.assertEqual(
            resolve_question_understood(
                "mere paas paisa kitna hoga",
                li,
                skip_reason="engine_required_no_direct_llm",
                intent_source="llm",
            ),
            "yes",
        )

    def test_gibberish_not_understood(self):
        self.assertEqual(
            resolve_question_understood("asdf qwer zx", {"domain": "general", "confidence": 0.2, "source": "llm"}),
            "no",
        )


if __name__ == "__main__":
    unittest.main()

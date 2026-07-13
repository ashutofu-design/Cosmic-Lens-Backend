"""Tests for Question DNA wiring into health validator + DNA Judge."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_health.answer_validator import (
    _enrich_dna_contract,
    _resolve_dna_contract,
    should_apply_health_overview_contract,
)
from ask_health.dna_judge import build_health_dna_judge_prompt


class HealthDnaContractTests(unittest.TestCase):
    def test_resolve_dna_contract_includes_full_question_dna(self):
        meta = {
            "question_dna": {
                "questions": [{
                    "normalized_question": "Jab travel karta hun tab health issue kyun?",
                    "intent": "why health issues during travel",
                    "user_wants": "User wants to know why health issues happen when travelling.",
                    "question_type": "cause",
                    "domain": "health",
                    "bucket": "general_health",
                    "answer_style": "short_paragraph",
                    "answer_approach": "Explain travel-health link from chart; why only.",
                }],
            },
        }
        contract = _resolve_dna_contract(meta)
        self.assertEqual(contract["question_type"], "cause")
        self.assertIn("travel", contract["user_wants"].lower())
        self.assertIn("travel", contract["normalized_question"].lower())

    def test_travel_health_not_overview_contract(self):
        q = "me jab bhi travel karta hun koi na koi health issue aa jaata he aisa kyun"
        self.assertFalse(should_apply_health_overview_contract(q))

    def test_general_overview_is_overview_contract(self):
        q = "mujhse mere health ke bare me jaana he"
        self.assertTrue(should_apply_health_overview_contract(q))

    def test_enrich_preserves_travel_health_dna(self):
        q = "me jab bhi travel karta hun koi na koi health issue aa jaata he aisa kyun"
        meta = {
            "user_wants": "User wants to know why health issues occur during travel.",
            "answer_approach": "Explain why travel triggers health issues using 6th-9th chart link.",
            "answer_style": "short_paragraph",
            "question_type": "cause",
            "intent": "travel health cause",
        }
        contract = _enrich_dna_contract(meta, q)
        self.assertIn("travel", contract["user_wants"].lower())
        self.assertIn("6th", contract["answer_approach"])
        self.assertNotIn("general overview", contract["answer_approach"].lower())

    def test_enrich_applies_overview_for_true_overview_ask(self):
        q = "mujhse mere health ke bare me batao"
        meta = {}
        contract = _enrich_dna_contract(meta, q)
        self.assertIn("general overview", contract.get("answer_approach", "").lower())
        self.assertEqual(contract.get("answer_style"), "short_paragraph")

    def test_dna_judge_prompt_prioritizes_user_wants(self):
        prompt = build_health_dna_judge_prompt(
            question="travel pe health issue kyun",
            answer="Paise kharcha zyada hota hai.",
            contract={
                "normalized_question": "Travel karte waqt health issue kyun aata hai?",
                "intent": "travel health cause",
                "user_wants": "User wants to know why health issues happen during travel.",
                "question_type": "cause",
                "answer_style": "short_paragraph",
                "answer_approach": "Explain travel-health why from chart.",
            },
        )
        self.assertIn("PRIMARY", prompt)
        self.assertIn("USER WANTS", prompt)
        self.assertIn("NORMALIZED QUESTION", prompt)
        self.assertIn("travel", prompt.lower())
        self.assertIn("FAIL PRIMARY if", prompt)


if __name__ == "__main__":
    unittest.main()

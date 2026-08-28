"""Relationship DNA judge + selected JSON — health-style mirrors."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_KUNDLI = {
    "ascendant": "Leo",
    "planets": [
        {"name": "Sun", "house": 1, "sign": "Leo"},
        {"name": "Moon", "house": 4, "sign": "Scorpio"},
        {"name": "Mars", "house": 7, "sign": "Aquarius"},
        {"name": "Mercury", "house": 2, "sign": "Virgo"},
        {"name": "Jupiter", "house": 9, "sign": "Aries"},
        {"name": "Venus", "house": 3, "sign": "Libra"},
        {"name": "Saturn", "house": 10, "sign": "Taurus"},
        {"name": "Rahu", "house": 5, "sign": "Sagittarius"},
        {"name": "Ketu", "house": 11, "sign": "Gemini"},
    ],
    "divisionalCharts": {
        "D9": {
            "ascendant": "Aries",
            "planets": [
                {"name": "Sun", "house": 5, "sign": "Leo"},
                {"name": "Moon", "house": 2, "sign": "Taurus"},
                {"name": "Mars", "house": 3, "sign": "Gemini"},
                {"name": "Mercury", "house": 4, "sign": "Cancer"},
                {"name": "Jupiter", "house": 1, "sign": "Aries"},
                {"name": "Venus", "house": 6, "sign": "Virgo"},
                {"name": "Saturn", "house": 7, "sign": "Libra"},
                {"name": "Rahu", "house": 8, "sign": "Scorpio"},
                {"name": "Ketu", "house": 2, "sign": "Taurus"},
            ],
        },
    },
}


class TestRelationshipSelectedAndDna(unittest.TestCase):
    def test_selected_blocks_priority_facts(self):
        from ask_mr import run_mr_static_engine
        from ask_mr.presenter import to_relationship_llm_payload
        from ask_mr.selected_blocks import (
            build_relationship_selected_blocks,
            classify_relationship_question_focus,
        )

        os.environ.pop("ASK_MR_LEGACY_ARCHETYPE_ENGINES", None)
        q = "Mera partner loyal hai kya?"
        self.assertEqual(
            classify_relationship_question_focus(q, routing_label="loyalty_trust"),
            "loyalty_trust",
        )
        res = run_mr_static_engine(_KUNDLI, q, archetype="loyalty_trust")
        pack = (res.checks or {}).get("relationship_engine_execution") or {}
        selected = build_relationship_selected_blocks(
            q, "", meta={"checks": res.checks}, execution=pack,
        )
        self.assertTrue(selected.get("applies"))
        self.assertEqual(selected.get("source"), "relationship_engine_execution")
        self.assertEqual(selected.get("focus"), "loyalty_trust")
        self.assertTrue(selected.get("has_d1"))
        self.assertTrue(selected.get("priority_facts_for_llm"))
        self.assertIn("QUESTION_PRIORITY_FACTS", selected["priority_facts_for_llm"])
        self.assertTrue(selected.get("expected_blocks"))

        payload = to_relationship_llm_payload(res, question=q)
        self.assertIn("RELATIONSHIP_ENGINE_EXECUTION_JSON", payload)
        self.assertIn("QUESTION_PRIORITY_FACTS", payload)
        self.assertIn("CITE THIS as proof", payload)

    def test_dna_judge_prompt_exports(self):
        from ask_mr.dna_judge import (
            build_relationship_dna_judge_prompt,
            relationship_dna_judge_enabled,
        )

        self.assertFalse(relationship_dna_judge_enabled())
        os.environ["ASK_MR_DNA_JUDGE"] = "1"
        self.assertTrue(relationship_dna_judge_enabled())
        os.environ.pop("ASK_MR_DNA_JUDGE", None)
        prompt = build_relationship_dna_judge_prompt(
            question="partner loyal hai kya",
            answer="Haan Venus 7th me strong hai.",
            contract={
                "user_wants": "Loyalty check",
                "intent": "loyalty_trust",
                "normalized_question": "Is my partner loyal?",
                "question_type": "risk",
            },
        )
        self.assertIn("USER WANTS", prompt)
        self.assertIn("Loyalty check", prompt)
        self.assertIn("missing_question_proof", prompt)

    def test_manglik_focus_from_question(self):
        from ask_mr.selected_blocks import classify_relationship_question_focus

        self.assertEqual(
            classify_relationship_question_focus("Kya main manglik hun?"),
            "manglik",
        )


if __name__ == "__main__":
    unittest.main()

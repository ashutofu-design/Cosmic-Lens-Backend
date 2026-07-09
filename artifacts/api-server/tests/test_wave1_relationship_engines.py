"""Tests for Wave-1 relationship engines (commitment, communication, future, decisions, toxicity, remedies)."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_mr import run_mr_static_engine
from ask_mr.classifier import classify_mr_archetype
from relationship_dna_taxonomy import map_love_bucket_to_mr

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Saturn", "sign": "Aries", "house": 5},
        {"name": "Mars", "sign": "Virgo", "house": 10},
        {"name": "Mercury", "sign": "Capricorn", "house": 2},
    ],
}


class Wave1RelationshipEnginesTests(unittest.TestCase):
    def test_dna_bucket_mr_mapping(self):
        self.assertEqual(map_love_bucket_to_mr("commitment"), "commitment")
        self.assertEqual(map_love_bucket_to_mr("communication"), "communication")
        self.assertEqual(map_love_bucket_to_mr("relationship_future"), "relationship_future")
        self.assertEqual(map_love_bucket_to_mr("relationship_decisions"), "relationship_decisions")
        self.assertEqual(map_love_bucket_to_mr("toxicity_red_flags"), "toxicity")
        self.assertEqual(map_love_bucket_to_mr("relationship_remedies"), "relationship_remedies")

    def test_classifier_routes_new_engines(self):
        cases = [
            ("Kya mera partner commitment ke liye ready hai?", "commitment"),
            ("Relationship me communication kaisi rahegi?", "communication"),
            ("Hamare relationship ka future kaisa rahega?", "relationship_future"),
            ("Kya mujhe is rishte me rehna chahiye ya chhod du?", "relationship_decisions"),
            ("Kya yeh relationship toxic hai?", "toxicity"),
            ("Love relationship ke liye koi upay batao", "relationship_remedies"),
        ]
        for q, expected in cases:
            with self.subTest(q=q[:48]):
                self.assertEqual(classify_mr_archetype(q), expected)

    def test_engines_run_with_evidence(self):
        cases = [
            ("Kya mera partner serious relationship chahta hai?", "commitment"),
            ("Partner mujhe samajh payega ya nahi?", "communication"),
            ("Relationship aage grow karega ya weak hoga?", "relationship_future"),
            ("Kya yeh rishta mere liye sahi hai?", "relationship_decisions"),
            ("Partner controlling aur manipulative hai kya?", "toxicity"),
            ("Rishta strong karne ka mantra upay?", "relationship_remedies"),
        ]
        for q, arch in cases:
            with self.subTest(q=q[:48]):
                res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
                self.assertEqual(res.archetype, arch)
                self.assertTrue(res.verdict)
                self.assertGreaterEqual(len(res.evidence or []), 1)


if __name__ == "__main__":
    unittest.main()

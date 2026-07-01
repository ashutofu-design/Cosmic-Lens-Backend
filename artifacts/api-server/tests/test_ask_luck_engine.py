"""Tests for ask_luck routing + engines."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_luck.classifier import classify_luck_archetype, is_luck_static_question
from ask_luck.engine import run_luck_static_engine

_SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Saturn", "sign": "Virgo", "house": 10},
        {"name": "Mars", "sign": "Cancer", "house": 8},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Mercury", "sign": "Aries", "house": 5},
        {"name": "Jupiter", "sign": "Pisces", "house": 4},
        {"name": "Rahu", "sign": "Aquarius", "house": 3},
        {"name": "Ketu", "sign": "Leo", "house": 9},
        {"name": "Sun", "sign": "Capricorn", "house": 2},
    ],
}


class TestAskLuckEngine(unittest.TestCase):
    def test_overall_luck_question(self):
        q = "mera luck kaise he"
        self.assertTrue(is_luck_static_question(q))
        self.assertEqual(classify_luck_archetype(q), "overall_luck")

    def test_timing_excluded(self):
        self.assertFalse(is_luck_static_question("mera luck kab milega"))

    def test_career_luck_routes(self):
        q = "career me mera luck kaisa hai"
        self.assertEqual(classify_luck_archetype(q), "career_luck")

    def test_engine_returns_evidence(self):
        res = run_luck_static_engine(_SAMPLE_KUNDLI, "mera luck kaise he")
        self.assertEqual(res.archetype, "overall_luck")
        self.assertTrue(res.verdict)
        self.assertGreaterEqual(len(res.evidence), 4)
        payload = res.to_narrator_payload()
        self.assertIn("VERDICT:", payload)
        self.assertIn("9th", " ".join(res.evidence).lower())


if __name__ == "__main__":
    unittest.main()

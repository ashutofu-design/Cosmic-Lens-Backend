"""Tests for ask_network static routing + engines."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_network.classifier import classify_network_archetype, is_network_static_question
from ask_network.engine import run_network_static_engine

_SAMPLE_KUNDLI = {
    "ascendant": "Libra",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 9},
        {"name": "Sun", "sign": "Libra", "house": 1},
        {"name": "Mars", "sign": "Leo", "house": 11},
        {"name": "Mercury", "sign": "Virgo", "house": 12},
        {"name": "Venus", "sign": "Scorpio", "house": 2},
        {"name": "Jupiter", "sign": "Gemini", "house": 9},
        {"name": "Saturn", "sign": "Aquarius", "house": 5},
        {"name": "Rahu", "sign": "Aries", "house": 7},
        {"name": "Ketu", "sign": "Libra", "house": 1},
    ],
}


class TestAskNetworkEngine(unittest.TestCase):
    def test_social_circle_quality_question(self):
        q = "Mera social circle acha he ya bura"
        self.assertTrue(is_network_static_question(q))
        self.assertEqual(classify_network_archetype(q), "social_circle_quality")

    def test_timing_excluded(self):
        self.assertFalse(is_network_static_question("dost kab milenge"))

    def test_engine_uses_11h_and_mars(self):
        res = run_network_static_engine(_SAMPLE_KUNDLI, "Mera social circle acha he ya bura")
        self.assertEqual(res.archetype, "social_circle_quality")
        blob = " ".join(res.evidence).lower()
        self.assertIn("11", blob)
        self.assertIn("mars", blob)
        self.assertIn("mercury", blob)
        payload = res.to_narrator_payload()
        self.assertIn("VERDICT:", payload)
        self.assertIn("11H", " ".join(res.evidence))


if __name__ == "__main__":
    unittest.main()
    
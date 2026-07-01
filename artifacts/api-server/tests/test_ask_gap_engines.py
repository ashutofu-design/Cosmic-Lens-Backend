"""Tests for Ask gap static engines + dispatch."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_gap_dispatch import detect_gap_static_key, run_gap_static_engine

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

_GAP_CASES = [
    ("Mera bhai supportive hai kya", "siblings"),
    ("Mere parents se rishta kaisa hai", "parents"),
    ("Mera shatru strong hai kya", "enemies"),
    ("Mera spiritual path kaisa hai", "spiritual"),
    ("Kya main famous hounga", "fame"),
    ("Mera swabhav kaisa hai", "personality"),
    ("Mere sapne ka matlab kya hai", "dreams"),
    ("Mujhe gussa jaldi kyu aata hai", "anger"),
    ("Kaun sa ratn pehnu", "remedy"),
    ("Daan karna chahiye kya", "charity"),
    ("Videsh me settle hona suitable hai kya", "settlement"),
    ("Ghar ka vastu theek hai kya", "vastu"),
    ("Pet rakhna chahiye kya", "pets"),
    ("Meri neend theek nahi aati", "wellness"),
]


class TestAskGapEngines(unittest.TestCase):
    def test_detect_all_gap_keys(self):
        for q, expected in _GAP_CASES:
            with self.subTest(q=q):
                self.assertEqual(detect_gap_static_key(q), expected)

    def test_timing_excluded(self):
        self.assertIsNone(detect_gap_static_key("bhai kab supportive hoga"))

    def test_engine_returns_evidence(self):
        out = run_gap_static_engine(_SAMPLE_KUNDLI, "Mera bhai supportive hai kya")
        self.assertIsNotNone(out)
        result, slice_id, topic, key = out
        self.assertEqual(key, "siblings")
        self.assertEqual(slice_id, "siblings_engine_v1")
        self.assertGreaterEqual(len(result.evidence), 4)
        self.assertIn("VERDICT:", result.to_narrator_payload())


if __name__ == "__main__":
    unittest.main()

"""Tests for Ask gap static engines + dispatch."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_gap_dispatch import detect_gap_static_key, gap_static_to_meta, run_gap_static_engine
from ask_mr.types import EngineResult

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
    ("Kya meri intuition power strong hai", "spiritual"),
    ("Mera past life karma kaisa hai", "spiritual"),
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

    def test_spiritual_awakening_routes_and_narrator_lock(self):
        q = "Kya mera kundli me spiritual awakening hai"
        out = run_gap_static_engine(_SAMPLE_KUNDLI, q)
        self.assertIsNotNone(out)
        result, slice_id, _topic, key = out
        self.assertEqual(key, "spiritual")
        self.assertEqual(slice_id, "spiritual_engine_v1")
        self.assertEqual(result.archetype, "spiritual_path")
        payload = result.to_narrator_payload()
        self.assertIn("NARRATOR_LOCK", payload)
        meta = gap_static_to_meta(result, slice_id=slice_id, topic="spiritual")
        self.assertEqual(meta.get("confidence"), result.confidence)

    def test_mixed_verdict_narrator_tone_not_bullish(self):
        eng = EngineResult(
            archetype="spiritual_path",
            verdict="Spiritual path mixed — phases of seeking + grounding dono",
            confidence="medium",
            evidence=["sample evidence"],
            checks={"open_chart_qa": True},
        )
        payload = eng.to_narrator_payload()
        self.assertIn("Do NOT upgrade", payload)
        self.assertIn("NARRATOR_LOCK", payload)
        self.assertNotIn("confident pattern voice", payload)


if __name__ == "__main__":
    unittest.main()

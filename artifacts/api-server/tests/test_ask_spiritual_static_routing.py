"""Spiritual static gap routing — intuition, karma, hijack guards."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_gap_dispatch import detect_gap_static_key
from ask_spiritual.spiritual_registry import detect_spiritual_archetype
from event_timing.timing_router import resolve_timing_domain

_SPIRITUAL_STATIC = [
    ("Kya meri intuition power strong hai", "intuition_occult"),
    ("Mera past life karma kaisa hai", "karma_past_life"),
    ("Kya mujhe guru milega", "guru_yog"),
    ("Mera spiritual awakening hua kya", "spiritual_path"),
    ("Kya main dhyan me focus kar paunga", "meditation_peace"),
    ("Shiv bhakti mere liye suitable hai kya", "deity_faith"),
    ("Kya mujhe moksha ka yog hai", "moksha_liberation"),
    ("Jo Guru abhi meri life me hain kya woh genuine hain", "guru_yog"),
    ("Kya meri kundli me sanyas yoga hai", "moksha_liberation"),
    ("Kya meri kundli me professional astrologer banne ka yoga hai", "intuition_occult"),
]

_HIJACK_CASES = [
    ("Kya mujhe sapno me divine sanket milenge", "spiritual"),
    ("Mere parents meri spirituality support karte hain kya", "spiritual"),
    ("Mera soul nature kaisa hai", "spiritual"),
]


class TestSpiritualStaticRouting(unittest.TestCase):
    def test_static_spiritual_gap_key(self):
        for q, _arch in _SPIRITUAL_STATIC:
            with self.subTest(q=q):
                dom, _, is_t = resolve_timing_domain(q)
                self.assertFalse(is_t, f"should be static: {q}")
                self.assertEqual(detect_gap_static_key(q), "spiritual")

    def test_spiritual_archetypes(self):
        for q, arch in _SPIRITUAL_STATIC:
            with self.subTest(q=q, arch=arch):
                self.assertEqual(detect_spiritual_archetype(q), arch)

    def test_no_hijack_from_other_gaps(self):
        for q, expected in _HIJACK_CASES:
            with self.subTest(q=q):
                self.assertEqual(detect_gap_static_key(q), expected)

    def test_timing_still_spiritual_domain(self):
        cases = [
            "Kya meri intuition power kab tak strong hogi",
            "Mere pichle janam ke punya kab se active honge",
            "Mera mukti kab hoga",
        ]
        for q in cases:
            with self.subTest(q=q):
                dom, bucket, is_t = resolve_timing_domain(q)
                self.assertTrue(is_t, q)
                self.assertEqual(dom, "spiritual", q)
                self.assertIn(
                    bucket,
                    ("occult_learning", "karma_past_life", "guru_deeksha", "general_spiritual", "inner_peace"),
                )


if __name__ == "__main__":
    unittest.main()

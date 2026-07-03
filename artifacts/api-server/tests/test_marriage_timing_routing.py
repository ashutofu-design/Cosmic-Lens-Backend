"""Marriage timing M17 must not steal static relationship questions."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_marriage_relationship_slice import is_marriage_relationship_static_question
from dcr_love import classify_buckets
from openai_helper import _is_marriage_timing_question


class MarriageTimingRoutingTests(unittest.TestCase):
    def test_shaadi_kab_is_timing_not_static(self):
        q = "Meri shaadi kab hogi?"
        self.assertFalse(is_marriage_relationship_static_question(q))
        self.assertTrue(_is_marriage_timing_question(q))

    def test_partner_nature_not_timing(self):
        for q in (
            "Mere partner ka nature kaisa hoga?",
            "Mere life partner ka nature kaisa hoga?",
            "mera pati ka nature kaisa hoga",
        ):
            with self.subTest(q=q):
                self.assertTrue(is_marriage_relationship_static_question(q))
                self.assertFalse(_is_marriage_timing_question(q))

    def test_love_vs_arranged_not_timing(self):
        q = "Love marriage hogi ya arranged marriage?"
        self.assertTrue(is_marriage_relationship_static_question(q))
        self.assertFalse(_is_marriage_timing_question(q))
        buckets = classify_buckets(q)
        self.assertIn("love_marriage_vs_arranged", buckets)

    def test_breakup_static_not_timing(self):
        q = "Kya mera rishta toot sakta hai?"
        self.assertTrue(is_marriage_relationship_static_question(q))
        self.assertFalse(_is_marriage_timing_question(q))


if __name__ == "__main__":
    unittest.main()

"""Promotion timing follow-up must route to timing engine, not static milestones."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class PromotionTimingFollowupRoutingTests(unittest.TestCase):
    def test_dec_2026_baad_is_career_timing(self):
        from ask_career.timing_registry import is_career_timing_question

        q = "agar yeh nhi hua to dec 2026 ke baad aur koi promotion he kya"
        self.assertTrue(is_career_timing_question(q, {"domain": "career"}))

    def test_dec_2026_baad_bucket_is_promotion(self):
        from ask_career.timing_registry import classify_career_timing_bucket

        q = "agar yeh nhi hua to dec 2026 ke baad aur koi promotion he kya"
        self.assertEqual(classify_career_timing_bucket(q), "promotion")


if __name__ == "__main__":
    unittest.main()

"""Promotion timing locked reply — PRIMARY vs backup (#2) window."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_career.timing_reply import (
    compose_promotion_timing_reply,
    detect_career_timing_constraint,
    pick_promotion_answer_window,
    window_dates_present_in_text,
)


def _promo_verdict() -> dict:
    return {
        "bucket": "promotion",
        "primary_window": "2026-06→2026-12",
        "promotion_engine": {
            "timing": {
                "windows": [
                    {
                        "rank": 1,
                        "lords": "Saturn/Saturn/Saturn",
                        "start": "2026-06",
                        "end": "2026-12",
                    },
                    {
                        "rank": 2,
                        "lords": "Saturn/Saturn/Mercury",
                        "start": "2026-12",
                        "end": "2027-05",
                    },
                    {
                        "rank": 3,
                        "lords": "Saturn/Saturn/Venus",
                        "start": "2027-07",
                        "end": "2028-01",
                    },
                ],
            },
        },
    }


class PromotionTimingReplyTests(unittest.TestCase):
    def test_primary_window_for_simple_question(self):
        q = "Meri promotion kab hogi?"
        w = pick_promotion_answer_window(_promo_verdict(), q)
        self.assertEqual(w.get("start"), "2026-06")
        self.assertEqual(w.get("end"), "2026-12")

    def test_backup_window_for_conditional_question(self):
        q = "next promotion kab hai agar 2026 june se dec tak nhi hoga to"
        self.assertTrue(detect_career_timing_constraint(q))
        w = pick_promotion_answer_window(_promo_verdict(), q)
        self.assertEqual(w.get("start"), "2026-12")
        self.assertEqual(w.get("end"), "2027-05")

    def test_next_time_phrase_uses_backup(self):
        q = "next time promotion kab ho sakta hai?"
        self.assertTrue(detect_career_timing_constraint(q))
        w = pick_promotion_answer_window(_promo_verdict(), q)
        self.assertEqual(w.get("start"), "2026-12")

    def test_compose_conditional_mentions_backup_dates(self):
        q = "next promotion kab hai agar 2026 june se dec tak nhi hoga to"
        text = compose_promotion_timing_reply(_promo_verdict(), q)
        self.assertTrue(window_dates_present_in_text(text, "2026-12", "2027-05"))
        self.assertFalse(window_dates_present_in_text(text, "2026-06", "2026-12"))

    def test_compose_simple_mentions_primary_dates(self):
        q = "Meri promotion kab hogi?"
        text = compose_promotion_timing_reply(_promo_verdict(), q)
        self.assertTrue(window_dates_present_in_text(text, "2026-06", "2026-12"))

    def test_after_dec_2026_uses_third_window(self):
        q = "agar yeh nhi hua to dec 2026 ke baad aur koi promotion he kya"
        w = pick_promotion_answer_window(_promo_verdict(), q)
        self.assertEqual(w.get("start"), "2027-07")


if __name__ == "__main__":
    unittest.main()

"""Universal #1 vs #2 timing window pick."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing._shared.timing_window_pick import (
    clip_timing_window_for_display,
    compose_timing_locked_reply,
    detect_next_timing_window_question,
    pick_timing_answer_window,
    timing_window_index,
    window_range_label,
)


class TimingWindowPickTests(unittest.TestCase):
    def _engine(self) -> dict:
        return {
            "next_3_windows": [
                {"md": "Saturn", "ad": "Saturn", "start_iso": "2026-06", "end_iso": "2026-12"},
                {"md": "Saturn", "ad": "Mercury", "start_iso": "2026-12", "end_iso": "2027-05"},
            ],
        }

    def test_first_ask_uses_primary(self):
        q = "Travel kab hoga?"
        self.assertEqual(timing_window_index(q), 0)
        w = pick_timing_answer_window(self._engine(), q)
        self.assertEqual(w.get("start"), "2026-06")

    def test_next_time_uses_second_window(self):
        for q in (
            "next kab ho sakta hai?",
            "agar is period me nahi hoga to agla kab?",
            "next time kab milega?",
        ):
            with self.subTest(q=q):
                self.assertTrue(detect_next_timing_window_question(q))
                w = pick_timing_answer_window(self._engine(), q)
                self.assertEqual(w.get("start"), "2026-12")

    def test_after_dec_2026_uses_third_window(self):
        q = "agar yeh nhi hua to dec 2026 ke baad aur koi promotion he kya"
        engine = {
            "promotion_engine": {
                "timing": {
                    "windows": [
                        {"lords": "Saturn/Saturn/Saturn", "start": "2026-06", "end": "2026-12"},
                        {"lords": "Saturn/Saturn/Mercury", "start": "2026-12", "end": "2027-05"},
                        {"lords": "Saturn/Saturn/Venus", "start": "2027-07", "end": "2028-01"},
                    ],
                },
            },
        }
        w = pick_timing_answer_window(engine, q)
        self.assertEqual(w.get("start"), "2027-07")
        self.assertEqual(w.get("end"), "2028-01")

    def test_past_start_is_clipped_to_current_month(self):
        today = datetime(2026, 8, 25)
        w = clip_timing_window_for_display(
            {"start": "2025-12", "end": "2027-10", "lords": "Saturn/Mercury/Mars"},
            today=today,
        )
        self.assertEqual(w.get("start"), "2026-08")
        self.assertEqual(w.get("end"), "2027-10")
        self.assertEqual(
            window_range_label(w),
            "August 2026 se October 2027 tak",
        )

    def test_fully_past_window_is_dropped(self):
        today = datetime(2026, 8, 25)
        self.assertIsNone(
            clip_timing_window_for_display({"start": "2024-01", "end": "2025-06"}, today=today)
        )

    def test_job_change_kab_question_skips_past_months(self):
        today = datetime(2026, 8, 25)
        engine = {
            "timing_window": {
                "next_career": {
                    "md": "Saturn",
                    "ad": "Mercury",
                    "pd": "Mars",
                    "start": "2025-12-01",
                    "end": "2027-10-15",
                    "lords": "Saturn/Mercury/Mars",
                },
            },
        }
        w = pick_timing_answer_window(engine, "job kab change hoga")
        self.assertIsNotNone(w)
        clipped = clip_timing_window_for_display(w, today=today)
        self.assertEqual(clipped.get("start"), "2026-08")
        reply = compose_timing_locked_reply(engine, "job kab change hoga", topic="job change")
        self.assertIn("August 2026", reply or "")
        self.assertNotIn("December 2025", reply or "")
        self.assertNotIn("2025", reply or "")


if __name__ == "__main__":
    unittest.main()

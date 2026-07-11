"""Universal #1 vs #2 timing window pick."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing._shared.timing_window_pick import (
    detect_next_timing_window_question,
    pick_timing_answer_window,
    timing_window_index,
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


if __name__ == "__main__":
    unittest.main()

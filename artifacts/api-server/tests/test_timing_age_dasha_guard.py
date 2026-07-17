"""Age ↔ dasha guard for non-marriage timing (stable walk + LLM match)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _windows(now_y: int = 2026):
    return [
        {
            "md": "Moon", "ad": "Mars", "pd": "Rahu",
            "start": f"{now_y}-03", "end": f"{now_y}-08",
            "window": f"{now_y}-03 → {now_y}-08",
            "lords": "Moon/Mars/Rahu",
        },
        {
            "md": "Moon", "ad": "Rahu", "pd": "Jupiter",
            "start": f"{now_y + 3}-01", "end": f"{now_y + 3}-06",
            "window": f"{now_y + 3}-01 → {now_y + 3}-06",
            "lords": "Moon/Rahu/Jupiter",
        },
        {
            "md": "Mars", "ad": "Jupiter", "pd": "Saturn",
            "start": f"{now_y + 6}-01", "end": f"{now_y + 6}-06",
            "window": f"{now_y + 6}-01 → {now_y + 6}-06",
            "lords": "Mars/Jupiter/Saturn",
        },
    ]


class TestTimingAgeDashaGuard(unittest.TestCase):
    def test_marriage_excluded(self):
        from ask_timing.age_dasha_guard import apply_timing_age_dasha_guard

        block = "=== MARRIAGE ===\n>>> NARRATE THIS WINDOW EXACTLY AS (#1 PRIMARY): 2026-07"
        out, audit = apply_timing_age_dasha_guard(
            client=None,
            question="shaadi kab hogi",
            domain="marriage",
            engine_raw={"next_3_windows": [{"start": "2026-07", "end": "2026-12", "window": "2026-07"}]},
            prompt_block=block,
            user_age=23,
        )
        self.assertEqual(out, block)
        self.assertEqual(audit.get("skipped"), "marriage_excluded")

    def test_baby_age_23_takes_next_dasha(self):
        from ask_timing.age_dasha_guard import apply_timing_age_dasha_guard

        now_y = 2026
        raw = {
            "engine_id": "children_timing_v1",
            "user_age": 23,
            "next_3_windows": _windows(now_y),
        }
        block = (
            "════════════════ CHILDREN / BABY TIMING ENGINE (LOCKED) ════════════════\n"
            f">>> NARRATE THIS WINDOW EXACTLY AS (#1 PRIMARY): {now_y}-03 → {now_y}-08\n"
        )
        out, audit = apply_timing_age_dasha_guard(
            client=None,
            question="baby kab hoga",
            domain="children",
            engine_raw=raw,
            prompt_block=block,
            user_age=23,
        )
        self.assertEqual(audit.get("result"), "locked")
        self.assertGreaterEqual(int(audit.get("picked_rank") or 0), 2)
        self.assertIn("STABLE TIMING LOCK", out)
        self.assertIn(f"{now_y + 3}", out)

    def test_same_question_twice_same_timing(self):
        from ask_timing.age_dasha_guard import apply_timing_age_dasha_guard

        now_y = 2026
        raw = {"next_3_windows": _windows(now_y), "user_age": 23}
        block = "=== TIMING ===\n>>> NARRATE THIS WINDOW EXACTLY AS (#1 PRIMARY): x\n"
        history = [
            {"role": "user", "content": "baby kab hoga"},
            {"role": "assistant", "content": f"Aapka baby window {now_y + 3}-01 dikhta hai"},
            {"role": "user", "content": "baby kab hoga"},
        ]
        out1, a1 = apply_timing_age_dasha_guard(
            client=None, question="baby kab hoga", domain="children",
            engine_raw=dict(raw), prompt_block=block, user_age=23, history=None,
        )
        out2, a2 = apply_timing_age_dasha_guard(
            client=None, question="baby kab hoga", domain="children",
            engine_raw=dict(raw), prompt_block=block, user_age=23, history=history,
        )
        self.assertEqual(a1.get("picked_rank"), a2.get("picked_rank"))
        self.assertEqual(a1.get("picked_window"), a2.get("picked_window"))
        self.assertFalse(a2.get("wants_next"))
        self.assertIn("STABLE TIMING LOCK", out2)

    def test_llm_mismatch_advances_next_only(self):
        from ask_timing.age_dasha_guard import apply_timing_age_dasha_guard

        client = MagicMock()
        # First candidate mismatch, second match
        client.chat.completions.create.side_effect = [
            MagicMock(choices=[MagicMock(message=MagicMock(
                content='{"match": false, "issues": ["too_soon"], "lock_note": "next", "reason": "early"}'
            ))]),
            MagicMock(choices=[MagicMock(message=MagicMock(
                content='{"match": true, "issues": [], "lock_note": "ok", "reason": "fit"}'
            ))]),
        ]
        raw = {
            "next_3_windows": [
                {"start": "2030-01", "end": "2030-06", "window": "2030-01", "lords": "A"},
                {"start": "2032-01", "end": "2032-06", "window": "2032-01", "lords": "B"},
            ],
        }
        block = ">>> NARRATE THIS WINDOW EXACTLY AS (#1 PRIMARY): 2030-01\n"
        out, audit = apply_timing_age_dasha_guard(
            client=client,
            question="property kab",
            domain="property",
            engine_raw=raw,
            prompt_block=block,
            user_age=30,
        )
        self.assertEqual(audit.get("picked_rank"), 2)
        self.assertIn("2032", out)
        self.assertEqual(client.chat.completions.create.call_count, 2)


if __name__ == "__main__":
    unittest.main()

"""Tests — universal answer fidelity verifier + retry loop."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestAnswerFidelity(unittest.TestCase):
    def test_infer_timing_shape(self):
        from ask_answer_fidelity import infer_answer_shape

        self.assertEqual(
            infer_answer_shape("Mera promotion kab hoga?", is_timing=True),
            "timing",
        )
        self.assertEqual(
            infer_answer_shape("Food business achha hai kya?"),
            "yes_no",
        )

    def test_timing_question_requires_period(self):
        from ask_answer_fidelity import verify_answer_fidelity

        ok, issues, _, _ = verify_answer_fidelity(
            "Mera promotion kab hoga?",
            "Aapko patience rakhni chahiye aur kaam par focus karein.",
            meta={"primary_window": "Promotion kab: Jupiter/Mercury · 2026-07 → 2027-02"},
            is_timing=True,
        )
        self.assertFalse(ok)
        self.assertIn("timing_question_no_period", issues)

    def test_timing_question_passes_with_engine_window(self):
        from ask_answer_fidelity import verify_answer_fidelity

        ok, issues, score, _ = verify_answer_fidelity(
            "Mera promotion kab hoga?",
            "Promotion ka strong window Jupiter/Mercury dasha mein 2026-07 se 2027-02 tak dikhta hai — abhi wait karein.",
            meta={"primary_window": "Promotion kab: Jupiter/Mercury · 2026-07 → 2027-02"},
            is_timing=True,
        )
        self.assertTrue(ok, issues)
        self.assertGreaterEqual(score, 0.8)

    def test_yes_no_requires_signal(self):
        from ask_answer_fidelity import verify_answer_fidelity

        ok, issues, _, _ = verify_answer_fidelity(
            "Food business achha hai kya?",
            "Chart mein 10th house strong hai aur gains axis active hai.",
        )
        self.assertFalse(ok)
        self.assertIn("yes_no_question_no_clear_signal", issues)

    def test_yes_no_passes(self):
        from ask_answer_fidelity import verify_answer_fidelity

        ok, issues, _, _ = verify_answer_fidelity(
            "Food business achha hai kya?",
            "Haan, food business aapke chart ke liye suitable hai — hospitality axis support karta hai.",
        )
        self.assertTrue(ok, issues)

    def test_fidelity_loop_repairs_until_ok(self):
        from ask_answer_fidelity import guard_answer_with_fidelity_loop

        client = MagicMock()
        client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(
                content="Promotion Jupiter/Mercury dasha mein 2026-07 se 2027-02 ke beech possible hai — abhi consolidate karein.",
            ))]
        )
        text, meta = guard_answer_with_fidelity_loop(
            client,
            "gpt-4o-mini",
            question="Mera promotion kab hoga?",
            answer="Focus on quality work and visibility.",
            meta={"primary_window": "2026-07 → 2027-02", "verdict": "yellow_wait"},
            is_timing=True,
        )
        self.assertIn("2026", text)
        self.assertTrue(meta.get("repairs"))
        self.assertTrue(meta.get("ok"))

    def test_static_promise_rejects_year_leak(self):
        from ask_answer_fidelity import verify_answer_fidelity

        ok, issues, _, _ = verify_answer_fidelity(
            "Kya mujhe life me true love milega?",
            "Haan, saccha pyaar 2024 ke second half se 2025 ke beech mil sakta hai.",
            is_timing=False,
        )
        self.assertFalse(ok)
        self.assertIn("static_promise_year_leak", issues)


if __name__ == "__main__":
    unittest.main()

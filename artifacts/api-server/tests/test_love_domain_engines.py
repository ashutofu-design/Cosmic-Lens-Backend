"""Tests for love domain — timing (8 buckets), static, milan."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.love import (
    assess_love_static,
    assess_love_timing,
    assess_milan,
    classify_love_timing_bucket,
    compute_love_window,
    format_love_timing_for_prompt,
    is_milan_question,
)
from love_engine import assess_love, format_verdict_for_prompt, extract_window_str


def _kundli() -> dict:
    return {
        "ascendant": "Libra",
        "planets": [
            {"name": "Venus", "sign": "Pisces", "house": 6},
            {"name": "Moon", "sign": "Taurus", "house": 8},
            {"name": "Mars", "sign": "Sagittarius", "house": 3},
            {"name": "Mercury", "sign": "Virgo", "house": 12},
            {"name": "Jupiter", "sign": "Aquarius", "house": 5},
            {"name": "Sun", "sign": "Leo", "house": 11},
            {"name": "Saturn", "sign": "Capricorn", "house": 4},
        ],
        "currentDasha": {"mahadasha": "Jupiter", "antardasha": "Venus"},
    }


def _intel() -> dict:
    return {
        "house_lords": [
            {"house": 5, "lord": "Saturn"},
            {"house": 7, "lord": "Mars"},
            {"house": 11, "lord": "Sun"},
        ],
        "dignities": [{"planet": "Venus", "status": "exalted"}],
    }


class TestLoveDomainEngines(unittest.TestCase):
    def test_timing_buckets(self):
        self.assertEqual(classify_love_timing_bucket("Patchup kab hoga?"), "reconciliation")
        self.assertEqual(classify_love_timing_bucket("Crush kab respond karega?"), "one_sided")
        self.assertEqual(classify_love_timing_bucket("Propose kab karun?"), "commitment")

    def test_timing_engine_locked_block(self):
        out = compute_love_window(_kundli(), _intel(), {}, None, "Pyaar kab milega?")
        block = format_love_timing_for_prompt(out)
        self.assertIn("LOVE TIMING ENGINE v1", block)
        self.assertIn("5L+7L", block)
        self.assertEqual(out.get("engine"), "love_timing_engine_v1")
        self.assertIn(out.get("bucket"), (
            "timing", "reconciliation", "one_sided", "commitment",
            "breakup", "meeting", "affair", "general_love",
            "family_approval", "healing", "stress_phase", "discovery",
        ))

    def test_static_engine_via_love_engine(self):
        out = assess_love(_kundli(), _intel(), {}, None, "Kya wo mujhse pyar karta hai?")
        self.assertTrue(out.get("score", 0) >= 0)
        self.assertIn(out.get("question_type"), (
            "general_love", "one_sided", "compatibility", "existing_status",
        ))
        block = format_verdict_for_prompt(out)
        self.assertIn("LOVE STATIC ENGINE", block)

    def test_timing_via_love_engine_wrapper(self):
        out = assess_love(_kundli(), _intel(), {}, None, "Patchup kab hoga?")
        self.assertEqual(out.get("question_type"), "reconciliation")
        self.assertTrue(extract_window_str(out) or out.get("strategy"))

    def test_milan_two_charts(self):
        self.assertTrue(is_milan_question("Hamari kundli match kaisi hai?"))
        b = {
            "ascendant": "Cancer",
            "planets": [
                {"name": "Moon", "sign": "Taurus", "house": 11, "sign_idx": 1},
                {"name": "Venus", "sign": "Gemini", "house": 12, "sign_idx": 2},
            ],
        }
        m = assess_milan(_kundli(), b, _intel(), {})
        self.assertIn("guna_score", m)
        self.assertIn(m.get("verdict"), (
            "MILAN_STRONG", "MILAN_GOOD", "MILAN_MODERATE", "MILAN_CHALLENGING",
        ))

    def test_router_love_still_works(self):
        from event_timing.timing_router import run_timing_engine, format_timing_block
        ctx = run_timing_engine(
            "Patchup kab hoga?", _kundli(), _intel(), {}, None, {"is_timing": True},
        )
        self.assertEqual(ctx.engine_status, "ready")
        self.assertIn("LOVE TIMING ENGINE", format_timing_block(ctx))


if __name__ == "__main__":
    unittest.main()

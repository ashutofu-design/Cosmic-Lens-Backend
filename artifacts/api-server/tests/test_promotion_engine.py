"""Tests for promotion_engine_v1 — 11L+10L BCP + promotion promise."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.career.promotion_engine_v1 import (
    assess_promotion,
    assess_promotion_promise,
    format_promotion_block_for_prompt,
    run_promotion_step1_bcp,
)


def _intel() -> dict:
    return {
        "house_lords": [
            {"house": 10, "lord": "Moon"},
            {"house": 11, "lord": "Sun"},
        ],
        "dignities": [
            {"planet": "Sun", "status": "exalted"},
            {"planet": "Moon", "status": "own-sign"},
            {"planet": "Jupiter", "status": "own-sign"},
        ],
    }


class TestPromotionEngine(unittest.TestCase):
    def test_bcp_step1_11l_10l(self):
        kundli = {
            "ascendant": "Cancer",
            "planets": [
                {"name": "Sun", "sign": "Taurus", "house": 11, "sign_idx": 1},
                {"name": "Moon", "sign": "Capricorn", "house": 7, "sign_idx": 9},
                {"name": "Jupiter", "sign": "Cancer", "house": 1, "sign_idx": 3},
                {"name": "Mars", "sign": "Aries", "house": 10, "sign_idx": 0},
            ],
        }
        lagna_si = 3  # Cancer → 11L=Venus, 10L=Mars
        step1 = run_promotion_step1_bcp(kundli, lagna_si, user_age=28)
        self.assertEqual(step1["eleventh_lord"], "Venus")
        self.assertEqual(step1["tenth_lord"], "Mars")
        self.assertTrue(step1.get("all_promotion_ages"))
        areas = step1.get("promotion_areas") or []
        self.assertTrue(any(a.get("role") == "11L" for a in areas))
        self.assertTrue(any(a.get("role") == "10L" for a in areas))

    def test_promotion_promise_10l_11l_link(self):
        kundli = {
            "ascendant": "Libra",
            "planets": [
                {"name": "Sun", "sign": "Virgo", "house": 11},
                {"name": "Moon", "sign": "Cancer", "house": 10},
            ],
            "divisionalCharts": {
                "D9": {"planets": [
                    {"name": "Sun", "sign": "Gemini", "house": 9},
                    {"name": "Moon", "sign": "Capricorn", "house": 4},
                ]},
                "D10": {"planets": [
                    {"name": "Sun", "sign": "Aquarius", "house": 11},
                    {"name": "Moon", "sign": "Leo", "house": 5},
                ]},
            },
        }
        intel = {
            "house_lords": [
                {"house": 10, "lord": "Moon"},
                {"house": 11, "lord": "Sun"},
            ],
            "dignities": [
                {"planet": "Sun", "status": "own-sign"},
                {"planet": "Moon", "status": "exalted"},
            ],
        }
        out = assess_promotion_promise(kundli, intel, karakas_d={"AmK": "Jupiter"})
        self.assertIn(out["promotion_promise_level"], ("high", "moderate"))
        self.assertGreaterEqual(out["promise_score"], 28)
        joined = " ".join(out["why"]).lower()
        self.assertTrue("11l" in joined or "10l" in joined)

    def test_prompt_block_locked(self):
        full = assess_promotion(
            {
                "ascendant": "Libra",
                "planets": [
                    {"name": "Sun", "sign": "Virgo", "house": 11},
                    {"name": "Moon", "sign": "Cancer", "house": 10},
                ],
            },
            _intel(),
            lagna_si=6,
            user_age=30,
        )
        block = format_promotion_block_for_prompt(full)
        self.assertIn("PROMOTION ENGINE v1 (LOCKED)", block)
        self.assertIn("CLASSICAL CHECKLIST", block)
        self.assertIn("AD/PD priority", block)
        self.assertIn("GUARD", block)

    def test_career_bucket_attaches_promotion_engine(self):
        from event_timing.career import assess_career, classify_career_question

        q = "Meri promotion kab hogi?"
        self.assertEqual(classify_career_question(q), "promotion")
        kundli = {
            "ascendant": "Libra",
            "planets": [
                {"name": "Sun", "sign": "Virgo", "house": 11},
                {"name": "Moon", "sign": "Cancer", "house": 10},
                {"name": "Mars", "sign": "Aries", "house": 7},
                {"name": "Mercury", "sign": "Virgo", "house": 11},
                {"name": "Jupiter", "sign": "Sagittarius", "house": 3},
                {"name": "Venus", "sign": "Pisces", "house": 6},
                {"name": "Saturn", "sign": "Capricorn", "house": 4},
            ],
            "currentDasha": {"mahadasha": "Jupiter", "antardasha": "Sun"},
        }
        out = assess_career(kundli, _intel(), kp={}, question=q)
        self.assertEqual(out["bucket"], "promotion")
        self.assertIn("promotion_engine", out)
        self.assertIn("promotion_prompt_block", out)
        self.assertIn("promotion_step1_bcp", out)
        audit = out.get("step_audit") or {}
        self.assertIn("step1", audit)
        promo_eng = out.get("promotion_engine") or {}
        self.assertIn("checklist", promo_eng.get("promise", {}))
        timing = promo_eng.get("timing") or {}
        self.assertIn("timing_source", timing)


if __name__ == "__main__":
    unittest.main()

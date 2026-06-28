"""Tests for transfer_engine_v1 — lean 3L+12L BCP + transfer likelihood/timing."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.career.transfer_engine_v1 import (
    assess_transfer,
    assess_transfer_likelihood,
    detect_transfer_mode,
    format_transfer_block_for_prompt,
    run_transfer_bcp_parallel,
)


def _intel() -> dict:
    return {
        "house_lords": [
            {"house": 3, "lord": "Mars"},
            {"house": 10, "lord": "Moon"},
            {"house": 12, "lord": "Venus"},
        ],
        "dignities": [
            {"planet": "Mars", "status": "own-sign"},
            {"planet": "Venus", "status": "exalted"},
        ],
    }


class TestTransferEngine(unittest.TestCase):
    def test_mode_detection(self):
        self.assertEqual(detect_transfer_mode("transfer kab hoga?"), "timing")
        self.assertEqual(detect_transfer_mode("kya transfer hoga?"), "general")

    def test_bcp_step1_3l_12l(self):
        kundli = {
            "ascendant": "Cancer",
            "planets": [
                {"name": "Mars", "sign": "Virgo", "house": 3, "sign_idx": 5},
                {"name": "Venus", "sign": "Gemini", "house": 12, "sign_idx": 2},
                {"name": "Moon", "sign": "Taurus", "house": 11, "sign_idx": 1},
            ],
        }
        lagna_si = 3  # Cancer → 3L=Mercury, 12L=Mercury (same sign lord possible)
        step1 = run_transfer_bcp_parallel(kundli, lagna_si, user_age=28)
        self.assertTrue(step1.get("third_lord"))
        self.assertTrue(step1.get("twelfth_lord"))
        self.assertTrue(step1.get("all_transfer_ages"))
        roles = {a.get("role") for a in (step1.get("transfer_areas") or [])}
        self.assertTrue("3L" in roles or "12L" in roles)

    def test_likelihood_3h_12h(self):
        kundli = {
            "ascendant": "Libra",
            "planets": [
                {"name": "Mars", "sign": "Sagittarius", "house": 3},
                {"name": "Venus", "sign": "Virgo", "house": 12},
                {"name": "Moon", "sign": "Cancer", "house": 10},
                {"name": "Rahu", "sign": "Gemini", "house": 9},
            ],
        }
        out = assess_transfer_likelihood(kundli, _intel(), lagna_si=6)
        self.assertTrue(out.get("fired"))
        self.assertIn(out["transfer_verdict"], (
            "STRONG_TRANSFER_LIKELY", "moderate_chance", "low_chance", "stay_put",
        ))
        joined = " ".join(out["why"]).lower()
        self.assertTrue("3l" in joined or "12l" in joined or "rahu" in joined)

    def test_prompt_block_locked(self):
        full = assess_transfer(
            {
                "ascendant": "Libra",
                "planets": [
                    {"name": "Mars", "sign": "Sagittarius", "house": 3},
                    {"name": "Venus", "sign": "Virgo", "house": 12},
                ],
            },
            _intel(),
            question="Meri posting kab milegi?",
            lagna_si=6,
            user_age=30,
        )
        block = format_transfer_block_for_prompt(full)
        self.assertIn("TRANSFER ENGINE v1 (LOCKED", block)
        self.assertIn("3L+12L", block)
        self.assertIn("GUARD", block)
        self.assertIn("AD/PD", block)

    def test_career_bucket_attaches_transfer_engine(self):
        from event_timing.career import assess_career, classify_career_question

        q = "Meri transfer kab hogi?"
        self.assertEqual(classify_career_question(q), "transfer")
        kundli = {
            "ascendant": "Libra",
            "planets": [
                {"name": "Mars", "sign": "Sagittarius", "house": 3},
                {"name": "Venus", "sign": "Virgo", "house": 12},
                {"name": "Moon", "sign": "Cancer", "house": 10},
                {"name": "Sun", "sign": "Leo", "house": 11},
                {"name": "Mercury", "sign": "Virgo", "house": 12},
                {"name": "Jupiter", "sign": "Sagittarius", "house": 3},
                {"name": "Saturn", "sign": "Capricorn", "house": 4},
                {"name": "Rahu", "sign": "Gemini", "house": 9},
            ],
            "currentDasha": {"mahadasha": "Jupiter", "antardasha": "Mars"},
        }
        out = assess_career(kundli, _intel(), kp={}, question=q)
        self.assertEqual(out["bucket"], "transfer")
        self.assertIn("transfer_engine", out)
        self.assertIn("transfer_prompt_block", out)
        self.assertIn("transfer_step1_bcp", out)
        self.assertNotIn("career_step1_bcp", out)
        audit = out.get("step_audit") or {}
        self.assertIn("all_transfer_ages", audit.get("step1") or {})
        conds = out.get("conditionals") or {}
        self.assertIn("C7_transfer", conds)
        self.assertEqual(conds["C7_transfer"].get("engine"), "transfer_engine_v1")
        timing = (out.get("transfer_engine") or {}).get("timing") or {}
        self.assertIn("timing_source", timing)


if __name__ == "__main__":
    unittest.main()

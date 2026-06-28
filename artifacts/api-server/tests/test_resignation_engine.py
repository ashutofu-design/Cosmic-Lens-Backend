"""Tests for resignation_engine_v1 — 12L+6L BCP + exit viability/timing."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.career.resignation_engine_v1 import (
    assess_resignation,
    assess_resignation_viability,
    detect_resignation_mode,
    format_resignation_block_for_prompt,
    run_resignation_bcp_parallel,
)


def _intel() -> dict:
    return {
        "house_lords": [
            {"house": 6, "lord": "Mars"},
            {"house": 8, "lord": "Mercury"},
            {"house": 10, "lord": "Moon"},
            {"house": 11, "lord": "Sun"},
            {"house": 12, "lord": "Venus"},
        ],
        "dignities": [
            {"planet": "Mars", "status": "debilitated"},
            {"planet": "Venus", "status": "own-sign"},
            {"planet": "Moon", "status": "exalted"},
        ],
    }


class TestResignationEngine(unittest.TestCase):
    def test_mode_detection(self):
        self.assertEqual(detect_resignation_mode("kya resign sahi hai?"), "viability")
        self.assertEqual(detect_resignation_mode("resignation kab dunga?"), "timing")
        self.assertEqual(detect_resignation_mode("kya resign karun aur kab?"), "both")

    def test_bcp_step1_12l_6l(self):
        kundli = {
            "ascendant": "Cancer",
            "planets": [
                {"name": "Venus", "sign": "Gemini", "house": 12, "sign_idx": 2},
                {"name": "Mars", "sign": "Capricorn", "house": 7, "sign_idx": 9},
                {"name": "Moon", "sign": "Taurus", "house": 11, "sign_idx": 1},
            ],
        }
        lagna_si = 3  # Cancer → 12L=Mercury, 6L=Jupiter
        step1 = run_resignation_bcp_parallel(kundli, lagna_si, user_age=30)
        self.assertEqual(step1["twelfth_lord"], "Mercury")
        self.assertEqual(step1["sixth_lord"], "Jupiter")
        self.assertTrue(step1.get("all_exit_ages"))
        areas = step1.get("exit_areas") or []
        roles = {a.get("role") for a in areas}
        self.assertIn("12L", roles)
        self.assertIn("6L", roles)

    def test_viability_12h_exit_channel(self):
        kundli = {
            "ascendant": "Libra",
            "planets": [
                {"name": "Venus", "sign": "Virgo", "house": 12},
                {"name": "Mars", "sign": "Aries", "house": 6},
                {"name": "Moon", "sign": "Cancer", "house": 10},
            ],
        }
        out = assess_resignation_viability(kundli, _intel(), lagna_si=6)
        self.assertTrue(out.get("fired"))
        self.assertIn(out["viability"], (
            "window_favourable", "plan_exit_3_6mo", "wait_for_window",
            "stay_financial_risk", "stay_hold",
        ))
        joined = " ".join(out["why"]).lower()
        self.assertTrue("12l" in joined or "6l" in joined)

    def test_prompt_block_locked(self):
        full = assess_resignation(
            {
                "ascendant": "Libra",
                "planets": [
                    {"name": "Venus", "sign": "Virgo", "house": 12},
                    {"name": "Mars", "sign": "Aries", "house": 6},
                ],
            },
            _intel(),
            question="resignation kab dunga?",
            lagna_si=6,
            user_age=32,
        )
        block = format_resignation_block_for_prompt(full)
        self.assertIn("RESIGNATION ENGINE v1 (LOCKED)", block)
        self.assertIn("CLASSICAL EXIT CHECKLIST", block)
        self.assertIn("AD/PD", block)
        self.assertIn("GUARD", block)
        self.assertIn("12L+6L", block)

    def test_career_bucket_attaches_resignation_engine(self):
        from event_timing.career import assess_career, classify_career_question

        q = "Kya resign karna sahi hai? Notice kab du?"
        self.assertEqual(classify_career_question(q), "resignation")
        kundli = {
            "ascendant": "Libra",
            "planets": [
                {"name": "Venus", "sign": "Virgo", "house": 12},
                {"name": "Mars", "sign": "Aries", "house": 6},
                {"name": "Moon", "sign": "Cancer", "house": 10},
                {"name": "Sun", "sign": "Leo", "house": 11},
                {"name": "Mercury", "sign": "Virgo", "house": 12},
                {"name": "Jupiter", "sign": "Sagittarius", "house": 3},
                {"name": "Saturn", "sign": "Capricorn", "house": 4},
            ],
            "currentDasha": {"mahadasha": "Saturn", "antardasha": "Venus"},
        }
        out = assess_career(kundli, _intel(), kp={}, question=q)
        self.assertEqual(out["bucket"], "resignation")
        self.assertIn("resignation_engine", out)
        self.assertIn("resignation_prompt_block", out)
        self.assertIn("resignation_step1_bcp", out)
        audit = out.get("step_audit") or {}
        self.assertIn("step1", audit)
        self.assertIn("all_exit_ages", audit["step1"])
        res_eng = out.get("resignation_engine") or {}
        self.assertIn("viability", res_eng)
        timing = res_eng.get("timing") or {}
        self.assertIn("timing_source", timing)
        conds = out.get("conditionals") or {}
        self.assertIn("C8_resignation", conds)
        self.assertEqual(conds["C8_resignation"].get("engine"), "resignation_engine_v1")


if __name__ == "__main__":
    unittest.main()

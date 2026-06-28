"""BCP career/job ages — 10L + 6L placement & aspects (STEP 1)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Sun", "sign": "Capricorn", "house": 2, "sign_idx": 9},
        {"name": "Moon", "sign": "Gemini", "house": 7, "sign_idx": 2},
        {"name": "Mars", "sign": "Cancer", "house": 8, "sign_idx": 3},
        {"name": "Mercury", "sign": "Aries", "house": 5, "sign_idx": 0},
        {"name": "Jupiter", "sign": "Pisces", "house": 4, "sign_idx": 11},
        {"name": "Venus", "sign": "Leo", "house": 9, "sign_idx": 4},
        {"name": "Saturn", "sign": "Virgo", "house": 10, "sign_idx": 5},
        {"name": "Rahu", "sign": "Aquarius", "house": 3, "sign_idx": 10},
        {"name": "Ketu", "sign": "Leo", "house": 9, "sign_idx": 4},
    ],
}


class TestBcpCareerAges(unittest.TestCase):
    def test_10l_6l_bcp_ages_computed(self):
        from event_timing.career.bcp_career_ages import compute_bcp_career_ages

        # Sagittarius lagna → 10L = Mercury (5H), 6L = Venus (9H)
        lagna_si = 8
        bcp = compute_bcp_career_ages(_SAMPLE_KUNDLI, lagna_si, user_age=28)
        self.assertEqual(bcp["tenth_lord"], "Mercury")
        self.assertEqual(bcp["sixth_lord"], "Venus")
        self.assertEqual(bcp["tenth_lord_house"], 5)
        self.assertEqual(bcp["sixth_lord_house"], 9)
        ages = bcp.get("all_job_ages") or []
        self.assertIn(5, ages)   # 10L in 5H
        self.assertIn(9, ages)   # 6L in 9H
        self.assertTrue(any(a >= 28 for a in ages))

    def test_career_step1_wrapper(self):
        from event_timing.career.career_step1_bcp import run_career_step1_bcp

        lagna_si = 8
        step1 = run_career_step1_bcp(_SAMPLE_KUNDLI, lagna_si, user_age=30)
        self.assertEqual(step1["tenth_lord"], "Mercury")
        self.assertEqual(step1["sixth_lord"], "Venus")
        areas = step1.get("career_areas") or []
        self.assertTrue(any(a.get("type") == "placement" and a.get("role") == "10L" for a in areas))
        self.assertTrue(any(a.get("type") == "placement" and a.get("role") == "6L" for a in areas))
        self.assertTrue(step1.get("all_job_ages"))

    def test_step_audit_step1_is_bcp(self):
        from event_timing.career.career_timing import build_career_timing_step_audit

        audit = build_career_timing_step_audit({
            "bucket": "govt_job",
            "tense": "future",
            "age_context": {"user_age": 25},
            "career_step1_bcp": {
                "tenth_lord": "Mercury",
                "tenth_lord_house": 5,
                "sixth_lord": "Saturn",
                "sixth_lord_house": 10,
                "all_job_ages": [5, 10, 17, 22],
                "detail": "10L Mercury in 5H · 6L Saturn in 10H",
            },
            "layers": {"L1_tenth_house": {"score": 3, "why": ["10L ok"]}},
            "triggers": {"T1_vimshottari": {"current_lords": "Jupiter/Saturn/Mercury", "score": 4}},
            "timing_window": {"current": {"lords": "Jupiter/Saturn/Mercury"}},
            "score_breakdown": {"layer_score": 5},
        })
        self.assertIn("BCP", audit["step1"]["name"])
        self.assertEqual(audit["step1"]["tenth_lord"], "Mercury")
        self.assertIn("step6", audit)
        self.assertIn("Dasha", audit["step6"]["name"])


if __name__ == "__main__":
    unittest.main()

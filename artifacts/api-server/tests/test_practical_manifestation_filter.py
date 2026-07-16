"""Tests for Practical Manifestation Filter (PMF)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestPMF(unittest.TestCase):
    def test_property_young_early_signal(self):
        from event_timing._shared.practical_manifestation_filter import (
            run_practical_manifestation_filter,
        )

        pmf = run_practical_manifestation_filter(
            "property",
            question="property kab buy karunga",
            user_age=22,
            kundli={
                "planets": [
                    {"name": "Saturn", "house": 12},
                    {"name": "Jupiter", "house": 8},
                ]
            },
        )
        self.assertEqual(pmf["filter"], "Practical Manifestation Filter")
        self.assertIn(pmf["overall"], ("EARLY_SIGNAL", "BLOCK_OR_DEFER"))
        checks = pmf["checks"]
        for key in (
            "age",
            "life_stage",
            "financial_readiness",
            "career_stability",
            "event_dependency",
            "legal_eligibility",
            "practical_reality",
        ):
            self.assertIn(key, checks)
        self.assertFalse(checks["age"]["ok"])

    def test_ready_adult_career(self):
        from event_timing._shared.practical_manifestation_filter import (
            run_practical_manifestation_filter,
        )

        pmf = run_practical_manifestation_filter(
            "career",
            question="promotion kab milegi",
            user_age=30,
            kundli={
                "planets": [
                    {"name": "Sun", "house": 10},
                    {"name": "Saturn", "house": 10},
                    {"name": "Mercury", "house": 1},
                    {"name": "Jupiter", "house": 11},
                ]
            },
        )
        self.assertEqual(pmf["overall"], "READY")
        self.assertTrue(pmf["eligible_now"])

    def test_eligibility_wraps_pmf_lock(self):
        from event_timing._shared.timing_eligibility import attach_timing_eligibility

        out = attach_timing_eligibility(
            {"_prompt_block": "=== TIMING ===\nWindow Jul 2026", "verdict": "OK"},
            domain="property",
            question="ghar kab kharidun",
            user_age=22,
        )
        self.assertIn("PRACTICAL MANIFESTATION FILTER", out["_prompt_block"])
        self.assertIn("pmf", out)
        self.assertTrue(out.get("eligibility_deferred"))


if __name__ == "__main__":
    unittest.main()

"""Tests for shared timing eligibility (PMF-backed age floor before dasha)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestTimingEligibility(unittest.TestCase):
    def test_property_buy_floor_24(self):
        from event_timing._shared.timing_eligibility import (
            assess_timing_eligibility,
            min_eligible_age,
        )

        self.assertEqual(min_eligible_age("property", "property kab buy karunga"), 24)
        elig = assess_timing_eligibility(
            "property",
            question="property kab buy karunga",
            user_age=22,
        )
        self.assertTrue(elig["too_young_now"])
        self.assertEqual(elig["life_stage"], "early")
        self.assertIn("pmf", elig)
        self.assertGreaterEqual(elig["earliest_year"], 2026)

    def test_property_rent_floor_lower(self):
        from event_timing._shared.timing_eligibility import min_eligible_age

        self.assertEqual(min_eligible_age("property", "kiraya ka ghar kab milega"), 18)

    def test_ready_adult(self):
        from event_timing._shared.timing_eligibility import assess_timing_eligibility

        elig = assess_timing_eligibility("career", question="promotion kab", user_age=30)
        self.assertFalse(elig["too_young_now"])
        self.assertEqual(elig["life_stage"], "ready")
        self.assertTrue(elig["eligible_now"])

    def test_attach_adds_pmf_prompt_lock(self):
        from event_timing._shared.timing_eligibility import attach_timing_eligibility

        raw = {
            "_prompt_block": "=== TIMING ENGINE ===\nWindow: Jul 2026",
            "verdict": "FAVOURABLE",
        }
        out = attach_timing_eligibility(
            raw,
            domain="property",
            question="ghar kab kharidun",
            user_age=22,
        )
        self.assertIn("PRACTICAL MANIFESTATION FILTER", out["_prompt_block"])
        self.assertTrue(out.get("eligibility_deferred"))
        self.assertEqual(out.get("life_stage"), "early")

    def test_utf_property_min_synced(self):
        from event_timing._shared.universal_timing_domains import MIN_PRACTICAL_AGE

        self.assertEqual(MIN_PRACTICAL_AGE.get("property"), 24)


if __name__ == "__main__":
    unittest.main()

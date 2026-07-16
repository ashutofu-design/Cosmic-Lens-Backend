"""BCP property ages — D1 4th lord placement + aspects."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing._shared.generic_timing_engine import _lagna_si
from event_timing.property.bcp_property_ages import compute_bcp_property_ages
from event_timing.property.property_timing_v1 import compute_property_window

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Saturn", "sign": "Virgo", "house": 10},
        {"name": "Mars", "sign": "Cancer", "house": 8},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Mercury", "sign": "Aries", "house": 5},
        {"name": "Jupiter", "sign": "Pisces", "house": 4},
        {"name": "Rahu", "sign": "Aquarius", "house": 3},
        {"name": "Sun", "sign": "Capricorn", "house": 2},
    ],
}


class TestPropertyBcpAges(unittest.TestCase):
    def test_property_uses_d9_and_d4_when_longitudes_are_available(self):
        chart = {
            **SAMPLE_KUNDLI,
            "ascendantDeg": 250.0,
            "planets": [
                {**planet, "longitude": float(index * 43 % 360)}
                for index, planet in enumerate(SAMPLE_KUNDLI["planets"])
            ],
        }
        raw = compute_property_window(
            chart, {}, {}, "1996-01-15", "me ghar kab buy karunga",
        )
        self.assertEqual(raw.get("divisional_charts_used"), ["D1", "D9", "D4"])

    def test_4l_jupiter_in_4h_placement_ages(self):
        lagna = _lagna_si(SAMPLE_KUNDLI)
        self.assertIsNotNone(lagna)
        bcp = compute_bcp_property_ages(SAMPLE_KUNDLI, lagna, user_age=30)
        self.assertEqual(bcp.get("fourth_lord"), "Jupiter")
        self.assertEqual(bcp.get("fourth_lord_house"), 4)
        all_ages = bcp.get("all_property_ages") or []
        self.assertIn(4, all_ages)
        d1_ages = bcp.get("d1_bcp_ages") or []
        self.assertTrue(all(a >= 30 for a in d1_ages))
        self.assertIn(32, d1_ages)
        self.assertTrue(bcp.get("focus_ages"))

    def test_property_engine_execution_does_not_use_bcp(self):
        raw = compute_property_window(
            SAMPLE_KUNDLI, {}, {}, "1996-01-15", "me ghar kab buy karunga",
        )
        self.assertNotIn("bcp_property_ages", raw)
        self.assertFalse(any("BCP" in str(x) for x in raw.get("factors") or []))
        self.assertEqual(raw.get("divisional_charts_used"), ["D1"])
        self.assertEqual(raw.get("divisional_charts_required"), ["D1", "D9", "D4"])

    def test_build_property_step1_bcp_fields(self):
        from event_timing.property.bcp_property_ages import build_property_step1_bcp

        bcp = compute_bcp_property_ages(SAMPLE_KUNDLI, _lagna_si(SAMPLE_KUNDLI), user_age=28)
        s1 = build_property_step1_bcp(bcp, 28)
        self.assertEqual(s1.get("fourth_lord"), "Jupiter")
        self.assertEqual(s1.get("fourth_lord_house"), 4)
        self.assertIn("aspects", s1.get("detail") or "")
        self.assertIn("rule", s1)

    def test_admin_does_not_recompute_property_bcp(self):
        from ask_llm_context_debug import recompute_property_bcp_from_kundli

        ctx = {
            "is_timing": True,
            "slice_meta": {
                "slice": "property_timing_v1",
                "step_audit": {
                    "step1": {
                        "name": "Active dasha — abhi kya chal raha hai",
                        "md": "Saturn",
                        "ad": "Saturn",
                        "pd": "Saturn",
                        "detail": "RUNNING MD/AD/PD Saturn/Saturn/Saturn",
                    },
                    "step2": {
                        "name": "Current AD/PD — property houses active?",
                        "detail": "ranked triggers: Mars",
                    },
                },
            },
        }
        out = recompute_property_bcp_from_kundli(
            ctx, SAMPLE_KUNDLI, "1996-01-15", question_text="me ghar kab buy karunga",
        )
        self.assertEqual(out, ctx)
        self.assertNotIn("bcp_property_ages", out.get("slice_meta") or {})


if __name__ == "__main__":
    unittest.main()

"""BCP property ages — D1 4th lord placement + aspects."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing._shared.generic_timing_engine import _lagna_si
from event_timing._shared.kaal_pipeline import expand_to_kaal_pipeline
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

    def test_step1_includes_bcp_for_property(self):
        raw = compute_property_window(
            SAMPLE_KUNDLI, {}, {}, "1996-01-15", "me ghar kab buy karunga",
        )
        self.assertTrue(raw.get("bcp_property_ages"))
        s1 = (raw.get("step_audit") or {}).get("step1") or {}
        self.assertIn("BCP", s1.get("name") or "")
        self.assertEqual(s1.get("fourth_lord"), "Jupiter")
        out = expand_to_kaal_pipeline(raw, "property")
        s1k = (out.get("step_audit") or {}).get("step1") or {}
        self.assertIn("BCP", s1k.get("name") or "")
        self.assertTrue(s1k.get("d1_bcp_ages") or s1k.get("focus_ages"))

    def test_build_property_step1_bcp_fields(self):
        from event_timing.property.bcp_property_ages import build_property_step1_bcp

        bcp = compute_bcp_property_ages(SAMPLE_KUNDLI, _lagna_si(SAMPLE_KUNDLI), user_age=28)
        s1 = build_property_step1_bcp(bcp, 28)
        self.assertEqual(s1.get("fourth_lord"), "Jupiter")
        self.assertEqual(s1.get("fourth_lord_house"), 4)
        self.assertIn("aspects", s1.get("detail") or "")
        self.assertIn("rule", s1)

    def test_admin_recompute_property_bcp_step1(self):
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
        sa = (out.get("slice_meta") or {}).get("step_audit") or {}
        s1 = sa.get("step1") or {}
        s2 = sa.get("step2") or {}
        self.assertIn("BCP", s1.get("name") or "")
        self.assertEqual(s1.get("fourth_lord"), "Jupiter")
        self.assertEqual(s1.get("fourth_lord_house"), 4)
        self.assertTrue(s1.get("recomputed_from_chart"))
        self.assertIn("Saturn", str(s2.get("detail") or ""))
        self.assertTrue((out.get("slice_meta") or {}).get("bcp_property_ages"))


if __name__ == "__main__":
    unittest.main()

"""All timing domains must expose dasha-first step_audit."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing._shared.generic_timing_engine import DomainTimingConfig, compute_generic_timing_window
from event_timing._shared.step_audit import (
    TIMING_STEP_ORDER,
    attach_timing_pipeline_audit,
    build_domain_timing_engine_trace,
    build_step_audit_from_timing_result,
    engine_id_for_domain,
)

_SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Saturn", "sign": "Virgo", "house": 10},
        {"name": "Mars", "sign": "Cancer", "house": 8},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Mercury", "sign": "Aries", "house": 5},
        {"name": "Jupiter", "sign": "Pisces", "house": 4},
        {"name": "Rahu", "sign": "Aquarius", "house": 3},
        {"name": "Ketu", "sign": "Leo", "house": 9},
        {"name": "Sun", "sign": "Capricorn", "house": 2},
    ],
    "dashas": [
        {
            "lord": "Jupiter",
            "start": "2020-01-01",
            "end": "2036-01-01",
            "antardashas": [
                {
                    "lord": "Saturn",
                    "start": "2024-01-01",
                    "end": "2026-12-01",
                    "pratyantar": [
                        {
                            "lord": "Mercury",
                            "start": "2025-06-01",
                            "end": "2025-12-01",
                        }
                    ],
                }
            ],
        }
    ],
}

_MINI_CFG = DomainTimingConfig(
    domain="love",
    concern_houses=[(5, 10.0, "5L"), (7, 10.0, "7L")],
    kp_cusps=[5, 7],
    double_transit_houses=[5, 7],
)


class TestAllDomainsStepAudit(unittest.TestCase):
    def test_generic_engine_attaches_step_audit(self):
        raw = compute_generic_timing_window(_SAMPLE_KUNDLI, _MINI_CFG)
        self.assertIn("step_audit", raw)
        self.assertIn("step5", raw["step_audit"])
        self.assertEqual(raw["step_audit"]["step5"]["name"], "Dasha activation (MD/AD/PD) — PRIMARY")

    def test_rich_engine_result_audit(self):
        now = datetime.utcnow()
        result = {
            "verdict": "FAVOURABLE_WINDOW",
            "band": "STRONG",
            "bucket": "foreign_settlement",
            "factors": [
                "STEP1 top=['Rahu', 'Jupiter', 'Moon']",
                "STEP5 dasha_windows_in_horizon=12",
                "STEP6 double_transit=STRONG",
            ],
            "current_window": {
                "md": "Jupiter",
                "ad": "Saturn",
                "pd": "Mercury",
                "start_iso": now.isoformat(),
                "end_iso": (now + timedelta(days=400)).isoformat(),
                "triggers": ["AD=Saturn(PROMOTE,+4.2)"],
            },
            "next_3_windows": [
                {
                    "md": "Jupiter",
                    "ad": "Mercury",
                    "start_iso": (now + timedelta(days=500)).isoformat(),
                    "end_iso": (now + timedelta(days=900)).isoformat(),
                    "score": 7.5,
                }
            ],
            "top_travel_planets": [{"name": "Rahu", "score": 18.0}],
            "kp_layer": {"score": 10.0},
        }
        out = attach_timing_pipeline_audit(result, "travel")
        self.assertIn("step5", out["step_audit"])
        self.assertTrue(out["step_audit"]["step5"]["current_lords"])
        ta = out["timing_audit"]
        self.assertEqual(ta["checks"][0]["name"], "dasha_trace")
        self.assertEqual(ta["checks"][1]["name"], "dasha_domain_activation")

    def test_all_domain_engine_ids(self):
        for domain in (
            "travel", "finance", "health", "children",
            "love", "education", "property", "litigation", "career",
        ):
            self.assertTrue(engine_id_for_domain(domain).endswith("_timing_v1"))

    def test_step_order_complete(self):
        result = attach_timing_pipeline_audit({"verdict": "X", "bucket": "y"}, "education")
        for key in TIMING_STEP_ORDER:
            self.assertIn(key, result["step_audit"])

    def test_engine_trace_payload(self):
        audit = build_step_audit_from_timing_result(
            {
                "verdict": "LOVE_WINDOW_SUPPORTIVE",
                "bucket": "timing",
                "current_window": {"md": "Venus", "ad": "Moon", "start_iso": "2025-01-01"},
            },
            "love",
        )
        trace = build_domain_timing_engine_trace(
            {"verdict": "LOVE_WINDOW_SUPPORTIVE", "step_audit": audit, "bucket": "timing"},
            "love",
        )
        self.assertEqual(trace["engine"], "love_timing_v1")
        self.assertIn("dasha_trace", trace)


if __name__ == "__main__":
    unittest.main()

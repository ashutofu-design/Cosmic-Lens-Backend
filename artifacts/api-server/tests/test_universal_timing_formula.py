"""Universal Timing Formula — Step 0 age gate + Steps 1–5."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _minimal_kundli() -> dict:
    return {
        "ascendant": "Sagittarius",
        "ascendantDeg": 250.0,
        "planets": [
            {"name": "Sun", "house": 5, "sign": "Aries", "sign_idx": 0},
            {"name": "Moon", "house": 7, "sign": "Gemini", "sign_idx": 2},
            {"name": "Mars", "house": 10, "sign": "Virgo", "sign_idx": 5},
            {"name": "Mercury", "house": 7, "sign": "Gemini", "sign_idx": 2},
            {"name": "Jupiter", "house": 2, "sign": "Capricorn", "sign_idx": 9},
            {"name": "Venus", "house": 6, "sign": "Taurus", "sign_idx": 1},
            {"name": "Saturn", "house": 11, "sign": "Libra", "sign_idx": 6},
            {"name": "Rahu", "house": 3, "sign": "Aquarius", "sign_idx": 10},
            {"name": "Ketu", "house": 9, "sign": "Leo", "sign_idx": 4},
        ],
        "dashas": [
            {
                "lord": "Jupiter",
                "start": "2020-01-01",
                "end": "2036-01-01",
                "subDashas": [
                    {
                        "lord": "Venus",
                        "start": "2024-06-01",
                        "end": "2027-06-01",
                        "pratyantar": [
                            {
                                "lord": "Mercury",
                                "start": "2026-01-01",
                                "end": "2026-07-01",
                            },
                        ],
                    },
                ],
            },
        ],
    }


class TestUniversalTimingFormula(unittest.TestCase):
    def test_shared_dasha_parser_reads_pratyantar_aliases(self):
        from event_timing._shared.generic_timing_engine import _dasha_children

        rows = [{"lord": "Venus"}]
        self.assertEqual(_dasha_children({"pratyantar_dashas": rows}), rows)
        self.assertEqual(_dasha_children({"pratyantardashas": rows}), rows)

    @patch("event_timing._shared.universal_timing_formula._step5_windows")
    def test_unqualified_ad_pd_windows_do_not_reach_final_selection(self, mock_windows):
        from event_timing._shared.universal_timing_domains import build_universal_formula_config
        from event_timing._shared.universal_timing_formula import _step3_dasha_activation

        now = datetime.utcnow()
        mock_windows.return_value = [{
            "md": "Saturn", "ad": "Moon", "pd": "Mars",
            "start": now + timedelta(days=10), "end": now + timedelta(days=30),
            "score": 99.0,
        }]
        qualified, step3, primary = _step3_dasha_activation(
            _minimal_kundli(),
            [{"name": "Jupiter", "score": 10.0, "links": ["5L"]}],
            build_universal_formula_config("children", "conception"),
            now,
        )
        self.assertEqual(qualified, [])
        self.assertIsNone(primary)
        self.assertEqual(step3.get("status"), "NONE_FOUND")

    def test_window_picker_prioritizes_ad_pd_confluence_over_earliest(self):
        from event_timing._shared.generic_timing_engine import pick_primary_timing_window

        now = datetime.utcnow()
        windows = [
            {
                "md": "Saturn", "ad": "Moon", "pd": "Jupiter",
                "start": now + timedelta(days=10), "end": now + timedelta(days=40),
            },
            {
                "md": "Saturn", "ad": "Jupiter", "pd": "Venus",
                "start": now + timedelta(days=80), "end": now + timedelta(days=120),
            },
        ]
        ranked = [
            {"name": "Jupiter", "score": 80.0},
            {"name": "Venus", "score": 75.0},
            {"name": "Moon", "score": 20.0},
        ]
        primary, _, _, _ = pick_primary_timing_window(
            windows,
            ranked,
            {"Jupiter", "Venus"},
            now,
            min_ad_pd=0,
        )
        self.assertEqual(primary.get("ad"), "Jupiter")
        self.assertEqual(primary.get("pd"), "Venus")

    def test_step1_uses_d1_d9_and_domain_divisional_chart(self):
        from event_timing._shared.universal_timing_formula import compute_universal_timing

        chart = _minimal_kundli()
        for index, planet in enumerate(chart["planets"]):
            planet["longitude"] = float(index * 37 % 360)
        out = compute_universal_timing(
            chart,
            "career",
            "promotion",
            {"year": datetime.utcnow().year - 28, "month": 5, "day": 10},
            "Promotion kab hogi?",
        )
        step1 = (out.get("step_audit") or {}).get("step1") or {}
        self.assertEqual(step1.get("charts_used"), ["D1", "D9", "D10"])
        self.assertTrue(step1.get("d9_house_lord"))
        self.assertTrue(step1.get("div_house_lord"))

    def test_step0_delays_baby_answer_for_16_year_old(self):
        from event_timing._shared.universal_timing_formula import compute_universal_timing

        birth = {"year": datetime.utcnow().year - 16, "month": 1, "day": 10}
        out = compute_universal_timing(
            _minimal_kundli(),
            "children",
            "conception",
            birth,
            "Mera baby kab hoga?",
        )
        s0 = (out.get("step_audit") or {}).get("step0") or {}
        s5 = (out.get("step_audit") or {}).get("step5") or {}
        self.assertTrue(s0.get("question_valid"))
        self.assertEqual(s0.get("status"), "DELAYED")
        self.assertEqual(s0.get("age_delay_years"), 4)
        self.assertNotEqual(out.get("verdict"), "QUESTION_NOT_PRACTICAL")
        self.assertIn(out.get("verdict"), ("DELAYED_WINDOW", "FAVOURABLE_WINDOW", "LOW_PROBABILITY"))
        if s5.get("primary_window"):
            self.assertTrue(s5.get("delayed_for_age"))

    def test_engine_arch_and_step_order(self):
        from event_timing._shared.universal_timing_formula import compute_universal_timing

        birth = {"year": datetime.utcnow().year - 28, "month": 5, "day": 10}
        out = compute_universal_timing(
            _minimal_kundli(),
            "career",
            "promotion",
            birth,
            "Mera promotion kab hoga?",
        )
        self.assertEqual(out.get("engine_arch"), "UNIVERSAL_TIMING_FORMULA_V1")
        self.assertEqual(
            out.get("step_order"),
            ["step0", "step1", "step2", "step3", "step4", "step5"],
        )
        self.assertIn("step0", out.get("step_audit") or {})
        self.assertIn("step5", out.get("step_audit") or {})

    def test_no_kp_layer(self):
        from event_timing._shared.universal_timing_formula import compute_universal_timing

        birth = {"year": datetime.utcnow().year - 30, "month": 5, "day": 10}
        out = compute_universal_timing(
            _minimal_kundli(),
            "travel",
            "visa_theme",
            birth,
            "Visa kab milega?",
        )
        self.assertNotIn("kp_layer", out)
        self.assertNotIn("kp_dasha_sync", out)


if __name__ == "__main__":
    unittest.main()

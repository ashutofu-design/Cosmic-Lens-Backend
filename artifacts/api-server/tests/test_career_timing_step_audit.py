"""Career timing step_audit + timing_audit (marriage-style pipeline)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _sample_verdict() -> dict:
    return {
        "bucket": "job_change",
        "tense": "future",
        "verdict": "yellow_wait",
        "score": 48,
        "confidence": 72,
        "strategy": "4-6 mahine consolidate karein, phir switch.",
        "age_context": {"user_age": 32, "age_reframe": None},
        "layers": {
            "L1_tenth_house": {"score": 4, "why": ["10L strong in Kendra"]},
            "L18_d9_overlay": {"score": 2},
            "L19_d10_overlay": {"score": 1},
            "L22_kp_csl": {"score": 3, "why": ["KP 10 cusp linked"]},
        },
        "triggers": {
            "T1_vimshottari": {
                "score": 5,
                "current_lords": "Jupiter/Saturn/Mercury",
                "career_lords_set": ["Saturn", "Mercury"],
                "why": ["AD lord Saturn rules 10H", "PD Mercury AmK"],
            },
            "T2_saturn_transit": {"score": 2, "why": ["Saturn on 10H"]},
            "T3_jupiter_yogini": {"score": 1, "why": ["Jupiter grace weak"]},
        },
        "timing_window": {
            "current": {
                "lords": "Jupiter/Saturn/Mercury",
                "start": "2024-03",
                "end": "2026-11",
            },
            "next_career": {
                "ad": "Mercury",
                "md": "Jupiter",
                "start": "2026-12",
                "end": "2029-02",
                "reason": "Mercury AmK AD",
            },
            "saturn_transit": {"on_tenth": True},
            "jupiter_active": {"sign": "Gemini"},
        },
        "score_breakdown": {"layer_score": 6, "trigger_score": 8},
        "brand_safety_warnings": ["No guarantee."],
        "reasons": ["10th lord strong", "Wait for AD shift"],
    }


class TestCareerTimingStepAudit(unittest.TestCase):
    def test_step_audit_has_dasha_primary_step6(self):
        from event_timing.career.career_timing import build_career_timing_step_audit

        audit = build_career_timing_step_audit(_sample_verdict())
        self.assertIn("step6", audit)
        s6 = audit["step6"]
        self.assertIn("Dasha", s6["name"])
        self.assertEqual(s6["status"], "DONE")
        self.assertIn("Jupiter/Saturn/Mercury", s6["current_lords"])
        self.assertTrue(s6.get("why"))

    def test_timing_audit_checks_dasha_first(self):
        from event_timing.career.career_timing import build_career_timing_audit

        ta = build_career_timing_audit(_sample_verdict())
        names = [c["name"] for c in ta.get("checks") or []]
        self.assertEqual(names[0], "dasha_trace")
        self.assertEqual(names[1], "dasha_career_activation")
        self.assertEqual(ta.get("status"), "PASS")

    def test_engine_trace_full_payload(self):
        from event_timing.career.career_timing import build_career_timing_engine_trace

        v = _sample_verdict()
        trace = build_career_timing_engine_trace(v)
        self.assertEqual(trace["engine"], "career_timing_v1")
        self.assertIn("step6", trace["step_audit"])
        self.assertIn("timing_audit", trace)
        self.assertIn("dasha_trace", trace)

    def test_slice_meta_includes_step_audit(self):
        from ask_hard_guards import build_career_timing_slice_meta

        v = _sample_verdict()
        v["step_audit"] = {"step6": {"current_lords": "Jupiter/Saturn/Mercury"}}
        v["timing_audit"] = {"status": "PASS"}
        meta = build_career_timing_slice_meta(v)
        self.assertEqual(meta["slice"], "career_timing_v1")
        self.assertIn("step_audit", meta)
        self.assertIn("timing_audit", meta)
        self.assertTrue(meta.get("dasha_trace"))

    def test_promotion_step_audit_omits_age_bcp_kp(self):
        from event_timing.career.career_timing import (
            build_career_timing_engine_trace,
            build_career_timing_step_audit,
            career_step_order_for_bucket,
        )

        v = _sample_verdict()
        v["bucket"] = "promotion"
        audit = build_career_timing_step_audit(v)
        self.assertNotIn("step1", audit)
        self.assertNotIn("step4", audit)
        self.assertNotIn("step0a", audit)
        self.assertEqual(audit["step0"]["name"], "User demand")
        self.assertNotIn("user_age", audit["step0"])
        self.assertNotIn("age", audit["step0"].get("detail", ""))

        trace = build_career_timing_engine_trace(v)
        self.assertEqual(trace.get("engine"), "career_timing_v1")
        order = list(trace.get("step_order") or [])
        self.assertNotIn("step1", order)
        self.assertNotIn("step4", order)
        self.assertEqual(order, list(career_step_order_for_bucket("promotion")))

    def test_hard_guards_trace_delegates_to_career_module(self):
        from ask_hard_guards import build_career_timing_engine_trace

        trace = build_career_timing_engine_trace(_sample_verdict())
        self.assertEqual(trace.get("engine"), "career_timing_v1")
        self.assertIn("step0", trace.get("step_order") or trace.get("step_audit", {}))

    def test_promotion_step8_uses_promotion_engine_timeline(self):
        from event_timing.career.career_timing import (
            _sync_promotion_timing_window,
            build_career_timing_engine_trace,
            build_career_timing_step_audit,
        )

        v = _sample_verdict()
        v["bucket"] = "promotion"
        v["promotion_engine"] = {
            "timing": {
                "timing_source": "next_dasha",
                "recommended_window": {
                    "md": "Saturn",
                    "ad": "Mercury",
                    "pd": "Venus",
                    "lords": "Saturn/Mercury/Venus",
                    "start": "2026-07",
                    "end": "2027-02",
                    "reason": "AD Mercury rules 10H",
                    "timing_source": "next_dasha",
                },
            },
        }
        _sync_promotion_timing_window(v)
        audit = build_career_timing_step_audit(v)
        s8 = audit["step8"]
        self.assertEqual(s8["status"], "DONE")
        self.assertIn("Promotion kab", s8.get("promotion_timeline") or "")
        self.assertIn("Saturn/Mercury/Venus", s8.get("promotion_timeline") or "")
        self.assertIn("2026-07", s8.get("detail") or "")

        trace = build_career_timing_engine_trace(v)
        self.assertIn("Promotion kab", str(trace.get("primary_window") or ""))
        dt = trace.get("dasha_trace") or {}
        self.assertEqual(dt.get("next_career_lords"), "Saturn/Mercury/Venus")

    def test_promotion_step8_shows_three_periods_primary_first(self):
        from event_timing.career.career_timing import build_career_timing_step_audit

        v = _sample_verdict()
        v["bucket"] = "promotion"
        v["promotion_engine"] = {
            "timing": {
                "timing_source": "next_dasha",
                "recommended_window": {
                    "md": "Jupiter",
                    "ad": "Mercury",
                    "pd": "Venus",
                    "lords": "Jupiter/Mercury/Venus",
                    "start": "2026-07",
                    "end": "2027-02",
                    "rank": 1,
                    "band": "PRIMARY",
                },
                "windows": [
                    {
                        "md": "Jupiter", "ad": "Mercury", "pd": "Venus",
                        "lords": "Jupiter/Mercury/Venus",
                        "start": "2026-07", "end": "2027-02", "rank": 1, "band": "PRIMARY",
                    },
                    {
                        "md": "Jupiter", "ad": "Saturn", "pd": "Mars",
                        "lords": "Jupiter/Saturn/Mars",
                        "start": "2027-03", "end": "2028-01", "rank": 2, "band": "BACKUP",
                    },
                    {
                        "md": "Saturn", "ad": "Mercury", "pd": "Jupiter",
                        "lords": "Saturn/Mercury/Jupiter",
                        "start": "2028-02", "end": "2029-06", "rank": 3, "band": "BACKUP",
                    },
                ],
            },
        }
        audit = build_career_timing_step_audit(v)
        s8 = audit["step8"]
        self.assertEqual(s8["status"], "DONE")
        periods = s8.get("promotion_periods") or []
        self.assertEqual(len(periods), 3)
        self.assertIn("PRIMARY", periods[0])
        self.assertIn("2026-07", periods[0])
        self.assertIn("answer_window", s8)
        self.assertIn("PRIMARY", str(s8.get("answer_window") or ""))

    def test_promotion_step8_never_uses_bcp_ages(self):
        from event_timing.career.career_timing import build_career_timing_step_audit

        v = _sample_verdict()
        v["bucket"] = "promotion"
        v["promotion_step1_bcp"] = {
            "future_priority_ages": [6, 18, 30, 42],
            "all_promotion_ages": [6, 18, 30, 42],
        }
        v["promotion_engine"] = {"timing": {"windows": [], "recommended_window": None}}
        v["triggers"]["T1_vimshottari"]["next_career_window"] = {
            "md": "Jupiter",
            "ad": "Mercury",
            "start": "2026-07",
            "end": "2029-02",
            "reason": "AD Mercury is career-significator",
        }
        audit = build_career_timing_step_audit(v)
        s8 = audit["step8"]
        detail = str(s8.get("detail") or "") + str(s8.get("promotion_timeline") or "")
        self.assertNotIn("BCP", detail)
        self.assertNotIn("bcp_ages", str(s8.get("timing_source") or ""))
        self.assertIn("Mercury", detail)

    def test_career_trace_step8_has_no_marriage_month_year(self):
        from event_timing.career.career_timing import build_career_timing_engine_trace

        trace = build_career_timing_engine_trace(_sample_verdict())
        s8 = (trace.get("step_audit") or {}).get("step8") or {}
        self.assertNotIn("marriage_month_year", s8)
        self.assertNotIn("late_chart_bcp_locked", s8)
        self.assertTrue(s8.get("next_ad") or s8.get("detail"))


if __name__ == "__main__":
    unittest.main()

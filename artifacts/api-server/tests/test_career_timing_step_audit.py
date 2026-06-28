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

    def test_hard_guards_trace_delegates_to_career_module(self):
        from ask_hard_guards import build_career_timing_engine_trace

        trace = build_career_timing_engine_trace(_sample_verdict())
        self.assertEqual(trace.get("engine"), "career_timing_v1")
        self.assertIn("step0", trace.get("step_order") or trace.get("step_audit", {}))


if __name__ == "__main__":
    unittest.main()

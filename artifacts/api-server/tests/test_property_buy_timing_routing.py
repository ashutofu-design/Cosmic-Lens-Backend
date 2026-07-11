"""Property buy timing — ghar kab kharidunga → property_timing_v1 + admin Kaal."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_property.timing_registry import is_property_timing_question, llm_says_property_timing
from ask_mr.timing_registry import finalize_is_timing_flag, question_requests_timing
from event_timing.property.property_timing_v1 import (
    _reconcile_property_answer_window,
    compute_property_window,
)
from event_timing.property.property_practicality import apply_property_practicality
from event_timing.timing_router import format_timing_block, resolve_timing_domain, run_timing_engine
from ask_hard_guards import is_real_timing_engine_block, passthrough_missing_required_engine

_Q = "me ghar kab buy karunga"
_LLM = {
    "domain": "property",
    "is_timing": True,
    "routed_domain": "property",
    "routed_timing": True,
}


def _sample_kundli() -> dict:
    return {
        "ascendant": "Sagittarius",
        "planets": [
            {"name": "Moon", "sign": "Gemini", "house": 7},
            {"name": "Saturn", "sign": "Virgo", "house": 10},
            {"name": "Mars", "sign": "Cancer", "house": 8},
            {"name": "Venus", "sign": "Leo", "house": 9},
            {"name": "Jupiter", "sign": "Pisces", "house": 4},
        ],
        "dashas": [{
            "lord": "Jupiter",
            "start": "2020-01-01",
            "end": "2036-01-01",
            "subDashas": [{
                "lord": "Venus",
                "start": "2024-01-01",
                "end": "2027-01-01",
                "subDashas": [{
                    "lord": "Mars",
                    "start": "2026-06-01",
                    "end": "2026-12-01",
                }],
            }],
        }],
    }


class TestPropertyBuyTimingRouting(unittest.TestCase):
    def test_is_property_timing_ghar_buy(self):
        self.assertTrue(is_property_timing_question(_Q))
        self.assertTrue(is_property_timing_question(_Q, _LLM))

    def test_llm_says_property_timing(self):
        self.assertTrue(llm_says_property_timing(_LLM))
        self.assertTrue(llm_says_property_timing({"routed_domain": "property", "routed_timing": True}))

    def test_question_requests_timing_property_llm(self):
        self.assertTrue(question_requests_timing(_Q, _LLM))
        self.assertTrue(finalize_is_timing_flag(_Q, True, _LLM))

    def test_resolve_domain_property_buy_bucket(self):
        dom, bucket, is_timing = resolve_timing_domain(_Q, _LLM)
        self.assertTrue(is_timing)
        self.assertEqual(dom, "property")
        self.assertEqual(bucket, "buy")

    def test_property_engine_block_and_step_audit(self):
        ctx = run_timing_engine(_Q, _sample_kundli(), {}, {}, {}, _LLM)
        block = format_timing_block(ctx) or ""
        self.assertEqual(ctx.engine_id, "property_timing_v1")
        self.assertIn(ctx.engine_status, ("ready", "partial"))
        self.assertTrue(is_real_timing_engine_block(block), block[:200])
        self.assertIn("PROPERTY TIMING ENGINE", block)
        raw = ctx.raw if isinstance(ctx.raw, dict) else {}
        self.assertTrue(raw.get("step_audit") or raw.get("verdict"))
        self.assertTrue(raw.get("dasha_running_now") or raw.get("current_window"))
        if raw.get("timing_periods"):
            self.assertTrue(raw.get("answer_window"))
        missing = passthrough_missing_required_engine(
            _Q, _LLM,
            domain_timing_block=block,
            has_domain_engine=is_real_timing_engine_block(block),
        )
        self.assertIsNone(missing)

    def test_reconcile_picks_mars_window_not_weak_saturn_pd(self):
        """Admin trace: Mars top sig but Saturn/Saturn/Saturn running → answer Mars PD window."""
        raw = {
            "verdict": "PROPERTY_LOW_PROBABILITY",
            "band": "WEAK",
            "timing_source": "current_dasha_active",
            "current_supports": True,
            "min_current_activation": 9.0,
            "current_running_activation_score": 12.0,
            "primary_significator": {"name": "Mars", "score": 18.99},
            "current_window": {
                "md": "Saturn",
                "ad": "Saturn",
                "pd": "Saturn",
                "start_iso": "2026-06-27",
                "end_iso": "2026-12-18",
                "is_active_now": True,
                "activation_score": 12.0,
            },
            "timing_periods": [
                {
                    "rank": 1,
                    "md": "Saturn",
                    "ad": "Saturn",
                    "pd": "Saturn",
                    "start_iso": "2026-06-27",
                    "end_iso": "2026-12-18",
                    "activation_score": 12.0,
                    "is_active_now": True,
                },
                {
                    "rank": 2,
                    "md": "Saturn",
                    "ad": "Saturn",
                    "pd": "Mars",
                    "start_iso": "2028-06-19",
                    "end_iso": "2028-08-22",
                    "activation_score": 15.0,
                },
            ],
            "factors": [],
        }
        fixed = _reconcile_property_answer_window(raw)
        ans = fixed.get("answer_window") or {}
        self.assertEqual(ans.get("pd"), "Mars")
        self.assertEqual(ans.get("start_iso"), "2028-06-19")
        self.assertEqual(fixed.get("timing_source"), "next_dasha_scan")
        self.assertEqual((fixed.get("timing_periods") or [{}])[0].get("pd"), "Mars")

    def test_practicality_delay_when_mars_window_future(self):
        raw = _reconcile_property_answer_window({
            "verdict": "PROPERTY_LOW_PROBABILITY",
            "band": "WEAK",
            "bucket": "buy",
            "timing_source": "next_dasha_scan",
            "current_supports": True,
            "min_current_activation": 9.0,
            "current_running_activation_score": 12.0,
            "primary_significator": {"name": "Mars", "score": 18.99},
            "top_planets": [{"name": "Mars", "score": 18}, {"name": "Jupiter", "score": 12}],
            "current_window": {
                "md": "Saturn", "ad": "Saturn", "pd": "Saturn",
                "start_iso": "2026-06-27", "end_iso": "2026-12-18",
                "is_active_now": True, "activation_score": 12.0,
            },
            "answer_window": {
                "rank": 1, "md": "Saturn", "ad": "Saturn", "pd": "Mars",
                "start_iso": "2028-06-19", "end_iso": "2028-08-22",
                "activation_score": 15.0, "lords": "Saturn/Saturn/Mars",
            },
            "timing_periods": [{
                "rank": 1, "md": "Saturn", "ad": "Saturn", "pd": "Mars",
                "start_iso": "2028-06-19", "end_iso": "2028-08-22",
                "activation_score": 15.0,
            }],
            "factors": [],
        })
        fixed = apply_property_practicality(raw, {}, "1990-01-15", "me ghar kab buy karunga")
        prac = fixed.get("practicality") or {}
        self.assertEqual(prac.get("buy_timing_label"), "delay")
        self.assertEqual(prac.get("purchase_timing_mode"), "DELAY_WAIT")
        self.assertFalse(prac.get("is_early_buy"))
        self.assertTrue(prac.get("is_delay_recommended"))
        self.assertIn("DELAY", fixed.get("strategy") or "")
        self.assertIn("2028-06-19", fixed.get("strategy") or "")


if __name__ == "__main__":
    unittest.main()

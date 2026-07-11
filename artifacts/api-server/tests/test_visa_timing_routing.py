"""Travel / visa timing — LLM-first routing → travel_timing_v1 + admin Kaal."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_travel.timing_registry import is_travel_timing_question, llm_says_travel_timing
from ask_mr.timing_registry import finalize_is_timing_flag, question_requests_timing
from event_timing.timing_router import format_timing_block, resolve_timing_domain, run_timing_engine
from ask_hard_guards import is_real_timing_engine_block, passthrough_missing_required_engine

_Q = "mera visa kab lagega"
_LLM = {
    "domain": "travel",
    "is_timing": True,
    "routed_domain": "travel",
    "routed_timing": True,
}


def _sample_kundli() -> dict:
    return {
        "ascendant": "Aries",
        "planets": [
            {"name": "Rahu", "house": 12, "sign": "Pisces"},
            {"name": "Jupiter", "house": 9, "sign": "Sagittarius"},
            {"name": "Moon", "house": 4, "sign": "Cancer"},
            {"name": "Saturn", "house": 10, "sign": "Capricorn"},
            {"name": "Venus", "house": 7, "sign": "Libra"},
        ],
        "dashas": [{
            "lord": "Saturn",
            "start": "2020-01-01",
            "end": "2039-01-01",
            "subDashas": [{
                "lord": "Jupiter",
                "start": "2026-01-01",
                "end": "2028-01-01",
                "subDashas": [{
                    "lord": "Venus",
                    "start": "2026-06-27",
                    "end": "2026-12-18",
                }],
            }],
        }],
    }


class TestVisaTimingRouting(unittest.TestCase):
    def test_is_travel_timing_visa(self):
        self.assertTrue(is_travel_timing_question(_Q))
        self.assertTrue(is_travel_timing_question(_Q, _LLM))

    def test_llm_says_travel_timing(self):
        self.assertTrue(llm_says_travel_timing(_LLM))
        self.assertTrue(llm_says_travel_timing({"routed_domain": "travel", "routed_timing": True}))

    def test_question_requests_timing_travel_llm(self):
        self.assertTrue(question_requests_timing(_Q, _LLM))
        self.assertTrue(finalize_is_timing_flag(_Q, True, _LLM))

    def test_resolve_domain_travel_visa_bucket(self):
        dom, bucket, is_timing = resolve_timing_domain(_Q, _LLM)
        self.assertTrue(is_timing)
        self.assertEqual(dom, "travel")
        self.assertEqual(bucket, "visa_theme")

    def test_travel_engine_block_and_step_audit(self):
        ctx = run_timing_engine(_Q, _sample_kundli(), {}, {}, {}, _LLM)
        block = format_timing_block(ctx) or ""
        self.assertEqual(ctx.engine_id, "travel_timing_v1")
        self.assertIn(ctx.engine_status, ("ready", "partial"))
        self.assertTrue(is_real_timing_engine_block(block), block[:160])
        raw = ctx.raw if isinstance(ctx.raw, dict) else {}
        self.assertTrue(raw.get("step_audit") or raw.get("verdict"))
        self.assertTrue(raw.get("dasha_running_now"))
        self.assertTrue(raw.get("answer_window"))
        self.assertTrue(raw.get("timing_periods"))
        run = raw.get("dasha_running_now") or {}
        self.assertTrue(run.get("md") and run.get("ad"))
        ans = raw.get("answer_window") or {}
        periods = raw.get("timing_periods") or []
        if periods:
            self.assertEqual(periods[0].get("start_iso"), ans.get("start_iso"))
            self.assertGreaterEqual(
                float(periods[0].get("score") or 0),
                float(periods[-1].get("score") or 0),
            )
        sa = raw.get("step_audit") or {}
        s1 = sa.get("step1") or {}
        s4 = sa.get("step4") or {}
        self.assertTrue(s1.get("current_lords"))
        self.assertEqual(s4.get("current_start"), ans.get("start_iso"))
        s8 = sa.get("step8") or {}
        if s8.get("event_month_year") and ans.get("start_iso"):
            self.assertIn(str(ans["start_iso"])[:4], str(s8.get("event_year") or s8.get("event_month_year")))
        missing = passthrough_missing_required_engine(
            _Q, _LLM,
            domain_timing_block=block,
            has_domain_engine=is_real_timing_engine_block(block),
        )
        self.assertIsNone(missing)


if __name__ == "__main__":
    unittest.main()

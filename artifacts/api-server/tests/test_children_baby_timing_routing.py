"""Children baby timing — mera baby kab hoga → children_timing_v1 + D7 + dasha."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_children.timing_registry import is_children_timing_question, llm_says_children_timing
from ask_health.health_registry import detect_health_archetype, is_health_static_question
from ask_mr.timing_registry import finalize_is_timing_flag, question_requests_timing
from event_timing.timing_router import format_timing_block, resolve_timing_domain, run_timing_engine
from ask_hard_guards import is_real_timing_engine_block

_Q = "mera baby kab hoga"
_LLM = {
    "domain": "children",
    "is_timing": True,
    "routed_domain": "children",
    "routed_timing": True,
}


def _sample_kundli() -> dict:
    return {
        "ascendant": "Sagittarius",
        "ascendantDeg": 250.0,
        "planets": [
            {"name": "Moon", "sign": "Gemini", "house": 7, "longitude": 95.0},
            {"name": "Saturn", "sign": "Virgo", "house": 10, "longitude": 165.0},
            {"name": "Mars", "sign": "Cancer", "house": 8, "longitude": 110.0},
            {"name": "Venus", "sign": "Leo", "house": 9, "longitude": 135.0},
            {"name": "Mercury", "sign": "Aries", "house": 5, "longitude": 25.0},
            {"name": "Jupiter", "sign": "Pisces", "house": 4, "longitude": 350.0},
            {"name": "Sun", "sign": "Capricorn", "house": 2, "longitude": 285.0},
            {"name": "Rahu", "sign": "Aquarius", "house": 3, "longitude": 310.0},
            {"name": "Ketu", "sign": "Leo", "house": 9, "longitude": 130.0},
        ],
        "dashas": [{
            "lord": "Jupiter",
            "start": "2020-01-01",
            "end": "2036-01-01",
            "children": [{
                "lord": "Saturn",
                "start": "2024-01-01",
                "end": "2027-01-01",
                "children": [{
                    "lord": "Mars",
                    "start": "2025-06-01",
                    "end": "2025-12-01",
                }],
            }],
        }],
    }


class TestChildrenBabyTimingRouting(unittest.TestCase):
    def test_is_children_timing_baby_kab(self):
        self.assertTrue(is_children_timing_question(_Q))
        self.assertTrue(is_children_timing_question(_Q, _LLM))
        self.assertTrue(llm_says_children_timing(_LLM))

    def test_health_engine_does_not_claim_baby_timing(self):
        self.assertFalse(is_health_static_question(_Q))
        self.assertIsNone(detect_health_archetype(_Q))

    def test_finalize_timing_flag_stays_true(self):
        self.assertTrue(question_requests_timing(_Q, _LLM))
        self.assertTrue(finalize_is_timing_flag(_Q, True, _LLM))

    def test_resolve_domain_children_conception(self):
        dom, bucket, timing = resolve_timing_domain(_Q, _LLM)
        self.assertEqual(dom, "children")
        self.assertTrue(timing)
        self.assertIn(bucket, ("conception", "general_children", "delay", "pregnancy"))

    def test_baby_engine_block_has_d7_and_dasha(self):
        ctx = run_timing_engine(_Q, _sample_kundli(), {}, {}, "1996-01-15", _LLM)
        self.assertEqual(ctx.engine_id, "children_timing_v1")
        block = format_timing_block(ctx) or ""
        self.assertTrue(is_real_timing_engine_block(block), block[:200])
        raw = ctx.raw if isinstance(ctx.raw, dict) else {}
        self.assertIn(raw.get("verdict"), (
            "CHILD_PROMISED", "FAVORABLE", "DELAYED", "OBSTRUCTED", "UNKNOWN",
        ))
        self.assertTrue(
            raw.get("d7_picture") or raw.get("next_child_window") or raw.get("next_3_windows"),
        )
        bcp = raw.get("bcp_baby_ages") or {}
        self.assertEqual(bcp.get("policy"), "BCP secondary; AD/PD primary")
        self.assertIn("D7", block.upper())


if __name__ == "__main__":
    unittest.main()

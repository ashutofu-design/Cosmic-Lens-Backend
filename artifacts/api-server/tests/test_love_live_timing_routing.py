"""Love timing — LLM-first routing; any phrasing / length → love_timing_v1."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_love.timing_registry import is_love_timing_question, llm_says_love_timing
from ask_mr.timing_registry import finalize_is_timing_flag, question_requests_timing
from event_timing.timing_router import resolve_timing_domain


_Q = "mera love live kab shuru hoga"
_LLM = {
    "domain": "love",
    "is_timing": True,
    "mr_archetype": "dating_courtship",
    "routed_domain": "love",
    "routed_timing": True,
    "routed_archetype": "dating_courtship",
}

_LONG_NO_KAB = """
Main aksar akela mehsoos karta hoon aur life mein koi special romantic connection nahi hai.
Chart mein kya pattern hai pyaar ke liye.
Kya aisa koi phase aayega jab relationship naturally shuru ho sakti hai.
Mujhe bas yeh samajhna hai ke stars kya kehte hain is bare mein.
"""

_LLM_LONG = {
    "domain": "love",
    "is_timing": True,
    "routed_domain": "love",
    "routed_timing": True,
    "mr_archetype": "general_love",
    "routed_archetype": "general_love",
}


class TestLoveLiveTimingRouting(unittest.TestCase):
    def test_is_love_timing_typo_without_llm(self):
        self.assertTrue(is_love_timing_question(_Q))

    def test_is_love_timing_typo_with_llm(self):
        self.assertTrue(is_love_timing_question(_Q, _LLM))

    def test_llm_says_love_timing_helper(self):
        self.assertTrue(llm_says_love_timing(_LLM))
        self.assertTrue(llm_says_love_timing({"routed_domain": "love", "routed_timing": True}))

    def test_long_narrative_llm_love_timing_without_kab_word(self):
        self.assertTrue(is_love_timing_question(_LONG_NO_KAB, _LLM_LONG))
        self.assertTrue(question_requests_timing(_LONG_NO_KAB, _LLM_LONG))
        self.assertTrue(finalize_is_timing_flag(_LONG_NO_KAB, True, _LLM_LONG))

    def test_resolve_domain_love_not_universal(self):
        dom, bucket, is_timing = resolve_timing_domain(_Q, _LLM)
        self.assertTrue(is_timing)
        self.assertEqual(dom, "love")
        self.assertEqual(bucket, "timing")

    def test_resolve_long_llm_love_not_universal(self):
        dom, bucket, is_timing = resolve_timing_domain(_LONG_NO_KAB, _LLM_LONG)
        self.assertTrue(is_timing)
        self.assertEqual(dom, "love")

    def test_routed_timing_only_intent(self):
        intent = {
            "routed_domain": "love",
            "routed_timing": True,
            "routed_archetype": "dating_courtship",
        }
        self.assertTrue(is_love_timing_question(_Q, intent))
        dom, _, is_timing = resolve_timing_domain(_Q, intent)
        self.assertTrue(is_timing)
        self.assertEqual(dom, "love")

    def test_office_approach_shubh_samay_routes_love_timing(self):
        q = (
            "Office mein ek ladki hai jise main bohot pasand karta hoon, par baat karne mein "
            "darr lagta hai. Kya mere chart mein abhi love approach karne ka koi shubh samay "
            "chal raha hai?"
        )
        self.assertTrue(is_love_timing_question(q))
        dom, bucket, is_timing = resolve_timing_domain(q, None)
        self.assertTrue(is_timing)
        self.assertEqual(dom, "love")

    def test_love_live_timing_block_passes_engine_guard(self):
        from ask_hard_guards import is_real_timing_engine_block
        from event_timing.timing_router import format_timing_block, run_timing_engine

        kundli = {
            "ascendant": "Aries",
            "planets": [
                {"name": "Venus", "house": 7, "sign": "Libra"},
                {"name": "Moon", "house": 5, "sign": "Leo"},
            ],
            "dashas": [{
                "lord": "Saturn", "start": "2020-01-01", "end": "2039-01-01",
                "subDashas": [{
                    "lord": "Saturn", "start": "2026-01-01", "end": "2028-01-01",
                    "subDashas": [{
                        "lord": "Saturn", "start": "2026-06-27", "end": "2026-12-18",
                    }],
                }],
            }],
        }
        ctx = run_timing_engine(_Q, kundli, {}, {}, {}, _LLM)
        block = format_timing_block(ctx) or ""
        self.assertEqual(ctx.engine_id, "love_timing_v1")
        self.assertTrue(is_real_timing_engine_block(block), block[:120])


if __name__ == "__main__":
    unittest.main()

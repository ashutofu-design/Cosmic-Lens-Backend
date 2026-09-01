"""Tests for D1-first LLM fallback (no generic engine refusal when chart exists)."""
from __future__ import annotations

import unittest

_SAMPLE_KUNDLI = {
    "ascendant": "Leo",
    "moonSign": "Taurus",
    "planets": [
        {"name": "Sun", "sign": "Leo", "house": 1, "degrees": "10°"},
        {"name": "Moon", "sign": "Taurus", "house": 10, "degrees": "5°"},
    ],
}


class TestAskChartLlmFallback(unittest.TestCase):
    def test_build_basic_d1_full_block(self):
        from ask_chart_llm_fallback import build_basic_d1_full_block

        block = build_basic_d1_full_block(_SAMPLE_KUNDLI, question="Career kaisi rahegi?")
        self.assertIn("D1 FULL BLOCK", block)
        self.assertIn("Sun", block)
        self.assertIn("Career kaisi", block)

    def test_selected_blocks_plus_d1_base(self):
        from ask_chart_llm_fallback import build_chart_text_for_llm_answer

        sel = "QUESTION_PRIORITY_FACTS:\n#1 [weak] Saturn: debilitated H6"
        out = build_chart_text_for_llm_answer(
            _SAMPLE_KUNDLI,
            question="Health issue?",
            selected_block_text=sel,
        )
        self.assertIn("QUESTION_PRIORITY_FACTS", out)
        self.assertIn("D1 BASE (always)", out)
        self.assertIn("D1 FULL BLOCK", out)

    def test_enforce_never_generic_refusal_when_d1_present(self):
        from ask_hard_guards import enforce_engine_only_or_refuse

        out = enforce_engine_only_or_refuse(
            question="Which career sector is best technology or marketing job or business?",
            qtype="STATIC",
            llm_intent={"domain": "general", "is_timing": False},
            checks={"slice_type": "full_compact"},
            slice_meta={},
            kundli=_SAMPLE_KUNDLI,
        )
        self.assertIsNone(out)

    def test_enforce_marriage_timing_without_engine_uses_d1_not_refusal(self):
        from ask_hard_guards import enforce_engine_only_or_refuse

        out = enforce_engine_only_or_refuse(
            question="Meri shaadi kab hogi?",
            qtype="TIMING",
            llm_intent={"domain": "marriage", "is_timing": True},
            checks={"slice_type": "timing_full_chart"},
            slice_meta={},
            marriage_block="",
            kundli=_SAMPLE_KUNDLI,
        )
        self.assertIsNone(out)

    def test_enforce_career_timing_without_engine_uses_d1_not_refusal(self):
        from ask_hard_guards import enforce_engine_only_or_refuse

        out = enforce_engine_only_or_refuse(
            question="Mera job change kab hoga",
            qtype="TIMING",
            llm_intent={"domain": "career", "is_timing": True},
            checks={"slice_type": "full_compact"},
            slice_meta={},
            career_block="",
            kundli=_SAMPLE_KUNDLI,
        )
        self.assertIsNone(out)


if __name__ == "__main__":
    unittest.main()

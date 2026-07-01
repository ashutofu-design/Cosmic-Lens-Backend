"""Universal D1+D9 chart+LLM systematic prompt."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_hard_guards import universal_chart_llm_fallback_eligible
from ask_universal_chart_llm import (
    build_universal_chart_llm_rules,
    infer_chart_topic,
)


class TestUniversalChartLlm(unittest.TestCase):
    def test_infer_love_topic(self):
        q = "Kya mujhse love life me dhoka milega"
        self.assertEqual(infer_chart_topic(q), "love")

    def test_rules_contain_systematic_steps(self):
        rules = build_universal_chart_llm_rules(
            "Meri career kaisi rahegi",
            qtype="STATIC",
            llm_intent={"domain": "career"},
        )
        self.assertIn("STEP 1", rules)
        self.assertIn("STEP 6", rules)
        self.assertIn("TOPIC FOCUS (career)", rules)
        self.assertIn("dignity", rules.lower())

    def test_timing_mode_in_rules(self):
        rules = build_universal_chart_llm_rules(
            "Meri shaadi kab hogi",
            qtype="TIMING",
            llm_intent={"domain": "marriage", "is_timing": True},
        )
        self.assertIn("MODE: TIMING", rules)
        self.assertIn("Mahadasha", rules)

    def test_universal_fallback_covers_mandatory_domain(self):
        q = "Kya mujhse love life me dhoka milega ya dhoka nehi milega"
        llm = {
            "domain": "love",
            "question_summary": "betrayal in love life",
            "is_timing": False,
        }
        self.assertTrue(
            universal_chart_llm_fallback_eligible(
                q,
                llm,
                qtype="STATIC",
                checks={"is_mr_static": True},
            )
        )


if __name__ == "__main__":
    unittest.main()

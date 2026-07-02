"""Open chart QA — locked facts for no-engine interpretive questions."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_chart_open_qa import (
    build_question_relevant_chart_facts,
    is_open_chart_interpretation_question,
    open_chart_qa_fallback_eligible,
    run_open_chart_qa,
    try_open_chart_qa_for_question,
)

_SAMPLE_KUNDLI = {
    "ascendant": "Leo",
    "planets": [
        {"name": "Sun", "house": 10, "sign": "Taurus"},
        {"name": "Moon", "house": 4, "sign": "Scorpio"},
        {"name": "Jupiter", "house": 9, "sign": "Aries"},
        {"name": "Ketu", "house": 12, "sign": "Cancer"},
        {"name": "Venus", "house": 9, "sign": "Aries"},
    ],
}


class TestOpenChartQaFallback(unittest.TestCase):
    def test_moksha_builds_spiritual_houses(self):
        q = "Kya meri kundli me moksha ka yog hai"
        facts = build_question_relevant_chart_facts(_SAMPLE_KUNDLI, q)
        joined = " ".join(facts).lower()
        self.assertIn("spiritual", joined)
        self.assertTrue(any("12" in f or "moksha" in f.lower() for f in facts))
        self.assertTrue(any("9" in f or "dharma" in f.lower() for f in facts))

    def test_moksha_interpretation_eligible(self):
        q = "Kya meri kundli me moksha ka yog hai"
        self.assertTrue(is_open_chart_interpretation_question(q))
        self.assertTrue(open_chart_qa_fallback_eligible(q, qtype="STATIC"))

    def test_timing_not_eligible(self):
        q = "Moksha kab milega"
        self.assertFalse(open_chart_qa_fallback_eligible(q, qtype="TIMING"))

    def test_chart_lookup_not_eligible(self):
        q = "12th house ka lord kaun hai"
        self.assertFalse(open_chart_qa_fallback_eligible(q, qtype="STATIC"))

    def test_try_open_chart_qa_returns_locked_payload(self):
        q = "Meri kundli me ketu moksha par kya effect dalta hai"
        out = try_open_chart_qa_for_question(_SAMPLE_KUNDLI, q, qtype="STATIC")
        self.assertIsNotNone(out)
        chart_text, meta = out
        self.assertIn("ARCHETYPE", chart_text.upper())
        self.assertEqual(meta.get("slice"), "open_chart_qa_engine_v1")
        self.assertGreater(len(meta.get("evidence") or []), 3)

    def test_love_style_still_has_venus_facts(self):
        q = "Meri kundli me venus mere love style ko kaise affect karti hai"
        res = run_open_chart_qa(_SAMPLE_KUNDLI, q)
        joined = " ".join(res.evidence or []).lower()
        self.assertIn("venus", joined)


if __name__ == "__main__":
    unittest.main()

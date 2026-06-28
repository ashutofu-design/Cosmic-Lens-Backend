"""Prem sambandh / love yog kab — must route to love timing, not chart_fact."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_love.timing_registry import is_love_timing_question
from chart_fact_answer import is_chart_lookup_question
from openai_helper import _classify_ask_intent, _resolve_response_lang


_Q = "Mere jeevan mein pehli baar prem sambandh ka yog kab banega"


class TestPremSambandhRouting(unittest.TestCase):
    def test_love_timing_regex(self):
        self.assertTrue(is_love_timing_question(_Q))

    def test_intent_is_timing_not_yoga_check(self):
        intent = _classify_ask_intent(_Q, "hn")
        self.assertEqual(intent["intent"], "timing_when")

    def test_not_chart_lookup(self):
        self.assertFalse(is_chart_lookup_question(_Q))

    def test_roman_hindi_question_gets_devanagari_reply_lang(self):
        self.assertEqual(_resolve_response_lang(_Q, "en", None), "hi")

    def test_explicit_hn_preference_keeps_hinglish_reply(self):
        self.assertEqual(_resolve_response_lang(_Q, "en", "hn"), "hn")

    def test_static_yoga_still_chart_lookup(self):
        q = "Kya meri kundli me Raj yoga hai?"
        intent = _classify_ask_intent(q, "hn")
        self.assertEqual(intent["intent"], "yoga_check")
        self.assertTrue(is_chart_lookup_question(q))


if __name__ == "__main__":
    unittest.main()

"""Marriage timing reply language = question language (hi | hn | en)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestMarriageTimingLang(unittest.TestCase):
    def test_answer_lang_follows_question(self):
        from openai_helper import _marriage_answer_lang

        self.assertEqual(
            _marriage_answer_lang("मेरा शादी कब और किससे होगा", "hinglish"),
            "hi",
        )
        self.assertEqual(
            _marriage_answer_lang("shaadi kab hogi", "english"),
            "hn",
        )
        self.assertEqual(
            _marriage_answer_lang("When will I get married?", "hinglish"),
            "en",
        )

    def test_devanagari_question_gets_devanagari_answer(self):
        from openai_helper import _compose_marriage_timing_reply

        text = _compose_marriage_timing_reply(
            "February – April 2033",
            0,
            "hn",  # picker says hinglish — question still wins
            question="मेरा शादी कब और किससे होगा",
        )
        self.assertEqual(
            text,
            "आपकी शादी फरवरी – अप्रैल 2033 के बीच होगी।",
        )

    def test_hinglish_question_gets_hinglish_answer(self):
        from openai_helper import _compose_marriage_timing_reply

        text = _compose_marriage_timing_reply(
            "February – April 2033",
            0,
            "hi",
            question="Meri shaadi kab hogi?",
        )
        self.assertEqual(
            text,
            "Aapki shaadi February – April 2033 ke beech hogi.",
        )

    def test_english_question_gets_english_answer(self):
        from openai_helper import _compose_marriage_timing_reply

        text = _compose_marriage_timing_reply(
            "February – April 2033",
            0,
            "hn",
            question="When will I get married?",
        )
        self.assertEqual(
            text,
            "Your marriage timing falls between February – April 2033.",
        )

    def test_devanagari_timing_detected(self):
        from openai_helper import _is_marriage_timing_question

        self.assertTrue(
            _is_marriage_timing_question("मेरा शादी कब और किससे होगा")
        )

    def test_safety_scrub_if_roman_leaks(self):
        from openai_helper import _force_devanagari_marriage_timing_answer

        scrubbed = _force_devanagari_marriage_timing_answer(
            "मेरा शादी कब होगा",
            "Aapki shaadi February – April 2033 ke beech hogi.",
        )
        self.assertEqual(
            scrubbed,
            "आपकी शादी फरवरी – अप्रैल 2033 के बीच होगी।",
        )


if __name__ == "__main__":
    unittest.main()

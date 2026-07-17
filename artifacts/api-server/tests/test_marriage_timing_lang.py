"""Marriage timing reply matches question language AND intent."""
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

    def test_devanagari_shaadi_question(self):
        from openai_helper import _compose_marriage_timing_reply

        text = _compose_marriage_timing_reply(
            "February – April 2033",
            0,
            "hn",
            question="मेरा शादी कब और किससे होगा",
        )
        self.assertEqual(
            text,
            "आपकी शादी फरवरी – अप्रैल 2033 के बीच होगी।",
        )

    def test_devanagari_jeevansathi_meet_question(self):
        from openai_helper import _compose_marriage_timing_reply

        text = _compose_marriage_timing_reply(
            "February – April 2033",
            0,
            "hn",
            question="मुझे मेरा जीवनसाथी कब मिलेगा?",
        )
        self.assertEqual(
            text,
            "आपको जीवनसाथी फरवरी – अप्रैल 2033 के बीच मिलने का समय दिखता है।",
        )
        self.assertNotIn("शादी", text)

    def test_hinglish_meet_question(self):
        from openai_helper import _compose_marriage_timing_reply

        text = _compose_marriage_timing_reply(
            "February – April 2033",
            0,
            "hi",
            question="Mujhe mera jeevansathi kab milega?",
        )
        self.assertIn("jeevansathi", text.lower())
        self.assertNotIn("shaadi", text.lower())

    def test_hinglish_shaadi_question(self):
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

    def test_scrub_wrong_shaadi_frame_for_meet_q(self):
        from openai_helper import align_ask_reply_to_question_lang

        scrubbed = align_ask_reply_to_question_lang(
            "मुझे मेरा जीवनसाथी कब मिलेगा?",
            "आपकी शादी फरवरी – अप्रैल 2033 के बीच होगी।",
        )
        self.assertIn("जीवनसाथी", scrubbed)
        self.assertNotIn("शादी", scrubbed)


if __name__ == "__main__":
    unittest.main()

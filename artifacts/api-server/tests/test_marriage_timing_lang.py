"""Devanagari question → Devanagari marriage timing reply."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestMarriageTimingLang(unittest.TestCase):
    def test_question_language_wins(self):
        from openai_helper import _resolve_response_lang

        # Devanagari → hi (even if picker sent hinglish)
        self.assertEqual(
            _resolve_response_lang("मेरा शादी कब और किससे होगा", "hinglish", None),
            "hi",
        )
        # Hinglish → hn
        self.assertEqual(
            _resolve_response_lang("shaadi kab hogi", "english", None),
            "hn",
        )
        # English → en (even if picker sent hinglish)
        self.assertEqual(
            _resolve_response_lang("When will I get married?", "hinglish", None),
            "en",
        )

    def test_compose_devanagari_reply(self):
        from openai_helper import _compose_marriage_timing_reply

        text = _compose_marriage_timing_reply(
            "February – April 2033", 0, "hi",
        )
        self.assertIn("आपकी शादी", text)
        self.assertIn("फरवरी", text)
        self.assertIn("अप्रैल", text)
        self.assertIn("2033", text)
        self.assertNotIn("Aapki shaadi", text)

    def test_compose_forces_hi_from_devanagari_question(self):
        from openai_helper import _compose_marriage_timing_reply

        # Even if lang=hn, Devanagari question forces Hindi reply
        text = _compose_marriage_timing_reply(
            "February – April 2033",
            0,
            "hn",
            question="मेरा शादी कब और किससे होगा",
        )
        self.assertIn("आपकी शादी", text)
        self.assertNotIn("Aapki shaadi", text)

    def test_force_scrub_roman_answer(self):
        from openai_helper import _force_devanagari_marriage_timing_answer

        scrubbed = _force_devanagari_marriage_timing_answer(
            "मेरा शादी कब होगा",
            "Aapki shaadi February – April 2033 ke beech hogi.",
        )
        self.assertIn("आपकी शादी", scrubbed)
        self.assertIn("फरवरी", scrubbed)
        self.assertNotIn("Aapki shaadi", scrubbed)

    def test_timing_question_detected_for_devanagari(self):
        from openai_helper import _is_marriage_timing_question

        self.assertTrue(
            _is_marriage_timing_question("मेरा शादी कब और किससे होगा")
        )


if __name__ == "__main__":
    unittest.main()

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

    def test_compose_hinglish_still_works(self):
        from openai_helper import _compose_marriage_timing_reply

        text = _compose_marriage_timing_reply(
            "February – April 2033", 0, "hn",
        )
        self.assertIn("Aapki shaadi", text)


if __name__ == "__main__":
    unittest.main()

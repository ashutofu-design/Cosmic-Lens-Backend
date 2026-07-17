"""Ask reply language follows the question for every domain."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_EN_MARRIAGE_ESSAY = (
    "I am currently going through a very difficult phase in my marriage, "
    "and things are not going well between us. There seems to be a complete "
    "lack of understanding and emotional connection lately. Even the smallest "
    "discussions are turning into constant arguments, and it feels like we "
    "are drifting apart day by day. I really want to understand what the root "
    "cause of these issues is and why we are facing so much negativity and "
    "distance in our relationship. Could you please analyze my situation and "
    "tell me what problems or planetary influences are causing this trouble "
    "in my married life, and how we can fix it"
)


class TestAskReplyLangGlobal(unittest.TestCase):
    def test_question_script_wins_over_picker(self):
        from openai_helper import _ask_lang_for_request, _resolve_response_lang

        cases = [
            ("मेरी नौकरी कब बदलेगी", "hinglish", "hi"),
            ("mera career kab improve hoga", "english", "hn"),
            ("When will my health improve?", "hindi", "en"),
            ("मेरा शादी कब और किससे होगा", "hinglish", "hi"),
        ]
        for q, picker, expect in cases:
            self.assertEqual(
                _resolve_response_lang(q, picker, "hn"),
                expect,
                msg=q,
            )
            code, api = _ask_lang_for_request(q, picker, "hn")
            self.assertEqual(code, expect, msg=q)
            self.assertIn(api, ("hindi", "hinglish", "english"))

    def test_long_english_marriage_essay_is_english(self):
        from openai_helper import _detect_question_lang, _resolve_response_lang

        # Regression: "the"/"me" used to force Hinglish on English essays
        self.assertEqual(_detect_question_lang(_EN_MARRIAGE_ESSAY, "en"), "en")
        self.assertEqual(
            _resolve_response_lang(_EN_MARRIAGE_ESSAY, "hinglish", "hn"),
            "en",
        )

    def test_short_hinglish_still_hinglish(self):
        from openai_helper import _detect_question_lang

        self.assertEqual(
            _detect_question_lang("Meri shaadi kab hogi?", "en"),
            "hn",
        )

    def test_preferred_does_not_override_question(self):
        from openai_helper import _resolve_response_lang

        self.assertEqual(
            _resolve_response_lang("मेरा स्वास्थ्य कैसा है", "hinglish", "hn"),
            "hi",
        )


if __name__ == "__main__":
    unittest.main()

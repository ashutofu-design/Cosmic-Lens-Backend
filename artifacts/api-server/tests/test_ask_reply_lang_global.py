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

    def test_english_with_kundli_loanword(self):
        from openai_helper import _detect_question_lang, _resolve_response_lang

        q = "What does my kundli say about my career?"
        self.assertEqual(_detect_question_lang(q, "hn"), "en")
        self.assertEqual(_resolve_response_lang(q, "hinglish", "hn"), "en")

    def test_english_when_will_marry(self):
        from openai_helper import _detect_question_lang

        self.assertEqual(
            _detect_question_lang("When will I get married?", "hn"),
            "en",
        )

    def test_preferred_does_not_override_question(self):
        from openai_helper import _resolve_response_lang

        self.assertEqual(
            _resolve_response_lang("मेरा स्वास्थ्य कैसा है", "hinglish", "hn"),
            "hi",
        )

    def test_hindi_question_needs_script_fix_on_latin_answer(self):
        from openai_helper import (
            _needs_hi_script_fix,
            _pt_language_system_override,
            align_ask_reply_to_question_lang,
        )

        q = "मेरी नौकरी के लिए कौन सा काम सही है?"
        latin = (
            "You are suited for careers involving communication and leadership "
            "because Mercury and Mars are strong in your chart."
        )
        self.assertTrue(_needs_hi_script_fix(q, latin))
        self.assertFalse(_needs_hi_script_fix(q, "आपके लिए संचार और नेतृत्व वाला काम सही है।"))
        self.assertFalse(_needs_hi_script_fix("Which job is best for me?", latin))
        self.assertIn("देवनागरी", _pt_language_system_override("hi"))
        self.assertEqual(_pt_language_system_override("hn"), "")
        # Without OpenAI, align keeps Latin body (rewrite is a no-op).
        aligned = align_ask_reply_to_question_lang(q, latin)
        self.assertTrue(isinstance(aligned, str) and aligned.strip())


class TestAskFollowupLangKey(unittest.TestCase):
    def test_hinglish_is_not_hindi(self):
        from ask_followup_chips import _lang_key, derive_follow_up_chips

        self.assertEqual(_lang_key("hinglish"), "hn")
        self.assertEqual(_lang_key("hindi"), "hi")
        self.assertEqual(_lang_key("english"), "en")
        self.assertEqual(_lang_key("hi"), "hi")
        hi_chips = derive_follow_up_chips(domain="career", lang="hi")
        hn_chips = derive_follow_up_chips(domain="career", lang="hinglish")
        en_chips = derive_follow_up_chips(domain="career", lang="english")
        self.assertTrue(any("\u0900" <= ch <= "\u097f" for c in hi_chips for ch in c))
        self.assertFalse(any("\u0900" <= ch <= "\u097f" for c in hn_chips for ch in c))
        self.assertTrue(any("promotion" in c.lower() for c in en_chips))

    def test_enrich_overwrites_mismatched_follow_ups(self):
        from ask_followup_chips import enrich_ask_result_followups

        out = {
            "text": "ok",
            "topic": "career",
            "domain": "career",
            "follow_ups": ["Promotion kab hogi?"],
        }
        enrich_ask_result_followups(out, lang="hi")
        self.assertTrue(
            any("\u0900" <= ch <= "\u097f" for c in out["follow_ups"] for ch in c)
        )


if __name__ == "__main__":
    unittest.main()

"""Ask reply language follows the question for every domain."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


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

    def test_preferred_does_not_override_question(self):
        from openai_helper import _resolve_response_lang

        # Profile sticky hinglish must not force Roman answer for Devanagari Q
        self.assertEqual(
            _resolve_response_lang("मेरा स्वास्थ्य कैसा है", "hinglish", "hn"),
            "hi",
        )


if __name__ == "__main__":
    unittest.main()

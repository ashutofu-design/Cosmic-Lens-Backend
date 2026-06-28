"""Tests for native overview routing (mere bare me kuch batao)."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_intent_llm import classify_ask_intent
from ask_native_overview import is_native_overview_question


class NativeOverviewTests(unittest.TestCase):
    def test_detects_mere_bare_me_kuch_batao(self):
        self.assertTrue(is_native_overview_question("Mere bare me kuch batao"))

    def test_detects_tell_me_about_myself(self):
        self.assertTrue(is_native_overview_question("Tell me about myself"))

    def test_not_overview_when_shaadi_mentioned(self):
        self.assertFalse(
            is_native_overview_question("Mere bare me batao shaadi kab hogi")
        )

    @patch("ask_intent_llm.client", create=True)
    def test_intent_llm_overrides_wrong_partner_nature(self):
        payload = {
            "domain": "marriage",
            "is_timing": False,
            "is_decision": False,
            "wants_explain": False,
            "mr_archetype": "partner_nature",
            "interpretation": "User wants to know about in-laws.",
            "confidence": 0.95,
        }

        class _Msg:
            content = __import__("json").dumps(payload)

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        class _Comp:
            def create(self, **kw):
                return _Resp()

        class _Chat:
            completions = _Comp()

        class _Client:
            chat = _Chat()

        res = classify_ask_intent("Mere bare me kuch batao", client=_Client())
        self.assertEqual(res["domain"], "general")
        self.assertIsNone(res["mr_archetype"])
        self.assertIn("themselves", res["interpretation"].lower())


if __name__ == "__main__":
    unittest.main()

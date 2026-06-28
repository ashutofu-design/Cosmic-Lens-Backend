"""Tests for LLM scope fallback (astro vs off-topic)."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_scope_gate import assess_ask_scope
from ask_scope_llm import classify_ask_scope_llm


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, payload):
        self._payload = payload

    def create(self, **kwargs):
        return _FakeResponse(json.dumps(self._payload))


class _FakeChat:
    def __init__(self, payload):
        self.completions = _FakeCompletions(payload)


class _FakeClient:
    def __init__(self, payload):
        self.chat = _FakeChat(payload)


def _client(payload):
    return _FakeClient(payload)


class AskScopeLlmTests(unittest.TestCase):
    def test_classify_personal_astro_heavy_typo(self):
        payload = {
            "category": "personal_astro",
            "cleaned_question": "health kaisi rahegi",
            "confidence": 0.91,
        }
        res = classify_ask_scope_llm("hlt kysi rhgi", client=_client(payload))
        self.assertTrue(res["allowed"])
        self.assertEqual(res["reason"], "ok")
        self.assertEqual(res["cleaned_question"], "health kaisi rahegi")

    def test_classify_blocks_recipe(self):
        payload = {
            "category": "off_topic",
            "cleaned_question": "biryani recipe",
            "confidence": 0.95,
        }
        res = classify_ask_scope_llm("biryani recipe batao", client=_client(payload))
        self.assertFalse(res["allowed"])
        self.assertEqual(res["reason"], "off_topic")

    def test_classify_blocks_gk(self):
        payload = {
            "category": "general_knowledge",
            "cleaned_question": "astrology kya hai",
            "confidence": 0.88,
        }
        res = classify_ask_scope_llm("astrology kya hai matlab", client=_client(payload))
        self.assertFalse(res["allowed"])
        self.assertEqual(res["reason"], "general_knowledge")

    @patch("ask_scope_llm.classify_ask_scope_llm")
    def test_scope_gate_llm_fallback_allows_heavy_typo(self, mock_llm):
        mock_llm.return_value = {
            "allowed": True,
            "reason": "ok",
            "cleaned_question": "health kaisi rahegi",
            "confidence": 0.9,
            "source": "llm",
        }
        v = assess_ask_scope("hlt kysi rhgi")
        self.assertTrue(v.allowed, v.reason)
        mock_llm.assert_called_once()
        self.assertIsNotNone(v.normalized_question)


if __name__ == "__main__":
    unittest.main()

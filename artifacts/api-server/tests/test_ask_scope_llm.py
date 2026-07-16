"""Tests for Ask scope — allow all cosmic; block only clear off-topic."""
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

    def test_classify_blocks_recipe(self):
        payload = {
            "category": "off_topic",
            "cleaned_question": "biryani recipe",
            "confidence": 0.95,
        }
        res = classify_ask_scope_llm("biryani recipe batao", client=_client(payload))
        self.assertFalse(res["allowed"])
        self.assertEqual(res["reason"], "off_topic")

    def test_gate_blocks_biryani_hard(self):
        v = assess_ask_scope("biryani recipe batao")
        self.assertFalse(v.allowed)
        self.assertEqual(v.reason, "off_topic")

    def test_gate_allows_dharmik_without_llm(self):
        with patch("ask_scope_llm.classify_ask_scope_llm") as mock_llm:
            v = assess_ask_scope("kya me dharmik hun")
            self.assertTrue(v.allowed, v.reason)
            mock_llm.assert_not_called()

    def test_gate_allows_leo_gemstone_without_llm(self):
        with patch("ask_scope_llm.classify_ask_scope_llm") as mock_llm:
            v = assess_ask_scope(
                "agar kisi ka leo lagna he to konsa gemstoene dharan karna chahiye"
            )
            self.assertTrue(v.allowed, v.reason)
            mock_llm.assert_not_called()

    def test_gate_allows_astrology_theory(self):
        """Theory/concept Qs must get answers — not refused as GK."""
        with patch("ask_scope_llm.classify_ask_scope_llm") as mock_llm:
            v = assess_ask_scope("astrology kya hai")
            self.assertTrue(v.allowed, v.reason)
            mock_llm.assert_not_called()

    def test_gate_allows_when_llm_says_gk(self):
        with patch("ask_scope_llm.classify_ask_scope_llm") as mock_llm:
            mock_llm.return_value = {
                "allowed": False,
                "reason": "general_knowledge",
                "cleaned_question": "random",
                "confidence": 0.99,
                "source": "llm",
            }
            # No cosmic anchor → still fail-open (answer layer handles).
            v = assess_ask_scope("batao kuch interesting")
            self.assertTrue(v.allowed, v.reason)

    def test_gate_blocks_only_confident_off_topic_from_llm(self):
        with patch("ask_scope_llm.classify_ask_scope_llm") as mock_llm:
            mock_llm.return_value = {
                "allowed": False,
                "reason": "off_topic",
                "cleaned_question": "tell a joke",
                "confidence": 0.95,
                "source": "llm",
            }
            v = assess_ask_scope("tell a joke please")
            self.assertFalse(v.allowed)
            self.assertEqual(v.reason, "off_topic")


if __name__ == "__main__":
    unittest.main()

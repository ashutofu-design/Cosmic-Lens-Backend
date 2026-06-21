import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_intent_llm import classify_ask_intent
from ask_mr import run_mr_static_engine
from ask_mr.classifier import classify_mr_archetype


SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Saturn", "sign": "Virgo", "house": 10},
        {"name": "Mars", "sign": "Cancer", "house": 8},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Mercury", "sign": "Aries", "house": 5},
        {"name": "Jupiter", "sign": "Pisces", "house": 4},
        {"name": "Rahu", "sign": "Aquarius", "house": 3},
        {"name": "Ketu", "sign": "Leo", "house": 9},
        {"name": "Sun", "sign": "Capricorn", "house": 2},
    ],
    "divisionalCharts": {
        "D9": {
            "ascendant": "Libra",
            "planets": [
                {"name": "Moon", "sign": "Capricorn", "house": 4},
                {"name": "Venus", "sign": "Aquarius", "house": 5},
                {"name": "Mars", "sign": "Aries", "house": 7},
            ],
        }
    },
}


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
    def __init__(self, payload, *, raise_exc=None):
        self._payload = payload
        self._raise_exc = raise_exc

    def create(self, **kwargs):
        if self._raise_exc is not None:
            raise self._raise_exc
        return _FakeResponse(json.dumps(self._payload))


class _FakeChat:
    def __init__(self, payload, *, raise_exc=None):
        self.completions = _FakeCompletions(payload, raise_exc=raise_exc)


class _FakeClient:
    """Minimal stand-in for the OpenAI client used by classify_ask_intent."""

    def __init__(self, payload, *, raise_exc=None):
        self.chat = _FakeChat(payload, raise_exc=raise_exc)


def _client(payload, **kw):
    return _FakeClient(payload, **kw)


class ClassifyAskIntentTests(unittest.TestCase):
    def test_partner_career_support_routes_out_of_general_mr(self):
        # The failing real-world example: regex mislabels this general_mr.
        # The LLM understands it is partner_nature (partner supporting goals).
        payload = {
            "domain": "love",
            "is_timing": False,
            "is_decision": False,
            "wants_explain": False,
            "mr_archetype": "partner_nature",
            "confidence": 0.86,
        }
        res = classify_ask_intent(
            "Mera partner mujse career me support karegi kya",
            client=_client(payload),
        )
        self.assertEqual(res["source"], "llm")
        self.assertEqual(res["domain"], "love")
        self.assertEqual(res["mr_archetype"], "partner_nature")
        self.assertFalse(res["is_timing"])

    def test_timing_question(self):
        payload = {
            "domain": "marriage",
            "is_timing": True,
            "is_decision": False,
            "wants_explain": False,
            "mr_archetype": "general_mr",
            "confidence": 0.9,
        }
        res = classify_ask_intent("Meri shaadi kab hogi?", client=_client(payload))
        self.assertTrue(res["is_timing"])
        self.assertEqual(res["domain"], "marriage")

    def test_finance_domain_clears_archetype(self):
        payload = {
            "domain": "finance",
            "is_timing": False,
            "is_decision": False,
            "wants_explain": False,
            "mr_archetype": "general_mr",  # should be cleared (non-relationship)
            "confidence": 0.8,
        }
        res = classify_ask_intent("Mera paisa kab badhega?", client=_client(payload))
        self.assertEqual(res["domain"], "finance")
        self.assertIsNone(res["mr_archetype"])

    def test_relationship_domain_defaults_archetype_when_missing(self):
        payload = {
            "domain": "marriage",
            "is_timing": False,
            "is_decision": False,
            "wants_explain": False,
            "mr_archetype": None,
            "confidence": 0.75,
        }
        res = classify_ask_intent("Meri shaadi kaisi rahegi?", client=_client(payload))
        self.assertEqual(res["mr_archetype"], "general_mr")

    def test_invalid_domain_falls_back_to_general(self):
        payload = {
            "domain": "spirituality",  # not in DOMAINS
            "is_timing": False,
            "mr_archetype": "loyalty_trust",
            "confidence": 0.9,
        }
        res = classify_ask_intent("random", client=_client(payload))
        self.assertEqual(res["domain"], "general")
        self.assertIsNone(res["mr_archetype"])

    def test_low_confidence_marked(self):
        payload = {
            "domain": "career",
            "is_timing": False,
            "mr_archetype": None,
            "confidence": 0.3,
        }
        res = classify_ask_intent("kuch to hoga", client=_client(payload))
        self.assertEqual(res["source"], "llm_low_conf")

    def test_client_error_returns_safe_fallback(self):
        res = classify_ask_intent(
            "Meri shaadi kab hogi?",
            client=_client({}, raise_exc=RuntimeError("boom")),
        )
        self.assertEqual(res["source"], "llm_error")
        self.assertEqual(res["domain"], "general")
        self.assertIsNone(res["mr_archetype"])

    def test_empty_question_unavailable(self):
        res = classify_ask_intent("   ", client=_client({}))
        self.assertEqual(res["source"], "llm_unavailable")


class EngineArchetypeOverrideTests(unittest.TestCase):
    def test_regex_default_when_no_override(self):
        # Sanity: regex routes this to general_mr (flag-off behaviour).
        q = "kya shaadi achhi hogi?"
        self.assertEqual(classify_mr_archetype(q), "general_mr")
        res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        self.assertEqual(res.archetype, "general_mr")

    def test_archetype_override_wins_over_regex(self):
        # Same question regex calls general_mr, but an injected archetype
        # (as the LLM-first path would provide) must take precedence.
        q = "kya shaadi achhi hogi?"
        res = run_mr_static_engine(
            SAMPLE_KUNDLI, q, wants_explain=False, archetype="loyalty_trust"
        )
        self.assertEqual(res.archetype, "loyalty_trust")

    def test_blank_override_falls_back_to_regex(self):
        q = "kya wo loyal hai ya dhokha karega?"
        res = run_mr_static_engine(
            SAMPLE_KUNDLI, q, wants_explain=False, archetype="   "
        )
        self.assertEqual(res.archetype, "loyalty_trust")


if __name__ == "__main__":
    unittest.main()

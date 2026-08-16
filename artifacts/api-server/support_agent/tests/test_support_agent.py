"""Support Agent — AI answers; leak guard stays on."""
from __future__ import annotations

import re
import unittest

from support_agent.agent import run
from support_agent.response_guard import guard


class SupportAgentTests(unittest.TestCase):
    def test_guard_strips_keys(self) -> None:
        text, leaked = guard("Use api_key abc and flask_app", "en")
        self.assertTrue(leaked)
        self.assertNotRegex(text, re.compile(r"api_key|flask_app", re.I))

    def test_guard_keeps_ai_report_answer(self) -> None:
        text, leaked = guard(
            "Love Reality Pro PDF is not an instant AI report. Our expert writes it after you pay.",
            "en",
        )
        self.assertFalse(leaked)
        self.assertIn("expert", text.lower())

    def test_ai_answers_relationship_report(self) -> None:
        import support_agent.agent as sag

        orig = sag._llm

        def fake_llm(*_a, **_k):
            return {
                "escalate": False,
                "reply": (
                    "Love Reality Pro PDF is written by our expert after you pay — "
                    "it is not an instant AI PDF. Open Life Map → Relationship."
                ),
                "source": "llm",
            }

        sag._llm = fake_llm  # type: ignore[method-assign]
        try:
            r = run("tell me is the realationship report a ai report", lang="en")
            self.assertFalse(r["escalate"])
            self.assertIn("expert", r["reply"].lower())
            self.assertEqual(r["source"], "llm")
        finally:
            sag._llm = orig

    def test_no_ai_falls_back_to_handoff(self) -> None:
        import support_agent.agent as sag

        orig = sag._llm
        sag._llm = lambda *_a, **_k: None  # type: ignore[method-assign]
        try:
            r = run("qwerty asdf zxcvb plugh", lang="en")
            self.assertTrue(r["escalate"])
            self.assertEqual(r["source"], "ai_unavailable")
            self.assertEqual(r["agent_state"], "waiting_for_human")
        finally:
            sag._llm = orig

    def test_knowledge_base_loads(self) -> None:
        from support_agent.knowledge import ALLOWED_KNOWLEDGE

        self.assertIn("Numerology", ALLOWED_KNOWLEDGE)
        self.assertIn("NO wallet", ALLOWED_KNOWLEDGE)

    def test_wallet_tool_has_no_wallet(self) -> None:
        from support_agent.tools import get_wallet_status

        w = get_wallet_status(None)
        self.assertTrue(w.get("ok"))
        self.assertFalse(w.get("has_wallet"))

    def test_string_false_does_not_escalate(self) -> None:
        import support_agent.agent as sag

        orig = sag._llm
        sag._llm = lambda *_a, **_k: {  # type: ignore[method-assign]
            "escalate": "false",
            "reply": "No wallet. Check Help → Transactions.",
            "source": "llm",
        }
        try:
            r = run("transaction not in wallet", lang="en")
            self.assertFalse(r["escalate"])
            self.assertIn("wallet", r["reply"].lower())
        finally:
            sag._llm = orig


if __name__ == "__main__":
    unittest.main()

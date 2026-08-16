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
        finally:
            sag._llm = orig


if __name__ == "__main__":
    unittest.main()

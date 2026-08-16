"""Help & Support — AI agent + leak scrub."""
from __future__ import annotations

import re
import unittest

import support_ai as sai
import support_agent.agent as sag


class SupportAiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_llm = sag._llm

    def tearDown(self) -> None:
        sag._llm = self._orig_llm

    def _fake(self, reply: str, escalate: bool = False):
        sag._llm = lambda *_a, **_k: {  # type: ignore[method-assign]
            "escalate": escalate,
            "reply": reply,
            "source": "llm",
        }

    def test_ai_relationship_report(self) -> None:
        self._fake(
            "Love Reality Pro PDF is written by our expert after you pay — "
            "it is not an instant AI PDF."
        )
        r = sai.answer_support(
            "tell me is the realationship report a ai report", lang="en"
        )
        self.assertFalse(r["escalate"])
        self.assertIn("expert", r["reply"].lower())
        self.assertEqual(r["source"], "llm")

    def test_refund_escalates_when_ai_says_so(self) -> None:
        self._fake(
            "A team member will join this chat shortly — please wait.",
            escalate=True,
        )
        r = sai.answer_support("Refund chahiye paise wapas karo", lang="hn")
        self.assertTrue(r["escalate"])

    def test_no_ai_handoff(self) -> None:
        sag._llm = lambda *_a, **_k: None  # type: ignore[method-assign]
        r = sai.answer_support("qwerty asdf zxcvb plugh", lang="hn")
        self.assertTrue(r["escalate"])
        self.assertNotRegex(r["reply"], r"telegram|api_key", re.I)

    def test_internal_data_banned(self) -> None:
        out = sai.scrub_customer_reply(
            "Open flask_app and send TELEGRAM_BOT_TOKEN with api_key", "hn"
        )
        self.assertNotRegex(out, r"api_key|telegram|flask_app", re.I)
        self.assertRegex(out, r"wait|support", re.I)

    def test_account_card_customer_safe(self) -> None:
        from types import SimpleNamespace

        from support_account import build_customer_facts

        u = SimpleNamespace(
            id=109,
            name="Ravi",
            cosmo_user_id="COSMO109",
            phone="+919000001109",
            plan="free",
            plan_expiry=None,
            ask_v1_questions_left=4,
            ask_v1_free_questions_used=3,
            ask_v1_bonus_questions=0,
        )
        card = build_customer_facts(u)["card"]
        self.assertIn("COSMO109", card)
        self.assertIn("Ravi", card)
        self.assertNotRegex(card, r"api_key|is_admin|telegram|openai", re.I)


if __name__ == "__main__":
    unittest.main()

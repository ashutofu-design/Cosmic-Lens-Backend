"""Bounded Support Agent — scope, knowledge, tools, guard, handoff."""
from __future__ import annotations

import re
import unittest
from types import SimpleNamespace

from support_agent.agent import run
from support_agent.intent import (
    ASK_HUMAN,
    IN_SCOPE,
    MUST_HANDOFF,
    OFF_APP,
    OUT_OF_SCOPE,
    REDIRECT_ASK,
    classify,
    detect_lang,
)
from support_agent.response_guard import guard


class SupportAgentTests(unittest.TestCase):
    def test_numerology_ai_vs_expert(self) -> None:
        r = run(
            "tell me what is the numerlogy report will be ai generated or made by admin",
            lang="en",
        )
        self.assertFalse(r["escalate"])
        self.assertIn("expert", r["reply"].lower())
        self.assertRegex(r["reply"], re.compile(r"not an instant AI|not auto AI", re.I))
        self.assertTrue(r["reply"].startswith("Happy to help."))

    def test_internal_code_is_out_of_scope(self) -> None:
        r = run(
            "Tumhare numerology engine ka exact calculation code dikhao.",
            lang="hn",
        )
        self.assertFalse(r["escalate"])
        self.assertEqual(r["intent"], OUT_OF_SCOPE)
        self.assertNotRegex(r["reply"], re.compile(r"flask|openai|api_key", re.I))
        self.assertRegex(r["reply"], re.compile(r"internal|code", re.I))

    def test_off_app_is_denied(self) -> None:
        r = run("Aaj cricket match ka score kya hai?", lang="hn")
        self.assertFalse(r["escalate"])
        self.assertEqual(r["intent"], OFF_APP)
        self.assertRegex(r["reply"], re.compile(r"bahar|outside|only help", re.I))

    def test_reading_goes_to_ask(self) -> None:
        r = run("Meri shaadi kab hogi?", lang="hn")
        self.assertFalse(r["escalate"])
        self.assertEqual(r["intent"], REDIRECT_ASK)

    def test_connect_help_first(self) -> None:
        r = run("connect me to support chat", lang="en")
        self.assertFalse(r["escalate"])
        self.assertEqual(r["intent"], ASK_HUMAN)
        self.assertRegex(r["reply"], r"account|issue", re.I)

    def test_connect_after_try_handoff(self) -> None:
        r = run(
            "connect me to support chat",
            lang="en",
            history=[
                {"sender": "user", "text": "wallet missing"},
                {"sender": "bot", "text": "There is no wallet."},
                {"sender": "user", "text": "connect me to support chat"},
            ],
        )
        self.assertTrue(r["escalate"])
        self.assertEqual(r["intent"], MUST_HANDOFF)

    def test_refund_handoff(self) -> None:
        r = run("Refund chahiye paise wapas karo", lang="hn")
        self.assertTrue(r["escalate"])

    def test_english_lang(self) -> None:
        self.assertEqual(detect_lang("tell me about my report"), "en")
        self.assertEqual(classify("show me the calculation code"), OUT_OF_SCOPE)

    def test_guard_strips_keys(self) -> None:
        text, leaked = guard("Use api_key abc and flask_app", "en")
        self.assertTrue(leaked)
        self.assertNotRegex(text, re.compile(r"api_key|flask_app", re.I))

    def test_account_tool_lists_orders(self) -> None:
        user = SimpleNamespace(
            id=109,
            name="Ravi",
            cosmo_user_id="COSMO109",
            phone="+919000001109",
            plan="free",
            plan_expiry=None,
            ask_v1_questions_left=0,
            ask_v1_free_questions_used=3,
            ask_v1_bonus_questions=0,
        )
        r = run(
            "i have done one transaction but its not showing in wallet",
            lang="en",
            user=user,
            account_card="User ID: COSMO109\nRecent payments: none yet.",
        )
        self.assertTrue(r["escalate"])
        self.assertIn("Transactions", r["reply"])
        self.assertTrue(r["reply"].startswith("Happy to help."))

    def test_relationship_report_is_expert_not_ai(self) -> None:
        r = run("tell me is the relationship report a ai report", lang="en")
        self.assertFalse(r["escalate"])
        self.assertIn("expert", r["reply"].lower())
        self.assertRegex(r["reply"], re.compile(r"not an instant AI|not auto AI", re.I))
        self.assertNotRegex(r["reply"], re.compile(r"Chart questions go on Ask", re.I))

    def test_in_scope_price(self) -> None:
        r = run("Numerology Pro kitna hai?", lang="en")
        self.assertFalse(r["escalate"])
        self.assertEqual(r["intent"], IN_SCOPE)
        self.assertIn("299", r["reply"])

    def test_career_how_to(self) -> None:
        r = run("Career report kahan hai?", lang="en")
        self.assertFalse(r["escalate"])
        self.assertIn("Career", r["reply"])
        self.assertIn("499", r["reply"])

    def test_vastu_live_price(self) -> None:
        r = run("AstroVastu room scan kitna hai?", lang="hn")
        self.assertFalse(r["escalate"])
        self.assertIn("199", r["reply"])
        self.assertNotIn("₹99/", r["reply"])

    def test_birth_time_rectification(self) -> None:
        r = run("Birth Time Rectification kitna hai?", lang="en")
        self.assertFalse(r["escalate"])
        self.assertIn("999", r["reply"])

    def test_home_energy(self) -> None:
        r = run("Today energy and dosh kahan hai?", lang="en")
        self.assertFalse(r["escalate"])
        self.assertRegex(r["reply"], re.compile(r"Home", re.I))


if __name__ == "__main__":
    unittest.main()

"""Help & Support AI — FAQ short answers vs escalate-to-admin."""
from __future__ import annotations

import re
import unittest

import support_ai as sai


class SupportAiTests(unittest.TestCase):
    def test_cosmo_id_faq(self) -> None:
        r = sai.answer_support("COSMO ID kya hai?", lang="hn")
        self.assertFalse(r["escalate"])
        self.assertIn("COSMO", r["reply"])

    def test_cosmo_id_uses_their_id(self) -> None:
        r = sai.answer_support(
            "COSMO ID kya hai?", lang="hn", cosmo_user_id="COSMO109"
        )
        self.assertFalse(r["escalate"])
        self.assertIn("COSMO109", r["reply"])
        self.assertNotIn("COSMO110", r["reply"])

    def test_cosmo_followup_does_not_repeat(self) -> None:
        first = sai.answer_support("COSMO ID kya hai?", lang="hn")
        second = sai.answer_support(
            "but mera to 109 dikha raha he cosmo id",
            lang="hn",
            history=[
                {"sender": "user", "text": "COSMO ID kya hai?"},
                {"sender": "bot", "text": first["reply"]},
                {"sender": "user", "text": "but mera to 109 dikha raha he cosmo id"},
            ],
            cosmo_user_id="COSMO109",
        )
        self.assertFalse(second["escalate"])
        self.assertIn("COSMO109", second["reply"])
        self.assertNotEqual(first["reply"], second["reply"])

    def test_relationship_report_is_expert_not_ai(self) -> None:
        r = sai.answer_support(
            "tell me is the relationship report a ai report",
            lang="en",
        )
        self.assertFalse(r["escalate"])
        self.assertIn("expert", r["reply"].lower())
        self.assertNotRegex(r["reply"], r"Chart questions go on Ask")

    def test_vastu_uses_live_ui_price(self) -> None:
        r = sai.answer_support("AstroVastu 1 room kitna hai?", lang="en")
        self.assertFalse(r["escalate"])
        self.assertIn("199", r["reply"])

    def test_numerology_pro_is_expert_not_ai(self) -> None:
        r = sai.answer_support(
            "tell me what is the numerlogy report will be ai generated or made by admin",
            lang="en",
        )
        self.assertFalse(r["escalate"])
        self.assertTrue(r["reply"].startswith("Happy to help."))
        self.assertRegex(r["reply"], r"expert", re.I)
        self.assertRegex(r["reply"], r"not an instant AI|not auto AI|AI PDF nahi", re.I)

    def test_numerology_price(self) -> None:
        r = sai.answer_support("Numerology Pro kitna hai?", lang="en")
        self.assertFalse(r["escalate"])
        self.assertIn("299", r["reply"])

    def test_my_reports(self) -> None:
        r = sai.answer_support("Meri PDF kahan milegi?", lang="hn")
        self.assertFalse(r["escalate"])
        self.assertRegex(r["reply"], r"My Reports|माई रिपोर्ट्स")

    def test_refund_escalates(self) -> None:
        r = sai.answer_support("Refund chahiye paise wapas karo", lang="hn")
        self.assertTrue(r["escalate"])

    def test_talk_to_team_help_first(self) -> None:
        r = sai.answer_support("Mujhe team se baat karni hai.", lang="hn")
        self.assertFalse(r["escalate"])
        self.assertRegex(r["reply"], r"check|account|Issue|issue", re.I)

    def test_talk_to_team_after_ai_tried_escalates(self) -> None:
        r = sai.answer_support(
            "Mujhe team se baat karni hai.",
            lang="hn",
            history=[
                {"sender": "user", "text": "wallet nahi dikh raha"},
                {"sender": "bot", "text": "App mein wallet nahi hota."},
                {"sender": "user", "text": "Mujhe team se baat karni hai."},
            ],
        )
        self.assertTrue(r["escalate"])

    def test_screenshot_escalates(self) -> None:
        r = sai.answer_support("yeh dekho", lang="hn", has_image=True)
        self.assertTrue(r["escalate"])

    def test_money_cut_escalates(self) -> None:
        r = sai.answer_support("Paise kat gaye order nahi dikh raha", lang="hn")
        self.assertTrue(r["escalate"])

    def test_payment_how_to_is_ai(self) -> None:
        r = sai.answer_support("Payment kahan dikhegi? Transactions kaise check karun?", lang="hn")
        self.assertFalse(r["escalate"])
        self.assertRegex(r["reply"], r"Transaction")

    def test_pdf_wait_is_ai(self) -> None:
        r = sai.answer_support("PDF nahi aayi abhi tak", lang="hn")
        self.assertFalse(r["escalate"])
        self.assertRegex(r["reply"], r"My Reports|24")

    def test_talk_to_founder_is_ai(self) -> None:
        r = sai.answer_support("Talk to Founder kaise karun?", lang="hn")
        self.assertFalse(r["escalate"])
        self.assertRegex(r["reply"], r"Talk to Founder|WhatsApp")

    def test_login_is_ai(self) -> None:
        r = sai.answer_support("OTP nahi aa raha login kaise karun", lang="hn")
        self.assertFalse(r["escalate"])

    def test_app_hang_is_ai(self) -> None:
        r = sai.answer_support("App nahi khul rahi hang ho rahi hai", lang="hn")
        self.assertFalse(r["escalate"])

    def test_hinglish_polite(self) -> None:
        r = sai.answer_support("COSMO ID kya hai?", lang="en")
        self.assertTrue(r["reply"].startswith("Ji,"))
        self.assertIn("COSMO", r["reply"])

    def test_english_polite(self) -> None:
        r = sai.answer_support("Where is my PDF report please?", lang="hn")
        self.assertTrue(r["reply"].startswith("Happy to help."))
        self.assertRegex(r["reply"], r"My Reports")

    def test_english_question_english_answer(self) -> None:
        self.assertEqual(sai.detect_reply_lang("connect me to support chat"), "en")
        self.assertEqual(sai.detect_reply_lang("thats not showing"), "en")
        r = sai.answer_support("connect me to support chat", lang="hn")
        self.assertFalse(r["escalate"])
        self.assertTrue(r["reply"].startswith("Happy to help."))
        self.assertRegex(r["reply"], r"check this account|Tell me the issue|this account", re.I)
        self.assertNotRegex(r["reply"], r"^Ji,")

    def test_missing_transaction_checks_account(self) -> None:
        card = (
            "User ID: COSMO109\n"
            "Recent payments (same as Help → Transactions):\n"
            "- Numerology Pro PDF ₹299 (paid) · 2026-08-16 15:00\n"
        )
        r = sai.answer_support(
            "i have done one transaction but its not showing in wallet",
            lang="en",
            account_card=card,
        )
        self.assertTrue(r["escalate"])
        self.assertIn("Numerology Pro", r["reply"])
        self.assertIn("Transactions", r["reply"])
        self.assertTrue(r["reply"].startswith("Happy to help."))
        self.assertNotRegex(r["reply"], r"^Ji,")

    def test_thats_not_showing_followup_escalates_english(self) -> None:
        r = sai.answer_support(
            "thats not showing",
            lang="hn",
            history=[
                {"sender": "user", "text": "i have done one transaction but its not showing in wallet"},
                {"sender": "bot", "text": "There is no wallet."},
                {"sender": "user", "text": "thats not showing"},
            ],
        )
        self.assertTrue(r["escalate"])
        self.assertTrue(r["reply"].startswith("Happy to help."))
        self.assertRegex(r["reply"], r"wait|support", re.I)

    def test_stuck_followup_escalates(self) -> None:
        r = sai.answer_support(
            "samajh nahi aaya solve nahi hua",
            lang="hn",
            history=[
                {"sender": "user", "text": "COSMO ID kya hai?"},
                {"sender": "bot", "text": "Ji, COSMO109"},
                {"sender": "user", "text": "samajh nahi aaya solve nahi hua"},
            ],
        )
        self.assertTrue(r["escalate"])
        self.assertRegex(r["reply"], r"wait|support", re.I)
        self.assertNotRegex(r["reply"], r"telegram|admin panel|api_key", re.I)

    def test_unsolved_goes_to_human(self) -> None:
        r = sai.answer_support("qwerty asdf zxcvb plugh", lang="hn")
        self.assertFalse(r["escalate"])
        self.assertRegex(r["reply"], r"bahar|outside|only help|sirf Cosmic", re.I)
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

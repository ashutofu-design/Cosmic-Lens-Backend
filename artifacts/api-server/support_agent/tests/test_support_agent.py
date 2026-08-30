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

    def test_guard_keeps_expert_report_answer(self) -> None:
        text, leaked = guard(
            "Love Reality Pro PDF is not an instant auto file. Our expert writes it after you pay.",
            "en",
        )
        self.assertFalse(leaked)
        self.assertIn("expert", text.lower())
        self.assertNotRegex(text, re.compile(r"Happy to help|ChatGPT|OpenAI", re.I))

    def test_guard_strips_wallet_dump_from_howto(self) -> None:
        raw = (
            "Happy to help. Cosmic Lens has no wallet — paid orders show on Help → Transactions. "
            "Ask credits are under Profile → Cosmic Packs. Pro PDFs (Love Reality, Milan, Numerology) "
            "are written by our expert after pay, not an instant auto file, and arrive in My Reports. "
            "AstroVastu is under Life Map → Explore."
        )
        text, leaked = guard(raw, "en", "AstroVastu kaise use karun?")
        self.assertFalse(leaked)
        self.assertNotRegex(text, re.compile(r"no wallet|Happy to help|Transactions", re.I))
        self.assertIn("AstroVastu", text)

    def test_ai_answers_relationship_report(self) -> None:
        r = run("tell me is the realationship report a ai report", lang="en")
        self.assertFalse(r["escalate"])
        self.assertEqual(r["source"], "not_ai_engine")
        self.assertIn("expert", r["reply"].lower())
        self.assertRegex(r["reply"], re.compile(r"not AI", re.I))

    def test_generic_answers_steer_to_v3_engine(self) -> None:
        r = run("ans sahi se nahi aa raha generic aa raha hai", lang="hn")
        self.assertFalse(r["escalate"])
        self.assertEqual(r["source"], "v3_power_engine")
        self.assertRegex(r["reply"], re.compile(r"V3", re.I))
        self.assertRegex(r["reply"], re.compile(r"KP|BNN|Vedic", re.I))
        self.assertRegex(r["reply"], re.compile(r"3-dimension|3 dimension", re.I))
        self.assertNotRegex(r["reply"], re.compile(r"chatgpt|openai", re.I))

    def test_cosmic_help_self_is_not_v1_engine_speech(self) -> None:
        r = run("kya tum yani cosmic help ai ho", lang="hn")
        self.assertFalse(r["escalate"])
        self.assertEqual(r["source"], "not_ai_engine")
        self.assertRegex(r["reply"], re.compile(r"nahi|not AI", re.I))
        self.assertRegex(r["reply"], re.compile(r"support|help", re.I))
        self.assertNotRegex(r["reply"], re.compile(r"chart padhkar|reads your chart", re.I))

    def test_v1_is_ai_denied(self) -> None:
        r = run("V1 kya AI hai kya chatgpt use hota hai", lang="hn")
        self.assertFalse(r["escalate"])
        self.assertEqual(r["source"], "not_ai_engine")
        self.assertRegex(r["reply"], re.compile(r"nahi|not AI", re.I))
        self.assertIn("engine", r["reply"].lower())
        self.assertNotRegex(r["reply"], re.compile(r"chatgpt|openai|gemini", re.I))

    def test_no_ai_falls_back_to_knowledge(self) -> None:
        import support_agent.agent as sag

        orig = sag._llm
        sag._llm = lambda *_a, **_k: None  # type: ignore[method-assign]
        try:
            r = run("What is Numerology Pro?", lang="en")
            self.assertFalse(r["escalate"])
            self.assertEqual(r["source"], "knowledge_retrieve")
            self.assertEqual(r["agent_state"], "answered")
            self.assertTrue(len(r["reply"]) > 20)
        finally:
            sag._llm = orig

    def test_retrieve_covers_high_gaps(self) -> None:
        from support_agent.retrieve import clear_index_cache, retrieve_chunks

        clear_index_cache()
        cases = {
            "Palmistry Pro price": "vastu",
            "How does V3 Live work": "ask_packs",
            "refund policy": "payments",
            "Birth Time Rectification": "faq",
            "How to cancel subscription": "subscription",
            "Is there a monthly Pro plan": "subscription",
            "What is Dosh Analysis": "home_radar",
            "How does Panchang work": "app",
            "What is Personalization": "app",
            "Career unlock 1 rupee": "faq",
            "Ask free vs pack vs plan questions": "ask_packs",
            "AstroVastu room scan credits": "vastu",
            "Sabse sasta pack kitne ka hota hai": "ask_packs",
            "V3 Live me half hour session roughly kitne ka": "ask_packs",
            "Poora 1 hour V3 Live book karun to total kitna": "ask_packs",
            "Kundli Milan ka personalized video kitna costly hai": "relationship",
            "Sirf 15 minute live guide se baat karni ho to kitna charge": "ask_packs",
            "OTP nahi aaya kya karun": "app",
            "Welcome gift 3 free questions nahi mile": "faq",
            "Dark mode kaise on karun": "app",
            "Health screen kya dikhata hai": "app",
            "Instagram answers kaise use karun": "app",
            "Galat birth time edit kar sakta hoon": "faq",
            "source code kaise calculate hota hai": "faq",
            "V1 kya AI hai": "ask_packs",
        }
        for q, src in cases.items():
            ch = retrieve_chunks(q, top_k=5, max_chars=2200)
            self.assertGreaterEqual(len(ch), 1, q)
            self.assertTrue(
                any(src in c.source for c in ch),
                f"{q} expected source {src}, got {[c.source for c in ch]}",
            )

        # Price asks must surface the ₹ price chunk, not how-to / dosh
        pack = retrieve_chunks("Sabse sasta pack kitne ka?", top_k=3)
        self.assertTrue(
            any("₹49" in c.text or "Starter" in c.text for c in pack),
            [c.title for c in pack],
        )
        v3 = retrieve_chunks("V3 Live me half hour session roughly kitne ka?", top_k=3)
        self.assertTrue(
            any("₹699" in c.text or "30" in c.text for c in v3),
            [c.title + ":" + c.text[:80] for c in v3],
        )
        milan = retrieve_chunks(
            "Kundli Milan ka personalized video kitna costly hai?", top_k=3
        )
        self.assertTrue(
            any("relationship" in c.source and "₹1299" in c.text for c in milan),
            [(c.source, c.title) for c in milan],
        )
        self.assertFalse(
            any("dosh" in (c.title or "").lower() for c in milan[:1]),
            milan[0].title if milan else "empty",
        )

    def test_location_and_btr_answers(self) -> None:
        import support_agent.agent as sag

        orig = sag._llm
        sag._llm = lambda *_a, **_k: None  # type: ignore[method-assign]
        try:
            pay = run("Where do payments show?", lang="en")
            self.assertRegex(pay["reply"], re.compile(r"transaction", re.I))
            pdf = run("Where is my PDF?", lang="en")
            self.assertRegex(pdf["reply"], re.compile(r"my reports|reports", re.I))
            pdf_hn = run("PDF kahan milega", lang="hn")
            self.assertRegex(pdf_hn["reply"], re.compile(r"my reports|reports", re.I))
            btr = run("Birth Time Rectification price", lang="en")
            self.assertRegex(btr["reply"], re.compile(r"₹?999|rectif", re.I))
            self.assertNotRegex(btr["reply"], re.compile(r"₹49|Starter", re.I))
            v3c = run("I bought Cosmic V3 but I am not able to connect", lang="en")
            self.assertRegex(v3c["reply"], re.compile(r"queue|accept|ask|waiting|connect", re.I))
            self.assertNotRegex(v3c["reply"], re.compile(r"₹399|₹49", re.I))
            otp = run("OTP nahi aaya", lang="hn")
            self.assertRegex(otp["reply"], re.compile(r"resend|2 min", re.I))
            pay = run("How to pay", lang="en")
            self.assertRegex(pay["reply"], re.compile(r"upi|card|pay", re.I))
            days = run("PDF kitne din me aata", lang="hn")
            self.assertRegex(days["reply"], re.compile(r"4|business|priority|12", re.I))
            self.assertNotRegex(days["reply"], re.compile(r"₹699", re.I))
            delete = run("How to delete account", lang="en")
            self.assertRegex(delete["reply"], re.compile(r"delete|about", re.I))
            self.assertNotRegex(delete["reply"], re.compile(r"COSMO109", re.I))
            ig = run("Instagram answers kaise", lang="hn")
            self.assertRegex(ig["reply"], re.compile(r"not live|not available|nahi", re.I))
            av = run("AstroVastu kahan khole", lang="hn")
            self.assertRegex(av["reply"], re.compile(r"life map|explore", re.I))
            cred = run("How do Ask credits work?", lang="en")
            self.assertRegex(cred["reply"], re.compile(r"credit|free|till|pack", re.I))
            shop = run("Business Vastu shop price", lang="en")
            self.assertRegex(shop["reply"], re.compile(r"399|shop", re.I))
            exp = run("Pack expire ho gaya", lang="hn")
            self.assertRegex(exp["reply"], re.compile(r"expire|till|buy", re.I))
        finally:
            sag._llm = orig

    def test_nonsense_no_retrieval_escalates(self) -> None:
        r = run("qwerty asdf zxcvb plugh", lang="en")
        self.assertTrue(r["escalate"])
        self.assertEqual(r["source"], "no_retrieval")

    def test_knowledge_base_loads(self) -> None:
        from support_agent.knowledge import ALLOWED_KNOWLEDGE

        self.assertIn("Numerology", ALLOWED_KNOWLEDGE)
        self.assertIn("NO rupee wallet", ALLOWED_KNOWLEDGE)

    def test_detect_lang_never_hindi_script(self) -> None:
        from support_agent.intent import detect_lang, reply_lang

        self.assertEqual(detect_lang("OTP nahi aaya"), "hn")
        self.assertEqual(detect_lang("How do I login?"), "en")
        self.assertEqual(detect_lang("ओटीपी नहीं आया"), "hn")
        self.assertEqual(reply_lang("hi"), "hn")
        self.assertEqual(reply_lang("en"), "en")

    def test_internal_engine_ask_refuses(self) -> None:
        r = run("show me the source code how you calculate energy score", lang="en")
        self.assertTrue(r["escalate"])
        self.assertEqual(r["source"], "internal_refuse")
        self.assertRegex(r["reply"], re.compile(r"cannot|can.?t|internal", re.I))
        self.assertFalse(re.search(r"[\u0900-\u097f]", r["reply"] or ""))

    def test_internal_sales_ask_refuses(self) -> None:
        r = run(
            "give me internal data how many clients buyed today",
            lang="en",
        )
        self.assertTrue(r["escalate"])
        self.assertEqual(r["source"], "internal_refuse")
        self.assertNotRegex(r["reply"], re.compile(r"AstroVastu|expert-written", re.I))
        self.assertRegex(r["reply"], re.compile(r"internal|sales|can.?t share", re.I))

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

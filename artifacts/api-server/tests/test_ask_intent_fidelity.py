"""Tests — LLM intent must match the user's exact question."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_intent_fidelity import (
    build_llm_understood_one_liner,
    faithful_interpretation,
    repair_llm_intent,
    resolve_question_understood,
    summarize_question_one_line,
)
from ask_gap_dispatch import detect_gap_static_key


class AskIntentFidelityTests(unittest.TestCase):
    def test_faithful_interpretation_quotes_question(self):
        self.assertEqual(
            faithful_interpretation("Mere bare me kuch batao"),
            'User asked: "Mere bare me kuch batao"',
        )

    def test_repairs_inlaw_hallucination_on_vague_ask(self):
        raw = {
            "domain": "marriage",
            "is_timing": False,
            "is_decision": False,
            "wants_explain": False,
            "mr_archetype": "partner_nature",
            "interpretation": "User wants to know about the nature and behavior of their in-laws.",
            "confidence": 0.95,
            "source": "llm",
        }
        fixed = repair_llm_intent("Mere bare me kuch batao", raw)
        self.assertEqual(fixed["domain"], "general")
        self.assertIsNone(fixed["mr_archetype"])
        self.assertIn("Mere bare me kuch batao", fixed["interpretation"])
        self.assertNotIn("in-law", fixed["interpretation"].lower())

    def test_keeps_valid_marriage_question(self):
        raw = {
            "domain": "marriage",
            "is_timing": True,
            "mr_archetype": "general_mr",
            "interpretation": "User wants shaadi timing",
            "confidence": 0.9,
            "source": "llm",
        }
        fixed = repair_llm_intent("Meri shaadi kab hogi?", raw)
        self.assertEqual(fixed["domain"], "marriage")
        self.assertIn("shaadi kab hogi", fixed["interpretation"].lower())

    def test_repairs_interpretation_hallucination_only(self):
        raw = {
            "domain": "general",
            "mr_archetype": None,
            "interpretation": "User wants to know about in-laws.",
            "confidence": 0.8,
            "source": "llm",
        }
        fixed = repair_llm_intent("Career kaisi rahegi?", raw)
        self.assertIn("Career kaisi rahegi", fixed["interpretation"])
        self.assertNotIn("in-law", fixed["interpretation"].lower())

    def test_upgrades_finance_from_paisa_question(self):
        raw = {
            "domain": "general",
            "mr_archetype": None,
            "interpretation": "User asked something",
            "confidence": 0.9,
            "source": "llm",
        }
        fixed = repair_llm_intent("Mere paas paisa kitna hoga", raw)
        self.assertEqual(fixed["domain"], "finance")
        self.assertEqual(fixed.get("finance_archetype"), "wealth_potential")
        self.assertTrue(str(fixed.get("understanding_line") or "").startswith("Yes"))

    def test_understanding_line_includes_question_summary(self):
        li = {
            "domain": "finance",
            "finance_archetype": "loss_reasons",
            "confidence": 0.9,
            "source": "llm",
            "question_summary": "Dhan kamane mein dikkat kyun aati hai",
        }
        line = build_llm_understood_one_liner(
            "mujhse dhan karne me itni dikkat kyun aati he",
            li,
            intent_source="llm",
        )
        self.assertIn("Dhan kamane", line)
        self.assertIn("finance", line.lower())

    def test_long_question_regex_summary_not_empty(self):
        long_q = (
            "Mere career me promotion nahi mil raha, boss supportive nahi, "
            "salary bhi kam hai, kya main job change karun ya business shuru karun, "
            "aur shaadi ke baad bhi paisa bach nahi pata — kya karna chahiye?"
        )
        summary = summarize_question_one_line(long_q)
        self.assertGreater(len(summary), 20)
        self.assertIn("career", summary.lower())

    def test_dhan_question_not_spiritual_gap(self):
        q = "mujhse dhan karne me itni dikkat kyun aati he"
        self.assertNotEqual(detect_gap_static_key(q), "spiritual")

    def test_finance_engine_required_still_understood_yes(self):
        li = {
            "domain": "finance",
            "finance_archetype": "wealth_potential",
            "confidence": 0.95,
            "source": "llm",
        }
        self.assertEqual(
            resolve_question_understood(
                "mere paas paisa kitna hoga",
                li,
                skip_reason="engine_required_no_direct_llm",
                intent_source="llm",
            ),
            "yes",
        )

    def test_gibberish_not_understood(self):
        self.assertEqual(
            resolve_question_understood("asdf qwer zx", {"domain": "general", "confidence": 0.2, "source": "llm"}),
            "no",
        )

    def test_love_live_timing_understood_with_engine(self):
        q = "mera love live kab shuru hoga"
        li = {
            "domain": "love",
            "mr_archetype": "dating_courtship",
            "routed_archetype": "dating_courtship",
            "confidence": 1.0,
            "source": "llm",
            "question_summary": (
                "User apne love life ke shuru hone ka samay jaanna chahta hai.\n"
                "Focus love life ke starting point par hai."
            ),
        }
        self.assertEqual(
            resolve_question_understood(
                q,
                li,
                intent_source="llm",
                has_engine_facts=True,
                engine_archetype="timing",
            ),
            "yes",
        )

    def test_commitment_timepass_overrides_loyalty_llm(self):
        q = (
            "Kya mera partner mujhse genuinely commitment karega "
            "ya sirf timepass kar raha hai?"
        )
        raw = {
            "domain": "love",
            "mr_archetype": "loyalty_trust",
            "is_timing": False,
            "source": "llm",
            "question_summary": (
                "User wants to know if partner is loyal and trustworthy in the relationship."
            ),
        }
        fixed = repair_llm_intent(q, raw)
        self.assertEqual(fixed.get("mr_archetype"), "commitment")
        self.assertIn(str(fixed.get("routing_override") or ""), ("commitment_classifier", "commitment_angle", "commitment_keyword_partner"))

    def test_classify_mr_archetype_commitment_timepass(self):
        from ask_mr.classifier import classify_mr_archetype

        q = "kya mera partner genuinely commitment karega ya sirf timepass kar raha hai"
        self.assertEqual(classify_mr_archetype(q), "commitment")

    def test_future_planning_routes_commitment_not_partner_nature(self):
        from ask_mr.classifier import classify_mr_archetype
        from ask_intent_fidelity import enforce_commitment_archetype_from_question

        q = "kya mere partner future ko lekar serious planning karta hai"
        self.assertEqual(classify_mr_archetype(q), "commitment")
        intent = {"domain": "love", "mr_archetype": "partner_nature", "bucket": "commitment"}
        self.assertTrue(enforce_commitment_archetype_from_question(q, intent))
        self.assertEqual(intent["mr_archetype"], "commitment")


if __name__ == "__main__":
    unittest.main()

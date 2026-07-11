from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import (
    compatibility_angle_label,
    infer_compatibility_angle,
    infer_partner_commitment_angle,
    infer_question_scope,
)
from ask_marriage_relationship_slice import is_marriage_relationship_static_question
from ask_mr.engines.general_mr import _question_intent
from ask_scope_gate import assess_ask_scope


class CompatibilityScopeAndMrTests(unittest.TestCase):
    def test_scope_gate_allows_couple_compat_questions(self):
        cases = [
            "Kya hum dono compatible hain?",
            "Kya hamare values same hain?",
            "Kya hamari life goals match karte hain?",
            "Kya hum mentally compatible hain?",
            "Kya hum emotionally compatible hain?",
            "Kya hum compromise kar payenge?",
        ]
        for q in cases:
            with self.subTest(q=q):
                self.assertTrue(assess_ask_scope(q).allowed)

    def test_scope_gate_allows_lifestyle_compatibility_no_anchor(self):
        q = "Kya lifestyle compatibility achhi hai?"
        self.assertTrue(assess_ask_scope(q).allowed)

    def test_mr_static_detection_support_and_jealousy(self):
        q_support = "Kya hum difficult situations me saath denge?"
        q_jealousy = "Kya jealousy relationship ko affect karegi?"
        q_compatible = "Kya hum dono compatible hain?"
        self.assertTrue(is_marriage_relationship_static_question(q_support))
        self.assertTrue(is_marriage_relationship_static_question(q_jealousy))
        self.assertTrue(is_marriage_relationship_static_question(q_compatible))


    def test_general_mr_intent_splits_mental_intellectual_emotional(self):
        self.assertEqual(
            _question_intent("Kya hum emotionally compatible hain?"),
            "emotional_compatibility",
        )
        self.assertEqual(
            _question_intent("Kya hum mentally compatible hain?"),
            "mental_compatibility",
        )
        self.assertEqual(
            _question_intent("Kya hum intellectually compatible hain?"),
            "intellectual_compatibility",
        )
        self.assertEqual(
            _question_intent("Kya hamari thinking match karti hai?"),
            "mental_compatibility",
        )
        self.assertEqual(
            _question_intent("Kya hamari personalities match karti hain?"),
            "quality",
        )

    def test_couple_scope_for_hamari_compat_questions(self):
        q = "Kya hamari personalities match karti hain?"
        self.assertEqual(infer_question_scope(q, {}), "couple")

    def test_compatibility_angles_are_distinct(self):
        cases = {
            "Kya hamari personalities match karti hain?": "personalities_match",
            "Kya hamari thinking match karti hai?": "thinking_match",
            "Kya hamare values same hain?": "values_match",
            "Kya hamare life goals match karte hain?": "life_goals_match",
            "Kya hamari expectations ek jaisi hain?": "expectations_match",
            "Kya hum emotionally compatible hain?": "emotional_compatibility",
            "Kya hum mentally compatible hain?": "mental_compatibility",
            "Kya hum intellectually compatible hain?": "intellectual_compatibility",
        }
        for q, expected in cases.items():
            with self.subTest(q=q):
                self.assertEqual(infer_compatibility_angle(q), expected)
                self.assertTrue(compatibility_angle_label(expected))

    def test_narrator_hint_includes_exact_angle(self):
        from ask_question_understand import narrator_intent_hint

        hint = narrator_intent_hint(
            "Kya hum mentally compatible hain?",
            {
                "question_scope": "couple",
                "question_summary": "User jaanna chahta hai dimaag ka match kaisa hai",
                "compatibility_angle": "mental_compatibility",
            },
        )
        self.assertIn("EXACT COMPATIBILITY ANGLE", hint)
        self.assertIn("Mental compatibility", hint)
        self.assertIn("do NOT answer emotional", hint)

    def test_partner_commitment_not_marriage_timing_rules(self):
        from ask_engine import process_ask

        q = "Kya mera partner commitment ke liye ready hai?"
        k = {
            "ascendant": "Sagittarius",
            "planets": [
                {"name": "Moon", "sign": "Gemini", "house": 7},
                {"name": "Mercury", "sign": "Scorpio", "house": 12},
                {"name": "Venus", "sign": "Leo", "house": 9},
                {"name": "Saturn", "sign": "Aries", "house": 5},
                {"name": "Jupiter", "sign": "Pisces", "house": 4},
                {"name": "Mars", "sign": "Sagittarius", "house": 1},
                {"name": "Sun", "sign": "Capricorn", "house": 2},
            ],
        }
        out = process_ask(q, k, "en")
        self.assertNotIn("Marriage promise exists", out.get("text") or "")
        self.assertNotIn("Next window:", out.get("text") or "")
        self.assertNotIn("transformative period", (out.get("text") or "").lower())
        self.assertIn(out.get("topic"), ("static",))

    def test_batch_sanitize_blocks_generic_rules_fallback(self):
        from ask_batch_runner import _sanitize_batch_result

        q = "Kya mera partner commitment ke liye ready hai?"
        k = {
            "ascendant": "Sagittarius",
            "planets": [
                {"name": "Moon", "sign": "Gemini", "house": 7},
                {"name": "Venus", "sign": "Leo", "house": 9},
            ],
        }
        bad = {
            "text": "Based on your current dasha and planetary positions, this is a transformative period. Stay focused on your goals.",
            "topic": "general",
            "source": "rules",
        }
        fixed = _sanitize_batch_result(q, bad, k, None, "en")
        self.assertNotEqual(fixed.get("source"), "rules")
        self.assertNotIn("transformative period", (fixed.get("text") or "").lower())

    def test_mr_static_ask_recovery_commitment(self):
        from ask_mr.static_answer import mr_static_ask_recovery
        from ask_mr.commitment_reply import format_partner_commitment_user_reply
        from ask_mr import run_mr_static_engine

        q = "Kya mera partner commitment ke liye ready hai?"
        k = {
            "ascendant": "Sagittarius",
            "planets": [
                {"name": "Moon", "sign": "Gemini", "house": 7},
                {"name": "Venus", "sign": "Leo", "house": 9},
            ],
        }
        eng = run_mr_static_engine(k, q, wants_explain=False, archetype="loyalty_trust")
        plain = format_partner_commitment_user_reply(q, eng)
        self.assertNotIn("house", plain.lower())
        self.assertIn("commitment", plain.lower())

        out = mr_static_ask_recovery(q, k, lang="en")
        self.assertIsNotNone(out)
        self.assertIn(out.get("source"), ("mr_engine_recovery", "mr_engine_then_llm"))
        text = (out.get("text") or "").lower()
        self.assertNotIn("transformative period", text)
        self.assertNotIn("5th house", text)
        self.assertNotIn("house 5 sign", text)
        self.assertNotIn("romance/trust axis", text)
        self.assertTrue(len((out.get("text") or "").strip()) > 20)
        self.assertTrue(
            any(
                w in text
                for w in ("commitment", "ready", "partner", "trust", "serious", "clear")
            )
        )

    def test_compatibility_plain_reply_no_jargon(self):
        from ask_mr.commitment_reply import format_compatibility_user_reply
        from ask_mr.engine_narrate import format_engine_rich_plain
        from ask_mr import run_mr_static_engine

        q = "Kya hum dono compatible hain"
        k = {
            "ascendant": "Sagittarius",
            "planets": [
                {"name": "Moon", "sign": "Gemini", "house": 7},
                {"name": "Venus", "sign": "Leo", "house": 9},
                {"name": "Saturn", "sign": "Aries", "house": 5},
            ],
        }
        eng = run_mr_static_engine(k, q)
        plain = format_compatibility_user_reply(q, eng)
        self.assertNotIn("house", plain.lower())
        self.assertNotIn("romance/trust axis", plain.lower())
        self.assertTrue(any(w in plain.lower() for w in ("compatib", "emotional", "mel", "bond")))

        rich = format_engine_rich_plain(q, eng, lang="hi")
        self.assertIn("मुख्य बात", rich)
        self.assertIn("क्यों", rich)
        self.assertNotIn("house 7", rich.lower())

        short = format_engine_rich_plain(q, eng, lang="hi", concise=True)
        self.assertNotIn("मुख्य बात", short)
        self.assertNotIn("---", short)
        self.assertNotIn("house 7", short.lower())
        self.assertTrue(len(short.split()) <= 120)

    def test_partner_commitment_angles_distinct(self):
        cases = {
            "Kya mera partner commitment ke liye ready hai?": "commitment_ready",
            "Kya mera partner serious relationship chahta hai?": "serious_relationship",
            "Kya mera partner casual relationship me interested hai?": "casual_relationship",
            "Kya mera partner long-term relationship chahta hai?": "long_term_intent",
            "Kya mera partner sirf time pass kar raha hai?": "time_pass",
        }
        for q, expected in cases.items():
            with self.subTest(q=q):
                self.assertEqual(infer_partner_commitment_angle(q), expected)


if __name__ == "__main__":
    unittest.main()


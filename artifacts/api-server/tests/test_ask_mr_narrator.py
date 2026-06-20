import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_mr.classifier import classify_mr_archetype
from ask_mr.narrator import build_mr_engine_narrator_system_prompt
from ask_mr import run_mr_static_engine


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


class MrNarratorTests(unittest.TestCase):
    def test_narrator_prompt_forbids_calculation(self):
        eng = run_mr_static_engine(SAMPLE_KUNDLI, "love marriage kyun?", wants_explain=True)
        payload = eng.to_narrator_payload()
        prompt = build_mr_engine_narrator_system_prompt(
            chart_text=payload,
            archetype=eng.archetype,
            word_budget=eng.word_budget,
            wants_explain=True,
        )
        self.assertIn("NOT calculating", prompt)
        self.assertIn("ENGINE FACTS", prompt)
        self.assertNotIn("Full D1 is below", prompt)
        self.assertLess(len(prompt), 2200)
        self.assertLess(len(payload), 900)

    def test_love_vs_arranged_uses_llm_not_template(self):
        eng = run_mr_static_engine(SAMPLE_KUNDLI, "love marriage ya arrange?", wants_explain=False)
        self.assertFalse(eng.skip_llm)

    def test_loyalty_commitment_routes_to_loyalty_trust(self):
        self.assertEqual(
            classify_mr_archetype("Marriage me loyalty aur commitment level kaise rahega"),
            "loyalty_trust",
        )
        self.assertEqual(
            classify_mr_archetype("meraove marriage he ya arrange"),
            "love_vs_arranged",
        )
        self.assertEqual(
            classify_mr_archetype("mera marriage hogi ya arranged?"),
            "love_vs_arranged",
        )

    def test_partner_nature_payload_maps_three_paragraphs(self):
        from ask_mr.engines.partner_nature import partner_nature_narrator_payload, run_partner_nature

        eng = run_partner_nature(SAMPLE_KUNDLI, "mera partner ka nature?", birth=None)
        payload = partner_nature_narrator_payload(eng)
        self.assertIn("PARA 1", payload)
        self.assertIn("PARA 2", payload)
        self.assertIn("PARA 3", payload)
        self.assertIn("7th house sign baseline", payload)

    def test_partner_nature_prompt_requires_three_paragraphs(self):
        from ask_mr.engines.partner_nature import partner_nature_narrator_payload, run_partner_nature

        eng = run_partner_nature(SAMPLE_KUNDLI, "partner nature?", birth=None)
        prompt = build_mr_engine_narrator_system_prompt(
            chart_text=partner_nature_narrator_payload(eng),
            archetype="partner_nature",
            is_partner_nature=True,
            word_budget=120,
        )
        self.assertIn("exactly 3 paragraphs", prompt)
        self.assertIn("PARAGRAPH 1", prompt)
        self.assertIn("BANNED hedging", prompt)


if __name__ == "__main__":
    unittest.main()

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
        eng = run_mr_static_engine(SAMPLE_KUNDLI, "love marriage ya arrange?", wants_explain=False)
        prompt = build_mr_engine_narrator_system_prompt(
            chart_text=eng.to_chart_text(question="love marriage ya arrange?"),
            archetype=eng.archetype,
            word_budget=eng.word_budget,
        )
        self.assertIn("Do NOT calculate", prompt)
        self.assertIn("ENGINE FACTS", prompt)
        self.assertNotIn("Full D1 is below", prompt)
        self.assertLess(len(prompt), 3500)

    def test_classifier_marriage_arrange_typo(self):
        self.assertEqual(
            classify_mr_archetype("meraove marriage he ya arrange"),
            "love_vs_arranged",
        )
        self.assertEqual(
            classify_mr_archetype("mera marriage hogi ya arranged?"),
            "love_vs_arranged",
        )


if __name__ == "__main__":
    unittest.main()

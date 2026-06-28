import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_property import run_property_static_engine
from ask_property.classifier import classify_property_archetype, is_property_static_question
from ask_property.property_registry import PROPERTY_ARCHETYPES, is_property_money_only_question
from ask_finance.classifier import classify_finance_archetype, is_finance_static_question


SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "ascendantDeg": 255.0,
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7, "longitude": 75.0},
        {"name": "Saturn", "sign": "Virgo", "house": 10, "longitude": 165.0},
        {"name": "Mars", "sign": "Cancer", "house": 8, "longitude": 105.0},
        {"name": "Venus", "sign": "Leo", "house": 9, "longitude": 135.0},
        {"name": "Mercury", "sign": "Aries", "house": 5, "longitude": 15.0},
        {"name": "Jupiter", "sign": "Pisces", "house": 4, "longitude": 345.0},
        {"name": "Rahu", "sign": "Aquarius", "house": 3, "longitude": 315.0},
        {"name": "Ketu", "sign": "Leo", "house": 9, "longitude": 135.0},
        {"name": "Sun", "sign": "Capricorn", "house": 2, "longitude": 285.0},
    ],
}

ROUTING_MATRIX = [
    ("Property yog hai kya?", "property_yog"),
    ("Kya mujhe ghar milega?", "property_yog"),
    ("Will I own a home?", "property_yog"),
    ("Apna ghar possible hai?", "property_yog"),
    ("Property capacity kaisi hai?", "property_capacity"),
    ("Ghar lene ki capacity chart me?", "property_capacity"),
    ("Property risk kaisa hai?", "property_risk"),
    ("Ghar dispute risk chart se?", "property_risk"),
    ("Plot ya flat kaun sa better?", "property_type_fit"),
    ("Which property type suits me?", "property_type_fit"),
    ("Kis tarah ka ghar hoga?", "property_type_fit"),
    ("Chota ya bada ghar?", "property_type_fit"),
    ("Ghar kaisa hoga chart se?", "property_type_fit"),
    ("Paitrik property milegi kya?", "property_inherit"),
    ("Ancestral home chart me?", "property_inherit"),
    ("Property dispute case hai?", "property_dispute"),
    ("Ghar ka vivad court me?", "property_dispute"),
    ("Rent income property se?", "property_rent"),
    ("Ghar rent pe dena sahi?", "property_rent"),
    ("Ghar banwana sahi rahega?", "property_build"),
    ("Home construction chart?", "property_build"),
    ("Property sell kar sakta hoon?", "property_sell"),
    ("Ghar bech sakta hoon?", "property_sell"),
    ("Ghar kharid sakta hoon?", "property_buy"),
    ("Buy flat possible hai?", "property_buy"),
    ("Home loan EMI chart se?", "property_loan"),
    ("Property loan ke liye chart?", "property_loan"),
    ("Plot lena sahi rahega?", "property_land"),
    ("Zameen khareedne ka yog?", "property_land"),
    ("Meri property overall kaisi?", "general_property"),
    ("Real estate chart reading?", "general_property"),
]


class PropertyEngineTests(unittest.TestCase):
    def test_all_archetypes_defined(self):
        self.assertEqual(len(PROPERTY_ARCHETYPES), 13)

    def test_routing_matrix(self):
        for q, expected in ROUTING_MATRIX:
            with self.subTest(q=q, expected=expected):
                self.assertTrue(is_property_static_question(q), msg=q)
                self.assertEqual(classify_property_archetype(q), expected, msg=q)

    def test_all_archetypes_emit_evidence(self):
        seen = set()
        for q, expected in ROUTING_MATRIX:
            res = run_property_static_engine(SAMPLE_KUNDLI, q)
            seen.add(res.archetype)
            self.assertEqual(res.archetype, expected, msg=q)
            self.assertGreaterEqual(len(res.evidence), 6, msg=q)
            ev_blob = " ".join(res.evidence)
            self.assertRegex(ev_blob, r"D4|Chaturthamsa", msg=q)
            self.assertTrue(res.verdict, msg=q)
        self.assertEqual(seen, set(a for _, a in ROUTING_MATRIX))

    def test_type_fit_d4_size_tone(self):
        for q in ("Chota ya bada ghar?", "Ghar kaisa hoga chart se?", "2BHK ya 3BHK?"):
            with self.subTest(q=q):
                res = run_property_static_engine(SAMPLE_KUNDLI, q)
                self.assertEqual(res.archetype, "property_type_fit")
                ev_blob = " ".join(res.evidence) + " " + res.verdict
                self.assertRegex(ev_blob, r"D4|Chaturthamsa|size|style", msg=q)

    def test_timing_not_property_static(self):
        self.assertFalse(is_property_static_question("Ghar kab milega?"))

    def test_money_stays_finance(self):
        q = "Ghar khareedne ke liye paisa banega kya?"
        self.assertTrue(is_property_money_only_question(q))
        self.assertFalse(is_property_static_question(q))
        self.assertTrue(is_finance_static_question(q))
        self.assertEqual(classify_finance_archetype(q), "property_money")

    def test_yog_stays_property_not_finance(self):
        q = "Property yog kaisa hai chart me?"
        self.assertTrue(is_property_static_question(q))
        self.assertFalse(is_finance_static_question(q))
        self.assertEqual(classify_property_archetype(q), "property_yog")


if __name__ == "__main__":
    unittest.main()

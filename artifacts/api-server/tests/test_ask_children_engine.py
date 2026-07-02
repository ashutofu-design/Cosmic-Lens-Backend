import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_children import run_children_static_engine
from ask_children.classifier import classify_children_archetype, is_children_static_question
from ask_children.children_registry import CHILDREN_ARCHETYPES
from ask_health.classifier import is_health_static_question


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
}

ROUTING_MATRIX = [
    ("Kya mujhe santan hogi?", "child_promise"),
    ("Putra prapti ke yog hain kya?", "child_promise"),
    ("Will I have a child?", "child_promise"),
    ("Conceive kar paungi kya?", "fertility_conception"),
    ("IVF successful ho sakta hai chart ke hisaab se?", "fertility_conception"),
    ("Infertility chart kaisa hai?", "fertility_conception"),
    ("Pregnancy safe rahegi kya?", "pregnancy_wellbeing"),
    ("Good news milegi kya?", "pregnancy_wellbeing"),
    ("Garbh tik sakta hai?", "pregnancy_wellbeing"),
    ("Santan me delay hai kya?", "child_delay"),
    ("Late motherhood chart me dikh raha hai?", "child_delay"),
    ("Ladka ya ladki hoga?", "child_gender_note"),
    ("Beta ya beti ka gender?", "child_gender_note"),
    ("Kitne bachche honge?", "number_of_children"),
    ("Twins possible hain kya?", "number_of_children"),
    ("Mera bachcha kaisa nature ka hoga?", "child_nature"),
    ("Child personality chart se?", "child_nature"),
    ("Bachche se mera rishta kaisa rahega?", "parent_child_bond"),
    ("Parent child bond strong hoga?", "parent_child_bond"),
    ("Bachche ki success ka yog?", "child_success"),
    ("Child future bright hoga?", "child_success"),
    ("Adoption possible hai kya?", "adoption_path"),
    ("Surrogacy ke liye chart?", "adoption_path"),
    ("Miscarriage ka dar hai?", "child_loss_concern"),
    ("Garbhpat ke baad hope hai?", "child_loss_concern"),
    ("Nisantan dosh hai kya?", "progeny_obstacles"),
    ("Santan nahi ho rahi obstacle kya?", "progeny_obstacles"),
    ("Meri santan overall kaisi?", "general_children"),
    ("Bachche ke baare me chart kya kehta hai?", "general_children"),
]


class ChildrenEngineTests(unittest.TestCase):
    def test_all_archetypes_defined(self):
        self.assertEqual(len(CHILDREN_ARCHETYPES), 13)

    def test_routing_matrix(self):
        for q, expected in ROUTING_MATRIX:
            with self.subTest(q=q, expected=expected):
                self.assertTrue(is_children_static_question(q), msg=q)
                self.assertEqual(classify_children_archetype(q), expected, msg=q)

    def test_all_archetypes_emit_evidence(self):
        seen = set()
        for q, expected in ROUTING_MATRIX:
            res = run_children_static_engine(SAMPLE_KUNDLI, q)
            seen.add(res.archetype)
            self.assertEqual(res.archetype, expected, msg=q)
            self.assertGreaterEqual(len(res.evidence), 4, msg=q)
            self.assertTrue(res.verdict, msg=q)
        self.assertEqual(seen, set(a for _, a in ROUTING_MATRIX))

    def test_timing_not_children_static(self):
        self.assertFalse(is_children_static_question("Bachcha kab hoga?"))

    def test_spouse_parenting_not_children(self):
        self.assertFalse(is_children_static_question("Spouse parenting style kaisa hoga?"))

    def test_medical_fertility_stays_health(self):
        q = "PCOD treatment ke baad fertility doctor ne kya kaha?"
        self.assertFalse(is_children_static_question(q))
        self.assertTrue(is_health_static_question(q))

    def test_d10_divisional_not_children_engine(self):
        q = "D10 mein Sun Makar rashi mein hai (5th house se kya hota hai"
        self.assertFalse(is_children_static_question(q))

    def test_astrological_fertility_stays_children(self):
        q = "Fertility chart kaisa hai conceive ke liye?"
        self.assertTrue(is_children_static_question(q))
        self.assertFalse(is_health_static_question(q))


if __name__ == "__main__":
    unittest.main()

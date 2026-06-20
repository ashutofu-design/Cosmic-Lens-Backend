"""Regression: 20 common marriage/partner Ask questions — routing + evidence smoke test."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_mr.classifier import classify_mr_archetype
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
                {"name": "Mercury", "sign": "Scorpio", "house": 2},
                {"name": "Jupiter", "sign": "Cancer", "house": 10},
            ],
        }
    },
}

# (question, expected_archetype, strict)
# strict=False → only assert engine runs + has evidence (routing debatable)
BATCH = [
    ("Mera life partner ka nature aur personality kaisa hoga?", "partner_nature", True),
    ("Partner emotionally expressive hoga ya reserved?", "partner_nature", True),
    ("Marriage mein loyalty aur commitment level kaisa rahega?", "loyalty_trust", True),
    ("Love marriage ke yog zyada hain ya arranged marriage ke?", "love_vs_arranged", True),
    ("Partner ka profession ya work field kis type ka ho sakta hai?", "spouse_profession", True),
    ("Partner ki family background kaisi ho sakti hai?", "partner_nature", True),
    ("Physical appearance aur overall personality kaisi ho sakti hai?", "partner_nature", True),
    ("Marriage ke baad relationship ki strengths kya hongi?", "general_mr", True),
    ("Relationship mein major challenges ya conflicts kis wajah se aa sakte hain?", "general_mr", True),
    ("Partner spiritual, practical, ambitious ya artistic nature ka hoga?", "partner_nature", True),
    ("Marriage ke baad emotional compatibility kaisi rahegi?", "general_mr", True),
    ("Partner dominant hoga ya cooperative?", "partner_nature", True),
    ("Partner ke love language (care dikhane ka tareeka) kya ho sakta hai?", "partner_nature", True),
    ("Relationship mein trust aur communication ka level kaisa rahega?", "loyalty_trust", True),
    ("Partner ke andar kaunsi qualities mujhe sabse zyada attract karengi?", "partner_nature", True),
    ("Marriage se meri life mein kya positive changes aa sakte hain?", "general_mr", True),
    ("Kya partner different culture, city ya background se ho sakta hai?", "partner_nature", True),
    ("Relationship mein kis cheez par mujhe sabse zyada kaam karna chahiye?", "general_mr", True),
    ("Ideal spouse ki qualities meri kundli ke hisab se kya hain?", "partner_nature", True),
    ("Marriage partner meri career aur life goals ko support karega ya nahi?", "general_mr", True),
]


class BatchMrTwentyQuestionsTests(unittest.TestCase):
    def test_all_twenty_run_with_evidence(self):
        for q, _expected, _strict in BATCH:
            with self.subTest(q=q[:50]):
                arch = classify_mr_archetype(q)
                res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
                self.assertEqual(arch, res.archetype)
                self.assertTrue(res.verdict)
                self.assertGreaterEqual(len(res.evidence or []), 1)

    def test_strict_routing(self):
        for q, expected, strict in BATCH:
            if not strict:
                continue
            with self.subTest(q=q[:50]):
                self.assertEqual(classify_mr_archetype(q), expected)


if __name__ == "__main__":
    unittest.main()

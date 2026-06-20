"""Full relationship Ask matrix — routing + engine smoke (70 questions)."""
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

# id, question, expected_archetype
MATRIX = [
    (1, "Mera life partner ka nature aur personality kaisa hoga?", "partner_nature"),
    (2, "Partner emotionally expressive hoga ya reserved?", "emotional_attachment"),
    (3, "Marriage mein loyalty aur commitment level kaisa rahega?", "loyalty_trust"),
    (4, "Love marriage ke yog zyada hain ya arranged marriage ke?", "love_vs_arranged"),
    (5, "Partner ka profession ya work field kis type ka ho sakta hai?", "spouse_profession"),
    (6, "Partner ki family background kaisi ho sakti hai?", "partner_nature"),
    (7, "Physical appearance aur overall personality kaisi ho sakti hai?", "partner_nature"),
    (8, "Marriage ke baad relationship ki strengths kya hongi?", "general_mr"),
    (9, "Relationship mein major challenges ya conflicts kis wajah se aa sakte hain?", "general_mr"),
    (10, "Partner spiritual, practical, ambitious ya artistic nature ka hoga?", "partner_nature"),
    (11, "Marriage ke baad emotional compatibility kaisi rahegi?", "general_mr"),
    (12, "Partner dominant hoga ya cooperative?", "partner_nature"),
    (13, "Partner ke love language (care dikhane ka tareeka) kya ho sakta hai?", "partner_nature"),
    (14, "Relationship mein trust aur communication ka level kaisa rahega?", "loyalty_trust"),
    (15, "Partner ke andar kaunsi qualities mujhe sabse zyada attract karengi?", "partner_nature"),
    (16, "Marriage se meri life mein kya positive changes aa sakte hain?", "general_mr"),
    (17, "Kya partner different culture, city ya background se ho sakta hai?", "partner_nature"),
    (18, "Relationship mein kis cheez par mujhe sabse zyada kaam karna chahiye?", "general_mr"),
    (19, "Ideal spouse ki qualities meri kundli ke hisab se kya hain?", "partner_nature"),
    (20, "Marriage partner meri career aur life goals ko support karega ya nahi?", "general_mr"),
    (21, "Meri patni ka kaam kis field mein hoga?", "spouse_profession"),
    (22, "Husband ki naukri ya business line kya ho sakti hai?", "spouse_profession"),
    (23, "Kya meri shaadi achhi rahegi?", "general_mr"),
    (24, "Vivah ke baad khushi aur sukh ka level kaisa rahega?", "general_mr"),
    (25, "Kya mera breakup ho sakta hai?", "breakup_risk"),
    (26, "Relationship tootne ka risk hai kya?", "breakup_risk"),
    (27, "Divorce ya alag hone ka pattern chart mein dikhta hai?", "breakup_risk"),
    (28, "Patchup ho sakta hai kya?", "patchup"),
    (29, "Kya woh wapas aa sakta hai?", "patchup"),
    (30, "Reconciliation possible hai relationship mein?", "patchup"),
    (31, "Hamari chemistry kaisi rahegi?", "chemistry"),
    (32, "Physical attraction strong rahega kya?", "chemistry"),
    (33, "Romance aur spark marriage mein rahega?", "chemistry"),
    (34, "Mera emotional attachment style kaisa hai relationship mein?", "emotional_attachment"),
    (35, "Partner ke saath feelings gehra rahenge ya halki rahengi?", "emotional_attachment"),
    (36, "Ghar wale meri shaadi ke liye maanenge kya?", "family_approval"),
    (37, "Intercaste marriage mein family approval milega?", "family_approval"),
    (38, "Parents meri pasand ko accept karenge?", "family_approval"),
    (39, "Kya main manglik hoon?", "manglik"),
    (40, "Mangal dosh hai kya meri kundli mein?", "manglik"),
    (41, "Kya chhupa rishta ya secret affair ka yog hai?", "secret_relationship"),
    (42, "Kya yeh ek tarfa pyar hai?", "one_sided_love"),
    (43, "Crush accept karega kya?", "one_sided_love"),
    (44, "Kya main possessive ya jealous nature ka hoon?", "obsession"),
    (45, "Private life aur conjugal compatibility kaisi rahegi?", "bed_intimacy"),
    (46, "Relationship mein self worth weak kyun lagti hai?", "self_worth"),
    (47, "Partner mujhe respect dega ya nahi?", "self_worth"),
    (48, "Kya meri dusri shaadi hogi?", "second_marriage"),
    (49, "Second marriage ka yog hai kya?", "second_marriage"),
    (50, "Long distance relationship chalega kya?", "long_distance"),
    (51, "Door rehkar rishta strong reh sakta hai?", "long_distance"),
    (52, "Partner rich hoga ya financially comfortable?", "spouse_wealth"),
    (53, "Spouse wealth aur paisa level kaisa hoga?", "spouse_wealth"),
    (54, "Ex wapas aayega kya?", "patchup"),
    (55, "Gun milan / 36 gun score kaisa rahega?", "general_mr"),
    (56, "Partner age gap zyada hoga kya?", "partner_nature"),
    (57, "Kya main marry kar paungi?", "general_mr"),
    (58, "Khud pasand se shaadi hogi ya ghar wale choose karenge?", "love_vs_arranged"),
    (59, "Kya mera partner loyal rahega ya dhokha de sakta hai?", "loyalty_trust"),
    (60, "Multiple love relationships ka pattern hai?", "secret_relationship"),
]


class MrRelationshipMatrixTests(unittest.TestCase):
    def test_matrix_routing(self):
        for qid, question, expected in MATRIX:
            with self.subTest(id=qid, q=question[:48]):
                self.assertEqual(classify_mr_archetype(question), expected)

    def test_matrix_engine_runs(self):
        for qid, question, expected in MATRIX:
            with self.subTest(id=qid, q=question[:48]):
                arch = classify_mr_archetype(question)
                res = run_mr_static_engine(SAMPLE_KUNDLI, question, wants_explain=False)
                self.assertEqual(res.archetype, arch)
                self.assertEqual(res.archetype, expected)
                self.assertTrue(res.verdict)
                self.assertGreaterEqual(len(res.evidence or []), 1)
                payload = res.to_narrator_payload()
                self.assertIn(f"ARCHETYPE: {expected}", payload)
                self.assertIn("VERDICT:", payload)


if __name__ == "__main__":
    unittest.main()

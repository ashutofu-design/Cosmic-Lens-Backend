import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_mr import run_mr_static_engine
from ask_mr.classifier import classify_mr_archetype
from ask_mr.narrator import render_template


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


class MrEngineTests(unittest.TestCase):
    def test_breakup_risk_engine_runs_and_emits_evidence(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "kya mera breakup hoga?", wants_explain=False)
        self.assertEqual(res.archetype, "breakup_risk")
        self.assertTrue(len(res.evidence) >= 1)

    def test_manglik_skips_llm_without_explain(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "kya main manglik hun?", wants_explain=False)
        self.assertEqual(res.archetype, "manglik")
        self.assertTrue(res.skip_llm)
        self.assertTrue(render_template(res))

    def test_manglik_uses_llm_when_explain(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "kya main manglik hun?", wants_explain=True)
        self.assertFalse(res.skip_llm)

    def test_general_mr_has_evidence(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "kya shaadi achhi hogi?", wants_explain=False)
        self.assertEqual(res.archetype, "general_mr")
        self.assertTrue(res.verdict)
        self.assertTrue(len(res.evidence) >= 1)

    def test_general_mr_strengths_question_leads_with_positives(self):
        q = "Marriage ke baad relationship ki strengths kya hongi?"
        res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        self.assertEqual(res.archetype, "general_mr")
        self.assertEqual(res.checks.get("question_intent"), "strengths")
        self.assertIn("strength", res.verdict.lower())
        joined = " ".join(res.evidence).lower()
        self.assertTrue(
            "moon in 7th" in joined or "jupiter in house" in joined or "venus in house" in joined
        )
        self.assertFalse(res.verdict.lower().startswith("marriage/relationship quality: strained"))

    def test_general_mr_emotional_compatibility_is_balanced(self):
        q = "Marriage ke baad emotional compatibility kaisi rahegi?"
        res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        self.assertEqual(res.archetype, "general_mr")
        self.assertEqual(res.checks.get("question_intent"), "emotional_compatibility")
        self.assertIn("emotional compatibility", res.verdict.lower())
        joined = " ".join(res.evidence).lower()
        self.assertIn("moon in 7th", joined)
        self.assertIn("emotional friction", joined)

    def test_partner_nature_dominant_cooperative_synthesis(self):
        q = "Partner dominant hoga ya cooperative?"
        res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        self.assertEqual(res.archetype, "partner_nature")
        joined = " ".join(res.evidence).lower()
        self.assertIn("partnership style", joined)

    def test_partner_nature_background_narrator_hint(self):
        q = "Partner ki family background kaisi ho sakti hai?"
        res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        from ask_mr.engines.partner_nature import partner_nature_narrator_payload

        payload = partner_nature_narrator_payload(res)
        self.assertIn("family background", payload.lower())
        self.assertIn("different background theme", payload.lower())

    def test_general_mr_partner_support_intent(self):
        q = "Marriage partner meri career aur life goals ko support karega ya nahi?"
        res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        self.assertEqual(res.checks.get("question_intent"), "partner_support")
        self.assertIn("support", res.verdict.lower())

    def test_one_sided_love(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "kya yeh ek tarfa pyar hai?", wants_explain=False)
        self.assertEqual(res.archetype, "one_sided_love")

    def test_secret_relationship(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "kya chhupa rishta chal raha hai?", wants_explain=False)
        self.assertEqual(res.archetype, "secret_relationship")

    def test_obsession(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "kya main possessive hun?", wants_explain=False)
        self.assertEqual(res.archetype, "obsession")

    def test_partner_expressive_routes_partner_nature(self):
        q = "Partner emotionally expressive hoga ya reserved?"
        self.assertEqual(classify_mr_archetype(q), "partner_nature")

    def test_partner_respect_routes_partner_nature(self):
        self.assertEqual(
            classify_mr_archetype("Partner mujhe respect dega ya nahi?"),
            "partner_nature",
        )

    def test_emotional_attachment(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "mera emotional attachment kaisa hai?", wants_explain=False)
        self.assertEqual(res.archetype, "emotional_attachment")

    def test_bed_intimacy(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "private life kaisi rahegi?", wants_explain=False)
        self.assertEqual(res.archetype, "bed_intimacy")

    def test_self_worth(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "relationship me self worth weak kyun lagti hai?", wants_explain=False)
        self.assertEqual(res.archetype, "self_worth")

    def test_love_vs_arranged_engine_emits_tilt(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "love marriage hogi ya arranged?", wants_explain=False)
        self.assertEqual(res.archetype, "love_vs_arranged")
        self.assertFalse(res.skip_llm)
        self.assertTrue(res.verdict)
        self.assertTrue(len(res.evidence) >= 1)

    def test_love_vs_arranged_hinglish_typo(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "mera love marriage he ya arrange?", wants_explain=False)
        self.assertEqual(res.archetype, "love_vs_arranged")
        self.assertTrue(len(res.evidence) >= 1)

    def test_partner_nature_engine_word_budget(self):
        res = run_mr_static_engine(
            SAMPLE_KUNDLI, "mera partner ka nature kaisa hoga?", wants_explain=False
        )
        self.assertEqual(res.archetype, "partner_nature")
        self.assertTrue(res.word_budget >= 90)
        self.assertTrue(len(res.evidence) >= 3)

    def test_loyalty_trust_engine_runs(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "kya wo loyal hai ya dhokha karega?", wants_explain=False)
        self.assertEqual(res.archetype, "loyalty_trust")
        self.assertTrue(len(res.evidence) >= 1)
        self.assertIn("trust_level", (res.checks or {}))

    def test_loyalty_commitment_question_routes(self):
        res = run_mr_static_engine(
            SAMPLE_KUNDLI,
            "Marriage me loyalty aur commitment level kaise rahega",
            wants_explain=False,
        )
        self.assertEqual(res.archetype, "loyalty_trust")
        level = (res.checks or {}).get("trust_level")
        self.assertIn(level, ("mixed", "unstable", "moderate", "risky"))
        if (res.checks or {}).get("negative_signal_count", 0) >= 1:
            self.assertTrue(any("Trust challenge:" in e for e in res.evidence))

    def test_patchup_engine_runs(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "patchup ho sakta hai?", wants_explain=False)
        self.assertEqual(res.archetype, "patchup")

    def test_chemistry_engine_runs(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "hamari chemistry kaisi rahegi?", wants_explain=False)
        self.assertEqual(res.archetype, "chemistry")

    def test_family_approval_engine_runs(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "ghar wale maanenge kya?", wants_explain=False)
        self.assertEqual(res.archetype, "family_approval")

    def test_spouse_profession_engine_runs(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "meri patni ka profession kya hoga?", wants_explain=False)
        self.assertEqual(res.archetype, "spouse_profession")
        self.assertTrue(len(res.evidence) >= 2)

    def test_partner_family_background_routes_partner_nature(self):
        q = "Partner ki family background kaisi ho sakti hai?"
        self.assertEqual(classify_mr_archetype(q), "partner_nature")

    def test_emotional_compatibility_routes_general_mr(self):
        q = "Marriage ke baad emotional compatibility kaisi rahegi?"
        self.assertEqual(classify_mr_archetype(q), "general_mr")

    def test_classifier_audit_regressions(self):
        cases = [
            ("Relationship tootne ka risk hai kya?", "breakup_risk"),
            ("Door rehkar rishta strong reh sakta hai?", "long_distance"),
            (
                "Khud pasand se shaadi hogi ya ghar wale choose karenge?",
                "love_vs_arranged",
            ),
        ]
        for q, expected in cases:
            with self.subTest(q=q[:48]):
                self.assertEqual(classify_mr_archetype(q), expected)
        q = "Marriage partner meri career aur life goals ko support karega ya nahi?"
        self.assertEqual(classify_mr_archetype(q), "general_mr")

    def test_family_approval_still_routes_elders(self):
        q = "ghar wale maanenge kya?"
        self.assertEqual(classify_mr_archetype(q), "family_approval")

    def test_second_marriage_engine(self):
        q = "Kya meri dusri shaadi hogi?"
        self.assertEqual(classify_mr_archetype(q), "second_marriage")
        res = run_mr_static_engine(SAMPLE_KUNDLI, q)
        self.assertEqual(res.archetype, "second_marriage")
        self.assertTrue(len(res.evidence) >= 1)

    def test_long_distance_engine(self):
        q = "Long distance relationship chalega kya?"
        self.assertEqual(classify_mr_archetype(q), "long_distance")
        res = run_mr_static_engine(SAMPLE_KUNDLI, q)
        self.assertEqual(res.archetype, "long_distance")

    def test_spouse_wealth_engine(self):
        q = "Partner rich hoga ya financially comfortable?"
        self.assertEqual(classify_mr_archetype(q), "spouse_wealth")
        res = run_mr_static_engine(SAMPLE_KUNDLI, q)
        self.assertEqual(res.archetype, "spouse_wealth")
        self.assertTrue(len(res.evidence) >= 2)

    def test_spouse_family_wale_uses_8th_house_evidence(self):
        q = "wife ke family wale kaise honge"
        self.assertEqual(classify_mr_archetype(q), "partner_nature")
        res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        self.assertEqual(res.checks.get("question_focus"), "spouse_family")
        joined = " ".join(res.evidence).lower()
        self.assertIn("8th house", joined)
        self.assertIn("in-law", joined)
        self.assertNotIn("7th house sign baseline", joined)

    def test_spouse_family_not_user_parents_approval(self):
        q = "ghar wale maanenge kya?"
        self.assertEqual(classify_mr_archetype(q), "family_approval")
        res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        self.assertEqual(res.archetype, "family_approval")

    def test_partner_family_background_stays_partner_upbringing(self):
        q = "Partner ki family background kaisi ho sakti hai?"
        res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        self.assertEqual(res.archetype, "partner_nature")
        self.assertNotEqual(res.checks.get("question_focus"), "spouse_family")
        joined = " ".join(res.evidence).lower()
        self.assertIn("7th house sign baseline", joined)
        self.assertIn("different background theme", joined)

    def test_partner_anger_uses_7th_house_temper(self):
        q = "Partner gussa wala hoga kya?"
        res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        self.assertEqual(res.archetype, "partner_nature")
        joined = " ".join(res.evidence).lower()
        self.assertIn("temper signal", joined)
        self.assertIn("7th", joined)

    def test_spouse_appearance_height_engine(self):
        q = "partner ki height kaisi hogi?"
        self.assertEqual(classify_mr_archetype(q), "spouse_appearance")
        res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        joined = " ".join(res.evidence).lower()
        self.assertIn("height", joined)
        self.assertIn("7th", joined)

    def test_children_parenting_engine(self):
        q = "spouse ka parenting style kaisa hoga?"
        self.assertEqual(classify_mr_archetype(q), "children_parenting")
        res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        self.assertIn("parenting", res.verdict.lower())

    def test_karmic_soulmate_engine(self):
        q = "kya yeh soulmate hai?"
        self.assertEqual(classify_mr_archetype(q), "karmic_marriage")
        res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        joined = " ".join(res.evidence).lower()
        self.assertIn("rahu", joined)

    def test_dating_red_flags_engine(self):
        q = "relationship me red flags kya hain?"
        self.assertEqual(classify_mr_archetype(q), "dating_courtship")
        res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        self.assertTrue(any("red flag" in e.lower() for e in res.evidence))

    def test_ex_return_routes_patchup(self):
        self.assertEqual(classify_mr_archetype("Ex wapas aayega kya?"), "patchup")


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_mr import run_mr_static_engine
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

    def test_one_sided_love(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "kya yeh ek tarfa pyar hai?", wants_explain=False)
        self.assertEqual(res.archetype, "one_sided_love")

    def test_secret_relationship(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "kya chhupa rishta chal raha hai?", wants_explain=False)
        self.assertEqual(res.archetype, "secret_relationship")

    def test_obsession(self):
        res = run_mr_static_engine(SAMPLE_KUNDLI, "kya main possessive hun?", wants_explain=False)
        self.assertEqual(res.archetype, "obsession")

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


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_career import run_career_static_engine
from ask_career.classifier import classify_career_archetype, is_career_static_question


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


class CareerEngineTests(unittest.TestCase):
    def test_job_vs_business_routes_and_emits_evidence(self):
        q = "Mere liye job better hai ya business?"
        self.assertEqual(classify_career_archetype(q), "job_vs_business")
        res = run_career_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        self.assertEqual(res.archetype, "job_vs_business")
        joined = " ".join(res.evidence).lower()
        self.assertIn("job", joined)
        self.assertIn("business", joined)

    def test_sector_fit_government(self):
        q = "Government job suit karegi?"
        self.assertTrue(is_career_static_question(q))
        self.assertEqual(classify_career_archetype(q), "sector_fit")
        res = run_career_static_engine(SAMPLE_KUNDLI, q)
        self.assertEqual(res.archetype, "sector_fit")
        self.assertTrue(len(res.evidence) >= 3)

    def test_career_traits_leadership(self):
        q = "Mere andar leadership quality kitni hai?"
        self.assertEqual(classify_career_archetype(q), "career_traits")
        res = run_career_static_engine(SAMPLE_KUNDLI, q)
        self.assertIn("leadership", " ".join(res.evidence).lower())

    def test_strengths_skills_natural_talent(self):
        q = "Mere natural talents kya hain?"
        self.assertTrue(is_career_static_question(q))
        res = run_career_static_engine(SAMPLE_KUNDLI, q)
        self.assertEqual(res.archetype, "strengths_skills")

    def test_entrepreneurship_startup(self):
        q = "Kya startup founder banna suit karega?"
        self.assertEqual(classify_career_archetype(q), "entrepreneurship")
        res = run_career_static_engine(SAMPLE_KUNDLI, q)
        self.assertEqual(res.checks.get("mode"), "startup")

    def test_foreign_career(self):
        q = "Kya mujhe foreign country me kaam karna chahiye?"
        self.assertEqual(classify_career_archetype(q), "foreign_career")
        res = run_career_static_engine(SAMPLE_KUNDLI, q)
        joined = " ".join(res.evidence).lower()
        self.assertIn("9th", joined)
        self.assertIn("12th", joined)

    def test_workplace_relations_boss(self):
        q = "Kya boss se relation achha rahega?"
        self.assertEqual(classify_career_archetype(q), "workplace_relations")
        res = run_career_static_engine(SAMPLE_KUNDLI, q)
        self.assertEqual(res.checks.get("focus"), "boss")

    def test_income_wealth_freelancing(self):
        q = "Kya mujhe freelancing suit karegi?"
        self.assertEqual(classify_career_archetype(q), "income_wealth")
        res = run_career_static_engine(SAMPLE_KUNDLI, q)
        self.assertIn("freelanc", " ".join(res.evidence).lower())

    def test_timing_question_not_career_static(self):
        self.assertFalse(is_career_static_question("Kab job milegi?"))

    def test_spouse_profession_not_career_static(self):
        self.assertFalse(is_career_static_question("Meri patni ka profession kya hoga?"))

    def test_general_career_open_chart(self):
        q = "Mera overall career pattern kaisa hai?"
        res = run_career_static_engine(SAMPLE_KUNDLI, q)
        self.assertEqual(res.archetype, "general_career")
        self.assertTrue(res.checks.get("open_chart_qa"))

    def test_engine_result_has_narrator_payload(self):
        res = run_career_static_engine(SAMPLE_KUNDLI, "IT industry suit karegi?")
        payload = res.to_narrator_payload()
        self.assertIn("EVIDENCE", payload)
        self.assertIn("VERDICT", payload)


if __name__ == "__main__":
    unittest.main()

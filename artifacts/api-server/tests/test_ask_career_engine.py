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


    def test_which_business_routes_sector_fit(self):
        q = "Agar business me jaau konsa business best hai"
        self.assertEqual(classify_career_archetype(q), "sector_fit")
        res = run_career_static_engine(SAMPLE_KUNDLI, q)
        self.assertEqual(res.archetype, "sector_fit")
        self.assertIn("business", " ".join(res.summary).lower())

    def test_resolve_overrides_llm_job_vs_biz(self):
        from ask_career.routing import resolve_career_archetype

        arch, reason = resolve_career_archetype(
            "Agar business me jaau konsa business best hai",
            llm_archetype="job_vs_business",
            interpretation="User wants to know which business is best for them to start.",
        )
        self.assertEqual(arch, "sector_fit")
        self.assertTrue(reason)

    def test_job_vs_business_still_routes(self):
        q = "Mere liye job better hai ya business?"
        self.assertEqual(classify_career_archetype(q), "job_vs_business")
        from ask_career.routing import resolve_career_archetype

        arch, _ = resolve_career_archetype(
            q,
            llm_archetype="sector_fit",
            interpretation="User wants to know if job or business suits them.",
        )
        self.assertEqual(arch, "job_vs_business")

    def test_youtuber_routes_creativity(self):
        q = "Acha youtuber ban sakta hun me?"
        self.assertTrue(is_career_static_question(q))
        self.assertEqual(classify_career_archetype(q), "creativity_innovation")
        from ask_career.routing import resolve_career_archetype

        arch, _ = resolve_career_archetype(
            q,
            llm_archetype="general_career",
            interpretation="User wants to know if they can become a YouTuber.",
        )
        self.assertEqual(arch, "creativity_innovation")
        res = run_career_static_engine(SAMPLE_KUNDLI, q)
        self.assertEqual(res.archetype, "creativity_innovation")
        self.assertIn("youtube", res.verdict.lower())

    def test_food_business_routes_sector_fit(self):
        q = "Food business acha he kya?"
        self.assertEqual(classify_career_archetype(q), "sector_fit")
        res = run_career_static_engine(SAMPLE_KUNDLI, q)
        self.assertEqual(res.archetype, "sector_fit")
        self.assertEqual(res.checks.get("sector"), "food")
        joined = " ".join(res.evidence).lower()
        self.assertNotIn("job vs business split", joined)


class TestCareerAnswerGuard(unittest.TestCase):
    _JOB_META = {
        "archetype": "job_vs_business",
        "verdict": "Employment path stronger — job ~60% vs business ~40%",
        "checks": {"job_pct": 60, "business_pct": 40},
    }

    def test_verify_blocks_labels_and_wrong_pick(self):
        from ask_career.answer_guard import verify_career_answer

        ok, issues = verify_career_answer(
            "job ya business kya better hai?",
            "Seedha jawab: pehle job phir business. Conclusion: dono.",
            self._JOB_META,
        )
        self.assertFalse(ok)
        self.assertIn("template_labels", issues)

    def test_verify_accepts_job_answer(self):
        from ask_career.answer_guard import verify_career_answer

        ans = (
            "Aapki kundli mein job path zyada strong hai — structure aur discipline se "
            "employment suit karta hai. Isliye job mein hi raho; business abhi secondary hai."
        )
        ok, _ = verify_career_answer(
            "job ya business kya better hai?",
            ans,
            self._JOB_META,
        )
        self.assertTrue(ok)

    def test_verify_rejects_job_split_for_which_business(self):
        from ask_career.answer_guard import verify_career_answer

        meta = {
            "archetype": "job_vs_business",
            "verdict": "Employment path stronger — job ~60% vs business ~40%",
            "checks": {"job_pct": 60, "business_pct": 40},
            "user_intent": "User wants to know which business is best for them to start.",
        }
        ans = (
            "Tere liye business ka scope lagbhag 40% hai, par abhi employment ya job "
            "zyada suit karti hai, kareeb 60%."
        )
        ok, issues = verify_career_answer(
            "Agar business me jaau konsa business best hai",
            ans,
            meta,
        )
        self.assertFalse(ok)
        self.assertIn("wrong_engine_job_vs_biz_for_which_business", issues)

    def test_verify_rejects_job_split_for_food_business(self):
        from ask_career.answer_guard import verify_career_answer

        meta = {
            "archetype": "sector_fit",
            "verdict": "Food/hospitality business: suitable pattern visible",
            "checks": {"sector": "food"},
            "user_intent": "User wants to know if food business is good for them.",
        }
        ans = (
            "Business ka scope 40% hai par employment zyada suit karti hai 60%. "
            "Structured professional field mein zyada achha kama sakte ho."
        )
        ok, issues = verify_career_answer("Food business acha he kya?", ans, meta)
        self.assertFalse(ok)
        self.assertIn("sector_suit_but_job_split_answer", issues)


if __name__ == "__main__":
    unittest.main()

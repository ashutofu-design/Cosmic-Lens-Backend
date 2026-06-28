import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_education import run_education_static_engine
from ask_education.classifier import classify_education_archetype, is_education_static_question
from ask_education.education_registry import EDUCATION_ARCHETYPES
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

# (question, expected_archetype)
ROUTING_MATRIX = [
    ("Kya mera exam pass ho jayega?", "exam_success"),
    ("NEET exam clear ho sakta hai kya?", "competitive_exam"),
    ("JEE main crack kar paunga?", "competitive_exam"),
    ("12th board exam me achha result aayega?", "competitive_exam"),
    ("Higher studies videsh mein possible hai?", "higher_studies"),
    ("Masters abroad ke liye chart kaisa hai?", "higher_studies"),
    ("PhD ke yog hain kya?", "higher_studies"),
    ("Mere liye kaunsi stream best rahegi science ya commerce?", "study_field"),
    ("PCM ya PCB kaunsa choose karun?", "study_field"),
    ("Medical line ke liye chart sahi hai?", "specialization_path"),
    ("Engineering line padh sakta hoon?", "specialization_path"),
    ("Law line ke liye suitable hoon?", "specialization_path"),
    ("College admission milega kya?", "admission"),
    ("University seat confirm hogi?", "admission"),
    ("Scholarship milegi kya?", "scholarship"),
    ("Merit scholarship ke chances kaisa?", "scholarship"),
    ("Degree complete ho jayegi kya?", "degree_completion"),
    ("Graduation ho paayega?", "degree_completion"),
    ("Achhe marks aayenge kya?", "marks_performance"),
    ("Percentage acchi ban sakti hai?", "marks_performance"),
    ("Padhai me mann nahi lagta kya karun?", "study_focus"),
    ("Meri buddhi padhai ke liye strong hai?", "learning_ability"),
    ("Maths me weak hoon kya karun?", "learning_ability"),
    ("Coaching join karni chahiye ya self study?", "coaching_support"),
    ("NEET coaching sahi rahegi?", "coaching_support"),
    ("Padhai me backlog clear ho jayega?", "education_obstacles"),
    ("Gap year ke baad padhai continue ho sakti hai?", "education_obstacles"),
    ("ITI course suit karega?", "vocational_diploma"),
    ("Polytechnic diploma ke liye chart?", "vocational_diploma"),
    ("Meri padhai overall kaisi rahegi?", "general_education"),
    ("Pariksha pass ho jayegi?", "exam_success"),
    ("Imtihaan clear ho payegi?", "exam_success"),
    ("NEET ke baad college admission milega?", "admission"),
    ("Sponsorship for higher studies?", "scholarship"),
    ("Science stream lena sahi hoga?", "study_field"),
    ("Maths me weak hoon kya karun?", "learning_ability"),
]


class EducationEngineTests(unittest.TestCase):
    def test_all_archetypes_defined(self):
        self.assertEqual(len(EDUCATION_ARCHETYPES), 15)

    def test_routing_matrix(self):
        for q, expected in ROUTING_MATRIX:
            with self.subTest(q=q, expected=expected):
                self.assertTrue(is_education_static_question(q), msg=q)
                self.assertEqual(classify_education_archetype(q), expected, msg=q)

    def test_all_archetypes_emit_evidence(self):
        seen = set()
        for q, expected in ROUTING_MATRIX:
            res = run_education_static_engine(SAMPLE_KUNDLI, q)
            seen.add(res.archetype)
            self.assertEqual(res.archetype, expected, msg=q)
            self.assertGreaterEqual(len(res.evidence), 4, msg=q)
            self.assertTrue(res.verdict, msg=q)
        self.assertEqual(seen, set(a for _, a in ROUTING_MATRIX))

    def test_timing_question_not_education_static(self):
        self.assertFalse(is_education_static_question("Exam kab clear hoga?"))

    def test_govt_exam_stays_career(self):
        q = "UPSC exam clear ho jayega kya?"
        self.assertFalse(is_education_static_question(q))
        self.assertTrue(is_career_static_question(q))
        self.assertEqual(classify_career_archetype(q), "career_milestones")

    def test_career_education_link_stays_career(self):
        q = "Career ke liye kaunsa course choose karun?"
        self.assertFalse(is_education_static_question(q))
        self.assertTrue(is_career_static_question(q))
        self.assertEqual(classify_career_archetype(q), "education_career")


if __name__ == "__main__":
    unittest.main()

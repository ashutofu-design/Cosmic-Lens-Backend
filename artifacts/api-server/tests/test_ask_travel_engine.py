import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_travel import run_travel_static_engine
from ask_travel.classifier import classify_travel_archetype, is_travel_static_question
from ask_travel.travel_registry import (
    TRAVEL_ARCHETYPES,
    is_career_job_abroad_question,
    is_education_study_abroad_question,
)
from ask_education.classifier import classify_education_archetype, is_education_static_question
from ask_career.classifier import classify_career_archetype, is_career_static_question

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
    ("Videsh jaa sakta hoon kya?", "travel_yog"),
    ("Foreign travel yog hai?", "travel_yog"),
    ("Settle abroad possible hai?", "foreign_settlement"),
    ("Videsh me bas sakta hoon?", "foreign_settlement"),
    ("Visa approve hoga kya?", "visa_theme"),
    ("US visa milega chart se?", "visa_theme"),
    ("Relocate abroad chart support?", "relocation_abroad"),
    ("Shift to Canada possible?", "relocation_abroad"),
    ("India wapas aa sakta hoon?", "return_india"),
    ("Abroad se wapas aana?", "return_india"),
    ("Videsh me delay hai kya?", "travel_obstacles"),
    ("Travel obstacle chart me?", "travel_obstacles"),
    ("Foreign trip possible hai?", "short_travel"),
    ("Abroad vacation chart?", "short_travel"),
    ("Teerth yatra hogi kya?", "pilgrimage_travel"),
    ("Pilgrimage abroad chart?", "pilgrimage_travel"),
    ("Passport milega chart se?", "passport_travel"),
    ("Travel capacity chart?", "passport_travel"),
    ("Green card possible hai?", "immigration"),
    ("PR file karna chart se?", "immigration"),
    ("Business trip abroad chart?", "business_travel"),
    ("Official travel abroad?", "business_travel"),
    ("Foreign travel risk chart?", "travel_risk"),
    ("Abroad accident risk?", "travel_risk"),
    ("Meri videsh yatra overall kaisi?", "general_travel"),
    ("Foreign travel chart reading?", "general_travel"),
    ("Kaun sa desh jaaunga?", "travel_country_fit"),
    ("USA ya Canada kaun sa better?", "travel_country_fit"),
]


class TravelEngineTests(unittest.TestCase):
    def test_all_archetypes_defined(self):
        self.assertEqual(len(TRAVEL_ARCHETYPES), 14)

    def test_routing_matrix(self):
        for q, expected in ROUTING_MATRIX:
            with self.subTest(q=q, expected=expected):
                self.assertTrue(is_travel_static_question(q), msg=q)
                self.assertEqual(classify_travel_archetype(q), expected, msg=q)

    def test_all_archetypes_emit_evidence(self):
        seen = set()
        for q, expected in ROUTING_MATRIX:
            res = run_travel_static_engine(SAMPLE_KUNDLI, q)
            seen.add(res.archetype)
            self.assertEqual(res.archetype, expected, msg=q)
            self.assertGreaterEqual(len(res.evidence), 6, msg=q)
            ev_blob = " ".join(res.evidence)
            self.assertRegex(ev_blob, r"9th|9H|12th|12H|Rahu|D9|Navamsa", msg=q)
            self.assertTrue(res.verdict, msg=q)
        self.assertEqual(seen, set(a for _, a in ROUTING_MATRIX))

    def test_study_abroad_stays_education(self):
        q = "Study abroad possible hai IELTS ke baad?"
        self.assertTrue(is_education_study_abroad_question(q))
        self.assertFalse(is_travel_static_question(q))
        self.assertTrue(is_education_static_question(q))
        self.assertEqual(classify_education_archetype(q), "higher_studies")

    def test_job_abroad_stays_career(self):
        q = "Foreign job milega chart se?"
        self.assertTrue(is_career_job_abroad_question(q))
        self.assertFalse(is_travel_static_question(q))
        self.assertTrue(is_career_static_question(q))
        self.assertEqual(classify_career_archetype(q), "foreign_career")

    def test_timing_not_travel_static(self):
        self.assertFalse(is_travel_static_question("Videsh kab jaunga?"))


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_litigation import run_litigation_static_engine
from ask_litigation.answer_guard import guard_litigation_answer
from ask_litigation.classifier import classify_litigation_archetype, is_litigation_static_question
from ask_litigation.litigation_registry import (
    LITIGATION_ARCHETYPES,
    is_career_police_job_question,
    is_death_penalty_crisis_question,
    is_property_court_question,
)
from ask_career.classifier import classify_career_archetype, is_career_static_question
from ask_property.classifier import classify_property_archetype, is_property_static_question

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
    ("Court case hoga kya?", "litigation_yog"),
    ("Mukadma ladega chart?", "litigation_yog"),
    ("Case jeet jaunga kya?", "case_outcome"),
    ("Will I win the case?", "case_outcome"),
    ("Case delay hoga kya?", "court_delay"),
    ("Mukadma lamba chalega?", "court_delay"),
    ("Bail milegi kya?", "bail_theme"),
    ("Zamanat milega chart se?", "bail_theme"),
    ("Jail hoga kya chart se?", "jail_concern"),
    ("Custody hoga kya?", "jail_concern"),
    ("FIR lag sakti hai kya?", "police_fir"),
    ("Police case hoga chart?", "police_fir"),
    ("Criminal case chart se?", "criminal_case"),
    ("498a case chart?", "criminal_case"),
    ("Civil case chart se?", "civil_litigation"),
    ("Consumer court case chart?", "civil_litigation"),
    ("Legal problem chart se?", "legal_obstacles"),
    ("Kanooni pareshani chart?", "legal_obstacles"),
    ("Dushman case chart se?", "enemy_case"),
    ("Enemy case chart?", "enemy_case"),
    ("Acquittal hoga kya chart?", "acquittal_relief"),
    ("Case dismiss chart se?", "acquittal_relief"),
    ("Advocate sahi milega chart?", "lawyer_support"),
    ("Vakil support chart se?", "lawyer_support"),
    ("Family court case chart?", "family_court"),
    ("Custody case chart se?", "family_court"),
    ("Court case chart reading?", "general_litigation"),
    ("Legal chart summary?", "general_litigation"),
]


class LitigationEngineTests(unittest.TestCase):
    def test_all_archetypes_defined(self):
        self.assertEqual(len(LITIGATION_ARCHETYPES), 15)

    def test_remedy_routing(self):
        q = "Court case ka upay kya hai?"
        self.assertTrue(is_litigation_static_question(q))
        self.assertEqual(classify_litigation_archetype(q), "litigation_remedy")

    def test_remedy_block_attached(self):
        from ask_litigation.remedy import is_litigation_remedy_question

        q = "Mukadma se bachne ka upay chart se?"
        self.assertTrue(is_litigation_remedy_question(q))
        res = run_litigation_static_engine(SAMPLE_KUNDLI, q)
        self.assertTrue((res.checks or {}).get("remedy_available"))
        self.assertTrue((res.checks or {}).get("remedy_text"))
        self.assertIn("practical", (res.checks or {}).get("remedy_text", "").lower())

    def test_non_remedy_no_block(self):
        q = "Court case hoga kya?"
        res = run_litigation_static_engine(SAMPLE_KUNDLI, q)
        self.assertFalse((res.checks or {}).get("remedy_available"))

    def test_routing_matrix(self):
        for q, expected in ROUTING_MATRIX:
            with self.subTest(q=q, expected=expected):
                self.assertTrue(is_litigation_static_question(q), msg=q)
                self.assertEqual(classify_litigation_archetype(q), expected, msg=q)

    def test_all_archetypes_emit_evidence(self):
        seen = set()
        for q, expected in ROUTING_MATRIX:
            res = run_litigation_static_engine(SAMPLE_KUNDLI, q)
            seen.add(res.archetype)
            self.assertEqual(res.archetype, expected, msg=q)
            self.assertGreaterEqual(len(res.evidence), 6, msg=q)
            ev_blob = " ".join(res.evidence)
            self.assertRegex(ev_blob, r"6th|6H|8th|8H|12th|12H|Mars|Saturn|Rahu", msg=q)
            self.assertNotRegex(res.verdict or "", r"jail\s+yog", msg=q)
            self.assertTrue(res.verdict, msg=q)
        self.assertEqual(seen, set(a for _, a in ROUTING_MATRIX))

    def test_property_court_stays_property(self):
        q = "Property court case chart se?"
        self.assertTrue(is_property_court_question(q))
        self.assertFalse(is_litigation_static_question(q))
        self.assertTrue(is_property_static_question(q))
        self.assertEqual(classify_property_archetype(q), "property_dispute")

    def test_police_job_stays_career(self):
        q = "Police job milegi chart se?"
        self.assertTrue(is_career_police_job_question(q))
        self.assertFalse(is_litigation_static_question(q))
        self.assertTrue(is_career_static_question(q))
        self.assertEqual(classify_career_archetype(q), "govt_job")

    def test_death_penalty_not_static(self):
        q = "Death penalty hoga kya chart?"
        self.assertTrue(is_death_penalty_crisis_question(q))
        self.assertFalse(is_litigation_static_question(q))

    def test_timing_not_litigation_static(self):
        self.assertFalse(is_litigation_static_question("Case kab khatam hoga?"))

    def test_answer_guard_blocks_fear_language(self):
        text, guard = guard_litigation_answer(
            "Jail hoga kya?",
            "Aapka jail yog strong hai aur pakka andar jayenge.",
            {},
        )
        self.assertTrue(guard.get("repaired"))
        self.assertNotRegex(text, r"jail\s+yog")
        self.assertNotRegex(text, r"pakka\s+andar")


if __name__ == "__main__":
    unittest.main()

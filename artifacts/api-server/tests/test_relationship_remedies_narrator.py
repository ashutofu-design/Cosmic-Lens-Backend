"""Relationship remedies narrator — intent-anchored template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_relationship_remedies_angle
from ask_mr.relationship_remedies_templates import detect_relationship_remedies_answer_focus, get_opening
from ask_mr.relationship_remedies_narrator import (
    engine_result_to_relationship_remedies_json,
    render_relationship_remedies_template_answer,
    relationship_remedies_engine_narrator_payload,
    validate_relationship_remedies_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.relationship_remedies import run_relationship_remedies_v2

SAMPLE_KUNDLI = {
    "ascendant": "Scorpio",
    "planets": [
        {"name": "Mars", "sign": "Aries", "house": 7},
        {"name": "Rahu", "sign": "Gemini", "house": 7},
        {"name": "Moon", "sign": "Capricorn", "house": 8},
        {"name": "Venus", "sign": "Taurus", "house": 12},
        {"name": "Saturn", "sign": "Aquarius", "house": 5},
        {"name": "Jupiter", "sign": "Pisces", "house": 6},
    ],
    "dasha": {"mahadasha": "Mars", "antardasha": "Rahu"},
}

GOLDEN_QUESTIONS = [
    ("Love relationship ke liye koi upay batao", "love_harmony"),
    ("Rishta strong karne ka mantra upay?", "mantra_upay"),
    ("Relationship me harmony ke liye kya upay hai?", "love_harmony"),
    ("Shaadi ke liye koi remedy batao", "marriage_remedy"),
    ("Partner se jhagda kam karne ka upay?", "friction_fix"),
    ("Koi totka hai relationship ke liye?", "puja_totka"),
    ("Mantra jap se rishta improve hoga?", "mantra_upay"),
    ("Love life ke liye puja upay?", "puja_totka"),
    ("Relationship problem solve karne ka upay?", "friction_fix"),
    ("Kya gemstone se love strong hota hai?", "gemstone_query"),
    ("Pyar pane ke liye daan seva kya karein?", "daan_seva"),
    ("Marriage delay ke liye upay kya hai?", "marriage_remedy"),
    ("Rishta thik karne ka koi mantra?", "mantra_upay"),
    ("Relationship tension door karne ka remedy?", "friction_fix"),
    ("Koi simple upay batao love ke liye", "love_harmony"),
    ("Puja path se relationship improve?", "puja_totka"),
    ("Neelam ya pukhraj relationship ke liye?", "gemstone_query"),
    ("Vivah yog ke liye remedy?", "marriage_remedy"),
    ("Rishta bachane ka upay kya hai?", "friction_fix"),
    ("General relationship remedy kya hai?", "general_remedy"),
]

REM_Q = "Love relationship ke liye koi upay batao"


class RelationshipRemediesNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_relationship_remedies_v2(SAMPLE_KUNDLI, REM_Q)
        self.result = v2_to_engine_result(self.out)

    def test_rem_json_shape(self):
        data = engine_result_to_relationship_remedies_json(self.result, question=REM_Q)
        self.assertEqual(data["question_type"], "relationship_remedies")
        self.assertIn(data["final_verdict"], ("Supportive", "Moderate", "Cautious", "Limited"))

    def test_love_harmony_angle(self):
        data = engine_result_to_relationship_remedies_json(self.result, question=REM_Q)
        self.assertEqual(data.get("answer_focus"), "love_harmony")

    def test_limited_not_supportive_praise(self):
        data = engine_result_to_relationship_remedies_json(self.result, question=REM_Q)
        data["remedy_level"] = "limited"
        data["relationship_remedies_level"] = "limited"
        data["direct_answer"] = get_opening("love_harmony", "limited")
        text = render_relationship_remedies_template_answer(data, REM_Q)
        self.assertNotRegex(text, r"(?i)mostly\s+supportive|gentle\s+upay\s*\+\s*daily\s+habit")

    def test_locked_template_valid(self):
        data = engine_result_to_relationship_remedies_json(self.result, question=REM_Q)
        ok, issues = validate_relationship_remedies_narrator_output(data.get("locked_template") or "", data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_no_chart(self):
        payload = relationship_remedies_engine_narrator_payload(self.result, question=REM_Q)
        parsed = json.loads(payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip())
        self.assertNotIn("ascendant", json.dumps(parsed).lower())

    def test_dna_bucket_mantra(self):
        dna = {"questions": [{"bucket": "relationship_remedies", "intent": "mantra upay"}]}
        angle = detect_relationship_remedies_answer_focus(
            "kya upay hai", question_dna=dna
        )
        self.assertEqual(angle, "mantra_upay")


class RelationshipRemediesGoldenTests(unittest.TestCase):
    def test_golden_angles(self):
        failures = []
        for q, exp in GOLDEN_QUESTIONS:
            got = infer_relationship_remedies_angle(q)
            if got != exp:
                failures.append(f"{q!r}: expected {exp}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_render_golden_batch(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for q, _ in GOLDEN_QUESTIONS[:10]:
            out = run_relationship_remedies_v2(SAMPLE_KUNDLI, q)
            data = engine_result_to_relationship_remedies_json(v2_to_engine_result(out), question=q)
            text = render_relationship_remedies_template_answer(data, q)
            ok, issues = validate_relationship_remedies_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{q}: {issues}")


if __name__ == "__main__":
    unittest.main()

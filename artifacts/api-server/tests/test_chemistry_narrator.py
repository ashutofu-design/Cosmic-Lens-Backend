"""Chemistry narrator — intent-anchored template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_chemistry_angle
from ask_mr.chemistry_templates import detect_chemistry_answer_focus, get_opening
from ask_mr.chemistry_narrator import (
    engine_result_to_chemistry_json,
    render_chemistry_template_answer,
    chemistry_engine_narrator_payload,
    validate_chemistry_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.chemistry import run_chemistry_v2

SAMPLE_KUNDLI = {
    "ascendant": "Scorpio",
    "planets": [
        {"name": "Mars", "sign": "Aries", "house": 7},
        {"name": "Rahu", "sign": "Gemini", "house": 7},
        {"name": "Moon", "sign": "Capricorn", "house": 8},
        {"name": "Venus", "sign": "Taurus", "house": 12},
        {"name": "Saturn", "sign": "Aquarius", "house": 5},
    ],
    "dasha": {"mahadasha": "Mars", "antardasha": "Rahu"},
}

GOLDEN_QUESTIONS = [
    ("Hamari chemistry kaisi rahegi?", "dyad_chemistry"),
    ("Hum dono ke beech chemistry kaisi dikhti hai?", "dyad_chemistry"),
    ("Hamare beech spark rahega kya?", "dyad_chemistry"),
    ("Dono ke beech chemistry normal ya intense?", "dyad_chemistry"),
    ("Physical attraction strong rahega kya?", "physical_attraction"),
    ("Physical chemistry strong hai kya?", "physical_attraction"),
    ("Hamari physical attraction zyada hai?", "physical_attraction"),
    ("Passion intense rahega kya?", "passion_intensity"),
    ("Intense passion develop hoga kya?", "passion_intensity"),
    ("Passion marriage me survive karega?", "passion_intensity"),
    ("Romance aur spark marriage mein rahega?", "romance_spark"),
    ("Romantic connection strong rahegi kya?", "romance_spark"),
    ("Romance fade ho jayegi kya?", "romance_spark"),
    ("Kya hamari chemistry strong hai?", "spark_strength"),
    ("Spark strong rahega kya marriage me?", "spark_strength"),
    ("Meri attraction pattern kaisi hai?", "native_attraction"),
    ("Mera romantic pull chart me kaisa hai?", "native_attraction"),
    ("Attraction level kya hai hamari?", "attraction_level"),
    ("Chemistry level chart me kya dikhta hai?", "attraction_level"),
    ("Overall chemistry pattern kaisa hai?", "general_chemistry"),
]

CHEM_Q = "Hamari chemistry kaisi rahegi?"


class ChemistryNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_chemistry_v2(SAMPLE_KUNDLI, CHEM_Q)
        self.result = v2_to_engine_result(self.out)

    def test_chem_json_shape(self):
        data = engine_result_to_chemistry_json(self.result, question=CHEM_Q)
        self.assertEqual(data["question_type"], "chemistry")
        self.assertIn(data["final_verdict"], ("Strong", "Moderate", "Uneven", "Low"))

    def test_dyad_chemistry_angle(self):
        data = engine_result_to_chemistry_json(self.result, question=CHEM_Q)
        self.assertEqual(data.get("answer_focus"), "dyad_chemistry")

    def test_low_not_strong_praise(self):
        data = engine_result_to_chemistry_json(self.result, question=CHEM_Q)
        data["chemistry_level"] = "low"
        data["chem_level"] = "low"
        data["direct_answer"] = get_opening("dyad_chemistry", "low")
        text = render_chemistry_template_answer(data, CHEM_Q)
        self.assertNotRegex(text, r"(?i)mostly\s+strong|spark\s+active")

    def test_locked_template_valid(self):
        data = engine_result_to_chemistry_json(self.result, question=CHEM_Q)
        ok, issues = validate_chemistry_narrator_output(data.get("locked_template") or "", data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_no_chart(self):
        payload = chemistry_engine_narrator_payload(self.result, question=CHEM_Q)
        parsed = json.loads(payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip())
        self.assertNotIn("ascendant", json.dumps(parsed).lower())

    def test_dna_bucket_physical(self):
        dna = {"questions": [{"bucket": "chemistry", "intent": "physical pull"}]}
        angle = detect_chemistry_answer_focus("physical spark between us", question_dna=dna)
        self.assertEqual(angle, "physical_attraction")


class ChemistryGoldenTests(unittest.TestCase):
    def test_golden_angles(self):
        failures = []
        for q, exp in GOLDEN_QUESTIONS:
            got = infer_chemistry_angle(q)
            if got != exp:
                failures.append(f"{q!r}: expected {exp}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_render_golden_batch(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for q, _ in GOLDEN_QUESTIONS[:10]:
            out = run_chemistry_v2(SAMPLE_KUNDLI, q)
            data = engine_result_to_chemistry_json(v2_to_engine_result(out), question=q)
            text = render_chemistry_template_answer(data, q)
            ok, issues = validate_chemistry_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{q}: {issues}")


if __name__ == "__main__":
    unittest.main()

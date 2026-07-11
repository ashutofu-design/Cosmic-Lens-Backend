"""Family approval narrator — intent-anchored template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_family_approval_angle
from ask_mr.family_approval_templates import detect_family_approval_answer_focus, get_opening
from ask_mr.family_approval_narrator import (
    engine_result_to_family_approval_json,
    family_approval_engine_narrator_payload,
    render_family_approval_template_answer,
    validate_family_approval_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.family_approval import run_family_approval_v2

SAMPLE_KUNDLI = {
    "ascendant": "Leo",
    "planets": [
        {"name": "Sun", "sign": "Leo", "house": 1},
        {"name": "Moon", "sign": "Taurus", "house": 10},
        {"name": "Jupiter", "sign": "Sagittarius", "house": 5},
        {"name": "Rahu", "sign": "Gemini", "house": 11},
        {"name": "Saturn", "sign": "Capricorn", "house": 6},
    ],
    "dasha": {"mahadasha": "Jupiter", "antardasha": "Saturn"},
}

GOLDEN_QUESTIONS = [
    ("Ghar wale meri shaadi ke liye maanenge kya?", "parents_approval"),
    ("Intercaste marriage mein family approval milega?", "inter_caste"),
    ("Parents meri pasand ko accept karenge?", "accept_partner"),
    ("Inter religion marriage family accept karegi?", "inter_religion"),
    ("Court marriage me family approval milega?", "court_marriage"),
    ("Family involvement kitna hoga shaadi me?", "family_involvement"),
    ("Ghar walon ka role kya hoga?", "family_involvement"),
    ("Family approval chances kya hain?", "general_approval"),
    ("Parents is rishte ke liye raazi honge?", "parents_approval"),
    ("Inter-caste shaadi me ghar wale maan jayenge?", "inter_caste"),
    ("Society me recognition milega rishte ko?", "societal_recognition"),
    ("Family resistance strong hogi kya?", "family_resistance"),
    ("Saas sasur approval milegi?", "in_laws_approval"),
    ("Ghar wale partner ko accept karenge?", "accept_partner"),
    ("Family pressure zyada hoga kya?", "family_pressure"),
    ("Elders meri choice accept karenge?", "accept_partner"),
    ("Parents approval for love marriage?", "parents_approval"),
    ("Intercaste rishte me family support?", "inter_caste"),
    ("Ghar walon se approval mushkil hogi?", "family_resistance"),
    ("Family maan jayegi ya nahi?", "general_approval"),
]

FA_Q = "Ghar wale meri shaadi ke liye maanenge kya?"


class FamilyApprovalNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_family_approval_v2(SAMPLE_KUNDLI, FA_Q)
        self.result = v2_to_engine_result(self.out)

    def test_fa_json_shape(self):
        data = engine_result_to_family_approval_json(self.result, question=FA_Q)
        self.assertEqual(data["question_type"], "family_approval")
        self.assertIn(data["final_verdict"], ("Supportive", "Mixed", "Resistant", "Unlikely"))

    def test_parents_approval_angle(self):
        data = engine_result_to_family_approval_json(self.result, question=FA_Q)
        self.assertEqual(data.get("answer_focus"), "parents_approval")

    def test_unlikely_not_supportive_praise(self):
        data = engine_result_to_family_approval_json(self.result, question=FA_Q)
        data["family_approval_level"] = "unlikely"
        data["direct_answer"] = get_opening("parents_approval", "unlikely")
        text = render_family_approval_template_answer(data, FA_Q)
        self.assertNotRegex(text, r"(?i)mostly\s+supportive|easy\s+approval")

    def test_locked_template_valid(self):
        data = engine_result_to_family_approval_json(self.result, question=FA_Q)
        ok, issues = validate_family_approval_narrator_output(data.get("locked_template") or "", data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_no_chart(self):
        payload = family_approval_engine_narrator_payload(self.result, question=FA_Q)
        parsed = json.loads(payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip())
        self.assertNotIn("ascendant", json.dumps(parsed).lower())

    def test_dna_bucket_intercaste(self):
        dna = {"questions": [{"bucket": "family_approval", "intent": "intercaste approval"}]}
        angle = detect_family_approval_answer_focus("intercaste marriage family", question_dna=dna)
        self.assertEqual(angle, "inter_caste")


class FamilyApprovalGoldenTests(unittest.TestCase):
    def test_golden_angles(self):
        failures = []
        for q, exp in GOLDEN_QUESTIONS:
            got = infer_family_approval_angle(q)
            if got != exp:
                failures.append(f"{q!r}: expected {exp}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_render_golden_batch(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for q, _ in GOLDEN_QUESTIONS[:10]:
            out = run_family_approval_v2(SAMPLE_KUNDLI, q)
            data = engine_result_to_family_approval_json(v2_to_engine_result(out), question=q)
            text = render_family_approval_template_answer(data, q)
            ok, issues = validate_family_approval_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{q}: {issues}")


if __name__ == "__main__":
    unittest.main()

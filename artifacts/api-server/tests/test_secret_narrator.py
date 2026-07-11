"""Secret relationship narrator — intent-anchored template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_secret_angle
from ask_mr.secret_templates import OPENING_TEMPLATES, detect_secret_answer_focus, effects_from_evidence, get_opening
from ask_mr.secret_narrator import (
    engine_result_to_secret_json,
    render_secret_template_answer,
    secret_narrator_payload,
    validate_secret_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.secret_relationship import run_secret_relationship_v2

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Venus", "sign": "Leo", "house": 12},
        {"name": "Rahu", "sign": "Cancer", "house": 7},
        {"name": "Mars", "sign": "Capricorn", "house": 5},
    ],
    "dasha": {"mahadasha": "Rahu", "antardasha": "Mars"},
}

GOLDEN_QUESTIONS = [
    ("kya chupke rishta chal raha hai", "chupke_rishta"),
    ("kya chhupa rishta hai", "chupke_rishta"),
    ("kya partner ka secret affair hai", "secret_affair"),
    ("kya chakkar chal raha hai", "secret_affair"),
    ("kya parallel attention hai", "parallel_attention"),
    ("kya do rishte chal rahe hain", "multiple_relationships"),
    ("kya multiple relationship pattern hai", "multiple_relationships"),
    ("kya partner chupke mil raha hai", "hidden_behavior"),
    ("kya hidden relationship hai", "chupke_rishta"),
    ("kya third person risk hai", "third_person_risk"),
    ("kya secret relationship ka yog hai", "general_secrecy"),
    ("kya partner secretly dating karta hai", "hidden_behavior"),
    ("kya parallel rishta hai", "parallel_attention"),
    ("kya chhipa affair hai", "secret_affair"),
    ("kya secrecy pattern active hai", "general_secrecy"),
    ("kya teesra factor hai rishte mein", "third_person_risk"),
    ("kya partner chipka hua hai kisi aur secretly", "hidden_behavior"),
    ("kya double dating chal rahi hai", "multiple_relationships"),
    ("kya hidden affair pattern hai", "parallel_attention"),
    ("kya dusra rishta chhupa hai", "parallel_attention"),
]

SECRET_Q = "kya chupke rishta chal raha hai"


class SecretNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_secret_relationship_v2(SAMPLE_KUNDLI, SECRET_Q)
        self.result = v2_to_engine_result(self.out)

    def test_secret_json_shape(self):
        data = engine_result_to_secret_json(self.result, question=SECRET_Q)
        self.assertEqual(data["question_type"], "secret_relationship")
        self.assertIn(data["final_verdict"], ("Low", "Possible", "Likely", "High"))

    def test_chupke_angle(self):
        data = engine_result_to_secret_json(self.result, question=SECRET_Q)
        self.assertEqual(data.get("answer_focus"), "chupke_rishta")

    def test_high_not_low_risk_language(self):
        data = engine_result_to_secret_json(self.result, question=SECRET_Q)
        data["secret_level"] = "high"
        data["direct_answer"] = get_opening("chupke_rishta", "high")
        text = render_secret_template_answer(data, SECRET_Q)
        self.assertNotRegex(text, r"(?i)pakka\s+affair|the\s+big\s+picture")
        self.assertRegex(text, r"(?i)high-risk|secrecy")

    def test_locked_template_valid(self):
        data = engine_result_to_secret_json(self.result, question=SECRET_Q)
        ok, issues = validate_secret_narrator_output(data.get("locked_template") or "", data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_no_chart(self):
        payload = secret_narrator_payload(self.result, question=SECRET_Q)
        parsed = json.loads(payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip())
        self.assertNotIn("ascendant", json.dumps(parsed).lower())

    def test_render_no_chart_jargon(self):
        data = engine_result_to_secret_json(self.result, question=SECRET_Q)
        data["weakest"] = ["D1 relationship axis shows friction"]
        data["weakest_effects"] = effects_from_evidence(data["weakest"], limit=2)
        text = render_secret_template_answer(data, SECRET_Q)
        self.assertNotRegex(text, r"(?i)\bd1\b|relationship\s+axis")


class SecretGoldenTests(unittest.TestCase):
    def test_golden_angles(self):
        failures = []
        for q, exp in GOLDEN_QUESTIONS:
            got = infer_secret_angle(q)
            if got != exp:
                failures.append(f"{q!r}: expected {exp}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_d1_evidence_humanized(self):
        from ask_mr.secret_templates import secret_evidence_to_effect

        eff = secret_evidence_to_effect("D1 relationship axis shows friction")
        self.assertNotIn("D1", eff)
        self.assertNotIn("axis", eff.lower())

    def test_render_golden_batch(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for q, _ in GOLDEN_QUESTIONS[:8]:
            out = run_secret_relationship_v2(SAMPLE_KUNDLI, q)
            data = engine_result_to_secret_json(v2_to_engine_result(out), question=q)
            text = render_secret_template_answer(data, q)
            self.assertNotIn("Asli wajah seedhi hai", text)
            self.assertNotIn("Jo mukhya sanket", text)
            self.assertNotRegex(text, r"(?i)\bd1\b|relationship\s+axis")
            self.assertRegex(text, r"(?i)confidence")

    def test_each_angle_has_levels(self):
        for angle in OPENING_TEMPLATES:
            for lv in ("low", "possible", "likely", "high"):
                self.assertTrue(get_opening(angle, lv))


if __name__ == "__main__":
    unittest.main()

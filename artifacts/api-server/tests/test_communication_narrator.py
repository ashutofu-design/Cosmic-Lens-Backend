"""Communication narrator — intent-anchored template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_communication_angle
from ask_mr.communication_templates import detect_communication_answer_focus, get_opening
from ask_mr.communication_narrator import (
    communication_engine_narrator_payload,
    engine_result_to_communication_json,
    render_communication_template_answer,
    validate_communication_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.communication import run_communication_v2

SAMPLE_KUNDLI = {
    "ascendant": "Gemini",
    "planets": [
        {"name": "Mercury", "sign": "Virgo", "house": 3},
        {"name": "Moon", "sign": "Cancer", "house": 4},
        {"name": "Venus", "sign": "Libra", "house": 5},
        {"name": "Mars", "sign": "Aries", "house": 11},
        {"name": "Saturn", "sign": "Capricorn", "house": 7},
    ],
    "dasha": {"mahadasha": "Mercury", "antardasha": "Venus"},
}

GOLDEN_QUESTIONS = [
    ("Kya hamari relationship me communication problem hai?", "communication_gap"),
    ("Partner mujhe samajh payega ya nahi?", "understanding_partner"),
    ("Partner silent rehta hai baat nahi karta?", "silence"),
    ("Kya partner mujhe sunta hai?", "listening"),
    ("Misunderstanding hoti hai kya humari?", "misunderstanding"),
    ("Jhagda zyada hota hai kya?", "arguments"),
    ("Relationship me baat cheet kaisi rahegi?", "general_communication"),
    ("Partner feelings express karta hai?", "express_feelings"),
    ("WhatsApp pe communication kaisi hogi?", "texting_style"),
    ("Conflict resolve hota hai ya nahi?", "conflict_resolution"),
    ("Seedhi honest baat hoti hai kya?", "honest_talk"),
    ("Partner baat se bachta hai?", "avoid_talk"),
    ("Partner ka tone harsh hai kya?", "tone_style"),
    ("Galatfehmi hoti hai baar baar?", "misunderstanding"),
    ("Khamoshi zyada rehti hai relationship me?", "silence"),
    ("Partner mujhe samjhega emotional baat pe?", "understanding_partner"),
    ("Communication gap hai hamare beech?", "communication_gap"),
    ("Ladai ke baad baat hoti hai?", "conflict_resolution"),
    ("Texting style match karega?", "texting_style"),
    ("Rishte me baat cheet theek hai?", "general_communication"),
]

COMM_Q = "Relationship me baat cheet kaisi rahegi?"


class CommunicationNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_communication_v2(SAMPLE_KUNDLI, COMM_Q)
        self.result = v2_to_engine_result(self.out)

    def test_comm_json_shape(self):
        data = engine_result_to_communication_json(self.result, question=COMM_Q)
        self.assertEqual(data["question_type"], "communication")
        self.assertIn(data["final_verdict"], ("Clear", "Uneven", "Strained", "Blocked"))

    def test_general_comm_angle(self):
        data = engine_result_to_communication_json(self.result, question=COMM_Q)
        self.assertEqual(data.get("answer_focus"), "general_communication")

    def test_blocked_not_clear_praise(self):
        data = engine_result_to_communication_json(self.result, question=COMM_Q)
        data["communication_level"] = "blocked"
        data["direct_answer"] = get_opening("general_communication", "blocked")
        text = render_communication_template_answer(data, COMM_Q)
        self.assertNotRegex(text, r"(?i)mostly\s+clear|smooth\s+talk")

    def test_locked_template_valid(self):
        data = engine_result_to_communication_json(self.result, question=COMM_Q)
        ok, issues = validate_communication_narrator_output(data.get("locked_template") or "", data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_no_chart(self):
        payload = communication_engine_narrator_payload(self.result, question=COMM_Q)
        parsed = json.loads(payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip())
        self.assertNotIn("ascendant", json.dumps(parsed).lower())

    def test_dna_bucket_silence(self):
        dna = {"questions": [{"bucket": "communication", "intent": "partner silence"}]}
        angle = detect_communication_answer_focus("partner silent hai baat nahi", question_dna=dna)
        self.assertEqual(angle, "silence")


class CommunicationGoldenTests(unittest.TestCase):
    def test_golden_angles(self):
        failures = []
        for q, exp in GOLDEN_QUESTIONS:
            got = infer_communication_angle(q)
            if got != exp:
                failures.append(f"{q!r}: expected {exp}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_render_golden_batch(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for q, _ in GOLDEN_QUESTIONS[:10]:
            out = run_communication_v2(SAMPLE_KUNDLI, q)
            data = engine_result_to_communication_json(v2_to_engine_result(out), question=q)
            text = render_communication_template_answer(data, q)
            ok, issues = validate_communication_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{q}: {issues}")


if __name__ == "__main__":
    unittest.main()

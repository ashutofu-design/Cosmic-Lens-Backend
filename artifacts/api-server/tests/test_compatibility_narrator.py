"""Compatibility narrator — intent-anchored, verdict-consistent template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_compatibility_angle
from ask_mr.compatibility_templates import (
    OPENING_TEMPLATES,
    detect_compatibility_answer_focus,
    get_opening,
)
from ask_mr.compatibility_narrator import (
    compatibility_narrator_payload,
    engine_result_to_compatibility_json,
    render_compatibility_template_answer,
    validate_compatibility_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.compatibility import run_compatibility_v2

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Jupiter", "sign": "Libra", "house": 11},
        {"name": "Mars", "sign": "Capricorn", "house": 7},
        {"name": "Mercury", "sign": "Virgo", "house": 10},
    ],
    "dasha": {"mahadasha": "Venus", "antardasha": "Mercury"},
}

GOLDEN_QUESTIONS: list[tuple[str, str]] = [
    ("Kya hum dono compatible hain?", "general_compatibility"),
    ("kya hum compatible hain", "general_compatibility"),
    ("Kya hum emotionally compatible hain?", "emotional_compatibility"),
    ("Kya hum mentally compatible hain?", "mental_compatibility"),
    ("Kya hum intellectually compatible hain?", "intellectual_compatibility"),
    ("Kya hamari personalities match karti hain?", "personalities_match"),
    ("Kya hamari thinking match karti hai?", "thinking_match"),
    ("Kya hamare values same hain?", "values_match"),
    ("Kya hamare life goals match karte hain?", "life_goals_match"),
    ("Kya hamari expectations ek jaisi hain?", "expectations_match"),
    ("kya hamara gun milan achha hai", "gun_milan"),
    ("36 gun kitne match hote hain", "gun_milan"),
    ("kya hamari chemistry strong hai", "chemistry_match"),
    ("kya humara rishta achha match hai", "overall_match"),
    ("kya humara overall match sahi hai", "overall_match"),
    ("Marriage ke baad emotional compatibility kaisi rahegi?", "emotional_compatibility"),
    ("kya dimaag ka match hai humara", "mental_compatibility"),
    ("kya values align hain hamare", "values_match"),
    ("kya life goals same hain", "life_goals_match"),
    ("kya expectations match karti hain", "expectations_match"),
    ("kya personality match hai", "personalities_match"),
    ("kya soch match karti hai", "thinking_match"),
    ("kya intellectual match hai", "intellectual_compatibility"),
    ("kya guna milan theek hai", "gun_milan"),
    ("kya humara match strong hai", "general_compatibility"),
]

COMPAT_Q = "Kya hum dono compatible hain?"


class CompatibilityNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_compatibility_v2(SAMPLE_KUNDLI, COMPAT_Q)
        self.result = v2_to_engine_result(self.out)

    def test_compat_json_shape(self):
        data = engine_result_to_compatibility_json(self.result, question=COMPAT_Q)
        self.assertEqual(data["question_type"], "compatibility")
        self.assertIn("final_verdict", data)
        self.assertIn("compat_level", data)
        self.assertIn("strongest", data)
        self.assertIn("weakest", data)
        self.assertIn("confidence", data)
        self.assertIn(data["final_verdict"], ("Supportive", "Moderate", "Mixed", "Strained"))
        self.assertGreater(data["confidence"], 0)

    def test_general_compat_angle_detected(self):
        data = engine_result_to_compatibility_json(self.result, question=COMPAT_Q)
        self.assertEqual(data.get("answer_focus"), "general_compatibility")

    def test_strained_opening_not_perfect_match(self):
        data = engine_result_to_compatibility_json(self.result, question=COMPAT_Q)
        data["compat_level"] = "strained"
        data["final_verdict"] = "Strained"
        data["direct_answer"] = get_opening("general_compatibility", "strained")
        text = render_compatibility_template_answer(data, COMPAT_Q)
        self.assertNotRegex(text, r"(?i)perfect\s+match|the\s+big\s+picture|100%\s+compatible")
        self.assertRegex(text, r"(?i)strained|effort")

    def test_locked_template_has_evidence_sections(self):
        data = engine_result_to_compatibility_json(self.result, question=COMPAT_Q)
        text = data.get("locked_template") or render_compatibility_template_answer(data, COMPAT_Q)
        self.assertIn("mukhya sanket", text.lower())
        self.assertIn("dhyan dene layak", text.lower())
        self.assertIn("bond growth", text.lower())
        self.assertNotIn("clarity", text.lower())
        self.assertRegex(text, r"Confidence\s+\w+\s*\(\d+%\)")

    def test_validate_rejects_contradiction(self):
        data = engine_result_to_compatibility_json(self.result, question=COMPAT_Q)
        data["compat_level"] = "strained"
        bad = "Perfect match hai humara — strong compatibility supportive dikhti hai. Confidence Low (38%) test."
        ok, issues = validate_compatibility_narrator_output(bad, data)
        self.assertFalse(ok)
        self.assertTrue(any("contradiction" in i or "banned" in i for i in issues))

    def test_validate_accepts_locked_template(self):
        data = engine_result_to_compatibility_json(self.result, question=COMPAT_Q)
        text = data.get("locked_template") or ""
        ok, issues = validate_compatibility_narrator_output(text, data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_json_no_chart_fields(self):
        payload = compatibility_narrator_payload(self.result, question=COMPAT_Q)
        self.assertIn("ENGINE_JSON:", payload)
        self.assertIn("SOURCE_LOCK", payload)
        json_text = payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip()
        parsed = json.loads(json_text)
        blob = json.dumps(parsed, ensure_ascii=False).lower()
        self.assertNotIn("ascendant", blob)
        self.assertNotIn("kundli", blob)
        self.assertIn("strongest", parsed)

    def test_dna_bucket_gun_milan(self):
        dna = {"questions": [{"bucket": "compatibility", "intent": "gun milan score"}]}
        angle = detect_compatibility_answer_focus("kya hum compatible hain gun milan", question_dna=dna)
        self.assertEqual(angle, "gun_milan")


class CompatibilityGoldenAngleTests(unittest.TestCase):
    def test_golden_angle_detection(self):
        failures: list[str] = []
        for question, expected in GOLDEN_QUESTIONS:
            got = infer_compatibility_angle(question)
            if got != expected:
                failures.append(f"{question!r}: expected {expected}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_each_angle_has_all_levels(self):
        for angle in OPENING_TEMPLATES:
            for level in ("supportive", "moderate", "mixed", "strained"):
                opening = get_opening(angle, level)
                self.assertTrue(opening, msg=f"missing {angle}/{level}")
                self.assertNotRegex(opening, r"(?i)the\s+big\s+picture|perfect\s+match")

    def test_golden_questions_render_without_crash(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for question, _expected in GOLDEN_QUESTIONS[:12]:
            out = run_compatibility_v2(SAMPLE_KUNDLI, question)
            result = v2_to_engine_result(out)
            data = engine_result_to_compatibility_json(result, question=question)
            text = render_compatibility_template_answer(data, question)
            self.assertGreater(len(text), 80, msg=question)
            self.assertNotIn("The Big Picture", text)
            ok, issues = validate_compatibility_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{question}: {issues}")

    def test_supportive_opening_not_alarmist(self):
        opening = get_opening("emotional_compatibility", "supportive")
        self.assertNotRegex(opening, r"(?i)strained|major\s+friction")
        self.assertRegex(opening, r"(?i)supportive|caring|depth")

    def test_gun_milan_angle(self):
        q = "kya hamara gun milan achha hai"
        self.assertEqual(infer_compatibility_angle(q), "gun_milan")


if __name__ == "__main__":
    unittest.main()

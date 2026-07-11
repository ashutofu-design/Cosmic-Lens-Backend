"""Breakup / separation risk narrator — intent-anchored, verdict-consistent template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_breakup_angle
from ask_mr.breakup_templates import (
    OPENING_TEMPLATES,
    detect_breakup_answer_focus,
    get_opening,
)
from ask_mr.breakup_narrator import (
    breakup_narrator_payload,
    engine_result_to_breakup_json,
    render_breakup_template_answer,
    validate_breakup_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.breakup_risk import run_breakup_risk_v2

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Mars", "sign": "Capricorn", "house": 7},
        {"name": "Saturn", "sign": "Aries", "house": 7},
        {"name": "Rahu", "sign": "Cancer", "house": 8},
    ],
    "dasha": {"mahadasha": "Saturn", "antardasha": "Mars"},
}

GOLDEN_QUESTIONS: list[tuple[str, str]] = [
    ("kya mera breakup hoga", "will_breakup"),
    ("kya rishta toot jayega", "will_breakup"),
    ("kya relationship end ho jayegi", "will_breakup"),
    ("kya breakup kyun ho raha hai", "breakup_cause"),
    ("breakup ka reason kya hai", "breakup_cause"),
    ("kyun rishta toot raha hai", "breakup_cause"),
    ("kya divorce hoga", "divorce_risk"),
    ("kya talak ho sakta hai", "divorce_risk"),
    ("kya husband divorce karega", "divorce_risk"),
    ("kya pati alag ho jayega", "separation_risk"),
    ("kya hum alag ho jayenge", "separation_risk"),
    ("kya separation hoga", "separation_risk"),
    ("kab breakup hoga", "breakup_timing"),
    ("breakup kab hoga timing", "breakup_timing"),
    ("kya breakup bacha sakte hain", "avoid_breakup"),
    ("kya rishta bach sakta hai", "avoid_breakup"),
    ("kya breakup se bach sakte hain", "avoid_breakup"),
    ("kya relationship survive karegi", "relationship_survive"),
    ("kya rishta chalega", "relationship_survive"),
    ("kya toxic relationship me breakup hoga", "toxic_breakup"),
    ("kya partner mujhe chhod dega", "partner_leave"),
    ("kya boyfriend leave karega", "partner_leave"),
    ("kya mera rishta tootega", "will_breakup"),
    ("divorce risk kya hai", "divorce_risk"),
    ("kya breakup ka chance hai", "will_breakup"),
]

BREAKUP_Q = "kya mera breakup hoga"


class BreakupNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_breakup_risk_v2(SAMPLE_KUNDLI, BREAKUP_Q)
        self.result = v2_to_engine_result(self.out)

    def test_breakup_json_shape(self):
        data = engine_result_to_breakup_json(self.result, question=BREAKUP_Q)
        self.assertEqual(data["question_type"], "breakup_risk")
        self.assertIn("final_verdict", data)
        self.assertIn("breakup_level", data)
        self.assertIn("strongest", data)
        self.assertIn("weakest", data)
        self.assertIn("confidence", data)
        self.assertIn(data["final_verdict"], ("Low risk", "Moderate risk", "Elevated risk", "High risk"))
        self.assertGreater(data["confidence"], 0)

    def test_will_breakup_angle_detected(self):
        data = engine_result_to_breakup_json(self.result, question=BREAKUP_Q)
        self.assertEqual(data.get("answer_focus"), "will_breakup")
        self.assertEqual(data.get("breakup_angle"), "will_breakup")

    def test_high_risk_opening_not_fatalistic(self):
        data = engine_result_to_breakup_json(self.result, question=BREAKUP_Q)
        data["breakup_level"] = "high"
        data["risk_level"] = "high"
        data["final_verdict"] = "High risk"
        data["direct_answer"] = get_opening("will_breakup", "high")
        text = render_breakup_template_answer(data, BREAKUP_Q)
        self.assertNotRegex(text, r"(?i)pakka\s+breakup|tootega\s+hi|the\s+big\s+picture")
        self.assertRegex(text, r"(?i)high-risk|repair")

    def test_locked_template_has_evidence_sections(self):
        data = engine_result_to_breakup_json(self.result, question=BREAKUP_Q)
        text = data.get("locked_template") or render_breakup_template_answer(data, BREAKUP_Q)
        self.assertIn("mukhya sanket", text.lower())
        self.assertIn("dhyan dene layak", text.lower())
        self.assertIn("repair / outlook", text.lower())
        self.assertNotIn("clarity", text.lower())
        self.assertRegex(text, r"Confidence\s+\w+\s*\(\d+%\)")

    def test_validate_rejects_fatalistic(self):
        data = engine_result_to_breakup_json(self.result, question=BREAKUP_Q)
        data["breakup_level"] = "high"
        bad = "Pakka breakup hoga rishta tootega hi. Confidence Low (32%) hai kyunki test."
        ok, issues = validate_breakup_narrator_output(bad, data)
        self.assertFalse(ok)
        self.assertTrue(any("fatalistic" in i or "banned" in i for i in issues))

    def test_validate_accepts_locked_template(self):
        data = engine_result_to_breakup_json(self.result, question=BREAKUP_Q)
        text = data.get("locked_template") or ""
        ok, issues = validate_breakup_narrator_output(text, data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_json_no_chart_fields(self):
        payload = breakup_narrator_payload(self.result, question=BREAKUP_Q)
        self.assertIn("ENGINE_JSON:", payload)
        self.assertIn("SOURCE_LOCK", payload)
        json_text = payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip()
        parsed = json.loads(json_text)
        blob = json.dumps(parsed, ensure_ascii=False).lower()
        self.assertNotIn("ascendant", blob)
        self.assertNotIn("kundli", blob)
        self.assertIn("strongest", parsed)

    def test_dna_bucket_overrides_general(self):
        dna = {"questions": [{"bucket": "breakup_separation", "intent": "breakup_risk"}]}
        angle = detect_breakup_answer_focus("kya rishta toot jayega", question_dna=dna)
        self.assertEqual(angle, "will_breakup")


class BreakupGoldenAngleTests(unittest.TestCase):
    def test_golden_angle_detection(self):
        failures: list[str] = []
        for question, expected in GOLDEN_QUESTIONS:
            got = infer_breakup_angle(question)
            if got != expected:
                failures.append(f"{question!r}: expected {expected}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_each_angle_has_all_levels(self):
        for angle, levels in OPENING_TEMPLATES.items():
            for level in ("low", "moderate", "elevated", "high"):
                opening = get_opening(angle, level)
                self.assertTrue(opening, msg=f"missing opening {angle}/{level}")
                self.assertNotRegex(opening, r"(?i)the\s+big\s+picture|tootega\s+hi|pakka\s+breakup")

    def test_golden_questions_render_without_crash(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for question, _expected in GOLDEN_QUESTIONS[:12]:
            out = run_breakup_risk_v2(SAMPLE_KUNDLI, question)
            result = v2_to_engine_result(out)
            data = engine_result_to_breakup_json(result, question=question)
            text = render_breakup_template_answer(data, question)
            self.assertGreater(len(text), 80, msg=question)
            self.assertNotIn("The Big Picture", text)
            self.assertNotRegex(text, r"(?i)tootega\s+hi|pakka\s+breakup")
            ok, issues = validate_breakup_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{question}: {issues}")

    def test_low_risk_opening_not_alarmist(self):
        opening = get_opening("will_breakup", "low")
        self.assertNotRegex(opening, r"(?i)high-risk|pakka|tootega")
        self.assertRegex(opening, r"(?i)low|repair|hold")

    def test_avoid_breakup_high_has_repair_hope(self):
        opening = get_opening("avoid_breakup", "high")
        self.assertRegex(opening, r"(?i)repair|effort|damage")
        self.assertNotRegex(opening, r"(?i)tootega\s+hi|pakka")

    def test_reconciliation_only_returns_none(self):
        self.assertIsNone(infer_breakup_angle("kya ex wapas aayega"))


if __name__ == "__main__":
    unittest.main()

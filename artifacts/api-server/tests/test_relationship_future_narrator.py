"""Relationship future narrator — intent-anchored template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_relationship_future_angle
from ask_mr.relationship_future_templates import detect_relationship_future_answer_focus, get_opening
from ask_mr.relationship_future_narrator import (
    engine_result_to_relationship_future_json,
    render_relationship_future_template_answer,
    relationship_future_engine_narrator_payload,
    validate_relationship_future_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.relationship_future import run_relationship_future_v2

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
    ("Hamare relationship ka future kaisa rahega?", "general_future"),
    ("Relationship aage grow karega ya weak hoga?", "growth_outlook"),
    ("Kya hamara relationship long-term chalega?", "long_term_stability"),
    ("Bond grow karega kya?", "growth_outlook"),
    ("Relationship weak ho jayega kya?", "weak_outlook"),
    ("Rishta aage kaise rahega?", "bond_direction"),
    ("Hamara relationship mature hoga kya?", "relationship_mature"),
    ("Kya ye relationship meri growth ke liye achha hai?", "personal_growth_impact"),
    ("Relationship sustain ho payega?", "long_term_stability"),
    ("Future outlook kaisa hai relationship ka?", "general_future"),
    ("Aage bond strong rahega kya?", "growth_outlook"),
    ("Long term me relationship tik payega?", "long_term_stability"),
    ("Rishta ka future promising hai kya?", "general_future"),
    ("Relationship ka direction kya hai?", "bond_direction"),
    ("Kya humara rishta aage badhega?", "growth_outlook"),
    ("Relationship end ho jayega kya?", "weak_outlook"),
    ("Hamare beech closeness badhegi kya?", "growth_outlook"),
    ("Relationship uncertain future dikhta hai?", "general_future"),
    ("Aage kya hoga hamari relationship me?", "bond_direction"),
    ("Overall relationship future strong hai?", "growth_outlook"),
]

RFUT_Q = "Hamare relationship ka future kaisa rahega?"


class RelationshipFutureNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_relationship_future_v2(SAMPLE_KUNDLI, RFUT_Q)
        self.result = v2_to_engine_result(self.out)

    def test_rfut_json_shape(self):
        data = engine_result_to_relationship_future_json(self.result, question=RFUT_Q)
        self.assertEqual(data["question_type"], "relationship_future")
        self.assertIn(data["final_verdict"], ("Promising", "Mixed", "Uncertain", "Weak"))

    def test_general_future_angle(self):
        data = engine_result_to_relationship_future_json(self.result, question=RFUT_Q)
        self.assertEqual(data.get("answer_focus"), "general_future")

    def test_weak_not_promising_praise(self):
        data = engine_result_to_relationship_future_json(self.result, question=RFUT_Q)
        data["future_level"] = "weak"
        data["relationship_future_level"] = "weak"
        data["direct_answer"] = get_opening("general_future", "weak")
        text = render_relationship_future_template_answer(data, RFUT_Q)
        self.assertNotRegex(text, r"(?i)mostly\s+promising|bond\s+deepen")

    def test_locked_template_valid(self):
        data = engine_result_to_relationship_future_json(self.result, question=RFUT_Q)
        ok, issues = validate_relationship_future_narrator_output(data.get("locked_template") or "", data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_no_chart(self):
        payload = relationship_future_engine_narrator_payload(self.result, question=RFUT_Q)
        parsed = json.loads(payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip())
        self.assertNotIn("ascendant", json.dumps(parsed).lower())

    def test_dna_bucket_long_term(self):
        dna = {"questions": [{"bucket": "relationship_future", "intent": "long-term stability"}]}
        angle = detect_relationship_future_answer_focus(
            "kya relationship chalega", question_dna=dna
        )
        self.assertEqual(angle, "long_term_stability")


class RelationshipFutureGoldenTests(unittest.TestCase):
    def test_golden_angles(self):
        failures = []
        for q, exp in GOLDEN_QUESTIONS:
            got = infer_relationship_future_angle(q)
            if got != exp:
                failures.append(f"{q!r}: expected {exp}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_render_golden_batch(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for q, _ in GOLDEN_QUESTIONS[:10]:
            out = run_relationship_future_v2(SAMPLE_KUNDLI, q)
            data = engine_result_to_relationship_future_json(v2_to_engine_result(out), question=q)
            text = render_relationship_future_template_answer(data, q)
            ok, issues = validate_relationship_future_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{q}: {issues}")


if __name__ == "__main__":
    unittest.main()

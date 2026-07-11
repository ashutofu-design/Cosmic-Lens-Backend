"""Relationship decisions narrator — intent-anchored template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_relationship_decisions_angle
from ask_mr.relationship_decisions_templates import detect_relationship_decisions_answer_focus, get_opening
from ask_mr.relationship_decisions_narrator import (
    engine_result_to_relationship_decisions_json,
    render_relationship_decisions_template_answer,
    relationship_decisions_engine_narrator_payload,
    validate_relationship_decisions_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.relationship_decisions import run_relationship_decisions_v2

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
    ("Kya mujhe is rishte me rehna chahiye ya chhod du?", "stay_or_leave"),
    ("Should I stay in this relationship?", "stay_continue"),
    ("Kya main relationship chhod du?", "leave_decision"),
    ("Kya ye relationship mere liye sahi hai?", "overall_suitability"),
    ("Overall kya ye rishta theek hai?", "overall_suitability"),
    ("Kya main is relationship me continue karu?", "stay_continue"),
    ("Second chance dena chahiye kya?", "second_chance"),
    ("Ek aur mauka dena sahi hoga?", "second_chance"),
    ("Kya main propose karu?", "move_forward"),
    ("Should I move on from this relationship?", "leave_decision"),
    ("Kya rishta nibhana chahiye?", "stay_continue"),
    ("Stay or leave — kya karna chahiye?", "stay_or_leave"),
    ("Kya main breakup karu?", "leave_decision"),
    ("Relationship me rahun ya alag ho jaaun?", "stay_or_leave"),
    ("Kya ye partner mere liye right fit hai?", "overall_suitability"),
    ("Aage badhna chahiye relationship me?", "move_forward"),
    ("Kya main try again karu?", "second_chance"),
    ("Decision kya hai — continue ya end?", "stay_or_leave"),
    ("Kya mujhe move forward karna chahiye?", "move_forward"),
    ("Kya main is rishte me rahun?", "stay_continue"),
]

RDEC_Q = "Kya mujhe is rishte me rehna chahiye ya chhod du?"


class RelationshipDecisionsNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_relationship_decisions_v2(SAMPLE_KUNDLI, RDEC_Q)
        self.result = v2_to_engine_result(self.out)

    def test_rdec_json_shape(self):
        data = engine_result_to_relationship_decisions_json(self.result, question=RDEC_Q)
        self.assertEqual(data["question_type"], "relationship_decisions")
        self.assertIn(data["final_verdict"], ("Favorable", "Wait", "Cautious", "Avoid"))

    def test_stay_or_leave_angle(self):
        data = engine_result_to_relationship_decisions_json(self.result, question=RDEC_Q)
        self.assertEqual(data.get("answer_focus"), "stay_or_leave")

    def test_avoid_not_favorable_praise(self):
        data = engine_result_to_relationship_decisions_json(self.result, question=RDEC_Q)
        data["decision_level"] = "avoid"
        data["relationship_decisions_level"] = "avoid"
        data["direct_answer"] = get_opening("stay_or_leave", "avoid")
        text = render_relationship_decisions_template_answer(data, RDEC_Q)
        self.assertNotRegex(text, r"(?i)mostly\s+favorable|forward\s+step\s+supports")

    def test_locked_template_valid(self):
        data = engine_result_to_relationship_decisions_json(self.result, question=RDEC_Q)
        ok, issues = validate_relationship_decisions_narrator_output(data.get("locked_template") or "", data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_no_chart(self):
        payload = relationship_decisions_engine_narrator_payload(self.result, question=RDEC_Q)
        parsed = json.loads(payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip())
        self.assertNotIn("ascendant", json.dumps(parsed).lower())

    def test_dna_bucket_suitability(self):
        dna = {"questions": [{"bucket": "relationship_decisions", "intent": "overall suitability"}]}
        angle = detect_relationship_decisions_answer_focus(
            "kya sahi hai", question_dna=dna
        )
        self.assertEqual(angle, "overall_suitability")


class RelationshipDecisionsGoldenTests(unittest.TestCase):
    def test_golden_angles(self):
        failures = []
        for q, exp in GOLDEN_QUESTIONS:
            got = infer_relationship_decisions_angle(q)
            if got != exp:
                failures.append(f"{q!r}: expected {exp}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_render_golden_batch(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for q, _ in GOLDEN_QUESTIONS[:10]:
            out = run_relationship_decisions_v2(SAMPLE_KUNDLI, q)
            data = engine_result_to_relationship_decisions_json(v2_to_engine_result(out), question=q)
            text = render_relationship_decisions_template_answer(data, q)
            ok, issues = validate_relationship_decisions_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{q}: {issues}")


if __name__ == "__main__":
    unittest.main()

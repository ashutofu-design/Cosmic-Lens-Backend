"""Emotional attachment narrator — intent-anchored template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_emotional_attachment_angle
from ask_mr.emotional_attachment_templates import detect_emotional_attachment_answer_focus, get_opening
from ask_mr.emotional_attachment_narrator import (
    emotional_attachment_engine_narrator_payload,
    engine_result_to_emotional_attachment_json,
    render_emotional_attachment_template_answer,
    validate_emotional_attachment_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.emotional_attachment import run_emotional_attachment_v2

SAMPLE_KUNDLI = {
    "ascendant": "Cancer",
    "planets": [
        {"name": "Moon", "sign": "Scorpio", "house": 5},
        {"name": "Venus", "sign": "Taurus", "house": 11},
        {"name": "Mars", "sign": "Libra", "house": 4},
        {"name": "Jupiter", "sign": "Pisces", "house": 9},
        {"name": "Saturn", "sign": "Aquarius", "house": 8},
    ],
    "dasha": {"mahadasha": "Moon", "antardasha": "Venus"},
}

GOLDEN_QUESTIONS = [
    ("Mera emotional attachment style kaisa hai relationship mein?", "attachment_style"),
    ("Meri emotional needs poori hongi?", "emotional_needs"),
    ("Emotional bond strong hoga?", "bond_depth"),
    ("Kya main emotionally secure feel karungi?", "emotional_security"),
    ("Fear of loss relationship me zyada hai?", "fear_of_loss"),
    ("Mood swings closeness ko affect karte hain?", "mood_sensitivity"),
    ("Kya main zyada clingy ho jati hoon?", "clinginess"),
    ("Partner emotionally distant lagta hai?", "emotional_distance"),
    ("Vulnerability share karna easy hoga?", "vulnerability"),
    ("Reassurance zyada chahiye hota hai?", "reassurance"),
    ("Emotional intensity high hogi?", "emotional_intensity"),
    ("Deep emotional capacity hai kya?", "emotional_capacity"),
    ("Mera lagav pattern kaisa hai?", "attachment_style"),
    ("Feelings gehra honge relationship me?", "bond_depth"),
    ("Insecurity relationship me affect karti hai?", "fear_of_loss"),
    ("Emotional bonding kaisi rahegi?", "general_attachment"),
    ("Attach hona easy hoga ya difficult?", "attachment_style"),
    ("Emotionally safe feel kar paungi?", "emotional_security"),
    ("Possessive side zyada active hai?", "clinginess"),
    ("Emotional withdraw hota hai kabhi?", "emotional_distance"),
]

EA_Q = "Mera emotional attachment style kaisa hai relationship mein?"


class EmotionalAttachmentNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_emotional_attachment_v2(SAMPLE_KUNDLI, EA_Q)
        self.result = v2_to_engine_result(self.out)

    def test_ea_json_shape(self):
        data = engine_result_to_emotional_attachment_json(self.result, question=EA_Q)
        self.assertEqual(data["question_type"], "emotional_attachment")
        self.assertIn(data["final_verdict"], ("Secure", "Mixed", "Anxious", "Volatile"))

    def test_attachment_style_angle(self):
        data = engine_result_to_emotional_attachment_json(self.result, question=EA_Q)
        self.assertEqual(data.get("answer_focus"), "attachment_style")

    def test_volatile_not_secure_praise(self):
        data = engine_result_to_emotional_attachment_json(self.result, question=EA_Q)
        data["attachment_level"] = "volatile"
        data["direct_answer"] = get_opening("attachment_style", "volatile")
        text = render_emotional_attachment_template_answer(data, EA_Q)
        self.assertNotRegex(text, r"(?i)mostly\s+secure|steady\s+closeness")

    def test_locked_template_valid(self):
        data = engine_result_to_emotional_attachment_json(self.result, question=EA_Q)
        ok, issues = validate_emotional_attachment_narrator_output(data.get("locked_template") or "", data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_no_chart(self):
        payload = emotional_attachment_engine_narrator_payload(self.result, question=EA_Q)
        parsed = json.loads(payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip())
        self.assertNotIn("ascendant", json.dumps(parsed).lower())

    def test_dna_bucket_needs(self):
        dna = {"questions": [{"bucket": "emotional_attachment", "intent": "emotional needs"}]}
        angle = detect_emotional_attachment_answer_focus("meri emotional needs poori", question_dna=dna)
        self.assertEqual(angle, "emotional_needs")


class EmotionalAttachmentGoldenTests(unittest.TestCase):
    def test_golden_angles(self):
        failures = []
        for q, exp in GOLDEN_QUESTIONS:
            got = infer_emotional_attachment_angle(q)
            if got != exp:
                failures.append(f"{q!r}: expected {exp}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_render_golden_batch(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for q, _ in GOLDEN_QUESTIONS[:10]:
            out = run_emotional_attachment_v2(SAMPLE_KUNDLI, q)
            data = engine_result_to_emotional_attachment_json(v2_to_engine_result(out), question=q)
            text = render_emotional_attachment_template_answer(data, q)
            ok, issues = validate_emotional_attachment_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{q}: {issues}")


if __name__ == "__main__":
    unittest.main()

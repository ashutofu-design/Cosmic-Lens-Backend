"""Partner nature narrator — intent-anchored template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_partner_nature_angle
from ask_mr.partner_nature_templates import detect_partner_nature_answer_focus, get_opening
from ask_mr.partner_nature_narrator import (
    engine_result_to_partner_nature_json,
    partner_nature_engine_narrator_payload,
    render_partner_nature_template_answer,
    validate_partner_nature_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.partner_nature import run_partner_nature_v2

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Jupiter", "sign": "Libra", "house": 11},
        {"name": "Mars", "sign": "Capricorn", "house": 7},
        {"name": "Saturn", "sign": "Aries", "house": 5},
    ],
    "dasha": {"mahadasha": "Venus", "antardasha": "Jupiter"},
}

GOLDEN_QUESTIONS = [
    ("Mera life partner ka nature kaisa hoga?", "general_nature"),
    ("Partner emotionally expressive hoga ya reserved?", "emotional_style"),
    ("Partner dominant hoga ya cooperative?", "dominant_cooperative"),
    ("Partner gussa karta hai kya?", "temper_anger"),
    ("Partner ka temper kaisa hai?", "temper_anger"),
    ("Partner ke love language kya honge?", "love_language"),
    ("Partner ki family background kaisi hai?", "family_background"),
    ("Partner spiritual hai ya practical?", "spiritual_practical"),
    ("Partner mujhe respect dega ya nahi?", "respect_behavior"),
    ("Ideal spouse ki qualities kya hain?", "ideal_spouse"),
    ("Partner ke andar kaunsi qualities attract karengi?", "qualities_attract"),
    ("Partner different culture se ho sakta hai?", "culture_background"),
    ("Partner ka personality kaisa hai?", "general_nature"),
    ("Partner attachment depth kaisi hogi?", "attachment_depth"),
    ("Partner ka swabhav kaisa hai?", "general_nature"),
    ("Partner ka nature aur personality kaisa hoga?", "general_nature"),
    ("Partner ambitious nature ka hoga?", "spiritual_practical"),
    ("Partner ka look aur personality?", "appearance_personality"),
    ("Partner feelings gehra rahenge?", "attachment_depth"),
    ("Partner pati ka nature kaisa hai?", "general_nature"),
]

PN_Q = "Mera life partner ka nature kaisa hoga?"


class PartnerNatureNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_partner_nature_v2(SAMPLE_KUNDLI, PN_Q)
        self.result = v2_to_engine_result(self.out)

    def test_pn_json_shape(self):
        data = engine_result_to_partner_nature_json(self.result, question=PN_Q)
        self.assertEqual(data["question_type"], "partner_nature")
        self.assertIn(data["final_verdict"], ("Balanced", "Mixed", "Complex", "Challenging"))

    def test_general_nature_angle(self):
        data = engine_result_to_partner_nature_json(self.result, question=PN_Q)
        self.assertEqual(data.get("answer_focus"), "general_nature")

    def test_challenging_not_balanced_praise(self):
        data = engine_result_to_partner_nature_json(self.result, question=PN_Q)
        data["nature_level"] = "challenging"
        data["direct_answer"] = get_opening("general_nature", "challenging")
        text = render_partner_nature_template_answer(data, PN_Q)
        self.assertNotRegex(text, r"(?i)mostly\s+balanced|perfect\s+partner")

    def test_locked_template_valid(self):
        data = engine_result_to_partner_nature_json(self.result, question=PN_Q)
        ok, issues = validate_partner_nature_narrator_output(data.get("locked_template") or "", data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_no_chart(self):
        payload = partner_nature_engine_narrator_payload(self.result, question=PN_Q)
        parsed = json.loads(payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip())
        self.assertNotIn("ascendant", json.dumps(parsed).lower())

    def test_dna_bucket_temper(self):
        dna = {"questions": [{"bucket": "partner_nature", "intent": "partner temper"}]}
        angle = detect_partner_nature_answer_focus("partner ka nature kaisa hai gussa", question_dna=dna)
        self.assertEqual(angle, "temper_anger")


class PartnerNatureGoldenTests(unittest.TestCase):
    def test_golden_angles(self):
        failures = []
        for q, exp in GOLDEN_QUESTIONS:
            got = infer_partner_nature_angle(q)
            if got != exp:
                failures.append(f"{q!r}: expected {exp}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_render_golden_batch(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for q, _ in GOLDEN_QUESTIONS[:10]:
            out = run_partner_nature_v2(SAMPLE_KUNDLI, q)
            data = engine_result_to_partner_nature_json(v2_to_engine_result(out), question=q)
            text = render_partner_nature_template_answer(data, q)
            ok, issues = validate_partner_nature_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{q}: {issues}")


if __name__ == "__main__":
    unittest.main()

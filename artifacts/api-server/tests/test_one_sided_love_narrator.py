"""One-sided love narrator — intent-anchored template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_one_sided_love_angle
from ask_mr.one_sided_love_templates import detect_one_sided_love_answer_focus, get_opening
from ask_mr.one_sided_love_narrator import (
    engine_result_to_one_sided_love_json,
    render_one_sided_love_template_answer,
    one_sided_love_engine_narrator_payload,
    validate_one_sided_love_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.one_sided_love import run_one_sided_love_v2

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
    ("Kya yeh ek tarfa pyar hai?", "ek_tarfa"),
    ("Crush accept karega kya?", "crush"),
    ("Kya wo mujhse pyar karta hai?", "partner_loves_back"),
    ("Kya wo bhi utna hi pyaar karta hai?", "reciprocity"),
    ("One sided love hai kya?", "ek_tarfa"),
    ("Crush mujhe notice karega?", "crush"),
    ("Proposal accept hoga?", "proposal"),
    ("Kya mutual love possible hai?", "reciprocity"),
    ("Meri taraf se zyada pyaar hai?", "effort_imbalance"),
    ("Wo mujhe pasand karta hai ya nahi?", "partner_loves_back"),
    ("Ek tarfa attraction hai kya?", "ek_tarfa"),
    ("Crush respond karega kab?", "crush"),
    ("Kya wo love me back karta hai?", "reciprocity"),
    ("Unrequited love pattern hai?", "unrequited"),
    ("Jitna main pyaar karti hun utna wo?", "reciprocity"),
    ("One sided feelings develop ho rahe hain?", "ek_tarfa"),
    ("Kya crush ko propose karna sahi hai?", "proposal"),
    ("Partner reciprocate karega?", "reciprocity"),
    ("Kya wo dil se pyaar karta hai?", "partner_loves_back"),
    ("Ek tarfa rishta ban raha hai?", "ek_tarfa"),
]

OS_Q = "Kya yeh ek tarfa pyar hai?"


class OneSidedLoveNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_one_sided_love_v2(SAMPLE_KUNDLI, OS_Q)
        self.result = v2_to_engine_result(self.out)

    def test_oslove_json_shape(self):
        data = engine_result_to_one_sided_love_json(self.result, question=OS_Q)
        self.assertEqual(data["question_type"], "one_sided_love")
        self.assertIn(data["final_verdict"], ("Reciprocal", "Unclear", "One-sided", "Unlikely"))

    def test_ek_tarfa_angle(self):
        data = engine_result_to_one_sided_love_json(self.result, question=OS_Q)
        self.assertEqual(data.get("answer_focus"), "ek_tarfa")

    def test_unlikely_not_reciprocal_praise(self):
        data = engine_result_to_one_sided_love_json(self.result, question=OS_Q)
        data["one_sided_level"] = "unlikely"
        data["oslove_level"] = "unlikely"
        data["direct_answer"] = get_opening("ek_tarfa", "unlikely")
        text = render_one_sided_love_template_answer(data, OS_Q)
        self.assertNotRegex(text, r"(?i)mostly\s+reciprocal|mutual\s+balance\s+strong")

    def test_locked_template_valid(self):
        data = engine_result_to_one_sided_love_json(self.result, question=OS_Q)
        ok, issues = validate_one_sided_love_narrator_output(data.get("locked_template") or "", data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_no_chart(self):
        payload = one_sided_love_engine_narrator_payload(self.result, question=OS_Q)
        parsed = json.loads(payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip())
        self.assertNotIn("ascendant", json.dumps(parsed).lower())

    def test_dna_bucket_reciprocity(self):
        dna = {"questions": [{"bucket": "one_sided", "intent": "reciprocity check"}]}
        angle = detect_one_sided_love_answer_focus(
            "kya feelings barabar hain", question_dna=dna
        )
        self.assertIn(angle, ("reciprocity", "general_one_sided"))


class OneSidedLoveGoldenTests(unittest.TestCase):
    def test_golden_angles(self):
        failures = []
        for q, exp in GOLDEN_QUESTIONS:
            got = infer_one_sided_love_angle(q)
            if got != exp:
                failures.append(f"{q!r}: expected {exp}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_render_golden_batch(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for q, _ in GOLDEN_QUESTIONS[:10]:
            out = run_one_sided_love_v2(SAMPLE_KUNDLI, q)
            data = engine_result_to_one_sided_love_json(v2_to_engine_result(out), question=q)
            text = render_one_sided_love_template_answer(data, q)
            ok, issues = validate_one_sided_love_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{q}: {issues}")


if __name__ == "__main__":
    unittest.main()

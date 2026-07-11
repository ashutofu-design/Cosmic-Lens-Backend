"""Toxicity narrator — intent-anchored template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_toxicity_angle
from ask_mr.toxicity_templates import detect_toxicity_answer_focus, get_opening
from ask_mr.toxicity_narrator import (
    engine_result_to_toxicity_json,
    render_toxicity_template_answer,
    toxicity_engine_narrator_payload,
    validate_toxicity_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.toxicity import run_toxicity_v2

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
    ("Kya yeh relationship toxic hai?", "toxic_dynamic"),
    ("Partner controlling aur manipulative hai kya?", "control_pattern"),
    ("Kya abuse ka risk hai relationship me?", "abuse_risk"),
    ("Red flags dikh rahe hain kya?", "red_flags"),
    ("Partner gaslight karta hai kya?", "gaslighting"),
    ("Unhealthy relationship pattern hai?", "unhealthy_dynamic"),
    ("Domestic violence ka yog hai?", "abuse_risk"),
    ("Partner possessive hai toxic level par?", "control_pattern"),
    ("Jealousy relationship me toxic banegi?", "jealousy_toxic"),
    ("Toxicity level kya hai hamari?", "toxic_dynamic"),
    ("Manipulative behaviour pattern hai?", "control_pattern"),
    ("Partner controlling nature toxic hai?", "control_pattern"),
    ("Emotional abuse ka pattern hai?", "abuse_risk"),
    ("Kya rishta unhealthy ho raha hai?", "unhealthy_dynamic"),
    ("Red flag signals strong hain?", "red_flags"),
    ("Gaslighting hoti hai kya?", "gaslighting"),
    ("Toxic dynamic develop ho raha hai?", "toxic_dynamic"),
    ("Partner maar peet karta hai kya?", "abuse_risk"),
    ("Control issues toxic hain?", "control_pattern"),
    ("Harm pattern chart me red flag dikhta hai?", "red_flags"),
]

TOX_Q = "Kya yeh relationship toxic hai?"


class ToxicityNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_toxicity_v2(SAMPLE_KUNDLI, TOX_Q)
        self.result = v2_to_engine_result(self.out)

    def test_tox_json_shape(self):
        data = engine_result_to_toxicity_json(self.result, question=TOX_Q)
        self.assertEqual(data["question_type"], "toxicity")
        self.assertIn(data["final_verdict"], ("Low", "Moderate", "Elevated", "High"))

    def test_toxic_dynamic_angle(self):
        data = engine_result_to_toxicity_json(self.result, question=TOX_Q)
        self.assertEqual(data.get("answer_focus"), "toxic_dynamic")

    def test_high_not_low_praise(self):
        data = engine_result_to_toxicity_json(self.result, question=TOX_Q)
        data["toxicity_level"] = "high"
        data["direct_answer"] = get_opening("toxic_dynamic", "high")
        text = render_toxicity_template_answer(data, TOX_Q)
        self.assertNotRegex(text, r"(?i)mostly\s+low|repairable\s+friction")

    def test_locked_template_valid(self):
        data = engine_result_to_toxicity_json(self.result, question=TOX_Q)
        ok, issues = validate_toxicity_narrator_output(data.get("locked_template") or "", data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_no_chart(self):
        payload = toxicity_engine_narrator_payload(self.result, question=TOX_Q)
        parsed = json.loads(payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip())
        self.assertNotIn("ascendant", json.dumps(parsed).lower())

    def test_dna_bucket_jealousy(self):
        dna = {"questions": [{"bucket": "toxicity_red_flags", "intent": "jealousy toxic"}]}
        angle = detect_toxicity_answer_focus("jealousy problem relationship", question_dna=dna)
        self.assertEqual(angle, "jealousy_toxic")


class ToxicityGoldenTests(unittest.TestCase):
    def test_golden_angles(self):
        failures = []
        for q, exp in GOLDEN_QUESTIONS:
            got = infer_toxicity_angle(q)
            if got != exp:
                failures.append(f"{q!r}: expected {exp}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_render_golden_batch(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for q, _ in GOLDEN_QUESTIONS[:10]:
            out = run_toxicity_v2(SAMPLE_KUNDLI, q)
            data = engine_result_to_toxicity_json(v2_to_engine_result(out), question=q)
            text = render_toxicity_template_answer(data, q)
            ok, issues = validate_toxicity_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{q}: {issues}")


if __name__ == "__main__":
    unittest.main()

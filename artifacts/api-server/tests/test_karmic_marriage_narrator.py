"""Karmic marriage narrator — intent-anchored template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_karmic_marriage_angle
from ask_mr.karmic_marriage_templates import detect_karmic_marriage_answer_focus, get_opening
from ask_mr.karmic_marriage_narrator import (
    engine_result_to_karmic_marriage_json,
    render_karmic_marriage_template_answer,
    karmic_marriage_engine_narrator_payload,
    validate_karmic_marriage_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.karmic_marriage import run_karmic_marriage_v2

SAMPLE_KUNDLI = {
    "ascendant": "Scorpio",
    "planets": [
        {"name": "Mars", "sign": "Aries", "house": 7},
        {"name": "Rahu", "sign": "Gemini", "house": 7},
        {"name": "Ketu", "sign": "Sagittarius", "house": 1},
        {"name": "Moon", "sign": "Capricorn", "house": 8},
        {"name": "Venus", "sign": "Taurus", "house": 12},
        {"name": "Saturn", "sign": "Aquarius", "house": 5},
        {"name": "Jupiter", "sign": "Pisces", "house": 6},
    ],
    "dasha": {"mahadasha": "Mars", "antardasha": "Rahu"},
}

GOLDEN_QUESTIONS = [
    ("Kya mera soulmate milega?", "soulmate"),
    ("Twin flame connection hai kya?", "twin_flame"),
    ("Past life connection hai kya partner se?", "past_life"),
    ("Karmic debt marriage me repay karna hoga?", "karmic_debt"),
    ("Spiritual growth shaadi se milegi?", "spiritual_growth"),
    ("Kya yeh karmic marriage hai?", "karmic_bond"),
    ("Rahu Ketu karmic pull dikhta hai?", "nodes_karma"),
    ("Pichle janam ka connection hai?", "past_life"),
    ("Karma debt partner ke saath clear hoga?", "karmic_debt"),
    ("Soul mate pattern chart me dikhta hai?", "soulmate"),
    ("Aadhyatmik growth marriage se hogi?", "spiritual_growth"),
    ("Karmic rishta banega kya?", "karmic_bond"),
    ("Twin flame ya soulmate ka yog hai?", "twin_flame"),
    ("Purva janm se partner pehchana hua lagta hai?", "past_life"),
    ("Karmic lesson marriage me repeat hoga?", "karmic_debt"),
    ("Marriage se dharma growth possible hai?", "spiritual_growth"),
    ("Kya hamara bond karmic connection hai?", "karmic_bond"),
    ("Ketu 7th house karmic theme dikhta hai?", "nodes_karma"),
    ("Overall karmic theme marriage me strong hai?", "general_karmic"),
    ("Karma through partnership clear hoga?", "general_karmic"),
]

KARM_Q = "Kya mera soulmate milega?"


class KarmicMarriageNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_karmic_marriage_v2(SAMPLE_KUNDLI, KARM_Q)
        self.result = v2_to_engine_result(self.out)

    def test_karm_json_shape(self):
        data = engine_result_to_karmic_marriage_json(self.result, question=KARM_Q)
        self.assertEqual(data["question_type"], "karmic_marriage")
        self.assertIn(data["final_verdict"], ("Strong", "Present", "Mixed", "Weak"))

    def test_soulmate_angle(self):
        data = engine_result_to_karmic_marriage_json(self.result, question=KARM_Q)
        self.assertEqual(data.get("answer_focus"), "soulmate")

    def test_weak_not_strong_praise(self):
        data = engine_result_to_karmic_marriage_json(self.result, question=KARM_Q)
        data["karmic_level"] = "weak"
        data["karmic_marriage_level"] = "weak"
        data["direct_answer"] = get_opening("soulmate", "weak")
        text = render_karmic_marriage_template_answer(data, KARM_Q)
        self.assertNotRegex(text, r"(?i)mostly\s+strong|deep\s+recognition")

    def test_locked_template_valid(self):
        data = engine_result_to_karmic_marriage_json(self.result, question=KARM_Q)
        ok, issues = validate_karmic_marriage_narrator_output(data.get("locked_template") or "", data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_no_chart(self):
        payload = karmic_marriage_engine_narrator_payload(self.result, question=KARM_Q)
        parsed = json.loads(payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip())
        self.assertNotIn("ascendant", json.dumps(parsed).lower())

    def test_dna_bucket_soulmate(self):
        dna = {"questions": [{"bucket": "spiritual_karmic", "intent": "soulmate bond"}]}
        angle = detect_karmic_marriage_answer_focus(
            "kya mera soulmate milega", question_dna=dna
        )
        self.assertEqual(angle, "soulmate")


class KarmicMarriageGoldenTests(unittest.TestCase):
    def test_golden_angles(self):
        failures = []
        for q, exp in GOLDEN_QUESTIONS:
            got = infer_karmic_marriage_angle(q)
            if got != exp:
                failures.append(f"{q!r}: expected {exp}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_render_golden_batch(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for q, _ in GOLDEN_QUESTIONS[:10]:
            out = run_karmic_marriage_v2(SAMPLE_KUNDLI, q)
            data = engine_result_to_karmic_marriage_json(v2_to_engine_result(out), question=q)
            text = render_karmic_marriage_template_answer(data, q)
            ok, issues = validate_karmic_marriage_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{q}: {issues}")


if __name__ == "__main__":
    unittest.main()

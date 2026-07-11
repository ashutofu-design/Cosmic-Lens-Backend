"""Long distance narrator — intent-anchored template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_long_distance_angle
from ask_mr.long_distance_templates import detect_long_distance_answer_focus, get_opening
from ask_mr.long_distance_narrator import (
    engine_result_to_long_distance_json,
    long_distance_engine_narrator_payload,
    render_long_distance_template_answer,
    validate_long_distance_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.long_distance import run_long_distance_v2

SAMPLE_KUNDLI = {
    "ascendant": "Aquarius",
    "planets": [
        {"name": "Saturn", "sign": "Aquarius", "house": 1},
        {"name": "Rahu", "sign": "Gemini", "house": 5},
        {"name": "Moon", "sign": "Scorpio", "house": 10},
        {"name": "Venus", "sign": "Libra", "house": 9},
        {"name": "Jupiter", "sign": "Sagittarius", "house": 11},
    ],
    "dasha": {"mahadasha": "Saturn", "antardasha": "Rahu"},
}

GOLDEN_QUESTIONS = [
    ("Long distance relationship chalega kya?", "ldr_viability"),
    ("Door rehkar rishta strong reh sakta hai?", "door_rehkar"),
    ("Online relationship successful hoga?", "online_relationship"),
    ("LDR work karega kya?", "ldr_viability"),
    ("Alag shahar me rehkar rishta chalega?", "different_city"),
    ("Different city me partner hai chalega?", "different_city"),
    ("Virtual love strong ho jayega?", "online_relationship"),
    ("Door rehkar trust bana rahega?", "trust_distance"),
    ("Kab milenge reunion plan LDR me?", "reunion_plans"),
    ("Long distance me communication important hai?", "communication_ldr"),
    ("Foreign country me partner door hai?", "foreign_partner"),
    ("Physical gap LDR me problem hogi?", "physical_gap"),
    ("Doori se rishta weak to nahi hoga?", "separation_stress"),
    ("Internet love relationship chalega?", "online_relationship"),
    ("Dur se rishta nibha paenge?", "ldr_viability"),
    ("Long distance bond hold karega?", "bond_strength"),
    ("LDR me visits kitni zaruri?", "reunion_plans"),
    ("Door rehkar shaadi possible hai?", "door_rehkar"),
    ("Long distance relationship sustainable hai?", "ldr_viability"),
    ("Online rishta trust ke saath chalega?", "online_relationship"),
]

LD_Q = "Long distance relationship chalega kya?"


class LongDistanceNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_long_distance_v2(SAMPLE_KUNDLI, LD_Q)
        self.result = v2_to_engine_result(self.out)

    def test_ld_json_shape(self):
        data = engine_result_to_long_distance_json(self.result, question=LD_Q)
        self.assertEqual(data["question_type"], "long_distance")
        self.assertIn(data["final_verdict"], ("Sustainable", "Mixed", "Fragile", "Strained"))

    def test_ldr_viability_angle(self):
        data = engine_result_to_long_distance_json(self.result, question=LD_Q)
        self.assertEqual(data.get("answer_focus"), "ldr_viability")

    def test_strained_not_sustainable_praise(self):
        data = engine_result_to_long_distance_json(self.result, question=LD_Q)
        data["long_distance_level"] = "strained"
        data["direct_answer"] = get_opening("ldr_viability", "strained")
        text = render_long_distance_template_answer(data, LD_Q)
        self.assertNotRegex(text, r"(?i)mostly\s+sustainable|easy\s+ldr")

    def test_locked_template_valid(self):
        data = engine_result_to_long_distance_json(self.result, question=LD_Q)
        ok, issues = validate_long_distance_narrator_output(data.get("locked_template") or "", data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_no_chart(self):
        payload = long_distance_engine_narrator_payload(self.result, question=LD_Q)
        parsed = json.loads(payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip())
        self.assertNotIn("ascendant", json.dumps(parsed).lower())

    def test_dna_bucket_online(self):
        dna = {"questions": [{"bucket": "long_distance", "intent": "online relationship"}]}
        angle = detect_long_distance_answer_focus("online rishta chalega", question_dna=dna)
        self.assertEqual(angle, "online_relationship")


class LongDistanceGoldenTests(unittest.TestCase):
    def test_golden_angles(self):
        failures = []
        for q, exp in GOLDEN_QUESTIONS:
            got = infer_long_distance_angle(q)
            if got != exp:
                failures.append(f"{q!r}: expected {exp}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_render_golden_batch(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for q, _ in GOLDEN_QUESTIONS[:10]:
            out = run_long_distance_v2(SAMPLE_KUNDLI, q)
            data = engine_result_to_long_distance_json(v2_to_engine_result(out), question=q)
            text = render_long_distance_template_answer(data, q)
            ok, issues = validate_long_distance_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{q}: {issues}")


if __name__ == "__main__":
    unittest.main()

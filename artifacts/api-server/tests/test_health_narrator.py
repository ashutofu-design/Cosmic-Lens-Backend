"""Tests for Health Engine narrator — JSON-only payload + prompt rules."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_health.engine import run_health_static_engine
from ask_health.health_narrator import (
    build_health_narrator_length_block,
    engine_result_to_health_json,
    health_narrator_payload,
    is_health_narratable_archetype,
)
from ask_mr.narrator import build_mr_engine_narrator_system_prompt

_SAMPLE_KUNDLI = {
    "ascendant": "Leo",
    "planets": [
        {"name": "Sun", "sign": "Leo", "house": 1},
        {"name": "Moon", "sign": "Scorpio", "house": 4},
        {"name": "Mars", "sign": "Aries", "house": 9},
        {"name": "Saturn", "sign": "Capricorn", "house": 6},
    ],
}


class HealthNarratorTests(unittest.TestCase):
    def setUp(self):
        self.q = "mera blood pressure high rehta hai chart me kya dikhta hai?"
        self.result = run_health_static_engine(
            _SAMPLE_KUNDLI,
            self.q,
            archetype="heart_blood_pressure",
        )

    def test_health_json_shape(self):
        data = engine_result_to_health_json(self.result, question=self.q)
        self.assertEqual(data["question_type"], "health")
        self.assertEqual(data["archetype"], "heart_blood_pressure")
        self.assertIn("direct_answer", data)
        self.assertIn("positive_indicators", data)
        self.assertIn("risk_indicators", data)
        self.assertIn("confidence_explanation", data)
        self.assertTrue(data["positive_indicators"] or data["risk_indicators"])

    def test_payload_has_engine_json(self):
        payload = health_narrator_payload(self.result, question=self.q)
        self.assertIn("ENGINE_JSON:", payload)
        self.assertIn("SOURCE_LOCK", payload)
        self.assertIn("heart_blood_pressure", payload)

    def test_system_prompt_uses_health_narrator_rules(self):
        payload = health_narrator_payload(self.result, question=self.q)
        prompt = build_mr_engine_narrator_system_prompt(
            chart_text=payload,
            reply_lang="hn",
            archetype="heart_blood_pressure",
        )
        self.assertIn("Cosmic Lens Health Narrator", prompt)
        self.assertIn("Kyun ye verdict aaya", prompt)
        self.assertIn("confidence_explanation", prompt)

    def test_heart_blood_pressure_is_narratable(self):
        self.assertTrue(is_health_narratable_archetype("heart_blood_pressure"))
        self.assertFalse(is_health_narratable_archetype("refuse_diagnosis"))

    def test_json_roundtrip(self):
        payload = health_narrator_payload(self.result, question=self.q)
        raw = payload.split("ENGINE_JSON:\n", 1)[1]
        data = json.loads(raw)
        self.assertEqual(data["topic_lock"], "Heart & blood pressure")


if __name__ == "__main__":
    unittest.main()

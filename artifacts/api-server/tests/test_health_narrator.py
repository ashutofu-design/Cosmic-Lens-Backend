"""Tests for health D1 + D9 engine execution pack."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_health.engine import run_health_static_engine
from ask_health.health_registry import detect_health_archetype
from ask_health.presenter import to_health_llm_payload
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

    def test_narrator_payload_uses_engine_facts(self):
        payload = to_health_llm_payload(self.result, question=self.q)
        self.assertIn("VERIFIED_HEALTH_CONTEXT_JSON:", payload)
        self.assertIn("heart_blood_pressure", payload)
        self.assertIn("d1_health_facts", payload)
        self.assertIn("health_engine_execution", payload)
        self.assertIn("health_d1_facts_v1", payload)

    def test_system_prompt_adapts_depth_from_same_prompt(self):
        payload = to_health_llm_payload(self.result, question=self.q)
        prompt = build_mr_engine_narrator_system_prompt(
            chart_text=payload,
            reply_lang="hn",
            archetype="heart_blood_pressure",
        )
        self.assertIn("ENGINE FACTS:", prompt)
        self.assertNotIn("The Big Picture", prompt)
        self.assertIn("VERIFIED_HEALTH_CONTEXT_JSON", prompt)
        self.assertIn("sawal samjho", prompt)
        self.assertIn("Normal astrologer", prompt)

    def test_disease_list_question_routes_health(self):
        q = "mujhse kya kya disease ho sakta he"
        arch = detect_health_archetype(q)
        self.assertIn(arch, ("preventive_risk", "general_health", "chronic_tendency"))

    def test_payload_includes_d1_and_d9_health_execution(self):
        q = "mujhse kya kya disease ho sakta he"
        kundli = {
            **_SAMPLE_KUNDLI,
            "divisionalCharts": {
                "D9": {
                    "ascendant": "Aries",
                    "planets": [
                        {"name": "Sun", "sign": "Leo", "house": 5},
                        {"name": "Moon", "sign": "Scorpio", "house": 8},
                        {"name": "Saturn", "sign": "Capricorn", "house": 10},
                    ],
                }
            },
        }
        result = run_health_static_engine(kundli, q, archetype="general_health")
        checks = result.checks or {}
        pack = checks.get("health_engine_execution") or {}
        self.assertEqual(pack.get("schema_version"), "health_engine_execution_v1")
        self.assertIn("d1", pack)
        self.assertIn("d9", pack)
        self.assertIn("lagnesh", pack)
        payload = to_health_llm_payload(result, question=q)
        self.assertIn("health_engine_execution", payload)
        self.assertIn("d9_health_facts", payload)


if __name__ == "__main__":
    unittest.main()

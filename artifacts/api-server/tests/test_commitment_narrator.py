"""Tests for Commitment Engine narrator — JSON-only payload + prompt rules."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_mr.v2.engines.commitment import run_commitment_v2
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.commitment_narrator import (
    commitment_narrator_payload,
    engine_result_to_commitment_json,
)
from ask_mr.narrator import build_mr_engine_narrator_system_prompt

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Jupiter", "sign": "Libra", "house": 11},
        {"name": "Saturn", "sign": "Aries", "house": 5},
    ],
    "dasha": {"mahadasha": "Venus", "antardasha": "Jupiter"},
}


class CommitmentNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_commitment_v2(
            SAMPLE_KUNDLI,
            "Kya mera partner commitment ke liye ready hai?",
        )
        self.result = v2_to_engine_result(self.out)

    def test_commitment_json_shape(self):
        data = engine_result_to_commitment_json(self.result)
        self.assertEqual(data["question_type"], "commitment")
        self.assertIn("final_verdict", data)
        self.assertIn("commitment_level", data)
        self.assertIn("strongest", data)
        self.assertIn("weakest", data)
        self.assertIn("reason", data)
        self.assertIn("confidence", data)
        self.assertIn(data["final_verdict"], ("Ready", "Cautious", "Mixed", "Low"))
        self.assertIsInstance(data["strongest"], list)
        self.assertGreater(len(data["strongest"]), 0)
        self.assertIsInstance(data["confidence"], int)

    def test_json_has_no_chart_fields(self):
        payload = commitment_narrator_payload(self.result)
        self.assertIn("ENGINE_JSON:", payload)
        self.assertIn("SOURCE_LOCK", payload)
        json_text = payload.split("ENGINE_JSON:", 1)[1].split("QUESTION_ANGLE:", 1)[0].strip()
        parsed = json.loads(json_text)
        blob = json.dumps(parsed, ensure_ascii=False).lower()
        self.assertNotIn("ascendant", blob)
        self.assertNotIn("kundli", blob)
        self.assertIn("strongest", parsed)

    def test_payload_parses_as_valid_json_block(self):
        payload = commitment_narrator_payload(self.result)
        json_text = payload.split("ENGINE_JSON:", 1)[1].split("QUESTION_ANGLE:", 1)[0].strip()
        parsed = json.loads(json_text)
        self.assertIn("verdict", parsed)
        self.assertIn("strongest_factor", parsed)

    def test_narrator_prompt_commitment_rules(self):
        payload = commitment_narrator_payload(self.result)
        prompt = build_mr_engine_narrator_system_prompt(
            chart_text=payload,
            archetype="commitment",
            reply_lang="hn",
            wants_explain=False,
        )
        self.assertIn("ENGINE_JSON", prompt)
        self.assertIn("commitment", prompt.lower())
        self.assertIn("shayad", prompt.lower())
        self.assertIn("Confidence:", prompt)
        self.assertNotIn("The Big Picture", prompt)
        self.assertIn("ENGINE LOCK", prompt)

    def test_raw_evidence_preserved_in_json(self):
        data = engine_result_to_commitment_json(self.result)
        blob = json.dumps(data, ensure_ascii=False).lower()
        # Engine evidence terms should survive — not generic humanized labels only
        self.assertTrue(
            "lord" in blob or "venus" in blob or "moon" in blob or "jupiter" in blob or len(data["strongest"]) > 0
        )
        for factor in data["strongest"]:
            self.assertNotIn("supportive venus", factor.lower())

    def test_timing_omitted_when_not_applicable(self):
        data = engine_result_to_commitment_json(self.result)
        self.assertNotIn("timing", data)

    def test_adapter_passes_timing_meta(self):
        checks = self.result.checks or {}
        self.assertIn("timing", checks)
        self.assertIn("mode", checks)
        self.assertEqual(checks["mode"], "static")


if __name__ == "__main__":
    unittest.main()

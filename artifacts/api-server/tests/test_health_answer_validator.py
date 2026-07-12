"""Tests for health LLM answer validator loop."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_health.answer_validator import (
    build_health_validator_retry_feedback,
    validate_health_llm_answer,
)

_SAMPLE_EXECUTION = {
    "schema_version": "health_engine_execution_v1",
    "d1": {
        "ascendant": "Leo",
        "planets": [
            {"name": "Sun", "sign": "Leo", "house": 1},
            {"name": "Saturn", "sign": "Capricorn", "house": 6},
            {"name": "Moon", "sign": "Scorpio", "house": 4},
        ],
    },
    "d9": {
        "ascendant": "Aries",
        "planets": [{"name": "Sun", "sign": "Leo", "house": 5}],
    },
}


class HealthAnswerValidatorTests(unittest.TestCase):
    def test_passes_on_topic_answer(self):
        meta = {
            "archetype": "respiratory_health",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        ok, issues = validate_health_llm_answer(
            "mujhse thandi bahut rehti hai kya karu",
            "Chart me sardi/thand ki tendency dikhti hai. Rest aur doctor checkup rakho.",
            meta,
        )
        self.assertTrue(ok, issues)

    def test_blocks_invented_planet_house(self):
        meta = {
            "archetype": "respiratory_health",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        ok, issues = validate_health_llm_answer(
            "meri sehat kaisi hai",
            "Saturn in house 8 se chronic pressure dikhta hai.",
            meta,
        )
        self.assertFalse(ok)
        self.assertTrue(any("wrong_house" in i or "invented" in i for i in issues))

    def test_blocks_question_drift(self):
        meta = {
            "archetype": "respiratory_health",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        ok, issues = validate_health_llm_answer(
            "mujhse thandi bahut rehti hai",
            "Aapka career strong hai aur promotion jaldi milegi.",
            meta,
        )
        self.assertFalse(ok)
        self.assertIn("question_drift", issues)

    def test_retry_feedback_mentions_issues(self):
        fb = build_health_validator_retry_feedback(
            ["question_drift", "template_sections"],
            "mujhse thandi bahut rehti hai",
        )
        self.assertIn("question_drift", fb)
        self.assertIn("HEALTH_ENGINE_EXECUTION_JSON", fb)


if __name__ == "__main__":
    unittest.main()

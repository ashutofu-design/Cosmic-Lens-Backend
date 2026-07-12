"""Tests for health chart proof validation."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_health.answer_validator import validate_health_llm_answer
from ask_health.answer_validator import validate_health_llm_answer
from ask_health.chart_proof import (
    answer_cites_chart_proof,
    chart_support_signals,
    validate_chart_proof_requirement,
)

_SUPPORTED_EXECUTION = {
    "schema_version": "health_engine_execution_v1",
    "d1": {
        "ascendant": "Leo",
        "planets": [
            {"name": "Sun", "sign": "Leo", "house": 1, "dignity": "own", "strength_score": 2},
            {"name": "Saturn", "sign": "Capricorn", "house": 6, "dignity": "own", "strength_score": 2},
            {"name": "Moon", "sign": "Scorpio", "house": 4, "dignity": "debilitated", "strength_score": -2},
        ],
        "afflictions": ["Malefics in H6: Saturn"],
        "sub_flags": {"moon_afflicted": True},
        "health_houses": [
            {"house": 6, "occupants": ["Saturn"], "lord": "Mercury"},
            {"house": 8, "lord": "Mars"},
        ],
    },
    "d9": {
        "ascendant": "Aries",
        "planets": [{"name": "Sun", "sign": "Leo", "house": 5}],
    },
}

_CLEAN_EXECUTION = {
    "schema_version": "health_engine_execution_v1",
    "d1": {
        "ascendant": "Leo",
        "planets": [
            {"name": "Sun", "sign": "Leo", "house": 1, "dignity": "own", "strength_score": 2},
            {"name": "Jupiter", "sign": "Sagittarius", "house": 5, "dignity": "own", "strength_score": 2},
        ],
        "afflictions": [],
        "sub_flags": {"moon_afflicted": False},
    },
    "d9": {"ascendant": "Aries", "planets": []},
}


class HealthChartProofTests(unittest.TestCase):
    def test_respiratory_question_has_chart_signals(self):
        supported, reasons = chart_support_signals(
            "mujhse thandi bahut rehti hai",
            "respiratory_health",
            _SUPPORTED_EXECUTION,
        )
        self.assertTrue(supported)
        self.assertTrue(any("Saturn" in r for r in reasons))

    def test_proof_cited_in_answer(self):
        answer = (
            "Saturn 6th ghar me hai, isliye thandi/sardi ki tendency chart me dikhti hai. "
            "Rest rakho aur doctor checkup karo."
        )
        self.assertTrue(answer_cites_chart_proof(answer, _SUPPORTED_EXECUTION))

    def test_blocks_generic_answer_without_proof(self):
        ok, issues = validate_chart_proof_requirement(
            "mujhse thandi bahut rehti hai kya karu",
            "Pollution se bacho, pranayama karo, fresh hawa lo.",
            "respiratory_health",
            _SUPPORTED_EXECUTION,
        )
        self.assertFalse(ok)
        self.assertIn("missing_chart_proof", issues)

    def test_allows_honest_low_when_no_chart_signal(self):
        ok, issues = validate_chart_proof_requirement(
            "mujhse thandi bahut rehti hai",
            "Chart me is sawal ki strong signal nahi dikhti, zyada tension mat lo.",
            "respiratory_health",
            _CLEAN_EXECUTION,
        )
        self.assertTrue(ok, issues)

    def test_validator_requires_proof_for_supported_chart(self):
        meta = {
            "archetype": "respiratory_health",
            "checks": {"health_engine_execution": _SUPPORTED_EXECUTION},
        }
        ok, issues = validate_health_llm_answer(
            "mujhse thandi bahut rehti hai kya karu",
            "Pollution se bacho aur pranayama karo.",
            meta,
        )
        self.assertFalse(ok)
        self.assertIn("missing_chart_proof", issues)


    def test_disease_list_good_answer_passes(self):
        ok, issues = validate_chart_proof_requirement(
            "mujhse kya kya disease ho sakta he",
            "6th ghar me Saturn pressure hai aur 8th lord dusthana me — chronic aur hospital zones monitor karo. Specific disease naam chart se nahi batata.",
            "general_health",
            _SUPPORTED_EXECUTION,
        )
        self.assertTrue(ok, issues)

    def test_disease_list_blocks_disease_names(self):
        ok, issues = validate_health_llm_answer(
            "mujhse kya kya disease ho sakta he",
            "Diabetes aur thyroid ki tendency ho sakti hai. Saturn 6th ghar me hai.",
            {
                "archetype": "general_health",
                "checks": {"health_engine_execution": _SUPPORTED_EXECUTION},
            },
        )
        self.assertFalse(ok)
        self.assertIn("disease_name", issues)


if __name__ == "__main__":
    unittest.main()

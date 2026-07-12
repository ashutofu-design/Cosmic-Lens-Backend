"""Tests for health LLM answer validator loop."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_health.answer_validator import (
    build_health_validator_display,
    build_health_validator_retry_feedback,
    run_health_llm_validator_loop,
    validate_health_llm_answer,
)

_SAMPLE_EXECUTION = {
    "schema_version": "health_engine_execution_v1",
    "d1": {
        "ascendant": "Leo",
        "planets": [
            {"name": "Sun", "sign": "Leo", "house": 1},
            {"name": "Saturn", "sign": "Capricorn", "house": 6},
            {"name": "Moon", "sign": "Scorpio", "house": 4, "dignity": "debilitated", "strength_score": -2},
        ],
        "afflictions": ["Malefics in H6: Saturn"],
        "sub_flags": {"moon_afflicted": True},
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
            "Saturn 6th ghar me hai, isliye chart me thandi/sardi ki tendency dikhti hai. Rest aur doctor checkup rakho.",
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

    def test_display_includes_check_rows(self):
        meta = {
            "archetype": "respiratory_health",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        display = build_health_validator_display(
            "mujhse thandi bahut rehti hai",
            "Saturn 6th ghar me hai, isliye thandi tendency dikhti hai.",
            meta,
            stored_audit={"attempts": 1, "passed": True},
        )
        self.assertTrue(display.get("applies"))
        self.assertTrue(display.get("passed"))
        self.assertGreaterEqual(len(display.get("checks") or []), 5)
        check_ids = {c.get("id") for c in display.get("checks") or []}
        self.assertIn("chart_proof", check_ids)

    def test_releases_last_answer_after_max_retries(self):
        class _Msg:
            def __init__(self, content):
                self.content = content

        class _Choice:
            def __init__(self, content):
                self.message = _Msg(content)

        class _Resp:
            def __init__(self, content):
                self.choices = [_Choice(content)]

        class _Client:
            def __init__(self):
                self.n = 0

            class chat:
                class completions:
                    @staticmethod
                    def create(**_kwargs):
                        return _Client._next()

            _answers = [
                "Pollution se bacho aur pranayama karo.",
                "Pollution se bacho aur pranayama karo.",
                "Pollution se bacho aur pranayama karo.",
                "Pollution se bacho aur pranayama karo.",
            ]
            _i = 0

            @classmethod
            def _next(cls):
                content = cls._answers[min(cls._i, len(cls._answers) - 1)]
                cls._i += 1
                return _Resp(content)

        meta = {
            "archetype": "respiratory_health",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        text, audit = run_health_llm_validator_loop(
            _Client(),
            model="test",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=100,
            question="mujhse thandi bahut rehti hai kya karu",
            meta=meta,
        )
        self.assertTrue(text)
        self.assertFalse(audit.get("passed"))
        self.assertTrue(audit.get("released_anyway"))


if __name__ == "__main__":
    unittest.main()

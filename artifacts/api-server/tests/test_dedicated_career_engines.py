"""Tests for job-change, general-career, setback, field-choice dedicated engines."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.career import assess_career, classify_career_question


def _intel() -> dict:
    return {
        "house_lords": [
            {"house": 3, "lord": "Mars"}, {"house": 5, "lord": "Sun"},
            {"house": 6, "lord": "Mercury"}, {"house": 8, "lord": "Saturn"},
            {"house": 9, "lord": "Venus"}, {"house": 10, "lord": "Moon"},
            {"house": 11, "lord": "Jupiter"},
        ],
        "dignities": [
            {"planet": "Moon", "status": "exalted"},
            {"planet": "Sun", "status": "own-sign"},
        ],
    }


def _kundli() -> dict:
    return {
        "ascendant": "Libra",
        "planets": [
            {"name": "Sun", "sign": "Leo", "house": 11},
            {"name": "Moon", "sign": "Taurus", "house": 8},
            {"name": "Mars", "sign": "Sagittarius", "house": 3},
            {"name": "Mercury", "sign": "Virgo", "house": 12},
            {"name": "Jupiter", "sign": "Aquarius", "house": 5},
            {"name": "Venus", "sign": "Gemini", "house": 9},
            {"name": "Saturn", "sign": "Capricorn", "house": 4},
        ],
        "currentDasha": {"mahadasha": "Jupiter", "antardasha": "Mars"},
    }


class TestDedicatedCareerEngines(unittest.TestCase):
    def test_job_change_engine_attached(self):
        q = "Naukri change kab karun?"
        self.assertEqual(classify_career_question(q), "job_change")
        out = assess_career(_kundli(), _intel(), kp={}, question=q)
        self.assertIn("job_change_engine", out)
        self.assertIn("job_change_prompt_block", out)
        self.assertNotIn("career_step1_bcp", out)

    def test_general_career_engine_attached(self):
        q = "Meri naukri kab milegi?"
        out = assess_career(_kundli(), _intel(), kp={}, question=q)
        self.assertEqual(out["bucket"], "general_career")
        self.assertIn("general_career_engine", out)
        self.assertIn("general_career_prompt_block", out)

    def test_setback_engine_attached(self):
        q = "Career setback se recovery kab hogi?"
        self.assertEqual(classify_career_question(q), "career_setback")
        out = assess_career(_kundli(), _intel(), kp={}, question=q)
        self.assertIn("setback_engine", out)
        self.assertIn("C5_setback_recovery", out.get("conditionals") or {})
        self.assertEqual(
            (out.get("conditionals") or {}).get("C5_setback_recovery", {}).get("engine"),
            "setback_engine_v1",
        )

    def test_field_choice_engine_attached(self):
        q = "Mujhe kaun sa career field choose karna chahiye?"
        self.assertEqual(classify_career_question(q), "career_field_choice")
        out = assess_career(_kundli(), _intel(), kp={}, question=q)
        self.assertIn("field_choice_engine", out)
        self.assertIn("field_recommendations", out)
        fr = out.get("field_recommendations") or {}
        self.assertTrue(fr.get("top_fields"))


if __name__ == "__main__":
    unittest.main()

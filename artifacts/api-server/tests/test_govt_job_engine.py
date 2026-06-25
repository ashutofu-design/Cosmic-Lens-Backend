"""Tests for govt_job_engine_v1 — Sun-Saturn life promise."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.career.govt_job_engine_v1 import (
    assess_govt_job,
    assess_govt_job_promise,
    format_govt_job_block_for_prompt,
)


def _intel() -> dict:
    return {
        "house_lords": [
            {"house": 6, "lord": "Mars"},
            {"house": 9, "lord": "Mercury"},
            {"house": 10, "lord": "Moon"},
        ],
        "dignities": [
            {"planet": "Sun", "status": "own-sign"},
            {"planet": "Saturn", "status": "own-sign"},
            {"planet": "Moon", "status": "neutral-sign"},
            {"planet": "Mercury", "status": "exalted"},
        ],
    }


class TestGovtJobEngine(unittest.TestCase):
    def test_sun_saturn_conjunct_d1_high_promise(self):
        kundli = {
            "ascendant": "Libra",
            "planets": [
                {"name": "Sun", "sign": "Capricorn", "house": 4},
                {"name": "Saturn", "sign": "Capricorn", "house": 4},
                {"name": "Moon", "sign": "Cancer", "house": 10},
                {"name": "Mars", "sign": "Aries", "house": 7},
                {"name": "Mercury", "sign": "Virgo", "house": 12},
                {"name": "Jupiter", "sign": "Sagittarius", "house": 3},
                {"name": "Venus", "sign": "Pisces", "house": 6},
            ],
            "divisionalCharts": {
                "D9": {
                    "planets": [
                        {"name": "Sun", "sign": "Taurus", "house": 8},
                        {"name": "Saturn", "sign": "Taurus", "house": 8},
                    ],
                },
                "D10": {
                    "planets": [
                        {"name": "Saturn", "sign": "Virgo", "house": 6},
                        {"name": "Sun", "sign": "Leo", "house": 5},
                    ],
                },
            },
            "currentDasha": {"mahadasha": "Saturn", "antardasha": "Mercury"},
        }
        out = assess_govt_job_promise(kundli, _intel(), karakas_d={"AmK": "Sun"})
        self.assertIn(out["govt_promise_level"], ("high", "moderate"))
        self.assertGreaterEqual(out["promise_score"], 30)
        joined = " ".join(out["why"]).lower()
        self.assertIn("sun-saturn", joined)
        self.assertTrue(any("conjunct" in f or "parivartana" in f for f in out["flags"]))

    def test_sun_saturn_parivartana_d1(self):
        kundli = {
            "ascendant": "Aries",
            "planets": [
                {"name": "Sun", "sign": "Capricorn", "house": 10},
                {"name": "Saturn", "sign": "Leo", "house": 5},
            ],
        }
        out = assess_govt_job_promise(kundli, _intel())
        flags = " ".join(out["flags"])
        self.assertIn("parivartana", flags)

    def test_low_promise_defers_timing(self):
        kundli = {
            "ascendant": "Gemini",
            "planets": [
                {"name": "Sun", "sign": "Libra", "house": 5},
                {"name": "Saturn", "sign": "Pisces", "house": 10},
            ],
        }
        promise = assess_govt_job_promise(kundli, {"house_lords": [], "dignities": []})
        full = assess_govt_job(kundli, {"house_lords": [], "dignities": []})
        if promise["govt_promise_level"] == "low":
            self.assertEqual(full["timing"]["status"], "deferred_low_promise")

    def test_prompt_block_locked(self):
        full = assess_govt_job(
            {
                "ascendant": "Libra",
                "planets": [
                    {"name": "Sun", "sign": "Capricorn", "house": 4},
                    {"name": "Saturn", "sign": "Capricorn", "house": 4},
                ],
            },
            _intel(),
        )
        block = format_govt_job_block_for_prompt(full)
        self.assertIn("GOVT JOB ENGINE v1 (LOCKED)", block)
        self.assertIn("GUARD", block)
        self.assertIn("Promise level", block)

    def test_career_bucket_attaches_govt_engine(self):
        from event_timing.career import assess_career, classify_career_question

        q = "Meri sarkari naukri kab lagegi?"
        self.assertEqual(classify_career_question(q), "govt_job")
        kundli = {
            "ascendant": "Libra",
            "planets": [
                {"name": "Sun", "sign": "Capricorn", "house": 4},
                {"name": "Saturn", "sign": "Capricorn", "house": 4},
                {"name": "Moon", "sign": "Cancer", "house": 10},
                {"name": "Mars", "sign": "Aries", "house": 7},
                {"name": "Mercury", "sign": "Virgo", "house": 12},
                {"name": "Jupiter", "sign": "Sagittarius", "house": 3},
                {"name": "Venus", "sign": "Pisces", "house": 6},
            ],
            "currentDasha": {"mahadasha": "Saturn", "antardasha": "Mercury"},
        }
        intel = _intel()
        out = assess_career(kundli, intel, kp={}, question=q)
        self.assertEqual(out["bucket"], "govt_job")
        self.assertIn("govt_job_engine", out)
        self.assertIn("govt_job_prompt_block", out)


if __name__ == "__main__":
    unittest.main()

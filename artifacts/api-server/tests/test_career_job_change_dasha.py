"""Job-change dasha: 3L/5L/9L change lords + PD cascade."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _intel() -> dict:
    return {
        "house_lords": [
            {"house": 3, "lord": "Mars"},
            {"house": 5, "lord": "Jupiter"},
            {"house": 6, "lord": "Mercury"},
            {"house": 9, "lord": "Sun"},
            {"house": 10, "lord": "Saturn"},
            {"house": 11, "lord": "Venus"},
            {"house": 2, "lord": "Moon"},
        ],
        "dignities": [],
    }


def _kundli_with_dashas() -> dict:
    today = datetime.utcnow()
    ad_start = today - timedelta(days=120)
    ad_end = today + timedelta(days=240)
    pd1_end = today + timedelta(days=30)
    pd2_start = pd1_end
    pd2_end = today + timedelta(days=90)

    return {
        "planets": [
            {"name": "Mars", "house": 3},
            {"name": "Jupiter", "house": 5},
            {"name": "Mercury", "house": 6},
            {"name": "Sun", "house": 9},
            {"name": "Saturn", "house": 10},
        ],
        "currentDasha": {
            "mahadasha": "Rahu",
            "antardasha": "Saturn",
            "pratyantardasha": "Venus",
            "startDate": ad_start.strftime("%Y-%m-%d"),
            "endDate": ad_end.strftime("%Y-%m-%d"),
        },
        "dashas": [
            {
                "planet": "Rahu",
                "subDashas": [
                    {
                        "planet": "Saturn",
                        "startDate": ad_start.strftime("%Y-%m-%d"),
                        "endDate": ad_end.strftime("%Y-%m-%d"),
                        "subDashas": [
                            {
                                "planet": "Venus",
                                "startDate": ad_start.strftime("%Y-%m-%d"),
                                "endDate": pd1_end.strftime("%Y-%m-%d"),
                            },
                            {
                                "planet": "Jupiter",
                                "startDate": pd2_start.strftime("%Y-%m-%d"),
                                "endDate": pd2_end.strftime("%Y-%m-%d"),
                            },
                        ],
                    }
                ],
            }
        ],
    }


class TestCareerJobChangeDasha(unittest.TestCase):
    def test_lord_sets_split_change_and_outcome(self):
        from event_timing.career.career_timing import _career_dasha_lord_sets

        sets = _career_dasha_lord_sets(_intel(), {"AmK": "Mercury"}, "job_change")
        self.assertEqual(sets["change_lords_set"], ["Jupiter", "Mars", "Sun"])
        self.assertEqual(sets["outcome_lords_set"], ["Mercury", "Saturn", "Venus"])

    def test_trigger_finds_next_change_pd_window(self):
        from event_timing.career.career_timing import _trigger_vimshottari

        t1 = _trigger_vimshottari(
            _kundli_with_dashas(),
            _intel(),
            {"AmK": "Mercury"},
            bucket="job_change",
        )
        self.assertIn("Jupiter", t1["change_lords_set"])
        self.assertFalse(t1["current_change_active"])
        nxt = t1["next_career_window"]
        self.assertIsNotNone(nxt)
        self.assertEqual(nxt["pd"], "Jupiter")
        self.assertIn("5L", nxt["reason"])

    def test_step_audit_exposes_change_lords(self):
        from event_timing.career.career_timing import (
            _trigger_vimshottari,
            build_career_timing_step_audit,
        )

        t1 = _trigger_vimshottari(
            _kundli_with_dashas(),
            _intel(),
            {"AmK": "Mercury"},
            bucket="job_change",
        )
        audit = build_career_timing_step_audit({
            "bucket": "job_change",
            "tense": "future",
            "triggers": {"T1_vimshottari": t1},
            "timing_window": {"current": {}, "next_career": t1["next_career_window"]},
            "layers": {
                "L1_tenth_house": {"score": 2, "why": ["10L ok"]},
                "L13_ninth_house": {"score": 1, "why": ["9L ok"], "ninth_lord": "Sun"},
                "L14_fifth_house": {"score": 1, "why": ["5L ok"], "fifth_lord": "Jupiter"},
                "L35_third_house": {"score": 1, "why": ["3L ok"], "third_lord": "Mars"},
            },
        })
        self.assertEqual(audit["step6"]["change_lords_set"], ["Jupiter", "Mars", "Sun"])
        self.assertEqual(audit["step8"]["next_pd"], "Jupiter")


if __name__ == "__main__":
    unittest.main()

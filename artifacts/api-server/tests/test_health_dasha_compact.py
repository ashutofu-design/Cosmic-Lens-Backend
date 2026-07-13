"""Tests for health timing-only compact dasha on Engine Execution."""
from __future__ import annotations

import json
import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_health.dasha_compact import compute_health_dasha_compact, maybe_attach_dasha_compact
from ask_health.presenter import HEALTH_ENGINE_EXECUTION_JSON_LABEL, to_health_llm_payload
from ask_mr.types import EngineResult
from health_static.health_facts import compute_health_engine_execution


def _sample_kundli_with_dasha():
    now = datetime(2026, 7, 1)
    start = (now - timedelta(days=30)).isoformat()
    end = (now + timedelta(days=90)).isoformat()
    end2 = (now + timedelta(days=400)).isoformat()
    return {
        "ascendant": "Leo",
        "planets": [
            {"name": "Sun", "sign": "Leo", "house": 1},
            {"name": "Moon", "sign": "Scorpio", "house": 4},
            {"name": "Mars", "sign": "Capricorn", "house": 6},
            {"name": "Saturn", "sign": "Aquarius", "house": 7},
            {"name": "Rahu", "sign": "Aries", "house": 9},
            {"name": "Ketu", "sign": "Libra", "house": 3},
            {"name": "Jupiter", "sign": "Sagittarius", "house": 5},
            {"name": "Venus", "sign": "Virgo", "house": 2},
            {"name": "Mercury", "sign": "Cancer", "house": 12},
        ],
        "dashas": [
            {
                "planet": "Saturn",
                "startDate": start,
                "endDate": (now + timedelta(days=2000)).isoformat(),
                "subDashas": [
                    {
                        "planet": "Mercury",
                        "startDate": start,
                        "endDate": end,
                        "subDashas": [
                            {
                                "planet": "Mars",
                                "startDate": start,
                                "endDate": end,
                            }
                        ],
                    },
                    {
                        "planet": "Ketu",
                        "startDate": end,
                        "endDate": end2,
                        "subDashas": [
                            {
                                "planet": "Venus",
                                "startDate": end,
                                "endDate": end2,
                            }
                        ],
                    },
                ],
            }
        ],
    }, now


class HealthDashaCompactTests(unittest.TestCase):
    def test_static_question_no_dasha_on_ee(self):
        kundli, _ = _sample_kundli_with_dasha()
        pack = compute_health_engine_execution(kundli, question="meri sehat kaisi hai")
        self.assertNotIn("dasha_timing_compact", pack)

    def test_timing_question_gets_compact_dasha(self):
        kundli, now = _sample_kundli_with_dasha()
        pack = compute_health_engine_execution(
            kundli, question="2027 me health kab improve hogi?",
        )
        self.assertIn("dasha_timing_compact", pack)
        compact = pack["dasha_timing_compact"]
        self.assertEqual(compact.get("horizon_years"), 10)
        self.assertLessEqual(len(compact.get("top_windows") or []), 5)

        raw = compute_health_dasha_compact(kundli, now=now)
        self.assertLessEqual(len(json.dumps(raw)), 2500)

    def test_maybe_attach_only_for_timing(self):
        kundli, _ = _sample_kundli_with_dasha()
        pack: dict = {"schema_version": "health_engine_execution_v1"}
        maybe_attach_dasha_compact(pack, kundli, "sehat kaisi hai")
        self.assertNotIn("dasha_timing_compact", pack)
        maybe_attach_dasha_compact(pack, kundli, "2027 me health kab improve hogi?")
        self.assertIn("dasha_timing_compact", pack)

    def test_llm_payload_includes_dasha_when_on_ee(self):
        kundli, _ = _sample_kundli_with_dasha()
        q = "2027 me health kab improve hogi?"
        pack = compute_health_engine_execution(kundli, question=q)
        result = EngineResult(
            archetype="health_engine_execution_v1",
            verdict="",
            confidence="medium",
            word_budget=75,
            answer_plan="",
            summary=[],
            evidence=[],
            ignore=[],
            checks={"health_engine_execution": pack},
        )
        text = to_health_llm_payload(result, question=q)
        self.assertTrue(text.startswith(HEALTH_ENGINE_EXECUTION_JSON_LABEL))
        body = text.split("\n", 1)[1].split("\n\n")[0]
        payload = json.loads(body)
        self.assertIn("dasha_timing_compact", payload)


if __name__ == "__main__":
    unittest.main()

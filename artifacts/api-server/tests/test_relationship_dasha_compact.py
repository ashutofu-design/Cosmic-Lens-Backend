"""Tests for relationship timing-only compact dasha on Engine Execution."""
from __future__ import annotations

import json
import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_mr.dasha_compact import (
    compute_relationship_dasha_compact,
    maybe_attach_dasha_compact,
)
from ask_mr.presenter import RELATIONSHIP_ENGINE_EXECUTION_JSON_LABEL, to_relationship_llm_payload
from ask_mr.types import EngineResult
from relationship_static.relationship_facts import compute_relationship_engine_execution


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
            {"name": "Mars", "sign": "Aquarius", "house": 7},
            {"name": "Saturn", "sign": "Capricorn", "house": 6},
            {"name": "Rahu", "sign": "Aries", "house": 9},
            {"name": "Ketu", "sign": "Libra", "house": 3},
            {"name": "Jupiter", "sign": "Sagittarius", "house": 5},
            {"name": "Venus", "sign": "Libra", "house": 3},
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


class RelationshipDashaCompactTests(unittest.TestCase):
    def test_static_question_no_dasha_on_ee(self):
        kundli, _ = _sample_kundli_with_dasha()
        pack = compute_relationship_engine_execution(
            kundli, question="Mera partner loyal hai kya?",
        )
        self.assertNotIn("dasha_timing_compact", pack)

    def test_timing_question_gets_compact_dasha(self):
        kundli, now = _sample_kundli_with_dasha()
        pack = compute_relationship_engine_execution(
            kundli, question="2027 me rishta kab improve hoga?",
        )
        self.assertIn("dasha_timing_compact", pack)
        compact = pack["dasha_timing_compact"]
        self.assertEqual(compact.get("horizon_years"), 10)
        self.assertLessEqual(len(compact.get("top_windows") or []), 5)
        self.assertTrue(
            str(compact.get("schema_version") or "").startswith("relationship_dasha_compact"),
        )

        raw = compute_relationship_dasha_compact(kundli, now=now)
        self.assertLessEqual(len(json.dumps(raw)), 2500)

    def test_maybe_attach_only_for_timing(self):
        kundli, _ = _sample_kundli_with_dasha()
        pack: dict = {"schema_version": "relationship_engine_execution_v1"}
        maybe_attach_dasha_compact(pack, kundli, "partner loyal hai?")
        self.assertNotIn("dasha_timing_compact", pack)
        maybe_attach_dasha_compact(pack, kundli, "2027 me rishta kab improve hoga?")
        self.assertIn("dasha_timing_compact", pack)

    def test_llm_payload_includes_dasha_when_on_ee(self):
        kundli, _ = _sample_kundli_with_dasha()
        q = "2027 me rishta kab improve hoga?"
        pack = compute_relationship_engine_execution(kundli, question=q)
        result = EngineResult(
            archetype="loyalty_trust",
            verdict="",
            confidence="medium",
            word_budget=75,
            answer_plan="",
            summary=[],
            evidence=[],
            ignore=[],
            checks={
                "relationship_engine_execution": pack,
                "routing_label": "loyalty_trust",
                "unified_execution": True,
            },
        )
        text = to_relationship_llm_payload(result, question=q)
        self.assertTrue(text.startswith(RELATIONSHIP_ENGINE_EXECUTION_JSON_LABEL))
        body = text.split("\n", 1)[1].split("\n\n")[0]
        payload = json.loads(body)
        self.assertIn("dasha_timing_compact", payload)


if __name__ == "__main__":
    unittest.main()

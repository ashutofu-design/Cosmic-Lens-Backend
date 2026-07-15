"""Finance timing-only compact dasha on Engine Execution."""
from __future__ import annotations

import json
import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_finance.dasha_compact import maybe_attach_dasha_compact
from ask_finance.presenter import FINANCE_ENGINE_EXECUTION_JSON_LABEL, to_finance_llm_payload
from ask_mr.types import EngineResult
from finance_static.finance_facts import compute_finance_engine_execution


def _sample_kundli_with_dasha():
    now = datetime(2026, 7, 1)
    start = (now - timedelta(days=30)).isoformat()
    end = (now + timedelta(days=90)).isoformat()
    end2 = (now + timedelta(days=400)).isoformat()
    return {
        "ascendant": "Leo",
        "planets": [
            {"name": "Sun", "sign": "Leo", "house": 1},
            {"name": "Moon", "sign": "Taurus", "house": 10},
            {"name": "Mars", "sign": "Capricorn", "house": 6},
            {"name": "Mercury", "sign": "Virgo", "house": 2},
            {"name": "Jupiter", "sign": "Sagittarius", "house": 5},
            {"name": "Venus", "sign": "Libra", "house": 3},
            {"name": "Saturn", "sign": "Aquarius", "house": 7},
            {"name": "Rahu", "sign": "Aries", "house": 9},
            {"name": "Ketu", "sign": "Libra", "house": 3},
        ],
        "dashas": [
            {
                "planet": "Jupiter",
                "startDate": start,
                "endDate": (now + timedelta(days=2000)).isoformat(),
                "subDashas": [
                    {
                        "planet": "Mercury",
                        "startDate": start,
                        "endDate": end,
                        "subDashas": [
                            {"planet": "Venus", "startDate": start, "endDate": end},
                        ],
                    },
                    {
                        "planet": "Saturn",
                        "startDate": end,
                        "endDate": end2,
                        "subDashas": [
                            {"planet": "Moon", "startDate": end, "endDate": end2},
                        ],
                    },
                ],
            }
        ],
    }, now


class FinanceDashaCompactTests(unittest.TestCase):
    def test_static_no_dasha(self):
        kundli, _ = _sample_kundli_with_dasha()
        pack = compute_finance_engine_execution(kundli, question="meri wealth kaisi hai")
        self.assertNotIn("dasha_timing_compact", pack)

    def test_timing_gets_dasha(self):
        kundli, _ = _sample_kundli_with_dasha()
        pack = compute_finance_engine_execution(
            kundli, question="2027 me paisa kab aayega?",
        )
        self.assertIn("dasha_timing_compact", pack)
        self.assertEqual(pack["dasha_timing_compact"].get("horizon_years"), 10)

    def test_payload_includes_dasha(self):
        kundli, _ = _sample_kundli_with_dasha()
        q = "2027 me paisa kab aayega?"
        pack = compute_finance_engine_execution(kundli, question=q)
        result = EngineResult(
            archetype="wealth_potential",
            verdict="",
            confidence="medium",
            word_budget=70,
            answer_plan="",
            summary=[],
            evidence=[],
            ignore=[],
            checks={"finance_engine_execution": pack, "routing_label": "wealth_potential"},
        )
        text = to_finance_llm_payload(result, question=q)
        self.assertTrue(text.startswith(FINANCE_ENGINE_EXECUTION_JSON_LABEL))
        body = text.split("\n", 1)[1].split("\n\n")[0]
        payload = json.loads(body)
        self.assertIn("dasha_timing_compact", payload)

    def test_maybe_attach(self):
        kundli, _ = _sample_kundli_with_dasha()
        pack: dict = {"schema_version": "finance_engine_execution_v1"}
        maybe_attach_dasha_compact(pack, kundli, "wealth kaisi")
        self.assertNotIn("dasha_timing_compact", pack)
        maybe_attach_dasha_compact(pack, kundli, "2027 me paisa kab aayega?")
        self.assertIn("dasha_timing_compact", pack)


if __name__ == "__main__":
    unittest.main()

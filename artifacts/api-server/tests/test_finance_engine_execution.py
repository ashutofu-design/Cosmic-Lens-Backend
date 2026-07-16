"""Tests for unified finance_engine_execution_v1."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_KUNDLI = {
    "ascendant": "Leo",
    "ascendantDeg": 125.0,
    "planets": [
        {"name": "Sun", "sign": "Leo", "house": 1, "longitude": 125.0},
        {"name": "Moon", "sign": "Taurus", "house": 10, "longitude": 45.0},
        {"name": "Mars", "sign": "Capricorn", "house": 6, "longitude": 280.0},
        {"name": "Mercury", "sign": "Virgo", "house": 2, "longitude": 155.0},
        {"name": "Jupiter", "sign": "Sagittarius", "house": 5, "longitude": 250.0},
        {"name": "Venus", "sign": "Libra", "house": 3, "longitude": 185.0},
        {"name": "Saturn", "sign": "Aquarius", "house": 7, "longitude": 310.0},
        {"name": "Rahu", "sign": "Aries", "house": 9, "longitude": 15.0},
        {"name": "Ketu", "sign": "Libra", "house": 3, "longitude": 195.0},
    ],
    "divisionalCharts": {
        "D9": {
            "ascendant": "Aries",
            "planets": [
                {"name": "Sun", "sign": "Leo", "house": 5},
                {"name": "Venus", "sign": "Libra", "house": 7},
                {"name": "Jupiter", "sign": "Cancer", "house": 4},
                {"name": "Mercury", "sign": "Virgo", "house": 6},
            ],
        }
    },
}


class FinanceEngineExecutionTests(unittest.TestCase):
    def test_pack_shape(self):
        from finance_static.finance_facts import compute_finance_engine_execution

        pack = compute_finance_engine_execution(
            _KUNDLI, question="meri wealth potential kaisi hai?", routing_label="wealth_potential",
        )
        self.assertEqual(pack.get("schema_version"), "finance_engine_execution_v1")
        self.assertIn("d1", pack)
        self.assertIn("d9", pack)
        self.assertIn("dimensions", pack)
        self.assertFalse(pack["d1"].get("error"))
        self.assertIn("planets", pack["d1"])
        self.assertIn("finance_houses", pack["d1"])

    def test_unified_engine_default(self):
        os.environ.pop("ASK_FINANCE_LEGACY_ARCHETYPE_ENGINES", None)
        from ask_finance import run_finance_static_engine

        res = run_finance_static_engine(_KUNDLI, "mere paas paisa kitna hoga?")
        self.assertTrue((res.checks or {}).get("unified_execution"))
        self.assertIn("finance_engine_execution", res.checks or {})
        self.assertEqual(
            (res.checks or {}).get("engine_version"),
            "finance_engine_execution_v1",
        )
        pack = (res.checks or {}).get("finance_engine_execution") or {}
        self.assertEqual(pack.get("divisional_chart_tag"), "D2")
        self.assertIn("D2", pack.get("charts_used") or [])

    def test_gatekeeper_exempt_unified(self):
        os.environ.pop("ASK_FINANCE_LEGACY_ARCHETYPE_ENGINES", None)
        from ask_execution_gatekeeper import check_final_answer_gate, run_post_engine_gate
        from ask_finance import run_finance_static_engine
        from ask_finance.engine import finance_engine_slice_meta
        from ask_finance.presenter import to_finance_llm_payload

        res = run_finance_static_engine(_KUNDLI, "wealth potential", archetype="wealth_potential")
        meta = finance_engine_slice_meta(res)
        chart = to_finance_llm_payload(res, question="wealth potential")
        gate = run_post_engine_gate({}, slice_meta=meta, chart_text=chart, question="wealth")
        self.assertTrue(gate.ok)
        self.assertEqual(gate.rule, "finance_unified_execution")
        final = check_final_answer_gate("maybe unclear", slice_meta=meta, question="wealth")
        self.assertTrue(final.ok)
        self.assertEqual(final.rule, "finance_unified_execution")


if __name__ == "__main__":
    unittest.main()

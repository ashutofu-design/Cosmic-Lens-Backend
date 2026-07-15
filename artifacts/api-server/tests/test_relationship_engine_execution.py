"""Unified relationship_engine_execution_v1 — health-style D1+D9 pack."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_KUNDLI = {
    "ascendant": "Leo",
    "planets": [
        {"name": "Sun", "house": 1, "sign": "Leo"},
        {"name": "Moon", "house": 4, "sign": "Scorpio"},
        {"name": "Mars", "house": 7, "sign": "Aquarius"},
        {"name": "Mercury", "house": 2, "sign": "Virgo"},
        {"name": "Jupiter", "house": 9, "sign": "Aries"},
        {"name": "Venus", "house": 3, "sign": "Libra"},
        {"name": "Saturn", "house": 10, "sign": "Taurus"},
        {"name": "Rahu", "house": 5, "sign": "Sagittarius"},
        {"name": "Ketu", "house": 11, "sign": "Gemini"},
    ],
    "divisionalCharts": {
        "D9": {
            "ascendant": "Aries",
            "planets": [
                {"name": "Sun", "house": 5, "sign": "Leo"},
                {"name": "Moon", "house": 2, "sign": "Taurus"},
                {"name": "Mars", "house": 3, "sign": "Gemini"},
                {"name": "Mercury", "house": 4, "sign": "Cancer"},
                {"name": "Jupiter", "house": 1, "sign": "Aries"},
                {"name": "Venus", "house": 6, "sign": "Virgo"},
                {"name": "Saturn", "house": 7, "sign": "Libra"},
                {"name": "Rahu", "house": 8, "sign": "Scorpio"},
                {"name": "Ketu", "house": 2, "sign": "Taurus"},
            ],
        },
    },
}


class TestRelationshipEngineExecution(unittest.TestCase):
    def test_pack_shape_d1_d9(self):
        from relationship_static.relationship_facts import (
            compute_relationship_engine_execution,
        )

        pack = compute_relationship_engine_execution(
            _KUNDLI, question="loyalty kaisi", routing_label="loyalty_trust",
        )
        self.assertEqual(pack.get("schema_version"), "relationship_engine_execution_v1")
        self.assertIn("d1", pack)
        self.assertIn("d9", pack)
        self.assertFalse(pack["d1"].get("error"))
        self.assertFalse(pack["d9"].get("error"))
        self.assertIn("axes", pack["d1"])
        self.assertIn("seventh_lord", pack["d1"]["axes"])
        self.assertIn("venus", pack["d1"]["axes"])
        self.assertIn("manglik", pack)
        self.assertEqual(pack.get("routing_label"), "loyalty_trust")
        self.assertIn("vargottama_details", pack)

    def test_unified_engine_no_legacy_dispatch(self):
        os.environ.pop("ASK_MR_LEGACY_ARCHETYPE_ENGINES", None)
        from ask_mr import run_mr_static_engine
        from ask_mr.presenter import to_relationship_llm_payload

        res = run_mr_static_engine(
            _KUNDLI, "Mera partner loyal hai kya?", archetype="loyalty_trust",
        )
        self.assertEqual(res.archetype, "loyalty_trust")
        self.assertTrue((res.checks or {}).get("unified_execution"))
        self.assertEqual(
            (res.checks or {}).get("engine_version"),
            "relationship_engine_execution_v1",
        )
        pack = (res.checks or {}).get("relationship_engine_execution") or {}
        self.assertEqual(pack.get("schema_version"), "relationship_engine_execution_v1")
        payload = to_relationship_llm_payload(res, question="Mera partner loyal hai kya?")
        self.assertIn("RELATIONSHIP_ENGINE_EXECUTION_JSON", payload)
        self.assertIn("routing_label", payload)

    def test_two_labels_same_schema(self):
        os.environ.pop("ASK_MR_LEGACY_ARCHETYPE_ENGINES", None)
        from ask_mr import run_mr_static_engine

        a = run_mr_static_engine(_KUNDLI, "loyalty trust kaisi", archetype="loyalty_trust")
        b = run_mr_static_engine(_KUNDLI, "relationship overall", archetype="general_mr")
        self.assertEqual(a.archetype, "loyalty_trust")
        self.assertEqual(b.archetype, "general_mr")
        sa = (a.checks or {}).get("relationship_engine_execution", {}).get("schema_version")
        sb = (b.checks or {}).get("relationship_engine_execution", {}).get("schema_version")
        self.assertEqual(sa, sb)
        self.assertEqual(sa, "relationship_engine_execution_v1")

    def test_legacy_flag_runs_archetype_engine(self):
        os.environ["ASK_MR_LEGACY_ARCHETYPE_ENGINES"] = "1"
        try:
            from ask_mr import run_mr_static_engine

            res = run_mr_static_engine(
                _KUNDLI, "Kya main manglik hun?", archetype="manglik",
            )
            self.assertEqual(res.archetype, "manglik")
            # Legacy still attaches unified pack for admin, and has manglik verdict
            self.assertTrue("Manglik" in (res.verdict or "") or res.verdict)
            self.assertIn("relationship_engine_execution", res.checks or {})
        finally:
            os.environ.pop("ASK_MR_LEGACY_ARCHETYPE_ENGINES", None)

    def test_gatekeeper_exempt_unified(self):
        os.environ.pop("ASK_MR_LEGACY_ARCHETYPE_ENGINES", None)
        from ask_execution_gatekeeper import check_final_answer_gate, run_post_engine_gate
        from ask_mr import run_mr_static_engine
        from ask_mr.engine import mr_engine_slice_meta
        from ask_mr.presenter import to_relationship_llm_payload

        res = run_mr_static_engine(_KUNDLI, "commitment kaisi", archetype="commitment")
        meta = mr_engine_slice_meta(res)
        chart = to_relationship_llm_payload(res, question="commitment kaisi")
        gate = run_post_engine_gate({}, slice_meta=meta, chart_text=chart, question="commitment")
        self.assertTrue(gate.ok)
        self.assertEqual(gate.rule, "relationship_unified_execution")

        final = check_final_answer_gate(
            "maybe something unclear",
            slice_meta=meta,
            question="commitment kaisi",
        )
        self.assertTrue(final.ok)
        self.assertEqual(final.rule, "relationship_unified_execution")


if __name__ == "__main__":
    unittest.main()

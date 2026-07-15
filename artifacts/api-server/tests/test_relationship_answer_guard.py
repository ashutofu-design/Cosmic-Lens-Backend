"""Relationship answer guard — soft repair parity with health."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_mr.answer_guard import guard_relationship_answer, verify_relationship_answer


class RelationshipAnswerGuardTests(unittest.TestCase):
    def test_clean_answer_ok(self):
        ok, issues = verify_relationship_answer(
            "partner loyal hai?",
            "Venus 3rd me hai — loyalty mixed dikhti hai.",
            {"checks": {}},
        )
        self.assertTrue(ok)
        self.assertEqual(issues, [])

    def test_strips_template_labels(self):
        text, meta = guard_relationship_answer(
            "commitment kaisi?",
            "Seedha jawab: Saturn 7th pe pressure hai.",
            {"checks": {}},
        )
        self.assertTrue(meta.get("repaired"))
        self.assertNotIn("Seedha jawab", text)
        self.assertIn("Saturn", text)

    def test_timing_year_ok_when_user_asks_when(self):
        ok, issues = verify_relationship_answer(
            "2027 me rishta kab improve hoga?",
            "2027 me Venus AD me improvement window dikhti hai.",
            {
                "checks": {
                    "relationship_engine_execution": {
                        "dasha_timing_compact": {"current": {"md": "Saturn"}},
                    }
                }
            },
        )
        self.assertTrue(ok)
        self.assertNotIn("unsolicited_timing", issues)

    def test_exact_date_guarantee_stripped(self):
        text, meta = guard_relationship_answer(
            "shaadi kab hogi?",
            "Exact marriage date 12 March pe pakka hai.",
            {"checks": {}},
        )
        self.assertTrue(meta.get("repaired") or "exact_date_guarantee" in (meta.get("issues") or []))
        self.assertNotRegex(text, r"(?i)exact\s+marriage\s+date")


if __name__ == "__main__":
    unittest.main()

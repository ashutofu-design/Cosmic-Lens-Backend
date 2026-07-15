"""Ask path must not run milan_engine_v1 — MR D1+D9 only."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_mr.classifier import classify_mr_archetype
from event_timing.routing_audit import audit_question_routing


class AskMilanStoppedTests(unittest.TestCase):
    def test_kundli_match_routes_to_mr_not_milan_engine(self):
        r = audit_question_routing("Hamari kundli match kaisi hai?")
        self.assertFalse(r.is_timing)
        self.assertEqual(r.sub_bucket, "compatibility")
        self.assertIn("mr_engine_v1", r.engine)
        self.assertNotIn("milan_engine", r.engine)

    def test_compatible_routes_to_mr(self):
        r = audit_question_routing("Hum compatible hain kya?")
        self.assertIn("mr_engine_v1", r.engine)
        self.assertNotIn("milan_engine", r.engine)

    def test_classifier_label_compatibility(self):
        self.assertEqual(
            classify_mr_archetype("Hamari kundli match kaisi hai?"),
            "compatibility",
        )
        self.assertEqual(
            classify_mr_archetype("Kundli milan kaisa hai?"),
            "compatibility",
        )


if __name__ == "__main__":
    unittest.main()

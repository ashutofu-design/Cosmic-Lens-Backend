"""Tests for question-aware health selected JSON blocks."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_health.selected_blocks import (
    build_health_selected_blocks,
    classify_health_question_focus,
)


class HealthSelectedBlocksTests(unittest.TestCase):
    def test_travel_health_focus(self):
        q = "me jab bhi travel karta hun koi na koi health issue aa jaata he aisa kyun"
        self.assertEqual(classify_health_question_focus(q), "travel_health")
        pack = build_health_selected_blocks(q, "Safar me immunity kamzor rehti hai.")
        self.assertTrue(pack["applies"])
        ids = {b["id"] for b in pack["expected_blocks"]}
        self.assertIn("d1.house_lords.h6", ids)
        self.assertIn("d1.house_lords.h9", ids)

    def test_used_planet_house_cite(self):
        pack = build_health_selected_blocks(
            "mujhse thandi bahut rehti hai",
            "Saturn 6th ghar me hai, isliye thandi tendency dikhti hai.",
        )
        used = pack["used_in_answer"]
        self.assertIn("Saturn", used["planets"])
        self.assertIn(6, used["houses"])
        self.assertTrue(any("Saturn H6" in c for c in used["planet_house_cites"]))


if __name__ == "__main__":
    unittest.main()

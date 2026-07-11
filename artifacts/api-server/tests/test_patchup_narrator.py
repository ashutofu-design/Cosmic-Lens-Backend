"""Patch-up narrator — intent-anchored, verdict-consistent template tests."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_mr.v2.engines.patchup import run_patchup_v2
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.patchup_narrator import (
    engine_result_to_patchup_json,
    render_patchup_template_answer,
    validate_patchup_narrator_output,
    _build_angle_direct_answer,
)

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Saturn", "sign": "Aries", "house": 7},
        {"name": "Mars", "sign": "Capricorn", "house": 7},
    ],
    "dasha": {"mahadasha": "Saturn", "antardasha": "Mars"},
}

EX_RETURN_Q = "kya mera previous relationship wapas aayega"


class PatchupNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_patchup_v2(SAMPLE_KUNDLI, EX_RETURN_Q)
        self.result = v2_to_engine_result(self.out)

    def test_ex_return_angle_detected(self):
        data = engine_result_to_patchup_json(self.result, question=EX_RETURN_Q)
        self.assertEqual(data.get("answer_focus"), "ex_return")
        self.assertEqual(data.get("reconciliation_angle"), "ex_return")

    def test_unlikely_opening_not_haan_chances(self):
        data = engine_result_to_patchup_json(self.result, question=EX_RETURN_Q)
        data["patchup_level"] = "unlikely"
        data["final_verdict"] = "Unlikely"
        data["direct_answer"] = _build_angle_direct_answer("unlikely", "ex_return")
        text = render_patchup_template_answer(data, EX_RETURN_Q)
        self.assertNotRegex(text, r"(?i)haan,?\s*chances|the\s+big\s+picture")
        self.assertIn("kamzor", text.lower())
        self.assertIn("wapas", text.lower())

    def test_template_uses_engine_challenges(self):
        data = engine_result_to_patchup_json(self.result, question=EX_RETURN_Q)
        text = data.get("locked_template") or render_patchup_template_answer(data, EX_RETURN_Q)
        self.assertIn("dhyan dene layak", text.lower())
        self.assertNotIn("clarity", text.lower())

    def test_validate_rejects_contradiction(self):
        data = engine_result_to_patchup_json(self.result, question=EX_RETURN_Q)
        data["patchup_level"] = "unlikely"
        bad = "Haan, chances hain ex wapas aayega. Confidence Low (19%) hai kyunki test."
        ok, issues = validate_patchup_narrator_output(bad, data)
        self.assertFalse(ok)
        self.assertIn("contradiction_unlikely_verdict", issues)

    def test_validate_accepts_locked_template(self):
        data = engine_result_to_patchup_json(self.result, question=EX_RETURN_Q)
        text = data.get("locked_template") or ""
        ok, issues = validate_patchup_narrator_output(text, data)
        self.assertTrue(ok, msg=str(issues))


if __name__ == "__main__":
    unittest.main()

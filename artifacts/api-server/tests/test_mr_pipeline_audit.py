"""Tests for MR pipeline step audit."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_mr.pipeline_audit import build_mr_step_audit_from_result
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.commitment import run_commitment_v2

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Jupiter", "sign": "Libra", "house": 11},
        {"name": "Saturn", "sign": "Aries", "house": 5},
    ],
    "dasha": {"mahadasha": "Venus", "antardasha": "Jupiter"},
}


class MrPipelineAuditTests(unittest.TestCase):
    def test_step_audit_saved_from_engine_result(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        out = run_commitment_v2(
            SAMPLE_KUNDLI,
            "Kya mera partner genuinely commitment karega ya sirf timepass kar raha hai?",
        )
        result = v2_to_engine_result(out)
        audit = build_mr_step_audit_from_result(result)
        self.assertIn("step4", audit)
        self.assertEqual(audit["step4"]["name"], "Rules Fired")
        self.assertGreater(len(audit["step4"].get("fired") or []), 0)
        self.assertIn("step_order", audit)


if __name__ == "__main__":
    unittest.main()

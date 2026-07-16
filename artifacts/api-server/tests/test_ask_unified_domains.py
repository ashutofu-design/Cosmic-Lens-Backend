"""Smoke test: unified stack for remaining Ask domains."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_unified import build_unified_engine_result, to_domain_llm_payload
from ask_unified.specs import all_domain_keys

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
}


class UnifiedDomainStackTests(unittest.TestCase):
    def test_all_domain_specs_build_ee(self):
        for key in all_domain_keys():
            with self.subTest(domain=key):
                res = build_unified_engine_result(
                    domain=key,
                    kundli=_KUNDLI,
                    question=f"mere {key} ke bare me batao",
                    archetype=f"general_{key}",
                )
                checks = dict(res.checks or {})
                self.assertTrue(checks.get("unified_execution"), msg=key)
                pack = checks.get(f"{key}_engine_execution")
                self.assertIsInstance(pack, dict, msg=key)
                self.assertEqual(pack.get("schema_version"), f"{key}_engine_execution_v1", msg=key)
                self.assertIn("d1", pack)
                self.assertIn("dimensions", pack)
                text = to_domain_llm_payload(res, domain=key, question=f"{key}?")
                self.assertIn("ENGINE_EXECUTION_JSON", text)
                self.assertIn("QUESTION_PRIORITY_FACTS", text)

    def test_career_engine_entry(self):
        from ask_career import run_career_static_engine

        res = run_career_static_engine(_KUNDLI, "meri career kaisi hai?")
        self.assertTrue((res.checks or {}).get("unified_execution"))
        self.assertIn("career_engine_execution", res.checks or {})


if __name__ == "__main__":
    unittest.main()

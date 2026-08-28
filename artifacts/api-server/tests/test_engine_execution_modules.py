"""Engine execution D1/D9 module check flags."""

from __future__ import annotations

import unittest

from ask_engine_execution_common import (
    attach_modules_checked,
    build_modules_checked,
    chart_module_ok,
)


class EngineExecutionModulesTests(unittest.TestCase):
    def test_llm_used_d1_when_planet_cited(self):
        pack = {
            "d1": {
                "ascendant": "Leo",
                "planets": [{"name": "Saturn", "sign": "Capricorn", "house": 6}],
            },
            "d9": {
                "ascendant": "Aries",
                "planets": [{"name": "Saturn", "sign": "Aries", "house": 1}],
            },
        }
        answer = "Saturn 6th house me weak pressure de raha hai."
        rows = build_modules_checked(pack, answer=answer)
        d1 = next(r for r in rows if r["module"] == "D1")
        self.assertTrue(d1["engine_loaded"])
        self.assertTrue(d1["llm_used"])

    def test_llm_not_used_d9_without_cite(self):
        pack = attach_modules_checked({
            "d1": {"ascendant": "Leo", "planets": [{"name": "Sun", "house": 1}]},
            "d9": {"ascendant": "Aries", "planets": [{"name": "Sun", "house": 1}]},
        })
        rows = build_modules_checked(
            pack,
            answer="Sun strong lagna support deta hai.",
        )
        d9 = next(r for r in rows if r["module"] == "D9")
        self.assertTrue(d9["engine_loaded"])
        self.assertFalse(d9["llm_used"])

    def test_llm_used_d9_when_navamsa_cited(self):
        pack = {
            "d1": {"planets": [{"name": "Venus", "house": 7}]},
            "d9": {"planets": [{"name": "Venus", "house": 3}]},
        }
        rows = build_modules_checked(pack, answer="Navamsa me Venus strong hai.")
        d9 = next(r for r in rows if r["module"] == "D9")
        self.assertTrue(d9["llm_used"])

    def test_dasha_llm_used(self):
        pack = {
            "d1": {"planets": [{"name": "Moon", "house": 4}]},
            "d9": {"planets": [{"name": "Moon", "house": 2}]},
            "dasha_timing_compact": {
                "current": {"md": "Saturn", "ad": "Mercury", "pd": "Venus"},
            },
        }
        rows = build_modules_checked(
            pack,
            answer="Saturn mahadasha chal rahi hai — 2027 tak focus career par.",
            required_modules=["D1", "D9", "DASHA"],
        )
        dasha = next(r for r in rows if r["module"] == "DASHA")
        self.assertTrue(dasha["llm_used"])

    def test_chart_module_ok(self):
        self.assertTrue(chart_module_ok({"planets": [{"name": "Sun"}]}))
        self.assertFalse(chart_module_ok({"error": "missing"}))


if __name__ == "__main__":
    unittest.main()

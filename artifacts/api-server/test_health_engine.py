"""
test_health_engine.py — unit tests for Health Timing Engine v1.

Run from artifacts/api-server:
    python3 test_health_engine.py
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from event_timing.health.health_engine_v1 import (
    compute_health_window,
    _step1_d1_filter,
    _step3_kp_layer,
    _detect_yogas,
    _aspects_house,
    _house_lord,
    _severity_of_window,
    _recommendation_tier,
    _derive_verdict,
    _SIGN_IDX,
)


def _load_fixture(path: str) -> dict:
    raw = open(path).read()
    data = json.loads(raw)
    if isinstance(data, str):
        data = json.loads(data)
    return data


class TestHelpers(unittest.TestCase):
    def test_house_lord(self):
        # Sagittarius lagna (idx 8) → 6th house = Taurus → Venus
        self.assertEqual(_house_lord(8, 6), "Venus")
        # Aries lagna (idx 0) → 6th house = Virgo → Mercury
        self.assertEqual(_house_lord(0, 6), "Mercury")
        # Aries lagna → 8th house = Scorpio → Mars
        self.assertEqual(_house_lord(0, 8), "Mars")

    def test_aspects_house_jupiter_5_9(self):
        # Jupiter in 1H aspects 5H, 7H, 9H
        self.assertTrue(_aspects_house("Jupiter", 1, 5))
        self.assertTrue(_aspects_house("Jupiter", 1, 7))
        self.assertTrue(_aspects_house("Jupiter", 1, 9))
        self.assertFalse(_aspects_house("Jupiter", 1, 6))

    def test_aspects_house_saturn_3_10(self):
        # Saturn in 1H aspects 3H, 7H, 10H
        self.assertTrue(_aspects_house("Saturn", 1, 3))
        self.assertTrue(_aspects_house("Saturn", 1, 7))
        self.assertTrue(_aspects_house("Saturn", 1, 10))

    def test_aspects_house_mars_4_8(self):
        # Mars in 2H aspects 5H (4th), 8H (7th), 9H (8th)
        self.assertTrue(_aspects_house("Mars", 2, 5))
        self.assertTrue(_aspects_house("Mars", 2, 8))
        self.assertTrue(_aspects_house("Mars", 2, 9))

    def test_aspects_house_planet_aspecting_6th_from_12(self):
        # Saturn in 12H aspects 2H (3rd), 6H (7th), 9H (10th)
        self.assertTrue(_aspects_house("Saturn", 12, 6))


class TestSeverityVerdict(unittest.TestCase):
    def test_severity_bands(self):
        self.assertEqual(_severity_of_window(2.0, 0.0), "stable")
        self.assertEqual(_severity_of_window(4.0, 0.0), "mild")
        self.assertEqual(_severity_of_window(7.0, 0.0), "moderate")
        self.assertEqual(_severity_of_window(10.0, 0.0), "serious")
        # Transit load can push moderate→serious
        self.assertEqual(_severity_of_window(7.0, 2.5), "serious")

    def test_recommendation_tier(self):
        self.assertEqual(_recommendation_tier("stable", 0, 30), "monitor")
        self.assertEqual(_recommendation_tier("moderate", 0, 30),
                          "preventive")
        self.assertEqual(_recommendation_tier("serious", 1, 30), "consult")
        self.assertEqual(_recommendation_tier("serious", 3, 30),
                          "urgent_consult")

    def test_derive_verdict_high_risk(self):
        yogas = [{"name": "Arishta-X", "severity": "high",
                   "planets": ["Moon"]}]
        v, b = _derive_verdict(8.5, "WEAK", yogas, 0.0)
        self.assertEqual(v, "HIGH_RISK_WINDOW")
        self.assertEqual(b, "WEAK")

    def test_derive_verdict_strong(self):
        yogas = [{"name": "Subhakartari", "severity": "protective",
                   "planets": ["Jupiter"]}]
        v, b = _derive_verdict(2.0, "STRONG", yogas, 0.0)
        self.assertEqual(v, "STRONG_VITALITY")


class TestStep1Filter(unittest.TestCase):
    def test_lagna_lord_always_in_filter(self):
        # Aries lagna → 1L = Mars
        kundli = {
            "ascendant": "Aries",
            "planets": [
                {"name": "Sun",     "house": 1, "sign": "Aries"},
                {"name": "Moon",    "house": 7, "sign": "Libra"},
                {"name": "Mars",    "house": 1, "sign": "Aries"},
                {"name": "Mercury", "house": 2, "sign": "Taurus"},
                {"name": "Jupiter", "house": 5, "sign": "Leo"},
                {"name": "Venus",   "house": 11, "sign": "Aquarius"},
                {"name": "Saturn",  "house": 10, "sign": "Capricorn"},
                {"name": "Rahu",    "house": 3, "sign": "Gemini"},
                {"name": "Ketu",    "house": 9, "sign": "Sagittarius"},
            ],
        }
        d1 = _step1_d1_filter(kundli, _SIGN_IDX["Aries"])
        # Mars is 1L AND occupies 1H → must survive
        self.assertTrue(d1["Mars"]["in_filter"])
        # Saturn is karaka (chronic) AND 11L → score should be > floor
        self.assertTrue(d1["Saturn"]["in_filter"])

    def test_planet_aspecting_6th_picked_up(self):
        # Aries lagna, Saturn in 12H aspects 6H (7th aspect)
        kundli = {
            "ascendant": "Aries",
            "planets": [
                {"name": "Saturn", "house": 12, "sign": "Pisces"},
            ],
        }
        d1 = _step1_d1_filter(kundli, _SIGN_IDX["Aries"])
        self.assertTrue(d1["Saturn"]["aspects_6"])
        self.assertIn("aspects 6H", d1["Saturn"]["links"])

    def test_planets_occupying_6th_picked_up(self):
        kundli = {
            "ascendant": "Aries",
            "planets": [
                {"name": "Mars", "house": 6, "sign": "Virgo"},
            ],
        }
        d1 = _step1_d1_filter(kundli, _SIGN_IDX["Aries"])
        self.assertEqual(d1["Mars"]["occupies"], 6)
        self.assertIn("occupies 6H", d1["Mars"]["links"])


class TestKpLayer(unittest.TestCase):
    def test_kp_csl_6_signifies_dusthana(self):
        kp = {
            "cusps": [{"house": 6, "sl": "Saturn"},
                       {"house": 8, "sl": "Jupiter"}],
            "significations": {"Saturn": [6, 8], "Jupiter": [5, 9, 11]},
        }
        out = _step3_kp_layer(kp, lagna_si=0)
        self.assertEqual(out["csl_6"], "Saturn")
        self.assertEqual(out["verdict_6"], "ILLNESS_YES")
        self.assertEqual(out["csl_8"], "Jupiter")
        self.assertEqual(out["verdict_8"], "CHRONIC_NO")

    def test_kp_missing_cusps_unknown(self):
        out = _step3_kp_layer({}, lagna_si=0)
        self.assertEqual(out["verdict_6"], "UNKNOWN")
        self.assertEqual(out["verdict_8"], "UNKNOWN")


class TestYogas(unittest.TestCase):
    def test_papakartari_around_lagna(self):
        # Malefics in 12H and 2H squeeze the Lagna
        planets = [
            {"name": "Saturn", "house": 12},
            {"name": "Mars",   "house": 2},
        ]
        yogas = _detect_yogas({}, lagna_si=0, planets=planets)
        names = [y["name"] for y in yogas]
        self.assertTrue(any("Papakartari (Lagna)" in n for n in names))

    def test_subhakartari_protective(self):
        planets = [
            {"name": "Jupiter", "house": 12},
            {"name": "Venus",   "house": 2},
        ]
        yogas = _detect_yogas({}, lagna_si=0, planets=planets)
        names = [y["name"] for y in yogas]
        self.assertTrue(any("Subhakartari" in n for n in names))

    def test_arishta_moon_with_8L_in_dusthana(self):
        # Aries lagna → 8L = Mars. Moon + Mars together in 8H
        planets = [
            {"name": "Moon", "house": 8},
            {"name": "Mars", "house": 8},
        ]
        yogas = _detect_yogas({}, lagna_si=0, planets=planets)
        names = [y["name"] for y in yogas]
        self.assertTrue(any("Arishta" in n for n in names))


class TestFullPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kundli = _load_fixture("/tmp/k.json")

    def test_pipeline_produces_required_fields(self):
        out = compute_health_window(self.kundli, intel={},
                                      kp=self.kundli.get("kp"))
        for field in ("verdict", "band", "current_window",
                       "next_3_windows", "protection_windows",
                       "affected_systems", "recommendation_tier",
                       "top_health_planets", "weighted_breakdown",
                       "kp_layer", "transits", "ashtakavarga",
                       "yogas", "risk_flags", "factors",
                       "llm_directives", "engine_version"):
            self.assertIn(field, out, f"Missing field: {field}")
        self.assertEqual(out["engine_version"], "v1.0.0")
        self.assertIn(out["verdict"],
                       ("STRONG_VITALITY", "STABLE", "VULNERABLE",
                        "HIGH_RISK_WINDOW", "UNKNOWN"))
        self.assertIn(out["recommendation_tier"],
                       ("monitor", "preventive", "consult",
                        "urgent_consult"))

    def test_mandatory_disclaimer_in_directives(self):
        out = compute_health_window(self.kundli, intel={},
                                      kp=self.kundli.get("kp"))
        self.assertIn("MEDICAL_DISCLAIMER", out["llm_directives"])
        self.assertIn("NO_DIAGNOSIS_NAMING", out["llm_directives"])
        self.assertIn("NO_CURE_GUARANTEE", out["llm_directives"])

    def test_top_health_planets_have_breakdown(self):
        out = compute_health_window(self.kundli, intel={},
                                      kp=self.kundli.get("kp"))
        for r in out["top_health_planets"]:
            for k in ("name", "score", "d1", "d9", "kp",
                       "karaka", "links", "significations"):
                self.assertIn(k, r)

    def test_empty_kundli_returns_unknown(self):
        out = compute_health_window({})
        self.assertEqual(out["verdict"], "UNKNOWN")

    def test_lagna_missing_returns_unknown(self):
        out = compute_health_window({"planets": [{"name": "Sun"}]})
        self.assertEqual(out["verdict"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main(verbosity=2)

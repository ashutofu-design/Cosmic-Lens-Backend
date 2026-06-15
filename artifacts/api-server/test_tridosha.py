"""Tests for Vata / Pitta / Kapha — health_tridosha_v1 (D1 + D9 + KP 6th CSL)."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vedic.health_tridosha_engine import compute_tridosha_balance
from vedic.life_specifics import compute_health_specifics


def _sample_planets() -> list:
    return [
        {"name": "Sun", "house": 5, "sign": "Leo"},
        {"name": "Moon", "house": 4, "sign": "Cancer"},
        {"name": "Mars", "house": 6, "sign": "Virgo"},
        {"name": "Mercury", "house": 3, "sign": "Gemini"},
        {"name": "Jupiter", "house": 9, "sign": "Sagittarius"},
        {"name": "Venus", "house": 2, "sign": "Taurus"},
        {"name": "Saturn", "house": 12, "sign": "Pisces"},
        {"name": "Rahu", "house": 8, "sign": "Scorpio"},
        {"name": "Ketu", "house": 2, "sign": "Taurus"},
    ]


def _sample_kundli(asc: str = "Aries") -> dict:
    planets = _sample_planets()
    d9_planets = []
    asc_idx = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
               "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"].index(asc)
    for p in planets:
        d9_planets.append({**p, "house": ((["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                                            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
                                           .index(p["sign"]) - asc_idx) % 12) + 1})
    return {
        "ascendant": asc,
        "planets": planets,
        "divisionalCharts": {
            "D9": {"ascendant": asc, "ascendantSignIndex": asc_idx, "planets": d9_planets},
        },
        "kp": {
            "cusps": [{"house": 6, "sl": "Moon"}],
            "significations": {"Moon": [6, 8]},
        },
    }


class TestTridosha(unittest.TestCase):
    def test_percentages_sum_to_100(self):
        out = compute_tridosha_balance(_sample_planets(), 0, _sample_kundli())
        bal = out["dosha_balance"]
        self.assertEqual(sum(bal.values()), 100)
        for k in ("vata", "pitta", "kapha"):
            self.assertIn(k, bal)
            self.assertGreaterEqual(bal[k], 0)

    def test_engine_tag(self):
        out = compute_tridosha_balance(_sample_planets(), 0, _sample_kundli())
        self.assertEqual(out["engine"], "health_tridosha_v1")

    def test_states_present(self):
        out = compute_tridosha_balance(_sample_planets(), 0, _sample_kundli())
        for k in ("vata", "pitta", "kapha"):
            self.assertIn(
                out["dosha_states"][k],
                ("Balanced", "Afflicted", "Elevated"),
            )

    def test_kp_6th_csl_meta(self):
        out = compute_tridosha_balance(_sample_planets(), 0, _sample_kundli())
        kp = out.get("kp_6th_csl") or {}
        self.assertEqual(kp.get("csl_planet"), "Moon")
        self.assertIn(kp.get("verdict"), ("DOSHA_PROMISE_ACTIVE", "IMMUNITY_HIGH", "NEUTRAL", "UNKNOWN"))

    def test_health_specifics_includes_tridosha(self):
        k = _sample_kundli()
        deep = compute_health_specifics(k["planets"], 0, kundli=k)
        self.assertEqual(sum(deep["dosha_balance"].values()), 100)
        self.assertEqual(deep.get("tridosha_engine"), "health_tridosha_v1")
        self.assertIn("d9_immunity_verdict", deep)
        self.assertIn("kp_6th_csl", deep)


if __name__ == "__main__":
    unittest.main()

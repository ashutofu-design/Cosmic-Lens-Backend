"""Tests for health_tridosha_v1 — D1 + D9 + KP 6th CSL chain."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vedic.health_tridosha_engine import compute_tridosha_balance
from vedic.life_specifics import compute_health_specifics


def _sample_planets() -> list:
    return [
        {"name": "Sun", "house": 5, "sign": "Leo", "longitude": 135.0},
        {"name": "Moon", "house": 4, "sign": "Cancer", "longitude": 95.0},
        {"name": "Mars", "house": 6, "sign": "Virgo", "longitude": 165.0},
        {"name": "Mercury", "house": 3, "sign": "Gemini", "longitude": 75.0},
        {"name": "Jupiter", "house": 9, "sign": "Sagittarius", "longitude": 255.0},
        {"name": "Venus", "house": 2, "sign": "Taurus", "longitude": 45.0},
        {"name": "Saturn", "house": 12, "sign": "Pisces", "longitude": 350.0},
        {"name": "Rahu", "house": 8, "sign": "Scorpio", "longitude": 220.0},
        {"name": "Ketu", "house": 2, "sign": "Taurus", "longitude": 40.0},
    ]


def _sample_kundli(asc: str = "Aries", dusthana_script: list | None = None) -> dict:
    planets = _sample_planets()
    asc_idx = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ].index(asc)
    d9_planets = []
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    for p in planets:
        si = signs.index(p["sign"])
        d9_planets.append({**p, "house": ((si - asc_idx) % 12) + 1})

    script = dusthana_script if dusthana_script is not None else [6, 8]
    return {
        "ascendant": asc,
        "planets": planets,
        "divisionalCharts": {
            "D9": {"ascendant": asc, "ascendantSignIndex": asc_idx, "planets": d9_planets},
        },
        "kp": {
            "cusps": [{"house": 6, "sb": "Moon"}],
            "significations": {
                "Moon": {
                    "pl": script,
                    "sl": [4],
                    "sb_houses": script,
                    "ss_houses": [],
                    "nl_lord": "Mars",
                    "sb_lord": "Moon",
                },
            },
        },
    }


class TestTridosha(unittest.TestCase):
    def test_percentages_sum_to_100(self):
        out = compute_tridosha_balance(_sample_planets(), 0, _sample_kundli())
        bal = out["dosha_balance"]
        self.assertEqual(sum(bal.values()), 100)

    def test_weight_formula_40_30_30(self):
        out = compute_tridosha_balance(_sample_planets(), 0, _sample_kundli())
        w = out["layer_breakdown"]["weights"]
        self.assertEqual(w["d1"], 0.40)
        self.assertEqual(w["d9"], 0.30)
        self.assertEqual(w["csl"], 0.30)

    def test_kp_house_script_extracted(self):
        out = compute_tridosha_balance(_sample_planets(), 0, _sample_kundli())
        kp = out["kp_6th_csl_validation"]
        self.assertEqual(kp.get("csl_planet"), "Moon")
        self.assertIn(6, kp.get("house_script") or [])
        self.assertIn(8, kp.get("house_script") or [])

    def test_clinical_promise_on_6_8_combo(self):
        out = compute_tridosha_balance(_sample_planets(), 0, _sample_kundli())
        self.assertTrue(out["clinical_disease_promise"])
        self.assertEqual(out["kp_6th_csl_validation"]["verdict"], "DISEASE_PROMISE_ACTIVE")

    def test_high_immunity_when_no_dusthana(self):
        k = _sample_kundli(dusthana_script=[1, 5, 11])
        out = compute_tridosha_balance(_sample_planets(), 0, k)
        kp = out["kp_6th_csl_validation"]
        self.assertFalse(kp.get("connects_to_dusthana"))
        self.assertEqual(kp.get("verdict"), "HIGH_IMMUNITY")
        self.assertIn("High Immunity", kp.get("immunity_message") or "")

    def test_clinical_kapha_override_for_moon_csl(self):
        out = compute_tridosha_balance(_sample_planets(), 0, _sample_kundli())
        self.assertIn("Kapha", out["dominant_clinical_trigger"])

    def test_health_specifics_integration(self):
        k = _sample_kundli()
        deep = compute_health_specifics(k["planets"], 0, kundli=k)
        self.assertEqual(deep.get("tridosha_engine"), "health_tridosha_v1")
        self.assertIn("structural_reason", deep)
        self.assertIn("dietary_remedies", deep)


if __name__ == "__main__":
    unittest.main()

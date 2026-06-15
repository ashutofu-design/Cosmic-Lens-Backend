"""Tests for Life Map health vitality score (health_engine_v1 layers)."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vedic.health_vitality_score_v1 import compute_health_vitality_score


def _sample_kundli() -> dict:
    planets = [
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
    return {
        "ascendant": "Aries",
        "planets": planets,
        "currentDasha": {"maha": "Jupiter", "antar": "Venus"},
        "dashas": [
            {
                "planet": "Jupiter",
                "startDate": "2020-01-01",
                "endDate": "2036-01-01",
                "subDashas": [
                    {
                        "planet": "Venus",
                        "startDate": "2024-01-01",
                        "endDate": "2027-01-01",
                    }
                ],
            }
        ],
        "divisionalCharts": {
            "D9": {
                "ascendant": "Aries",
                "ascendantSignIndex": 0,
                "planets": planets,
            },
        },
        "kp": {
            "cusps": [
                {"house": 6, "sb": "Moon"},
                {"house": 8, "sb": "Saturn"},
                {"house": 12, "sb": "Rahu"},
            ],
            "significations": {
                "Moon": {"pl": [1, 5, 11], "sb_houses": [1, 5, 11]},
                "Saturn": {"pl": [6, 8], "sb_houses": [6, 8]},
                "Rahu": {"pl": [12], "sb_houses": [12]},
            },
        },
    }


class TestHealthVitality(unittest.TestCase):
    def test_score_in_range(self):
        out = compute_health_vitality_score(_sample_kundli())
        self.assertGreaterEqual(out["score"], 25)
        self.assertLessEqual(out["score"], 95)
        self.assertIn(out["risk"], ("Low", "Moderate", "High"))

    def test_layer_weights(self):
        out = compute_health_vitality_score(_sample_kundli())
        w = out["layer_scores"]["weights"]
        self.assertEqual(w["d1"], 0.40)
        self.assertEqual(w["d9"], 0.30)
        self.assertEqual(w["kp_csl"], 0.20)
        self.assertEqual(w["dasha"], 0.10)

    def test_engine_tag(self):
        out = compute_health_vitality_score(_sample_kundli())
        self.assertEqual(out["engine"], "health_vitality_v1")


if __name__ == "__main__":
    unittest.main()

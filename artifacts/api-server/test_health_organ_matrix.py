"""Tests for health_organ_matrix_v1 — 6-zone organ vulnerability heatmap."""
import unittest

from vedic.health_organ_matrix_v1 import compute_organ_vulnerability_matrix


def _sample_planets():
    return [
        {"name": "Sun", "sign": "Leo", "house": 5},
        {"name": "Moon", "sign": "Scorpio", "house": 12},
        {"name": "Mars", "sign": "Cancer", "house": 6},
        {"name": "Mercury", "sign": "Virgo", "house": 5},
        {"name": "Jupiter", "sign": "Capricorn", "house": 9},
        {"name": "Venus", "sign": "Libra", "house": 4},
        {"name": "Saturn", "sign": "Aries", "house": 1},
        {"name": "Rahu", "sign": "Gemini", "house": 3},
        {"name": "Ketu", "sign": "Sagittarius", "house": 9},
    ]


class TestHealthOrganMatrix(unittest.TestCase):
    def test_returns_six_zones(self):
        out = compute_organ_vulnerability_matrix(_sample_planets(), 0)
        self.assertEqual(len(out), 6)
        ids = {z["id"] for z in out}
        self.assertEqual(
            ids,
            {"digestion", "respiratory", "joints_nerves", "heart_circulation", "mind_sleep", "metabolism"},
        )

    def test_status_values(self):
        out = compute_organ_vulnerability_matrix(_sample_planets(), 0)
        for z in out:
            self.assertIn(z["status"], ("high", "moderate", "stable"))
            self.assertEqual(z["engine"], "health_organ_matrix_v1")

    def test_high_dosha_raises_digestion(self):
        dosha = {"vata": 20, "pitta": 45, "kapha": 35}
        out = compute_organ_vulnerability_matrix(_sample_planets(), 0, dosha_balance=dosha)
        digestion = next(z for z in out if z["id"] == "digestion")
        self.assertIn(digestion["status"], ("high", "moderate"))

    def test_empty_planets_stable(self):
        out = compute_organ_vulnerability_matrix([], 0)
        self.assertEqual(len(out), 6)
        self.assertTrue(all(z["status"] == "stable" for z in out))


if __name__ == "__main__":
    unittest.main()

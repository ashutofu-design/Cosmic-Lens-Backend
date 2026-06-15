"""Tests for health_organ_matrix v2 — 6-zone organ vulnerability heatmap."""
import unittest

from vedic.health_organ_matrix_v1 import compute_organ_vulnerability_matrix

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


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

    def test_engine_v2(self):
        out = compute_organ_vulnerability_matrix(_sample_planets(), 0)
        for z in out:
            self.assertEqual(z["engine"], "health_organ_matrix_v2")

    def test_status_values(self):
        out = compute_organ_vulnerability_matrix(_sample_planets(), 0)
        for z in out:
            self.assertIn(z["status"], ("high", "moderate", "stable"))

    def test_high_dosha_raises_digestion(self):
        dosha = {"vata": 20, "pitta": 45, "kapha": 35}
        out = compute_organ_vulnerability_matrix(_sample_planets(), 0, dosha_balance=dosha)
        digestion = next(z for z in out if z["id"] == "digestion")
        self.assertIn(digestion["status"], ("high", "moderate"))

    def test_empty_planets_stable(self):
        out = compute_organ_vulnerability_matrix([], 0)
        self.assertEqual(len(out), 6)
        self.assertTrue(all(z["status"] == "stable" for z in out))

    def test_sun_leo_5th_not_inflates_all_zones(self):
        """Strong Sun in Leo 5H should not push every zone to high."""
        planets = [
            {"name": "Sun", "sign": "Leo", "house": 5},
            {"name": "Moon", "sign": "Taurus", "house": 4},
            {"name": "Mars", "sign": "Capricorn", "house": 10},
            {"name": "Mercury", "sign": "Virgo", "house": 6},
            {"name": "Jupiter", "sign": "Cancer", "house": 2},
            {"name": "Venus", "sign": "Pisces", "house": 12},
            {"name": "Saturn", "sign": "Libra", "house": 7},
            {"name": "Rahu", "sign": "Gemini", "house": 3},
            {"name": "Ketu", "sign": "Sagittarius", "house": 9},
        ]
        dosha = {"vata": 33, "pitta": 34, "kapha": 33}
        out = compute_organ_vulnerability_matrix(planets, 0, dosha_balance=dosha)
        high_count = sum(1 for z in out if z["status"] == "high")
        self.assertLessEqual(high_count, 3)

    def test_asc_cusp_sign_affects_zone(self):
        """Virgo asc → 6H Pisces cusp should not zero-score digestion issues path."""
        planets = [{"name": "Mars", "sign": "Pisces", "house": 6}]
        asc = SIGNS.index("Virgo")
        out = compute_organ_vulnerability_matrix(planets, asc)
        digestion = next(z for z in out if z["id"] == "digestion")
        self.assertGreater(digestion["score"], 0)


if __name__ == "__main__":
    unittest.main()

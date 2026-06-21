"""Tests for money_habits_v1 chart-matched habit templates."""
import unittest

from vedic.money_habits_v1 import derive_money_habits


def _planets():
    return [
        {"name": "Sun", "sign": "Leo", "house": 10},
        {"name": "Moon", "sign": "Taurus", "house": 2},
        {"name": "Mars", "sign": "Capricorn", "house": 7},
        {"name": "Mercury", "sign": "Virgo", "house": 11},
        {"name": "Jupiter", "sign": "Cancer", "house": 5},
        {"name": "Venus", "sign": "Pisces", "house": 9},
        {"name": "Saturn", "sign": "Libra", "house": 4},
        {"name": "Rahu", "sign": "Gemini", "house": 3},
        {"name": "Ketu", "sign": "Sagittarius", "house": 9},
    ]


class TestMoneyHabitsV1(unittest.TestCase):
    def test_returns_two_to_three_habits(self):
        out = derive_money_habits(_planets(), 0, "rich", {})
        self.assertGreaterEqual(len(out), 2)
        self.assertLessEqual(len(out), 3)

    def test_no_astro_jargon(self):
        planets = [p if p["name"] != "Rahu" else {**p, "house": 8} for p in _planets()]
        out = derive_money_habits(planets, 0, "middle_class", {"rahu_8": True})
        joined = " ".join(out).lower()
        self.assertNotIn("lord", joined)
        self.assertNotIn("house", joined)
        self.assertNotIn("dusthana", joined)

    def test_ketu_2h_impulsive_habit(self):
        planets = [p if p["name"] != "Ketu" else {**p, "house": 2} for p in _planets()]
        out = derive_money_habits(planets, 0, "rich", {})
        self.assertTrue(any("bank app" in line.lower() for line in out))

    def test_fallback_when_chart_clean(self):
        out = derive_money_habits(_planets(), 0, "millionaire", {})
        self.assertGreaterEqual(len(out), 2)
        self.assertTrue(any("salary" in line.lower() or "month" in line.lower() for line in out))


if __name__ == "__main__":
    unittest.main()

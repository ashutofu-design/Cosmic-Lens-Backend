"""Tests for raj_yoga_engine_v1 — kendra-trikona raj yogas."""
import unittest

from vedic.dhan_yoga_engine_v1 import _lord_pair_link
from vedic.raj_yoga_engine_v1 import scan_raj_yogas


def _aries_asc_9_10_conjunct():
    """Aries asc: 9L Jupiter + 10L Saturn both in 10th (Dharma-Karmadhipati)."""
    return [
        {"name": "Mars", "sign": "Aries", "house": 1},
        {"name": "Venus", "sign": "Taurus", "house": 2},
        {"name": "Sun", "sign": "Leo", "house": 5},
        {"name": "Jupiter", "sign": "Capricorn", "house": 10},
        {"name": "Saturn", "sign": "Capricorn", "house": 10},
        {"name": "Mercury", "sign": "Virgo", "house": 6},
        {"name": "Moon", "sign": "Gemini", "house": 3},
        {"name": "Rahu", "sign": "Gemini", "house": 3},
        {"name": "Ketu", "sign": "Sagittarius", "house": 9},
    ]


class TestRajYogaEngine(unittest.TestCase):
    def test_dharma_karmadhipati_conjunct(self):
        planets = _aries_asc_9_10_conjunct()
        self.assertEqual(_lord_pair_link(planets, 0, 10, 9), "conjunction")
        out = scan_raj_yogas(planets, 0)
        names = {y["name"] for y in out}
        self.assertIn("Dharma-Karmadhipati Yoga", names)

    def test_no_generic_benefic_strength(self):
        planets = _aries_asc_9_10_conjunct()
        out = scan_raj_yogas(planets, 0)
        names = {y["name"] for y in out}
        self.assertNotIn("Benefic strength", names)

    def test_vipreet_in_dusthana(self):
        """Cancer asc: 6L Jupiter + 8L Saturn in 8th."""
        planets = [
            {"name": "Moon", "sign": "Cancer", "house": 1},
            {"name": "Sun", "sign": "Leo", "house": 2},
            {"name": "Mars", "sign": "Scorpio", "house": 5},
            {"name": "Mercury", "sign": "Virgo", "house": 3},
            {"name": "Jupiter", "sign": "Aquarius", "house": 8},
            {"name": "Venus", "sign": "Libra", "house": 4},
            {"name": "Saturn", "sign": "Aquarius", "house": 8},
            {"name": "Rahu", "sign": "Gemini", "house": 12},
            {"name": "Ketu", "sign": "Sagittarius", "house": 6},
        ]
        out = scan_raj_yogas(planets, 3)
        names = {y["name"] for y in out}
        self.assertIn("Vipreet Raj Yoga", names)

    def test_yogakaraka_capricorn_venus(self):
        """Capricorn asc: Venus YK in 10th own sign."""
        planets = [
            {"name": "Saturn", "sign": "Capricorn", "house": 1},
            {"name": "Venus", "sign": "Libra", "house": 10},
            {"name": "Sun", "sign": "Leo", "house": 8},
            {"name": "Moon", "sign": "Cancer", "house": 7},
            {"name": "Mars", "sign": "Aries", "house": 4},
            {"name": "Mercury", "sign": "Virgo", "house": 9},
            {"name": "Jupiter", "sign": "Pisces", "house": 3},
            {"name": "Rahu", "sign": "Gemini", "house": 6},
            {"name": "Ketu", "sign": "Sagittarius", "house": 12},
        ]
        out = scan_raj_yogas(planets, 9)
        names = {y["name"] for y in out}
        self.assertIn("Yogakaraka Yoga", names)


if __name__ == "__main__":
    unittest.main()

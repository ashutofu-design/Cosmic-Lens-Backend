"""Tests for dhan_yoga_engine_v1 — lord-pair wealth yogas."""
import unittest

from vedic.dhan_yoga_engine_v1 import _lord_pair_link, scan_dhan_yogas


def _aries_asc_planets():
    """Aries asc: 1L Mars + 2L Venus both in 2nd house (conjunction)."""
    return [
        {"name": "Mars", "sign": "Taurus", "house": 2},
        {"name": "Venus", "sign": "Taurus", "house": 2},
        {"name": "Sun", "sign": "Leo", "house": 5},
        {"name": "Jupiter", "sign": "Cancer", "house": 4},
        {"name": "Mercury", "sign": "Virgo", "house": 6},
        {"name": "Moon", "sign": "Gemini", "house": 3},
        {"name": "Saturn", "sign": "Aquarius", "house": 11},
        {"name": "Rahu", "sign": "Gemini", "house": 3},
        {"name": "Ketu", "sign": "Sagittarius", "house": 9},
    ]


class TestDhanYogaLordPairs(unittest.TestCase):
    def test_1_2_conjunction_detected(self):
        planets = _aries_asc_planets()
        self.assertEqual(_lord_pair_link(planets, 0, 1, 2), "conjunction")

    def test_all_seven_pairs_scanned(self):
        planets = _aries_asc_planets()
        out = scan_dhan_yogas(planets, 0)
        names = {y["name"] for y in out}
        self.assertIn("Lagna-Dhana Yoga", names)

    def test_no_lakshmi_or_chandra_mangal(self):
        planets = _aries_asc_planets()
        out = scan_dhan_yogas(planets, 0)
        names = {y["name"] for y in out}
        self.assertNotIn("Lakshmi Yoga", names)
        self.assertNotIn("Chandra-Mangal Yoga", names)

    def test_mutual_aspect_only_not_single(self):
        """One-way aspect should not count — Mars h1 Aries vs Venus h2 Taurus."""
        planets = [
            {"name": "Mars", "sign": "Aries", "house": 1},
            {"name": "Venus", "sign": "Taurus", "house": 2},
            {"name": "Sun", "sign": "Leo", "house": 5},
            {"name": "Jupiter", "sign": "Cancer", "house": 4},
            {"name": "Mercury", "sign": "Virgo", "house": 6},
            {"name": "Moon", "sign": "Cancer", "house": 4},
            {"name": "Saturn", "sign": "Capricorn", "house": 10},
            {"name": "Rahu", "sign": "Gemini", "house": 3},
            {"name": "Ketu", "sign": "Sagittarius", "house": 9},
        ]
        link = _lord_pair_link(planets, 0, 1, 2)
        self.assertIsNone(link)


if __name__ == "__main__":
    unittest.main()

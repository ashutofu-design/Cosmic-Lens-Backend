"""Tests for leak_channels_v1 personalized wealth leak scanner."""
import unittest

from vedic.leak_channels_v1 import scan_wealth_leak_channels


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


class TestLeakChannelsV1(unittest.TestCase):
    def test_rahu_8h_sudden_loss_channel(self):
        planets = [p if p["name"] != "Rahu" else {**p, "house": 8} for p in _planets()]
        out = scan_wealth_leak_channels(planets, 0)
        channels = [row["channel"] for row in out]
        self.assertIn("sudden_loss_tax", channels)
        self.assertIn("Rahu in 8th house", out[0]["message_en"])

    def test_ketu_2h_savings_channel(self):
        planets = [p if p["name"] != "Ketu" else {**p, "house": 2} for p in _planets()]
        out = scan_wealth_leak_channels(planets, 0)
        self.assertTrue(any(row["channel"] == "savings_dont_stick" for row in out))

    def test_kp_income_leak_channel(self):
        h11 = {"csl_planet": "Saturn", "verdict": "RED", "loss_hits": [12], "chain": {"signified": [11, 12]}}
        out = scan_wealth_leak_channels(_planets(), 0, None, h11, None)
        self.assertTrue(any(row["channel"] == "kp_income_leak" for row in out))

    def test_max_four_channels(self):
        planets = _planets()
        planets = [p if p["name"] != "Rahu" else {**p, "house": 8} for p in planets]
        planets = [p if p["name"] != "Ketu" else {**p, "house": 2} for p in planets]
        planets = [p if p["name"] != "Mercury" else {**p, "house": 12} for p in planets]
        h12 = {
            "csl_planet": "Rahu",
            "verdict": "RED",
            "loss_hits": [12],
            "chain": {"signified": [5, 12]},
        }
        out = scan_wealth_leak_channels(planets, 0, None, None, h12)
        self.assertLessEqual(len(out), 4)

    def test_messages_trilingual(self):
        planets = [p if p["name"] != "Rahu" else {**p, "house": 8} for p in _planets()]
        out = scan_wealth_leak_channels(planets, 0)
        row = out[0]
        self.assertTrue(row.get("message_en"))
        self.assertTrue(row.get("message_hn"))
        self.assertTrue(row.get("message_hi"))


if __name__ == "__main__":
    unittest.main()

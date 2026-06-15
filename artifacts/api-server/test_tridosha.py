"""Tests for Vata / Pitta / Kapha tridosha balance."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vedic.life_specifics import compute_tridosha_balance, compute_health_specifics


def _sample_planets(asc: str = "Aries") -> list:
  """Minimal chart with ascendant handled via asc_idx in callers."""
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


class TestTridosha(unittest.TestCase):
    def test_percentages_sum_to_100(self):
        planets = _sample_planets()
        out = compute_tridosha_balance(planets, 0)
        bal = out["dosha_balance"]
        self.assertEqual(sum(bal.values()), 100)
        for k in ("vata", "pitta", "kapha"):
            self.assertIn(k, bal)
            self.assertGreaterEqual(bal[k], 0)

    def test_states_present(self):
        out = compute_tridosha_balance(_sample_planets(), 0)
        for k in ("vata", "pitta", "kapha"):
            self.assertIn(out["dosha_states"][k], ("Balanced", "Afflicted", "Highly Critical"))

    def test_health_specifics_includes_tridosha(self):
        deep = compute_health_specifics(_sample_planets(), 0)
        self.assertEqual(sum(deep["dosha_balance"].values()), 100)
        self.assertIn("dosha_states", deep)
        self.assertIn("tridosha_care", deep)


if __name__ == "__main__":
    unittest.main()

"""Tests for deterministic career inclination engine."""
from __future__ import annotations

import unittest

from vedic.career_inclination_engine import compute_career_inclination


def _planet(name: str, house: int, sign: str, **extra) -> dict:
    return {"name": name, "house": house, "sign": sign, **extra}


class TestCareerInclinationEngine(unittest.TestCase):
  def _run(self, planets: list, asc: str = "Capricorn", d10: list | None = None, d9: list | None = None) -> dict:
    asc_idx = [
      "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
      "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ].index(asc)
    kundli = {"ascendant": asc, "planets": planets}
    div: dict = {}
    if d10 is not None:
      div["D10"] = {"planets": d10, "ascendant": asc}
    if d9 is not None:
      div["D9"] = {"planets": d9, "ascendant": asc}
    if div:
      kundli["divisionalCharts"] = div
    return compute_career_inclination(planets, asc_idx, kundli)

  def test_deterministic_same_input(self):
    planets = [
      _planet("Sun", 10, "Libra"),
      _planet("Saturn", 6, "Gemini"),
      _planet("Mercury", 7, "Cancer"),
      _planet("Mars", 3, "Pisces"),
      _planet("Moon", 4, "Aries"),
      _planet("Jupiter", 11, "Scorpio"),
      _planet("Venus", 2, "Aquarius"),
      _planet("Rahu", 10, "Libra"),
      _planet("Ketu", 4, "Aries"),
    ]
    a = self._run(planets)
    b = self._run(planets)
    self.assertEqual(a["job_pct"], b["job_pct"])
    self.assertEqual(a["path_verdict"], b["path_verdict"])

  def test_percentages_sum_to_100(self):
    planets = [
      _planet("Sun", 10, "Libra"),
      _planet("Saturn", 10, "Libra"),
      _planet("Mercury", 7, "Cancer"),
    ]
    r = self._run(planets)
    self.assertEqual(r["job_pct"] + r["business_pct"], 100)

  def test_job_leaning_chart(self):
    """Saturn+Sun in 10, Saturn in 6 → employment lean."""
    planets = [
      _planet("Sun", 10, "Libra"),
      _planet("Saturn", 6, "Gemini"),
      _planet("Saturn", 10, "Libra"),
      _planet("Mercury", 3, "Pisces"),
    ]
    r = self._run(planets)
    self.assertGreaterEqual(r["job_pct"], 50)
    self.assertIn(r["confidence"], ("Low", "Medium", "Medium-High", "High"))

  def test_business_leaning_chart(self):
    planets = [
      _planet("Mercury", 7, "Cancer"),
      _planet("Rahu", 10, "Libra"),
      _planet("Venus", 7, "Cancer"),
    ]
    r = self._run(planets)
    self.assertGreaterEqual(r["business_pct"], 45)

  def test_has_reasoning_factors(self):
    planets = [_planet("Sun", 10, "Libra"), _planet("Saturn", 6, "Gemini")]
    r = self._run(planets)
    self.assertTrue(r.get("reasoning_summary") or r.get("factors"))
    self.assertTrue(r.get("career_mode"))

  def test_empty_planets_safe(self):
    r = compute_career_inclination([], 0, {})
    self.assertEqual(r["job_pct"] + r["business_pct"], 100)
    self.assertNotEqual(r["job_pct"], 50)

  def test_never_exact_fifty_fifty(self):
    """Any chart must show a lean (min 60-40), never 50-50."""
    charts = [
      [
        _planet("Sun", 10, "Libra"),
        _planet("Mercury", 7, "Cancer"),
        _planet("Venus", 7, "Cancer"),
      ],
      [
        _planet("Sun", 5, "Leo"),
        _planet("Moon", 5, "Leo"),
        _planet("Mars", 5, "Leo"),
      ],
    ]
    for planets in charts:
      r = self._run(planets)
      self.assertNotEqual(r["job_pct"], 50, f"got 50-50 for {planets}")
      self.assertGreaterEqual(abs(r["job_pct"] - 50), 10)

  def test_dhanu_lagna_moon_gemini_not_forced_fifty_fifty(self):
    """Dhanu lagna + Moon in Gemini (7th) — should not flatten to 50/50."""
    asc = "Sagittarius"
    asc_idx = 8
    planets = [
      _planet("Sun", 10, "Virgo"),
      _planet("Moon", 7, "Gemini"),
      _planet("Mars", 8, "Scorpio"),
      _planet("Mercury", 10, "Virgo"),
      _planet("Jupiter", 1, "Sagittarius"),
      _planet("Venus", 11, "Libra"),
      _planet("Saturn", 3, "Aquarius"),
      _planet("Rahu", 7, "Gemini"),
      _planet("Ketu", 1, "Sagittarius"),
    ]
    kundli = {"ascendant": "Sagittarius", "ascendantDeg": 8 * 30 + 5, "planets": planets}
    r = compute_career_inclination(planets, asc_idx, kundli)
    self.assertNotEqual(
      (r["job_pct"], r["business_pct"]),
      (50, 50),
      "Dhanu+Moon Gemini chart should show a lean, not forced 50/50",
    )
    self.assertGreater(r["business_pct"], 45)

  def test_dhanu_alias_ascendant(self):
    asc_idx = 8
    planets = [
      _planet("Moon", 7, "Gemini"),
      _planet("Mercury", 7, "Gemini"),
      _planet("Jupiter", 1, "Sagittarius"),
      _planet("Sun", 10, "Virgo"),
      _planet("Mars", 8, "Scorpio"),
      _planet("Venus", 11, "Libra"),
      _planet("Saturn", 3, "Aquarius"),
      _planet("Rahu", 7, "Gemini"),
      _planet("Ketu", 1, "Sagittarius"),
    ]
    kundli = {"ascendant": "Dhanu", "planets": planets}
    r = compute_career_inclination(planets, asc_idx, kundli)
    self.assertGreater(r["business_pct"], 48)

  def test_mercury_in_6th_not_pure_business(self):
    planets = [
      _planet("Sun", 10, "Capricorn"),
      _planet("Mercury", 6, "Virgo"),
      _planet("Saturn", 6, "Capricorn"),
      _planet("Moon", 4, "Aries"),
      _planet("Mars", 3, "Pisces"),
      _planet("Jupiter", 11, "Scorpio"),
      _planet("Venus", 2, "Aquarius"),
      _planet("Rahu", 5, "Cancer"),
      _planet("Ketu", 11, "Scorpio"),
    ]
    r = self._run(planets, "Capricorn")
    self.assertGreater(r.get("commercial_score", 0), 0)
    self.assertIn(r["career_mode"], (
      "Commercial Professional", "Advisory / Consulting",
      "Structured Professional", "Hybrid Career", "Authority-Oriented",
    ))

  def test_amatyakaraka_saturn_boosts_job(self):
    """AmK Saturn with karaka degrees → employment lean strengthens."""
    planets = [
      _planet("Sun", 10, "Libra", degree_in_sign=28),
      _planet("Moon", 4, "Aries", degree_in_sign=22),
      _planet("Mars", 3, "Pisces", degree_in_sign=18),
      _planet("Mercury", 3, "Pisces", degree_in_sign=15),
      _planet("Jupiter", 11, "Scorpio", degree_in_sign=12),
      _planet("Venus", 2, "Aquarius", degree_in_sign=8),
      _planet("Saturn", 6, "Gemini", degree_in_sign=25),
      _planet("Rahu", 10, "Libra"),
      _planet("Ketu", 4, "Aries"),
    ]
    r = self._run(planets)
    self.assertEqual(r.get("amatyakaraka"), "Saturn")
    self.assertGreaterEqual(r["job_pct"], 55)

  def test_amatyakaraka_mercury_boosts_business(self):
    planets = [
      _planet("Sun", 5, "Leo", degree_in_sign=29),
      _planet("Mercury", 7, "Gemini", degree_in_sign=27),
      _planet("Jupiter", 9, "Sagittarius", degree_in_sign=12),
      _planet("Moon", 4, "Cancer", degree_in_sign=8),
      _planet("Mars", 8, "Aries", degree_in_sign=6),
      _planet("Venus", 2, "Taurus", degree_in_sign=5),
      _planet("Saturn", 3, "Capricorn", degree_in_sign=3),
      _planet("Rahu", 7, "Gemini"),
      _planet("Ketu", 1, "Sagittarius"),
    ]
    r = self._run(planets, "Sagittarius")
    self.assertEqual(r.get("amatyakaraka"), "Mercury")
    self.assertGreaterEqual(r["business_pct"], 52)

  def test_d9_and_d10_raise_confidence_when_aligned(self):
    asc = "Capricorn"
    planets = [
      _planet("Sun", 10, "Libra"),
      _planet("Saturn", 6, "Gemini"),
      _planet("Saturn", 10, "Libra"),
      _planet("Mercury", 3, "Pisces"),
      _planet("Moon", 4, "Aries"),
      _planet("Mars", 8, "Leo"),
      _planet("Jupiter", 11, "Scorpio"),
      _planet("Venus", 2, "Aquarius"),
      _planet("Rahu", 5, "Cancer"),
      _planet("Ketu", 11, "Scorpio"),
    ]
    d10 = [
      _planet("Sun", 10, "Libra"),
      _planet("Saturn", 10, "Libra"),
    ]
    d9 = [
      _planet("Sun", 10, "Libra"),
      _planet("Saturn", 6, "Gemini"),
    ]
    r = self._run(planets, asc, d10=d10, d9=d9)
    self.assertIn(r["confidence"], ("Medium", "Medium-High", "High"))
    self.assertGreaterEqual(r["job_pct"], 50)


if __name__ == "__main__":
  unittest.main()

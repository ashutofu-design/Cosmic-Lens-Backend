"""Tests for deterministic career inclination engine."""
from __future__ import annotations

import unittest

from vedic.career_inclination_engine import compute_career_inclination


def _planet(name: str, house: int, sign: str, **extra) -> dict:
    return {"name": name, "house": house, "sign": sign, **extra}


class TestCareerInclinationEngine(unittest.TestCase):
  def _run(self, planets: list, asc: str = "Capricorn", d10: list | None = None) -> dict:
    asc_idx = [
      "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
      "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ].index(asc)
    kundli = {"ascendant": asc, "planets": planets}
    if d10 is not None:
      kundli["divisionalCharts"] = {"D10": {"planets": d10}}
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


if __name__ == "__main__":
  unittest.main()

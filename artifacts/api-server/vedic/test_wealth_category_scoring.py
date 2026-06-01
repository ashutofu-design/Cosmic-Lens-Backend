"""Wealth category scoring — pattern amplifier & parivartana."""
import unittest

from vedic.life_specifics import (
    compute_finance_specifics,
    _has_lord_exchange,
    _wealth_exchange_bonus,
    _wealth_saturn_compounding_bonus,
    _d1_rahu_eighth_bonus,
)


def _sag_pattern_kundli(*, with_vargas: bool = True) -> dict:
    """Sagittarius-style chart: 9↔11 exchange, strong D9/D10 Saturn, D10 Rahu 11."""
    d1 = [
        {"name": "Mars", "sign": "Sagittarius", "house": 1},
        {"name": "Jupiter", "sign": "Aries", "house": 5},
        {"name": "Saturn", "sign": "Aries", "house": 5},
        {"name": "Rahu", "sign": "Cancer", "house": 8},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Sun", "sign": "Libra", "house": 11},
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Mercury", "sign": "Virgo", "house": 10},
        {"name": "Ketu", "sign": "Capricorn", "house": 2},
    ]
    k = {"ascendant": "Sagittarius", "planets": d1}
    if not with_vargas:
        return k
    k["divisionalCharts"] = {
        "D9": {
            "ascendant": "Sagittarius",
            "planets": [
                {"name": "Saturn", "sign": "Libra", "house": 11},
                {"name": "Venus", "sign": "Pisces", "house": 12},
                {"name": "Rahu", "sign": "Pisces", "house": 12},
                {"name": "Jupiter", "sign": "Virgo", "house": 6},
                {"name": "Ketu", "sign": "Virgo", "house": 6},
                {"name": "Sun", "sign": "Aries", "house": 5},
                {"name": "Mars", "sign": "Sagittarius", "house": 1},
                {"name": "Moon", "sign": "Gemini", "house": 7},
                {"name": "Mercury", "sign": "Leo", "house": 9},
            ],
        },
        "D10": {
            "ascendant": "Sagittarius",
            "planets": [
                {"name": "Saturn", "sign": "Libra", "house": 2},
                {"name": "Moon", "sign": "Libra", "house": 2},
                {"name": "Rahu", "sign": "Leo", "house": 11},
                {"name": "Mercury", "sign": "Virgo", "house": 12},
                {"name": "Jupiter", "sign": "Aries", "house": 9},
                {"name": "Mars", "sign": "Aries", "house": 9},
                {"name": "Sun", "sign": "Gemini", "house": 11},
                {"name": "Venus", "sign": "Taurus", "house": 10},
                {"name": "Ketu", "sign": "Scorpio", "house": 4},
            ],
        },
    }
    return k


class TestWealthCategoryScoring(unittest.TestCase):
    def test_saturn_empire_pattern_bonus(self):
        k = _sag_pattern_kundli(with_vargas=True)
        self.assertGreaterEqual(_wealth_saturn_compounding_bonus(k, 8), 8)

    def test_d1_rahu_8th_bonus(self):
        k = _sag_pattern_kundli(with_vargas=False)
        self.assertEqual(_d1_rahu_eighth_bonus(k["planets"], 8), 5)

    def test_wealth_styles_returned(self):
        k = _sag_pattern_kundli(with_vargas=True)
        r = compute_finance_specifics(k["planets"], 8, kundli=k)
        styles = r.get("wealth_styles") or []
        self.assertIsInstance(styles, list)
        self.assertGreater(len(styles), 0)

    def test_sag_has_9_11_exchange(self):
        k = _sag_pattern_kundli(with_vargas=False)
        self.assertTrue(_has_lord_exchange(k["planets"], 8, 9, 11))
        self.assertGreaterEqual(_wealth_exchange_bonus(k["planets"], 8), 10)

    def test_pattern_chart_reaches_ultra_rich_with_vargas(self):
        k = _sag_pattern_kundli(with_vargas=True)
        r = compute_finance_specifics(k["planets"], 8, kundli=k)
        score = int(r["wealth_karma_score"])
        cat = r["wealth_category"]
        self.assertGreaterEqual(score, 65, f"expected ultra zone, got {score} ({cat})")
        self.assertEqual(cat, "ultra_rich", f"debil-soft chart caps at ultra, got {cat}")

    def test_d1_only_lower_than_full_chart(self):
        full = compute_finance_specifics(
            _sag_pattern_kundli()["planets"], 8, kundli=_sag_pattern_kundli(),
        )
        d1 = compute_finance_specifics(
            _sag_pattern_kundli(with_vargas=False)["planets"],
            8,
            kundli=_sag_pattern_kundli(with_vargas=False),
        )
        self.assertGreater(
            int(full["wealth_karma_score"]),
            int(d1["wealth_karma_score"]),
        )

    def test_weak_chart_stays_middle_or_rich(self):
        """Average chart should not auto-hit millionaire."""
        weak = {
            "ascendant": "Virgo",
            "planets": [
                {"name": "Sun", "sign": "Virgo", "house": 1},
                {"name": "Moon", "sign": "Pisces", "house": 7},
                {"name": "Mars", "sign": "Gemini", "house": 10},
                {"name": "Mercury", "sign": "Virgo", "house": 1},
                {"name": "Jupiter", "sign": "Capricorn", "house": 5},
                {"name": "Venus", "sign": "Libra", "house": 2},
                {"name": "Saturn", "sign": "Aries", "house": 8},
                {"name": "Rahu", "sign": "Cancer", "house": 11},
                {"name": "Ketu", "sign": "Capricorn", "house": 5},
            ],
        }
        r = compute_finance_specifics(weak["planets"], 5, kundli=weak)
        self.assertLess(int(r["wealth_karma_score"]), 80)
        self.assertIn(
            r["wealth_category"],
            ("middle_class", "rich", "ultra_rich"),
        )


if __name__ == "__main__":
    unittest.main()

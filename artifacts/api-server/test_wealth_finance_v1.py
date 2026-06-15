"""Tests for wealth_finance_v1 diagnostic engine."""
import unittest

from vedic.wealth_finance_v1 import compute_wealth_finance_diagnostic, wealth_tier_from_score


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


class TestWealthFinanceV1(unittest.TestCase):
    def test_returns_engine_payload(self):
        out = compute_wealth_finance_diagnostic(_planets(), 0)
        self.assertEqual(out["engine"], "wealth_finance_v1")
        self.assertIn("yog_metrics", out)
        self.assertIn("chart_matrix", out)
        self.assertIn("wealth_tier", out)
        self.assertIn("wealth_source", out)
        self.assertIn("disclaimer", out)

    def test_yog_counts_non_negative(self):
        out = compute_wealth_finance_diagnostic(_planets(), 0)
        ym = out["yog_metrics"]
        self.assertGreaterEqual(ym["dhan_count"], 0)
        self.assertGreaterEqual(ym["raj_count"], 0)
        self.assertGreaterEqual(ym["activation_pct"], 0)
        self.assertLessEqual(ym["activation_pct"], 100)

    def test_dasha_activation(self):
        out = compute_wealth_finance_diagnostic(
            _planets(),
            0,
            current_dasha={"maha": "Jupiter", "antar": "Venus"},
        )
        self.assertIsInstance(out["yog_metrics"]["activation_pct"], int)

    def test_wealth_source_has_label(self):
        out = compute_wealth_finance_diagnostic(_planets(), 0)
        self.assertTrue(out["wealth_source"].get("label"))

    def test_score_56_is_average_not_rich(self):
        self.assertEqual(wealth_tier_from_score(56), "middle_class")
        self.assertEqual(wealth_tier_from_score(60), "rich")


if __name__ == "__main__":
    unittest.main()

"""Tests for wealth_finance_v1 diagnostic engine."""
import unittest

from vedic.wealth_finance_v1 import (
    _d1_leakage_flags,
    _kp_leakage_flags,
    _leakage_alerts,
    compute_wealth_finance_diagnostic,
    wealth_tier_from_score,
)

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

    def test_d1_ketu_2h_triggers_expense_drain(self):
        planets = _planets()
        planets = [p if p["name"] != "Ketu" else {**p, "house": 2} for p in planets]
        flags = _d1_leakage_flags(planets, 0)
        self.assertIn("expense_drain_active", flags)

    def test_d1_rahu_8h_triggers_property_risk(self):
        planets = _planets()
        planets = [p if p["name"] != "Rahu" else {**p, "house": 8} for p in planets]
        flags = _d1_leakage_flags(planets, 0)
        self.assertIn("property_legal_loss_risk", flags)

    def test_kp_12_red_only_expense_not_triple(self):
        h12 = {
            "csl_planet": "Mercury",
            "verdict": "RED",
            "loss_hits": [12],
            "chain": {"signified": [3, 12]},
        }
        flags = _kp_leakage_flags(None, None, h12)
        self.assertIn("expense_drain_active", flags)
        self.assertNotIn("property_legal_loss_risk", flags)
        self.assertNotIn("speculation_trading_fraud_risk", flags)

    def test_kp_speculation_requires_rahu_and_5_or_8(self):
        h12_rahu_only = {
            "csl_planet": "Rahu",
            "verdict": "YELLOW",
            "loss_hits": [],
            "chain": {"signified": [3, 9]},
        }
        self.assertNotIn(
            "speculation_trading_fraud_risk",
            _kp_leakage_flags(None, None, h12_rahu_only),
        )
        h12_rahu_5 = {**h12_rahu_only, "chain": {"signified": [3, 5, 9]}}
        self.assertIn(
            "speculation_trading_fraud_risk",
            _kp_leakage_flags(None, None, h12_rahu_5),
        )
        h12_mercury_5 = {**h12_rahu_5, "csl_planet": "Mercury"}
        self.assertNotIn(
            "speculation_trading_fraud_risk",
            _kp_leakage_flags(None, None, h12_mercury_5),
        )

    def test_kp_h2_loss_adds_expense_drain(self):
        h2 = {"verdict": "RED", "loss_hits": [8], "chain": {"signified": [2, 8]}}
        flags = _kp_leakage_flags(h2, None, None)
        self.assertEqual(flags, {"expense_drain_active"})

    def test_leakage_order_stable(self):
        planets = _planets()
        planets = [p if p["name"] != "Ketu" else {**p, "house": 2} for p in planets]
        h12 = {
            "csl_planet": "Rahu",
            "verdict": "RED",
            "loss_hits": [12],
            "chain": {"signified": [5, 12]},
        }
        out = _leakage_alerts(planets, 0, None, None, h12)
        self.assertEqual(out[0], "expense_drain_active")
        self.assertIn("speculation_trading_fraud_risk", out)


if __name__ == "__main__":    unittest.main()

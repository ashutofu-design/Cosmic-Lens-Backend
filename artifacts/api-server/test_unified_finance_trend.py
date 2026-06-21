"""Unified finance score + trend — one Money Builder engine."""
import unittest

from vedic.life_specifics import (
    _derive_finance_trend,
    _finance_transit_nudge,
    build_finance_basic_insights,
)


class TestUnifiedFinanceTrend(unittest.TestCase):
    def test_transit_nudge_bounds(self):
        notes = [
            "Jupiter currently in your 11th — wealth-building & opportunity phase active",
            "Saturn in 12th — extra discipline on expenses needed",
        ]
        nudge = _finance_transit_nudge(notes)
        self.assertGreaterEqual(nudge, -5)
        self.assertLessEqual(nudge, 5)

    def test_gain_when_dasha_lifts(self):
        self.assertEqual(_derive_finance_trend(72, 60), "Gain")

    def test_loss_when_dasha_drags(self):
        self.assertEqual(_derive_finance_trend(48, 62), "Loss")

    def test_stable_in_band(self):
        self.assertEqual(_derive_finance_trend(58, 56), "Stable")

    def test_build_insights_score_matches_trend_engine(self):
        deep = {
            "wealth_karma_score": 60,
            "wealth_operational_score": 68,
            "wealth_category": "rich",
            "money_habits": ["Save first on payday."],
        }
        out = build_finance_basic_insights(deep, transit_notes=[])
        self.assertEqual(out["score"], 68)
        self.assertEqual(out["trend"], "Gain")
        self.assertEqual(out["wealth_karma_score"], 60)


if __name__ == "__main__":
    unittest.main()

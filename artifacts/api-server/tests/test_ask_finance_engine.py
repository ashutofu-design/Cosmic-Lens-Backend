"""Smoke tests for ask_finance routing + engines."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_finance.classifier import classify_finance_archetype, is_finance_static_question
from ask_finance.engine import run_finance_static_engine
from ask_finance.routing import resolve_finance_archetype

_SAMPLE_KUNDLI = {
    "ascendant": "Leo",
    "planets": [
        {"name": "Sun", "house": 1, "sign": "Leo", "longitude": 120.0},
        {"name": "Moon", "house": 4, "sign": "Scorpio", "longitude": 220.0},
        {"name": "Mars", "house": 10, "sign": "Taurus", "longitude": 40.0},
        {"name": "Mercury", "house": 2, "sign": "Virgo", "longitude": 160.0},
        {"name": "Jupiter", "house": 5, "sign": "Sagittarius", "longitude": 250.0},
        {"name": "Venus", "house": 3, "sign": "Libra", "longitude": 190.0},
        {"name": "Saturn", "house": 7, "sign": "Aquarius", "longitude": 300.0},
        {"name": "Rahu", "house": 11, "sign": "Gemini", "longitude": 80.0},
        {"name": "Ketu", "house": 5, "sign": "Sagittarius", "longitude": 260.0},
    ],
    "currentDasha": {"maha": "Jupiter", "antar": "Saturn", "pratyantar": "Mercury"},
}


class TestAskFinanceEngine(unittest.TestCase):
    def test_scope_income_savings_debt_property(self):
        cases = [
            ("meri income stable hai ya nahi?", "income_source"),
            ("kitni bachat kar sakta hoon?", "savings_capacity"),
            ("karz lena chahiye?", "debt_loan"),
            ("ghar khareedne ke liye paisa banega?", "property_money"),
            ("sudden wealth lottery yog hai?", "sudden_gain_loss"),
            ("paisa kyun nahi tikta?", "expense_pattern"),
            ("amir ban sakta hoon?", "wealth_potential"),
            ("dhana yoga hai kya?", "dhana_yoga"),
        ]
        for q, expected in cases:
            with self.subTest(q=q):
                self.assertTrue(is_finance_static_question(q))
                self.assertEqual(classify_finance_archetype(q), expected)

    def test_timing_excluded(self):
        self.assertFalse(is_finance_static_question("kab paisa aayega?"))

    def test_stock_excluded_from_scope(self):
        self.assertFalse(is_finance_static_question("nifty me invest karu?"))

    def test_resolve_override_llm(self):
        arch, reason = resolve_finance_archetype(
            "karz clear hoga?",
            llm_archetype="general_finance",
        )
        self.assertEqual(arch, "debt_loan")
        self.assertIn("regex", reason)

    def test_engines_return_evidence(self):
        for arch in (
            "income_source",
            "savings_capacity",
            "debt_loan",
            "property_money",
            "sudden_gain_loss",
            "general_finance",
        ):
            with self.subTest(archetype=arch):
                res = run_finance_static_engine(
                    _SAMPLE_KUNDLI,
                    "paisa question",
                    archetype=arch,
                )
                self.assertEqual(res.archetype, arch)
                self.assertTrue(res.verdict)
                self.assertGreaterEqual(len(res.evidence), 3)
                payload = res.to_narrator_payload()
                self.assertIn("VERDICT:", payload)


if __name__ == "__main__":
    unittest.main()

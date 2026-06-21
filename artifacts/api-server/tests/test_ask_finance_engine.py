"""Smoke tests for ask_finance routing + engines."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_career.classifier import classify_career_archetype, is_career_static_question
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

_FOUNDATION_10 = [
    ("Kya main ameer banne ki potential rakhta hoon?", "wealth_potential"),
    ("Mera paisa kamaane ka natural tareeka kya hai?", "income_source"),
    ("Main wealth create karne me kitna capable hoon?", "wealth_potential"),
    ("Main financial discipline me kaisa hoon?", "financial_discipline"),
    ("Main paisa bachane wala hoon ya kharch karne wala?", "save_vs_spend"),
    ("Main risk lene wala investor hoon ya conservative?", "investment_risk"),
    ("Main financial decisions me practical hoon?", "general_finance"),
    ("Main emotional spending karta hoon?", "spending_personality"),
    ("Main luxury-oriented hoon?", "spending_personality"),
]


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

    def test_foundation_10_finance_routes(self):
        for q, expected in _FOUNDATION_10:
            with self.subTest(q=q):
                self.assertTrue(is_finance_static_question(q), q)
                self.assertEqual(classify_finance_archetype(q), expected, q)

    def test_employee_mindset_goes_career_not_finance(self):
        q = "Main employee mindset wala hoon ya entrepreneur mindset wala?"
        self.assertFalse(is_finance_static_question(q))
        self.assertTrue(is_career_static_question(q))
        self.assertEqual(classify_career_archetype(q), "job_vs_business")

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
            "save_vs_spend",
            "financial_discipline",
            "investment_risk",
            "spending_personality",
            "debt_loan",
            "property_money",
            "sudden_gain_loss",
            "wealth_potential",
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

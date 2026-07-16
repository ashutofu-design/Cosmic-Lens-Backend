"""LLM path for interpretation/combo — chart_fact only for pure placement."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chart_fact_answer import (
    is_pure_chart_fact_lookup,
    needs_llm_chart_answer,
    try_deterministic_chart_fact,
)

_KUNDLI = {
    "ascendant": "Leo",
    "planets": [{"name": "Sun", "house": 10, "sign": "Taurus"}],
    "divisionalCharts": {
        "D10": {
            "ascendant": "Aries",
            "planets": [{"name": "Sun", "house": 5, "sign": "Capricorn"}],
        },
    },
}


class TestNeedsLlmChartAnswer(unittest.TestCase):
    def test_d10_statement_placement_needs_llm(self):
        q = "D10 mein Sun Makar rashi mein hai (5th house)"
        self.assertTrue(needs_llm_chart_answer(q))
        self.assertFalse(is_pure_chart_fact_lookup(q))
        self.assertIsNone(try_deterministic_chart_fact(q, _KUNDLI))

    def test_d10_se_kya_hota_he_needs_llm(self):
        q = "D10 mein Sun Makar rashi mein hai (5th house). se kya hota he"
        self.assertTrue(needs_llm_chart_answer(q))
        self.assertFalse(is_pure_chart_fact_lookup(q))
        self.assertIsNone(try_deterministic_chart_fact(q, _KUNDLI))

    def test_d10_career_effect_needs_llm(self):
        q = "D10 mein Sun mere career par kya effect dalta hai"
        self.assertTrue(needs_llm_chart_answer(q))
        self.assertFalse(is_pure_chart_fact_lookup(q))
        self.assertIsNone(try_deterministic_chart_fact(q, _KUNDLI))

    def test_planet_combo_needs_llm(self):
        q = "Mars aur Saturn ka combination kya karta hai"
        self.assertTrue(needs_llm_chart_answer(q))
        self.assertIsNone(try_deterministic_chart_fact(q, _KUNDLI))

    def test_pure_d10_placement_still_chart_fact(self):
        # Chart-fact lookup disabled — pure placement goes to LLM (not deterministic).
        q = "D10 mein Sun kis house me hai"
        self.assertFalse(is_pure_chart_fact_lookup(q))
        self.assertIsNone(try_deterministic_chart_fact(q, _KUNDLI))

    def test_hypothetical_lord_place_needs_llm_not_house_lookup(self):
        q = (
            "kya placement change ho sakta he like 6th lord ko 10th me "
            "place kar sakta hun kya"
        )
        from chart_fact_answer import answer_hypothetical_placement_change

        self.assertTrue(needs_llm_chart_answer(q))
        self.assertFalse(is_pure_chart_fact_lookup(q))
        hyp = answer_hypothetical_placement_change(q)
        self.assertIsNotNone(hyp)
        self.assertIn("change nahi", hyp.get("text", "").lower())
        self.assertNotIn("koi graha nahi", hyp.get("text", "").lower())
        # Locked answer works even without planet list
        det = try_deterministic_chart_fact(q, {"ascendant": "Virgo", "planets": []})
        self.assertIsNotNone(det)
        self.assertIn("change nahi", det.get("text", "").lower())

    def test_placememt_typo_hypothetical_lock(self):
        from chart_fact_answer import answer_hypothetical_placement_change

        q = "kya placememt change ho sakta he like 6th lord ko 10th me place kar sakta hun kya"
        hyp = answer_hypothetical_placement_change(q)
        self.assertIsNotNone(hyp)
        self.assertNotIn("koi graha nahi", (hyp.get("text") or "").lower())

    def test_pure_tenth_house_occupants_still_chart_fact(self):
        # Chart-fact lookup disabled — pure house occupants go to LLM.
        q = "Mere 10th house mein kaun se graha hain"
        self.assertFalse(is_pure_chart_fact_lookup(q))
        det = try_deterministic_chart_fact(q, _KUNDLI)
        self.assertIsNone(det)

    def test_lord_debilitated_effect_needs_llm(self):
        q = (
            "pehele samjhao 6th lord 3rd house me he woh sun he and "
            "deblited he to kya hota he"
        )
        self.assertTrue(needs_llm_chart_answer(q))
        self.assertFalse(is_pure_chart_fact_lookup(q))

    def test_house_debilitated_vs_exalted_needs_llm(self):
        """Conceptual dignity Q — must NOT dump empty-house occupants."""
        q = "6th house me deblited planet acha he ya exalted"
        self.assertTrue(needs_llm_chart_answer(q))
        self.assertFalse(is_pure_chart_fact_lookup(q))
        det = try_deterministic_chart_fact(q, _KUNDLI)
        self.assertIsNone(det)

    def test_leo_lagna_gemstone_not_native_lagna_lookup(self):
        """Leo/kisi-ka gem advice must NEVER become 'Your ascendant is …'."""
        from ask_question_normalize import normalize_ask_typos
        from ask_remedy.remedy_registry import is_remedy_static_question
        from chart_fact_answer import is_gemstone_or_remedy_advice_question
        from openai_helper import _classify_ask_intent

        q_raw = "agar kisi ka leo lagna he to konsa gemstoene dharan karna chahiye"
        q = normalize_ask_typos(q_raw)
        self.assertIn("gemstone", q.lower())
        self.assertTrue(is_gemstone_or_remedy_advice_question(q))
        self.assertTrue(needs_llm_chart_answer(q))
        self.assertFalse(is_pure_chart_fact_lookup(q))
        # Personal chart remedy engine must not steal named-lagna theory Q.
        self.assertFalse(is_remedy_static_question(q))
        # Intent must not be lagna_lookup for native chart.
        it = (_classify_ask_intent(q, "hn").get("intent") or "")
        self.assertNotEqual(it, "lagna_lookup")
        # Native is Sagittarius — must not return that one-liner.
        sag_kundli = {
            "ascendant": "Sagittarius",
            "planets": [{"name": "Sun", "house": 9, "sign": "Leo"}],
        }
        det = try_deterministic_chart_fact(q, sag_kundli, lang="en")
        self.assertIsNone(det)
        if det:
            self.assertNotIn("Sagittarius", det.get("text", ""))


if __name__ == "__main__":
    unittest.main()

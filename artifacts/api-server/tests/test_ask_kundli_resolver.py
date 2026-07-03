import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_kundli_resolver import _normalize_chart_payload


class AskKundliResolverTests(unittest.TestCase):
    def _sample_planets(self):
        return [
            {"name": "Sun", "sign": "Libra", "house": 11},
            {"name": "Moon", "sign": "Gemini", "house": 7},
            {"name": "Mars", "sign": "Sagittarius", "house": 1},
            {"name": "Mercury", "sign": "Scorpio", "house": 12},
            {"name": "Jupiter", "sign": "Aries", "house": 5},
            {"name": "Venus", "sign": "Leo", "house": 9},
            {"name": "Saturn", "sign": "Aries", "house": 5},
            {"name": "Rahu", "sign": "Cancer", "house": 8},
            {"name": "Ketu", "sign": "Capricorn", "house": 2},
        ]

    def test_flat_chart(self):
        chart = {"ascendant": "Sagittarius", "planets": self._sample_planets()}
        norm = _normalize_chart_payload(chart)
        self.assertIsNotNone(norm)
        self.assertEqual(len(norm["planets"]), 9)

    def test_nested_chart_wrapper(self):
        inner = {"ascendant": "Sagittarius", "planets": self._sample_planets()}
        wrapped = {"chart_data": inner, "meta": {"source": "profile"}}
        norm = _normalize_chart_payload(wrapped)
        self.assertIsNotNone(norm)
        self.assertEqual(norm["ascendant"], "Sagittarius")

    def test_coerce_string_house_planets(self):
        from ask_llm_context_debug import coerce_chart_for_marriage_engine

        planets = []
        for p in self._sample_planets():
            row = dict(p)
            row["house"] = str(row["house"])
            planets.append(row)
        chart = coerce_chart_for_marriage_engine(
            {"ascendant": "Sagittarius", "planets": planets},
        )
        self.assertIsNotNone(chart)
        self.assertIsInstance(chart["planets"][0]["house"], int)

    def test_marriage_m17_block_on_nested_chart(self):
        from openai_helper import _run_marriage_m17_block

        inner = {
            "ascendant": "Sagittarius",
            "ascendantDeg": 248.5,
            "planets": self._sample_planets(),
        }
        wrapped = {"kundli": inner}
        mb, er = _run_marriage_m17_block(
            "mera shaadi kab hoga",
            wrapped,
            {"dob": "26 Nov 1999"},
        )
        self.assertTrue(mb, "M17 block should not be empty for valid nested chart")
        self.assertIsInstance(er, dict)
        self.assertTrue(er)


if __name__ == "__main__":
    unittest.main()

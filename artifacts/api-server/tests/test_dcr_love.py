import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import openai_helper as oh
from dcr_love import (
    build_dcr_love_context,
    classify_buckets,
    is_love_static_question,
)


class DcrLoveTests(unittest.TestCase):
    def test_love_static_question_excludes_timing(self):
        self.assertTrue(is_love_static_question("love marriage possible hai?"))
        self.assertTrue(is_love_static_question("mera future husband ka nature kaisa hoga?"))
        self.assertTrue(is_love_static_question("meri patni ka nature kaisa hoga?"))
        self.assertFalse(is_love_static_question("love marriage kab hoga?"))

    def test_emotional_vs_practical_selects_both_buckets(self):
        buckets = classify_buckets(
            "Mere chart me emotional attachment zyada strong hai ya practical relationship approach?"
        )
        self.assertIn("core_love_base", buckets)
        self.assertIn("emotional_attachment", buckets)
        self.assertIn("practical_relationship_approach", buckets)

    def test_spouse_profession_bucket_and_explain_trigger(self):
        buckets = classify_buckets("mera spouse ka profession kis type ka ho sakta hai")
        self.assertIn("spouse_profession", buckets)
        self.assertTrue(oh._user_wants_explanation("kya check kiya he kaise pata chalega"))

    def test_context_contains_selected_d1_d9_facts(self):
        kundli = {
            "ascendant": "Sagittarius",
            "planets": [
                {"name": "Moon", "sign": "Gemini", "house": 7, "nakshatra": "Ardra"},
                {"name": "Venus", "sign": "Leo", "house": 9},
                {"name": "Saturn", "sign": "Virgo", "house": 10},
                {"name": "Mercury", "sign": "Aries", "house": 5},
                {"name": "Mars", "sign": "Cancer", "house": 8},
                {"name": "Jupiter", "sign": "Pisces", "house": 4},
            ],
            "divisionalCharts": {
                "D9": {
                    "ascendant": "Libra",
                    "planets": [
                        {"name": "Moon", "sign": "Capricorn", "house": 4},
                        {"name": "Venus", "sign": "Aquarius", "house": 5},
                    ],
                }
            },
        }
        block, meta = build_dcr_love_context(
            kundli,
            "emotional attachment aur practical relationship approach compare karo",
        )
        self.assertIn("DCR LOVE SLICE", block)
        self.assertIn("D1 partner focus:", block)
        self.assertIn("D9 partner focus:", block)
        self.assertIn("spouse profession focus:", block)
        self.assertIn("7H=Gemini, lord=Mercury", block)
        self.assertIn("Moon Gemini H7 nak:Ardra", block)
        self.assertIn("D9 houses:", block)
        self.assertIn("7H=Aries, lord=Mars", block)
        self.assertIn("D9 relevant planets", block)
        self.assertEqual(
            meta["buckets"],
            ["core_love_base", "emotional_attachment", "practical_relationship_approach"],
        )

    def test_partner_nature_context_uses_relationship_slice(self):
        kundli = {
            "ascendant": "Sagittarius",
            "planets": [
                {"name": "Moon", "sign": "Gemini", "house": 7},
                {"name": "Mercury", "sign": "Scorpio", "house": 12},
                {"name": "Venus", "sign": "Leo", "house": 9},
                {"name": "Jupiter", "sign": "Pisces", "house": 4},
                {"name": "Mars", "sign": "Cancer", "house": 8},
            ],
            "divisionalCharts": {
                "D9": {
                    "ascendant": "Libra",
                    "planets": [
                        {"name": "Mars", "sign": "Aries", "house": 7},
                        {"name": "Venus", "sign": "Aquarius", "house": 5},
                    ],
                }
            },
        }
        block, meta = build_dcr_love_context(kundli, "mera partner ka nature kaise he")
        self.assertIn("partner_nature", meta["buckets"])
        self.assertIn("D1 houses:", block)
        self.assertIn("D9 houses:", block)
        self.assertIn("D1 partner focus: 7H=Gemini, 7L=Mercury", block)
        self.assertIn("D9 partner focus: 7H=Aries, 7L=Mars", block)
        self.assertIn("D1 spouse profession focus:", block)
        self.assertIn("D9 spouse profession focus:", block)
        self.assertIn("7H=Gemini, lord=Mercury", block)
        self.assertIn("7H=Aries, lord=Mars", block)


if __name__ == "__main__":
    unittest.main()

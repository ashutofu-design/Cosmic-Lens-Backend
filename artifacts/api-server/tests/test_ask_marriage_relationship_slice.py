import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_marriage_relationship_slice import (
    build_marriage_relationship_slice,
    is_marriage_relationship_static_question,
)


SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7, "nakshatra": "Ardra"},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Saturn", "sign": "Virgo", "house": 10},
        {"name": "Mercury", "sign": "Aries", "house": 5},
        {"name": "Mars", "sign": "Cancer", "house": 8},
        {"name": "Jupiter", "sign": "Pisces", "house": 4},
        {"name": "Rahu", "sign": "Aquarius", "house": 3},
        {"name": "Ketu", "sign": "Leo", "house": 9},
        {"name": "Sun", "sign": "Capricorn", "house": 2},
    ],
    "divisionalCharts": {
        "D9": {
            "ascendant": "Libra",
            "planets": [
                {"name": "Moon", "sign": "Capricorn", "house": 4},
                {"name": "Venus", "sign": "Aquarius", "house": 5},
                {"name": "Mars", "sign": "Aries", "house": 7},
                {"name": "Mercury", "sign": "Scorpio", "house": 2},
                {"name": "Jupiter", "sign": "Cancer", "house": 10},
            ],
        }
    },
}


class MarriageRelationshipSliceTests(unittest.TestCase):
    def test_static_detector_includes_marriage_excludes_timing(self):
        self.assertTrue(
            is_marriage_relationship_static_question("mera partner ka nature kaisa hoga?")
        )
        self.assertTrue(
            is_marriage_relationship_static_question("love marriage hogi ya arranged?")
        )
        self.assertTrue(
            is_marriage_relationship_static_question("kya main manglik hun?")
        )
        self.assertFalse(
            is_marriage_relationship_static_question("shaadi kab hogi?")
        )
        self.assertFalse(
            is_marriage_relationship_static_question("career kab badhega?")
        )

    def test_partner_nature_minimal_four_checks_only(self):
        block, meta = build_marriage_relationship_slice(
            SAMPLE_KUNDLI,
            "mera partner ka nature kya hai",
            birth={"gender": "male"},
        )
        self.assertEqual(meta["slice"], "partner_nature_minimal")
        self.assertEqual(meta["chart_gender"], "male")
        self.assertEqual(meta["karak_planet"], "Venus")
        self.assertEqual(
            meta["checks"],
            ["7H_rashi", "7L_rashi_house", "7H_planets", "Venus_karak_rashi"],
        )
        self.assertIn("EXECUTION PRIORITY", block)
        self.assertIn("STEP 1", block)
        self.assertIn("STEP 2", block)
        self.assertIn("STEP 3", block)
        self.assertIn("OUTPUT FORMAT", block)
        self.assertIn("7th house rashi: Gemini", block)
        self.assertIn("Occupants: ['Moon']", block)
        self.assertIn("7th lord Mercury", block)
        self.assertIn("karak Venus", block)
        self.assertIn("Venus: rashi=Leo", block)
        self.assertNotIn("D9", block)
        self.assertNotIn("PRE-CALCULATED", block)

    def test_partner_nature_female_uses_jupiter_karak(self):
        block, meta = build_marriage_relationship_slice(
            SAMPLE_KUNDLI,
            "mera pati ka nature kaisa hoga",
            birth={"gender": "female"},
        )
        self.assertEqual(meta["chart_gender"], "female")
        self.assertEqual(meta["karak_planet"], "Jupiter")
        self.assertIn("karak Jupiter", block)
        self.assertIn("Jupiter: rashi=Pisces", block)
        self.assertNotIn("karak Venus", block)

    def test_love_marriage_uses_expanded_slice(self):
        block, meta = build_marriage_relationship_slice(
            SAMPLE_KUNDLI,
            "love marriage hogi ya arranged?",
        )
        self.assertEqual(meta["slice"], "marriage_relationship")
        self.assertIn("D9", block)
        self.assertIn("PRE-CALCULATED FLAGS:", block)

    def test_slice_has_d1_d9_and_precalc_no_dasha(self):
        block, meta = build_marriage_relationship_slice(
            SAMPLE_KUNDLI,
            "kya main manglik hun",
        )
        self.assertIn("MARRIAGE / RELATIONSHIP SLICE", block)
        self.assertIn("D1 partner focus:", block)
        self.assertIn("D9 partner focus:", block)
        self.assertIn("D1 houses:", block)
        self.assertIn("D9 houses:", block)
        self.assertIn("PRE-CALCULATED FLAGS:", block)
        self.assertIn("manglik:", block.lower())
        self.assertIn("venus_afflicted:", block)
        self.assertIn("d9_marriage:", block)
        self.assertIn("marriage_tilt:", block)
        self.assertNotIn("DASHA", block)
        self.assertNotIn("Mahadasha", block)
        self.assertEqual(meta["slice"], "marriage_relationship")
        self.assertTrue(meta["flags"])

    def test_slice_covers_spouse_profession_angle(self):
        block, _ = build_marriage_relationship_slice(
            SAMPLE_KUNDLI,
            "meri patni ka profession kya hoga",
        )
        self.assertIn("spouse profession focus:", block)


if __name__ == "__main__":
    unittest.main()

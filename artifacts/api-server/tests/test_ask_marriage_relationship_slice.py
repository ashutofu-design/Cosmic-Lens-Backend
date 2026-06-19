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

    def test_partner_nature_slice_is_lean(self):
        block, meta = build_marriage_relationship_slice(
            SAMPLE_KUNDLI,
            "mera partner ka nature kya hai",
        )
        self.assertIn("partner_nature", meta["buckets"])
        self.assertIn("D1 partner focus:", block)
        self.assertIn("7H=Gemini", block)
        self.assertIn("5H=", block)
        self.assertNotIn("spouse profession focus:", block)
        self.assertNotIn("10H=", block)
        self.assertNotIn("nak:", block)
        self.assertNotIn("marriage_tilt:", block)
        self.assertIn("7th_house_afflicted:", block)
        self.assertIn("d9_marriage:", block)

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

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_mr.engines._lordship import houses_ruled_by, lordship_clause
from vedic.love_reality.scoring_core import KundliReader


SAG_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Mercury", "sign": "Scorpio", "house": 12},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Mars", "sign": "Cancer", "house": 8},
        {"name": "Jupiter", "sign": "Pisces", "house": 4},
        {"name": "Saturn", "sign": "Virgo", "house": 10},
        {"name": "Sun", "sign": "Capricorn", "house": 2},
    ],
}


class LordshipEvidenceTests(unittest.TestCase):
    def test_mercury_rules_7_and_10_for_sag_asc(self):
        r = KundliReader(SAG_KUNDLI)
        self.assertEqual(houses_ruled_by(r, "Mercury"), [7, 10])
        self.assertIn("7H+10H", lordship_clause(r, "Mercury"))

    def test_emotional_compat_evidence_includes_lordship(self):
        from ask_mr.engines.general_mr import _synthesize_emotional_compatibility
        from ask_mr.engines._person_signals import build_person_signals

        sig = build_person_signals(SAG_KUNDLI)
        lines = _synthesize_emotional_compatibility(SAG_KUNDLI, sig)
        moon_lines = [ln for ln in lines if "Moon" in ln and "7th" in ln]
        self.assertTrue(moon_lines)
        self.assertIn("rules", moon_lines[0])


if __name__ == "__main__":
    unittest.main()

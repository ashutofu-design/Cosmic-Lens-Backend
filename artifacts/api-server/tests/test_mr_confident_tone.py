import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_mr.narrator import polish_mr_confident_tone


class MrConfidentToneTests(unittest.TestCase):
    def test_strips_shayad_and_ho_sakta_hai(self):
        raw = "Shayad partner chatty ho sakta hai aur emotional depth lagti hai."
        out = polish_mr_confident_tone(raw)
        self.assertNotIn("shayad", out.lower())
        self.assertNotIn("ho sakta", out.lower())
        self.assertNotIn("lagti hai", out.lower())

    def test_preserves_paragraph_breaks(self):
        raw = "Para one lagta hai strong.\n\nPara two ho sakti hai deep."
        out = polish_mr_confident_tone(raw)
        self.assertIn("\n\n", out)


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openai_helper import _enforce_partner_nature_paragraphs


class PartnerNatureFormatTests(unittest.TestCase):
    def test_single_block_splits_into_three_paragraphs(self):
        blob = (
            "Partner chatty lag sakta hai baat karne mein comfortable hai. "
            "Emotional side gehra hai mood kabhi soft kabhi intense ho sakta hai. "
            "Presence warm ho sakti hai relationship mein thoughtful rehte hain."
        )
        out = _enforce_partner_nature_paragraphs(blob)
        self.assertIn("\n\n", out)
        parts = [p for p in out.split("\n\n") if p.strip()]
        self.assertGreaterEqual(len(parts), 2)
        self.assertTrue(out.rstrip()[-1] in ".?!")

    def test_word_cap_ends_with_period(self):
        long_blob = " ".join(["word"] * 200) + "."
        out = _enforce_partner_nature_paragraphs(long_blob)
        self.assertLessEqual(len(out.split()), 125)
        self.assertTrue(out.endswith("."))


if __name__ == "__main__":
    unittest.main()

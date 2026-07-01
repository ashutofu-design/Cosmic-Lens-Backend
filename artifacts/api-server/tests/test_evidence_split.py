import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_mr.engines._evidence_split import (
    classify_evidence_line,
    format_split_evidence_block,
    narrator_balance_instruction,
    split_evidence_polarity,
)
from ask_mr.engine import mr_engine_slice_meta
from ask_mr.types import EngineResult


class EvidenceSplitTests(unittest.TestCase):
    def test_classify_negative_affliction(self):
        self.assertEqual(
            classify_evidence_line("Love challenge: Venus debilitated"),
            "negative",
        )
        self.assertEqual(
            classify_evidence_line("Saturn in 5th (Leo, dignity debilitated) — delay"),
            "negative",
        )
        self.assertEqual(
            classify_evidence_line("Venus in house 7 sign Virgo — dignity enemy-sign"),
            "negative",
        )

    def test_classify_positive(self):
        self.assertEqual(
            classify_evidence_line("True-love marker: Venus on 5th romance axis"),
            "positive",
        )
        self.assertEqual(
            classify_evidence_line("Jupiter in house 5 — dharmic true love"),
            "positive",
        )

    def test_split_keeps_all_lines(self):
        lines = [
            "True-love marker: Venus on 5th",
            "Love challenge: Saturn on 7th",
            "5th house sign Cancer; occupants = ['Jupiter']",
            "Saturn aspects 7th house — patience needed",
        ]
        pos, neg, neu = split_evidence_polarity(lines)
        self.assertEqual(len(pos) + len(neg) + len(neu), len(lines))
        self.assertEqual(len(neg), 2)
        self.assertEqual(len(pos), 1)

    def test_format_block_lists_all_points(self):
        lines = [
            "True-love marker: Venus on 5th",
            "Love challenge: Venus debilitated",
            "Love challenge: Saturn on 7th",
        ]
        block = format_split_evidence_block(lines)
        text = "\n".join(block)
        self.assertIn("POSITIVE EVIDENCE (1 points)", text)
        self.assertIn("NEGATIVE / AFFLICTION EVIDENCE (2 points)", text)
        self.assertIn("+ True-love marker", text)
        self.assertIn("− Love challenge: Venus debilitated", text)
        self.assertIn("BALANCE:", text)

    def test_balance_strict_when_many_negatives(self):
        inst = narrator_balance_instruction([], ["a", "b", "c"])
        self.assertIn("STRICT", inst)

    def test_house_axis_mixed_occupants_stays_neutral(self):
        line = (
            "Romance/dating axis (5th house): house 5 sign Aries; lord Mars in house 1 "
            "sign Sagittarius (dignity neutral); occupants=['Jupiter', 'Saturn']; "
            "malefics in house=['Saturn']."
        )
        self.assertEqual(classify_evidence_line(line), "neutral")

    def test_house_axis_malefic_only_is_negative(self):
        line = "5th house: occupants=['Saturn']; malefics in house=['Saturn']."
        self.assertEqual(classify_evidence_line(line), "negative")

    def test_balance_mixed_when_both_sides(self):
        inst = narrator_balance_instruction(["a", "b"], ["x", "y"])
        self.assertIn("MIXED", inst)

    def test_engine_result_narrator_payload_has_split(self):
        result = EngineResult(
            archetype="dating_courtship",
            verdict="Mixed true love yog",
            evidence=[
                "True-love marker: Venus on 5th",
                "Love challenge: Saturn on 7th",
                "5th house sign Cancer; occupants = ['Jupiter']",
            ],
        )
        payload = result.to_narrator_payload()
        self.assertIn("POSITIVE EVIDENCE", payload)
        self.assertIn("NEGATIVE / AFFLICTION EVIDENCE", payload)
        self.assertIn("BALANCE:", payload)

    def test_mr_engine_slice_meta_includes_split(self):
        result = EngineResult(
            archetype="dating_courtship",
            verdict="Test",
            evidence=[
                "True-love marker: Venus on 5th",
                "Love challenge: Venus debilitated",
            ],
        )
        meta = mr_engine_slice_meta(result)
        self.assertEqual(meta["slice"], "mr_engine_v1")
        self.assertEqual(len(meta["evidence"]), 2)
        self.assertEqual(len(meta["evidence_positive"]), 1)
        self.assertEqual(len(meta["evidence_negative"]), 1)


if __name__ == "__main__":
    unittest.main()

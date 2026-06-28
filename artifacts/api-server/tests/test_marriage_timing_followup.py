import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_scope_gate import assess_ask_scope
from openai_helper import _detect_marriage_constraint, _last_assistant_topic_was_marriage


class MarriageTimingFollowupTests(unittest.TestCase):
    def test_scope_allows_alt_timing_followup(self):
        q = "Agar june - nov 2029 ke bich nehi hoga aage kab hoga"
        v = assess_ask_scope(q)
        self.assertTrue(v.allowed, v.reason)

    def test_detect_marriage_constraint(self):
        q = "Agar june - nov 2029 ke bich nehi hoga aage kab hoga"
        self.assertTrue(_detect_marriage_constraint(q, []))

    def test_last_assistant_marriage_from_history(self):
        hist = [
            {"role": "user", "text": "Mera shaadi kab hoga"},
            {"role": "assistant", "text": "Aapki shaadi June – November 2029 ke beech hogi."},
        ]
        self.assertTrue(_last_assistant_topic_was_marriage(hist))


if __name__ == "__main__":
    unittest.main()

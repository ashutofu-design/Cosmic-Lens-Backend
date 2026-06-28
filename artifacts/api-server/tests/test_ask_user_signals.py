import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_user_signals import extract_question_signals
from user_ask_profile import (
    build_personalization_hint,
    merge_signals_into_profile,
)


class AskUserSignalsTests(unittest.TestCase):
    def test_short_timing_question(self):
        sig = extract_question_signals("Mera shaadi kab hoga", topic="marriage")
        self.assertEqual(sig["style"], "short")
        self.assertTrue(sig["is_timing"])
        self.assertIn("marriage", sig["topics_detected"])

    def test_anxious_followup(self):
        q = "Agar june nov 2029 mein nahi hoga aage kab hoga"
        sig = extract_question_signals(q, topic="timing")
        self.assertTrue(sig["is_followup"])
        self.assertIn("timing", sig["question_types"])

    def test_profile_merge_labels(self):
        prof = {}
        for q, topic in [
            ("Mera shaadi kab hoga", "marriage"),
            ("Aur agla kab", "marriage"),
            ("kaise pata", "marriage"),
        ]:
            sig = extract_question_signals(q, topic=topic)
            prof = merge_signals_into_profile(prof, sig)
        self.assertGreaterEqual(prof["question_count"], 3)
        self.assertIn("labels", prof)
        hint = build_personalization_hint(prof)
        self.assertTrue(hint == "" or "PERSONALIZATION" in hint)


if __name__ == "__main__":
    unittest.main()

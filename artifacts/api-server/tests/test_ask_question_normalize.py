"""Typo normalization for Ask questions."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_question_normalize import prepare_ask_question
from chart_fact_answer import is_chart_lookup_question, is_domain_outcome_yoga_question


class TestAskQuestionNormalize(unittest.TestCase):
    def test_bachcha_pyaar_love_yog_becomes_sacha_pyaar(self):
        q = "Kya meri kundli me bachcha pyaar (true love milne ka yog likha hai"
        out = prepare_ask_question(q)
        self.assertIn("sacha pyaar", out.lower())
        self.assertNotIn("bachcha pyaar", out.lower())

    def test_correct_sachcha_pyaar_unchanged_semantics(self):
        q = "Kya meri kundli me sachcha pyar (true love) milne ka yog likha hai?"
        out = prepare_ask_question(q)
        self.assertRegex(out.lower(), r"sach(a|cha)\s+pya?ar")
        self.assertTrue(is_domain_outcome_yoga_question(out))
        self.assertFalse(is_chart_lookup_question(out))

    def test_bachcha_child_question_not_rewritten(self):
        q = "Kya mera bachcha hoga kab"
        out = prepare_ask_question(q)
        self.assertIn("bachcha", out.lower())
        self.assertNotIn("sacha pyaar", out.lower())

    def test_batch_number_prefix_stripped(self):
        q = (
            "Hate 2. career According to my birth chart which career sector is best "
            "for me, job or business which is best"
        )
        out = prepare_ask_question(q)
        self.assertTrue(out.lower().startswith("career according"))
        self.assertNotIn("hate 2", out.lower())


if __name__ == "__main__":
    unittest.main()

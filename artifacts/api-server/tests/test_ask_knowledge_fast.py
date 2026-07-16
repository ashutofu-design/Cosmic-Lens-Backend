"""Knowledge-fast path: Leo lagna gemstone must not soft-fail / timeout."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_knowledge_fast import (
    is_astrology_knowledge_fast_question,
    try_astrology_knowledge_fast_answer,
)
from ask_question_normalize import prepare_ask_question


_Q = "agar kisi ka leo lagna he to konsa gemstoene dharan karna chahiye"


class TestKnowledgeFast(unittest.TestCase):
    def test_detects_leo_gemstone(self):
        q = prepare_ask_question(_Q)
        self.assertTrue(is_astrology_knowledge_fast_question(q))

    def test_skips_personal_chart_gem(self):
        q = prepare_ask_question("mere liye kaunsa gemstone pehnna chahiye")
        self.assertFalse(is_astrology_knowledge_fast_question(q))

    def test_classical_fallback_mentions_ruby(self):
        q = prepare_ask_question(_Q)
        # Classical-first — no LLM mock needed.
        out = try_astrology_knowledge_fast_answer(q, lang="hn")
        self.assertIsNotNone(out)
        self.assertEqual(out.get("source"), "knowledge_fast_classical")
        text = (out.get("text") or "").lower()
        self.assertTrue("manik" in text or "ruby" in text)
        self.assertNotIn("kshama", text)

    def test_personal_shani_not_knowledge_fast(self):
        q = prepare_ask_question("mera shani kahan he")
        self.assertFalse(is_astrology_knowledge_fast_question(q))


if __name__ == "__main__":
    unittest.main()

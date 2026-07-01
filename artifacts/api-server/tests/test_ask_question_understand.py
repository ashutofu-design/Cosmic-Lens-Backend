"""Tests for mandatory question understanding."""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import build_llm_understood_one_liner, resolve_question_understood
from ask_question_understand import (
    _summary_is_weak,
    ensure_question_understanding,
    narrator_intent_hint,
)


class TestQuestionUnderstand(unittest.TestCase):
    def test_weak_summary_detects_echo(self):
        q = "mujhse dhan karne me itni dikkat kyun aati he " * 3
        self.assertTrue(_summary_is_weak(q[:80], q))

    def test_ensure_fallback_without_client(self):
        out = ensure_question_understanding(
            "dhan kamane me dikkat kyun",
            {"domain": "finance"},
            force_llm=False,
        )
        self.assertTrue(str(out.get("question_summary") or "").strip())
        self.assertEqual(out.get("question_understood"), "yes")

    def test_understood_yes_when_summary_present(self):
        li = {"question_summary": "Dhan kamane mein bar-bar dikkat kyun aati hai", "domain": "finance"}
        self.assertEqual(
            resolve_question_understood("dhan dikkat", li, intent_source="llm"),
            "yes",
        )

    def test_admin_line_shows_summary_first(self):
        li = {
            "domain": "finance",
            "finance_archetype": "loss_reasons",
            "confidence": 0.9,
            "source": "llm",
            "question_summary": "Paisa kamane mein mushkil kyun rehti hai",
        }
        line = build_llm_understood_one_liner("dhan dikkat kyun", li, intent_source="llm")
        self.assertIn("Paisa kamane", line)
        self.assertTrue(line.startswith("Yes"))

    def test_narrator_hint_uses_summary(self):
        hint = narrator_intent_hint(
            "dhan dikkat",
            {"question_summary": "Dhan kamaane mein problem kyun"},
        )
        self.assertIn("Dhan kamaane", hint)
        self.assertIn("USER ASKED", hint)

    @patch("ask_question_understand.llm_understand_question")
    def test_force_llm_fills_summary(self, mock_llm):
        mock_llm.return_value = {
            "question_summary": "User puch raha hai dhan kamane mein dikkat kyun hoti hai",
            "understood": True,
            "source": "understand_llm",
        }
        out = ensure_question_understanding("dhan karne me dikkat", None, force_llm=True)
        self.assertIn("dhan kamane", str(out.get("question_summary") or "").lower())
        mock_llm.assert_called_once()


if __name__ == "__main__":
    unittest.main()

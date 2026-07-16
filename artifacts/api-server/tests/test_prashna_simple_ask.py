"""Smoke tests for Prashna Kundli simple ask (not Ask Anything)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestPrashnaSimpleAsk(unittest.TestCase):
    def test_knowledge_branch_uses_knowledge_fast(self):
        from prashna_simple_ask import ask_prashna_simple

        with mock.patch(
            "ask_understand_phase2.run_understand_phase2",
            return_value={
                "ok": True,
                "branch": "knowledge",
                "effective_question": "3rd house strong for younger brother?",
            },
        ), mock.patch(
            "ask_knowledge_fast.try_astrology_knowledge_fast_answer",
            return_value={
                "text": "Younger sibling ke liye 3rd house strong better maana jata hai.",
                "source": "knowledge_fast_llm",
            },
        ):
            out = ask_prashna_simple("agar mera chota bhai he to 3rd house strong?")
        self.assertTrue(out["ok"])
        self.assertEqual(out["mode"], "knowledge")
        self.assertIn("3rd", out["text"])

    def test_personal_requires_kundli(self):
        from prashna_simple_ask import ask_prashna_simple

        with mock.patch(
            "ask_understand_phase2.run_understand_phase2",
            return_value={
                "ok": True,
                "branch": "engine",
                "effective_question": "Mera career kaisa hai?",
            },
        ):
            out = ask_prashna_simple("Mera career kaisa hai?", kundli=None, user=None)
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "kundli_required")

    def test_personal_uses_d1_llm(self):
        from prashna_simple_ask import ask_prashna_simple

        with mock.patch(
            "ask_understand_phase2.run_understand_phase2",
            return_value={
                "ok": True,
                "branch": "engine",
                "effective_question": "Mera career kaisa hai?",
            },
        ), mock.patch(
            "prashna_simple_ask._compact_d1_dasha",
            return_value="Lagna Leo.",
        ), mock.patch(
            "prashna_simple_ask._llm_personal_answer",
            return_value="Career mein steady growth dikhti hai.",
        ):
            out = ask_prashna_simple(
                "Mera career kaisa hai?",
                kundli={"planets": []},
            )
        self.assertTrue(out["ok"])
        self.assertEqual(out["mode"], "personal")
        self.assertEqual(out["source"], "prashna_simple_d1")
        self.assertFalse(out.get("timing"))

    def test_timing_includes_dasha_flag(self):
        from prashna_simple_ask import ask_prashna_simple

        with mock.patch(
            "ask_understand_phase2.run_understand_phase2",
            return_value={
                "ok": True,
                "branch": "engine",
                "timing": True,
                "question_type": "timing",
                "effective_question": "Meri shaadi kab hogi?",
            },
        ), mock.patch(
            "prashna_simple_ask._compact_d1_dasha",
            return_value="Lagna Leo. MD Saturn.",
        ) as compact, mock.patch(
            "prashna_simple_ask._llm_personal_answer",
            return_value="2027 ke around window dikhti hai.",
        ):
            out = ask_prashna_simple(
                "Meri shaadi kab?",
                kundli={"planets": []},
            )
        self.assertTrue(out["ok"])
        self.assertTrue(out.get("timing"))
        self.assertEqual(out["source"], "prashna_simple_d1_dasha")
        compact.assert_called_once()
        self.assertTrue(compact.call_args.kwargs.get("include_dasha"))


if __name__ == "__main__":
    unittest.main()

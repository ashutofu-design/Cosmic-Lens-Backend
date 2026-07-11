"""Cosmo Ask engine narrator prompt and post-processing."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_cosmo_narrator import (
    build_cosmo_ask_length_block,
    enforce_cosmo_engine_answer,
    is_cosmo_engine_slice,
)
from ask_mr.narrator import build_mr_engine_narrator_system_prompt


class TestCosmoNarrator(unittest.TestCase):
    def test_engine_slice_ids(self):
        self.assertTrue(is_cosmo_engine_slice("open_chart_qa_engine_v1"))
        self.assertTrue(is_cosmo_engine_slice("health_engine_v1"))
        self.assertFalse(is_cosmo_engine_slice("timing_v1"))

    def test_prompt_has_markdown_sections(self):
        prompt = build_mr_engine_narrator_system_prompt(
            chart_text="VERDICT: test\n+ Venus in 9th",
            archetype="open_chart_qa",
            open_chart_qa=True,
        )
        self.assertIn("Cosmo Ask", prompt)
        self.assertIn("The Big Picture", prompt)
        self.assertIn("Ab kya karein", prompt)

    def test_batch_concise_prompt_is_short_form(self):
        prompt = build_mr_engine_narrator_system_prompt(
            chart_text="VERDICT: test",
            archetype="general_mr",
            concise=True,
        )
        self.assertIn("batch test", prompt.lower())
        self.assertNotIn("The Big Picture", prompt)
        self.assertIn("35", prompt)
        self.assertIn("90", prompt)

    def test_enforce_preserves_markdown(self):
        md = (
            "**The Big Picture**\n"
            "Bhai, tera love style warm aur expressive hai.\n\n"
            "---\n\n"
            "**Kyun aisa lagta hai**\n"
            "Detail line here.\n\n"
            "---\n\n"
            "**Ab kya karein**\n"
            "* Baat-cheet clear rakho\n"
            "> Patience se bond strong hota hai."
        )
        out = enforce_cosmo_engine_answer(md)
        self.assertIn("---", out)
        self.assertIn("* Baat-cheet", out)

    def test_length_block_word_range(self):
        block = build_cosmo_ask_length_block(wants_explain=False, topic="love")
        self.assertIn("180", block)
        self.assertIn("280", block)


if __name__ == "__main__":
    unittest.main()

"""Tests for universal story-style MR answers."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_mr.story_answer import (
    looks_like_bad_story_llm_output,
    render_story_human_answer,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.loyalty_trust import run_loyalty_trust_v2
from ask_mr.loyalty_narrator import engine_result_to_loyalty_json

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Jupiter", "sign": "Libra", "house": 11},
    ],
    "dasha": {"mahadasha": "Venus", "antardasha": "Jupiter"},
}


class StoryAnswerTests(unittest.TestCase):
    def test_rejects_counseling_llm(self):
        bad = (
            "Asli wajah yeh hai ki chart me signals zyada hain. "
            "Main aapko kehna chahungi ki thanda dimaag rakho."
        )
        self.assertTrue(looks_like_bad_story_llm_output(bad))

    def test_loyalty_story_shape(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        out = run_loyalty_trust_v2(SAMPLE_KUNDLI, "kya mera partner loyal hai")
        data = engine_result_to_loyalty_json(v2_to_engine_result(out), question="kya mera partner loyal hai")
        text = render_story_human_answer(data, "kya mera partner loyal hai", engine="loyalty_trust")
        self.assertRegex(text, r"(?i)seedhi baat|chart")
        self.assertNotIn("Asli wajah seedhi hai", text)
        self.assertNotIn("Jo mukhya sanket", text)
        self.assertRegex(text, r"(?i)confidence")


if __name__ == "__main__":
    unittest.main()

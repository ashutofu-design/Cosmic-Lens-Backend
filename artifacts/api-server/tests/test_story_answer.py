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

    def test_secret_chart_pinpoints_in_story(self):
        data = {
            "question_type": "secret_relationship",
            "final_verdict": "Likely",
            "direct_answer": "Partner kisi aur me interest ke likely indicators active hain.",
            "original_question": "kya mera partner kisi aur me intrested he",
            "strongest": ["Moon in 7th — emotional bond strong"],
            "weakest": ["Venus in 12th house — hidden romance tone"],
            "strongest_effects": ["Emotional bond supportive hai."],
            "weakest_effects": ["Hidden-romance tone secret attention signals ko colour karta hai."],
            "practical_guidance": "Accusation se pehle facts collect karein — calm approach rakhein.",
            "confidence": 45,
            "confidence_label": "Medium",
            "confidence_explanation": "Confidence Medium (45%) hai kyunki zyada tar indicators secrecy direction me hain.",
        }
        text = render_story_human_answer(
            data,
            "kya mera partner kisi aur me intrested he",
            engine="secret_relationship",
        )
        self.assertRegex(text, r"(?i)venus.*12")
        self.assertRegex(text, r"(?i)moon.*7")
        self.assertNotIn("Likely matlab secrecy signals", text)


if __name__ == "__main__":
    unittest.main()

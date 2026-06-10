"""Unit test: when pro has chapter bodies, PDF data uses LLM not engine fallback."""
from __future__ import annotations

import unittest

from vedic.love_reality.pdf_data_v2 import build_love_reality_pdf_v2_context


def _fake_pro() -> dict:
    long = " ".join(["word"] * 120)
    return {
        "verdict": long,
        "chapters": [
            {"key": "love_connection", "chapter_body": f"LLM_LOVE_CONNECTION {long}"},
            {"key": "breakup", "chapter_body": f"LLM_BREAKUP {long}"},
            {"key": "loyalty", "chapter_body": f"LLM_LOYALTY {long}"},
            {"key": "red_flags", "chapter_body": f"LLM_RED_FLAGS {long}"},
        ],
        "harmony": f"LLM_HARMONY {long}",
        "moon_sync_narrative": f"LLM_MOON_SYNC {long}",
        "blueprint_reality": f"LLM_BLUEPRINT_REALITY {long}",
    }


def _minimal_bundle() -> dict:
    return {
        "p1": {"name": "a"},
        "p2": {"name": "R"},
        "kundli_p1": {"moonSign": "Gemini", "ascendant": "Sagittarius", "planets": []},
        "kundli_p2": {"moonSign": "Taurus", "ascendant": "Gemini", "planets": []},
        "love_compatibility": {
            "score": 13,
            "emotional_summary": "ENGINE_ONE_LINER fallback",
            "breakdown": {},
            "reasons": [],
        },
        "breakup_chances": {"breakup_score": 100, "reasons": []},
        "loyalty_check": {"loyalty_score": 0, "reasons": []},
        "will_return": {"return_probability": 8},
        "future_outcome": {"future_score": 33, "timeline_flow": []},
        "hidden_red_flags": {"reasons": ["ENGINE_BULLET_ONLY"]},
    }


class TestSectionPdfMapping(unittest.TestCase):
    def test_love_connection_and_red_flags_use_llm_not_engine(self):
        ctx = build_love_reality_pdf_v2_context(
            _minimal_bundle(),
            _fake_pro(),
            {"name": "a"},
            {"name": "R"},
            "en",
        )
        part2 = ctx["page2_3_blueprint"]["part2"]
        self.assertIn("LLM_BLUEPRINT_REALITY", part2)
        self.assertNotIn("ENGINE_ONE_LINER", part2)

        root = ctx["page6_root_cause"]
        self.assertIn("LLM_BREAKUP", root)
        self.assertNotIn("LLM_LOYALTY", root, "loyalty must not bleed into root cause")

        rf_body = ctx["page8_red_flags"]["body"]
        self.assertIn("LLM_RED_FLAGS", rf_body)

        self.assertIn("LLM_HARMONY", ctx["page9_harmony"])

        moon_body = ctx["page5_moon"]["body"]
        self.assertIn("LLM_MOON_SYNC", moon_body)
        self.assertNotIn("emotional rhythm out of sync", moon_body.lower())


if __name__ == "__main__":
    unittest.main()

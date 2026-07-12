"""Tests for presenter-only LLM mode — JSON formatting, no astro invention."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_mr.v2.engines.commitment import run_commitment_v2
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.story_answer import engine_result_to_narrator_json, render_story_human_answer
from ask_mr.engine_presenter import (
    build_engine_presenter_system_prompt,
    detect_astro_jargon,
    engine_llm_enabled,
    extract_presenter_fields,
    human_narrator_enabled,
    use_engine_presenter_mode,
    validate_presenter_output,
)

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Jupiter", "sign": "Libra", "house": 11},
        {"name": "Saturn", "sign": "Aries", "house": 5},
    ],
    "dasha": {"mahadasha": "Venus", "antardasha": "Jupiter"},
}


class EnginePresenterTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self._saved = {
            k: os.environ.get(k)
            for k in (
                "ASK_ENGINE_PRESENTER",
                "ASK_COMMITMENT_PRESENTER",
                "ASK_COMMITMENT_USE_LLM",
            )
        }
        self.out = run_commitment_v2(
            SAMPLE_KUNDLI,
            "Kya mera partner commitment ke liye ready hai?",
        )
        self.result = v2_to_engine_result(self.out)
        self.data = engine_result_to_narrator_json(
            self.result,
            question="Kya mera partner commitment ke liye ready hai?",
        )

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_presenter_mode_on_when_commitment_llm_on(self):
        os.environ["ASK_COMMITMENT_USE_LLM"] = "1"
        os.environ.pop("ASK_COMMITMENT_PRESENTER", None)
        self.assertTrue(use_engine_presenter_mode("commitment"))

    def test_presenter_mode_off_when_global_disabled(self):
        os.environ["ASK_COMMITMENT_USE_LLM"] = "1"
        os.environ["ASK_ENGINE_PRESENTER"] = "0"
        self.assertFalse(use_engine_presenter_mode("commitment"))

    def test_presenter_mode_off_when_per_engine_disabled(self):
        os.environ["ASK_COMMITMENT_USE_LLM"] = "1"
        os.environ["ASK_COMMITMENT_PRESENTER"] = "0"
        self.assertFalse(use_engine_presenter_mode("commitment"))

    def test_extract_presenter_fields_commitment(self):
        fields = extract_presenter_fields("commitment", self.data)
        self.assertEqual(fields["engine"], "commitment")
        self.assertIn("direct_answer", fields)
        self.assertIn("strongest_effects", fields)
        self.assertIn("weakest_effects", fields)
        self.assertIn("confidence_explanation", fields)
        self.assertNotIn("strongest", fields)
        self.assertNotIn("scorecard", fields)

    def test_presenter_prompt_contains_json_fields(self):
        prompt = build_engine_presenter_system_prompt(
            engine="commitment",
            narrator_json=self.data,
            lang="hn",
            question="Kya mera partner commitment ke liye ready hai?",
        )
        self.assertIn("ENGINE_JSON", prompt)
        self.assertIn("Cosmic Lens Relationship Narrator", prompt)
        self.assertIn(self.data["direct_answer"], prompt)

    def test_detect_astro_jargon(self):
        hits = detect_astro_jargon("Venus in 7th house shows strong commitment.")
        self.assertIn("venus", hits)
        self.assertTrue(any("house" in h for h in hits))

    def test_validate_rejects_invented_astro(self):
        locked = render_story_human_answer(
            self.data, "test question", engine="commitment", lang="hn"
        )
        bad = locked + " Venus 7th house se support milta hai."
        ok, issues = validate_presenter_output(bad, self.data, "commitment")
        self.assertFalse(ok)
        self.assertTrue(any("astro_jargon" in i for i in issues))

    def test_validate_accepts_locked_template_rephrase(self):
        locked = render_story_human_answer(
            self.data,
            "Kya mera partner commitment ke liye ready hai?",
            engine="commitment",
            lang="hn",
        )
        ok, issues = validate_presenter_output(locked, self.data, "commitment")
        self.assertTrue(ok or "counseling_fluff" in issues, msg=f"issues={issues}")

    def test_human_narrator_default_on(self):
        os.environ.pop("ASK_MR_HUMAN_NARRATOR", None)
        self.assertTrue(human_narrator_enabled())
        self.assertTrue(engine_llm_enabled("secret_relationship"))

    def test_secret_presenter_accepts_prose_without_section_labels(self):
        data = {
            "final_verdict": "Likely",
            "secret_level": "likely",
            "secrecy_level": "likely",
            "confidence": 45,
            "confidence_label": "Medium",
        }
        human = (
            "Seedhi baat — partner kisi aur me interest ke signs chart me active dikh rahe hain, "
            "isliye verdict Likely hai. Trust ko test karne wale signals hain, blind trust avoid karein. "
            "Confidence Medium (45%) hai kyunki zyada tar indicators secrecy-challenging direction me hain."
        )
        ok, issues = validate_presenter_output(human, data, "secret_relationship")
        self.assertTrue(ok, msg=f"issues={issues}")

    def test_presenter_rejects_cosmo_markdown(self):
        data = {
            "final_verdict": "Likely",
            "confidence": 45,
            "confidence_label": "Medium",
        }
        bad = (
            "**The Big Picture**\nBhai chance hai.\n\n"
            "**Kyun aisa lagta hai (deep breakdown)**\nLong story.\n\n"
            "Confidence Medium (45%) hai kyunki test."
        )
        ok, issues = validate_presenter_output(bad, data, "secret_relationship")
        self.assertFalse(ok)
        self.assertTrue(any("cosmo_markdown" in i for i in issues))


if __name__ == "__main__":
    unittest.main()

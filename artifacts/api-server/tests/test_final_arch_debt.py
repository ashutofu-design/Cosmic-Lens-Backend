"""Final-arch regression tests."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestFinalArchDebt(unittest.TestCase):
    def test_only_two_branches(self):
        from ask_understand_phase2 import BRANCHES, normalize_branch

        self.assertEqual(BRANCHES, frozenset({"knowledge", "engine"}))
        self.assertEqual(normalize_branch("refuse"), "engine")
        self.assertEqual(normalize_branch("llm_knowledge"), "knowledge")

    def test_domain_maps_to_engine_flags(self):
        from ask_understand_phase2 import phase2_engine_static_flags

        flags = phase2_engine_static_flags(
            {"branch": "engine", "domain": "love", "archetype": "trust_loyalty"}
        )
        self.assertTrue(flags["mr"])
        self.assertFalse(flags["career"])
        self.assertFalse(flags["health"])

    def test_no_engine_bypass(self):
        from ask_routing_policy import should_bypass_static_engines_for_direct_llm

        bypass, reason = should_bypass_static_engines_for_direct_llm(
            "D10 me Sun kya kehta hai?",
            {"domain": "career", "answer_mode": "llm_chart"},
        )
        self.assertFalse(bypass)
        self.assertEqual(reason, "")

    def test_flask_no_duplicate_gates(self):
        flask = Path(__file__).resolve().parents[1].joinpath("flask_app.py").read_text(
            encoding="utf-8"
        )
        # After shortcut, RP owns gates — no assess_ask_language in flask.
        self.assertNotIn("assess_ask_language", flask)
        self.assertNotIn("apply_privacy_guard", flask)
        self.assertIn("raw_passthrough_ask", flask)

    def test_narrator_is_final_modifier(self):
        src = Path(__file__).resolve().parents[1].joinpath("openai_helper.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("PHASE1_RAW_NARRATOR", src)
        idx = src.find("PHASE1_RAW_NARRATOR")
        window = src[idx : idx + 3000]
        self.assertNotIn("enforce_cosmo_engine_answer", window)
        self.assertNotIn("polish_mr_confident_tone", window)
        self.assertNotIn("guard_answer_with_fidelity_loop", window)
        self.assertNotIn("_strip_decision_template_labels", window)

    def test_phase2_sole_route_markers(self):
        src = Path(__file__).resolve().parents[1].joinpath("openai_helper.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("PHASE2_SOLE_ROUTE", src)
        self.assertIn("PHASE2_ENGINE_FLAGS", src)
        self.assertIn("knowledge_fast after PHASE2", src)
        self.assertNotIn("knowledge_fast emergency_fallback", src)

    def test_prompt_owns_tone(self):
        from ask_mr.narrator import _MR_CONFIDENT_TONE, build_mr_engine_narrator_system_prompt
        from ask_mr.relationship_narrator import RELATIONSHIP_NARRATOR_RULES

        self.assertIn("BANNED hedging", _MR_CONFIDENT_TONE)
        self.assertIn("FINAL", RELATIONSHIP_NARRATOR_RULES)
        prompt = build_mr_engine_narrator_system_prompt(
            chart_text="VERDICT: ok",
            reply_lang="hn",
            wants_explain=False,
            archetype="trust_loyalty",
            word_budget=80,
        )
        self.assertIn("BANNED hedging", prompt)
        self.assertIn("OUTPUT FORMAT", prompt)


if __name__ == "__main__":
    unittest.main()

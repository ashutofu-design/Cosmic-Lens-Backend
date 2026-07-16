"""Phase 2: Understand decides branch before knowledge_fast / engines."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestPhase2Understand(unittest.TestCase):
    def test_normalize_branch_and_schema(self):
        from ask_understand_phase2 import normalize_understand, understand_to_admin

        u = normalize_understand(
            {
                "branch": "knowledge",
                "domain": "remedy",
                "archetype": "gemstone_remedy",
                "question_type": "remedy",
                "timing": False,
                "subject": "other",
                "target": "situation",
                "knowledge": True,
                "question_summary": "User Leo lagna ke liye classical gemstone rule jaanna chahta hai.",
                "confidence": 0.9,
            },
            question="Leo lagna gemstone?",
        )
        self.assertEqual(u["branch"], "knowledge")
        self.assertTrue(u["knowledge"])
        self.assertEqual(u["answer_mode"], "llm_knowledge")

        admin = understand_to_admin(u, question="Leo lagna gemstone?")
        self.assertEqual(admin["branch"], "knowledge")
        self.assertEqual(admin["routed_domain"], "remedy")
        dna = admin["question_dna"]
        self.assertEqual(dna["source"], "understand_phase2")
        self.assertEqual(dna["questions"][0]["bucket"], "gemstone_remedy")

    def test_answer_mode_compat_maps_to_branch(self):
        from ask_understand_phase2 import normalize_branch

        self.assertEqual(normalize_branch("llm_knowledge"), "knowledge")
        self.assertEqual(normalize_branch("engine"), "engine")
        self.assertEqual(normalize_branch("refuse"), "refuse")

    def test_knowledge_fast_force_skips_regex_gate(self):
        from ask_knowledge_fast import try_astrology_knowledge_fast_answer

        # Personal-sounding but Understand already said knowledge — force allows classical.
        out = try_astrology_knowledge_fast_answer(
            "Leo lagna ke liye kaunsa gemstone?",
            lang="hn",
            force=True,
        )
        self.assertIsNotNone(out)
        self.assertIn("Manik", out["text"])
        self.assertEqual(out["source"], "knowledge_fast_classical")

    def test_raw_passthrough_no_early_knowledge_fast(self):
        src = Path(__file__).resolve().parents[1].joinpath("openai_helper.py").read_text(
            encoding="utf-8"
        )
        # Early regex shortcut must be gone; Phase2 marker must exist.
        self.assertIn("PHASE2_UNDERSTAND", src)
        self.assertIn("knowledge_fast after PHASE2", src)
        # The old comment block should not call try_* before PHASE2.
        early = src.split("PHASE2_UNDERSTAND", 1)[0]
        # After death/privacy section start — still before PHASE2 — must not call KF.
        self.assertNotIn("try_astrology_knowledge_fast_answer(question or \"\", lang=lang or \"hn\")", early)

    def test_phase2_enabled_by_default(self):
        from ask_understand_phase2 import phase2_understand_enabled

        old = os.environ.pop("ASK_UNDERSTAND_PHASE2", None)
        try:
            self.assertTrue(phase2_understand_enabled())
        finally:
            if old is not None:
                os.environ["ASK_UNDERSTAND_PHASE2"] = old

    def test_run_understand_mocked_branch_knowledge(self):
        from ask_understand_phase2 import run_understand_phase2

        class _Msg:
            content = (
                '{"branch":"knowledge","domain":"remedy","archetype":"gemstone_remedy",'
                '"question_type":"remedy","timing":false,"subject":"other","target":"situation",'
                '"knowledge":true,"question_summary":"Named Leo lagna gemstone rule chahiye.",'
                '"confidence":0.91}'
            )

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        client = mock.Mock()
        client.chat.completions.create.return_value = _Resp()
        out = run_understand_phase2("Leo lagna gemstone?", client=client)
        self.assertTrue(out["ok"])
        self.assertEqual(out["branch"], "knowledge")
        self.assertTrue(out["knowledge"])


if __name__ == "__main__":
    unittest.main()

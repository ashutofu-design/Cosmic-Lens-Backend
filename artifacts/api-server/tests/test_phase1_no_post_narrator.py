"""Phase 1: no post-narrator modifiers after main LLM."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestPhase1NoPostNarrator(unittest.TestCase):
    def test_fidelity_off_by_default(self):
        from ask_answer_fidelity import fidelity_enabled

        old = os.environ.pop("ANSWER_FIDELITY_ENABLED", None)
        try:
            self.assertFalse(fidelity_enabled())
        finally:
            if old is not None:
                os.environ["ANSWER_FIDELITY_ENABLED"] = old

    def test_gatekeeper_off_by_default(self):
        from ask_execution_gatekeeper import gatekeeper_enabled

        old = os.environ.pop("ASK_EXECUTION_GATEKEEPER", None)
        try:
            self.assertFalse(gatekeeper_enabled())
        finally:
            if old is not None:
                os.environ["ASK_EXECUTION_GATEKEEPER"] = old

    def test_dna_judge_off_by_default(self):
        from ask_unified import domain_dna_judge_enabled

        for key in list(os.environ):
            if key.endswith("_DNA_JUDGE") or key == "ASK_UNIFIED_DNA_JUDGE":
                os.environ.pop(key, None)
        self.assertFalse(domain_dna_judge_enabled("health"))
        self.assertFalse(domain_dna_judge_enabled("relationship"))
        self.assertFalse(domain_dna_judge_enabled("spiritual"))

    def test_raw_passthrough_has_phase1_marker(self):
        from pathlib import Path

        src = Path(__file__).resolve().parents[1].joinpath("openai_helper.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("PHASE1_RAW_NARRATOR", src)
        self.assertIn("phase1_no_post_narrator", src)
        # Post-modifier calls must not appear after the Phase1 marker.
        idx = src.find("PHASE1_RAW_NARRATOR")
        window = src[idx : idx + 2500]
        self.assertNotIn("guard_answer_with_fidelity_loop", window)
        self.assertNotIn("enforce_cosmo_engine_answer", window)
        self.assertNotIn("check_final_answer_gate", window)
        self.assertNotIn("guard_career_answer", window)


if __name__ == "__main__":
    unittest.main()

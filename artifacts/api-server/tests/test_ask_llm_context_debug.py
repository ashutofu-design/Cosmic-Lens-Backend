import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_llm_context_debug import (
    build_admin_llm_context,
    derive_answer_path,
    parse_llm_context_from_db,
    serialize_llm_context_for_db,
)


class AskLlmContextDebugTests(unittest.TestCase):
    def test_roundtrip_serialize(self):
        ctx = build_admin_llm_context(
            question="mera partner kaisa hoga",
            checks={"slice_type": "marriage_relationship"},
            chart_text="=== MARRIAGE SLICE ===",
            system_prompt="You are Cosmo",
        )
        raw = serialize_llm_context_for_db(ctx)
        self.assertIsNotNone(raw)
        parsed = parse_llm_context_from_db(raw)
        self.assertEqual(parsed["checks"]["slice_type"], "marriage_relationship")
        self.assertIn("MARRIAGE SLICE", parsed["chart_text"])

    def test_answer_path_engine_then_llm(self):
        ctx = build_admin_llm_context(
            question="love marriage ya arrange",
            llm_called=True,
            checks={"slice_type": "mr_engine_v1", "mr_engine": "v1", "is_mr_static": True},
            slice_meta={
                "slice": "mr_engine_v1",
                "verdict": "Arrange side stronger",
                "evidence": ["Arrange indicator: Manglik dosha"],
            },
            model="gpt-4.1-mini",
        )
        self.assertEqual(ctx["answer_path"], "engine_then_llm")
        self.assertEqual(ctx["engine_facts"]["verdict"], "Arrange side stronger")
        self.assertEqual(len(ctx["engine_facts"]["evidence"]), 1)

    def test_answer_path_engine_only(self):
        code, label = derive_answer_path(
            llm_called=False,
            skip_reason="mr_engine_template",
            checks={"skip_llm": True},
            slice_meta={"slice": "mr_engine_v1", "verdict": "Manglik: yes"},
        )
        self.assertEqual(code, "engine_only")
        self.assertIn("no LLM", label)

    def test_answer_path_direct_llm(self):
        code, _ = derive_answer_path(
            llm_called=True,
            checks={"slice_type": "compact_chart"},
            slice_meta={},
        )
        self.assertEqual(code, "direct_llm")


if __name__ == "__main__":
    unittest.main()

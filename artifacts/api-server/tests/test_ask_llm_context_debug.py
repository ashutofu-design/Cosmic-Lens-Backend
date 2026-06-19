import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_llm_context_debug import (
    build_admin_llm_context,
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


if __name__ == "__main__":
    unittest.main()

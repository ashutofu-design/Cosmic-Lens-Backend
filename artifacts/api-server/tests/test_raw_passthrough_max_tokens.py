"""Engine narrator max_tokens budget."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai_helper import _raw_passthrough_max_tokens


class TestRawPassthroughMaxTokens(unittest.TestCase):
    def test_children_engine_default_480(self):
        meta = {"slice": "children_engine_v1"}
        self.assertEqual(
            _raw_passthrough_max_tokens(
                wants_explain=False,
                is_timing=False,
                is_decision=False,
                is_finance=False,
                dcr_love_meta=meta,
                is_sensitive=False,
            ),
            480,
        )

    def test_children_engine_explain_650(self):
        meta = {"slice": "children_engine_v1"}
        self.assertEqual(
            _raw_passthrough_max_tokens(
                wants_explain=True,
                is_timing=False,
                is_decision=False,
                is_finance=False,
                dcr_love_meta=meta,
                is_sensitive=False,
            ),
            650,
        )

    def test_non_engine_stays_short(self):
        self.assertEqual(
            _raw_passthrough_max_tokens(
                wants_explain=False,
                is_timing=False,
                is_decision=False,
                is_finance=False,
                dcr_love_meta=None,
                is_sensitive=False,
            ),
            90,
        )


if __name__ == "__main__":
    unittest.main()

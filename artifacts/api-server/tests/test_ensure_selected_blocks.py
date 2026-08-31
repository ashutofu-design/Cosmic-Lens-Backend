"""Engine execution must never ship without selected blocks."""
from __future__ import annotations

import unittest

_MINIMAL_EE = {
    "schema_version": "career_engine_execution_v1",
    "domain": "career",
    "d1": {
        "ascendant": "Leo",
        "house_lords": {
            "h10": {
                "lord": "Venus",
                "lord_house": 3,
                "lord_sign": "Libra",
                "lord_dignity": "own",
                "lord_strength_score": 2,
            },
        },
        "karakas": {
            "Saturn": {"sign": "Aquarius", "house": 7, "dignity": "own", "strength_score": 2},
            "Sun": {"sign": "Leo", "house": 1, "dignity": "own", "strength_score": 2},
        },
        "dimensions": {
            "career_strength": {"verdict": "GREEN", "reason": "10th lord strong"},
        },
    },
    "composite_score": 72,
    "strength_label": "moderate career",
}


class TestEnsureSelectedBlocks(unittest.TestCase):
    def test_empty_blocks_get_minimum_from_execution(self):
        from ask_selected_blocks_common import ensure_minimum_selected_blocks

        blocks, used = ensure_minimum_selected_blocks(
            [],
            _MINIMAL_EE,
            question="Career kaisi rahegi?",
            focus="general_career",
            domain="career",
        )
        self.assertTrue(used)
        self.assertGreaterEqual(len(blocks), 1)
        self.assertTrue(all(b.get("rank") for b in blocks))

    def test_finalize_audit_never_blocks_empty_when_ee_present(self):
        from ask_selected_blocks_common import (
            coverage_check_selected_blocks,
            finalize_selected_blocks_audit,
        )

        audit = finalize_selected_blocks_audit(
            {
                "applies": True,
                "focus": "general_career",
                "expected_blocks": [],
                "available_blocks": [],
                "domain": "career",
            },
            _MINIMAL_EE,
            question="Which sector is best?",
        )
        self.assertTrue(audit.get("expected_blocks"))
        self.assertTrue(audit.get("priority_facts_for_llm"))
        coverage = coverage_check_selected_blocks(
            "Which sector is best?",
            audit=audit,
            execution=_MINIMAL_EE,
        )
        issues = coverage.get("issues") or []
        self.assertFalse(any("blocks_empty" in str(i) for i in issues))

    def test_unified_build_domain_selected_blocks_never_empty(self):
        from ask_unified import build_domain_selected_blocks

        out = build_domain_selected_blocks(
            "Career me technology ya marketing?",
            "",
            domain="career",
            execution=_MINIMAL_EE,
            meta={"routing_label": "general_career"},
        )
        self.assertTrue(out.get("expected_blocks"))
        self.assertTrue(out.get("priority_facts_for_llm"))


if __name__ == "__main__":
    unittest.main()

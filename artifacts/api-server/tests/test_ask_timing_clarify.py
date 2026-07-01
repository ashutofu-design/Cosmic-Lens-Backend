"""Tests for vague timing domain clarifier."""
from __future__ import annotations

import unittest

from ask_timing_clarify import (
    build_timing_domain_clarifier_result,
    needs_timing_domain_clarifier,
)


class TestTimingDomainClarifier(unittest.TestCase):
    def test_vague_life_struggle_needs_clarifier(self):
        self.assertTrue(
            needs_timing_domain_clarifier("Mera life me struggle kab jaayega"),
        )

    def test_specific_career_does_not_need_clarifier(self):
        self.assertFalse(
            needs_timing_domain_clarifier("Career me struggle kab khatam hogi?"),
        )

    def test_specific_marriage_does_not_need_clarifier(self):
        self.assertFalse(
            needs_timing_domain_clarifier("Shaadi me delay kab khatam hogi?"),
        )

    def test_mukti_spiritual_timing_skips_clarifier(self):
        q = "Mera mukti kab hoga"
        llm = {"domain": "general", "is_timing": True}
        self.assertFalse(needs_timing_domain_clarifier(q, llm))
        self.assertFalse(needs_timing_domain_clarifier(q, None))

    def test_clarifier_has_tappable_options(self):
        out = build_timing_domain_clarifier_result("Mera life me struggle kab jaayega")
        self.assertEqual(out["source"], "timing_domain_clarifier")
        self.assertEqual(out["topic"], "needs_clarification")
        self.assertIn("clarification", out)
        opts = out["clarification"]["options"]
        self.assertGreaterEqual(len(opts), 4)
        self.assertTrue(any("Career" in o for o in opts))
        self.assertTrue(any("Paisa" in o for o in opts))


if __name__ == "__main__":
    unittest.main()

"""Tests for global Ask hard guards (death refusal + engine-only policy)."""

from __future__ import annotations

import os
import unittest


class TestDeathLifespanGuard(unittest.TestCase):
    def test_death_timing_question_detected(self):
        from ask_hard_guards import is_death_lifespan_question

        cases = [
            "Mera death kab hoga",
            "death kab hogi meri?",
            "kab marunga main?",
            "kitni umar hai meri?",
            "when will I die?",
        ]
        for q in cases:
            with self.subTest(q=q):
                self.assertTrue(is_death_lifespan_question(q), q)

    def test_death_refusal_has_no_llm_source(self):
        from ask_hard_guards import death_refusal_result

        out = death_refusal_result("Mera death kab hoga")
        self.assertEqual(out["source"], "refuse_death")
        self.assertIn("death", out["text"].lower())
        self.assertNotIn("8th house", out["text"].lower())


class TestEngineOnlyPolicy(unittest.TestCase):
    def test_direct_llm_off_by_default(self):
        from ask_hard_guards import direct_llm_allowed

        old = os.environ.pop("RAW_PASSTHROUGH_DIRECT_LLM", None)
        try:
            self.assertFalse(direct_llm_allowed())
        finally:
            if old is not None:
                os.environ["RAW_PASSTHROUGH_DIRECT_LLM"] = old

    def test_passthrough_has_engine_with_marriage_block(self):
        from ask_hard_guards import passthrough_has_domain_engine_facts

        self.assertTrue(
            passthrough_has_domain_engine_facts(
                checks={"is_marriage_engine": True},
                marriage_block="PRIMARY_WINDOW: June 2029",
            )
        )

    def test_passthrough_flags_alone_not_enough(self):
        from ask_hard_guards import passthrough_has_domain_engine_facts

        self.assertFalse(
            passthrough_has_domain_engine_facts(
                checks={
                    "is_marriage_engine": True,
                    "is_mr_static": True,
                    "is_career_engine": True,
                    "slice_type": "timing_full_chart",
                },
                slice_meta={},
            )
        )

    def test_passthrough_career_timing_slice_meta_counts(self):
        from ask_hard_guards import passthrough_has_domain_engine_facts

        self.assertTrue(
            passthrough_has_domain_engine_facts(
                slice_meta={
                    "slice": "career_timing_v1",
                    "verdict": "yellow_wait",
                    "evidence": ["Saturn delay"],
                },
            )
        )

    def test_enforce_engine_only_blocks_compact_chart(self):
        from ask_hard_guards import enforce_engine_only_or_refuse

        out = enforce_engine_only_or_refuse(
            question="Mera lucky number kya hai?",
            qtype="STATIC",
            checks={"slice_type": "full_compact"},
            slice_meta={},
        )
        self.assertIsNotNone(out)
        self.assertEqual(out["source"], "engine_required")

    def test_enforce_engine_only_allows_career_block(self):
        from ask_hard_guards import enforce_engine_only_or_refuse

        out = enforce_engine_only_or_refuse(
            question="Mera job change kab hoga",
            qtype="TIMING",
            career_block="COSMIC CAREER VERDICT",
            slice_meta={
                "slice": "career_timing_v1",
                "verdict": "yellow_wait",
            },
        )
        self.assertIsNone(out)

    def test_marriage_timing_required_without_block(self):
        from ask_hard_guards import marriage_timing_engine_required

        self.assertTrue(marriage_timing_engine_required("Meri shaadi kab hogi?"))

    def test_career_timing_required_detected(self):
        from ask_hard_guards import career_timing_engine_required

        self.assertTrue(career_timing_engine_required("Mera job change kab hoga"))

    def test_passthrough_no_engine_without_facts(self):
        from ask_hard_guards import passthrough_has_domain_engine_facts

        self.assertFalse(
            passthrough_has_domain_engine_facts(
                checks={"slice_type": "full_compact"},
                slice_meta={},
            )
        )

    def test_no_engine_refusal_message(self):
        from ask_hard_guards import no_engine_refusal_result

        out = no_engine_refusal_result("random chart question")
        self.assertEqual(out["source"], "engine_required")
        self.assertIn("engine", out["text"].lower())

    def test_timing_spec_block_not_counted_as_engine(self):
        from ask_hard_guards import is_real_timing_engine_block, passthrough_has_domain_engine_facts

        spec = (
            "=== TIMING SPEC (GENERAL) — ENGINE READY ===\n"
            "Focus: Career / job\nPipeline:\n  • STEP1"
        )
        self.assertFalse(is_real_timing_engine_block(spec))
        self.assertFalse(
            passthrough_has_domain_engine_facts(domain_timing_block=spec),
        )

    def test_general_life_struggle_timing_requires_engine(self):
        from ask_hard_guards import (
            enforce_engine_only_or_refuse,
            general_timing_engine_required,
        )

        q = "Mera life me struggle kab jaayega"
        self.assertTrue(general_timing_engine_required(q))
        spec_only = (
            "=== TIMING SPEC (GENERAL) — ENGINE READY ===\n"
            "Focus: test"
        )
        out = enforce_engine_only_or_refuse(
            question=q,
            qtype="TIMING",
            domain_timing_block=spec_only,
        )
        self.assertIsNotNone(out)
        self.assertEqual(out["source"], "engine_required")

    def test_vague_struggle_triggers_clarifier_not_health_route(self):
        from ask_timing_clarify import needs_timing_domain_clarifier
        from event_timing.timing_router import resolve_timing_domain

        q = "Mera life me struggle kab jaayega"
        self.assertTrue(needs_timing_domain_clarifier(q))
        dom, bucket, is_timing = resolve_timing_domain(q)
        self.assertTrue(is_timing)
        self.assertEqual(dom, "general")

    def test_career_timing_answer_guard_red_verdict(self):
        from ask_career.answer_guard import verify_career_timing_answer

        ok, issues = verify_career_timing_answer(
            "Mera job change kab hoga",
            "Abhi switch karna favourable hai — interview shuru kar dein.",
            {
                "verdict": "red_avoid",
                "summary": ["4-6 mahine ruk jaayein"],
                "dasha_trace": {"current_lords": "Jupiter/Saturn/Mercury"},
            },
        )
        self.assertFalse(ok)
        self.assertIn("red_verdict_but_positive_switch", issues)

    def test_career_timing_answer_guard_aligned(self):
        from ask_career.answer_guard import verify_career_timing_answer

        ok, issues = verify_career_timing_answer(
            "Mera job change kab hoga",
            "Jupiter Mahadasha me abhi switch risk hai — 4-6 mahine ruk kar consolidate karein.",
            {
                "verdict": "red_avoid",
                "summary": ["4-6 mahine ruk jaayein"],
                "dasha_trace": {"current_lords": "Jupiter/Saturn/Mercury"},
            },
        )
        self.assertTrue(ok, issues)


if __name__ == "__main__":
    unittest.main()

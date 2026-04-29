"""Phase 5.6 — Yoga registry activation tests.

Covers:
  • Question detector (`_phase56_is_yoga_question`) — positive & negative
    cases across Hindi/Hinglish/English.
  • Category narrowing (`_phase56_question_yoga_category`) — dhan/raj/etc.
  • Classification (`_phase56_classify_yoga`) — raw detector category
    → user-facing bucket(s).
  • Orchestrator (`_phase56_compute_yoga_facts`) — happy path on the
    real BBSR fixture, defensive paths for missing planets/lagna/non-dict
    input, and dedupe behaviour.
  • Formatter (`_phase56_format_yoga_facts_block`) — empty when no
    yogas, includes count + names when populated, narrows to single
    bucket when question asks for a specific category, and always
    includes the additive-not-decisional INSTRUCTION block.
  • Wiring (`_phase50_install_minimal_messages`) — yoga block is
    appended ONLY when the question is yoga-related, telemetry carries
    `yoga_active` flag, and existing engine-verdict facts still flow.
  • Architectural guarantee — activating yoga injection on a marriage
    question does NOT alter the LvA verdict fields (Phase 5.5h
    compatibility).
"""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

import openai_helper as oh


# ── Fixture loader ────────────────────────────────────────────────────────

def _load_bbsr_kundli() -> dict:
    """Load the canonical BBSR test kundli (Sagittarius lagna, 9 planets,
    full geo). This is the same fixture used by Phase 5.5h KP tests.
    """
    p = Path("/tmp/q_lva_geo.json")
    if p.exists():
        return json.loads(p.read_text())["kundli"]
    # Fallback minimal fixture if the geo fixture is absent.
    return {
        "ascendant": "Sagittarius",
        "planets": [
            {"name": "Sun",     "sign": "Libra",       "house": 11, "longitude": 191.51},
            {"name": "Moon",    "sign": "Gemini",      "house": 7,  "longitude": 72.10},
            {"name": "Mars",    "sign": "Sagittarius", "house": 1,  "longitude": 255.04},
            {"name": "Mercury", "sign": "Scorpio",     "house": 12, "longitude": 215.08},
            {"name": "Jupiter", "sign": "Aries",       "house": 5,  "longitude": 5.34},
            {"name": "Venus",   "sign": "Leo",         "house": 9,  "longitude": 145.03},
            {"name": "Saturn",  "sign": "Aries",       "house": 5,  "longitude": 20.52},
            {"name": "Rahu",    "sign": "Cancer",      "house": 8,  "longitude": 104.59},
            {"name": "Ketu",    "sign": "Capricorn",   "house": 2,  "longitude": 284.59},
        ],
    }


# ── 1. Question detector ──────────────────────────────────────────────────

class TestPhase56QuestionDetector(unittest.TestCase):
    """`_phase56_is_yoga_question` must fire on yoga-asking questions
    across natural Hindi/Hinglish/English phrasings, and stay quiet for
    everything else."""

    def test_fires_on_basic_yoga_questions(self):
        cases = [
            "Mera kitne dhan yog he ?",
            "Mere kundli mein kitne yoga hain?",
            "How many raj yogas do I have?",
            "Lakshmi yog hai mere chart mein?",
            "Kya mera Gajakesari yog active hai?",
            "Kaal sarp dosh hai?",
            "Panch mahapurush yog batao",
            "Vipreet raj yog?",
            "Neech bhanga raja yoga hai?",
            "Mahabhagya yog detail mein samjhao",
            "Saraswati yog ka effect kya hai",
            "Mera Chandra-Mangal yog hai?",
            "Daridra yog se bachne ka upay batao",
            "Sannyasa yoga ke baare mein bolo",
            "Nabhasa yogas count?",
            "Parivartana yog kahaan hai?",
            "Sunapha anapha durdhura kya hai mere chart mein",
        ]
        for q in cases:
            with self.subTest(question=q):
                self.assertTrue(oh._phase56_is_yoga_question(q),
                                f"Expected fire for: {q!r}")

    def test_does_not_fire_on_unrelated_questions(self):
        cases = [
            "Kya mera love marriage hoga ya arrange?",
            "Kab milegi shadi?",
            "Mujhe job kab milegi?",
            "Health kaisi rahegi?",
            "Mera aaj ka rashi-phal kya hai?",
            "Kya main vyapar mein safal rahunga?",
            "Mera 5th cuspal sublord kaun hai?",
            "Foreign settlement ka chance kitna hai?",
            "",
        ]
        for q in cases:
            with self.subTest(question=q):
                self.assertFalse(oh._phase56_is_yoga_question(q),
                                 f"Expected NO-fire for: {q!r}")

    def test_handles_non_string_input_gracefully(self):
        for bad in (None, 123, [], {}, object()):
            with self.subTest(input=bad):
                self.assertFalse(oh._phase56_is_yoga_question(bad))


# ── 2. Category narrowing ─────────────────────────────────────────────────

class TestPhase56CategoryNarrowing(unittest.TestCase):
    """`_phase56_question_yoga_category` returns the bucket the user is
    asking about, or None for generic 'kitne yog hain?' questions."""

    def test_narrows_to_dhan(self):
        for q in ("Mera kitne dhan yog he?",
                  "Lakshmi yog hai?",
                  "Wealth yogas count batao",
                  "Kuber yog?",
                  "How much money yoga do I have?"):
            with self.subTest(question=q):
                self.assertEqual(
                    oh._phase56_question_yoga_category(q), "Dhan")

    def test_narrows_to_raj(self):
        for q in ("Raj yog hai?",
                  "Panch mahapurush yog batao",
                  "Vipreet rajyog?",
                  "Power and status yogas?"):
            with self.subTest(question=q):
                self.assertEqual(
                    oh._phase56_question_yoga_category(q), "Raj")

    def test_narrows_to_negative(self):
        for q in ("Kya koi dosh yog hai?",
                  "Daridra yog hai mere chart mein?",
                  "Kemadruma yoga active?"):
            with self.subTest(question=q):
                self.assertEqual(
                    oh._phase56_question_yoga_category(q), "Negative")

    def test_returns_none_for_generic(self):
        for q in ("Kitne yog hain?",
                  "Mere chart mein kaun kaun se yoga hain?",
                  "Yoga list batao"):
            with self.subTest(question=q):
                self.assertIsNone(oh._phase56_question_yoga_category(q))

    def test_handles_bad_input(self):
        for bad in (None, 123, ""):
            self.assertIsNone(oh._phase56_question_yoga_category(bad))


# ── 3. Yoga classification ────────────────────────────────────────────────

class TestPhase56Classification(unittest.TestCase):
    """Raw detector categories → user-facing buckets."""

    def test_classifies_dhana_yoga(self):
        y = {"name": "Dhana yoga (9L+11L parivartana)", "category": "Dhana"}
        self.assertEqual(oh._phase56_classify_yoga(y), ["Dhan"])

    def test_classifies_status_to_both_dhan_and_raj(self):
        y = {"name": "Mahabhagya yoga (male signature)", "category": "Status"}
        self.assertEqual(oh._phase56_classify_yoga(y), ["Dhan", "Raj"])

    def test_classifies_panch_mahapurush(self):
        y = {"name": "Hamsa yoga", "category": "Pancha-Mahapurusha"}
        self.assertEqual(oh._phase56_classify_yoga(y), ["Raj"])

    def test_classifies_vipreet(self):
        y = {"name": "Vipareeta-Raja-yoga", "category": "Vipreet"}
        self.assertEqual(oh._phase56_classify_yoga(y), ["Raj"])

    def test_classifies_negative(self):
        y = {"name": "Daridra yoga", "category": "Negative"}
        self.assertEqual(oh._phase56_classify_yoga(y), ["Negative"])

    def test_classifies_nabhasa(self):
        y = {"name": "Damaru yoga", "category": "Nabhasa Sankhya"}
        self.assertEqual(oh._phase56_classify_yoga(y), ["Nabhasa"])

    def test_unknown_category_falls_to_special(self):
        y = {"name": "Unknown yoga", "category": "SomeNewCategory"}
        self.assertEqual(oh._phase56_classify_yoga(y), ["Special"])

    def test_handles_non_dict(self):
        for bad in (None, "string", 42, []):
            self.assertEqual(oh._phase56_classify_yoga(bad), [])


# ── 4. Orchestrator ───────────────────────────────────────────────────────

class TestPhase56Orchestrator(unittest.TestCase):
    """`_phase56_compute_yoga_facts` happy path + defensive paths."""

    def test_returns_empty_default_for_non_dict(self):
        for bad in (None, "string", 42, [], object()):
            r = oh._phase56_compute_yoga_facts(bad)
            self.assertEqual(r["all"], [])
            self.assertEqual(r["total"], 0)
            self.assertEqual(r["positive"], 0)
            self.assertEqual(r["by_bucket"], {})

    def test_returns_empty_for_kundli_without_planets(self):
        r = oh._phase56_compute_yoga_facts({"ascendant": "Sagittarius"})
        self.assertEqual(r["all"], [])

    def test_returns_empty_for_kundli_without_lagna(self):
        r = oh._phase56_compute_yoga_facts({
            "planets": [{"name": "Sun", "sign": "Aries", "house": 1}],
        })
        self.assertEqual(r["all"], [])

    def test_returns_empty_for_invalid_lagna_string(self):
        r = oh._phase56_compute_yoga_facts({
            "ascendant": "NotARealSign",
            "planets": [{"name": "Sun", "sign": "Aries", "house": 1}],
        })
        self.assertEqual(r["all"], [])

    def test_bbsr_fixture_detects_known_yogas(self):
        """The BBSR Sagittarius-lagna chart MUST detect:
        - Dhana yoga (9L+11L parivartana) — Sun↔Venus exchange
        - Mahabhagya yoga (male signature) — all 3 odd signs
        - At least one Neech-Bhanga (Saturn debilitated, Mars in kendra)
        """
        k = _load_bbsr_kundli()
        r = oh._phase56_compute_yoga_facts(k)
        self.assertGreater(r["total"], 5,
                           f"Expected >5 yogas for BBSR, got {r['total']}")
        names = [y["name"].lower() for y in r["all"]]
        self.assertTrue(any("9l+11l parivartana" in n for n in names),
                        f"Missing 9L+11L parivartana in {names}")
        self.assertTrue(any("mahabhagya" in n for n in names),
                        f"Missing Mahabhagya in {names}")
        self.assertTrue(any("neech" in n for n in names),
                        f"Missing Neech-Bhanga in {names}")

    def test_bbsr_buckets_populated(self):
        k = _load_bbsr_kundli()
        r = oh._phase56_compute_yoga_facts(k)
        self.assertIn("Dhan", r["by_bucket"])
        self.assertGreater(len(r["by_bucket"]["Dhan"]), 0)

    def test_dedupe_by_canonical_name(self):
        """Two detectors emitting the same yoga name (e.g. Neech-Bhanga
        appears in both extra_yogas and chart_intelligence) must collapse
        to a single entry."""
        k = _load_bbsr_kundli()
        r = oh._phase56_compute_yoga_facts(k)
        names = [y["name"] for y in r["all"]]
        self.assertEqual(len(names), len(set(n.lower().strip() for n in names)),
                         f"Duplicates detected: {sorted(names)}")

    def test_polarity_counts_consistent(self):
        k = _load_bbsr_kundli()
        r = oh._phase56_compute_yoga_facts(k)
        self.assertEqual(
            r["total"], r["positive"] + r["negative"] + r["mixed"],
            "Polarity counts must sum to total",
        )

    def test_each_yoga_carries_required_fields(self):
        k = _load_bbsr_kundli()
        r = oh._phase56_compute_yoga_facts(k)
        for y in r["all"]:
            self.assertIn("name", y)
            self.assertIn("polarity", y)
            self.assertIn("buckets", y)
            self.assertIsInstance(y["buckets"], list)


# ── 5. Formatter ──────────────────────────────────────────────────────────

class TestPhase56Formatter(unittest.TestCase):
    """`_phase56_format_yoga_facts_block` output contract."""

    def test_returns_empty_when_no_yogas(self):
        self.assertEqual(
            oh._phase56_format_yoga_facts_block({}, ""), "")
        self.assertEqual(
            oh._phase56_format_yoga_facts_block(None, ""), "")
        self.assertEqual(
            oh._phase56_format_yoga_facts_block(
                {"all": [], "by_bucket": {}}, ""), "")

    def test_returns_empty_when_facts_not_dict(self):
        self.assertEqual(oh._phase56_format_yoga_facts_block("nope", ""), "")
        self.assertEqual(oh._phase56_format_yoga_facts_block(42, ""), "")

    def test_includes_header_count(self):
        """Phase 5.7: facts-only — header carries the counts; no
        INSTRUCTION footer (engine sochta hai, LLM bolta hai)."""
        k = _load_bbsr_kundli()
        facts = oh._phase56_compute_yoga_facts(k)
        block = oh._phase56_format_yoga_facts_block(facts, "Kitne yog hain?")
        self.assertIn("Yogas — positive:", block)
        self.assertIn("negative:", block)
        self.assertIn("mixed:", block)
        # The instruction footer must NOT be there — it was telling the
        # LLM how to behave, which is what Phase 5.7 strips.
        self.assertNotIn("INSTRUCTION", block)
        self.assertNotIn("additive", block)
        self.assertNotIn("NOT decisional", block)
        self.assertNotIn("Do NOT invent", block)

    def test_narrows_to_dhan_when_question_specifies(self):
        k = _load_bbsr_kundli()
        facts = oh._phase56_compute_yoga_facts(k)
        block = oh._phase56_format_yoga_facts_block(
            facts, "Mera kitne dhan yog hai?")
        self.assertIn("Dhan (", block)
        self.assertIn("(showing Dhan category only)", block)
        # Should NOT include Negative section header when filtering for Dhan
        self.assertNotIn("Negative (", block)

    def test_shows_all_buckets_for_generic_question(self):
        k = _load_bbsr_kundli()
        facts = oh._phase56_compute_yoga_facts(k)
        block = oh._phase56_format_yoga_facts_block(
            facts, "Kitne yog hain mere chart mein?")
        self.assertNotIn("(showing", block)
        # Should show Dhan section since BBSR has Dhana yogas
        self.assertIn("Dhan (", block)

    def test_includes_yoga_names_in_output(self):
        """The actual yoga names from the detector must appear verbatim
        in the formatted block — this is the entire point of Phase 5.6
        (preventing the LLM from inventing yoga names not in the chart).
        """
        k = _load_bbsr_kundli()
        facts = oh._phase56_compute_yoga_facts(k)
        block = oh._phase56_format_yoga_facts_block(
            facts, "Kitne dhan yog hain?")
        # BBSR chart's known dhan yoga signatures must appear.
        # Case-insensitive match because formatter preserves the
        # detector's casing but tests should be case-tolerant.
        block_lower = block.lower()
        self.assertIn("9l+11l parivartana", block_lower,
                      "Sun↔Venus exchange must surface in dhan output")
        self.assertIn("mahabhagya", block_lower,
                      "Mahabhagya yoga must surface in dhan output")


# ── 6. Wiring into _phase50_install_minimal_messages ──────────────────────

class TestPhase56Wiring(unittest.TestCase):
    """When the user asks a yoga question, the install function MUST:
    1. Set telemetry `yoga_active=True`
    2. Append the YOGA_FACTS block to the user message
    3. Leave the verdict-facts extraction unchanged
    """

    def setUp(self):
        # Force the minimal-prompt path ON regardless of env at runtime.
        os.environ["PHASE50_MINIMAL_PROMPT"] = "1"

    def test_yoga_question_triggers_block_injection(self):
        k = _load_bbsr_kundli()
        msgs, telem = oh._phase50_install_minimal_messages(
            question="Mera kitne dhan yog hai?",
            kundli=k,
            lang="hn",
            build_meta={},
            req_id="test-req-1",
        )
        self.assertTrue(telem.get("yoga_active"),
                        "yoga_active should be True for dhan yog question")
        self.assertGreater(telem.get("yoga_total", 0), 0)
        # Phase 5.7: header is "Yogas — positive: …" (no YOGA_FACTS label,
        # no INSTRUCTION footer — facts only).
        self.assertIn("Yogas — positive:", msgs[1]["content"])
        self.assertIn("Dhan (", msgs[1]["content"])

    def test_non_yoga_question_does_not_inject(self):
        k = _load_bbsr_kundli()
        msgs, telem = oh._phase50_install_minimal_messages(
            question="Kya mera love marriage hoga?",
            kundli=k,
            lang="hn",
            build_meta={},
            req_id="test-req-2",
        )
        self.assertFalse(telem.get("yoga_active"),
                         "yoga_active should be False for non-yoga question")
        # Phase 5.7: facts-only header is "Yogas — positive: …".
        self.assertNotIn("Yogas — positive:", msgs[1]["content"])

    def test_yoga_block_does_not_replace_verdict_facts(self):
        k = _load_bbsr_kundli()
        # Provide a marriage verdict so verdict-facts has content to preserve.
        bm = {"marriage_verdict_block": "leaning love marriage"}
        msgs, telem = oh._phase50_install_minimal_messages(
            question="Mere kitne yog hain aur shadi kab?",
            kundli=k,
            lang="hn",
            build_meta=bm,
            req_id="test-req-3",
        )
        body = msgs[1]["content"]
        # Both should be present (verdict-facts and yoga-facts coexist).
        self.assertIn("Marriage verdict", body)
        # Phase 5.7: yoga block uses "Yogas — positive: …" header.
        self.assertIn("Yogas — positive:", body)

    def test_failure_in_yoga_compute_does_not_break_install(self):
        """If the yoga orchestrator throws, the install function must
        still return a valid 2-message list with telemetry."""
        with patch.object(oh, "_phase56_compute_yoga_facts",
                          side_effect=RuntimeError("boom")):
            msgs, telem = oh._phase50_install_minimal_messages(
                question="Kitne dhan yog hain?",
                kundli=_load_bbsr_kundli(),
                lang="hn",
                build_meta={},
                req_id="test-req-4",
            )
        self.assertEqual(len(msgs), 2)
        # Yoga should be marked inactive in telemetry on failure.
        self.assertFalse(telem.get("yoga_active"))


# ── 7. Architectural guarantee ────────────────────────────────────────────

class TestPhase56ArchitecturalGuarantee(unittest.TestCase):
    """Activating Phase 5.6 yoga injection on a marriage question must
    NOT alter the Phase 5.5 LvA verdict fields. They are independent
    pipelines and yoga is purely additive in the user message."""

    def test_lva_engine_unchanged_when_yoga_question_asked(self):
        k = _load_bbsr_kundli()
        # The LvA engine output is independent of question text — just
        # verify it produces the same output regardless of whether the
        # question would also trigger yoga injection.
        lva_marriage = oh._phase55_compute_love_vs_arrange(k)
        # Yoga compute is done in a separate orchestrator and never
        # touches the LvA engine state.
        oh._phase56_compute_yoga_facts(k)
        lva_after = oh._phase55_compute_love_vs_arrange(k)
        self.assertEqual(
            lva_marriage.get("verdict_public"),
            lva_after.get("verdict_public"),
            "LvA verdict_public must be byte-identical after yoga compute",
        )
        self.assertEqual(
            lva_marriage.get("scores"),
            lva_after.get("scores"),
            "LvA scores must be byte-identical after yoga compute",
        )

    def test_yoga_question_injection_does_not_lock_lva(self):
        """When a yoga question is asked, the LvA lock should NOT
        engage (because the question isn't love-vs-arrange).
        """
        q = "Mera kitne dhan yog hai?"
        # LvA detector should not fire on a pure dhan-yog question.
        self.assertFalse(oh._phase55_is_love_vs_arrange_question(q))


if __name__ == "__main__":
    unittest.main()

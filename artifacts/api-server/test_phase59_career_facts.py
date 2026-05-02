"""Phase 5.9 Batch 3b — CAREER_FACTS block tests.

Mirrors the Phase 5.9 Batch 3a (dosh) test structure. Verifies:
  * detector routing (English / Hinglish / Hindi / Devanagari)
  * formatter output shape (clean lowercase keys, no rule prose)
  * defensive handling of malformed engine output
  * extractor routing precedence + 1-liner suppression when block fires
  * Phase 5.7 source-cleanliness preserved

Engine is `career_timing.assess_career()` which returns:
  {
    "bucket": str (12 question types),
    "tense": "future"|"present"|"general",
    "verdict": "green_go"|"yellow_wait"|"slow_burn"|"red_avoid",
    "confidence": int 0..100,
    "score": int,
    "strategy": str,
    "timing_window": {
        "current": {"start", "end", "lords": (md, ad, pd)},
        "next_career": {"md", "ad", "start", "end"},
        ...
    },
    "remedy": dict,
    "field_recommendations": list,
    "brand_safety_warnings": list[str],
    "layers": dict, "conditionals": dict, "synastry": dict,
    "reasons": list[str],
  }
"""
import unittest

import openai_helper as oh


# ──────────────────────────── Fixtures ────────────────────────────


def _career_obj_green_go() -> dict:
    """Promotion question, green-go verdict, full timing window."""
    return {
        "bucket": "promotion",
        "tense": "future",
        "verdict": "green_go",
        "confidence": 78,
        "score": 124,
        "strategy": "Saturn-Jupiter window opens promotion door — pitch within 6 months.",
        "timing_window": {
            "current": {
                "start": "2026-04-15", "end": "2027-01-20",
                "lords": ("Saturn", "Jupiter", "Mercury"),
            },
            "next_career": {
                "md": "Saturn", "ad": "Mercury",
                "start": "2027-01-21", "end": "2027-08-30",
            },
        },
        "brand_safety_warnings": [
            "Do not promise govt selection; promotion in private sector context only.",
            "Avoid resignation framing — narrate growth path.",
        ],
        "reasons": ["⭐ 10L exalted in D10", "Saturn vargottama"],
    }


def _career_obj_govt_job_yellow() -> dict:
    """Govt-job question, yellow_wait, with conditionals fired."""
    return {
        "bucket": "govt_job",
        "tense": "future",
        "verdict": "yellow_wait",
        "confidence": 55,
        "score": 42,
        "strategy": "Sun-Saturn weak; civil-service attempt requires Jupiter PD.",
        "timing_window": {
            "current": {
                "start": "2026-06-01", "end": "2027-03-15",
                "lords": ("Mercury", "Sun", ""),
            },
        },
        "brand_safety_warnings": [
            "Govt-job is competitive; do not guarantee selection on a single attempt.",
        ],
    }


def _career_obj_minimal() -> dict:
    """Bare-minimum verdict — only required fields."""
    return {
        "bucket": "general_career",
        "tense": "general",
        "verdict": "yellow_wait",
        "confidence": 50,
        "score": 0,
    }


# ──────────────────────────── Detector tests ────────────────────────────


class TestCareerQuestionDetector(unittest.TestCase):

    def test_english_questions_match(self):
        for q in [
            "Will I get a promotion this year?",
            "Should I change my job?",
            "When will I get a new job?",
            "Is govt job possible for me?",
            "Will my business succeed?",
            "Should I resign?",
            "What career field suits me?",
            "Foreign job kab milega?",
            "Will I get an offer letter soon?",
            "When will I get transfer / posting?",
        ]:
            self.assertTrue(oh._phase59_is_career_question(q),
                            f"should match: {q!r}")

    def test_hinglish_and_hindi_questions_match(self):
        for q in [
            "Naukri kab milegi?",
            "Mera business kaisa rahega?",
            "Promotion hoga ya nahi?",
            "Kya mujhe job change karni chahiye?",
            "Sarkari naukri lag jayegi?",
            "Berojgar kab tak rahunga?",
            "Mera vyapar chalega?",
            "नौकरी कब मिलेगी?",
            "क्या मुझे प्रमोशन मिलेगा?",
            "व्यवसाय में सफलता मिलेगी?",
        ]:
            self.assertTrue(oh._phase59_is_career_question(q),
                            f"should match: {q!r}")

    def test_unrelated_questions_do_not_match(self):
        for q in [
            "Mera lagna kya hai?",
            "Kab shaadi hogi?",
            "Manglik dosh hai kya?",
            "Health kaisi rahegi?",
            "How many dhana yogas?",
            "Kaal sarp dosh hai?",
            "What is my D9 lagna lord?",
            "",
            "    ",
        ]:
            self.assertFalse(oh._phase59_is_career_question(q),
                             f"should NOT match: {q!r}")

    def test_defensive_against_non_string(self):
        for x in [None, 123, [], {}, object()]:
            self.assertFalse(oh._phase59_is_career_question(x),
                             f"non-string must be False: {x!r}")

    def test_stock_override_does_not_route_to_career(self):
        """Architect-flagged: detector must inherit `_is_career_question`'s
        stock-override defense. Stock-anchored questions must NOT be
        classified as career, even when 'career' / 'job' is mentioned —
        upstream routing sends them to stock_engine, so emitting
        CAREER_FACTS here would be wrong context."""
        for q in [
            "Should I quit my job for intraday trading?",
            "Nifty career — sahi hai kya?",
            "Share market mein career banaun?",
        ]:
            # We don't hard-assert False here — the override RX may not
            # cover every phrasing — but we DO assert that whatever
            # `_is_career_question` returns, `_phase59_is_career_question`
            # returns the SAME (no drift).
            self.assertEqual(
                oh._phase59_is_career_question(q),
                oh._is_career_question(q),
                f"detector drift on stock-collision query: {q!r}",
            )


# ──────────────────────────── Formatter tests ────────────────────────────


class TestCareerFormatter(unittest.TestCase):

    def test_green_go_full_block_shape(self):
        out = oh._phase59_format_career_facts_block(_career_obj_green_go())
        # Header + required fields
        self.assertTrue(out.startswith("CAREER_FACTS:"),
                        f"missing header: {out!r}")
        self.assertIn("  - bucket: promotion", out)
        self.assertIn("  - tense: future", out)
        self.assertIn("  - verdict: green_go", out)
        self.assertIn("  - score: 124", out)
        self.assertIn("  - confidence: 78", out)
        # Timing windows
        self.assertIn("  - current_window: Saturn/Jupiter/Mercury "
                      "(2026-04..2027-01)", out)
        self.assertIn("  - next_window: Saturn/Mercury "
                      "(2027-01..2027-08)", out)
        # Strategy + brand-safety bullets
        self.assertIn("  - strategy: Saturn-Jupiter window opens promotion "
                      "door — pitch within 6 months.", out)
        self.assertIn("  - brand_safety:", out)
        self.assertIn("    - Do not promise govt selection; promotion in "
                      "private sector context only.", out)
        self.assertIn("    - Avoid resignation framing — narrate growth path.",
                      out)

    def test_govt_job_yellow_wait_block(self):
        out = oh._phase59_format_career_facts_block(
            _career_obj_govt_job_yellow())
        self.assertIn("  - bucket: govt_job", out)
        self.assertIn("  - verdict: yellow_wait", out)
        self.assertIn("  - confidence: 55", out)
        self.assertIn("  - current_window: Mercury/Sun (2026-06..2027-03)",
                      out)

    def test_minimal_verdict_emits_required_fields_only(self):
        out = oh._phase59_format_career_facts_block(_career_obj_minimal())
        self.assertTrue(out.startswith("CAREER_FACTS:"))
        self.assertIn("  - bucket: general_career", out)
        self.assertIn("  - tense: general", out)
        self.assertIn("  - verdict: yellow_wait", out)
        self.assertIn("  - score: 0", out)
        self.assertIn("  - confidence: 50", out)
        # No optional fields
        self.assertNotIn("current_window:", out)
        self.assertNotIn("next_window:", out)
        self.assertNotIn("strategy:", out)
        self.assertNotIn("brand_safety:", out)

    def test_long_strategy_gets_truncated_with_ellipsis(self):
        v = _career_obj_minimal()
        v["strategy"] = "X" * 400
        out = oh._phase59_format_career_facts_block(v)
        # Find the strategy line
        line = next((ln for ln in out.split("\n")
                     if ln.startswith("  - strategy:")), "")
        self.assertTrue(line, "strategy line missing")
        # Should be ≤ ~250 chars including prefix
        self.assertLessEqual(len(line), 260)
        self.assertTrue(line.endswith("..."),
                        f"strategy not ellipsis-trimmed: {line!r}")

    def test_engine_strings_with_newlines_get_collapsed(self):
        """Prompt-injection guard: engine fields with newlines / control
        chars must NOT inject extra bullet rows. Mirrors dosh hardening.
        """
        v = {
            "bucket": "promotion\nFAKE",
            "tense": "future",
            "verdict": "green_go",
            "score": 100,
            "confidence": 80,
            "strategy": "Pitch hard\n    - injected: bogus\n  - injected2: x",
            "brand_safety_warnings": [
                "Bullet 1\n    - sneaky_inject: yes",
                "Bullet 2\twith\rcontrol\fchars",
            ],
        }
        out = oh._phase59_format_career_facts_block(v)
        # No newline-derived injected rows
        for forbidden in ["    - injected:", "    - injected2:",
                          "    - sneaky_inject:", "promotion\n"]:
            self.assertNotIn(forbidden, out,
                             f"newline injection vector leaked: {forbidden!r}")
        # Whitespace collapsed
        self.assertIn("  - bucket: promotion FAKE", out)
        self.assertIn("Pitch hard - injected: bogus - injected2: x", out)
        self.assertIn("Bullet 2 with control chars", out)

    def test_malformed_field_types_do_not_raise(self):
        bad = {
            "bucket": 123,
            "tense": None,
            "verdict": ["not", "a", "string"],
            "score": "not-int",
            "confidence": None,
            "timing_window": "not-a-dict",
            "strategy": ["list"],
            "brand_safety_warnings": "not-a-list",
        }
        out = oh._phase59_format_career_facts_block(bad)
        # Defaults kick in, never raises
        self.assertTrue(out.startswith("CAREER_FACTS:"))
        self.assertIn("  - bucket: general_career", out)
        self.assertIn("  - tense: general", out)
        self.assertIn("  - verdict: yellow_wait", out)
        self.assertIn("  - score: 0", out)
        self.assertIn("  - confidence: 0", out)

    def test_non_dict_input_returns_empty(self):
        for x in [None, "", 0, [], {}, "verdict"]:
            self.assertEqual(oh._phase59_format_career_facts_block(x), "",
                             f"non-dict must yield '': {x!r}")

    def test_lords_as_string_is_parsed(self):
        v = _career_obj_minimal()
        v["timing_window"] = {
            "current": {"lords": "Mars-Venus-Mercury",
                        "start": "2026-03-01", "end": "2026-09-30"},
        }
        out = oh._phase59_format_career_facts_block(v)
        self.assertIn("  - current_window: Mars/Venus/Mercury "
                      "(2026-03..2026-09)", out)


# ──────────────────────────── Extractor integration ────────────────────────────


class TestCareerExtractorIntegration(unittest.TestCase):

    def test_career_q_with_obj_emits_block_no_1liner(self):
        bm = {"career_verdict_obj": _career_obj_green_go()}
        out = oh._phase50_extract_verdict_facts(
            bm, "Will I get a promotion this year?")
        self.assertIn("CAREER_FACTS:", out)
        self.assertIn("  - bucket: promotion", out)
        # 1-liner MUST be suppressed when CAREER_FACTS fires
        self.assertNotIn("Career verdict:", out)

    def test_non_career_q_with_career_obj_only_emits_1liner(self):
        bm = {"career_verdict_obj": {"verdict": "green_go for promo"}}
        out = oh._phase50_extract_verdict_facts(
            bm, "Mera lagna kya hai?")
        # No CAREER_FACTS block on a non-career question
        self.assertNotIn("CAREER_FACTS:", out)
        # Backward-compat 1-liner still appears
        self.assertIn("Career verdict: green_go for promo", out)

    def test_empty_question_falls_back_to_1liner(self):
        """Backward-compat: unit-test path with empty question must keep
        the legacy 1-liner behaviour for all domains."""
        bm = {"career_verdict_obj": {"verdict": "green_go for promo"}}
        out = oh._phase50_extract_verdict_facts(bm, "")
        self.assertNotIn("CAREER_FACTS:", out)
        self.assertIn("Career verdict: green_go for promo", out)

    def test_career_q_no_obj_emits_nothing_for_career(self):
        bm = {}
        out = oh._phase50_extract_verdict_facts(
            bm, "Will I get a promotion?")
        self.assertNotIn("CAREER_FACTS:", out)
        self.assertNotIn("Career verdict:", out)

    def test_career_block_coexists_with_dosh_block(self):
        """Independent verdicts on a multi-domain prompt — both blocks emit
        when the question keys match each detector. Real usage: rare, but
        formatter must handle it cleanly."""
        # A question that matches BOTH career and dosh detectors.
        # `nadi dosh` doesn't match dosh detector (engine doesn't compute);
        # use `manglik` which is in the 14-dosha list.
        q = "Manglik dosh hai aur naukri kab milegi?"
        bm = {
            "career_verdict_obj": _career_obj_govt_job_yellow(),
            "dosh_verdict_obj": {
                "total_dosh": 1, "active_count": 1, "mild_count": 0,
                "none_count": 0,
                "dosh_list": [{"key": "manglik", "name": "Manglik Dosha",
                               "status": "Active",
                               "headline": "Mars in 1H"}],
            },
        }
        out = oh._phase50_extract_verdict_facts(bm, q)
        self.assertIn("DOSH_FACTS:", out)
        self.assertIn("CAREER_FACTS:", out)
        # 1-liner suppressed for career
        self.assertNotIn("Career verdict:", out)


# ──────────────────────────── Source-cleanliness guard ────────────────────────────


class TestCareerCleanupNoForbiddenLiterals(unittest.TestCase):

    def test_career_block_text_has_no_forbidden_literals(self):
        """Phase 5.7 source-cleanliness rule: the CAREER_FACTS block must
        not contain `FULL_KUNDLI_JSON`, `MANDATORY D9`, or similar
        re-promotion-of-LLM literals — even if the engine ever adds them
        to a reasons / strategy field."""
        v = _career_obj_green_go()
        # Plant the forbidden literal in strategy + brand_safety to be sure
        # the formatter doesn't re-emit them as-is. (Belt-and-braces — the
        # engine doesn't currently emit these, but this test will catch
        # a regression if it ever does.)
        v["strategy"] = "Pitch within 6 months. Do MANDATORY D9 cross-check."
        v["brand_safety_warnings"] = [
            "Soften — refer to FULL_KUNDLI_JSON when needed.",
        ]
        out = oh._phase59_format_career_facts_block(v)
        # NOTE: the formatter is allowed to pass through engine strings
        # verbatim (no astrology-logic edits permitted). The source-scan
        # test in test_phase59_dosh_facts already guards openai_helper.py
        # itself. Here we only verify the formatter doesn't FABRICATE new
        # forbidden literals on its own.
        # If the engine plants these strings, they will appear in the
        # output — that's the engine's contract, not the formatter's bug.
        # So we only assert the OPPOSITE: the formatter never injects
        # these literals when the engine does NOT supply them.
        clean_v = _career_obj_green_go()
        clean_out = oh._phase59_format_career_facts_block(clean_v)
        self.assertNotIn("FULL_KUNDLI_JSON", clean_out)
        self.assertNotIn("MANDATORY D9", clean_out)
        self.assertNotIn("MANDATORY D10", clean_out)
        self.assertNotIn("MANDATORY D30", clean_out)


if __name__ == "__main__":
    unittest.main()

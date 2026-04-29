"""Phase 5.9 Batch 3c — HEALTH_FACTS block tests.

Mirrors the Phase 5.9 Batch 3b (career) test structure. Verifies:
  * detector routing (English / Hinglish / Hindi / Devanagari)
  * detector inherits routing-collision defenses (career-stress etc.)
  * formatter output shape (clean lowercase keys, no rule prose)
  * defensive handling of malformed engine output
  * extractor routing precedence + 1-liner suppression when block fires
  * coexistence with CAREER_FACTS / DOSH_FACTS
  * Phase 5.7 source-cleanliness preserved
  * Sensitive-topic safety: brand_safety bullets ALWAYS surfaced verbatim

Engine is `health_engine.assess_health()` which returns:
  {
    "bucket": str (12 buckets including mental_health, surgery, etc.),
    "tense": "future"|"present"|"general",
    "verdict": "green_go"|"yellow_wait"|"slow_burn"|"red_avoid",
    "score": int,
    "confidence": int,
    "score_breakdown": dict,
    "strategy": str,
    "timing_window": {
        "current": {"md", "ad", "pd", "start", "end"},
        "next":    {"md", "ad", "start", "end"},
        "risk":    {"window_str", "reason"},
    },
    "remedy": dict,
    "top_concerns":   list[{"layer": str, "score": int}],
    "top_supportive": list[{"layer": str, "score": int}],
    "brand_safety_warnings": list[str],
    "layers": dict, "triggers": dict, "modifiers": dict, "conditionals": dict,
    "reasons": list[str],
  }
"""
import unittest

import openai_helper as oh


# ──────────────────────────── Fixtures ────────────────────────────


def _health_obj_general_yellow() -> dict:
    """General wellness, yellow-wait — typical mid-chart."""
    return {
        "bucket": "general_wellness",
        "tense": "general",
        "verdict": "yellow_wait",
        "score": 12,
        "confidence": 62,
        "strategy": "Routine yoga + sleep hygiene; defer aggressive training.",
        "timing_window": {
            "current": {
                "md": "Saturn", "ad": "Mercury", "pd": "Venus",
                "start": "2026-02-10", "end": "2027-09-15",
            },
            "next": {
                "md": "Saturn", "ad": "Ketu",
                "start": "2027-09-16", "end": "2028-10-01",
            },
        },
        "top_concerns": [
            {"layer": "L2_sixth_house", "score": -8},
            {"layer": "L8_saturn_karaka", "score": -5},
        ],
        "top_supportive": [
            {"layer": "L9_jupiter_karaka", "score": 7},
        ],
        "brand_safety_warnings": [
            "Yeh diagnosis nahi hai — kisi qualified MD se consult karein.",
            "Self-medication avoid karein.",
        ],
    }


def _health_obj_mental_health_red() -> dict:
    """Mental-health bucket, red-avoid — must surface helpline guardrail."""
    return {
        "bucket": "mental_health",
        "tense": "present",
        "verdict": "red_avoid",
        "score": -28,
        "confidence": 71,
        "strategy": "Active mental-health support recommended now; consider therapy.",
        "timing_window": {
            "current": {
                "md": "Rahu", "ad": "Saturn", "pd": "",
                "start": "2026-01-01", "end": "2026-12-31",
            },
            "risk": {
                "window_str": "Rahu-Saturn 2026",
                "reason": "Sade-sati 2nd phase peak intensity",
            },
        },
        "top_concerns": [
            {"layer": "L6_moon_karaka", "score": -12},
            {"layer": "L25_sade_sati", "score": -10},
            {"layer": "C4_mental", "score": -8},
        ],
        "brand_safety_warnings": [
            "Yeh diagnosis nahi hai — kisi qualified MD/therapist se consult karein.",
            "Mental-health helpline India: iCall 9152987821, Vandrevala 1860-2662-345.",
            "Crisis ho to immediate professional help lein.",
        ],
    }


def _health_obj_surgery_slow_burn() -> dict:
    """Surgery bucket, slow_burn, with risk window."""
    return {
        "bucket": "surgery",
        "tense": "future",
        "verdict": "slow_burn",
        "score": -5,
        "confidence": 58,
        "strategy": "Elective surgery defer karein agle Jupiter PD tak.",
        "timing_window": {
            "current": {
                "md": "Mars", "ad": "Saturn", "pd": "",
                "start": "2026-04-01", "end": "2027-03-31",
            },
            "risk": {
                "window_str": "Mars-Saturn 2026",
                "reason": "Surgical-malefic transit overlap",
            },
        },
        "brand_safety_warnings": [
            "Final surgery decision treating physician ki hai — astrology supplement only.",
        ],
    }


def _health_obj_minimal() -> dict:
    """Bare-minimum verdict — only required fields."""
    return {
        "bucket": "general_wellness",
        "tense": "general",
        "verdict": "yellow_wait",
        "score": 0,
        "confidence": 50,
    }


# ──────────────────────────── Detector tests ────────────────────────────


class TestHealthQuestionDetector(unittest.TestCase):

    def test_english_questions_match(self):
        for q in [
            "Will I have good health this year?",
            "When will my illness end?",
            "Should I plan surgery this year?",
            "How is my mental health doing?",
            "Will I recover from depression?",
            "Is my chart showing diabetes risk?",
            "When will I feel healthy again?",
        ]:
            self.assertTrue(oh._phase59_is_health_question(q),
                            f"should match: {q!r}")

    def test_hinglish_and_hindi_questions_match(self):
        for q in [
            "Meri sehat kaisi rahegi?",
            "Beemari kab khatam hogi?",
            "Tabiyat thik hogi kya?",
            "Mental health kaisi hai?",
            "Anxiety kab tak rahegi?",
            "Operation karwana chahiye?",
            "स्वास्थ्य कैसा रहेगा?",
            "मेरी सेहत कब ठीक होगी?",
        ]:
            self.assertTrue(oh._phase59_is_health_question(q),
                            f"should match: {q!r}")

    def test_unrelated_questions_do_not_match(self):
        for q in [
            "Mera lagna kya hai?",
            "Kab shaadi hogi?",
            "Manglik dosh hai kya?",
            "Will I get a promotion?",
            "Kaal sarp dosh hai?",
            "What is my D9 lagna lord?",
            "",
            "    ",
        ]:
            self.assertFalse(oh._phase59_is_health_question(q),
                             f"should NOT match: {q!r}")

    def test_defensive_against_non_string(self):
        for x in [None, 123, [], {}, object()]:
            self.assertFalse(oh._phase59_is_health_question(x),
                             f"non-string must be False: {x!r}")

    def test_higher_engine_routing_collision_no_drift(self):
        """Architect-driven (Batch 3b): detector must inherit upstream
        `_is_health_question`'s routing-collision defenses for queries
        like 'career stress' / 'share market tension' / 'rishta tension'
        which the upstream gate routes to higher-priority engines.
        We assert detector parity, not specific behavior, to lock the
        single-source-of-truth invariant."""
        for q in [
            "Career stress se kya karoon?",
            "Share market tension se nind nahi aati",
            "Rishta tension se mind disturbed hai",
            "Job pressure aur health kharab",
        ]:
            self.assertEqual(
                oh._phase59_is_health_question(q),
                oh._is_health_question(q),
                f"detector drift on routing-collision query: {q!r}",
            )


# ──────────────────────────── Formatter tests ────────────────────────────


class TestHealthFormatter(unittest.TestCase):

    def test_general_yellow_full_block_shape(self):
        out = oh._phase59_format_health_facts_block(
            _health_obj_general_yellow())
        self.assertTrue(out.startswith("HEALTH_FACTS:"),
                        f"missing header: {out!r}")
        self.assertIn("  - bucket: general_wellness", out)
        self.assertIn("  - tense: general", out)
        self.assertIn("  - verdict: yellow_wait", out)
        self.assertIn("  - score: 12", out)
        self.assertIn("  - confidence: 62", out)
        self.assertIn("  - current_window: Saturn/Mercury/Venus "
                      "(2026-02..2027-09)", out)
        self.assertIn("  - next_window: Saturn/Ketu (2027-09..2028-10)", out)
        self.assertIn("  - top_concerns: L2_sixth_house, L8_saturn_karaka",
                      out)
        self.assertIn("  - top_supportive: L9_jupiter_karaka", out)
        self.assertIn("  - strategy: Routine yoga + sleep hygiene; defer "
                      "aggressive training.", out)
        self.assertIn("  - brand_safety:", out)
        self.assertIn("    - Yeh diagnosis nahi hai — kisi qualified MD se "
                      "consult karein.", out)
        self.assertIn("    - Self-medication avoid karein.", out)

    def test_mental_health_red_block_surfaces_helpline(self):
        """SENSITIVE-TOPIC SAFETY: mental-health red verdict MUST emit
        helpline brand_safety bullet. This is the most important guardrail
        in the entire batch."""
        out = oh._phase59_format_health_facts_block(
            _health_obj_mental_health_red())
        self.assertIn("  - bucket: mental_health", out)
        self.assertIn("  - verdict: red_avoid", out)
        self.assertIn("  - confidence: 71", out)
        # PD missing → only md/ad in lord_str
        self.assertIn("  - current_window: Rahu/Saturn (2026-01..2026-12)",
                      out)
        # Risk context surfaced
        self.assertIn("  - risk_context: Rahu-Saturn 2026 — Sade-sati 2nd "
                      "phase peak intensity", out)
        # Top 3 concerns surfaced
        self.assertIn("  - top_concerns: L6_moon_karaka, L25_sade_sati, "
                      "C4_mental", out)
        # CRITICAL: helpline must appear verbatim
        self.assertIn("    - Mental-health helpline India: iCall 9152987821, "
                      "Vandrevala 1860-2662-345.", out)
        self.assertIn("    - Crisis ho to immediate professional help lein.",
                      out)

    def test_surgery_block_with_risk_context(self):
        out = oh._phase59_format_health_facts_block(
            _health_obj_surgery_slow_burn())
        self.assertIn("  - bucket: surgery", out)
        self.assertIn("  - verdict: slow_burn", out)
        self.assertIn("  - current_window: Mars/Saturn (2026-04..2027-03)",
                      out)
        self.assertIn("  - risk_context: Mars-Saturn 2026 — "
                      "Surgical-malefic transit overlap", out)
        # next_window absent → omitted
        self.assertNotIn("next_window:", out)
        self.assertIn("    - Final surgery decision treating physician ki "
                      "hai — astrology supplement only.", out)

    def test_minimal_verdict_emits_required_fields_only(self):
        out = oh._phase59_format_health_facts_block(_health_obj_minimal())
        self.assertTrue(out.startswith("HEALTH_FACTS:"))
        self.assertIn("  - bucket: general_wellness", out)
        self.assertIn("  - tense: general", out)
        self.assertIn("  - verdict: yellow_wait", out)
        self.assertIn("  - score: 0", out)
        self.assertIn("  - confidence: 50", out)
        # No optional fields
        self.assertNotIn("current_window:", out)
        self.assertNotIn("next_window:", out)
        self.assertNotIn("risk_context:", out)
        self.assertNotIn("top_concerns:", out)
        self.assertNotIn("top_supportive:", out)
        self.assertNotIn("strategy:", out)
        self.assertNotIn("brand_safety:", out)

    def test_long_strategy_gets_truncated_with_ellipsis(self):
        v = _health_obj_minimal()
        v["strategy"] = "X" * 400
        out = oh._phase59_format_health_facts_block(v)
        line = next((ln for ln in out.split("\n")
                     if ln.startswith("  - strategy:")), "")
        self.assertTrue(line, "strategy line missing")
        self.assertLessEqual(len(line), 260)
        self.assertTrue(line.endswith("..."),
                        f"strategy not ellipsis-trimmed: {line!r}")

    def test_engine_strings_with_newlines_get_collapsed(self):
        """Prompt-injection guard: engine fields with newlines / control
        chars must NOT inject extra bullet rows. Mirrors dosh+career
        hardening."""
        v = {
            "bucket": "mental_health\nFAKE",
            "tense": "present",
            "verdict": "red_avoid",
            "score": -10,
            "confidence": 70,
            "strategy": "See doctor\n    - injected: bogus",
            "brand_safety_warnings": [
                "Bullet 1\n    - sneaky_inject: yes",
                "Bullet 2\twith\rcontrol\fchars",
            ],
            "timing_window": {
                "risk": {"window_str": "Rahu\nINJECT",
                         "reason": "Reason\n    - leak: x"},
            },
        }
        out = oh._phase59_format_health_facts_block(v)
        for forbidden in ["    - injected:", "    - sneaky_inject:",
                          "    - leak:", "mental_health\n"]:
            self.assertNotIn(forbidden, out,
                             f"injection vector leaked: {forbidden!r}")
        # Whitespace collapsed
        self.assertIn("  - bucket: mental_health FAKE", out)
        self.assertIn("See doctor - injected: bogus", out)
        self.assertIn("Bullet 2 with control chars", out)
        self.assertIn("Rahu INJECT", out)

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
            "top_concerns": "not-a-list",
            "top_supportive": [{"not_layer_key": "x"}, "string-not-dict"],
        }
        out = oh._phase59_format_health_facts_block(bad)
        self.assertTrue(out.startswith("HEALTH_FACTS:"))
        self.assertIn("  - bucket: general_wellness", out)
        self.assertIn("  - tense: general", out)
        self.assertIn("  - verdict: yellow_wait", out)
        self.assertIn("  - score: 0", out)
        self.assertIn("  - confidence: 0", out)
        # Bad lists yield no rows for concerns/supportive
        self.assertNotIn("top_concerns:", out)
        self.assertNotIn("top_supportive:", out)

    def test_non_dict_input_returns_empty(self):
        for x in [None, "", 0, [], {}, "verdict"]:
            self.assertEqual(oh._phase59_format_health_facts_block(x), "",
                             f"non-dict must yield '': {x!r}")

    def test_confidence_pct_fallback(self):
        """Some upstream call sites log `confidence_pct`. The formatter
        accepts both, preferring canonical `confidence`."""
        v = _health_obj_minimal()
        del v["confidence"]
        v["confidence_pct"] = 88
        out = oh._phase59_format_health_facts_block(v)
        self.assertIn("  - confidence: 88", out)


# ──────────────────────────── Extractor integration ────────────────────────────


class TestHealthExtractorIntegration(unittest.TestCase):

    def test_health_q_with_obj_emits_block_no_1liner(self):
        bm = {"health_verdict_obj": _health_obj_general_yellow()}
        out = oh._phase50_extract_verdict_facts(
            bm, "Meri sehat kaisi rahegi?")
        self.assertIn("HEALTH_FACTS:", out)
        self.assertIn("  - bucket: general_wellness", out)
        self.assertNotIn("Health verdict:", out)

    def test_non_health_q_with_health_obj_only_emits_1liner(self):
        bm = {"health_verdict_obj": {"verdict": "yellow_wait status"}}
        out = oh._phase50_extract_verdict_facts(
            bm, "Mera lagna kya hai?")
        self.assertNotIn("HEALTH_FACTS:", out)
        self.assertIn("Health verdict: yellow_wait status", out)

    def test_empty_question_falls_back_to_1liner(self):
        bm = {"health_verdict_obj": {"verdict": "yellow_wait status"}}
        out = oh._phase50_extract_verdict_facts(bm, "")
        self.assertNotIn("HEALTH_FACTS:", out)
        self.assertIn("Health verdict: yellow_wait status", out)

    def test_health_q_no_obj_emits_nothing_for_health(self):
        bm = {}
        out = oh._phase50_extract_verdict_facts(
            bm, "Meri sehat kaisi rahegi?")
        self.assertNotIn("HEALTH_FACTS:", out)
        self.assertNotIn("Health verdict:", out)

    def test_health_block_coexists_with_career_and_dosh(self):
        """Multi-domain questions: health, career, and dosh all emit
        their respective FACTS blocks independently."""
        q = "Manglik dosh hai, naukri kab milegi, sehat bhi kharab hai"
        bm = {
            "health_verdict_obj": _health_obj_general_yellow(),
            "career_verdict_obj": {
                "bucket": "promotion", "tense": "future",
                "verdict": "yellow_wait", "score": 30, "confidence": 60,
                "brand_safety_warnings": ["Career caveat."],
            },
            "dosh_verdict_obj": {
                "total_dosh": 1, "active_count": 1, "mild_count": 0,
                "none_count": 0,
                "dosh_list": [{"key": "manglik", "name": "Manglik Dosha",
                               "status": "Active", "headline": "Mars in 1H"}],
            },
        }
        out = oh._phase50_extract_verdict_facts(bm, q)
        self.assertIn("DOSH_FACTS:", out)
        self.assertIn("CAREER_FACTS:", out)
        self.assertIn("HEALTH_FACTS:", out)
        self.assertNotIn("Career verdict:", out)
        self.assertNotIn("Health verdict:", out)


# ──────────────────────────── Sensitive-topic safety guard ────────────────────────────


class TestHealthSensitiveTopicSafety(unittest.TestCase):
    """Phase 5.9 Batch 3c — explicit safety-net assertions for the
    sensitive-topic surface. These are the most important tests in the
    batch — a regression here means the LLM could output unsafe health
    content without proper guardrails."""

    def test_brand_safety_bullets_always_pass_through_verbatim(self):
        """Engine's brand_safety_warnings must appear in the prompt
        block VERBATIM (modulo whitespace collapse). The formatter must
        never editorialize, summarize, or drop them."""
        v = _health_obj_mental_health_red()
        out = oh._phase59_format_health_facts_block(v)
        for original in v["brand_safety_warnings"]:
            self.assertIn(f"    - {original}", out,
                          f"brand_safety bullet dropped: {original!r}")

    def test_helpline_string_preserved_in_extractor_output(self):
        """End-to-end: even after the extractor wraps the block with
        whatever prefix/suffix, the helpline numbers must survive."""
        bm = {"health_verdict_obj": _health_obj_mental_health_red()}
        out = oh._phase50_extract_verdict_facts(
            bm, "Mental health kaisi hai?")
        self.assertIn("iCall 9152987821", out)
        self.assertIn("Vandrevala 1860-2662-345", out)

    def test_formatter_does_not_inject_forbidden_literals(self):
        """Phase 5.7 source-cleanliness: formatter must never fabricate
        FULL_KUNDLI_JSON / MANDATORY-D-anything literals on its own."""
        clean = oh._phase59_format_health_facts_block(
            _health_obj_general_yellow())
        self.assertNotIn("FULL_KUNDLI_JSON", clean)
        self.assertNotIn("MANDATORY D9", clean)
        self.assertNotIn("MANDATORY D10", clean)
        self.assertNotIn("MANDATORY D30", clean)

    def test_helpline_survives_malformed_bucket_field(self):
        """Architect-flagged: even when the engine returns a malformed /
        missing bucket, the brand_safety bullets (including the
        mental-health helpline) MUST still pass through. The formatter
        must NOT gate brand_safety emission on bucket validity — the
        helpline is the engine's deterministic safety net and must
        survive any bucket-routing regression."""
        for bad_bucket in [None, "", 12345, [], {"x": 1}]:
            v = _health_obj_mental_health_red().copy()
            v["bucket"] = bad_bucket
            out = oh._phase59_format_health_facts_block(v)
            # Helpline still surfaces verbatim
            self.assertIn("iCall 9152987821", out,
                          f"helpline lost on bucket={bad_bucket!r}")
            self.assertIn("Vandrevala 1860-2662-345", out,
                          f"vandrevala lost on bucket={bad_bucket!r}")
            # Bucket falls back to safe default (or stringifies cleanly)
            self.assertIn("  - bucket:", out)

    def test_red_avoid_verdict_score_preserved_no_softening(self):
        """The formatter must NOT soften a red_avoid verdict by hiding
        the negative score or raising the verdict label. Engine ka final
        word — formatter is pure pass-through."""
        v = _health_obj_mental_health_red()  # score=-28, verdict=red_avoid
        out = oh._phase59_format_health_facts_block(v)
        self.assertIn("  - verdict: red_avoid", out)
        self.assertIn("  - score: -28", out)
        # No "yellow_wait" / "green_go" injected
        self.assertNotIn("verdict: yellow_wait", out)
        self.assertNotIn("verdict: green_go", out)


if __name__ == "__main__":
    unittest.main()

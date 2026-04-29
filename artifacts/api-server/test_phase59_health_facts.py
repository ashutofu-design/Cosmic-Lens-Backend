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
        """v3 vocabulary merge: yellow_wait + score=12 → overall_risk=stable.
        2 concerns / 1 supportive → stability=fluctuating (mixed)."""
        out = oh._phase59_format_health_facts_block(
            _health_obj_general_yellow())
        self.assertTrue(out.startswith("HEALTH_FACTS:"),
                        f"missing header: {out!r}")
        # New vocabulary
        self.assertIn("  - overall_risk: stable", out)
        self.assertIn("  - stability: fluctuating", out)
        self.assertIn("  - confidence: 62", out)
        # Old vocab MUST NOT appear in prompt block
        self.assertNotIn("bucket:", out)
        self.assertNotIn("verdict:", out)
        self.assertNotIn("- score:", out)
        self.assertNotIn("tense:", out)
        # Timing windows unchanged
        self.assertIn("  - current_window: Saturn/Mercury/Venus "
                      "(2026-02..2027-09)", out)
        self.assertIn("  - next_window: Saturn/Ketu (2027-09..2028-10)", out)
        # top_concerns → sensitive_areas section
        self.assertIn("  - sensitive_areas:", out)
        self.assertIn("    - L2_sixth_house", out)
        self.assertIn("    - L8_saturn_karaka", out)
        # top_supportive → supportive_factors section
        self.assertIn("  - supportive_factors:", out)
        self.assertIn("    - L9_jupiter_karaka", out)
        # Strategy unchanged
        self.assertIn("  - strategy: Routine yoga + sleep hygiene; defer "
                      "aggressive training.", out)
        # Brand safety unchanged (verbatim)
        self.assertIn("  - brand_safety:", out)
        self.assertIn("    - Yeh diagnosis nahi hai — kisi qualified MD se "
                      "consult karein.", out)
        self.assertIn("    - Self-medication avoid karein.", out)

    def test_mental_health_red_block_surfaces_helpline(self):
        """SENSITIVE-TOPIC SAFETY: red_avoid + score=-28 → overall_risk=
        vulnerable (above -40 high_risk threshold). Helpline must appear
        verbatim — most important guardrail in the entire batch."""
        out = oh._phase59_format_health_facts_block(
            _health_obj_mental_health_red())
        # New vocabulary: red_avoid + score=-28 → vulnerable (>= -40)
        self.assertIn("  - overall_risk: vulnerable", out)
        # 3 concerns, 0 supportive in this fixture → stability=vulnerable
        self.assertIn("  - stability: vulnerable", out)
        self.assertIn("  - confidence: 71", out)
        # PD missing → only md/ad in lord_str
        self.assertIn("  - current_window: Rahu/Saturn (2026-01..2026-12)",
                      out)
        # risk_context → risk_factors section
        self.assertIn("  - risk_factors:", out)
        self.assertIn("    - Rahu-Saturn 2026 — Sade-sati 2nd "
                      "phase peak intensity", out)
        # top_concerns → sensitive_areas section (top 3 surfaced)
        self.assertIn("  - sensitive_areas:", out)
        self.assertIn("    - L6_moon_karaka", out)
        self.assertIn("    - L25_sade_sati", out)
        self.assertIn("    - C4_mental", out)
        # CRITICAL: helpline must appear verbatim (UNCHANGED guarantee)
        self.assertIn("    - Mental-health helpline India: iCall 9152987821, "
                      "Vandrevala 1860-2662-345.", out)
        self.assertIn("    - Crisis ho to immediate professional help lein.",
                      out)

    def test_surgery_block_with_risk_context(self):
        """v3 vocabulary: slow_burn → overall_risk=fluctuating.
        Empty concerns + supportive → stability=fluctuating."""
        out = oh._phase59_format_health_facts_block(
            _health_obj_surgery_slow_burn())
        self.assertIn("  - overall_risk: fluctuating", out)
        self.assertIn("  - stability: fluctuating", out)
        self.assertIn("  - current_window: Mars/Saturn (2026-04..2027-03)",
                      out)
        # risk_context → risk_factors
        self.assertIn("  - risk_factors:", out)
        self.assertIn("    - Mars-Saturn 2026 — "
                      "Surgical-malefic transit overlap", out)
        # next_window absent → omitted
        self.assertNotIn("next_window:", out)
        self.assertIn("    - Final surgery decision treating physician ki "
                      "hai — astrology supplement only.", out)

    def test_minimal_verdict_emits_required_fields_only(self):
        """v3: required fields are now overall_risk/stability/confidence
        (bucket/tense/verdict/score dropped from prompt-facing block)."""
        out = oh._phase59_format_health_facts_block(_health_obj_minimal())
        self.assertTrue(out.startswith("HEALTH_FACTS:"))
        # Required fields (new vocabulary)
        self.assertIn("  - overall_risk: stable", out)  # yellow_wait → stable
        self.assertIn("  - stability: stable", out)     # 0/0 satisfies <=
        self.assertIn("  - confidence: 50", out)
        # Old vocabulary MUST NOT leak into prompt block
        self.assertNotIn("bucket:", out)
        self.assertNotIn("verdict:", out)
        self.assertNotIn("- score:", out)
        self.assertNotIn("tense:", out)
        # No optional fields
        self.assertNotIn("current_window:", out)
        self.assertNotIn("next_window:", out)
        self.assertNotIn("risk_factors:", out)
        self.assertNotIn("sensitive_areas:", out)
        self.assertNotIn("supportive_factors:", out)
        self.assertNotIn("strategy:", out)
        self.assertNotIn("brand_safety:", out)
        # tone_rules ALWAYS emit even on minimal — engine-owned policy
        self.assertIn("tone_rules:", out)

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
        hardening. v3: tests injection via strategy / brand_safety /
        risk_context (now in risk_factors) — bucket/verdict no longer
        in prompt-facing output, so they cannot be injection vectors."""
        v = {
            "bucket": "mental_health\nFAKE",   # not surfaced; ignored
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
                          "    - leak:"]:
            self.assertNotIn(forbidden, out,
                             f"injection vector leaked: {forbidden!r}")
        # Whitespace collapsed in surfaced fields
        self.assertIn("See doctor - injected: bogus", out)
        self.assertIn("Bullet 2 with control chars", out)
        self.assertIn("Rahu INJECT", out)
        # Bucket-with-newline NEVER appears in output (bucket dropped from prompt)
        self.assertNotIn("mental_health FAKE", out)
        self.assertNotIn("mental_health\n", out)

    def test_malformed_field_types_do_not_raise(self):
        """v3: malformed engine output → safe defaults. verdict=non-string
        falls back to yellow_wait → overall_risk=stable; confidence=None
        → 0; bad lists yield no sensitive_areas / supportive_factors."""
        bad = {
            "bucket": 123,
            "tense": None,
            "verdict": ["not", "a", "string"],  # → "" → "yellow_wait" default
            "score": "not-int",                  # → 0
            "confidence": None,                  # → 0
            "timing_window": "not-a-dict",
            "strategy": ["list"],
            "brand_safety_warnings": "not-a-list",
            "top_concerns": "not-a-list",
            "top_supportive": [{"not_layer_key": "x"}, "string-not-dict"],
        }
        out = oh._phase59_format_health_facts_block(bad)
        self.assertTrue(out.startswith("HEALTH_FACTS:"))
        self.assertIn("  - overall_risk: stable", out)  # safe default
        self.assertIn("  - stability: stable", out)     # 0/0 → stable
        self.assertIn("  - confidence: 0", out)
        # Bad lists yield no rows for areas/factors
        self.assertNotIn("sensitive_areas:", out)
        self.assertNotIn("supportive_factors:", out)
        # Old vocab still absent
        self.assertNotIn("bucket:", out)
        self.assertNotIn("verdict:", out)

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


class TestHealthToneRules(unittest.TestCase):
    """User-mandated tone-rule enforcement (Phase 5.9 Batch 3c v2):
    avoid absolute claims / no diagnosis tone / neutral phrasing must be
    handled by the ENGINE, not LLM discretion. The formatter surfaces
    `health_engine.HEALTH_TONE_RULES` as a verbatim `tone_rules:` section
    in EVERY HEALTH_FACTS block — regardless of bucket / verdict /
    presence of brand_safety bullets."""

    def test_tone_rules_constant_lives_in_engine_module(self):
        """Single source of truth: rules MUST be defined in
        health_engine, not in openai_helper. Locks the architectural
        invariant 'tone policy = engine ka decision'."""
        from health_engine import HEALTH_TONE_RULES
        self.assertIsInstance(HEALTH_TONE_RULES, tuple,
                              "Must be tuple (immutable, prevents accidental mutation)")
        self.assertGreaterEqual(len(HEALTH_TONE_RULES), 4,
                                "At minimum: absolute / diagnosis / neutral / prescription rules")
        for r in HEALTH_TONE_RULES:
            self.assertIsInstance(r, str)
            self.assertGreater(len(r.strip()), 30,
                               f"Rule too short to be meaningful: {r!r}")

    def test_tone_rules_section_present_in_every_health_facts(self):
        """Tone rules emit for ALL buckets / verdicts (not just red_avoid).
        Even green-go / surgery / general-wellness must carry tone rules."""
        for fixture in (
            _health_obj_mental_health_red(),
            _health_obj_surgery_slow_burn(),
            _health_obj_minimal(),
            _health_obj_general_yellow(),
        ):
            out = oh._phase59_format_health_facts_block(fixture)
            self.assertIn("  - tone_rules:", out,
                          f"Missing tone_rules in: {fixture.get('bucket')}")

    def test_tone_rules_emit_verbatim_no_paraphrasing(self):
        """Each engine-defined rule appears verbatim as a sub-bullet.
        Locks the 'pure pass-through' invariant."""
        from health_engine import HEALTH_TONE_RULES
        out = oh._phase59_format_health_facts_block(_health_obj_mental_health_red())
        for rule in HEALTH_TONE_RULES:
            self.assertIn(f"    - {rule}", out,
                          f"Rule not surfaced verbatim: {rule[:60]}...")

    def test_tone_rules_appear_after_brand_safety(self):
        """Tone rules must be the LAST section of HEALTH_FACTS so they
        get the highest recency-bias attention weight in the LLM's
        prompt window. Locks the section ordering."""
        out = oh._phase59_format_health_facts_block(_health_obj_mental_health_red())
        bs_idx = out.find("  - brand_safety:")
        tr_idx = out.find("  - tone_rules:")
        self.assertGreater(bs_idx, 0, "brand_safety section must exist")
        self.assertGreater(tr_idx, bs_idx,
                           "tone_rules MUST come after brand_safety (recency bias)")

    def test_tone_rules_emit_even_when_no_brand_safety(self):
        """Tone rules are independent of brand_safety bullets. Even when
        the engine emits zero brand_safety_warnings, tone rules still
        appear (every health response must respect tone)."""
        v = _health_obj_minimal().copy()
        v["brand_safety_warnings"] = []
        out = oh._phase59_format_health_facts_block(v)
        self.assertNotIn("  - brand_safety:", out)
        self.assertIn("  - tone_rules:", out)

    def test_tone_rules_cover_required_policies(self):
        """The four user-mandated policies (absolute / diagnosis /
        neutral / prescription) must each be represented in the rules."""
        from health_engine import HEALTH_TONE_RULES
        joined = " ".join(HEALTH_TONE_RULES).upper()
        self.assertIn("ABSOLUTE", joined,
                      "Missing 'avoid absolute claims' rule")
        self.assertIn("DIAGNOSIS", joined,
                      "Missing 'no diagnosis tone' rule")
        self.assertIn("NEUTRAL", joined,
                      "Missing 'neutral phrasing' rule")
        self.assertIn("PRESCRIPTION", joined,
                      "Missing 'no prescription' rule")

    def test_tone_rules_emit_when_engine_import_fails_fail_closed(self):
        """Architect-mandated FAIL-CLOSED guard: even if the engine
        import fails (broken module / missing constant / partial deploy),
        tone rules MUST still emit using the hardcoded floor in
        openai_helper. Silent dropping = reverting to LLM discretion =
        the exact failure mode the user banned. This test simulates the
        import failure by patching sys.modules to break the import."""
        import sys
        import unittest.mock as mock

        # Verify the floor constant exists in openai_helper
        self.assertTrue(hasattr(oh, "_HEALTH_TONE_RULES_FALLBACK"),
                        "_HEALTH_TONE_RULES_FALLBACK floor missing from openai_helper")
        floor = oh._HEALTH_TONE_RULES_FALLBACK
        self.assertIsInstance(floor, tuple)
        self.assertGreaterEqual(len(floor), 4,
                                "Floor must carry at least 4 rules")

        # Verify the floor and engine constant agree (DRY-violation
        # sync-check — if they drift, this test fails immediately)
        from health_engine import HEALTH_TONE_RULES as engine_rules
        self.assertEqual(floor, engine_rules,
                         "Floor and engine HEALTH_TONE_RULES must stay in sync")

        # Simulate the import failing by replacing health_engine in
        # sys.modules with a broken stub that raises on attribute access
        class _BrokenStub:
            def __getattr__(self, name):
                raise ImportError(f"simulated failure for {name}")

        original = sys.modules.get("health_engine")
        sys.modules["health_engine"] = _BrokenStub()
        try:
            out = oh._phase59_format_health_facts_block(
                _health_obj_mental_health_red()
            )
            self.assertIn("  - tone_rules:", out,
                          "FAIL-CLOSED violated: tone_rules dropped on import failure")
            # Each floor rule must still appear
            for rule in floor:
                self.assertIn(f"    - {rule}", out,
                              f"Floor rule missing on import failure: {rule[:60]}")
        finally:
            if original is not None:
                sys.modules["health_engine"] = original
            else:
                sys.modules.pop("health_engine", None)

    def test_engine_import_failure_is_logged(self):
        """Architect-recommended: when the engine import fails and we
        fall back to the floor, the failure MUST be logged via the
        module logger so prod observability is preserved. Silent
        fallback (even if functionally correct) hides regressions."""
        import sys
        import logging

        original = sys.modules.get("health_engine")

        class _BrokenStub:
            def __getattr__(self, name):
                raise ImportError(f"simulated failure for {name}")

        sys.modules["health_engine"] = _BrokenStub()
        try:
            with self.assertLogs(oh.logger.name, level="ERROR") as cm:
                _ = oh._phase59_format_health_facts_block(
                    _health_obj_mental_health_red()
                )
            joined = "\n".join(cm.output)
            self.assertIn("HEALTH_TONE_RULES", joined,
                          "Import-failure log must mention HEALTH_TONE_RULES")
            self.assertIn("falling back", joined.lower(),
                          "Log must indicate fallback was used")
        finally:
            if original is not None:
                sys.modules["health_engine"] = original
            else:
                sys.modules.pop("health_engine", None)

    def test_tone_rules_survive_in_extractor_output(self):
        """End-to-end check: when the extractor emits HEALTH_FACTS for a
        health Q, the tone_rules section must be present in the final
        prompt-bound text (not just in the formatter's direct output)."""
        bm = {"health_verdict_obj": _health_obj_mental_health_red()}
        out = oh._phase50_extract_verdict_facts(bm, "Mental health kaisi rahegi?")
        self.assertIn("HEALTH_FACTS:", out)
        self.assertIn("  - tone_rules:", out)
        # And at least one tone-rule keyword survives the pipe
        self.assertIn("ABSOLUTE", out)
        self.assertIn("DIAGNOSIS", out)


if __name__ == "__main__":
    unittest.main()

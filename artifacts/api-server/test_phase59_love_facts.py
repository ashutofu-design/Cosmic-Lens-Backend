"""Phase 5.9 Batch 3d — LOVE_FACTS block tests.

Mirrors the Phase 5.9 Batch 3c v3 (health) test structure. Verifies:
  * detector routing (English / Hinglish / Hindi / Devanagari)
  * detector inherits marriage-override defense (love-marriage q ⇢ marriage)
  * formatter output shape (clean lowercase keys, v3 vocabulary)
  * vocabulary mapping (bucket → overall_risk, stability heuristic)
  * defensive handling of malformed engine output
  * extractor routing precedence + 1-liner suppression when block fires
  * coexistence with HEALTH_FACTS / CAREER_FACTS / DOSH_FACTS
  * Phase 5.7 source-cleanliness preserved
  * Sensitive-topic safety: brand_safety bullets ALWAYS surfaced verbatim
  * LOVE_TONE_RULES: engine source-of-truth + FAIL-CLOSED hardcoded floor
  * Architect-locked invariants: red_avoid no softening, brand_safety
    survival on malformed bucket, third-party identity never leaked

Engine is `love_engine.assess_love()` which returns (key fields):
  {
    "verdict": str (locked-text from _VERDICT_TABLE),
    "score":   int (0-100, clipped per bucket),
    "confidence": int,
    "bucket":  "green" | "yellow_wait" | "slow_burn" | "red_avoid",
    "question_type": str (one of 10 buckets — affair_third_party,
                          breakup_signal, reconciliation, commitment_fear,
                          one_sided, long_distance, feelings_check,
                          new_love_timing, compatibility, existing_status),
    "framework_decision": str,
    "current_dasha": str, "next_window": {dasha, start, end, reason},
    "reasons_strong": list[str], "reasons_weak": list[str],
    "strategy": {do: list, do_not: list},
    "affair_check": {fires, signal_strength, indicators, ...} | None,
    "foreign_check": {fires, why, ...} | None,
    "brand_safety_warnings": list[str],
  }
"""
import unittest

import openai_helper as oh


# ──────────────────────────── Fixtures ────────────────────────────


def _love_obj_feelings_green() -> dict:
    """Feelings_check bucket, green — strong love promise + current trigger."""
    return {
        "verdict": "Pyaar ki neev solid hai — current dasha bhi support kar rahi hai.",
        "score": 82,
        "confidence": 78,
        "bucket": "green",
        "question_type": "feelings_check",
        "framework_decision": "Love-window OPEN",
        "current_dasha": "Venus/Jupiter",
        "next_window": {
            "dasha": "Venus/Mercury",
            "start": "2026-08-01",
            "end": "2027-03-15",
            "reason": "Venus mahadasha continues with friendly antar lord",
        },
        "reasons_strong": [
            "Venus exalted in 5th house — strong romance karaka",
            "5L Jupiter in own sign — emotional commitment promise",
            "D9 7L Venus in own sign — deep navamsa support",
        ],
        "reasons_weak": [
            "Saturn aspect on 7th — minor commitment delay",
        ],
        "strategy": {
            "do": [
                "Express feelings honestly during Venus-Mercury antar.",
                "Plan meaningful gestures around Shukravar.",
            ],
            "do_not": ["Force timeline", "Compare with peers"],
        },
        "brand_safety_warnings": [],
    }


def _love_obj_breakup_red() -> dict:
    """Breakup_signal bucket, red_avoid — must surface healing-pair guardrail."""
    return {
        "verdict": "Rishte mein abhi friction-window active hai — separation ka direct prediction nahi karte.",
        "score": 22,
        "confidence": 68,
        "bucket": "red_avoid",
        "question_type": "breakup_signal",
        "framework_decision": "Avoid + remedies first",
        "current_dasha": "Saturn/Mars",
        "next_window": {
            "dasha": "Saturn/Rahu",
            "start": "2027-01-10",
            "end": "2028-06-20",
            "reason": "Healing window — Saturn matures, Rahu provides perspective",
        },
        "reasons_strong": [
            "Jupiter aspects 7th — moral commitment intact",
        ],
        "reasons_weak": [
            "Mars-Saturn 7th house tension — friction high",
            "5L combust — emotional clarity reduced",
            "D9 7L debilitated — deep-chart strain",
        ],
        "strategy": {
            "do": [
                "Active relationship support — counselling consider karein.",
                "Avoid major decisions until Saturn-Rahu antar.",
            ],
            "do_not": ["Make ultimatums", "Involve third parties"],
        },
        "brand_safety_warnings": [
            "BREAKUP BUCKET — narrator MUST soften language; pair every separation indicator with a healing window + remedy; never say 'definite breakup hoga'.",
        ],
    }


def _love_obj_one_sided_red() -> dict:
    """One_sided bucket — must preserve self-worth framing."""
    return {
        "verdict": "Mutual cosmic resonance abhi weak hai — self-care + Venus strengthen karein.",
        "score": 28,
        "confidence": 65,
        "bucket": "red_avoid",
        "question_type": "one_sided",
        "framework_decision": "Avoid + remedies first",
        "current_dasha": "Mercury/Saturn",
        "next_window": {
            "dasha": "Mercury/Venus",
            "start": "2026-11-05",
            "end": "2027-04-12",
            "reason": "Venus antar opens reciprocal feelings window",
        },
        "reasons_strong": [],
        "reasons_weak": [
            "Venus weak — own attractor karaka needs strengthening",
            "5L afflicted by Ketu — communication-channel disruption",
        ],
        "strategy": {
            "do": [
                "Apni Venus mazboot karein — self-presentation, art, beauty.",
            ],
            "do_not": ["Pursue obsessively", "Take rejection personally"],
        },
        "brand_safety_warnings": [
            "ONE-SIDED BUCKET — tone must preserve self-worth; frame as 'mutual cosmic resonance abhi weak hai' not 'wo tumhe pasand nahi karta'.",
        ],
    }


def _love_obj_affair_check_high() -> dict:
    """Affair_third_party bucket with high-signal C1 conditional fire."""
    return {
        "verdict": "Cosmic patterns external influence ka indication dete hain — partner ka direct accusation nahi.",
        "score": 30,
        "confidence": 60,
        "bucket": "red_avoid",
        "question_type": "affair_third_party",
        "framework_decision": "Avoid + remedies first",
        "current_dasha": "Rahu/Venus",
        "reasons_strong": [],
        "reasons_weak": [
            "Rahu in 7th — external influence indicator",
            "Venus in 12th — secrecy pattern",
        ],
        "strategy": {
            "do": [
                "Open communication with partner — assumptions verify karein.",
            ],
            "do_not": ["Surveil partner", "Confront based on cosmic indication alone"],
        },
        "affair_check": {
            "fires": True,
            "signal_strength": "high",
            "indicators": ["Rahu-Venus", "12H secrecy", "Mars-7L"],
            "brand_safety_note": "AFFAIR-CHECK HIGH — narrator MUST describe patterns only; NEVER name a third party.",
        },
        "brand_safety_warnings": [
            "AFFAIR-CHECK HIGH — narrator MUST describe patterns only; NEVER name a third party.",
        ],
    }


def _love_obj_long_distance_yellow() -> dict:
    """Long_distance bucket with foreign_check fire — yellow_wait."""
    return {
        "verdict": "LDR sustainable hai agar communication-window mein effort lagaya jaye.",
        "score": 55,
        "confidence": 70,
        "bucket": "yellow_wait",
        "question_type": "long_distance",
        "framework_decision": "Wait until next window",
        "current_dasha": "Mercury/Moon",
        "next_window": {
            "dasha": "Mercury/Jupiter",
            "start": "2026-09-01",
            "end": "2027-12-15",
            "reason": "Jupiter antar boosts long-distance commitment",
        },
        "reasons_strong": [
            "Mercury strong — communication karaka supports LDR",
            "Jupiter in 11th — fulfillment via friendship base",
        ],
        "reasons_weak": [
            "12th house Venus — physical distance friction",
        ],
        "strategy": {
            "do": ["Schedule consistent video time during Budhvar (Wednesday)."],
            "do_not": ["Skip communication during stressed weeks"],
        },
        "foreign_check": {
            "fires": True,
            "score": 4,
            "why": ["12H significator activates", "Rahu-Venus aspect"],
        },
        "brand_safety_warnings": [],
    }


def _love_obj_minimal() -> dict:
    """Bare-minimum dict — every field optional except shape."""
    return {
        "verdict": "Generic love verdict.",
        "score": 50,
        "confidence": 55,
        "bucket": "yellow_wait",
        "question_type": "feelings_check",
    }


# ──────────────────────────── Detector ────────────────────────────


class TestLoveQuestionDetector(unittest.TestCase):
    """Verifies _phase59_is_love_question delegates to upstream gate."""

    def test_english_love_questions_match(self):
        for q in [
            "Will I find love this year?",
            "Is my crush going to like me back?",
            "When will my soulmate appear?",
            "Should I propose to my girlfriend?",
            "Are we compatible as a couple?",
        ]:
            with self.subTest(q=q):
                self.assertTrue(oh._phase59_is_love_question(q),
                                f"Should match: {q}")

    def test_hinglish_and_hindi_questions_match(self):
        for q in [
            "Mujhe pyaar kab milega?",
            "Mera crush mujhe pasand karta hai kya?",
            "Hum dono ka rishta chalega?",
            "Breakup hoga kya?",
            "Kya wo dhokha de raha hai?",
            "क्या मेरा प्यार सच्चा है?",
            "ब्रेकअप होगा क्या?",
            "धोखा तो नहीं देगा?",
        ]:
            with self.subTest(q=q):
                self.assertTrue(oh._phase59_is_love_question(q),
                                f"Should match: {q}")

    def test_marriage_override_does_not_match(self):
        """Love-marriage questions must route to marriage_engine, not love."""
        for q in [
            "Love marriage kab hogi?",
            "Will I have an arranged marriage?",
            "Mera shaadi kis se hogi?",
            "My husband ke saath compatible hu kya?",
            "Wife ke saath rishta theek hoga?",
            "शादी कब होगी?",
        ]:
            with self.subTest(q=q):
                self.assertFalse(oh._phase59_is_love_question(q),
                                 f"Should NOT match (marriage override): {q}")

    def test_unrelated_questions_do_not_match(self):
        for q in [
            "Job kab milegi?",
            "Stock market mein kya hoga?",
            "Mera health kaisa rahega?",
            "Kitne dhan yog hain?",
            "When is my next promotion?",
        ]:
            with self.subTest(q=q):
                self.assertFalse(oh._phase59_is_love_question(q),
                                 f"Should NOT match: {q}")

    def test_defensive_against_non_string(self):
        for bad in [None, 123, [], {}, b"bytes"]:
            with self.subTest(bad=type(bad).__name__):
                self.assertFalse(oh._phase59_is_love_question(bad))

    def test_defensive_against_empty_or_whitespace(self):
        for s in ["", "   ", "\n\t", None]:
            with self.subTest(s=repr(s)):
                self.assertFalse(oh._phase59_is_love_question(s))


# ──────────────────────────── Formatter ────────────────────────────


class TestLoveFormatter(unittest.TestCase):
    """Verifies _phase59_format_love_facts_block output shape and content."""

    def test_feelings_green_full_block_shape(self):
        block = oh._phase59_format_love_facts_block(_love_obj_feelings_green())
        self.assertTrue(block.startswith("LOVE_FACTS:"))
        self.assertIn("- overall_risk: strong", block)
        self.assertIn("- stability: stable", block)
        self.assertIn("- confidence: 78", block)
        self.assertIn("- question_type: feelings_check", block)
        self.assertIn("- current_dasha: Venus/Jupiter", block)
        self.assertIn("- next_window: Venus/Mercury (2026-08..2027-03)", block)
        self.assertIn("- supportive_factors:", block)
        self.assertIn("    - Venus exalted in 5th house — strong romance karaka", block)
        self.assertIn("- risk_factors:", block)
        self.assertIn("    - Saturn aspect on 7th — minor commitment delay", block)
        self.assertIn("- strategy: Express feelings honestly", block)
        self.assertIn("- tone_rules:", block)

    def test_breakup_red_score_22_is_high_risk(self):
        """red_avoid + score 22 (< 25) → high_risk per the boundary."""
        block = oh._phase59_format_love_facts_block(_love_obj_breakup_red())
        self.assertIn("- overall_risk: high_risk", block)
        self.assertIn("- question_type: breakup_signal", block)
        # brand_safety verbatim survival
        self.assertIn("- brand_safety:", block)
        self.assertIn(
            "BREAKUP BUCKET — narrator MUST soften language; "
            "pair every separation indicator with a healing window "
            "+ remedy; never say 'definite breakup hoga'.",
            block,
        )

    def test_one_sided_block_surfaces_self_worth_guardrail(self):
        block = oh._phase59_format_love_facts_block(_love_obj_one_sided_red())
        self.assertIn("- question_type: one_sided", block)
        # score=28 → red_avoid + score >= 25 → vulnerable (not high_risk)
        self.assertIn("- overall_risk: vulnerable", block)
        # bucket-derived sensitive area
        self.assertIn("- sensitive_areas:", block)
        self.assertIn("    - one_sided_dynamic", block)
        # self-worth brand_safety verbatim
        self.assertIn("ONE-SIDED BUCKET", block)
        self.assertIn("frame as 'mutual cosmic resonance abhi weak hai' "
                      "not 'wo tumhe pasand nahi karta'.", block)

    def test_affair_check_high_signal_emits_sensitive_area(self):
        block = oh._phase59_format_love_facts_block(_love_obj_affair_check_high())
        self.assertIn("- sensitive_areas:", block)
        self.assertIn("    - affair_check_active", block)
        self.assertIn("    - affair_check_high_signal", block)
        # brand_safety verbatim
        self.assertIn("AFFAIR-CHECK HIGH — narrator MUST describe patterns "
                      "only; NEVER name a third party.", block)

    def test_long_distance_with_foreign_check_fires(self):
        block = oh._phase59_format_love_facts_block(_love_obj_long_distance_yellow())
        self.assertIn("- overall_risk: stable", block)
        self.assertIn("- sensitive_areas:", block)
        self.assertIn("    - foreign_distance_factor", block)
        self.assertIn("- next_window: Mercury/Jupiter (2026-09..2027-12)", block)

    def test_minimal_verdict_emits_required_fields_only(self):
        block = oh._phase59_format_love_facts_block(_love_obj_minimal())
        # bucket=yellow_wait → overall_risk=stable
        self.assertIn("- overall_risk: stable", block)
        # 0 supportive, 0 risk → upper-tier balanced check yields "stable"
        # (per `_phase59_love_stability` heuristic: strong/stable + risk
        # <= supportive → stable). This is the safe outcome — no signals
        # to indicate instability.
        self.assertIn("- stability: stable", block)
        self.assertIn("- confidence: 55", block)
        self.assertIn("- question_type: feelings_check", block)
        # No sensitive_areas / supportive_factors / risk_factors / strategy
        self.assertNotIn("- sensitive_areas:", block)
        self.assertNotIn("- supportive_factors:", block)
        self.assertNotIn("- risk_factors:", block)
        self.assertNotIn("- strategy:", block)
        # tone_rules ALWAYS emitted (FAIL-CLOSED)
        self.assertIn("- tone_rules:", block)

    def test_long_strategy_gets_truncated_with_ellipsis(self):
        v = dict(_love_obj_minimal())
        long_do = "Express feelings " * 50  # ~850 chars
        v["strategy"] = {"do": [long_do], "do_not": []}
        block = oh._phase59_format_love_facts_block(v)
        # Find strategy line and check length
        for line in block.splitlines():
            if line.startswith("  - strategy:"):
                # Strategy content (everything after "  - strategy: ")
                content = line[len("  - strategy: "):]
                self.assertLessEqual(len(content), 240)
                self.assertTrue(content.endswith("..."))
                break
        else:
            self.fail("strategy line not found")

    def test_engine_strings_with_newlines_get_collapsed(self):
        v = dict(_love_obj_minimal())
        v["reasons_strong"] = ["Reason\n\nwith\nbreaks"]
        block = oh._phase59_format_love_facts_block(v)
        self.assertIn("Reason with breaks", block)
        self.assertNotIn("Reason\n\nwith", block)

    def test_malformed_field_types_do_not_raise(self):
        v = {
            "verdict": "x",
            "score": "not-an-int",
            "confidence": None,
            "bucket": 12345,        # wrong type
            "reasons_strong": "not a list",
            "reasons_weak": None,
            "strategy": 42,
            "brand_safety_warnings": "not a list",
            "next_window": "not a dict",
            "affair_check": "garbage",
            "foreign_check": [],
        }
        # Must not raise
        block = oh._phase59_format_love_facts_block(v)
        self.assertTrue(block.startswith("LOVE_FACTS:"))
        # tone_rules still emit
        self.assertIn("- tone_rules:", block)

    def test_non_dict_input_returns_empty(self):
        for bad in [None, [], "", 0, "string", b"bytes"]:
            with self.subTest(bad=type(bad).__name__):
                self.assertEqual(oh._phase59_format_love_facts_block(bad), "")

    def test_confidence_pct_fallback(self):
        """Accept either `confidence` or `confidence_pct` (canonical preferred)."""
        v = {"verdict": "x", "bucket": "green", "score": 70,
             "confidence_pct": 88}
        block = oh._phase59_format_love_facts_block(v)
        self.assertIn("- confidence: 88", block)


# ──────────────────────────── Vocabulary mapping ────────────────────────────


class TestLoveVocabularyMapping(unittest.TestCase):
    """Locks the bucket→overall_risk and stability heuristic semantics."""

    # ── overall_risk mapping ──
    def test_overall_risk_green_to_strong(self):
        self.assertEqual(oh._phase59_love_overall_risk("green", 80), "strong")
        self.assertEqual(oh._phase59_love_overall_risk("green", 65), "strong")

    def test_overall_risk_yellow_wait_to_stable(self):
        self.assertEqual(
            oh._phase59_love_overall_risk("yellow_wait", 55), "stable")
        self.assertEqual(
            oh._phase59_love_overall_risk("yellow_wait", 45), "stable")

    def test_overall_risk_slow_burn_to_fluctuating(self):
        self.assertEqual(
            oh._phase59_love_overall_risk("slow_burn", 50), "fluctuating")
        self.assertEqual(
            oh._phase59_love_overall_risk("slow_burn", 35), "fluctuating")

    def test_overall_risk_red_avoid_score_threshold(self):
        """red_avoid + score >= 25 → vulnerable; < 25 → high_risk."""
        # boundary
        self.assertEqual(
            oh._phase59_love_overall_risk("red_avoid", 25), "vulnerable")
        # below boundary
        self.assertEqual(
            oh._phase59_love_overall_risk("red_avoid", 24), "high_risk")
        # well above
        self.assertEqual(
            oh._phase59_love_overall_risk("red_avoid", 38), "vulnerable")
        # well below
        self.assertEqual(
            oh._phase59_love_overall_risk("red_avoid", 10), "high_risk")

    def test_overall_risk_unknown_bucket_safe_default(self):
        self.assertEqual(
            oh._phase59_love_overall_risk("garbage", 50), "fluctuating")
        self.assertEqual(
            oh._phase59_love_overall_risk("", 50), "fluctuating")
        self.assertEqual(
            oh._phase59_love_overall_risk(None, 50), "fluctuating")

    def test_overall_risk_case_insensitive_match(self):
        for raw, expected in [
            ("GREEN",       "strong"),
            ("Yellow_Wait", "stable"),
            ("  slow_burn ", "fluctuating"),
            ("RED_AVOID",   "vulnerable"),  # score 30 → vulnerable
        ]:
            with self.subTest(raw=raw):
                self.assertEqual(
                    oh._phase59_love_overall_risk(raw, 30), expected)

    # ── stability heuristic ──
    def test_stability_strong_with_supportive_majority_is_stable(self):
        self.assertEqual(
            oh._phase59_love_stability("strong", n_supportive=3, n_risk=1),
            "stable")
        self.assertEqual(
            oh._phase59_love_stability("strong", n_supportive=2, n_risk=2),
            "stable")  # tie counts as stable for upper tiers

    def test_stability_stable_tier_with_supportive_balance_is_stable(self):
        self.assertEqual(
            oh._phase59_love_stability("stable", n_supportive=2, n_risk=1),
            "stable")

    def test_stability_strong_but_risk_outweighs_is_fluctuating(self):
        self.assertEqual(
            oh._phase59_love_stability("strong", n_supportive=1, n_risk=3),
            "fluctuating")

    def test_stability_vulnerable_with_risk_majority_is_vulnerable(self):
        self.assertEqual(
            oh._phase59_love_stability("vulnerable", n_supportive=1, n_risk=3),
            "vulnerable")
        self.assertEqual(
            oh._phase59_love_stability("high_risk", n_supportive=0, n_risk=2),
            "vulnerable")

    def test_stability_middle_tier_is_fluctuating(self):
        self.assertEqual(
            oh._phase59_love_stability("fluctuating", n_supportive=2, n_risk=2),
            "fluctuating")
        self.assertEqual(
            oh._phase59_love_stability("fluctuating", n_supportive=0, n_risk=0),
            "fluctuating")


# ──────────────────────────── Sensitive-topic safety ────────────────────────────


class TestLoveSensitiveTopicSafety(unittest.TestCase):
    """Architect-locked invariants for the love sensitive-topic surface."""

    def test_breakup_brand_safety_surfaces_verbatim(self):
        block = oh._phase59_format_love_facts_block(_love_obj_breakup_red())
        # Verbatim text — no paraphrasing
        self.assertIn(
            "BREAKUP BUCKET — narrator MUST soften language; pair every "
            "separation indicator with a healing window + remedy; never "
            "say 'definite breakup hoga'.",
            block,
        )

    def test_one_sided_brand_safety_surfaces_verbatim(self):
        block = oh._phase59_format_love_facts_block(_love_obj_one_sided_red())
        self.assertIn(
            "ONE-SIDED BUCKET — tone must preserve self-worth; "
            "frame as 'mutual cosmic resonance abhi weak hai' "
            "not 'wo tumhe pasand nahi karta'.",
            block,
        )

    def test_affair_brand_safety_surfaces_verbatim(self):
        block = oh._phase59_format_love_facts_block(_love_obj_affair_check_high())
        self.assertIn(
            "AFFAIR-CHECK HIGH — narrator MUST describe patterns only; "
            "NEVER name a third party.",
            block,
        )

    def test_third_party_identity_never_leaked(self):
        """Architect-locked: NO specific person identification ever surfaces.

        Even if the engine were to put names in indicators (it doesn't,
        but defensive), the formatter's sensitive_areas labels are
        engine-internal STRUCTURAL labels only.
        """
        v = dict(_love_obj_affair_check_high())
        # Inject hypothetical leak-attempt
        v["affair_check"] = dict(v["affair_check"])
        v["affair_check"]["indicators"] = [
            "Cousin Rohit", "Office colleague Priya", "Neighbor uncle"
        ]
        block = oh._phase59_format_love_facts_block(v)
        # None of the names appear (formatter does not surface indicators
        # at all — only the structural high_signal label).
        self.assertNotIn("Rohit", block)
        self.assertNotIn("Priya", block)
        self.assertNotIn("uncle", block)

    def test_brand_safety_survives_malformed_bucket_field(self):
        """Architect-locked guard: even with broken bucket, brand_safety
        + tone_rules + overall_risk still emit cleanly. Malformed bucket
        falls through `_phase59_love_overall_risk()`'s unknown-bucket
        path → "fluctuating" (safe middle, never claims strength).
        """
        v = {
            "verdict": "x",
            "score": 22,
            "confidence": 60,
            "bucket": ["GARBAGE", "TYPE"],  # wrong type — coerces to ""
            "question_type": "breakup_signal",
            "brand_safety_warnings": [
                "BREAKUP BUCKET — narrator MUST soften language; pair every separation indicator with a healing window + remedy; never say 'definite breakup hoga'.",
            ],
        }
        block = oh._phase59_format_love_facts_block(v)
        # overall_risk falls back to fluctuating (safe middle)
        self.assertIn("- overall_risk: fluctuating", block)
        # brand_safety still verbatim
        self.assertIn("BREAKUP BUCKET — narrator MUST soften language", block)
        # tone_rules still present
        self.assertIn("- tone_rules:", block)
        self.assertIn("BREAKUP ki ABSOLUTE prediction band.", block)

    def test_red_avoid_no_softening_in_new_vocabulary(self):
        """Architect-locked: red_avoid bucket MUST surface as
        vulnerable or high_risk only — never softer tiers.
        """
        for score in [40, 30, 25, 24, 10, 0]:
            v = dict(_love_obj_minimal())
            v["bucket"] = "red_avoid"
            v["score"] = score
            block = oh._phase59_format_love_facts_block(v)
            # Must NOT be softened to strong / stable / fluctuating
            self.assertNotIn("- overall_risk: strong", block,
                             f"red_avoid score={score} softened to strong")
            self.assertNotIn("- overall_risk: stable", block,
                             f"red_avoid score={score} softened to stable")
            self.assertNotIn("- overall_risk: fluctuating", block,
                             f"red_avoid score={score} softened to fluctuating")
            # Must be vulnerable or high_risk
            self.assertTrue(
                "- overall_risk: vulnerable" in block
                or "- overall_risk: high_risk" in block,
                f"red_avoid score={score} did not surface as worst tiers"
            )


# ──────────────────────────── LOVE_TONE_RULES ────────────────────────────


class TestLoveToneRules(unittest.TestCase):
    """Verifies engine-owned tone rules + FAIL-CLOSED hardcoded floor."""

    def test_tone_rules_constant_lives_in_engine_module(self):
        from love_engine import LOVE_TONE_RULES
        self.assertIsInstance(LOVE_TONE_RULES, tuple)
        self.assertEqual(len(LOVE_TONE_RULES), 5,
                         "Five tone-policy rules expected")
        for r in LOVE_TONE_RULES:
            self.assertIsInstance(r, str)
            self.assertTrue(r.strip())

    def test_tone_rules_fallback_matches_engine_constant(self):
        """Sync test — the FAIL-CLOSED floor must be byte-identical to
        the engine source. If the engine changes a rule, the floor MUST
        be updated in the same diff."""
        from love_engine import LOVE_TONE_RULES
        self.assertEqual(
            oh._LOVE_TONE_RULES_FALLBACK,
            LOVE_TONE_RULES,
            "Hardcoded floor in openai_helper drifted from "
            "love_engine.LOVE_TONE_RULES — sync them in the same diff."
        )

    def test_tone_rules_section_present_in_every_love_facts(self):
        for fixture in [
            _love_obj_feelings_green(),
            _love_obj_breakup_red(),
            _love_obj_one_sided_red(),
            _love_obj_affair_check_high(),
            _love_obj_long_distance_yellow(),
            _love_obj_minimal(),
        ]:
            with self.subTest(question_type=fixture.get("question_type")):
                block = oh._phase59_format_love_facts_block(fixture)
                self.assertIn("- tone_rules:", block)

    def test_tone_rules_emit_verbatim_no_paraphrasing(self):
        from love_engine import LOVE_TONE_RULES
        block = oh._phase59_format_love_facts_block(_love_obj_breakup_red())
        for rule in LOVE_TONE_RULES:
            self.assertIn(rule, block,
                          f"Tone rule paraphrased or dropped: {rule[:60]}")

    def test_tone_rules_appear_after_brand_safety(self):
        """Recency-bias position: tone_rules must be the LAST section."""
        block = oh._phase59_format_love_facts_block(_love_obj_breakup_red())
        idx_brand = block.index("- brand_safety:")
        idx_tone  = block.index("- tone_rules:")
        self.assertLess(idx_brand, idx_tone,
                        "tone_rules must come AFTER brand_safety")
        # tone_rules must be the FINAL section — nothing else after it
        # except the rule bullets themselves
        tail = block[idx_tone:]
        for line in tail.splitlines()[1:]:  # skip "- tone_rules:" header
            stripped = line.strip()
            if stripped and not stripped.startswith("- "):
                continue  # rule body
            # Any "- foo:" header after tone_rules would be a regression
            if stripped.startswith("- ") and stripped.endswith(":"):
                self.fail(f"Section header found after tone_rules: {stripped}")

    def test_tone_rules_emit_when_no_brand_safety(self):
        v = dict(_love_obj_minimal())
        v.pop("brand_safety_warnings", None)
        block = oh._phase59_format_love_facts_block(v)
        self.assertNotIn("- brand_safety:", block)
        self.assertIn("- tone_rules:", block)

    def test_tone_rules_cover_required_policies(self):
        """Verify each required policy area is named in some rule."""
        from love_engine import LOVE_TONE_RULES
        joined = " || ".join(LOVE_TONE_RULES)
        for keyword in [
            "BETRAYAL",       # rule 1
            "REJECTION",      # rule 2
            "BREAKUP",        # rule 3
            "THIRD-PARTY",    # rule 4
            "TIMING",         # rule 5
        ]:
            self.assertIn(keyword, joined,
                          f"Missing required tone-policy area: {keyword}")

    def test_tone_rules_emit_when_engine_import_fails_fail_closed(self):
        """Architect-mandated FAIL-CLOSED: even with a broken engine
        import, tone rules MUST still emit (from the hardcoded floor).
        """
        import sys
        import importlib
        # Save real module
        real_engine = sys.modules.get("love_engine")
        try:
            # Inject broken module
            class _Broken:
                def __getattr__(self, name):
                    raise ImportError("simulated engine break")
            sys.modules["love_engine"] = _Broken()
            # Force re-import in the formatter's try-block
            block = oh._phase59_format_love_facts_block(_love_obj_minimal())
            self.assertIn("- tone_rules:", block,
                          "FAIL-CLOSED floor did not fire — tone enforcement lost")
            # Floor content must match the canonical 5 rules
            for rule in oh._LOVE_TONE_RULES_FALLBACK:
                self.assertIn(rule, block)
        finally:
            if real_engine is not None:
                sys.modules["love_engine"] = real_engine
            elif "love_engine" in sys.modules:
                del sys.modules["love_engine"]
            # Reload to restore real binding
            try:
                importlib.import_module("love_engine")
            except Exception:
                pass


# ──────────────────────────── Extractor wiring ────────────────────────────


class TestLoveExtractorIntegration(unittest.TestCase):
    """Verifies _phase50_extract_verdict_facts wires LOVE_FACTS correctly."""

    def test_love_q_with_obj_emits_block_no_1liner(self):
        bm = {"love_verdict_obj": _love_obj_feelings_green()}
        out = oh._phase50_extract_verdict_facts(bm, "Will I find love this year?")
        self.assertIn("LOVE_FACTS:", out)
        self.assertIn("- overall_risk: strong", out)
        # 1-liner suppressed
        self.assertNotIn("Love verdict:", out)

    def test_non_love_q_with_love_obj_only_emits_1liner(self):
        """Existing test_phase58 / test_phase50 mocks rely on this:
        when the question doesn't match love-detector, the 1-liner
        backward-compat path still fires.
        """
        bm = {"love_verdict_obj": {"verdict": "L"}}
        out = oh._phase50_extract_verdict_facts(bm, "")  # empty q
        self.assertNotIn("LOVE_FACTS:", out)
        self.assertIn("Love verdict: L", out)

    def test_marriage_q_with_love_obj_only_emits_1liner(self):
        """Marriage-override routing: love-marriage Qs should NOT trigger
        the LOVE_FACTS block (marriage_engine handles them upstream).
        """
        bm = {"love_verdict_obj": _love_obj_feelings_green()}
        out = oh._phase50_extract_verdict_facts(bm, "Love marriage kab hogi?")
        # detector returns False (marriage override) → 1-liner only
        self.assertNotIn("LOVE_FACTS:", out)
        self.assertIn("Love verdict:", out)

    def test_love_q_no_obj_emits_nothing_for_love(self):
        bm = {}
        out = oh._phase50_extract_verdict_facts(bm, "Will I find love?")
        self.assertNotIn("LOVE_FACTS:", out)
        self.assertNotIn("Love verdict:", out)

    def test_love_block_coexists_with_health_career_dosh(self):
        """Multi-domain bm should emit all relevant FACTS blocks, but the
        question routing decides which block is the leader. Here the
        question is love-only, so only LOVE_FACTS fires.
        """
        bm = {
            "love_verdict_obj":   _love_obj_feelings_green(),
            "career_verdict_obj": {"verdict": "C"},
            "health_verdict_obj": {"verdict": "H"},
            "stock_verdict_obj":  {"verdict": "S"},
        }
        out = oh._phase50_extract_verdict_facts(bm, "Will I find love?")
        self.assertIn("LOVE_FACTS:", out)
        # Other engines fall back to 1-liners (their detectors don't fire)
        self.assertIn("Career verdict: C", out)
        self.assertIn("Health verdict: H", out)
        self.assertIn("Stock verdict: S", out)
        # The love 1-liner is suppressed
        self.assertNotIn("Love verdict:", out)


# ──────────────────────────── Phase 5.7 source-cleanliness ────────────────────


class TestLoveSourceCleanliness(unittest.TestCase):
    """Ensures the formatter never re-leaks Phase-5.7-cleaned literals."""

    def test_formatter_does_not_inject_forbidden_literals(self):
        v = _love_obj_feelings_green()
        block = oh._phase59_format_love_facts_block(v)
        for forbidden in [
            "FULL_KUNDLI_JSON",
            "MANDATORY-D",
            "MANDATORY_D",
            "LOCKED FACTS",
            "supertype contract",
            "UNIFIED NARRATOR",
        ]:
            self.assertNotIn(
                forbidden, block,
                f"Phase 5.7 forbidden literal leaked into LOVE_FACTS: {forbidden}"
            )


if __name__ == "__main__":
    unittest.main()

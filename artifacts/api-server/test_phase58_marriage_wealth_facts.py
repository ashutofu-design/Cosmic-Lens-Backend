"""
Phase 5.8 — Marriage & Wealth FACTS blocks (clean architecture)

Pins the contract for the new clean facts blocks that replace the heavy
`format_verdict_for_prompt` prose blocks (with `>>> NARRATE EXACTLY ... <<<`
instructions, JSON envelopes, Sanskrit jargon labels) in the minimal-prompt
path. Same lock pattern as Phase 5.5h KP / Phase 5.6 yoga / Phase 5.7.1
verdict: engine = source of truth, LLM = narrator only.

Tests cover:
  - question detectors (positive + negative + non-string defensive)
  - MARRIAGE_FACTS formatter (schema, mapping rules, no rule-prose,
    no `>>> NARRATE` directives, defensive against bad input)
  - WEALTH_FACTS formatter (schema, mapping rules, no rule-prose,
    defensive against bad input)
  - install_minimal_messages routing:
      * marriage Q + marriage_verdict_obj  → MARRIAGE_FACTS emitted
      * wealth   Q + wealth_verdict_obj    → WEALTH_FACTS emitted
      * marriage Q + only legacy text      → 1-line fallback emitted
      * non-marriage non-wealth Q          → neither block emitted
      * empty/no question (unit-test path) → backward-compat 1-liners
"""
import os
import unittest
from unittest.mock import patch

import openai_helper as oh


# ───────────────────────── Fixtures ─────────────────────────

def _sample_kundli() -> dict:
    return {
        "ascendant":      "Sagittarius",
        "moonSign":       "Gemini",
        "sunSign":        "Libra",
        "nakshatra":      "Ardra",
        "currentDasha": {"maha": "Jupiter", "antar": "Rahu",
                         "startDate": "2010-06-27", "endDate": "2026-06-27"},
        "planets": [
            {"name": "Mars",    "sign": "Sagittarius", "house": 1,  "degrees": 12.5},
            {"name": "Moon",    "sign": "Gemini",      "house": 7,  "degrees": 5.4},
            {"name": "Venus",   "sign": "Leo",         "house": 9,  "degrees": 18.3},
            {"name": "Sun",     "sign": "Libra",       "house": 11, "degrees": 11.9},
        ],
    }


def _marriage_obj_clear() -> dict:
    """High-confidence promised marriage with a window."""
    return {
        "verdict":           "Vivah promised — strong yog",
        "marriage_promised": True,
        "marriage_denied":   False,
        "delay":             False,
        "score":             72,
        "confidence":        85,
        "reasons_strong":    ["7th lord Jupiter exalted in 5H",
                              "Venus dignity strong",
                              "D9 7L well-placed"],
        "reasons_weak":      ["Saturn aspecting 7H"],
        "delay_reasons":     [],
        "next_window": {
            "dasha":          "Jupiter-Venus",
            "start":          "2026-04",
            "end":            "2026-06",
            "refined_start":  "",
            "refined_end":    "",
        },
    }


def _marriage_obj_inconclusive() -> dict:
    """Denied / very low score."""
    return {
        "marriage_promised": False,
        "marriage_denied":   True,
        "score":             18,
        "confidence":        72,
        "reasons_strong":    [],
        "reasons_weak":      ["Combust 7L", "Mars + Saturn malefic on 7H"],
        "delay_reasons":     ["Sade-sati on Moon"],
        "next_window":       {},
    }


def _wealth_obj_strong() -> dict:
    return {
        "bucket":     "general_wealth",
        "tense":      "general",
        "verdict":    "green_go",
        "score":      78,
        "confidence": 83,
        "top_supportive": [
            {"layer": "L1_second_house", "score": 8},
            {"layer": "L9_jupiter_dhana_karaka", "score": 6},
            {"layer": "L23_dhana_yogas", "score": 5},
        ],
        "top_concerns": [
            {"layer": "L8_sixth_house_wealth", "score": -4},
        ],
    }


def _wealth_obj_weak() -> dict:
    return {
        "bucket":     "loan_clearance",
        "verdict":    "red_avoid",
        "score":      32,
        "confidence": 65,
        "top_supportive": [],
        "top_concerns": [
            {"layer": "L7_twelfth_house_wealth", "score": -7},
            {"layer": "L8_sixth_house_wealth",  "score": -5},
        ],
    }


# ───────────────────────── Detectors ─────────────────────────

class TestPhase58MarriageDetector(unittest.TestCase):

    def test_english_keywords_match(self):
        for q in ["When will I get married?",
                  "marriage timing please",
                  "kab shaadi hogi?",
                  "tell me about my spouse",
                  "wife kab milegi?",
                  "life-partner kab milega?"]:
            self.assertTrue(oh._phase58_is_marriage_question(q),
                            f"should match: {q!r}")

    def test_hindi_keywords_match(self):
        for q in ["मेरी शादी कब होगी?",
                  "विवाह योग kab hai?",
                  "जीवनसाथी kaisa milega?"]:
            self.assertTrue(oh._phase58_is_marriage_question(q),
                            f"should match: {q!r}")

    def test_unrelated_questions_do_not_match(self):
        for q in ["mera career kab badhega?",
                  "kya mujhe ghar kharidna chahiye?",
                  "money kab milega?",
                  "health kaisi rahegi?",
                  ""]:
            self.assertFalse(oh._phase58_is_marriage_question(q),
                             f"should NOT match: {q!r}")

    def test_defensive_against_non_string(self):
        for bad in [None, 123, [], {}, 4.5]:
            self.assertFalse(oh._phase58_is_marriage_question(bad))


class TestPhase58WealthDetector(unittest.TestCase):

    def test_wealth_keywords_match(self):
        for q in ["mera paisa strong hai?",
                  "When will I become rich?",
                  "dhan-yog hai?",
                  "income badhega kab?",
                  "loan kab clear hoga?"]:
            self.assertTrue(oh._phase58_is_wealth_question_p58(q),
                            f"should match: {q!r}")

    def test_unrelated_questions_do_not_match(self):
        for q in ["meri shaadi kab hogi?",
                  "love marriage hoga?",
                  "career kya hogi?"]:
            self.assertFalse(oh._phase58_is_wealth_question_p58(q),
                             f"should NOT match: {q!r}")

    def test_defensive_against_non_string(self):
        for bad in [None, 123, [], {}, 4.5]:
            self.assertFalse(oh._phase58_is_wealth_question_p58(bad))


# ───────────────────────── MARRIAGE_FACTS formatter ─────────────────────────

class TestPhase58FormatMarriageFactsBlock(unittest.TestCase):

    def test_clean_block_for_promised_marriage(self):
        out = oh._phase58_format_marriage_facts_block(_marriage_obj_clear())
        # Header
        self.assertTrue(out.startswith("MARRIAGE_FACTS:"),
                        f"missing MARRIAGE_FACTS: header — {out!r}")
        # Lowercase keys with "  - " bullets
        self.assertIn("  - verdict: clear", out)
        self.assertIn("  - confidence: 0.85", out)
        # Engine timing window phrase pulled in
        self.assertIn("April 2026 to June 2026", out)
        # Reasons appear as nested "    - " bullets
        self.assertIn("  - reasons_positive:", out)
        self.assertIn("    - 7th lord Jupiter exalted in 5H", out)
        self.assertIn("  - reasons_negative:", out)
        self.assertIn("    - Saturn aspecting 7H", out)

    def test_inconclusive_label_for_denied(self):
        out = oh._phase58_format_marriage_facts_block(_marriage_obj_inconclusive())
        self.assertIn("  - verdict: inconclusive", out)
        # No timing window present
        self.assertIn("  - timing_window: unknown", out)
        # Delay reasons merged into negatives
        self.assertIn("    - Sade-sati on Moon", out)
        # No positive reasons → "none" placeholder
        self.assertIn("  - reasons_positive: none", out)

    def test_leaning_label_for_promised_mid_score(self):
        v = _marriage_obj_clear()
        v["score"] = 50          # promised but not strong
        v["confidence"] = 60
        out = oh._phase58_format_marriage_facts_block(v)
        self.assertIn("  - verdict: leaning", out)
        self.assertIn("  - confidence: 0.6", out)

    def test_no_rule_prose_or_narrate_directives(self):
        """Critical: NO `>>> NARRATE` rules, NO `DO NOT widen`, NO
        `AUTHORITATIVE`, NO Sanskrit jargon labels — just facts."""
        out = oh._phase58_format_marriage_facts_block(_marriage_obj_clear())
        for forbidden in [">>> NARRATE", "DO NOT widen", "AUTHORITATIVE",
                          "VERDICT:", "Score:", "marriage_promised:",
                          "Recommended remedy", "JSON envelope",
                          "════"]:
            self.assertNotIn(forbidden, out,
                             f"forbidden rule-prose `{forbidden}` leaked")

    def test_returns_empty_for_bad_input(self):
        for bad in [None, {}, "string", 123, []]:
            self.assertEqual(oh._phase58_format_marriage_facts_block(bad), "")

    def test_handles_missing_keys_without_raising(self):
        out = oh._phase58_format_marriage_facts_block({"score": 0})
        self.assertTrue(out.startswith("MARRIAGE_FACTS:"))
        self.assertIn("  - verdict: inconclusive", out)
        self.assertIn("  - confidence: 0.0", out)
        self.assertIn("  - timing_window: unknown", out)

    def test_caps_reasons_at_five(self):
        v = _marriage_obj_clear()
        v["reasons_strong"] = [f"Reason {i}" for i in range(20)]
        out = oh._phase58_format_marriage_facts_block(v)
        # Count "    - Reason " occurrences
        count = sum(1 for ln in out.splitlines()
                    if ln.startswith("    - Reason "))
        self.assertEqual(count, 5)


# ───────────────────────── WEALTH_FACTS formatter ─────────────────────────

class TestPhase58FormatWealthFactsBlock(unittest.TestCase):

    def test_clean_block_for_strong_wealth(self):
        out = oh._phase58_format_wealth_facts_block(_wealth_obj_strong())
        self.assertTrue(out.startswith("WEALTH_FACTS:"))
        self.assertIn("  - wealth_level: strong", out)
        self.assertIn("  - stability: stable", out)
        self.assertIn("  - bucket: general_wealth", out)
        self.assertIn("  - supporting_indicators:", out)
        self.assertIn("    - L1_second_house", out)
        self.assertIn("  - risk_factors:", out)
        self.assertIn("    - L8_sixth_house_wealth", out)
        self.assertIn("  - confidence: 0.83", out)

    def test_weak_wealth_label(self):
        out = oh._phase58_format_wealth_facts_block(_wealth_obj_weak())
        self.assertIn("  - wealth_level: weak", out)
        self.assertIn("  - stability: unstable", out)
        # No supportive layers → placeholder
        self.assertIn("  - supporting_indicators: none", out)

    def test_moderate_yellow_wait_is_mixed(self):
        v = _wealth_obj_strong()
        v["score"]   = 55
        v["verdict"] = "yellow_wait"
        out = oh._phase58_format_wealth_facts_block(v)
        self.assertIn("  - wealth_level: moderate", out)
        self.assertIn("  - stability: mixed", out)

    def test_no_rule_prose_or_jargon_labels(self):
        out = oh._phase58_format_wealth_facts_block(_wealth_obj_strong())
        for forbidden in ["⭐", "COSMIC WEALTH VERDICT", "LOCKED FACTS",
                          "do NOT modify", "QUESTION TYPE:",
                          "QUESTION TENSE:", "VERDICT:", "▸",
                          "SCORE BREAKDOWN", "════"]:
            self.assertNotIn(forbidden, out,
                             f"forbidden rule-prose `{forbidden}` leaked")

    def test_returns_empty_for_bad_input(self):
        for bad in [None, {}, "string", 123, []]:
            self.assertEqual(oh._phase58_format_wealth_facts_block(bad), "")

    def test_handles_missing_keys_without_raising(self):
        out = oh._phase58_format_wealth_facts_block({"score": 0})
        self.assertTrue(out.startswith("WEALTH_FACTS:"))
        self.assertIn("  - wealth_level: weak", out)
        self.assertIn("  - stability: unstable", out)
        self.assertIn("  - confidence: 0.0", out)

    def test_caps_indicators_at_three(self):
        v = _wealth_obj_strong()
        v["top_supportive"] = [{"layer": f"L{i}_x", "score": 5}
                               for i in range(10)]
        out = oh._phase58_format_wealth_facts_block(v)
        count = sum(1 for ln in out.splitlines()
                    if ln.startswith("    - L"))
        # 3 supporting + 1 risk
        self.assertLessEqual(count, 4)

    def test_malformed_field_types_do_not_raise(self):
        """Defensive contract: docstring promises 'never raises'.

        Regression guard for the case where upstream emits non-string
        values for `verdict` / `bucket` (e.g. accidentally an int from
        a refactor). The formatter must coerce gracefully, not crash
        the entire minimal-prompt assembly.
        """
        bad_inputs = [
            {"score": 80, "verdict": 123, "bucket": ["unexpected"]},
            {"score": 50, "verdict": None, "bucket": 42},
            {"score": "not-an-int", "verdict": {"green_go": True},
             "bucket": object(), "confidence": "high"},
            {"score": 75, "verdict": "GREEN_GO", "bucket": " strong ",
             "top_supportive": "should-be-list",
             "top_concerns": {"layer": "wrong-shape"}},
        ]
        for v in bad_inputs:
            try:
                out = oh._phase58_format_wealth_facts_block(v)
            except Exception as e:  # pragma: no cover
                self.fail(
                    f"formatter raised {type(e).__name__} on {v!r}: {e}")
            self.assertIsInstance(out, str)
            # Must still produce a header even when most fields are junk
            self.assertTrue(out.startswith("WEALTH_FACTS:"),
                            f"missing header for {v!r}")

    def test_marriage_formatter_malformed_types_do_not_raise(self):
        """Symmetric defensive guard for the marriage formatter."""
        bad_inputs = [
            {"score": "x", "confidence": "y", "marriage_promised": "yes",
             "marriage_denied": 0, "reasons_strong": "not-a-list",
             "reasons_weak": {"k": "v"}, "delay_reasons": 99},
            {"score": None, "confidence": None,
             "marriage_promised": None, "marriage_denied": None},
        ]
        for v in bad_inputs:
            try:
                out = oh._phase58_format_marriage_facts_block(v)
            except Exception as e:  # pragma: no cover
                self.fail(
                    f"marriage formatter raised {type(e).__name__} "
                    f"on {v!r}: {e}")
            self.assertIsInstance(out, str)
            self.assertTrue(out.startswith("MARRIAGE_FACTS:"),
                            f"missing header for {v!r}")


# ───────────────────────── Install routing ─────────────────────────

class TestPhase58InstallRouting(unittest.TestCase):

    def test_marriage_question_emits_marriage_facts_block(self):
        bm = {"marriage_verdict_obj": _marriage_obj_clear()}
        msgs, _ = oh._phase50_install_minimal_messages(
            "kya meri shaadi 2026 mein hogi?",
            _sample_kundli(), "hn", bm,
            req_id="m-test",
        )
        user_msg = msgs[1]["content"]
        self.assertIn("MARRIAGE_FACTS:", user_msg)
        self.assertIn("  - verdict: clear", user_msg)
        # NO wealth block
        self.assertNotIn("WEALTH_FACTS:", user_msg)

    def test_wealth_question_emits_wealth_facts_block(self):
        bm = {"wealth_verdict_obj": _wealth_obj_strong()}
        msgs, _ = oh._phase50_install_minimal_messages(
            "mera paisa kab strong hoga?",
            _sample_kundli(), "hn", bm,
            req_id="w-test",
        )
        user_msg = msgs[1]["content"]
        self.assertIn("WEALTH_FACTS:", user_msg)
        self.assertIn("  - wealth_level: strong", user_msg)
        # NO marriage block
        self.assertNotIn("MARRIAGE_FACTS:", user_msg)

    def test_marriage_legacy_text_fallback(self):
        """When only `marriage_verdict_block` (legacy text) exists and
        no `marriage_verdict_obj`, marriage Q must still get the 1-line
        fallback so we never lose data."""
        bm = {"marriage_verdict_block":
              "Vivah patience zaroori — significant rukawat\n  (engine score 17)"}
        msgs, _ = oh._phase50_install_minimal_messages(
            "shaadi kab hogi?",
            _sample_kundli(), "hn", bm,
            req_id="m-fallback",
        )
        user_msg = msgs[1]["content"]
        self.assertIn("Marriage verdict: Vivah patience zaroori", user_msg)
        # No clean MARRIAGE_FACTS block (no obj available)
        self.assertNotIn("MARRIAGE_FACTS:", user_msg)

    def test_unrelated_question_strips_marriage_and_wealth(self):
        """A general/career question must NOT leak marriage or wealth
        facts even if the build_meta has them."""
        bm = {"marriage_verdict_obj": _marriage_obj_clear(),
              "wealth_verdict_obj":   _wealth_obj_strong()}
        msgs, _ = oh._phase50_install_minimal_messages(
            "mera career kaisi hogi?",
            _sample_kundli(), "hn", bm,
            req_id="general-test",
        )
        user_msg = msgs[1]["content"]
        self.assertNotIn("MARRIAGE_FACTS:", user_msg)
        self.assertNotIn("WEALTH_FACTS:", user_msg)
        self.assertNotIn("Marriage verdict:", user_msg)
        self.assertNotIn("Wealth verdict:", user_msg)

    def test_question_about_both_marriage_and_wealth_emits_both(self):
        bm = {"marriage_verdict_obj": _marriage_obj_clear(),
              "wealth_verdict_obj":   _wealth_obj_strong()}
        msgs, _ = oh._phase50_install_minimal_messages(
            "marriage ke baad wealth kaisi rahegi?",
            _sample_kundli(), "hn", bm,
            req_id="both-test",
        )
        user_msg = msgs[1]["content"]
        self.assertIn("MARRIAGE_FACTS:", user_msg)
        self.assertIn("WEALTH_FACTS:", user_msg)

    def test_empty_question_keeps_legacy_one_liners(self):
        """Backward compat: when called with empty question
        (existing unit-test fixture path), legacy 1-liners still emit."""
        bm = {"marriage_verdict_block": "Vivah promised\n(score 70)",
              "wealth_verdict_obj":     {"verdict": "Stable", "bucket": "moderate"},
              "love_verdict_obj":       {"verdict": "L"},
              "career_verdict_obj":     {"verdict": "C"}}
        out = oh._phase50_extract_verdict_facts(bm, question="")
        self.assertIn("Marriage verdict: Vivah promised", out)
        self.assertIn("Wealth verdict: Stable (moderate)", out)
        self.assertIn("Love verdict: L", out)
        self.assertIn("Career verdict: C", out)
        # No clean blocks when no question routing
        self.assertNotIn("MARRIAGE_FACTS:", out)
        self.assertNotIn("WEALTH_FACTS:", out)


# ───────────────────────── Import smoke ─────────────────────────

class TestPhase58ImportSmoke(unittest.TestCase):

    def test_all_phase58_helpers_callable(self):
        for fn_name in ["_phase58_is_marriage_question",
                        "_phase58_is_wealth_question_p58",
                        "_phase58_format_marriage_facts_block",
                        "_phase58_format_wealth_facts_block"]:
            self.assertTrue(hasattr(oh, fn_name), f"missing {fn_name}")
            self.assertTrue(callable(getattr(oh, fn_name)), f"{fn_name} not callable")


if __name__ == "__main__":
    unittest.main()

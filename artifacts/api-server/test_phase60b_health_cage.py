"""Phase 6.0b — HEALTH NARRATOR CAGE tests.

Two fixes covered here:

  1. ENGINE-TAG NEUTRALIZATION (`_phase60b_neutralize_triggers`):
     medical-noun engine tags (vitality_dip / weakness / infection /
     hormonal / metabolic / vulnerability / nervous) project to safer
     phase-descriptor tokens (extra_care / balance / stress) BEFORE
     they reach the FACTS block. Engine internals stay unchanged.

  2. EXPLAIN-MODE SHORT-CIRCUIT (`_phase60b_is_health_explain_followup`
     + `_phase60b_health_explain_text`): "kaise check kiya?" follow-ups
     to a health question return a deterministic engine pipeline
     answer, NOT a generic Vedic textbook reply.

Both behaviours are reversible via env flags
(PHASE60B_NEUTRALIZE_TAGS / PHASE60B_EXPLAIN_MODE — default "1" = ON).

Test invariants this file locks:
  - Forbidden vocab list expanded with the symptom/trajectory nouns
    user flagged: vitality / weakness / fatigue / infection / hormonal
    / chronic / mental / nervous / metabolic / vulnerability + cousins.
  - Neutralizer maps the worst offenders to safer tokens; safe tokens
    pass through unchanged.
  - `_phase60_health_key_triggers` calls the neutralizer at the end so
    medical tokens cannot leak into the FACTS block.
  - Scrubber strips sentences with the new forbidden words (since they
    no longer appear in `key_triggers` after neutralization).
  - Explain-mode detector requires BOTH explain phrasing AND health
    context in recent history — false positives on bare explain Qs
    or non-health follow-ups would be confusing.
  - Explain-mode emits Hinglish by default, English when lang explicit.
  - Env-flag OFF restores legacy behaviour for both helpers.
"""

import os
import re
import importlib

import openai_helper as oh


# ─────────────────────────────────────────────────────────────────────────────
# 1) Forbidden vocab expansion
# ─────────────────────────────────────────────────────────────────────────────


class TestForbiddenVocabExpansion:
    """Phase 6.0b adds 23 new forbidden words to the original 5.

    The list MUST contain the user-flagged symptom/trajectory nouns —
    if any of these are removed, narration drift on health surface
    silently re-opens.
    """

    REQUIRED_NEW = [
        "vitality", "weakness", "fatigue", "tiredness", "exhaustion",
        "lethargy", "drowsiness", "dizziness", "ailment", "illness",
        "sickness", "infection", "inflammation", "immunity", "immune",
        "disease", "vigor", "vigour", "stamina", "nervous",
        "metabolic", "vulnerability", "vulnerable",
    ]

    REQUIRED_ORIGINAL = [
        "hormonal", "chronic", "mental", "emotional", "internal imbalance",
    ]

    def test_all_phase60_originals_preserved(self):
        for w in self.REQUIRED_ORIGINAL:
            assert w in oh._PHASE60_FORBIDDEN_HEALTH_VOCAB, (
                f"original Phase 6.0 vocab {w!r} must remain in "
                f"_PHASE60_FORBIDDEN_HEALTH_VOCAB"
            )

    def test_phase60b_new_vocab_present(self):
        for w in self.REQUIRED_NEW:
            assert w in oh._PHASE60_FORBIDDEN_HEALTH_VOCAB, (
                f"Phase 6.0b vocab {w!r} missing — user-flagged drift "
                f"will re-open without it"
            )

    def test_forbidden_re_compiles_and_matches(self):
        # Sanity — the regex compiled at import time matches each word
        for w in self.REQUIRED_NEW + self.REQUIRED_ORIGINAL:
            sentence = f"This sentence has {w} in it."
            assert oh._PHASE60_FORBIDDEN_RE.search(sentence), (
                f"_PHASE60_FORBIDDEN_RE failed to match {w!r}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# 2) Engine-tag neutralizer
# ─────────────────────────────────────────────────────────────────────────────


class TestNeutralizer:
    """`_phase60b_neutralize_triggers` projects medical engine tags
    to safer narrator tokens BEFORE they reach the FACTS block."""

    def test_medical_tokens_neutralized(self):
        out = oh._phase60b_neutralize_triggers(
            ["vitality_dip", "weakness", "infection", "hormonal",
             "metabolic", "vulnerability", "nervous"]
        )
        # All medical tokens should be gone
        assert "vitality_dip" not in out
        assert "weakness" not in out
        assert "infection" not in out
        assert "hormonal" not in out
        assert "metabolic" not in out
        assert "vulnerability" not in out
        assert "nervous" not in out
        # And mapped to safe tokens
        assert "extra_care" in out  # vitality_dip + weakness + infection + vulnerability
        assert "balance" in out     # hormonal + metabolic
        assert "stress" in out      # nervous

    def test_safe_tokens_pass_through(self):
        # Tokens already in safe form should be returned unchanged
        out = oh._phase60b_neutralize_triggers(
            ["heat", "stress", "sudden", "hidden", "chronic", "energy"]
        )
        assert out == ["heat", "stress", "sudden", "hidden", "chronic", "energy"]

    def test_unknown_token_falls_through_lowercased(self):
        # Defensive: unknown tokens should pass through lowercased,
        # not raise. (If engine adds a new tag we'd surface it as-is.)
        out = oh._phase60b_neutralize_triggers(["MYSTERY_TAG"])
        assert out == ["mystery_tag"]

    def test_dedup_after_mapping(self):
        # vitality_dip and weakness BOTH map to extra_care — should
        # appear ONCE in output, not twice.
        out = oh._phase60b_neutralize_triggers(
            ["vitality_dip", "weakness", "infection"]
        )
        assert out == ["extra_care"]

    def test_preserves_order(self):
        # First-seen wins — relative order of distinct mapped tokens
        # must match input order.
        out = oh._phase60b_neutralize_triggers(
            ["heat", "vitality_dip", "stress", "hormonal"]
        )
        assert out == ["heat", "extra_care", "stress", "balance"]

    def test_non_string_entries_dropped(self):
        out = oh._phase60b_neutralize_triggers(
            ["heat", None, 42, "", "  ", "stress"]
        )
        assert out == ["heat", "stress"]

    def test_non_iterable_input_returns_empty(self):
        assert oh._phase60b_neutralize_triggers(None) == []
        assert oh._phase60b_neutralize_triggers("not_a_list") == []
        assert oh._phase60b_neutralize_triggers(42) == []

    def test_env_flag_off_returns_input_unchanged(self):
        try:
            os.environ["PHASE60B_NEUTRALIZE_TAGS"] = "0"
            out = oh._phase60b_neutralize_triggers(
                ["vitality_dip", "weakness", "heat"]
            )
            # Strings preserved verbatim, no neutralization
            assert out == ["vitality_dip", "weakness", "heat"]
        finally:
            os.environ.pop("PHASE60B_NEUTRALIZE_TAGS", None)


# ─────────────────────────────────────────────────────────────────────────────
# 3) FACTS-block integration — neutralized triggers reach the prompt
# ─────────────────────────────────────────────────────────────────────────────


class TestKeyTriggersIntegration:
    """`_phase60_health_key_triggers` must call neutralizer so the
    HEALTH_FACTS block exposes only safe narrator tokens."""

    def test_general_wellness_bucket_projects_to_extra_care(self):
        # general_wellness bucket → "vitality_dip" tag → extra_care after
        # neutralization
        v = {
            "bucket": "general_wellness",
            "verdict": "yellow_wait",
            "top_concerns": [],
            "top_supportive": [],
            "timing_window": {},
        }
        triggers = oh._phase60_health_key_triggers(v)
        assert "vitality_dip" not in triggers
        assert "extra_care" in triggers

    def test_recovery_bucket_projects_to_extra_care(self):
        v = {
            "bucket": "recovery_timing",
            "verdict": "yellow_wait",
            "top_concerns": [],
            "top_supportive": [],
            "timing_window": {},
        }
        triggers = oh._phase60_health_key_triggers(v)
        assert "weakness" not in triggers
        assert "extra_care" in triggers

    def test_female_repro_bucket_projects_to_balance(self):
        v = {
            "bucket": "female_reproductive",
            "verdict": "yellow_wait",
            "top_concerns": [],
            "top_supportive": [],
            "timing_window": {},
        }
        triggers = oh._phase60_health_key_triggers(v)
        assert "hormonal" not in triggers
        assert "balance" in triggers

    def test_top_concerns_layer_tags_neutralized(self):
        # L1 layer → vitality_dip → extra_care
        v = {
            "bucket": "general_wellness",
            "verdict": "yellow_wait",
            "top_concerns": [
                {"layer": "L1_lagna_first_house", "score": 5},
                {"layer": "L4_twelfth_house",     "score": 3},
                {"layer": "L11_venus_karaka",     "score": 2},
            ],
            "top_supportive": [],
            "timing_window": {},
        }
        triggers = oh._phase60_health_key_triggers(v)
        for bad in ("vitality_dip", "weakness", "hormonal"):
            assert bad not in triggers, (
                f"{bad!r} leaked through from top_concerns → triggers"
            )
        assert "extra_care" in triggers
        assert "balance" in triggers

    def test_facts_block_contains_no_medical_tokens(self):
        # End-to-end: feed engine-shaped output, render full FACTS block,
        # assert no medical noun tokens appear in the key_triggers line.
        v = {
            "bucket": "general_wellness",
            "verdict": "yellow_wait",
            "confidence": 80,
            "top_concerns": [
                {"layer": "L1_lagna_first_house", "score": 5},
                {"layer": "L11_venus_karaka",     "score": 4},
            ],
            "top_supportive": [],
            "timing_window": {"current": {"md": "Jupiter", "ad": "Venus"}},
            "brand_safety_warnings": [],
        }
        block = oh._phase60_format_health_facts_block(v)
        assert "key_triggers:" in block
        # Pull out the triggers line
        triggers_line = [
            ln for ln in block.split("\n")
            if ln.strip().startswith("- key_triggers:")
        ][0]
        for bad in ("vitality_dip", "weakness", "hormonal", "infection",
                    "metabolic", "vulnerability"):
            assert bad not in triggers_line, (
                f"{bad!r} leaked into FACTS block key_triggers line: "
                f"{triggers_line!r}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# 4) Scrubber catches the new forbidden words
# ─────────────────────────────────────────────────────────────────────────────


class TestScrubberCatchesNewVocab:
    """With Phase 6.0b vocab expansion + neutralization, the user-flagged
    leakage cases ('vitality dip', 'weakness ke chances') get stripped."""

    def test_vitality_dip_sentence_dropped(self):
        text = (
            "April-June 2026 mein aapki health thodi unstable reh sakti hai, "
            "jisme vitality dip aur weakness ke chances dikh rahe hain. "
            "Is dauran extra care zaroori ho sakta hai."
        )
        # key_triggers does NOT contain vitality / weakness — neutralizer
        # would have mapped them to extra_care. So scrubber should drop
        # the middle sentence.
        scrubbed, tel = oh._phase60_health_vocab_scrub(
            text, allowed_triggers=["extra_care"], overall_risk="fluctuating",
        )
        assert "vitality" not in scrubbed.lower()
        assert "weakness" not in scrubbed.lower()
        assert tel.get("dropped_sentences", 0) >= 1

    def test_infection_sentence_dropped(self):
        text = (
            "Aapki sehat is window mein stable hai. "
            "Infection ki possibility nazar aati hai. "
            "Doctor consult zaroor karein."
        )
        scrubbed, tel = oh._phase60_health_vocab_scrub(
            text, allowed_triggers=["extra_care"], overall_risk="fluctuating",
        )
        assert "infection" not in scrubbed.lower()
        assert tel.get("dropped_sentences", 0) >= 1

    def test_clean_answer_passes_through(self):
        text = (
            "Aapki sehat thodi unstable hai. "
            "Dhyaan rakhoge to major issue avoid ho jayega. "
            "Doctor consult zaroor karein."
        )
        scrubbed, tel = oh._phase60_health_vocab_scrub(
            text, allowed_triggers=["extra_care"], overall_risk="fluctuating",
        )
        # Nothing dropped, no fallback
        assert tel.get("dropped_sentences") == 0
        assert tel.get("fallback_used") is False


# ─────────────────────────────────────────────────────────────────────────────
# 5) Explain-mode detector
# ─────────────────────────────────────────────────────────────────────────────


class TestExplainModeDetector:
    """Detector requires BOTH explain phrasing AND health context."""

    HEALTH_HISTORY = [
        {"role": "user", "content": "Abhi meri health stable hai ya risky phase me hoon?"},
        {"role": "assistant", "content": "Aapki sehat thodi unstable hai..."},
    ]

    NON_HEALTH_HISTORY = [
        {"role": "user", "content": "Mera marriage kab hoga?"},
        {"role": "assistant", "content": "Marriage timing 2027 mein..."},
    ]

    def test_explain_phrasing_in_health_context_true(self):
        cases = [
            "Aur yeh tumne kaise bataya kya kya check kiya",
            "Hn mera kaise check kiya batao",
            "Kaise pata chala?",
            "How did you check this?",
            "How do you determine this?",
            "Steps batao",
            "Step by step explain karo",
            "Process kya hai?",
            "Method kya use kiya?",
        ]
        for q in cases:
            assert oh._phase60b_is_health_explain_followup(
                q, self.HEALTH_HISTORY,
            ), f"failed to detect explain-mode in {q!r}"

    def test_explain_phrasing_no_history_false(self):
        # Without history we cannot confirm health context — return False
        # (safe: fall back to LLM rather than emit engine-steps blindly).
        assert not oh._phase60b_is_health_explain_followup(
            "Kaise check kiya?", None,
        )
        assert not oh._phase60b_is_health_explain_followup(
            "Kaise check kiya?", [],
        )

    def test_explain_phrasing_non_health_context_false(self):
        # Recent context is marriage — explain-mode should NOT fire.
        assert not oh._phase60b_is_health_explain_followup(
            "Kaise check kiya?", self.NON_HEALTH_HISTORY,
        )

    def test_no_explain_phrasing_health_context_false(self):
        # Question is just a fresh non-explain Q; should not fire.
        assert not oh._phase60b_is_health_explain_followup(
            "Mera health kaisa rahega next month?", self.HEALTH_HISTORY,
        )

    def test_empty_question_false(self):
        assert not oh._phase60b_is_health_explain_followup("", self.HEALTH_HISTORY)
        assert not oh._phase60b_is_health_explain_followup(None, self.HEALTH_HISTORY)

    def test_assistant_only_history_false(self):
        # If only assistant turns mention health, that's not the user's
        # established context — should not fire.
        history = [
            {"role": "assistant", "content": "Your health is stable."},
        ]
        assert not oh._phase60b_is_health_explain_followup(
            "Kaise check kiya?", history,
        )

    def test_pronoun_branch_excludes_prognosis(self):
        """Architect-mandated regression: pronoun branch must NOT match
        prognosis questions like 'Iska treatment kaise hoga?' / 'Iska
        effect kaise rahega?'. Original `\\w*` wildcard between subject
        and `kaise` was too permissive and caused these false positives.
        """
        prognosis_negatives = [
            "Iska treatment kaise hoga?",
            "Iska effect kaise rahega?",
            "Iska result kaise milega?",
            "Iska remedy kaise lagega?",
            "Iska solution kaise hoga?",
            "Aap kaise ho?",        # casual "how are you", not explain
            "Yeh kaise hoga?",      # bare "how will this happen"
        ]
        for q in prognosis_negatives:
            assert not oh._phase60b_is_health_explain_followup(
                q, self.HEALTH_HISTORY,
            ), (
                f"prognosis question {q!r} wrongly matched explain-mode "
                "(the `kaise hoga / rahega / milega / lagega` future-tense "
                "branch must stay outside the explain pattern)"
            )

    def test_extra_explain_phrasings_match(self):
        """Architect-mandated coverage: high-frequency explain phrasings
        the user naturally reaches for that the initial 6.0b regex
        missed. These MUST match (else LLM falls back to generic Vedic
        textbook — the exact failure 6.0b prevents).
        """
        new_positives = [
            "Yeh kaise maloom hua?",
            "Ye kaise malum hua?",
            "Konsa method use kiya?",
            "Kaunsa method use kiya?",
            "Which method use kiya?",
            "Kaise analyse kiya?",
            "Kaise analyze kiya?",
            "Method use kiya kya?",
            "Yeh kaise samajh aaya?",
        ]
        for q in new_positives:
            assert oh._phase60b_is_health_explain_followup(
                q, self.HEALTH_HISTORY,
            ), (
                f"explain phrasing {q!r} did NOT match — would fall "
                "back to LLM and risk generic Vedic-textbook drift"
            )


# ─────────────────────────────────────────────────────────────────────────────
# 6) Explain-mode deterministic text
# ─────────────────────────────────────────────────────────────────────────────


class TestExplainText:

    def test_default_returns_hinglish(self):
        text = oh._phase60b_health_explain_text("")
        assert text == oh._PHASE60B_HEALTH_EXPLAIN_HI

    def test_hi_returns_hinglish(self):
        for code in ("hi", "hi-IN", "hindi", "HI", ""):
            assert oh._phase60b_health_explain_text(code).startswith(
                "Engine ne aapki health"
            )

    def test_en_returns_english(self):
        for code in ("en", "en-IN", "EN", "english"):
            assert oh._phase60b_health_explain_text(code).startswith(
                "The engine ran these steps"
            )

    def test_text_mentions_actual_engine_pipeline(self):
        # The text MUST reference the engine's actual computational
        # vocabulary, not generic Vedic textbook terms. This locks in
        # the user's spec ("Lagna check / 6th house / 8th-12th /
        # current dasha / final combine").
        for text in (
            oh._PHASE60B_HEALTH_EXPLAIN_HI,
            oh._PHASE60B_HEALTH_EXPLAIN_EN,
        ):
            low = text.lower()
            assert "lagna" in low
            assert "6th" in low
            assert "8th" in low
            assert "12th" in low
            assert "mahadasha" in low or "dasha" in low
            assert "transit" in low
            assert "verdict" in low
            assert "stable" in low
            assert "unstable" in low
            assert "fluctuating" in low

    def test_text_avoids_generic_textbook_phrases(self):
        # Anti-pattern check — these phrases marked the LLM-generated
        # generic explanation the user complained about.
        for text in (
            oh._PHASE60B_HEALTH_EXPLAIN_HI,
            oh._PHASE60B_HEALTH_EXPLAIN_EN,
        ):
            low = text.lower()
            # "Identify your Lagna" / "follow these steps" — generic
            assert "identify your lagna" not in low
            assert "follow these steps" not in low
            assert "navamsha (d9)" not in low
            assert "dashamsha (d10)" not in low


# ─────────────────────────────────────────────────────────────────────────────
# 7) Env-flag reversibility
# ─────────────────────────────────────────────────────────────────────────────


class TestEnvFlagReversibility:

    def test_neutralize_default_on(self):
        os.environ.pop("PHASE60B_NEUTRALIZE_TAGS", None)
        assert oh._phase60b_neutralize_tags_enabled() is True

    def test_neutralize_off_when_zero(self):
        try:
            os.environ["PHASE60B_NEUTRALIZE_TAGS"] = "0"
            assert oh._phase60b_neutralize_tags_enabled() is False
        finally:
            os.environ.pop("PHASE60B_NEUTRALIZE_TAGS", None)

    def test_explain_mode_default_on(self):
        os.environ.pop("PHASE60B_EXPLAIN_MODE", None)
        assert oh._phase60b_explain_mode_enabled() is True

    def test_explain_mode_off_when_zero(self):
        try:
            os.environ["PHASE60B_EXPLAIN_MODE"] = "0"
            assert oh._phase60b_explain_mode_enabled() is False
        finally:
            os.environ.pop("PHASE60B_EXPLAIN_MODE", None)

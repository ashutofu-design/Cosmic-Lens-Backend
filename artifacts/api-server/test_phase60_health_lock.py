"""Phase 6.0 — Health Narrator Lock tests.

Covers:
  - sentence-level scrub of forbidden vocab (hormonal, chronic, mental,
    emotional, internal imbalance) when NOT in key_triggers
  - allow-pass when forbidden word is literally in key_triggers
  - deterministic template fallback when scrub leaves text incoherent
  - env-flag gate (PHASE60_HEALTH_NARRATOR_LOCK="0" disables scrubber)
  - response_format string contains the Phase 6.0 LOCK clause
  - tone-rule update bans new abstract terms
  - non-health questions bypass the scrub entirely (smoke check)
"""
from __future__ import annotations

import os

import openai_helper as oh


# ── Pure scrubber unit tests ────────────────────────────────────────────


def test_forbidden_word_not_in_triggers_is_dropped() -> None:
    text = (
        "Aapki sehat is window mein generally stable rahegi. "
        "Hormonal imbalance ka indication hai. "
        "Doctor se consult karein zaroor."
    )
    out, tel = oh._phase60_health_vocab_scrub(text, allowed_triggers=[], overall_risk="stable")
    # "hormonal" is forbidden and not allowed → middle sentence dropped.
    assert "hormonal" not in out.lower()
    assert tel["dropped_sentences"] >= 1
    assert "hormonal" in tel["dropped_words"]


def test_forbidden_word_allowed_when_in_triggers() -> None:
    text = (
        "Aapki sehat is window mein stable hai. "
        "Hormonal balance par dhyaan dein. "
        "Doctor se consult karein zaroor."
    )
    # "hormonal" is in key_triggers → must NOT be scrubbed.
    out, tel = oh._phase60_health_vocab_scrub(
        text, allowed_triggers=["hormonal", "venus karaka"], overall_risk="stable",
    )
    assert "hormonal" in out.lower()
    assert tel["dropped_sentences"] == 0
    assert tel["fallback_used"] is False


def test_chronic_allowed_when_in_triggers() -> None:
    text = (
        "Saturn ke prabhav se chronic patterns dikh sakte hain. "
        "Routine self-care zaroori hai. Doctor se consult karein."
    )
    out, _tel = oh._phase60_health_vocab_scrub(
        text, allowed_triggers=["chronic", "saturn karaka"], overall_risk="fluctuating",
    )
    assert "chronic" in out.lower()


def test_template_fallback_fires_when_scrub_too_aggressive() -> None:
    # All 3 sentences contain forbidden words → ALL get dropped → fallback.
    text = (
        "Mental imbalance ka indication hai. "
        "Emotional ups-downs ho sakte hain. "
        "Internal imbalance par dhyaan dein."
    )
    out, tel = oh._phase60_health_vocab_scrub(
        text, allowed_triggers=[], overall_risk="sensitive",
    )
    assert tel["fallback_used"] is True
    # Must use sensitive-template
    assert out == oh._PHASE60_HEALTH_FALLBACK_TEMPLATES["sensitive"]
    assert "doctor" in out.lower()


def test_template_fallback_uses_correct_risk_template() -> None:
    text = "Mental imbalance hai. Emotional drift dikh raha hai."
    for risk in ("stable", "fluctuating", "sensitive"):
        out, tel = oh._phase60_health_vocab_scrub(
            text, allowed_triggers=[], overall_risk=risk,
        )
        assert tel["fallback_used"] is True
        assert out == oh._PHASE60_HEALTH_FALLBACK_TEMPLATES[risk]


def test_template_fallback_unknown_risk_defaults_to_fluctuating() -> None:
    text = "Mental imbalance hai. Emotional drift dikh raha hai."
    out, tel = oh._phase60_health_vocab_scrub(
        text, allowed_triggers=[], overall_risk="invalid_risk_label",
    )
    assert tel["fallback_used"] is True
    assert out == oh._PHASE60_HEALTH_FALLBACK_TEMPLATES["fluctuating"]


def test_clean_text_passes_through_unchanged() -> None:
    text = (
        "Aapki sehat is window mein stable rahegi. "
        "Routine self-care kaafi hai. Doctor consult zaroor karein."
    )
    out, tel = oh._phase60_health_vocab_scrub(text, allowed_triggers=[], overall_risk="stable")
    assert out == text
    assert tel["dropped_sentences"] == 0
    assert tel["fallback_used"] is False


def test_empty_or_invalid_input_is_safe() -> None:
    assert oh._phase60_health_vocab_scrub("", allowed_triggers=[])[0] == ""
    assert oh._phase60_health_vocab_scrub(None, allowed_triggers=[])[0] == ""  # type: ignore[arg-type]
    assert oh._phase60_health_vocab_scrub("   ", allowed_triggers=[])[0] == "   "


def test_case_insensitive_match() -> None:
    text = "Sehat stable hai. HORMONAL changes ka indication. Doctor consult karein."
    out, tel = oh._phase60_health_vocab_scrub(text, allowed_triggers=[], overall_risk="stable")
    assert "hormonal" not in out.lower()
    assert "hormonal" in tel["dropped_words"]


def test_multi_word_forbidden_phrase_caught() -> None:
    text = (
        "Sehat band hai. Internal imbalance ka indication hai. "
        "Doctor consult karein zaroor."
    )
    out, tel = oh._phase60_health_vocab_scrub(text, allowed_triggers=[], overall_risk="stable")
    assert "internal imbalance" not in out.lower()
    assert "internal imbalance" in tel["dropped_words"]


def test_hindi_danda_sentence_split() -> None:
    text = (
        "Sehat stable hai। "
        "Mental imbalance ka indication hai। "
        "Doctor consult karein zaroor।"
    )
    out, tel = oh._phase60_health_vocab_scrub(text, allowed_triggers=[], overall_risk="stable")
    assert "mental" not in out.lower()
    assert tel["dropped_sentences"] >= 1


# ── Env-flag gate ──────────────────────────────────────────────────────


def test_narrator_lock_default_on() -> None:
    os.environ.pop("PHASE60_HEALTH_NARRATOR_LOCK", None)
    assert oh._phase60_health_narrator_lock_enabled() is True


def test_narrator_lock_disabled_when_flag_zero() -> None:
    os.environ["PHASE60_HEALTH_NARRATOR_LOCK"] = "0"
    try:
        assert oh._phase60_health_narrator_lock_enabled() is False
    finally:
        os.environ.pop("PHASE60_HEALTH_NARRATOR_LOCK", None)


def test_narrator_lock_enabled_for_non_zero_values() -> None:
    for v in ("1", "true", "yes", "on", "anything"):
        os.environ["PHASE60_HEALTH_NARRATOR_LOCK"] = v
        try:
            assert oh._phase60_health_narrator_lock_enabled() is True, f"{v=}"
        finally:
            os.environ.pop("PHASE60_HEALTH_NARRATOR_LOCK", None)


# ── Prompt-side constraint strings ─────────────────────────────────────


def test_response_format_contains_phase60_lock_clause() -> None:
    rf = oh._PHASE60_HEALTH_RESPONSE_FORMAT
    assert "Phase 6.0 LOCK" in rf
    for word in ("hormonal", "chronic", "mental", "emotional", "internal imbalance"):
        assert word in rf, f"{word!r} missing from response_format constraint"
    assert "key_triggers" in rf


def test_tone_rules_fallback_bans_abstract_vocab() -> None:
    diagnosis_rule = oh._HEALTH_TONE_RULES_FALLBACK[1]
    assert "Phase 6.0" in diagnosis_rule
    for word in ("hormonal", "chronic", "mental", "emotional", "internal imbalance"):
        assert word in diagnosis_rule, f"{word!r} missing from tone_rules fallback"
    assert "key_triggers" in diagnosis_rule


def test_engine_tone_rules_match_fallback() -> None:
    """Engine source-of-truth and openai_helper fallback must agree."""
    from health_engine import HEALTH_TONE_RULES
    # Diagnosis rule (index 1) must carry the Phase 6.0 ban in BOTH places.
    assert "Phase 6.0" in HEALTH_TONE_RULES[1]
    for word in ("hormonal", "chronic", "mental", "emotional", "internal imbalance"):
        assert word in HEALTH_TONE_RULES[1], f"{word!r} missing from engine tone_rules"


# ── Forbidden-vocab tuple sanity ────────────────────────────────────────


def test_forbidden_vocab_set_is_exactly_the_five_terms() -> None:
    assert set(oh._PHASE60_FORBIDDEN_HEALTH_VOCAB) == {
        "hormonal", "chronic", "mental", "emotional", "internal imbalance",
    }


def test_fallback_templates_have_doctor_consult() -> None:
    for risk, tpl in oh._PHASE60_HEALTH_FALLBACK_TEMPLATES.items():
        assert "doctor" in tpl.lower(), f"{risk} template missing doctor consult"
        assert len(tpl) < 400, f"{risk} template too long for 2-3 line spec"


# ── extract_health_lock_context ────────────────────────────────────────


def test_extract_health_lock_context_handles_missing_meta() -> None:
    triggers, risk = oh._phase60_extract_health_lock_context(None)
    assert triggers == []
    assert risk == "fluctuating"

    triggers, risk = oh._phase60_extract_health_lock_context({})
    assert triggers == []
    assert risk == "fluctuating"

    triggers, risk = oh._phase60_extract_health_lock_context({"health_verdict_obj": None})
    assert triggers == []
    assert risk == "fluctuating"


def test_clean_one_sentence_text_does_not_fallback() -> None:
    """Architect-flagged regression: short clean text must NOT trigger
    the deterministic template fallback when nothing was scrubbed."""
    text = "Aapki sehat is window mein stable rahegi."
    out, tel = oh._phase60_health_vocab_scrub(text, allowed_triggers=[], overall_risk="stable")
    assert tel["fallback_used"] is False
    assert tel["dropped_sentences"] == 0
    assert out == text


def test_clean_two_sentence_text_does_not_fallback() -> None:
    text = "Aapki sehat stable hai. Doctor consult karein."
    out, tel = oh._phase60_health_vocab_scrub(text, allowed_triggers=[], overall_risk="stable")
    assert tel["fallback_used"] is False
    assert "stable" in out
    assert "doctor" in out.lower()


def test_partial_scrub_three_sentences_does_not_fallback() -> None:
    """3 sentences, 1 dropped, 2 kept → coherent enough, no fallback."""
    text = (
        "Aapki sehat stable hai. "
        "Hormonal indication hai. "
        "Doctor consult karein."
    )
    out, tel = oh._phase60_health_vocab_scrub(text, allowed_triggers=[], overall_risk="stable")
    assert tel["fallback_used"] is False
    assert tel["dropped_sentences"] == 1
    assert "hormonal" not in out.lower()
    assert "stable" in out
    assert "doctor" in out.lower()


def test_hindi_danda_no_space_splits() -> None:
    """Architect-flagged: `।Doctor` (no space) must split correctly."""
    text = "Mental imbalance hai।Doctor consult karein zaroor।"
    out, tel = oh._phase60_health_vocab_scrub(text, allowed_triggers=[], overall_risk="stable")
    # Mental sentence dropped, doctor sentence kept (or fallback fires)
    assert "mental" not in out.lower()
    assert tel["dropped_sentences"] >= 1


def test_newline_sentence_boundary_splits() -> None:
    text = "Aapki sehat stable hai.\nMental imbalance ka indication hai.\nDoctor consult karein."
    out, tel = oh._phase60_health_vocab_scrub(text, allowed_triggers=[], overall_risk="stable")
    assert "mental" not in out.lower()
    assert tel["dropped_sentences"] >= 1


def test_extract_health_lock_context_returns_list_and_str() -> None:
    bm = {"health_verdict_obj": {"verdict": "fluctuating", "snapshot": {}}}
    triggers, risk = oh._phase60_extract_health_lock_context(bm)
    assert isinstance(triggers, list)
    assert isinstance(risk, str)

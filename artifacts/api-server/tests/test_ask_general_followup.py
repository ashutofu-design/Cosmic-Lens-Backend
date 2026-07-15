"""Generic follow-up merge tests — Hinglish, English, Hindi."""
from __future__ import annotations

from ask_general_followup import (
    is_contextual_followup,
    is_generic_followup,
    resolve_general_followup_question,
)

_HISTORY = [
    {"role": "user", "text": "Mera job change kab hoga"},
    {"role": "assistant", "text": "4-6 mahine ruk jaayein — abhi switch risky hai."},
]

_HEALTH_HISTORY = [
    {"role": "user", "text": "Meri health kaisi rahegi"},
    {"role": "assistant", "text": "Overall vitality mixed — kuch zones pe dhyan."},
]


def test_hinglish_followup_merges():
    eff, is_fu = resolve_general_followup_question("Aur detail do", _HISTORY)
    assert is_fu
    assert "job change" in eff.lower()


def test_english_followup_merges():
    eff, is_fu = resolve_general_followup_question("Tell me more", _HISTORY)
    assert is_fu
    assert "job change" in eff.lower()


def test_hindi_devanagari_followup_merges():
    eff, is_fu = resolve_general_followup_question("और बताओ", _HISTORY)
    assert is_fu
    assert "job change" in eff.lower()


def test_english_not_clear_detected():
    assert is_generic_followup("I didn't understand, explain again")


def test_hindi_not_understood_detected():
    assert is_generic_followup("समझ नहीं आया")


def test_generic_followup_does_not_merge_vague_prior():
    history = [
        {"role": "user", "text": "Mere bare me kuch batao"},
        {"role": "assistant", "text": "Aapka lagna..."},
    ]
    eff, is_fu = resolve_general_followup_question("Aur detail do", history)
    assert not is_fu
    assert eff.lower().startswith("aur")


def test_health_improve_followup_merges_prior_topic():
    assert is_contextual_followup("kab improve hogi?")
    eff, is_fu = resolve_general_followup_question("kab improve hogi?", _HEALTH_HISTORY)
    assert is_fu
    assert "health" in eff.lower()
    assert "improve" in eff.lower()


def test_health_deixis_followup_merges():
    eff, is_fu = resolve_general_followup_question("iske baare me aur batao", _HEALTH_HISTORY)
    assert is_fu
    assert "health" in eff.lower()


def test_health_remedy_followup_merges():
    eff, is_fu = resolve_general_followup_question("upay kya hai?", _HEALTH_HISTORY)
    assert is_fu
    assert "health" in eff.lower()
    assert "upay" in eff.lower()


def test_cross_domain_followup_does_not_merge():
    eff, is_fu = resolve_general_followup_question(
        "mera career kab change hoga",
        _HEALTH_HISTORY,
    )
    assert not is_fu


def test_contextual_without_history_stays_raw():
    eff, is_fu = resolve_general_followup_question("kab improve hogi?", [])
    assert not is_fu
    assert eff == "kab improve hogi?"

"""Tests for general Ask typo normalization and scope gate."""
from ask_question_normalize import looks_like_personal_life_question, prepare_ask_question
from ask_scope_gate import assess_ask_scope


def test_normalize_lagna_typos():
    assert prepare_ask_question("mera lagnaa kya he") == "mera lagna kya hai"
    assert prepare_ask_question("mera lagan kya ho") == "mera lagna kya hai"


def test_normalize_life_domain_typos():
    assert "shaadi" in prepare_ask_question("meri shaadii kab hogiii")
    assert "career" in prepare_ask_question("mera carrer kaisa he")
    assert "naukri" in prepare_ask_question("nokri kab lagegi")


def test_scope_allows_lagna_typo_question():
    v = assess_ask_scope("mera lagnaa kya he")
    assert v.allowed, v.reason


def test_scope_allows_career_typo():
    v = assess_ask_scope("mera carrer kaisa he")
    assert v.allowed, v.reason


def test_scope_allows_mera_shadi_kab_hoga():
    v = assess_ask_scope("mera shadi kab hoga")
    assert v.allowed, v.reason


def test_normalize_shadi():
    assert prepare_ask_question("mera shadi kab hoga") == "mera shaadi kab hoga"


def test_looks_like_personal_life():
    assert looks_like_personal_life_question("mera paisa kab milega")
    assert looks_like_personal_life_question("mujhe shaadi kab hogi")

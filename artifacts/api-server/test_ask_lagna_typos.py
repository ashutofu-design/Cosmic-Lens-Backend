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


def test_scope_allows_current_dasha_without_mera():
    v = assess_ask_scope("Abhi kaun sa dasha chal raha hai aur kya effect hai?")
    assert v.allowed, v.reason


def test_normalize_health_typos():
    assert "health" in prepare_ask_question("helth kaisi rahegii")
    assert "sehat" in prepare_ask_question("meri sehatt kaisa he")
    assert prepare_ask_question("tabiat kaisi hai") == "tabiyat kaisi hai"


def test_scope_allows_health_typo_implicit():
    v = assess_ask_scope("helth kaisi rahegi")
    assert v.allowed, v.reason


def test_scope_allows_health_kyahe_glued():
    v = assess_ask_scope("meri health kyahe")
    assert v.allowed, v.reason


def test_fuzzy_repair_health_typo():
    from ask_question_normalize import prepare_ask_question

    assert "health" in prepare_ask_question("helth kaisi rahegi")
    assert prepare_ask_question("hlt kaisi rahegi") == "health kaisi rahegi"

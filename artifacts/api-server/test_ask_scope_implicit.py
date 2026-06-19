"""Scope gate must allow real user asks without mera/meri."""
import pytest

from ask_scope_gate import assess_ask_scope


@pytest.mark.parametrize(
    "question",
    [
        "Abhi kaun sa dasha chal raha hai aur kya effect hai?",
        "Shadi kab hogi?",
        "Career kis direction me jau?",
        "8th house me Rahu kya result?",
        "D9 me moon kahan hai?",
        "Lagna kya hai?",
        "Meri health kaisi rahegi?",
        "Koi strong yoga hai kya?",
        "Sade sati chal rahi hai kya?",
        "Naukri kab lagegi?",
        "Love marriage hogi ya arranged?",
        "Business start karun ya risk hai?",
    ],
)
def test_implicit_asks_allowed_without_mera(question):
    v = assess_ask_scope(question)
    assert v.allowed, f"{question!r} blocked as {v.reason}"


@pytest.mark.parametrize(
    "question",
    [
        "who invented astrology",
        "astrology kya hai matlab",
        "president of india kaun hai",
        "python function likho",
        "biryani recipe batao",
        "match kaun jeetega aaj",
    ],
)
def test_off_topic_still_blocked(question):
    v = assess_ask_scope(question)
    assert not v.allowed, f"{question!r} should be blocked"

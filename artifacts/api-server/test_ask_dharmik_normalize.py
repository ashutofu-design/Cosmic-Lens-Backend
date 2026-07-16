"""Typo normalization for colloquial personal asks."""

from ask_question_normalize import prepare_ask_question
from ask_scope_gate import assess_ask_scope


def test_kya_me_normalizes_to_main():
    assert prepare_ask_question("kya me dharmik hun") == "kya main dharmik hai"


def test_dharmik_question_allowed_even_if_llm_not_personal(monkeypatch):
    monkeypatch.setattr(
        "ask_scope_llm.classify_ask_scope_llm",
        lambda *_args, **_kwargs: {
            "allowed": False,
            "reason": "not_personal",
            "cleaned_question": "kya main dharmik hai",
            "confidence": 0.95,
            "source": "llm",
        },
    )
    v = assess_ask_scope("kya me dharmik hun")
    assert v.allowed, v.reason

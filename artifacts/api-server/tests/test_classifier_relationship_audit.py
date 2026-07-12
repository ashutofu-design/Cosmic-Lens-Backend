"""Classifier fixes for relationship audit questions 5 and 10."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_mr.classifier import classify_mr_archetype


@pytest.mark.parametrize(
    "question,expected",
    [
        ("Kya partner cheat kar raha hai?", "secret_relationship"),
        ("Kya main is rishte me rahun?", "relationship_decisions"),
    ],
)
def test_relationship_audit_classifier(question, expected):
    assert classify_mr_archetype(question) == expected

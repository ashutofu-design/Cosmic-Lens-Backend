"""Tests for unified relationship narrator master rules."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_mr.relationship_narrator import (
    RELATIONSHIP_NARRATOR_RULES,
    build_relationship_narrator_system_prompt,
)


def test_relationship_narrator_rules_constant():
    assert "Cosmic Lens Relationship Narrator" in RELATIONSHIP_NARRATOR_RULES
    assert "ENGINE_JSON" in RELATIONSHIP_NARRATOR_RULES
    assert "Never become the astrologer yourself" in RELATIONSHIP_NARRATOR_RULES


def test_build_prompt_includes_master_rules():
    prompt = build_relationship_narrator_system_prompt(
        chart_text="VERDICT: loyal pattern\nCONFIDENCE: high",
        question="Mera bf loyal hai?",
        reply_lang="hn",
        engine_result=None,
    )
    assert RELATIONSHIP_NARRATOR_RULES.splitlines()[0] in prompt
    assert "ENGINE_JSON:" in prompt
    assert "Mera bf loyal hai?" in prompt
    assert "loyal pattern" in prompt

"""Tests for numerology name Ask engine."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_numerology import (
    extract_dob_from_question,
    extract_name_from_question,
    is_numerology_name_question,
    run_numerology_name_engine,
)

_USER_Q = (
    "mere name ashutosh kumar swain he kya numerlogy ke anusar sahi he ya change chahiye "
    "29-10-1999 mera dob he"
)


def test_numerology_question_detected() -> None:
    assert is_numerology_name_question(_USER_Q)
    assert extract_name_from_question(_USER_Q) == "Ashutosh Kumar Swain"
    assert extract_dob_from_question(_USER_Q) == "1999-10-29"


def test_numerology_engine_runs() -> None:
    result = run_numerology_name_engine(_USER_Q)
    assert result.archetype == "name_correction"
    assert result.checks.get("driver") == 2
    assert result.checks.get("conductor") == 4
    assert result.checks.get("harmony_score") is not None
    assert any("LOCKED_PICK" in s for s in (result.summary or []))
    assert len(result.evidence) >= 3
    payload = result.to_narrator_payload()
    assert "Driver" in payload or "driver" in payload.lower()


def test_passthrough_has_numerology_slice() -> None:
    from ask_hard_guards import passthrough_has_domain_engine_facts

    result = run_numerology_name_engine(_USER_Q)
    assert passthrough_has_domain_engine_facts(
        slice_meta={
            "slice": "numerology_engine_v1",
            "verdict": result.verdict,
            "evidence": result.evidence,
            "checks": result.checks,
        },
    )

"""Tests — universal timing fallback (only when no dedicated engine)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.timing_router import resolve_timing_domain, run_timing_engine
from event_timing.universal.topic_atlas import DOMAINS_WITH_DEDICATED_ENGINE
from event_timing.universal.universal_timing_v1 import (
    compute_universal_window,
    format_universal_timing_for_prompt,
)

_MIN_KUNDLI = {
    "ascendant": "Leo",
    "planets": [
        {"name": "Sun", "house": 1, "sign": "Leo"},
        {"name": "Moon", "house": 5, "sign": "Sagittarius"},
        {"name": "Mars", "house": 9, "sign": "Aries"},
        {"name": "Mercury", "house": 2, "sign": "Virgo"},
        {"name": "Jupiter", "house": 11, "sign": "Gemini"},
        {"name": "Venus", "house": 3, "sign": "Libra"},
        {"name": "Saturn", "house": 7, "sign": "Aquarius"},
        {"name": "Rahu", "house": 5, "sign": "Sagittarius"},
        {"name": "Ketu", "house": 11, "sign": "Gemini"},
    ],
    "dashas": [
        {
            "lord": "Jupiter",
            "start": "2020-01-01",
            "end": "2036-01-01",
            "subDashas": [
                {
                    "lord": "Saturn",
                    "start": "2024-01-01",
                    "end": "2026-06-01",
                    "subDashas": [
                        {"lord": "Mercury", "start": "2025-01-01", "end": "2025-06-01"},
                    ],
                },
            ],
        },
    ],
}


def test_lottery_routes_to_universal_not_skipped() -> None:
    dom, bkt, is_t = resolve_timing_domain("Lottery kab lagegi?")
    assert is_t
    assert dom == "universal"
    assert bkt == "lottery_speculation"


def test_fame_still_uses_dedicated_engine() -> None:
    dom, _, is_t = resolve_timing_domain("Mera content kab viral hoga?")
    assert is_t
    assert dom == "fame"
    assert dom != "universal"


def test_network_still_uses_dedicated_engine() -> None:
    dom, _, is_t = resolve_timing_domain("Bade log meri help kab karenge?")
    assert is_t
    assert dom == "network"


def test_universal_engine_produces_verdict() -> None:
    result = compute_universal_window(
        _MIN_KUNDLI,
        question="Pet dog kab adopt karun?",
        bucket="pet_animal",
    )
    assert result.get("domain") == "universal"
    assert result.get("fallback_mode") is True
    assert result.get("verdict")
    assert result.get("verdict") != "UNKNOWN"
    assert "pet_animal" in (result.get("resolved_topics") or [])


def test_universal_router_wiring() -> None:
    ctx = run_timing_engine(
        "Lottery kab lagegi?",
        _MIN_KUNDLI,
        {},
        {},
        None,
    )
    assert ctx.demand.domain == "universal"
    assert ctx.engine_status == "ready"
    assert ctx.verdict
    block = format_universal_timing_for_prompt(ctx.raw or {})
    assert "UNIVERSAL TIMING ENGINE" in block


def test_dedicated_domains_set_complete() -> None:
    assert "fame" in DOMAINS_WITH_DEDICATED_ENGINE
    assert "network" in DOMAINS_WITH_DEDICATED_ENGINE
    assert "universal" not in DOMAINS_WITH_DEDICATED_ENGINE


def test_llm_finance_hint_does_not_steal_lottery() -> None:
    dom, bkt, is_t = resolve_timing_domain(
        "Lottery kab lagegi?",
        {"domain": "finance", "is_timing": True},
    )
    assert is_t
    assert dom == "universal", f"got {dom}/{bkt}"
    assert bkt == "lottery_speculation"


def test_general_life_event_fallback_bucket() -> None:
    dom, bkt, is_t = resolve_timing_domain("Meri zindagi me bada badlav kab aayega?")
    assert is_t
    assert dom == "universal"
    assert bkt == "general_life_event"

"""Tests — friends, network & circle timing (11H, Mercury/Rahu)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_network import classify_network_timing_bucket, is_network_timing_question
from event_timing.network.network_timing_v1 import (
    compute_network_window,
    format_network_timing_for_prompt,
)
from event_timing.timing_router import resolve_timing_domain, run_timing_engine

_MIN_KUNDLI = {
    "ascendant": "Gemini",
    "planets": [
        {"name": "Sun", "house": 3, "sign": "Leo"},
        {"name": "Moon", "house": 11, "sign": "Aries"},
        {"name": "Mars", "house": 6, "sign": "Scorpio"},
        {"name": "Mercury", "house": 11, "sign": "Aquarius"},
        {"name": "Jupiter", "house": 7, "sign": "Sagittarius"},
        {"name": "Venus", "house": 5, "sign": "Libra"},
        {"name": "Saturn", "house": 9, "sign": "Aquarius"},
        {"name": "Rahu", "house": 11, "sign": "Aquarius"},
        {"name": "Ketu", "house": 5, "sign": "Leo"},
    ],
    "dashas": [
        {
            "lord": "Mercury",
            "start": "2020-01-01",
            "end": "2037-01-01",
            "subDashas": [
                {
                    "lord": "Rahu",
                    "start": "2024-06-01",
                    "end": "2027-02-01",
                    "subDashas": [
                        {"lord": "Mercury", "start": "2025-01-01", "end": "2025-08-01"},
                        {"lord": "Jupiter", "start": "2025-08-01", "end": "2026-03-01"},
                    ],
                },
            ],
        },
    ],
}

CASES = [
    (
        "Bade aur influential logo se network kab banega?",
        "network",
        "influential_network",
    ),
    (
        "Kab bade log meri help karenge?",
        "network",
        "influential_network",
    ),
    (
        "Dosto se chal raha dhoka ya misunderstanding kab khatam hogi?",
        "network",
        "friend_conflict",
    ),
    (
        "Karan bina dushmani jo chal rahi hai wo kab shant hogi?",
        "network",
        "enmity_peace",
    ),
    (
        "Meri social circle kab badegi?",
        "network",
        "influential_network",
    ),
]


@pytest.mark.parametrize("question,domain,bucket", CASES)
def test_network_routing(question: str, domain: str, bucket: str) -> None:
    assert is_network_timing_question(question)
    assert classify_network_timing_bucket(question) == bucket
    dom, bkt, is_timing = resolve_timing_domain(question)
    assert is_timing, question
    assert dom == domain, question
    assert bkt == bucket, question


def test_network_engine_runs() -> None:
    result = compute_network_window(
        _MIN_KUNDLI,
        question="Network kab banega?",
        bucket="influential_network",
    )
    assert result.get("domain") == "network"
    assert result.get("verdict")
    assert result.get("verdict") != "UNKNOWN"
    factors = " ".join(result.get("factors") or [])
    assert "Mercury" in factors or "Rahu" in factors or "11L" in factors or "11H" in factors


def test_network_dasha_kp_sync() -> None:
    result = compute_network_window(_MIN_KUNDLI, bucket="influential_network")
    assert result.get("dasha_running_now")
    assert "kp_dasha_sync" in result


def test_network_router_engine_wiring() -> None:
    ctx = run_timing_engine(
        "Bade log meri help kab karenge?",
        _MIN_KUNDLI,
        {},
        {},
        None,
    )
    assert ctx.demand.domain == "network"
    assert ctx.engine_status == "ready"
    block = format_network_timing_for_prompt(ctx.raw or {})
    assert "FRIENDS & NETWORK TIMING ENGINE" in block


def test_friend_dhoka_not_love() -> None:
    dom, bkt, is_t = resolve_timing_domain(
        "Dosto se chal raha dhoka kab khatam hogi?",
    )
    assert is_t
    assert dom == "network"
    assert bkt == "friend_conflict"


def test_enmity_not_litigation_without_court() -> None:
    dom, bkt, is_t = resolve_timing_domain(
        "Karan bina dushmani kab shant hogi?",
    )
    assert is_t
    assert dom == "network"
    assert bkt == "enmity_peace"

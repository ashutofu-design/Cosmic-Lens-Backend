"""100-question spiritual routing audit — engine, dasha, KP."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.timing_router import detect_timing_intent, resolve_timing_domain, run_timing_engine
from scripts.spiritual_100_cases import ALL_CASES

KUNDLI = {
    "ascendant": "Sagittarius",
    "ascendantDeg": 255.0,
    "planets": [
        {"name": "Moon", "sign": "Scorpio", "house": 12, "longitude": 225.0},
        {"name": "Saturn", "sign": "Virgo", "house": 10, "longitude": 165.0},
        {"name": "Mars", "sign": "Cancer", "house": 8, "longitude": 105.0},
        {"name": "Venus", "sign": "Leo", "house": 9, "longitude": 135.0},
        {"name": "Mercury", "sign": "Aries", "house": 5, "longitude": 15.0},
        {"name": "Jupiter", "sign": "Pisces", "house": 4, "longitude": 345.0},
        {"name": "Rahu", "sign": "Aquarius", "house": 3, "longitude": 315.0},
        {"name": "Ketu", "sign": "Leo", "house": 9, "longitude": 135.0},
        {"name": "Sun", "sign": "Capricorn", "house": 2, "longitude": 285.0},
    ],
    "dashas": [
        {
            "lord": "Jupiter",
            "start": "2024-01-01",
            "end": "2040-12-31",
            "subDashas": [
                {
                    "lord": "Ketu",
                    "start": "2025-01-01",
                    "end": "2027-12-31",
                    "subDashas": [
                        {"lord": "Mercury", "start": "2025-01-01", "end": "2025-07-01"},
                        {"lord": "Moon", "start": "2025-07-01", "end": "2026-01-01"},
                        {"lord": "Mars", "start": "2026-01-01", "end": "2026-07-01"},
                    ],
                },
            ],
        },
    ],
}

KP = {
    "cusps": [
        {"house": 8, "subLord": "Ketu"},
        {"house": 9, "subLord": "Jupiter"},
        {"house": 12, "subLord": "Moon"},
    ],
}

_WHEN_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+se|when|kis\s+(?:mahine|saal|year|month|date|turning\s+point)|"
    r"kis\s+dasha|dasha\s+me|gochar|transit|trigger|kitne\s+mahine|"
    r"active\s+honge|shuru\s+honge|approve|prapt|ban\s+raha|chal\s+rahi"
    r")\b"
)


def _kind(q: str) -> str:
    if re.search(r"(?ix)\bkya\b", q) and not _WHEN_RX.search(q):
        return "static"
    return "timing"


TIMING_CASES = [(cat, q) for cat, _dom, q in ALL_CASES if _kind(q) == "timing"]
STATIC_CASES = [(cat, q) for cat, _dom, q in ALL_CASES if _kind(q) == "static"]


@pytest.mark.parametrize("category,question", TIMING_CASES)
def test_timing_questions_route_spiritual(category: str, question: str) -> None:
    dom, bucket, is_t = resolve_timing_domain(question)
    assert is_t, f"expected timing: {question[:80]}"
    assert dom == "spiritual", f"got {dom} bucket={bucket}: {question[:80]}"
    assert bucket in (
        "guru_deeksha",
        "occult_learning",
        "pilgrimage",
        "inner_peace",
        "karma_past_life",
        "general_spiritual",
    )


@pytest.mark.parametrize("category,question", STATIC_CASES)
def test_static_questions_route_spiritual_gap(category: str, question: str) -> None:
    from ask_gap_dispatch import detect_gap_static_key

    assert detect_gap_static_key(question) == "spiritual", f"gap!=spiritual: {question[:80]}"


@pytest.mark.parametrize("category,question", STATIC_CASES)
def test_static_kya_not_timing(category: str, question: str) -> None:
    dom, _, is_t = resolve_timing_domain(question)
    assert not is_t, f"static kya flagged timing → {dom}: {question[:80]}"
    assert not detect_timing_intent(question)


def test_spiritual_engine_dasha_kp_fields() -> None:
    ctx = run_timing_engine(
        "Meri life me sahi Guru kab aayega?",
        KUNDLI,
        {},
        KP,
        None,
    )
    assert ctx.demand.domain == "spiritual"
    assert ctx.engine_status == "ready"
    raw = ctx.raw or {}
    assert raw.get("verdict") not in (None, "", "UNKNOWN")

    run = raw.get("dasha_running_now") or {}
    assert run.get("md") and run.get("ad")
    assert run.get("is_running_now") is True
    assert run.get("start_iso") and run.get("end_iso")

    sync = raw.get("kp_dasha_sync") or {}
    assert sync.get("cusp_sub_lords")
    assert "active_now" in sync and "upcoming" in sync

    cw = raw.get("current_window") or {}
    if cw:
        assert "is_active_now" in cw
        assert "kp_csl_hits" in cw
    assert len(raw.get("next_3_windows") or []) >= 1
    for w in raw.get("next_3_windows") or []:
        assert "is_active_now" in w
        assert "is_upcoming" in w

    kp_layer = raw.get("kp_layer") or {}
    assert kp_layer.get("cusps")
    factors = " ".join(raw.get("factors") or [])
    assert "STEP5a RUNNING_NOW" in factors
    assert "STEP1" in factors and "STEP5" in factors


def test_100_case_count() -> None:
    assert len(ALL_CASES) == 100

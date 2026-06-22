"""Phase 2 timing engine tests — property/education/litigation/love v1."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.education.education_timing_v1 import compute_education_window
from event_timing.litigation.litigation_timing_v1 import compute_litigation_window
from event_timing.love.love_timing_v1 import compute_love_window, format_love_timing_for_prompt
from event_timing.property.property_timing_v1 import compute_property_window
from event_timing.timing_router import format_timing_block, run_timing_engine

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7, "longitude": 75.0},
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
                    "lord": "Venus",
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


def test_property_engine_returns_window():
    raw = compute_property_window(SAMPLE_KUNDLI, {}, {}, None, "Ghar kab lun?")
    assert raw.get("verdict")
    assert raw.get("verdict") != "UNKNOWN"
    assert raw.get("domain") == "property"
    assert isinstance(raw.get("factors"), list)


def test_education_engine_returns_window():
    raw = compute_education_window(SAMPLE_KUNDLI, {}, {}, None, "Exam kab hoga?")
    assert raw.get("verdict")
    assert raw.get("bucket") in ("exam_success", "admission", "degree_completion", "higher_studies")


def test_litigation_engine_has_guards():
    raw = compute_litigation_window(SAMPLE_KUNDLI, {}, {}, None, "Bail kab milegi?")
    guards = raw.get("brand_safety_warnings") or []
    assert any("jail" in g.lower() or "lawyer" in g.lower() for g in guards)


def test_love_engine_tone_rules():
    raw = compute_love_window(SAMPLE_KUNDLI, {}, {}, None, "Patchup kab hoga?")
    block = format_love_timing_for_prompt(raw)
    assert "LOVE TIMING ENGINE" in block
    assert raw.get("love_tone_rules")


def test_router_wires_phase2_domains():
    for q, marker in (
        ("Registry kab hogi?", "PROPERTY TIMING ENGINE"),
        ("Admission kab hogi?", "EDUCATION TIMING ENGINE"),
        ("Case verdict kab aayega?", "LITIGATION TIMING ENGINE"),
        ("Patchup kab hoga?", "LOVE TIMING ENGINE"),
    ):
        ctx = run_timing_engine(q, SAMPLE_KUNDLI, {}, {}, None, {"is_timing": True})
        assert ctx.engine_status == "ready", f"{q} status={ctx.engine_status}"
        block = format_timing_block(ctx)
        assert marker in block, f"{q} block missing {marker}"

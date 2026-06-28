"""Ask integration — timing LOCKED blocks must pass hard-guard recognition."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_hard_guards import is_real_timing_engine_block, passthrough_has_domain_engine_facts
from event_timing.love.love_timing_v1 import compute_love_window, format_love_timing_for_prompt
from event_timing.vehicle.vehicle_timing_v1 import compute_vehicle_window, format_vehicle_timing_for_prompt
from event_timing.fame.fame_timing_v1 import compute_fame_window, format_fame_timing_for_prompt
from event_timing.network.network_timing_v1 import compute_network_window, format_network_timing_for_prompt
from event_timing.spiritual.spiritual_timing_v1 import compute_spiritual_window, format_spiritual_timing_for_prompt
from event_timing.timing_router import run_timing_engine
from event_timing.universal.universal_timing_v1 import compute_universal_window, format_universal_timing_for_prompt

_K = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Sun", "house": 10, "sign": "Virgo"},
        {"name": "Moon", "house": 5, "sign": "Aries"},
        {"name": "Mars", "house": 8, "sign": "Cancer"},
        {"name": "Mercury", "house": 5, "sign": "Aries"},
        {"name": "Jupiter", "house": 1, "sign": "Sagittarius"},
        {"name": "Venus", "house": 11, "sign": "Libra"},
        {"name": "Saturn", "house": 3, "sign": "Aquarius"},
        {"name": "Rahu", "house": 11, "sign": "Libra"},
        {"name": "Ketu", "house": 5, "sign": "Aries"},
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
                    "end": "2027-01-01",
                    "subDashas": [{"lord": "Mercury", "start": "2025-01-01", "end": "2025-06-01"}],
                },
            ],
        },
    ],
}


@pytest.mark.parametrize(
    "formatter,raw",
    [
        (format_fame_timing_for_prompt, compute_fame_window(_K, bucket="social_fame")),
        (format_spiritual_timing_for_prompt, compute_spiritual_window(_K, bucket="guru_deeksha")),
        (format_network_timing_for_prompt, compute_network_window(_K, bucket="influential_network")),
        (format_universal_timing_for_prompt, compute_universal_window(_K, question="Lottery kab?")),
    ],
)
def test_locked_blocks_recognized_by_ask_guard(formatter, raw) -> None:
    block = formatter(raw)
    assert is_real_timing_engine_block(block), block[:120]
    assert passthrough_has_domain_engine_facts(domain_timing_block=block)


def test_love_timing_v2_block_passes_ask_guard() -> None:
    raw = compute_love_window(_K, question="Mera love life kab shuru hoga")
    block = format_love_timing_for_prompt(raw, "Mera love life kab shuru hoga")
    assert block
    assert is_real_timing_engine_block(block), block[:160]
    assert passthrough_has_domain_engine_facts(domain_timing_block=block)


def test_vehicle_timing_block_passes_ask_guard() -> None:
    raw = compute_vehicle_window(_K, question="Main new car kab lunga")
    block = format_vehicle_timing_for_prompt(raw, "Main new car kab lunga")
    assert block
    assert is_real_timing_engine_block(block), block[:160]
    assert passthrough_has_domain_engine_facts(domain_timing_block=block)


def test_router_block_passes_ask_guard() -> None:
    ctx = run_timing_engine("Lottery kab lagegi?", _K, {}, {}, None)
    block = (ctx.raw or {}).get("_prompt_block") or ""
    assert is_real_timing_engine_block(block)
    assert "DUAL-TRACK" in block

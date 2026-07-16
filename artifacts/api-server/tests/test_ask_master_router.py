"""Tests for central ask_master_router."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_master_router import finalize_ask_route, guard_trait_only_blocks_timing, resolve_ask_route

_OFFICE_Q = (
    "Office mein ek ladki hai jise main bohot pasand karta hoon, par baat karne mein "
    "darr lagta hai. Kya mere chart mein abhi love approach karne ka koi shubh samay "
    "chal raha hai?"
)

_TRAIT_Q = "Meri shaadi kaisi hogi — partner kaisa dikhega?"


def test_office_approach_routes_love_timing():
    intent = {
        "domain": "love",
        "is_timing": True,
        "routed_domain": "love",
        "routed_timing": True,
        "mr_archetype": "one_sided_love",
    }
    route = resolve_ask_route(_OFFICE_Q, llm_intent=intent, llm_intent_admin=intent)
    assert route.is_timing is True
    assert route.path == "engine_timing"
    assert route.timing_engine_slice == "love_timing_v1"
    assert route.lock_timing is True
    assert route.mr_static is False


def test_trait_only_guard_blocks_timing():
    assert guard_trait_only_blocks_timing(_TRAIT_Q) is True
    route = resolve_ask_route(_TRAIT_Q, llm_intent={"domain": "marriage", "is_timing": True})
    assert route.is_timing is False
    assert route.path == "engine_static"


def test_finalize_patches_intent():
    intent = {"domain": "love", "is_timing": False}
    admin = {"domain": "love", "routed_timing": False}
    route = finalize_ask_route(_OFFICE_Q, llm_intent=intent, llm_intent_admin=admin)
    assert route.is_timing is True
    assert intent["is_timing"] is True
    assert admin["routed_timing"] is True
    assert admin.get("master_route", {}).get("path") == "engine_timing"


def test_registry_timing_without_llm():
    route = resolve_ask_route(_OFFICE_Q)
    assert route.is_timing is True
    assert route.timing_engine_slice == "love_timing_v1"


def test_trusted_static_dna_does_not_force_relationship_engine():
    admin = {
        "dna_routing_applied": True,
        "question_dna": {
            "source": "llm",
            "questions": [{
                "domain": "health",
                "bucket": "general_health",
                "timing": False,
            }],
        },
    }
    route = resolve_ask_route(
        "Meri health overall kaisi hai?",
        llm_intent={"domain": "health", "is_timing": False},
        llm_intent_admin=admin,
    )
    assert route.path == "engine_static"
    assert route.domain == "health"
    assert route.mr_static is False

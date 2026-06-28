"""Audit — 100 health real-life Q → engine family + archetype."""
from __future__ import annotations

from typing import Optional

from ask_health.health_registry import detect_health_archetype, is_health_static_question
from ask_health.timing_registry import classify_health_timing_bucket
from event_timing.timing_router import resolve_timing_domain
from health_focus_routing import detect_hard_guard, is_health_question


def classify_health_routing(question: str) -> dict[str, Optional[str]]:
    q = question or ""
    dom, bucket, is_timing = resolve_timing_domain(q)

    if dom == "health" and is_timing:
        return {
            "family": "health_timing",
            "archetype": classify_health_timing_bucket(q),
            "guard": None,
            "domain": dom,
            "bucket": bucket,
        }

    hard = detect_hard_guard(q)
    if hard:
        arch = detect_health_archetype(q) or hard.lower()
        return {
            "family": "health_hard_guard",
            "archetype": arch,
            "guard": hard,
            "domain": None,
            "bucket": None,
        }

    if is_health_static_question(q):
        arch = detect_health_archetype(q)
        return {
            "family": "health_static",
            "archetype": arch or "general_health",
            "guard": None,
            "domain": dom if is_timing else None,
            "bucket": bucket if is_timing else None,
        }

    if is_health_question(q):
        arch = detect_health_archetype(q)
        return {
            "family": "health_static",
            "archetype": arch or "general_health",
            "guard": None,
            "domain": dom,
            "bucket": bucket,
        }

    if is_timing and is_health_question(q):
        return {
            "family": "health_timing_gap",
            "archetype": detect_health_archetype(q),
            "guard": None,
            "domain": dom,
            "bucket": bucket,
        }

    if dom not in ("general", "") and is_timing:
        return {
            "family": f"cross_domain:{dom}",
            "archetype": detect_health_archetype(q),
            "guard": None,
            "domain": dom,
            "bucket": bucket,
        }

    return {
        "family": "llm",
        "archetype": detect_health_archetype(q),
        "guard": None,
        "domain": dom,
        "bucket": bucket,
    }


def family_label(route: dict) -> str:
    fam = route.get("family") or "?"
    if fam == "health_hard_guard":
        return f"hard_guard:{route.get('guard')}"
    if fam == "health_static":
        return f"static:{route.get('archetype')}"
    if fam == "health_timing":
        return "health_timing_v1"
    if fam == "health_timing_gap":
        return f"TIMING_GAP->{route.get('domain')}"
    return str(fam)

"""Audit — 100 litigation real-life Q → engine family + archetype."""
from __future__ import annotations

from typing import Optional

from ask_litigation.litigation_registry import (
    detect_litigation_archetype,
    is_death_penalty_crisis_question,
    is_litigation_static_question,
)
from ask_litigation.timing_registry import classify_litigation_timing_bucket
from event_timing.timing_router import resolve_timing_domain


def classify_litigation_routing(question: str) -> dict[str, Optional[str]]:
    q = question or ""
    dom, bucket, is_timing = resolve_timing_domain(q)

    if dom == "litigation" and is_timing:
        return {
            "family": "litigation_timing",
            "archetype": classify_litigation_timing_bucket(q),
            "guard": None,
            "domain": dom,
            "bucket": bucket,
        }

    if is_death_penalty_crisis_question(q):
        return {
            "family": "litigation_hard_guard",
            "archetype": detect_litigation_archetype(q) or "death_penalty",
            "guard": "REFUSE_DEATH_PENALTY",
            "domain": None,
            "bucket": None,
        }

    if is_litigation_static_question(q):
        arch = detect_litigation_archetype(q)
        return {
            "family": "litigation_static",
            "archetype": arch or "general_litigation",
            "guard": None,
            "domain": dom if is_timing else None,
            "bucket": bucket if is_timing else None,
        }

    if is_timing and dom not in ("general", ""):
        return {
            "family": f"cross_domain:{dom}",
            "archetype": detect_litigation_archetype(q),
            "guard": None,
            "domain": dom,
            "bucket": bucket,
        }

    return {
        "family": "llm",
        "archetype": detect_litigation_archetype(q),
        "guard": None,
        "domain": dom,
        "bucket": bucket,
    }


def family_label(route: dict) -> str:
    fam = route.get("family") or "?"
    if fam == "litigation_hard_guard":
        return f"hard_guard:{route.get('guard')}"
    if fam == "litigation_static":
        return f"static:{route.get('archetype')}"
    if fam == "litigation_timing":
        return "litigation_timing_v1"
    return str(fam)

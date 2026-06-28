"""Unified routing audit — which timing domain + engine module a question hits."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

from event_timing.timing_router import resolve_timing_domain

_MARRIAGE_RX = re.compile(
    r"(?ix)\b(shaadi|shadi|vivah|marriage|wedding|biwi|pati|patni|dulhan|dulha)\b"
)
_MARRIAGE_EVENT_RX = re.compile(
    r"(?ix)\b(engagement|roka|sagai|rishta\s+pakk|rishta\s+fix|delay\s+in\s+marriage)\b"
)
_TIMING_RX = re.compile(
    r"(?ix)\b(kab|when|milega|hoga|hogi|aayega|dasha|transit|gochar|kis\s+(saal|mahine))\b"
)

DOMAIN_ENGINES: dict[str, str] = {
    "marriage": "event_timing.marriage.marriage_engine_v2",
    "love": "event_timing.love.love_timing_engine_v1",
    "career": "event_timing.career.career_timing",
    "travel": "event_timing.travel.travel_engine_v1",
    "education": "event_timing.education.education_engine_v1",
    "children": "event_timing.children.children_engine_v1",
    "property": "event_timing.property.property_timing_v1",
    "vehicle": "event_timing.vehicle.vehicle_timing_v1",
    "litigation": "event_timing.litigation.litigation_engine_v1",
    "finance": "wealth_engine",
    "health": "health_engine",
    "general": "llm_only",
}


@dataclass(frozen=True)
class RoutingAudit:
    question: str
    is_timing: bool
    domain: str
    router_bucket: str
    sub_bucket: str
    engine: str
    notes: str = ""


def _love_scope(q: str) -> bool:
    try:
        from ask_love.timing_registry import _LOVE_SCOPE_RX  # type: ignore
        return bool(_LOVE_SCOPE_RX.search(q))
    except Exception:
        return False


def _is_love_static(q: str) -> bool:
    if _MARRIAGE_RX.search(q) or _MARRIAGE_EVENT_RX.search(q):
        return False
    try:
        from ask_love.timing_registry import _MARRIAGE_OVERRIDE_RX  # type: ignore
        if _MARRIAGE_OVERRIDE_RX.search(q):
            return False
    except Exception:
        pass
    return _love_scope(q)


def _classify_sub_bucket(domain: str, question: str, router_bucket: str) -> str:
    q = question or ""
    if domain == "love":
        if _TIMING_RX.search(q) or router_bucket == "timing":
            from event_timing.love.love_timing_engine_v1 import classify_love_timing_bucket
            return classify_love_timing_bucket(q)
        from event_timing.love.love_static_engine_v1 import classify_love_static_bucket
        return classify_love_static_bucket(q)
    if domain == "career":
        try:
            from ask_career.timing_registry import classify_career_timing_bucket
            return classify_career_timing_bucket(q)
        except Exception:
            return router_bucket
    if domain == "vehicle":
        from event_timing.vehicle.vehicle_timing_v1 import classify_vehicle_timing_bucket
        return classify_vehicle_timing_bucket(q)
    if domain == "property":
        from event_timing.property.property_timing_v1 import classify_property_timing_bucket
        return classify_property_timing_bucket(q)
    if domain == "marriage":
        return "timing"
    if domain == "travel":
        try:
            from ask_travel.travel_registry import detect_travel_archetype
            return detect_travel_archetype(q) or router_bucket
        except Exception:
            return router_bucket
    return router_bucket


def _resolve_static_domain(question: str) -> tuple[str, str]:
    """Non-timing deterministic engine routing (openai_helper priority sketch)."""
    q = question or ""
    if _MARRIAGE_RX.search(q) or _MARRIAGE_EVENT_RX.search(q):
        return "marriage", "static"
    try:
        from event_timing.love.milan_engine_v1 import is_milan_question
        if is_milan_question(q):
            return "love", "milan"
    except Exception:
        pass
    if _is_love_static(q):
        from event_timing.love.love_static_engine_v1 import classify_love_static_bucket
        return "love", classify_love_static_bucket(q)
    try:
        from ask_career.timing_registry import is_career_question
        if is_career_question(q):
            from event_timing.career.career_timing import classify_career_question
            return "career", classify_career_question(q)
    except Exception:
        pass
    return "general", "general"


def audit_question_routing(
    question: str,
    llm_intent: Optional[dict] = None,
) -> RoutingAudit:
    domain, router_bucket, is_timing = resolve_timing_domain(question, llm_intent)

    if is_timing and domain not in ("general",):
        sub = _classify_sub_bucket(domain, question, router_bucket)
        engine = DOMAIN_ENGINES.get(domain, "llm_only")
        if domain == "love":
            engine = "event_timing.love.love_timing_engine_v1"
        return RoutingAudit(
            question=question,
            is_timing=True,
            domain=domain,
            router_bucket=router_bucket,
            sub_bucket=sub,
            engine=engine,
        )

    static_dom, static_sub = _resolve_static_domain(question)
    if static_dom != "general":
        eng = DOMAIN_ENGINES.get(static_dom, "llm_only")
        if static_sub == "milan":
            eng = "event_timing.love.milan_engine_v1"
        elif static_dom == "love":
            eng = "event_timing.love.love_static_engine_v1"
        return RoutingAudit(
            question=question,
            is_timing=False,
            domain=static_dom,
            router_bucket="static",
            sub_bucket=static_sub,
            engine=eng,
            notes="static_gate",
        )

    return RoutingAudit(
        question=question,
        is_timing=is_timing,
        domain=domain,
        router_bucket=router_bucket,
        sub_bucket=router_bucket,
        engine="llm_only",
        notes="no_deterministic_engine",
    )

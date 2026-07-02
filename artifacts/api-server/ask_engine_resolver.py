"""Single winner for Ask static engine routing — LLM domain first, one engine only."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from engine_collision_registry import (
    DOMAIN_MUTEX_CLEAR,
    DOMAIN_PRIMARY_ENGINE,
    should_force_mr_for_question,
    should_suppress_health_for_question,
)

# Same priority as openai_helper elif chain (first match wins when no LLM domain).
STATIC_ENGINE_ORDER: tuple[str, ...] = (
    "education",
    "children",
    "property",
    "vehicle",
    "travel",
    "litigation",
    "gap",
    "network",
    "luck",
    "career",
    "finance",
    "health",
    "mr",
)

ENGINE_SLICE_IDS: dict[str, str] = {
    "education": "education_engine_v1",
    "children": "children_engine_v1",
    "property": "property_engine_v1",
    "vehicle": "vehicle_engine_v1",
    "travel": "travel_engine_v1",
    "litigation": "litigation_engine_v1",
    "gap": "gap_engine_v1",
    "network": "network_engine_v1",
    "luck": "luck_engine_v1",
    "career": "career_engine_v1",
    "finance": "finance_engine_v1",
    "health": "health_engine_v1",
    "mr": "mr_engine_v1",
}

ALL_FLAG_KEYS: tuple[str, ...] = STATIC_ENGINE_ORDER


@dataclass
class EngineRoute:
    """Exactly one static engine winner (or none → chart-only fallback)."""

    engine_key: str | None
    domain: str
    archetype: str | None
    slice_id: str | None
    reason: str
    suppressed: list[str] = field(default_factory=list)
    is_timing: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _llm_domain(
    llm_intent: dict[str, Any] | None,
    llm_intent_admin: dict[str, Any] | None,
) -> str:
    for src in (llm_intent_admin, llm_intent):
        if not isinstance(src, dict):
            continue
        dom = str(src.get("routed_domain") or src.get("domain") or "").strip().lower()
        if dom and dom != "general":
            return dom
    return "general"


def _llm_archetype(
    llm_intent: dict[str, Any] | None,
    llm_intent_admin: dict[str, Any] | None,
) -> str | None:
    for src in (llm_intent_admin, llm_intent):
        if not isinstance(src, dict):
            continue
        for key in (
            "routed_archetype",
            "mr_archetype",
            "career_archetype",
            "health_archetype",
            "finance_archetype",
            "education_archetype",
        ):
            val = src.get(key)
            if val:
                return str(val).strip().lower()
    return None


def _active_engines(flags: dict[str, bool]) -> list[str]:
    return [k for k in STATIC_ENGINE_ORDER if flags.get(k)]


def _apply_domain_mutex(
    flags: dict[str, bool],
    *,
    domain: str,
    question: str,
) -> tuple[dict[str, bool], list[str]]:
    """Clear conflicting regex-only engines when LLM domain is known."""
    out = dict(flags)
    suppressed: list[str] = []

    if should_suppress_health_for_question(question, llm_domain=domain):
        if out.get("health"):
            out["health"] = False
            suppressed.append("health:collision_love_dil")

    mutex = DOMAIN_MUTEX_CLEAR.get(domain)
    if mutex:
        for key in mutex:
            if out.get(key):
                out[key] = False
                suppressed.append(f"{key}:domain_mutex_{domain}")

    primary = DOMAIN_PRIMARY_ENGINE.get(domain)
    if should_force_mr_for_question(question, llm_domain=domain):
        out["mr"] = True
    elif primary and domain in ("love", "marriage"):
        out["mr"] = out.get("mr") or should_force_mr_for_question(question, llm_domain=domain)

    return out, suppressed


def _pick_winner(flags: dict[str, bool], *, domain: str) -> tuple[str | None, str]:
    active = _active_engines(flags)
    if not active:
        return None, "no_static_engine"

    primary = DOMAIN_PRIMARY_ENGINE.get(domain)
    if primary and flags.get(primary):
        return primary, f"llm_domain:{domain}"

    if len(active) == 1:
        return active[0], "single_candidate"

    # Multiple flags still true — use pipeline order but prefer domain primary if present
    if primary and primary in active:
        return primary, f"domain_priority:{domain}"

    for key in STATIC_ENGINE_ORDER:
        if flags.get(key):
            return key, "pipeline_order"

    return None, "no_static_engine"


def resolve_static_engine_route(
    question: str,
    *,
    flags: dict[str, bool],
    llm_intent: dict[str, Any] | None = None,
    llm_intent_admin: dict[str, Any] | None = None,
    is_timing: bool = False,
) -> tuple[dict[str, bool], EngineRoute]:
    """Return mutex-corrected flags (exactly one True) + route metadata."""
    domain = _llm_domain(llm_intent, llm_intent_admin)
    archetype = _llm_archetype(llm_intent, llm_intent_admin)

    try:
        from ask_routing_policy import should_bypass_static_engines_for_direct_llm

        _bypass, _bypass_reason = should_bypass_static_engines_for_direct_llm(
            question or "",
            llm_intent if isinstance(llm_intent, dict) else None,
        )
        if _bypass:
            route = EngineRoute(
                engine_key=None,
                domain=domain,
                archetype=archetype,
                slice_id=None,
                reason=_bypass_reason,
                suppressed=list(_active_engines({k: bool(flags.get(k)) for k in ALL_FLAG_KEYS})),
                is_timing=False,
            )
            return {k: False for k in ALL_FLAG_KEYS}, route
    except Exception:
        pass

    if is_timing:
        route = EngineRoute(
            engine_key=None,
            domain=domain,
            archetype=archetype,
            slice_id=None,
            reason="timing_path",
            suppressed=[],
            is_timing=True,
        )
        return dict(flags), route

    normalized = {k: bool(flags.get(k)) for k in ALL_FLAG_KEYS}
    mutexed, suppressed = _apply_domain_mutex(
        normalized,
        domain=domain,
        question=question or "",
    )
    winner, reason = _pick_winner(mutexed, domain=domain)

    final = {k: False for k in ALL_FLAG_KEYS}
    if winner:
        final[winner] = True
        for k in ALL_FLAG_KEYS:
            if k != winner and mutexed.get(k):
                suppressed.append(f"{k}:not_winner")

    route = EngineRoute(
        engine_key=winner,
        domain=domain,
        archetype=archetype,
        slice_id=ENGINE_SLICE_IDS.get(winner or "", None),
        reason=reason,
        suppressed=suppressed,
        is_timing=False,
    )
    return final, route


def merge_route_into_admin_intent(
    llm_intent_admin: dict[str, Any] | None,
    route: EngineRoute,
) -> dict[str, Any]:
    """Attach resolver output for admin truth (selected vs ran)."""
    out = dict(llm_intent_admin) if isinstance(llm_intent_admin, dict) else {}
    out["engine_route"] = route.to_dict()
    out["engine_ran"] = route.engine_key
    out["engine_ran_slice"] = route.slice_id
    out["engine_route_reason"] = route.reason
    if not route.engine_key and route.reason.startswith("divisional"):
        out["direct_llm_bypass"] = True
    return out

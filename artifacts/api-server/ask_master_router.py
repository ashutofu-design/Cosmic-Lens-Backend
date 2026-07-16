"""Central Ask routing — LLM authority for timing/static; regex as guards only.

Replaces scattered override patches in openai_helper with one decision:
  engine_timing | engine_static | chart_llm | chart_fact
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

# domain → timing engine slice (ask_engine_catalog)
_TIMING_SLICE: dict[str, str] = {
    "love": "love_timing_v1",
    "marriage": "marriage_timing_m17",
    "career": "career_timing_v1",
    "travel": "travel_timing_v1",
    "property": "property_timing_v1",
    "vehicle": "vehicle_timing_v1",
    "finance": "finance_timing_v1",
    "health": "health_timing_v1",
    "children": "children_timing_v1",
    "education": "education_timing_v1",
    "litigation": "litigation_timing_v1",
    "spiritual": "spiritual_timing_v1",
    "fame": "fame_timing_v1",
    "network": "network_timing_v1",
    "universal": "universal_timing_v1",
    "general": "universal_timing_v1",
}

_TRAIT_STATIC_RX = re.compile(
    r"(?ix)\b("
    r"kaisa\s+hoga|kaisi\s+hogi|kaise\s+honge|kaisi\s+rahegi|kaisa\s+rahega|"
    r"dikhne\s+me|attractive|handsome|beautiful|nature|swabhav|"
    r"hoga\s+kya|hogi\s+kya|rahega\s+kya|rahegi\s+kya|"
    r"loyal\w*|dhokh\w*|faithful|trust\s+issue|chhup\w*|betray\w*"
    r")\b",
)


@dataclass
class MasterRoute:
    path: str  # engine_timing | engine_static | chart_llm | chart_fact
    is_timing: bool
    domain: str
    timing_domain: str | None = None
    timing_engine_slice: str | None = None
    archetype: str | None = None
    mr_static: bool = False
    reason: str = ""
    guards: list[str] = field(default_factory=list)
    lock_timing: bool = False  # when True, downstream must not strip timing

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _combined_text(
    question: str,
    understanding: dict[str, Any] | None = None,
    llm_intent: dict[str, Any] | None = None,
) -> str:
    parts = [question or ""]
    for src in (understanding, llm_intent):
        if isinstance(src, dict):
            parts.append(str(src.get("question_summary") or ""))
            parts.append(str(src.get("question_meaning") or ""))
    return " ".join(p for p in parts if p).strip()


def _domain_from_intent(
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


def _archetype_from_intent(
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
            "children_archetype",
            "property_archetype",
            "travel_archetype",
            "litigation_archetype",
        ):
            val = src.get(key)
            if val:
                return str(val).strip().lower()
    return None


def llm_claims_timing(
    llm_intent: dict[str, Any] | None,
    llm_intent_admin: dict[str, Any] | None,
) -> bool:
    for src in (llm_intent_admin, llm_intent):
        if not isinstance(src, dict):
            continue
        if src.get("is_timing") or src.get("routed_timing"):
            return True
        if str(src.get("question_kind") or "").strip().lower() == "timing":
            return True
    return False


def guard_trait_only_blocks_timing(combined: str) -> bool:
    """True when question is trait/static shape without WHEN — regex guard only."""
    try:
        from ask_mr.timing_registry import has_explicit_timing_anchor

        if has_explicit_timing_anchor(combined):
            return False
    except Exception:
        pass
    if not _TRAIT_STATIC_RX.search(combined):
        return False
    # loyalty static is always trait unless explicit when
    try:
        from ask_love.timing_registry import is_love_static_loyalty_question

        if is_love_static_loyalty_question(combined):
            return True
    except Exception:
        pass
    try:
        from ask_mr.timing_registry import is_trait_static_mr_question

        if is_trait_static_mr_question(combined):
            return True
    except Exception:
        pass
    return bool(_TRAIT_STATIC_RX.search(combined))


def _registry_timing_domain(
    combined: str,
    llm_intent: dict[str, Any] | None,
) -> tuple[str, bool, str]:
    """Domain timing registries + event_timing router — confirm LLM, not override it."""
    try:
        from event_timing.timing_router import resolve_timing_domain

        dom, _bucket, is_timing = resolve_timing_domain(combined, llm_intent)
        if is_timing:
            return dom, True, f"timing_registry:{dom}"
    except Exception:
        pass
    return "general", False, "no_timing_registry"


def resolve_ask_route(
    question: str,
    *,
    understanding: dict[str, Any] | None = None,
    llm_intent: dict[str, Any] | None = None,
    llm_intent_admin: dict[str, Any] | None = None,
) -> MasterRoute:
    combined = _combined_text(question, understanding, llm_intent)
    domain = _domain_from_intent(llm_intent, llm_intent_admin)
    archetype = _archetype_from_intent(llm_intent, llm_intent_admin)
    guards: list[str] = []

    try:
        from ask_question_dna import dna_routing_lock

        dna_lock = dna_routing_lock(llm_intent_admin)
        if dna_lock and not dna_lock.get("is_timing"):
            guards.append("dna_static_authority")
            dna_dom = str(dna_lock.get("domain") or domain or "love").strip().lower()
            dna_arch = str(dna_lock.get("archetype") or archetype or "").strip().lower() or None
            return MasterRoute(
                path="engine_static",
                is_timing=False,
                domain=dna_dom or "general",
                archetype=dna_arch,
                mr_static=dna_dom in ("love", "marriage"),
                reason="dna_static_authority",
                guards=guards,
            )
    except Exception:
        pass

    # ── Guards (refuse wrong path) ─────────────────────────────────────
    if guard_trait_only_blocks_timing(combined):
        guards.append("trait_only_no_timing")
        return MasterRoute(
            path="engine_static",
            is_timing=False,
            domain=domain if domain != "general" else "love",
            archetype=archetype,
            mr_static=True,
            reason="guard_trait_static",
            guards=guards,
        )

    try:
        from ask_love.timing_registry import is_love_static_loyalty_question

        if is_love_static_loyalty_question(combined):
            guards.append("love_loyalty_static")
            return MasterRoute(
                path="engine_static",
                is_timing=False,
                domain="love",
                archetype=archetype or "loyalty_trust",
                mr_static=True,
                reason="guard_loyalty_static",
                guards=guards,
            )
    except Exception:
        pass

    try:
        from ask_health.timing_registry import health_static_overrides_llm_timing

        if health_static_overrides_llm_timing(combined, llm_intent):
            guards.append("health_static_over_timing")
            return MasterRoute(
                path="engine_static",
                is_timing=False,
                domain="health",
                archetype=archetype,
                mr_static=False,
                reason="guard_health_static",
                guards=guards,
            )
    except Exception:
        pass

    # ── LLM authority: timing intent wins ───────────────────────────────
    llm_timing = llm_claims_timing(llm_intent, llm_intent_admin)
    reg_dom, reg_timing, reg_reason = _registry_timing_domain(combined, llm_intent)

    is_timing = False
    reason = "static_default"
    timing_domain = None

    if llm_timing:
        is_timing = True
        timing_domain = domain if domain != "general" else reg_dom
        reason = "llm_timing_authority"
        guards.append("llm_timing_authority")
    elif reg_timing:
        is_timing = True
        timing_domain = reg_dom
        reason = reg_reason
        guards.append(reg_reason)

    if is_timing:
        td = timing_domain or reg_dom or domain or "universal"
        if td in ("marriage", "love") and not timing_domain:
            td = reg_dom if reg_dom in ("love", "marriage") else domain or "love"
        if td == "general":
            td = reg_dom if reg_dom not in ("general", "") else "universal"
        arch = archetype
        if td == "love" and arch in ("one_sided_love", "general_mr", "partner_nature", None):
            arch = "dating_courtship"
        return MasterRoute(
            path="engine_timing",
            is_timing=True,
            domain=td,
            timing_domain=td,
            timing_engine_slice=_TIMING_SLICE.get(td, "universal_timing_v1"),
            archetype=arch,
            mr_static=False,
            reason=reason,
            guards=guards,
            lock_timing=True,
        )

    # ── Answer-mode authority (understand + deterministic validate) ──────
    try:
        from ask_answer_mode import resolve_answer_mode

        answer_mode = resolve_answer_mode(
            question,
            llm_intent_admin if isinstance(llm_intent_admin, dict) else llm_intent,
        )
        guards.append(f"answer_mode:{answer_mode}")
        if answer_mode == "chart_fact":
            return MasterRoute(
                path="chart_fact",
                is_timing=False,
                domain=domain,
                archetype=archetype,
                reason="answer_mode_chart_fact",
                guards=guards,
            )
        if answer_mode in ("llm_chart", "llm_knowledge"):
            return MasterRoute(
                path="chart_llm",
                is_timing=False,
                domain=domain,
                archetype=archetype,
                mr_static=False,
                reason=f"answer_mode_{answer_mode}",
                guards=guards,
            )
    except Exception:
        pass

    # ── Static engines / chart LLM ────────────────────────────────────────
    try:
        from ask_routing_policy import matches_dedicated_static_engine

        if matches_dedicated_static_engine(combined, llm_intent):
            dom = domain if domain != "general" else _domain_from_intent(llm_intent, llm_intent_admin)
            mr = False
            if dom in ("love", "marriage"):
                mr = True
            else:
                try:
                    from ask_mr.timing_registry import is_mr_static_question

                    mr = bool(is_mr_static_question(combined))
                except Exception:
                    pass
            return MasterRoute(
                path="engine_static",
                is_timing=False,
                domain=dom,
                archetype=archetype,
                mr_static=mr,
                reason="dedicated_static_engine",
                guards=guards,
            )
    except Exception:
        pass

    try:
        from chart_fact_answer import is_pure_chart_fact_lookup

        if is_pure_chart_fact_lookup(combined):
            return MasterRoute(
                path="chart_fact",
                is_timing=False,
                domain=domain,
                archetype=archetype,
                reason="chart_fact_lookup",
                guards=guards,
            )
    except Exception:
        pass

    return MasterRoute(
        path="chart_llm",
        is_timing=False,
        domain=domain,
        archetype=archetype,
        mr_static=False,
        reason="no_engine_chart_llm",
        guards=guards,
    )


def apply_route_to_intent(
    route: MasterRoute,
    llm_intent: dict[str, Any] | None,
    llm_intent_admin: dict[str, Any] | None,
) -> None:
    """Sync intent dicts with master route (LLM fields = routing truth)."""
    for src in (llm_intent, llm_intent_admin):
        if not isinstance(src, dict):
            continue
        src["is_timing"] = bool(route.is_timing)
        src["routed_timing"] = bool(route.is_timing)
        if route.domain and route.domain != "general":
            src["domain"] = route.domain
            src["routed_domain"] = route.domain
        if route.archetype:
            src["mr_archetype"] = route.archetype
            src["routed_archetype"] = route.archetype
        src["master_route"] = route.to_dict()


def patch_static_flags(
    route: MasterRoute,
    flags: dict[str, bool],
) -> dict[str, bool]:
    """When timing wins, clear conflicting static flags."""
    out = dict(flags)
    if route.is_timing and route.lock_timing:
        for key in list(out.keys()):
            out[key] = False
        return out
    if route.path == "engine_static" and route.mr_static:
        out = {k: False for k in out}
        out["mr"] = True
    return out


def finalize_ask_route(
    question: str,
    *,
    understanding: dict[str, Any] | None = None,
    llm_intent: dict[str, Any] | None = None,
    llm_intent_admin: dict[str, Any] | None = None,
) -> MasterRoute:
    """Resolve + apply to intent dicts; single entry for raw_passthrough."""
    route = resolve_ask_route(
        question,
        understanding=understanding,
        llm_intent=llm_intent,
        llm_intent_admin=llm_intent_admin,
    )
    apply_route_to_intent(route, llm_intent, llm_intent_admin)
    return route

"""Wire Question DNA (domain + bucket + intent) → engine execution.

Rule: whatever DNA says, that domain's engine runs with a mapped archetype.
No keyword/follow-up hijack after this wire is applied.
"""
from __future__ import annotations

from typing import Any

from engine_collision_registry import DOMAIN_PRIMARY_ENGINE

# Free-form DNA buckets (LLM invents names) → known static-engine archetypes.
_FINANCE_BUCKET_MAP: dict[str, str] = {
    "wealth_potential": "wealth_potential",
    "wealth_prediction": "wealth_potential",
    "wealth_timing": "wealth_potential",
    "wealth_dasha_analysis": "wealth_potential",
    "wealth_analysis_dasha": "wealth_potential",
    "wealth_analysis_with_dasha": "wealth_potential",
    "wealth_dasha": "wealth_potential",
    "general_wealth": "wealth_potential",
    "dhana_yoga": "dhana_yoga",
    "income_source": "income_source",
    "savings_capacity": "savings_capacity",
    "save_vs_spend": "save_vs_spend",
    "expense_pattern": "expense_pattern",
    "spending_personality": "spending_personality",
    "financial_discipline": "financial_discipline",
    "investment_risk": "investment_risk",
    "debt_loan": "debt_loan",
    "loan_emi": "debt_loan",
    "property_money": "property_money",
    "sudden_gain_loss": "sudden_gain_loss",
    "sudden_windfall": "sudden_gain_loss",
    "business_profit": "business_profit",
    "loss_reasons": "loss_reasons",
    "salary_growth": "income_source",
    "general_finance": "general_finance",
}

_INTENT_FINANCE_HINTS: tuple[tuple[str, str], ...] = (
    (r"wealth|dhan|paisa|money|financial|finance", "wealth_potential"),
    (r"debt|loan|emi|karz", "debt_loan"),
    (r"invest|mutual|sip|risk", "investment_risk"),
    (r"save|bachat|spend|kharch", "save_vs_spend"),
    (r"business|profit", "business_profit"),
    (r"dhana\s*yoga|raj\s*yoga", "dhana_yoga"),
)


def _primary_dna_item(admin: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(admin, dict):
        return {}
    dna = admin.get("question_dna")
    if not isinstance(dna, dict):
        return {}
    items = dna.get("questions")
    if isinstance(items, list) and items and isinstance(items[0], dict):
        return items[0]
    return {}


def _map_finance_archetype(bucket: str, intent: str, engine_arch: str) -> str:
    for raw in (engine_arch, bucket):
        key = (raw or "").strip().lower().replace(" ", "_").replace("-", "_")
        if key in _FINANCE_BUCKET_MAP:
            return _FINANCE_BUCKET_MAP[key]
        # soft prefix: wealth_* → wealth_potential
        if key.startswith("wealth"):
            return "wealth_potential"
    intent_l = (intent or "").strip().lower()
    if intent_l:
        import re

        for rx, arch in _INTENT_FINANCE_HINTS:
            if re.search(rx, intent_l, re.I):
                return arch
    return "general_finance"


def _map_domain_archetype(domain: str, bucket: str, intent: str, engine_arch: str) -> str:
    """Normalize DNA bucket/intent into the domain engine's archetype label."""
    dom = (domain or "").strip().lower()
    raw = (engine_arch or bucket or "").strip().lower().replace(" ", "_").replace("-", "_")
    if dom == "finance":
        return _map_finance_archetype(bucket, intent, engine_arch)
    if dom in ("love", "marriage", "relationship"):
        # Keep DNA label if present; MR engine treats it as routing_label.
        return raw or "general_mr"
    if dom == "career":
        return raw or "general_career"
    if dom == "health":
        return raw or "general_health"
    return raw or "general"


def resolve_dna_engine_wire(
    admin: dict[str, Any] | None,
    *,
    question: str = "",
) -> dict[str, Any] | None:
    """Return execution wire from trusted Question DNA, or None.

    Keys: domain, engine_key, archetype, bucket, intent, is_timing, trusted, reason
    """
    if not isinstance(admin, dict):
        return None
    item = _primary_dna_item(admin)
    if not item and not admin.get("dna_routing_applied"):
        return None

    try:
        from ask_question_dna import (
            dna_item_trusted_for_routing,
            resolve_engine_archetype_from_dna_item,
        )

        trusted = dna_item_trusted_for_routing(
            item,
            dna_source=str((admin.get("question_dna") or {}).get("source") or ""),
        )
    except Exception:
        trusted = bool(admin.get("dna_routing_applied"))

    if not trusted and admin.get("dna_routing_applied"):
        trusted = True
    if not trusted:
        return None

    domain = str(
        item.get("domain")
        or admin.get("routed_domain")
        or admin.get("domain")
        or ""
    ).strip().lower()
    if not domain or domain == "general":
        return None

    engine_key = DOMAIN_PRIMARY_ENGINE.get(domain)
    if not engine_key:
        return None

    bucket = str(item.get("bucket") or admin.get("bucket") or "").strip().lower()
    intent = str(
        item.get("intent")
        or item.get("user_wants")
        or admin.get("intent")
        or ""
    ).strip()
    try:
        from ask_question_dna import resolve_engine_archetype_from_dna_item

        engine_arch = str(
            resolve_engine_archetype_from_dna_item(item)
            or admin.get("dna_engine_archetype")
            or bucket
            or ""
        ).strip().lower()
    except Exception:
        engine_arch = str(admin.get("dna_engine_archetype") or bucket or "").strip().lower()

    if "timing" in item:
        is_timing = bool(item.get("timing"))
    elif "routed_timing" in admin:
        is_timing = bool(admin.get("routed_timing"))
    else:
        is_timing = bool(admin.get("is_timing"))

    archetype = _map_domain_archetype(domain, bucket, intent, engine_arch)
    return {
        "trusted": True,
        "domain": domain,
        "engine_key": engine_key,
        "archetype": archetype,
        "bucket": bucket,
        "intent": intent[:240],
        "is_timing": is_timing,
        "reason": f"dna_wire:{domain}/{bucket or archetype}",
        "question": (question or "")[:80],
    }


def apply_dna_wire_to_static_flags(
    wire: dict[str, Any],
    *,
    flags: dict[str, bool] | None = None,
) -> dict[str, bool]:
    """Return one-hot static engine flags for the DNA wire's engine_key."""
    keys = (
        "education", "children", "property", "vehicle", "travel",
        "litigation", "gap", "network", "luck", "career", "finance", "health", "mr",
    )
    out = {k: False for k in keys}
    if isinstance(flags, dict):
        for k in keys:
            if k in flags:
                out[k] = False
    eng = str(wire.get("engine_key") or "").strip().lower()
    if not wire.get("is_timing") and eng in out:
        out[eng] = True
    return out

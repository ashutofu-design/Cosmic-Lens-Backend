"""Shared helpers for ask_finance engines — wraps finance_static facts."""

from __future__ import annotations

from typing import Any

from finance_static.finance_facts import compute_finance_facts

_VERDICT_PLAIN = {
    "GREEN": "Strong",
    "YELLOW": "Mixed",
    "RED": "Weak",
}

_TIER_PLAIN = {
    "high": "high reliability",
    "moderate": "moderate reliability",
    "low": "low reliability",
    "none": "very low reliability",
}


def load_facts(kundli: dict) -> dict[str, Any]:
    return compute_finance_facts(kundli if isinstance(kundli, dict) else {})


def dim(facts: dict, key: str) -> dict:
    return (facts.get("dimensions") or {}).get(key) or {}


def dim_evidence(facts: dict, key: str, label: str) -> str:
    d = dim(facts, key)
    v = d.get("verdict", "?")
    reason = d.get("reason") or ""
    tier = d.get("tier") or "?"
    plain = _VERDICT_PLAIN.get(v, v)
    tier_plain = _TIER_PLAIN.get(tier, tier)
    return f"{label}: {plain} ({tier_plain}) — {reason}".strip(" —")


def lord_evidence(facts: dict, house_key: str, label: str) -> str:
    h = (facts.get("house_lords") or {}).get(house_key) or {}
    lord = h.get("lord") or "?"
    lh = h.get("lord_house") or "?"
    dig = h.get("lord_dignity") or "?"
    dust = " (dusthana placement)" if h.get("lord_in_dusthana") else ""
    return f"{label}: lord {lord} in H{lh}, dignity {dig}{dust}"


def yogas_line(facts: dict) -> str:
    yogas = facts.get("wealth_yogas") or []
    if yogas:
        return f"Wealth yogas active: {', '.join(yogas)}"
    return "No major dhan-yog active in chart"


def affliction_lines(facts: dict, limit: int = 3) -> list[str]:
    aff = facts.get("afflictions") or []
    return [f"Drain signal: {a}" for a in aff[:limit]]


def sub_flag(facts: dict, key: str, default: Any = False) -> Any:
    return (facts.get("sub_flags") or {}).get(key, default)


def income_affinity_lines(facts: dict) -> list[str]:
    aff = sub_flag(facts, "income_affinity", []) or []
    if not aff:
        return ["Income style: mixed — chart does not lock one single source"]
    return [f"Income affinity: {', '.join(aff[:4])}"]


def dasha_money_note(facts: dict) -> str | None:
    cd = facts.get("current_dasha") or {}
    md = cd.get("md") or ""
    ad = cd.get("ad") or ""
    if not md:
        return None
    md_link = cd.get("md_money_link")
    md_bad = cd.get("md_dusthana_link")
    if md_link:
        return f"Current phase ({md}-{ad}): money-house link active — earning/saving theme stronger in this period"
    if md_bad:
        return f"Current phase ({md}-{ad}): expense/drain theme active — control spending in this period"
    return None


def composite_verdict(facts: dict, *, focus: str) -> str:
    return f"Finance ({focus}): chart-based pattern from locked engine facts"

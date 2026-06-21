"""Shared helpers for ask_health engines — wraps health_static facts."""

from __future__ import annotations

from typing import Any

from health_static.health_facts import compute_health_facts

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
    return compute_health_facts(kundli if isinstance(kundli, dict) else {})


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


def karaka_evidence(facts: dict, name: str, label: str) -> str:
    k = (facts.get("karakas") or {}).get(name) or {}
    return f"{label}: {name} in H{k.get('house', '?')}, dignity {k.get('dignity', '?')}"


def affliction_lines(facts: dict, limit: int = 3) -> list[str]:
    aff = facts.get("afflictions") or []
    return [f"Pressure signal: {a}" for a in aff[:limit]]


def vitality_line(facts: dict) -> str:
    score = facts.get("vitality_score")
    risk = facts.get("vitality_risk") or "?"
    return f"Vitality score: {score}/100 ({risk} structural risk)"


def sub_flag(facts: dict, key: str, default: Any = False) -> Any:
    return (facts.get("sub_flags") or {}).get(key, default)

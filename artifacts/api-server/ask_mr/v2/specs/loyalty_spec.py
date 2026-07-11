"""Loyalty / trust engine spec — dedicated TRUST-xxx rules + v1 level logic."""
from __future__ import annotations

import re
from typing import Any

from ..engine_spec import EngineSpec
from ..rules.trust_rules import RULE_PREFIX, RULES_VERSION


def _loyalty_intent(question: str) -> str:
    q = (question or "").strip()
    if not q:
        return "general_trust"
    if re.search(r"(?ix)\b(cheat|dhokha|dhoka|affair|chakkar|beimaan|unfaithful)\b", q):
        return "cheating_suspicion"
    if re.search(r"(?ix)\b(betray|dhokha\s*diya|broken\s*trust)\b", q):
        return "betrayal"
    if re.search(r"(?ix)\b(vishwas|trust|loyal|faithful|wafad|vafad)\b", q):
        return "general_trust"
    return "general_trust"


def _loyalty_context(question: str, kundli: dict, sig: Any) -> dict[str, Any]:
    return {"intent": _loyalty_intent(question)}


def _loyalty_level(score: int, contradiction: bool, intent: str, ctx: dict[str, Any]) -> str:
    s = ctx.get("sig")
    if s is not None:
        if s.third_person_risk or s.venus_mars_conjunct_tight or s.moon_in_8th:
            return "risky"
        if s.loyalty_risk_high or s.venus_mars_conjunct or s.rahu_on_7th_axis:
            return "unstable"

        w = int(getattr(s, "affliction_weight", 0) or 0)
        neg_flags = sum(1 for flag in (
            s.seventh_lord_dusthana,
            s.seventh_lord_debil,
            s.venus_debil,
            s.venus_afflicted,
            s.moon_debil,
            s.moon_in_8th,
            s.mars_on_7th,
            s.saturn_on_7th_not_lord,
            s.d9_seventh_lord_weak,
            s.moon_d9_debil,
        ) if flag)

        if neg_flags >= 3 or w >= 38:
            return "unstable"
        if neg_flags >= 2 or w >= 22 or (s.saturn_on_7th and s.mars_on_7th):
            return "mixed"
        if neg_flags >= 1 or w >= 14 or s.saturn_on_7th or s.mars_on_7th or s.moon_afflicted:
            return "mixed"
        if loyalty_safe_from_ctx(ctx):
            return "moderate"

    adjusted = score - 6 if contradiction and score > 55 else score
    if adjusted >= 75:
        return "moderate"
    if adjusted >= 60:
        return "mixed"
    if adjusted >= 45:
        return "unstable"
    return "risky"


def loyalty_safe_from_ctx(ctx: dict[str, Any]) -> bool:
    from ..rules._trust_ctx import loyalty_safe_bonus

    return loyalty_safe_bonus(ctx)


def _loyalty_headline(level: str, intent: str, ctx: dict[str, Any]) -> str:
    topic = {
        "cheating_suspicion": "Cheating/loyalty check",
        "betrayal": "Betrayal/trust recovery",
        "general_trust": "Trust/loyalty",
    }.get(intent, "Trust/loyalty")
    tone = {
        "moderate": f"{topic}: mostly stable — clear talk keeps vishwas strong",
        "mixed": f"{topic}: mixed — distance or friction can test trust",
        "unstable": f"{topic}: sensitive — clarity and boundaries are needed",
        "risky": f"{topic}: high-risk pattern — secrecy or impulse weakens loyalty",
    }
    return tone.get(level, tone["mixed"])


def _loyalty_confidence(score: int, contradiction: bool) -> str:
    if contradiction:
        return "medium"
    if score >= 78:
        return "high"
    if score <= 42:
        return "low"
    return "medium"


def _loyalty_checks(
    engine_id: str,
    score: int,
    level: str,
    sig: Any,
    ctx: dict[str, Any],
) -> dict[str, Any]:
    return {
        "trust_level": level,
        "loyalty_intent": ctx.get("intent", "general_trust"),
        "loyalty_risk_high": bool(getattr(sig, "loyalty_risk_high", False)),
        "third_person_risk": bool(getattr(sig, "third_person_risk", False)),
        "primary_score": score,
        "affliction_weight": int(getattr(sig, "affliction_weight", 0) or 0),
        "level": level,
    }


def loyalty_spec() -> EngineSpec:
    return EngineSpec(
        engine_id="loyalty_trust",
        rule_prefix=RULE_PREFIX,
        rules_version=f"{RULE_PREFIX}-{RULES_VERSION}",
        base_score=56,
        levels=((75, "moderate"), (60, "mixed"), (45, "unstable"), (0, "risky")),
        headlines={},
        resolve_intent=_loyalty_intent,
        build_context=_loyalty_context,
        resolve_level=_loyalty_level,
        resolve_headline=_loyalty_headline,
        resolve_confidence=_loyalty_confidence,
        build_checks=_loyalty_checks,
        narrator_plan="2–3 sentences: trust level → strongest chart factor → one boundary habit",
        ignore=["timing dates unless asked", "spouse profession", "manglik unless asked"],
    )

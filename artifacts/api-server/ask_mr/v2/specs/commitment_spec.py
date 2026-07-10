"""Commitment reference engine spec — dedicated COM-xxx rules."""
from __future__ import annotations

from typing import Any

from ..engine_spec import EngineSpec
from ..rules.commitment_rules import RULE_PREFIX, RULES_VERSION


def _commitment_intent(question: str) -> str:
    from ask_intent_fidelity import infer_partner_commitment_angle

    angle = (infer_partner_commitment_angle(question or "") or "general_commitment").strip().lower()
    if angle == "loyalty_intent":
        return "general_commitment"
    return angle


def _commitment_context(question: str, kundli: dict, sig: Any) -> dict[str, Any]:
    angle = _commitment_intent(question)
    return {
        "angle": angle,
        "third_person_risk": bool(getattr(sig, "third_person_risk", False)),
    }


def _commitment_level(score: int, contradiction: bool, intent: str, ctx: dict[str, Any]) -> str:
    if contradiction:
        if score >= 65:
            return "cautious"
        if score >= 50:
            return "mixed"
        return "low"
    if score >= 75:
        return "ready"
    if score >= 62:
        return "cautious"
    if score >= 48:
        return "mixed"
    return "low"


def _commitment_headline(level: str, intent: str, ctx: dict[str, Any]) -> str:
    topic = {
        "commitment_ready": "Commitment readiness",
        "serious_relationship": "Serious relationship intent",
        "casual_relationship": "Casual vs serious intent",
        "time_pass": "Time-pass vs genuine intent",
        "long_term_intent": "Long-term commitment intent",
        "future_together": "Future together intent",
        "life_partner_view": "Life-partner view",
        "genuine_intent": "Genuine investment intent",
        "effort_and_maintain": "Effort & maintain intent",
        "trust_blockers": "Trust blockers to commitment",
        "public_acceptance": "Public/family acceptance intent",
        "general_commitment": "Commitment intent",
    }.get(intent, "Commitment intent")
    tone = {
        "ready": f"{topic}: mostly ready — consistency strengthens the bond",
        "cautious": f"{topic}: cautious — interest hai par clarity chahiye",
        "mixed": f"{topic}: mixed — friction ya distance commitment test karta hai",
        "low": f"{topic}: low / hesitant — boundaries aur honest intent check zaroori",
    }
    return tone.get(level, tone["mixed"])


def _commitment_confidence(score: int, contradiction: bool) -> str:
    if contradiction:
        return "medium"
    if score >= 78:
        return "high"
    if score <= 42:
        return "low"
    return "medium"


def _commitment_checks(
    engine_id: str,
    score: int,
    level: str,
    sig: Any,
    ctx: dict[str, Any],
) -> dict[str, Any]:
    return {
        "commitment_level": level,
        "commitment_angle": ctx.get("angle", "general_commitment"),
        "primary_score": score,
        "affliction_weight": int(getattr(sig, "affliction_weight", 0) or 0),
        "level": level,
    }


def commitment_spec() -> EngineSpec:
    return EngineSpec(
        engine_id="commitment",
        rule_prefix=RULE_PREFIX,
        rules_version=f"{RULE_PREFIX}-{RULES_VERSION}",
        base_score=58,
        levels=((75, "ready"), (62, "cautious"), (48, "mixed"), (0, "low")),
        headlines={},  # custom resolver
        resolve_intent=_commitment_intent,
        build_context=_commitment_context,
        resolve_level=_commitment_level,
        resolve_headline=_commitment_headline,
        resolve_confidence=_commitment_confidence,
        build_checks=_commitment_checks,
        narrator_plan=(
            "JSON narrator flow: direct answer → short why → strongest_factor → "
            "warnings/caution → timing (if asked) → practical guidance → Confidence %"
        ),
        ignore=["timing dates unless asked", "cheating accusations unless asked"],
    )

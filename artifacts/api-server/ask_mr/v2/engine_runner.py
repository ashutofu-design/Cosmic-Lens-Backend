"""Single frozen pipeline for all 20 relationship MR engines."""
from __future__ import annotations

from typing import Any

from .contradiction import detect_contradictions
from .engine_spec import EngineSpec
from .explanation import build_explanation
from .module_loader import ModuleLoader
from .registry import question_has_timing_trigger
from .rules.conflict_resolver import ConflictResolver
from .rules.evaluator import RuleEvaluator
from .rules.rule_registry import get_registered_rules, get_rules_version
from .schema import EngineOutputV2, TimingBlock, VerdictBlock
from .scorecard import build_scorecard
from .rules.generic_rules import generic_rules_for


def _default_level(spec: EngineSpec, score: int, contradiction: bool) -> str:
    adjusted = score - 6 if contradiction and score > 55 else score
    for threshold, level in spec.levels:
        if adjusted >= threshold:
            return str(level)
    return str(spec.levels[-1][1])


def _default_confidence(score: int, contradiction: bool) -> str:
    if contradiction:
        return "medium"
    if score >= 78:
        return "high"
    if score <= 42:
        return "low"
    return "medium"


def _default_checks(
    engine_id: str,
    score: int,
    level: str,
    sig: Any,
    ctx: dict[str, Any],
) -> dict[str, Any]:
    checks: dict[str, Any] = {
        "primary_score": score,
        "affliction_weight": int(getattr(sig, "affliction_weight", 0) or 0),
        "level": level,
    }
    eid = engine_id.strip().lower()
    if eid == "loyalty_trust":
        checks.update({
            "trust_level": level,
            "loyalty_risk_high": bool(getattr(sig, "loyalty_risk_high", False)),
            "third_person_risk": bool(getattr(sig, "third_person_risk", False)),
        })
    elif eid == "compatibility":
        checks["compat_level"] = level
    elif eid == "breakup_risk":
        checks.update({
            "risk_level": level,
            "separation_yoga": bool(getattr(sig, "separation_yoga", False)),
            "reconnection_yoga": bool(getattr(sig, "reconnection_yoga", False)),
            "third_person_risk": bool(getattr(sig, "third_person_risk", False)),
            "loyalty_risk_high": bool(getattr(sig, "loyalty_risk_high", False)),
        })
    elif eid == "patchup":
        checks.update({
            "patchup_level": level,
            "reconnection_yoga": bool(getattr(sig, "reconnection_yoga", False)),
            "separation_yoga": bool(getattr(sig, "separation_yoga", False)),
        })
    elif eid == "commitment":
        checks.update({
            "commitment_level": level,
            "commitment_angle": ctx.get("angle", eid),
        })
    elif eid == "secret_relationship":
        checks.update({
            "secrecy_level": level,
            "secret_level": level,
            "third_person_risk": bool(getattr(sig, "third_person_risk", False)),
        })
    elif eid == "partner_nature":
        checks.update({
            "nature_level": level,
            "partner_nature_level": level,
        })
    elif eid == "family_approval":
        checks["family_approval_level"] = level
    elif eid == "long_distance":
        checks.update({
            "long_distance_level": level,
            "ldr_level": level,
        })
    elif eid == "toxicity":
        checks.update({
            "toxicity_level": level,
            "tox_level": level,
        })
    elif eid == "one_sided_love":
        checks.update({
            "one_sided_level": level,
            "oslove_level": level,
        })
    elif eid == "chemistry":
        checks.update({
            "chemistry_level": level,
            "chem_level": level,
        })
    elif eid == "bed_intimacy":
        checks.update({
            "intimacy_level": level,
            "bed_intimacy_level": level,
            "intim_level": level,
        })
    elif eid == "karmic_marriage":
        checks.update({
            "karmic_level": level,
            "karmic_marriage_level": level,
            "karm_level": level,
        })
    elif eid == "relationship_future":
        checks.update({
            "future_level": level,
            "relationship_future_level": level,
            "rfut_level": level,
        })
    elif eid == "relationship_decisions":
        checks.update({
            "decision_level": level,
            "relationship_decisions_level": level,
            "rdec_level": level,
        })
    elif eid == "communication":
        checks["communication_level"] = level
    elif eid == "emotional_attachment":
        checks.update({
            "attachment_level": level,
            "emotional_attachment_level": level,
        })
    elif eid == "relationship_remedies":
        checks["remedy_scope"] = level
    return checks


def run_engine_from_spec(
    spec: EngineSpec,
    kundli: dict,
    question: str,
    *,
    session_id: str = "",
    wants_explain: bool = False,
    orchestrator_meta: dict[str, Any] | None = None,
) -> EngineOutputV2:
    from ask_mr.engines._person_signals import build_person_signals
    from vedic.love_reality.scoring_core import KundliReader

    eid = spec.engine_id.strip().lower()
    timing = question_has_timing_trigger(question)
    mode = "timing" if timing else "static"
    intent = (spec.resolve_intent(question) if spec.resolve_intent else eid).strip().lower()

    bundle = ModuleLoader().load(eid, question, kundli)
    k = dict(kundli or {})
    k.setdefault("name", "You")
    sig = build_person_signals(kundli)
    chart_reader = KundliReader(k)
    ctx: dict[str, Any] = {
        "question": question,
        "intent": intent,
        "angle": intent,
        "mode": mode,
        "sig": sig,
        "reader": chart_reader,
        "session_id": session_id,
        "wants_explain": wants_explain,
    }
    if spec.build_context:
        ctx.update(spec.build_context(question, kundli, sig))

    rules = get_registered_rules(eid)
    if rules is None:
        rules = spec.rules_factory() if spec.rules_factory else generic_rules_for(spec)

    effective_rules_version = get_rules_version(eid, fallback_prefix=spec.rule_prefix)
    fired = RuleEvaluator().evaluate(rules, bundle, ctx)
    resolved = ConflictResolver().resolve(bundle, fired, base_score=int(spec.base_score), engine_id=eid)
    contradiction = detect_contradictions(bundle)

    score = int(resolved["score"])
    if spec.apply_contradiction_penalty and contradiction.detected and score > 55:
        score = max(spec.contradiction_floor, score - spec.contradiction_penalty)

    level = (
        spec.resolve_level(score, contradiction.detected, intent, ctx)
        if spec.resolve_level
        else _default_level(spec, score, contradiction.detected)
    )
    headline = (
        spec.resolve_headline(level, intent, ctx)
        if spec.resolve_headline
        else spec.headlines.get(level, spec.headlines.get(spec.levels[-1][1], "Mixed pattern"))
    )
    confidence = (
        spec.resolve_confidence(score, contradiction.detected)
        if spec.resolve_confidence
        else _default_confidence(score, contradiction.detected)
    )

    scorecard = build_scorecard(eid, bundle, fired, primary_score=score)
    checks = (
        spec.build_checks(eid, score, level, sig, ctx)
        if spec.build_checks
        else _default_checks(eid, score, level, sig, ctx)
    )
    checks.update({
        "engine_version": spec.engine_version,
        "rules_version": effective_rules_version,
        "schema_version": spec.schema_version,
    })

    output = EngineOutputV2(
        engine_id=eid,
        engine_version=spec.engine_version,
        rules_version=effective_rules_version,
        schema_version=spec.schema_version,
        question_intent=intent,
        mode=mode,
        modules_used=list(bundle.modules_requested),
        verdict=VerdictBlock(level=level, headline=headline, confidence=confidence),
        scorecard=scorecard,
        evidence={
            "positive": resolved["evidence_positive"],
            "negative": resolved["evidence_negative"],
            "neutral": resolved["evidence_neutral"],
        },
        rules_fired=[f.to_dict() for f in fired],
        contradiction=contradiction,
        explanation=build_explanation(fired, score=score),
        timing=TimingBlock(applicable=timing),
        checks=checks,
        narrator_plan=spec.narrator_plan,
        ignore=list(spec.ignore),
        orchestrator=orchestrator_meta or {},
    )

    if contradiction.detected:
        output.explanation.why.insert(0, contradiction.summary)

    if spec.post_process:
        output = spec.post_process(output, kundli, sig)

    return output

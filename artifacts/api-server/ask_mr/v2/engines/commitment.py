"""Commitment Engine — v2 reference implementation."""
from __future__ import annotations

from typing import Any

from ask_intent_fidelity import infer_partner_commitment_angle

from ..contradiction import detect_contradictions
from ..explanation import build_explanation
from ..memory import load_memory, merge_with_memory, save_memory
from ..module_loader import ModuleLoader
from ..registry import question_has_timing_trigger
from ..rules.conflict_resolver import ConflictResolver
from ..rules.evaluator import RuleEvaluator
from ..schema import EngineOutputV2, TimingBlock, VerdictBlock
from ..scorecard import build_scorecard
from .commitment_rules import commitment_rules


def _level_from_score(score: int, *, contradiction: bool) -> str:
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


def _headline(level: str, angle: str) -> str:
    topic = {
        "commitment_ready": "Commitment readiness",
        "serious_relationship": "Serious relationship intent",
        "casual_relationship": "Casual vs serious intent",
        "time_pass": "Time-pass vs genuine intent",
        "long_term_intent": "Long-term commitment intent",
    }.get(angle, "Commitment intent")
    tone = {
        "ready": f"{topic}: mostly ready — consistency strengthens the bond",
        "cautious": f"{topic}: cautious — interest hai par clarity chahiye",
        "mixed": f"{topic}: mixed — friction ya distance commitment test karta hai",
        "low": f"{topic}: low / hesitant — boundaries aur honest intent check zaroori",
    }
    return tone.get(level, tone["mixed"])


def _confidence(score: int, refire: int) -> str:
    if score >= 78 or refire >= 2:
        return "high"
    if score <= 42:
        return "low"
    return "medium"


def run_commitment_v2(
    kundli: dict,
    question: str,
    *,
    session_id: str = "",
    wants_explain: bool = False,
    orchestrator_meta: dict[str, Any] | None = None,
) -> EngineOutputV2:
    from ask_mr.engines._person_signals import build_person_signals

    angle = (infer_partner_commitment_angle(question or "") or "general_commitment").strip().lower()
    timing = question_has_timing_trigger(question)
    mode = "timing" if timing else "static"

    loader = ModuleLoader()
    bundle = loader.load("commitment", question, kundli)

    sig = build_person_signals(kundli)
    ctx = {
        "question": question,
        "angle": angle,
        "third_person_risk": bool(getattr(sig, "third_person_risk", False)),
    }

    evaluator = RuleEvaluator()
    fired = evaluator.evaluate(commitment_rules(), bundle, ctx)

    resolver = ConflictResolver()
    resolved = resolver.resolve(bundle, fired, base_score=58)

    contradiction = detect_contradictions(bundle)
    score = int(resolved["score"])
    if contradiction.detected and score > 55:
        score = max(48, score - 8)

    level = _level_from_score(score, contradiction=contradiction.detected)
    scorecard = build_scorecard("commitment", bundle, fired, primary_score=score)

    memory = load_memory(session_id, "commitment")
    refire = sum(1 for f in fired if f.rule_id in memory.previously_fired_rules)

    output = EngineOutputV2(
        engine_id="commitment",
        engine_version="v2",
        question_intent=angle,
        mode=mode,
        modules_used=list(bundle.modules_requested),
        verdict=VerdictBlock(
            level=level,
            headline=_headline(level, angle),
            confidence=_confidence(score, refire),
        ),
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
        checks={
            "commitment_level": level,
            "commitment_angle": angle,
            "primary_score": score,
            "affliction_weight": int(sig.affliction_weight or 0),
        },
        narrator_plan="2–3 sentences: commitment level → strongest factor → one clarity habit",
        ignore=["timing dates unless asked", "cheating accusations unless asked"],
        orchestrator=orchestrator_meta or {},
    )

    if contradiction.detected:
        output.explanation.why.insert(0, contradiction.summary)

    output = merge_with_memory(output, memory)
    save_memory(session_id, output)
    return output

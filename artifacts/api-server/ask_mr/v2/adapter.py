"""Adapter — EngineOutputV2 → legacy EngineResult."""
from __future__ import annotations

from ask_mr.types import EngineResult

from .schema import EngineOutputV2


def v2_to_engine_result(output: EngineOutputV2) -> EngineResult:
    ev = output.evidence
    pos = list(ev.get("positive") or [])
    neg = list(ev.get("negative") or [])
    neu = list(ev.get("neutral") or [])
    evidence = pos + neg + neu

    checks = dict(output.checks or {})
    checks["slice_type"] = "mr_engine_v2"
    checks["engine_version"] = output.engine_version
    checks["rules_version"] = output.rules_version
    checks["schema_version"] = output.schema_version
    checks["scorecard"] = dict(output.scorecard)
    checks["contradiction"] = output.contradiction.detected
    checks["contradiction_pattern"] = output.contradiction.pattern
    checks["explanation"] = {
        "why": output.explanation.why,
        "why_not": output.explanation.why_not,
        "strongest_factor": (
            output.explanation.strongest_factor.label
            if output.explanation.strongest_factor
            else ""
        ),
        "weakest_factor": (
            output.explanation.weakest_factor.label
            if output.explanation.weakest_factor
            else ""
        ),
    }
    checks["timing"] = {
        "applicable": bool(output.timing.applicable),
        "windows": list(output.timing.windows or []),
        "trigger_planets": list(output.timing.trigger_planets or []),
    }
    checks["mode"] = output.mode
    checks["modules_used"] = list(output.modules_used or [])
    checks["rules_fired"] = list(output.rules_fired or [])
    checks["contradiction_detail"] = {
        "detected": bool(output.contradiction.detected),
        "pattern": output.contradiction.pattern,
        "summary": output.contradiction.summary,
        "module_polarity": dict(output.contradiction.module_polarity or {}),
    }
    if output.orchestrator:
        checks["orchestrator"] = dict(output.orchestrator)
    return EngineResult(
        archetype=output.engine_id,
        verdict=output.verdict.headline,
        confidence=output.verdict.confidence,
        word_budget=90 if output.mode == "timing" else 65,
        answer_plan=output.narrator_plan,
        summary=[
            "v2 engine — use WHY/WHY NOT + scorecard; no shayad/ho sakta hai.",
            output.contradiction.summary if output.contradiction.detected else "",
        ],
        evidence=evidence[:10],
        evidence_positive=pos,
        evidence_negative=neg,
        ignore=list(output.ignore),
        checks=checks,
    )

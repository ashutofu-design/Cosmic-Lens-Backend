"""MR engine pipeline step_audit — admin debug trace for static MR v2 engines."""
from __future__ import annotations

from typing import Any

MR_PIPELINE_STEP_ORDER = (
    "step1",
    "step2",
    "step3",
    "step4",
    "step5",
    "step6",
    "step7",
    "step8",
    "step9",
)


def _step(name: str, status: str, **fields: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"name": name, "status": status}
    out.update(fields)
    return out


def _module_checks(rules_fired: list[dict[str, Any]]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {}
    for rule in rules_fired:
        if not isinstance(rule, dict):
            continue
        mod = str(rule.get("module") or "other").strip().lower()
        label = str(rule.get("rule_id") or rule.get("label") or "").strip()
        note = str(rule.get("note") or rule.get("evidence") or rule.get("label") or "").strip()
        line = f"{label}: {note}" if label and note and label not in note else (note or label)
        if not line:
            continue
        buckets.setdefault(mod, [])
        if line not in buckets[mod]:
            buckets[mod].append(line[:200])
    return buckets


def build_mr_step_audit_from_result(result: Any) -> dict[str, Any]:
    """Structured step audit from EngineResult — saved on every MR static answer."""
    checks = dict(getattr(result, "checks", None) or {})
    archetype = str(getattr(result, "archetype", "") or "").strip()
    rules_fired = list(checks.get("rules_fired") or [])
    modules_used = list(checks.get("modules_used") or [])
    narrator_input = checks.get("narrator_input")
    scorecard = checks.get("scorecard") if isinstance(checks.get("scorecard"), dict) else {}
    explanation = checks.get("explanation") if isinstance(checks.get("explanation"), dict) else {}

    pos = list(getattr(result, "evidence_positive", None) or [])
    neg = list(getattr(result, "evidence_negative", None) or [])
    module_checks = _module_checks(rules_fired)

    return {
        "step1": _step(
            "Engine Selected",
            "DONE",
            engine=archetype,
            engine_version=checks.get("engine_version"),
            rules_version=checks.get("rules_version"),
        ),
        "step2": _step(
            "Modules Loaded",
            "DONE",
            loaded=modules_used,
            skipped=[
                m
                for m in ("d1", "d9", "dasha", "transit", "kp", "jaimini", "bcp")
                if m not in {str(x).lower() for x in modules_used}
            ],
        ),
        "step3": _step(
            "Astrology Checks",
            "DONE",
            d1=module_checks.get("d1", [])[:8],
            d9=module_checks.get("d9", [])[:8],
            dasha=module_checks.get("dasha", [])[:6],
            transit=module_checks.get("transit", [])[:6],
            kp=module_checks.get("kp", [])[:6],
            jaimini=module_checks.get("jaimini", [])[:4],
            bcp=module_checks.get("bcp", [])[:4],
        ),
        "step4": _step(
            "Rules Fired",
            "DONE",
            fired=rules_fired[:40],
            count=len(rules_fired),
        ),
        "step5": _step(
            "Planet Evidence",
            "DONE",
            positive=pos[:12],
            negative=neg[:12],
        ),
        "step6": _step(
            "Conflict Resolution",
            "DONE",
            detected=bool(checks.get("contradiction")),
            pattern=checks.get("contradiction_pattern") or "",
            summary=(checks.get("contradiction_detail") or {}).get("summary")
            if isinstance(checks.get("contradiction_detail"), dict)
            else "",
        ),
        "step7": _step(
            "Scorecard",
            "DONE",
            scorecard=scorecard,
            primary_score=checks.get("primary_score"),
        ),
        "step8": _step(
            "Final Verdict",
            "DONE",
            verdict=str(getattr(result, "verdict", "") or ""),
            level=checks.get("commitment_level") or checks.get("level") or "",
            confidence=str(getattr(result, "confidence", "") or ""),
            strongest=explanation.get("strongest_factor"),
            weakest=explanation.get("weakest_factor"),
        ),
        "step9": _step(
            "Narrator Input JSON",
            "DONE" if narrator_input else "SKIPPED",
            narrator_input=narrator_input if isinstance(narrator_input, dict) else None,
        ),
        "step_order": list(MR_PIPELINE_STEP_ORDER),
    }

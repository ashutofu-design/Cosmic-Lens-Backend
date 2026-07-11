"""Relationship decisions engine narrator — templates + fired rules only."""
from __future__ import annotations

import json
import re
from typing import Any

from .commitment_narrator import (
    _all_engine_evidence,
    _build_confidence_explanation,
    _build_ignored_evidence,
    _compact_evidence_line,
    _confidence_label_from_score,
    _evidence_from_rules,
    _promote_moon_to_weakest,
)
from .relationship_decisions_templates import (
    LEVEL_SCORE_FALLBACK,
    USER_SECTION,
    VERDICT_LABELS,
    detect_relationship_decisions_answer_focus,
    effects_from_evidence,
    get_meaning,
    get_opening,
    get_practical,
    get_rdec_outlook,
)
from .types import EngineResult

_BANNED_NARRATOR_PHRASES = re.compile(
    r"(?i)\b("
    r"the\s+big\s+picture|kehna mushkil|ho sakta hai|ho sakti hai|shayad|lagta hai|"
    r"emotional\s+attachment|emotional\s+confusion|clarity\s+chahiye|"
    r"patience\s+rakho|open\s+communication|honest\s+check-in|"
    r"perfect\s+partner|soul\s*mate"
    r")\b",
)

_ALWAYS_BANNED_WORDS = ("clarity", "patience", "the big picture", "emotional attachment")


def _resolve_rdec_level(checks: dict[str, Any]) -> str:
    level = str(
        checks.get("decision_level")
        or checks.get("relationship_decisions_level")
        or checks.get("rdec_level")
        or checks.get("level")
        or ""
    ).strip().lower()
    if level in VERDICT_LABELS:
        return level
    blob = f"{checks.get('headline') or ''} {checks.get('verdict') or ''} {checks.get('decision_posture') or ''}".lower()
    for key in ("favorable", "cautious", "avoid", "wait"):
        if key in blob:
            return key
    if "lean_stay" in blob:
        return "favorable"
    if "mixed_weigh" in blob:
        return "wait"
    if "caution_leave" in blob or "pause_and_clarify" in blob:
        return "cautious"
    return "wait"


def _resolve_confidence(level: str, checks: dict[str, Any]) -> tuple[int, str]:
    score = 0
    try:
        score = int(checks.get("primary_score") or 0)
    except (TypeError, ValueError):
        score = 0
    if score <= 0:
        score = LEVEL_SCORE_FALLBACK.get(level, 55)
    return score, _confidence_label_from_score(score)


def _join_effect_lines(items: list[str], *, prefix: str, fallback: str, limit: int = 3) -> str:
    effects = effects_from_evidence(items, limit=limit)
    if not effects:
        return fallback
    if len(effects) == 1:
        return f"{prefix} {effects[0]}"
    if len(effects) == 2:
        return f"{prefix} {effects[0]} Saath hi {effects[1]}"
    return f"{prefix} {effects[0]} Saath hi {effects[1]} Aur {effects[2]}"


def _build_reason_summary(strongest: list[str], weakest: list[str], verdict: str) -> str:
    n_pos = len([x for x in strongest if str(x).strip()])
    n_neg = len([x for x in weakest if str(x).strip()])
    if n_pos and n_neg:
        return f"Chart analysis me {n_pos} supportive aur {n_neg} challenging decision indicators mile. Isi wajah se final verdict {verdict} hai."
    if n_neg:
        return f"Chart me challenging decision indicators zyada active hain. Isi wajah se final verdict {verdict} hai."
    if n_pos:
        return f"Chart me supportive decision indicators zyada dikhte hain. Isi wajah se final verdict {verdict} hai."
    return f"Chart ke signals limited ya mixed hain — isi wajah se final verdict {verdict} hai."


def render_relationship_decisions_template_answer(data: dict[str, Any], question: str = "", *, lang: str = "hn") -> str:
    verdict = str(data.get("final_verdict") or "Wait")
    level = str(data.get("decision_level") or data.get("relationship_decisions_level") or verdict).strip().lower()
    angle = str(data.get("answer_focus") or data.get("decision_angle") or "general_decision")
    strongest = list(data.get("strongest") or [])
    weakest = list(data.get("weakest") or [])
    score = int(data.get("confidence") or 0)
    conf_label = str(data.get("confidence_label") or "Medium")
    scorecard = data.get("scorecard") if isinstance(data.get("scorecard"), dict) else {}

    parts = [
        str(data.get("direct_answer") or "").strip() or get_opening(angle, level),
        f"{USER_SECTION['why_verdict']} {_build_reason_summary(strongest, weakest, verdict)}",
        _join_effect_lines(strongest, prefix=USER_SECTION["positive"], fallback=f"{USER_SECTION['positive']} supportive decision indicators limited hain."),
        _join_effect_lines(weakest, prefix=USER_SECTION["challenges"], fallback=f"{USER_SECTION['challenges']} challenging decision indicators active hain."),
        f"{USER_SECTION['meaning']} {str(data.get('meaning_note') or '').strip() or get_meaning(angle, level)}",
        f"{USER_SECTION['outlook']} {str(data.get('rdec_outlook') or '').strip() or get_rdec_outlook(level)}",
        f"{USER_SECTION['focus']} {str(data.get('practical_guidance') or '').strip() or get_practical(angle, level)}",
        _build_confidence_explanation(score, conf_label, strongest, weakest, scorecard),
    ]
    return "\n\n".join(parts)


def validate_relationship_decisions_narrator_output(text: str, data: dict[str, Any]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    t = (text or "").strip()
    if not t:
        return False, ["empty"]
    level = str(data.get("decision_level") or data.get("relationship_decisions_level") or "").strip().lower()
    if level == "avoid" and re.search(r"(?i)\b(mostly\s+favorable|forward\s+step\s+supports|strong\s+room)\b", t):
        issues.append("contradiction_avoid")
    if level == "favorable" and re.search(r"(?i)\b(avoid\s+impulse|blindly\s+mat|exit\s+ya\s+hard)\b", t):
        issues.append("contradiction_favorable")
    if _BANNED_NARRATOR_PHRASES.search(t):
        issues.append("banned_phrase")
    tl = t.lower()
    for banned in _ALWAYS_BANNED_WORDS:
        if banned in tl:
            issues.append(f"banned_{banned.replace(' ', '_')}")
    if "mukhya sanket" not in tl and "support karne wale" not in tl:
        issues.append("missing_positive_section")
    if "dhyan dene layak" not in tl:
        issues.append("missing_challenges_section")
    score = int(data.get("confidence") or 0)
    label = str(data.get("confidence_label") or "Medium")
    if not re.search(rf"Confidence\s+{re.escape(label)}\s*\(\s*{score}\s*%\)", t, re.I):
        issues.append("confidence_line")
    return len(issues) == 0, issues


def engine_result_to_relationship_decisions_json(
    result: EngineResult,
    question: str = "",
    *,
    question_dna: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checks = dict(result.checks or {})
    q = (question or str(checks.get("question") or "")).strip()
    angle = detect_relationship_decisions_answer_focus(q, question_dna=question_dna)
    level = _resolve_rdec_level(checks)
    checks.update({
        "decision_angle": angle,
        "question": q,
        "decision_level": level,
        "relationship_decisions_level": level,
        "rdec_level": level,
    })

    verdict_label = VERDICT_LABELS.get(level, level.title())
    scorecard = checks.get("scorecard") if isinstance(checks.get("scorecard"), dict) else {}
    score, conf_label = _resolve_confidence(level, checks)
    rules_fired = list(checks.get("rules_fired") or [])
    strongest, strongest_rids = _evidence_from_rules(rules_fired, polarity="positive", limit=3)
    weakest, weakest_rids = _evidence_from_rules(rules_fired, polarity="negative", limit=3)
    explanation = checks.get("explanation") if isinstance(checks.get("explanation"), dict) else {}
    if not strongest:
        for item in (result.evidence_positive or [])[:3]:
            line = _compact_evidence_line(str(item))
            if line and line not in strongest:
                strongest.append(line)
    if not strongest:
        for item in (result.evidence or [])[:3]:
            line = _compact_evidence_line(str(item))
            if line and ("support" in line.lower() or "stay" in line.lower()):
                if line not in strongest:
                    strongest.append(line)
    if not weakest:
        wf = str(explanation.get("weakest_factor") or "").strip()
        if wf:
            weakest.append(_compact_evidence_line(wf))
        for item in (result.evidence_negative or [])[:3]:
            line = _compact_evidence_line(str(item))
            if line and line not in weakest:
                weakest.append(line)
        for item in (result.evidence or [])[:3]:
            line = _compact_evidence_line(str(item))
            if line and ("pressure" in line.lower() or "separation" in line.lower()):
                if line and line not in weakest:
                    weakest.append(line)
    weakest = _promote_moon_to_weakest(weakest[:3], result)[:3]
    all_evidence = _all_engine_evidence(result, rules_fired)
    ignored_evidence = _build_ignored_evidence(all_evidence, strongest[:3], weakest[:3])

    payload: dict[str, Any] = {
        "question_type": "relationship_decisions",
        "original_question": q,
        "decision_angle": angle,
        "answer_focus": angle,
        "decision_level": level,
        "relationship_decisions_level": level,
        "final_verdict": verdict_label,
        "direct_answer": get_opening(angle, level),
        "meaning_note": get_meaning(angle, level),
        "rdec_outlook": get_rdec_outlook(level),
        "practical_guidance": get_practical(angle, level),
        "strongest": strongest[:3],
        "weakest": weakest[:3],
        "strongest_rule_ids": strongest_rids[:3],
        "weakest_rule_ids": weakest_rids[:3],
        "confidence": score,
        "confidence_label": conf_label,
        "verdict": verdict_label,
        "scorecard": {k: int(v) for k, v in scorecard.items() if isinstance(v, (int, float))},
        "rules_fired_count": len(rules_fired),
        "ignored_evidence": ignored_evidence,
    }
    payload["_checks"] = checks
    payload["locked_template"] = render_relationship_decisions_template_answer(payload, question=q)
    return payload


def relationship_decisions_engine_narrator_payload(
    result: EngineResult,
    *,
    wants_explain: bool = False,
    question: str = "",
    question_dna: dict[str, Any] | None = None,
) -> str:
    q = (question or str((result.checks or {}).get("question") or "")).strip()
    data = engine_result_to_relationship_decisions_json(result, question=q, question_dna=question_dna)
    data.pop("_checks", None)
    locked = data.pop("locked_template", "")
    json_block = json.dumps(data, indent=2, ensure_ascii=False)
    return "\n".join([
        "ARCHETYPE: relationship_decisions",
        "SOURCE_LOCK: ENGINE_JSON_ONLY — narrate ONLY fired rules in JSON.",
        "ENGINE_JSON:", json_block, "",
        f"ANSWER_FOCUS: {data.get('answer_focus')}",
        f"ORIGINAL_QUESTION: {data.get('original_question', q)}", "",
        "LOCKED_TEMPLATE:", locked, "",
        "RULES: Use direct_answer verbatim. Never contradict avoid verdict with 'mostly favorable'.",
        "BANNED: clarity, patience, emotional attachment, The Big Picture.",
    ])

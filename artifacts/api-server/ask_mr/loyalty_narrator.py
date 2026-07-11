"""Loyalty / trust engine narrator — templates + fired rules only."""
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
from .loyalty_templates import (
    LEVEL_SCORE_FALLBACK,
    USER_SECTION,
    VERDICT_LABELS,
    detect_loyalty_answer_focus,
    effects_from_evidence,
    get_meaning,
    get_opening,
    get_practical,
)
from .types import EngineResult

_BANNED_NARRATOR_PHRASES = re.compile(
    r"(?i)\b("
    r"the\s+big\s+picture|kehna mushkil|ho sakta hai|ho sakti hai|shayad|lagta hai|"
    r"emotional\s+attachment|emotional\s+confusion|clarity\s+chahiye|"
    r"patience\s+rakho|boundaries|open\s+communication|honest\s+check-in|"
    r"haan,?\s+chances"
    r")\b",
)

_ALWAYS_BANNED_WORDS = (
    "clarity",
    "patience",
    "boundaries",
    "the big picture",
    "emotional attachment",
)


def _resolve_loyalty_level(checks: dict[str, Any]) -> str:
    level = str(
        checks.get("trust_level")
        or checks.get("loyalty_level")
        or checks.get("level")
        or ""
    ).strip().lower()
    if level in VERDICT_LABELS:
        return level
    headline = str(checks.get("headline") or "").lower()
    for key in VERDICT_LABELS:
        if key in headline:
            return key
    return "mixed"


def _resolve_confidence(level: str, checks: dict[str, Any]) -> tuple[int, str]:
    score = 0
    try:
        score = int(checks.get("primary_score") or 0)
    except (TypeError, ValueError):
        score = 0
    if score <= 0:
        score = LEVEL_SCORE_FALLBACK.get(level, 48)
    return score, _confidence_label_from_score(score)


def _join_effect_lines(
    items: list[str],
    *,
    prefix: str,
    fallback: str,
    limit: int = 3,
) -> str:
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
        return (
            f"Chart analysis me {n_pos} supportive aur {n_neg} challenging trust indicators mile. "
            f"Isi wajah se final verdict {verdict} hai."
        )
    if n_neg:
        return (
            f"Chart me trust-challenging indicators zyada active hain. "
            f"Isi wajah se final verdict {verdict} hai."
        )
    if n_pos:
        return (
            f"Chart me trust-supportive indicators zyada dikhte hain. "
            f"Isi wajah se final verdict {verdict} hai."
        )
    return f"Chart ke signals limited ya mixed hain — isi wajah se final verdict {verdict} hai."


def render_loyalty_template_answer(
    data: dict[str, Any],
    question: str = "",
    *,
    lang: str = "hn",
) -> str:
    verdict = str(data.get("final_verdict") or data.get("verdict") or "Mixed")
    level = str(data.get("loyalty_level") or verdict).strip().lower()
    angle = str(data.get("answer_focus") or data.get("loyalty_angle") or "general_trust")
    strongest = list(data.get("strongest") or [])
    weakest = list(data.get("weakest") or [])
    score = int(data.get("confidence") or 0)
    conf_label = str(data.get("confidence_label") or "Medium")
    scorecard = data.get("scorecard") if isinstance(data.get("scorecard"), dict) else {}

    p1 = str(data.get("direct_answer") or "").strip() or get_opening(angle, level)
    p2 = f"{USER_SECTION['why_verdict']} {_build_reason_summary(strongest, weakest, verdict)}"
    p3 = _join_effect_lines(
        strongest,
        prefix=USER_SECTION["positive"],
        fallback=f"{USER_SECTION['positive']} trust-supportive indicators limited hain.",
    )
    p4 = _join_effect_lines(
        weakest,
        prefix=USER_SECTION["challenges"],
        fallback=f"{USER_SECTION['challenges']} trust-challenging indicators active hain.",
    )
    meaning = str(data.get("meaning_note") or "").strip() or get_meaning(angle, level)
    practical = str(data.get("practical_guidance") or "").strip() or get_practical(angle, level)

    parts = [
        p1,
        p2,
        p3,
        p4,
        f"{USER_SECTION['meaning']} {meaning}",
        f"{USER_SECTION['focus']} {practical}",
        _build_confidence_explanation(score, conf_label, strongest, weakest, scorecard),
    ]
    return "\n\n".join(parts)


def validate_loyalty_narrator_output(text: str, data: dict[str, Any]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    t = (text or "").strip()
    if not t:
        return False, ["empty"]
    level = str(data.get("loyalty_level") or data.get("final_verdict") or "").strip().lower()
    angle = str(data.get("answer_focus") or "").strip().lower()
    if level == "risky" and angle == "cheating_risk":
        if re.search(r"(?i)\b(haan,?\s+chances|mostly\s+loyal|trustworthy\s+dikhta)\b", t):
            issues.append("contradiction_risky_cheating")
    if level == "risky" and re.search(r"(?i)\b(haan,?\s+chances|shayad\s+loyal)\b", t):
        issues.append("contradiction_risky_verdict")
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


def engine_result_to_loyalty_json(
    result: EngineResult,
    question: str = "",
    *,
    question_dna: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checks = dict(result.checks or {})
    q = (question or str(checks.get("question") or "")).strip()
    angle = detect_loyalty_answer_focus(q, question_dna=question_dna)
    level = _resolve_loyalty_level(checks)
    checks.update({"loyalty_angle": angle, "question": q, "trust_level": level})

    verdict_label = VERDICT_LABELS.get(level, level.title() if level else "Mixed")
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
    if not weakest:
        wf = str(explanation.get("weakest_factor") or "").strip()
        if wf:
            weakest.append(_compact_evidence_line(wf))
        for item in (result.evidence_negative or [])[:3]:
            line = _compact_evidence_line(str(item))
            if line and line not in weakest:
                weakest.append(line)
    weakest = _promote_moon_to_weakest(weakest[:3], result)[:3]

    all_evidence = _all_engine_evidence(result, rules_fired)
    ignored_evidence = _build_ignored_evidence(all_evidence, strongest[:3], weakest[:3])

    payload: dict[str, Any] = {
        "question_type": "loyalty_trust",
        "original_question": q,
        "loyalty_angle": angle,
        "answer_focus": angle,
        "primary_user_concern": angle,
        "opening_style": angle,
        "loyalty_level": level,
        "final_verdict": verdict_label,
        "direct_answer": get_opening(angle, level),
        "meaning_note": get_meaning(angle, level),
        "practical_guidance": get_practical(angle, level),
        "strongest": strongest[:3],
        "weakest": weakest[:3],
        "strongest_rule_ids": strongest_rids[:3],
        "weakest_rule_ids": weakest_rids[:3],
        "strongest_effects": effects_from_evidence(strongest, limit=3),
        "weakest_effects": effects_from_evidence(weakest, limit=3),
        "ignored_evidence": ignored_evidence,
        "warnings": weakest[:2],
        "confidence": score,
        "confidence_label": conf_label,
        "verdict": verdict_label,
        "scorecard": {k: int(v) for k, v in scorecard.items() if isinstance(v, (int, float))},
        "rules_fired_count": len(rules_fired),
    }
    payload["_checks"] = checks
    payload["locked_template"] = render_loyalty_template_answer(payload, question=q)
    return payload


def loyalty_narrator_payload(
    result: EngineResult,
    *,
    wants_explain: bool = False,
    question: str = "",
    question_dna: dict[str, Any] | None = None,
) -> str:
    q = (question or str((result.checks or {}).get("question") or "")).strip()
    data = engine_result_to_loyalty_json(result, question=q, question_dna=question_dna)
    data.pop("_checks", None)
    locked = data.pop("locked_template", "")
    json_block = json.dumps(data, indent=2, ensure_ascii=False)
    return "\n".join([
        "ARCHETYPE: loyalty_trust",
        "SOURCE_LOCK: ENGINE_JSON_ONLY — narrate ONLY fired rules in JSON.",
        "ENGINE_JSON:",
        json_block,
        "",
        f"ANSWER_FOCUS: {data.get('answer_focus')}",
        f"ORIGINAL_QUESTION: {data.get('original_question', q)}",
        "",
        "LOCKED_TEMPLATE:",
        locked,
        "",
        "RULES: Use direct_answer verbatim. Never contradict risky verdict with 'loyal/chances'.",
        "BANNED: clarity, patience, boundaries, emotional attachment, The Big Picture.",
    ])

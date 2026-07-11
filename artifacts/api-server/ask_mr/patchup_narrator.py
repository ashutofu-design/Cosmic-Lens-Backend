"""Patch-up / reconciliation engine narrator — evidence-bound, intent-anchored answers."""
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
from .types import EngineResult
from .user_section_labels import NATURAL_USER_SECTION as _NATURAL_SEC

_VERDICT_LABELS = {
    "favorable": "Favorable",
    "possible": "Possible",
    "weak": "Weak",
    "unlikely": "Unlikely",
}

_LEVEL_SCORE_FALLBACK = {
    "favorable": 78,
    "possible": 62,
    "weak": 48,
    "unlikely": 22,
}

_BANNED_NARRATOR_PHRASES = re.compile(
    r"(?i)\b("
    r"the\s+big\s+picture|kehna mushkil|ho sakta hai|ho sakti hai|shayad|lagta hai|"
    r"emotional\s+attachment|emotional\s+confusion|clarity\s+chahiye|"
    r"patience\s+rakho|boundaries|open\s+communication|honest\s+check-in"
    r")\b",
)

_ALWAYS_BANNED_WORDS = (
    "clarity",
    "patience",
    "boundaries",
    "the big picture",
    "emotional attachment",
    "emotional confusion",
)

_PATCH_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"separation\s+yoga|separation\s+friction", re.I), "Separation ke yog reconciliation ko weak karte hain."),
    (re.compile(r"relationship\s+axis.*friction|d1\s+relationship", re.I), "Relationship axis par friction patch-up ko slow ya difficult banata hai."),
    (re.compile(r"\bsaturn\b.*7th|saturn\s+on\s+7th", re.I), "Delay aur distance reconciliation me extra challenge la sakte hain."),
    (re.compile(r"\bmars\b.*7th|mars\s+on\s+7th", re.I), "Conflict / impulse reconciliation ko test karta hai."),
    (re.compile(r"moon\s+afflict|moon\s+under", re.I), "Emotional instability reconciliation ko mushkil bana sakti hai."),
    (re.compile(r"reconnection|reconnect|5th\s*lord\s+strong|emotional\s+reopening", re.I), "Reconnection ke supportive indicators dikhte hain."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase reconciliation signals ko colour karti hai."),
]

_USER_SECTION = dict(_NATURAL_SEC)

_ANGLE_OPENINGS: dict[str, dict[str, str]] = {
    "ex_return": {
        "favorable": (
            "Chart ke hisaab se previous relationship ke wapas aane / reconciliation ke "
            "supportive yog dikhte hain — lekin dono taraf se honest repair zaruri hai."
        ),
        "possible": (
            "Chart me ex ke wapas aane ke possible signals hain, lekin patch-up tabhi "
            "stable rahega jab real repair aur changed behaviour dikhe."
        ),
        "weak": (
            "Is chart ke hisaab se previous relationship ke wapas aane ke yog abhi weak dikhte hain — "
            "distance aur friction active hain."
        ),
        "unlikely": (
            "Is chart ke hisaab se previous relationship ke naturally wapas aane ke yog filhaal kamzor dikhte hain. "
            "Agar reconciliation hoti bhi hai, to bina major changes aur relationship repair ke uske tikne ke yog kam hain."
        ),
    },
    "second_chance": {
        "favorable": "Second chance dene ke supportive chart signals hain — lekin dono ki readiness verify karein.",
        "possible": "Second chance possible hai, par sirf tab jab core issues genuinely address ho rahe hon.",
        "weak": "Abhi second chance ke yog weak hain — friction aur distance reconciliation ko slow karte hain.",
        "unlikely": (
            "Abhi second chance / reconciliation ke strong yog nahi dikhte — "
            "bina real repair ke patch-up stable rehna mushkil hoga."
        ),
    },
    "ex_contact": {
        "favorable": "Ex se contact / reconnection ke supportive timing ya signals dikh rahe hain.",
        "possible": "Contact possible dikhta hai, lekin conversation se pehle intent verify karein.",
        "weak": "Contact ke yog weak hain — distance themes abhi zyada active hain.",
        "unlikely": "Filhaal ex se meaningful contact / unblock ke strong yog kam dikhte hain.",
    },
    "reconciliation_timing": {
        "favorable": "Timing supportive dikhti hai — reconciliation window open reh sakta hai.",
        "possible": "Kuch supportive timing hints hain, par effort aur repair ke bina window miss ho jayegi.",
        "weak": "Abhi reconciliation timing weak hai — better alignment baad me dikh sakti hai.",
        "unlikely": "Filhaal reconciliation ke liye strong timing support nahi dikhta — delay ke yog zyada hain.",
    },
    "general_reconciliation": {
        "favorable": "Reconciliation / patch-up ke supportive chart signals hain.",
        "possible": "Reconciliation possible hai, par consistent repair effort ke bina stable nahi rahega.",
        "weak": "Reconciliation ke yog abhi weak hain — friction active hai.",
        "unlikely": "Reconciliation ke strong yog filhaal kam hain — repair ke bina patch-up mushkil hai.",
    },
}


def _resolve_patchup_level(checks: dict[str, Any]) -> str:
    level = str(
        checks.get("patchup_level")
        or checks.get("level")
        or checks.get("commitment_level")
        or ""
    ).strip().lower()
    if level in _VERDICT_LABELS:
        return level
    headline = str(checks.get("headline") or "").lower()
    for key in _VERDICT_LABELS:
        if key in headline:
            return key
    return "weak"


def _resolve_confidence(level: str, checks: dict[str, Any], scorecard: dict[str, Any]) -> tuple[int, str]:
    score = 0
    try:
        score = int(checks.get("primary_score") or 0)
    except (TypeError, ValueError):
        score = 0
    if score <= 0:
        score = _LEVEL_SCORE_FALLBACK.get(level, 48)
    return score, _confidence_label_from_score(score)


def _patch_evidence_to_effect(raw: str, *, rule_id: str = "") -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in _PATCH_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me reconciliation-related friction active hai."


def _patch_effects_from_evidence(items: list[str], *, limit: int = 3, rule_ids: list[str] | None = None) -> list[str]:
    out: list[str] = []
    rids = rule_ids or []
    for i, raw in enumerate(items):
        eff = _patch_evidence_to_effect(str(raw), rule_id=rids[i] if i < len(rids) else "")
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out


def _build_angle_direct_answer(level: str, angle: str) -> str:
    lv = (level or "weak").strip().lower()
    ang = (angle or "general_reconciliation").strip().lower()
    openings = _ANGLE_OPENINGS.get(ang) or _ANGLE_OPENINGS["general_reconciliation"]
    return openings.get(lv) or openings.get("weak", openings["unlikely"])


def _build_reason_summary(strongest: list[str], weakest: list[str], verdict: str) -> str:
    n_pos = len([x for x in strongest if str(x).strip()])
    n_neg = len([x for x in weakest if str(x).strip()])
    if n_pos and n_neg:
        return (
            f"Chart analysis me {n_pos} supportive aur {n_neg} challenging reconciliation indicators mile. "
            f"Isi wajah se final verdict {verdict} hai."
        )
    if n_neg:
        return (
            f"Chart me reconciliation-challenging indicators zyada active hain. "
            f"Isi wajah se final verdict {verdict} hai."
        )
    if n_pos:
        return (
            f"Chart me reconciliation-supportive indicators zyada dikhte hain. "
            f"Isi wajah se final verdict {verdict} hai."
        )
    return f"Chart ke signals mixed ya limited hain — isi wajah se final verdict {verdict} hai."


def _build_meaning_note(level: str) -> str:
    lv = (level or "").strip().lower()
    if lv == "unlikely":
        return (
            "Agar ex khud se wapas bhi aaye, to bina original issues solve kiye "
            "patch-up long-term stable rehna mushkil hoga."
        )
    if lv == "weak":
        return "Reconciliation tabhi meaningful hogi jab distance ke reasons genuinely address hon."
    if lv == "possible":
        return "Patch-up tabhi tik sakta hai jab dono taraf behaviour change dikhe, sirf emotions wapas aane se nahi."
    return "Supportive window hai, lekin reconciliation ke liye consistent repair effort zaruri hai."


def _build_conditions_line(level: str, weakest: list[str]) -> str:
    lv = (level or "").strip().lower()
    if lv in ("favorable", "possible"):
        return (
            "Agar wapas aaye, to tabhi positive tab jab repeated actions, accountability aur "
            "core issues par real repair dikhe — sirf message ya temporary closeness se nahi."
        )
    return (
        "Agar koi contact ya return hint dikhe bhi, to tabhi consider karein jab circumstances aur "
        "behaviour pehle se genuinely badle hon — warna same friction dubara active ho sakte hain."
    )


def _build_practical_guidance(level: str, weakest: list[str]) -> str:
    blob = " ".join(weakest).lower()
    lv = (level or "").strip().lower()
    if lv in ("unlikely", "weak"):
        return (
            "Reconciliation consider karte hain to pehle dekhein ki behaviour aur circumstances "
            "badle hain ya sirf missing-feeling / emotions wapas aaye hain."
        )
    if "separation" in blob:
        return "Separation signals active hain — wapas aane se pehle reason-of-breakup par honest assessment karein."
    return "Patch-up tabhi pursue karein jab actions aur accountability feelings se aage dikhein."


def _build_timing_answer(checks: dict[str, Any], result: EngineResult, level: str, angle: str) -> dict[str, str] | None:
    timing = checks.get("timing") if isinstance(checks.get("timing"), dict) else {}
    windows = timing.get("windows") or []
    window = ""
    if windows and isinstance(windows[0], dict):
        window = str(windows[0].get("label") or windows[0].get("window") or "").strip()

    dasha_support = "unknown"
    for rule in checks.get("rules_fired") or []:
        if not isinstance(rule, dict):
            continue
        blob = " ".join(str(rule.get(k) or "") for k in ("note", "evidence", "label", "module")).lower()
        if "dasha" not in blob:
            continue
        pol = str(rule.get("polarity") or "").strip().lower()
        if pol == "positive":
            dasha_support = "positive"
            break
        if pol == "negative":
            dasha_support = "negative"

    if str(checks.get("mode") or "").lower() != "timing" and not window:
        return None

    if dasha_support == "positive" and window:
        summary = f"Current dasha reconciliation ko support karti hai — supportive window {window} dikhta hai."
    elif dasha_support == "positive":
        summary = "Current dasha reconciliation conversations ke liye relatively supportive dikhti hai."
    elif dasha_support == "negative" and window:
        summary = (
            f"Abhi dasha delay / test dikha rahi hai — zyada supportive reconciliation phase "
            f"{window} ke around dikh sakta hai."
        )
    elif window:
        summary = f"Reconciliation timing ke liye {window} relatively better phase dikhta hai."
    else:
        summary = (
            "Abhi strong reconciliation timing limited hai — next supportive dasha / transit phase me "
            "signals zyada settle ho jayenge."
        )
    return {"window": window, "dasha_support": dasha_support, "summary": summary}


def _join_patch_effect_lines(
    items: list[str],
    *,
    prefix: str,
    fallback: str,
    limit: int = 3,
    rule_ids: list[str] | None = None,
) -> str:
    effects = _patch_effects_from_evidence(items, limit=limit, rule_ids=rule_ids)
    if not effects:
        return fallback
    if len(effects) == 1:
        return f"{prefix} {effects[0]}"
    if len(effects) == 2:
        return f"{prefix} {effects[0]} Saath hi {effects[1]}"
    return f"{prefix} {effects[0]} Saath hi {effects[1]} Aur {effects[2]}"


def render_patchup_template_answer(data: dict[str, Any], question: str = "", *, lang: str = "hn") -> str:
    verdict = str(data.get("final_verdict") or data.get("verdict") or "Weak")
    level = str(data.get("patchup_level") or verdict).strip().lower()
    strongest = list(data.get("strongest") or [])
    weakest = list(data.get("weakest") or [])
    score = int(data.get("confidence") or 0)
    conf_label = str(data.get("confidence_label") or "Medium")
    scorecard = data.get("scorecard") if isinstance(data.get("scorecard"), dict) else {}
    strongest_rids = list(data.get("strongest_rule_ids") or [])
    weakest_rids = list(data.get("weakest_rule_ids") or [])
    angle = str(data.get("answer_focus") or data.get("reconciliation_angle") or "general_reconciliation")

    p1 = str(data.get("direct_answer") or "").strip() or _build_angle_direct_answer(level, angle)
    p2 = f"{_USER_SECTION['why_verdict']} {_build_reason_summary(strongest, weakest, verdict)}"
    p3 = _join_patch_effect_lines(
        strongest,
        prefix=_USER_SECTION["positive"],
        fallback=f"{_USER_SECTION['positive']} reconciliation-supportive indicators limited hain.",
        limit=3,
        rule_ids=strongest_rids,
    )
    p4 = _join_patch_effect_lines(
        weakest,
        prefix=_USER_SECTION["challenges"],
        fallback=f"{_USER_SECTION['challenges']} reconciliation-challenging indicators active hain.",
        limit=3,
        rule_ids=weakest_rids,
    )
    parts = [
        p1,
        p2,
        p3,
        p4,
        f"{_USER_SECTION['meaning']} {_build_meaning_note(level)}",
        f"{_USER_SECTION['conditions']} {_build_conditions_line(level, weakest)}",
    ]
    timing = data.get("timing") if isinstance(data.get("timing"), dict) else None
    if timing and str(timing.get("summary") or "").strip():
        parts.append(f"Timing: {str(timing.get('summary')).strip()}")
    parts.append(f"{_USER_SECTION['focus']} {_build_practical_guidance(level, weakest)}")
    parts.append(
        _build_confidence_explanation(
            score, conf_label, strongest, weakest, scorecard, topic="reconciliation"
        )
    )
    return "\n\n".join(parts)


def validate_patchup_narrator_output(text: str, data: dict[str, Any]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    t = (text or "").strip()
    if not t:
        return False, ["empty"]
    level = str(data.get("patchup_level") or data.get("final_verdict") or "").strip().lower()
    if level == "unlikely" and re.search(r"(?i)\b(haan,?\s+chances|chances\s+hain|ho\s+sakta)\b", t):
        issues.append("contradiction_unlikely_verdict")
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


def engine_result_to_patchup_json(result: EngineResult, question: str = "") -> dict[str, Any]:
    from ask_intent_fidelity import infer_reconciliation_angle

    checks = dict(result.checks or {})
    q = (question or str(checks.get("question") or "")).strip()
    angle = infer_reconciliation_angle(q) or "general_reconciliation"
    checks.update({"reconciliation_angle": angle, "question": q, "patchup_level": _resolve_patchup_level(checks)})

    level = str(checks.get("patchup_level") or "weak").strip().lower()
    verdict_label = _VERDICT_LABELS.get(level, level.title() if level else "Weak")

    scorecard = checks.get("scorecard") if isinstance(checks.get("scorecard"), dict) else {}
    score, conf_label = _resolve_confidence(level, checks, scorecard)

    rules_fired = list(checks.get("rules_fired") or [])
    strongest, strongest_rids = _evidence_from_rules(rules_fired, polarity="positive", limit=3)
    weakest, weakest_rids = _evidence_from_rules(rules_fired, polarity="negative", limit=3)

    explanation = checks.get("explanation") if isinstance(checks.get("explanation"), dict) else {}
    if not strongest:
        sf = str(explanation.get("strongest_factor") or "").strip()
        if sf:
            strongest.append(_compact_evidence_line(sf))
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

    warnings = [w for w in weakest[:2] if w]
    timing_block = _build_timing_answer(checks, result, level, angle)
    direct_answer = _build_angle_direct_answer(level, angle)

    payload: dict[str, Any] = {
        "question_type": "patchup",
        "original_question": q,
        "reconciliation_angle": angle,
        "answer_focus": angle,
        "primary_user_concern": angle,
        "opening_style": angle,
        "patchup_level": level,
        "final_verdict": verdict_label,
        "direct_answer": direct_answer,
        "strongest": strongest[:3],
        "weakest": weakest[:3],
        "strongest_rule_ids": strongest_rids[:3],
        "weakest_rule_ids": weakest_rids[:3],
        "strongest_effects": _patch_effects_from_evidence(strongest, limit=3, rule_ids=strongest_rids),
        "weakest_effects": _patch_effects_from_evidence(weakest, limit=3, rule_ids=weakest_rids),
        "ignored_evidence": ignored_evidence,
        "warnings": warnings,
        "confidence": score,
        "confidence_label": conf_label,
        "verdict": verdict_label,
        "scorecard": {k: int(v) for k, v in scorecard.items() if isinstance(v, (int, float))},
    }
    if timing_block:
        payload["timing"] = timing_block
    payload["_checks"] = checks
    payload["locked_template"] = render_patchup_template_answer(payload, question=q)
    return payload


def patchup_narrator_payload(
    result: EngineResult,
    *,
    wants_explain: bool = False,
    question: str = "",
) -> str:
    q = (question or str((result.checks or {}).get("question") or "")).strip()
    data = engine_result_to_patchup_json(result, question=q)
    data.pop("_checks", None)
    locked = data.pop("locked_template", "")
    json_block = json.dumps(data, indent=2, ensure_ascii=False)
    lines = [
        "ARCHETYPE: patchup",
        "SOURCE_LOCK: ENGINE_JSON_ONLY",
        "ENGINE_JSON:",
        json_block,
        "",
        f"ANSWER_FOCUS: {data.get('answer_focus', 'general_reconciliation')}",
        f"ORIGINAL_QUESTION: {data.get('original_question', q)}",
        "",
        "LOCKED_TEMPLATE:",
        locked,
        "",
        "RULES: Use direct_answer opening verbatim in meaning. Never contradict unlikely verdict with 'chances hain'.",
        "BANNED: clarity, patience, boundaries, emotional attachment, The Big Picture.",
    ]
    return "\n".join(lines)

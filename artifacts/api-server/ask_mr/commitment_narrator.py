"""Commitment engine narrator — JSON-only facts → natural Hinglish answer.

LLM never sees the kundli. It receives a compact ENGINE_JSON block plus strict
narration rules (direct answer → reasons → caution → timing → practical).
"""
from __future__ import annotations

import json
import re
from typing import Any

from .types import EngineResult

_VERDICT_LABELS = {
    "ready": "Ready",
    "cautious": "Cautious",
    "mixed": "Mixed",
    "low": "Low",
}

_LEVEL_SCORE_FALLBACK = {
    "ready": 82,
    "cautious": 68,
    "mixed": 55,
    "low": 42,
}

_BANNED_NARRATOR_PHRASES = re.compile(
    r"(?i)\b("
    r"kehna mushkil|mushkil hai ki|ho sakta hai|ho sakti hai|shayad|lagta hai|lagti hai|"
    r"perhaps|maybe|might|possibly|"
    r"patience rakho|boundaries set|communication strong|emotional clarity|"
    r"emotional investment|trust challenge|clear talk se|honest check-in|"
    r"feelings samjho|feelings ko samjho|clarity chahiye|sabr rakho|"
    r"boundaries set karo|open communication|honest conversation"
    r")\b",
)

_ALWAYS_BANNED_WORDS = (
    "clarity",
    "patience",
    "boundaries",
    "feelings samjho",
    "emotional investment",
    "open communication",
    "honest check-in",
)

_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"7th\s*lord.*dusthana|dusthana.*7th|partnership.*stability\s+weak|7th\s*lord\s+in\s+dusthana",
            re.I,
        ),
        "Long-term stability ko support milne me challenge dikh raha hai.",
    ),
    (
        re.compile(r"7th\s*lord.*debilit|debilit.*7th|commitment\s+structure\s+needs", re.I),
        "Commitment structure ko strengthen karne me extra challenge dikh raha hai.",
    ),
    (
        re.compile(r"7th\s*lord.*strong|structurally\s+strong|partnership/commitment\s+axis", re.I),
        "Partnership axis structurally strong hai — long-term pairing ko backing milti hai.",
    ),
    (
        re.compile(r"venus.*(afflict|debil|combust)|afflict.*venus", re.I),
        "Affection layer me friction ya inconsistency dikh sakti hai.",
    ),
    (
        re.compile(r"\bvenus\b", re.I),
        "Relationship me genuine affection aur warm bonding ko support milta hai.",
    ),
    (
        re.compile(r"jupiter.*(weak|dusthana)|weak\s+promise", re.I),
        "Long-term faith aur promise layer me weakness dikh rahi hai.",
    ),
    (
        re.compile(r"\bjupiter\b", re.I),
        "Long-term faith aur growth orientation commitment ko support karta hai.",
    ),
    (
        re.compile(r"\bsaturn\b|delay|hesitation", re.I),
        "Commitment lane me delay ya hesitation ka pattern dikh raha hai.",
    ),
    (
        re.compile(r"\bmoon\b", re.I),
        "Emotional ups-downs commitment consistency ko affect kar sakte hain.",
    ),
    (
        re.compile(r"\bmercury\b", re.I),
        "Day-to-day expression aur alignment factor chart me mixed dikh raha hai.",
    ),
    (
        re.compile(r"\bmars\b", re.I),
        "Passion ya impulse commitment pace ko affect kar sakta hai.",
    ),
    (
        re.compile(r"\brahu\b", re.I),
        "Attraction strong dikh rahi hai par stability verify karni padti hai.",
    ),
    (
        re.compile(r"\bdasha\b|\btransit\b|\bjaimini\b", re.I),
        "Current timing phase commitment signals ko colour kar raha hai.",
    ),
    (
        re.compile(r"5th.*7th|romance.*linkage", re.I),
        "Romance se commitment linkage supportive dikh raha hai.",
    ),
    (
        re.compile(r"\bbcp\b|marriage\s+linkage", re.I),
        "Marriage linkage pattern commitment direction ko affect karta hai.",
    ),
]

_TIMING_RX = re.compile(
    r"(?i)(late\s+20\d{2}|early\s+20\d{2}|mid\s+20\d{2}|"
    r"20\d{2}\s*(?:ke\s+)?(?:end|start|mid)|"
    r"timing[:\s]+[^.;]+|window[^.;]+|phase[^.;]+)"
)


def _evidence_to_effect(raw: str) -> str:
    """Translate engine evidence → real-life commitment effect (no planet jargon)."""
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in _EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\b(house|sign|lord|karak|axis|dignity|occupants|dusthana)\b", "", s, flags=re.I)
    cleaned = re.sub(r"\([^)]*\)", "", cleaned).strip(" ,;—-")
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    if len(cleaned) > 20:
        return cleaned[:120].rstrip(".") + "."
    return "Chart me ek commitment-related factor active hai."


def _effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = _evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out


def _extract_timing_window(result: EngineResult, checks: dict[str, Any]) -> str:
    timing_data = checks.get("timing") or {}
    windows = timing_data.get("windows") or []
    if windows:
        w0 = windows[0] if isinstance(windows[0], dict) else {}
        label = str(w0.get("label") or w0.get("window") or "").strip()
        if label:
            return label
    pool = list(result.evidence_positive or []) + list(result.evidence or [])
    for line in pool:
        m = _TIMING_RX.search(str(line))
        if m:
            return m.group(0).strip().rstrip(".")
    return ""


def _compact_evidence_line(raw: str, *, max_len: int = 96) -> str:
    """Keep engine evidence verbatim — first clause only, no humanize drift."""
    s = (raw or "").strip()
    if not s:
        return ""
    s = re.split(r"[;]\s*", s)[0].strip()
    s = re.sub(r"\s{2,}", " ", s)
    return s[:max_len]


def _evidence_from_rules(
    rules_fired: list[Any],
    *,
    polarity: str,
    limit: int = 3,
) -> list[str]:
    out: list[str] = []
    for rule in rules_fired:
        if not isinstance(rule, dict):
            continue
        if str(rule.get("polarity") or "").strip().lower() != polarity:
            continue
        note = str(rule.get("note") or rule.get("evidence") or rule.get("label") or "").strip()
        line = _compact_evidence_line(note)
        if line and line not in out:
            out.append(line)
        if len(out) >= limit:
            break
    return out


def _resolve_confidence(level: str, checks: dict[str, Any], scorecard: dict[str, Any]) -> tuple[int, str]:
    """Numeric score + certainty label — never 0% when engine ran."""
    score = 0
    try:
        score = int(
            checks.get("primary_score")
            or (scorecard.get("primary") if isinstance(scorecard, dict) else 0)
            or 0
        )
    except (TypeError, ValueError):
        score = 0
    if score <= 0:
        score = _LEVEL_SCORE_FALLBACK.get(level, 55)
    certainty = str(checks.get("confidence_certainty") or "").strip().title()
    if certainty not in ("High", "Medium", "Low"):
        certainty = "High" if score >= 78 else ("Medium" if score >= 52 else "Low")
    return score, certainty


def _question_angles(question: str, checks: dict[str, Any]) -> tuple[str, bool, bool]:
    from ask_intent_fidelity import infer_partner_commitment_angle

    angle = str(checks.get("commitment_angle") or infer_partner_commitment_angle(question) or "general_commitment")
    ql = (question or "").lower()
    timepass_q = bool(re.search(r"time\s*pass|timepass", ql)) or angle == "time_pass"
    genuine_q = bool(re.search(r"genuine|sachch", ql)) or angle == "genuine_intent"
    return angle, timepass_q, genuine_q


def _build_direct_answer(level: str, *, timepass_q: bool, genuine_q: bool) -> str:
    lv = (level or "mixed").strip().lower()
    if lv == "low":
        base = (
            "Is chart ke hisaab se abhi partner ki taraf se strong aur stable commitment ka support kam dikh raha hai."
        )
        if timepass_q and genuine_q:
            tail = (
                "Is stage par unhe fully serious ya long-term committed nahi maana ja sakta — "
                "genuine long-term intent abhi weak dikhta hai; timepass pattern zyada dikhta hai."
            )
        elif timepass_q:
            tail = "Is stage par unhe sirf timepass ya casual intent zyada maana ja sakta, fully serious nahi."
        else:
            tail = "Is stage par unhe fully serious ya long-term committed nahi maana ja sakta."
        return f"{base} {tail}"
    if lv == "ready":
        return (
            "Is chart ke hisaab se partner ki taraf se commitment support strong dikhta hai. "
            "Long-term serious intent ko chart backing milti hai."
        )
    if lv == "cautious":
        return (
            "Is chart ke hisaab se partner me interest hai lekin commitment abhi cautious / hesitant phase me hai. "
            "Full stability abhi develop ho rahi hai."
        )
    return (
        "Is chart ke hisaab se partner ke commitment signals mixed hain — "
        "supportive factors aur challenging factors dono ek saath dikh rahe hain."
    )


def _build_verdict_line(verdict_label: str) -> str:
    return f"Final Verdict: {verdict_label} commitment."


def _join_effect_lines(
    items: list[str],
    *,
    prefix: str,
    fallback: str,
    limit: int = 3,
) -> str:
    effects = _effects_from_evidence(items, limit=limit)
    if not effects:
        return fallback
    if len(effects) == 1:
        return f"{prefix} {effects[0]}"
    if len(effects) == 2:
        return f"{prefix} {effects[0]} Saath hi {effects[1]}"
    return f"{prefix} {effects[0]} Saath hi {effects[1]} Aur {effects[2]}"


def _build_meaning_note(level: str, warnings: list[str]) -> str:
    lv = (level or "").strip().lower()
    warn_blob = " ".join(warnings).lower()
    if "cheat" in warn_blob or "affair" in warn_blob:
        return "Ye cheating ka direct indication nahi hai — chart commitment hesitation dikha raha hai."
    if lv == "low":
        return (
            "Iska practical matlab: abhi partner ki taraf se long-term serious commitment ka "
            "support kam hai — ye rejection nahi, lekin readiness weak dikh rahi hai."
        )
    if lv == "ready":
        return (
            "Iska practical matlab: chart long-term serious intent ko backing deta hai — "
            "consistency ke saath verdict aur strong hota hai."
        )
    if lv == "cautious":
        return (
            "Iska practical matlab: interest hai lekin full stability abhi develop ho rahi hai — "
            "process slow ya hesitant phase me hai."
        )
    return (
        "Iska practical matlab: interest hai lekin long-term consistency abhi fully establish nahi — "
        "mixed phase me decision evidence aur repeated behaviour se lena better hai."
    )


def _build_practical_guidance(strongest: list[str], weakest: list[str]) -> str:
    """Evidence-tied observation — not generic counselling."""
    blob = " ".join(weakest + strongest).lower()
    if "7th" in blob or "dusthana" in blob or "stability" in blob:
        return (
            "Engine ke challenging stability signals ke hisaab se partner ke consistent actions "
            "aur long-term planning ko words se zyada verify karein."
        )
    if "saturn" in blob or "delay" in blob or "hesitation" in blob:
        return (
            "Engine delay/hesitation signal de raha hai — slow progress possible hai, "
            "lekin regular effort aur planning pattern dekhein."
        )
    if "venus" in blob and any(x in blob for x in ("afflict", "debil", "combust", "friction")):
        return (
            "Affection layer me friction signal hai — warmth ko sirf words se nahi, "
            "repeated behaviour se match karein."
        )
    if "jupiter" in blob:
        return (
            "Long-term faith signals supportive hain — lekin partner ke behaviour se "
            "future planning match honi chahiye."
        )
    return (
        "Engine mixed signals de raha hai — partner ke consistent behaviour aur "
        "long-term planning ko observe karein, sirf promises par depend mat karein."
    )


def _build_scorecard_note(scorecard: dict[str, Any]) -> str:
    if not scorecard:
        return ""
    commit = scorecard.get("commitment")
    trust = scorecard.get("trust")
    comm = scorecard.get("communication")
    if commit is None:
        return ""
    header = f"Scorecard: Commitment {commit}"
    if trust is not None:
        header += f", Trust {trust}"
    if comm is not None:
        header += f", Communication {comm}"
    header += "."
    notes: list[str] = []
    if comm is not None and int(comm) < 50:
        notes.append(
            f"Communication score ({comm}) relatively kam hai — day-to-day alignment abhi fully strong nahi."
        )
    elif trust is not None and int(trust) < 50:
        notes.append(
            f"Trust score ({trust}) moderate hai — reliability signals abhi poori tarah establish nahi."
        )
    elif int(commit) < 50:
        notes.append(
            f"Commitment score ({commit}) moderate hai — long-term intent abhi developing phase me hai."
        )
    return header + (" " + notes[0] if notes else "")


def _build_confidence_explanation(
    score: int,
    conf_label: str,
    strongest: list[str],
    weakest: list[str],
    scorecard: dict[str, Any],
) -> str:
    reasons: list[str] = []
    if strongest and weakest:
        reasons.append("positive aur negative dono tarah ke indicators ek saath mile")
    elif strongest:
        reasons.append("zyada tar indicators commitment-supporting direction me hain")
    elif weakest:
        reasons.append("zyada tar indicators commitment-challenging direction me hain")

    if strongest and weakest and abs(len(strongest) - len(weakest)) <= 1:
        reasons.append("chart mixed signals de raha hai")

    comm = scorecard.get("communication")
    if comm is not None and int(comm) < 50:
        reasons.append(f"communication score ({comm}) relatively kam hai")

    if score < 55 and conf_label == "Medium":
        reasons.append("primary score mid-range par hai")
    elif score >= 78:
        reasons.append("primary score strong range me hai")

    reason_text = " aur ".join(reasons) if reasons else "engine signals balanced hain"
    return f"Confidence {conf_label} ({score}%) hai kyunki {reason_text}."


def render_commitment_template_answer(
    data: dict[str, Any],
    question: str = "",
    *,
    lang: str = "hn",
) -> str:
    """Deterministic production answer — fixed 9-step flow, effect-based, zero generic advice."""
    verdict = str(data.get("final_verdict") or data.get("verdict") or "Mixed")
    level = verdict.strip().lower()
    strongest = list(data.get("strongest") or data.get("strongest_factor") or [])
    weakest = list(data.get("weakest") or data.get("weakest_factor") or [])
    warnings = list(data.get("warnings") or [])
    score = int(data.get("confidence") or 0)
    conf_label = str(data.get("confidence_label") or "Medium")
    timing = data.get("timing") if isinstance(data.get("timing"), dict) else None
    scorecard = data.get("scorecard") if isinstance(data.get("scorecard"), dict) else {}

    angle, timepass_q, genuine_q = _question_angles(question, data.get("_checks") or {})

    p1 = str(data.get("direct_answer") or "").strip() or _build_direct_answer(
        level, timepass_q=timepass_q, genuine_q=genuine_q
    )
    p2 = str(data.get("verdict_line") or _build_verdict_line(verdict))
    p3 = _join_effect_lines(
        strongest,
        prefix="Strongest Reasons:",
        fallback="Strongest Reasons: chart me commitment-supporting factors mile hain.",
        limit=3,
    )
    p4 = _join_effect_lines(
        weakest,
        prefix="Biggest Challenges:",
        fallback="Biggest Challenges: chart me commitment-challenging factors bhi mile hain.",
        limit=3,
    )
    p5 = _build_reason_summary(strongest, weakest, verdict)
    p6 = _build_meaning_note(level, warnings)
    parts = [p1, p2, p3, p4, p5, p6]
    scorecard_note = _build_scorecard_note(scorecard)
    if scorecard_note:
        parts.append(scorecard_note)
    if timing and str(timing.get("window") or "").strip():
        parts.append(f"Timing: {str(timing.get('window')).strip()}.")
    parts.append(f"Practical guidance: {_build_practical_guidance(strongest, weakest)}")
    parts.append(
        _build_confidence_explanation(score, conf_label, strongest, weakest, scorecard)
    )

    body = "\n\n".join(parts)
    if (lang or "hn").strip().lower() == "hi":
        return body
    return body


def _build_reason_summary(strongest: list[str], weakest: list[str], verdict: str = "Mixed") -> str:
    n_pos = len([x for x in strongest if str(x).strip()])
    n_neg = len([x for x in weakest if str(x).strip()])
    if n_pos and n_neg:
        pos_word = "factor" if n_pos == 1 else "factors"
        neg_word = "factor" if n_neg == 1 else "factors"
        return (
            f"Engine ke hisaab se {n_pos} commitment-supporting {pos_word} "
            f"aur {n_neg} commitment-challenging {neg_word} mile hain. "
            f"Isi wajah se final verdict '{verdict}' hai."
        )
    if n_pos:
        return (
            f"Engine ke hisaab se {n_pos} commitment-supporting factor mile hain. "
            f"Isi wajah se final verdict '{verdict}' hai."
        )
    if n_neg:
        return (
            f"Engine ke hisaab se {n_neg} commitment-challenging factor mile hain. "
            f"Isi wajah se final verdict '{verdict}' hai."
        )
    return f"Engine signals mixed hain — isi wajah se final verdict '{verdict}' hai."


def validate_commitment_narrator_output(text: str, data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Reject hedging, generic advice, banned words, missing structure."""
    issues: list[str] = []
    t = (text or "").strip()
    if not t:
        return False, ["empty"]

    level = str(data.get("final_verdict") or "").strip().lower()
    if level == "low" and re.search(r"(?i)(kehna mushkil|mushkil hai|ho sakta|shayad|serious hain ya sirf)", t):
        issues.append("contradiction_low_verdict")

    if _BANNED_NARRATOR_PHRASES.search(t):
        issues.append("banned_phrase")

    tl = t.lower()
    for banned in _ALWAYS_BANNED_WORDS:
        if banned in tl:
            issues.append(f"banned_{banned.replace(' ', '_')}")

    if "strongest reasons" not in tl and "strongest" not in tl:
        issues.append("missing_strongest_section")
    if "biggest challenges" not in tl and "weakest" not in tl and "challenges" not in tl:
        issues.append("missing_challenges_section")

    score = int(data.get("confidence") or 0)
    label = str(data.get("confidence_label") or "Medium")
    if not re.search(rf"Confidence\s+{re.escape(label)}\s*\(\s*{score}\s*%\)", t, re.I):
        issues.append("confidence_line")
    if "kyunki" not in tl and "because" not in tl:
        issues.append("confidence_explanation_missing")

    return len(issues) == 0, issues


def engine_result_to_commitment_json(result: EngineResult) -> dict[str, Any]:
    """Compact narrator JSON — engine evidence only (no chart / no humanize drift)."""
    checks = result.checks or {}
    explanation = checks.get("explanation") or {}
    if not isinstance(explanation, dict):
        explanation = {}

    level = str(
        checks.get("commitment_level") or checks.get("level") or ""
    ).strip().lower()
    verdict_label = _VERDICT_LABELS.get(level, level.title() if level else "Mixed")

    scorecard = checks.get("scorecard") or {}
    if not isinstance(scorecard, dict):
        scorecard = {}
    score, conf_label = _resolve_confidence(level, checks, scorecard)

    rules_fired = list(checks.get("rules_fired") or [])
    strongest = _evidence_from_rules(rules_fired, polarity="positive", limit=3)
    weakest = _evidence_from_rules(rules_fired, polarity="negative", limit=2)

    if not strongest:
        sf = str(explanation.get("strongest_factor") or "").strip()
        if sf:
            strongest.append(_compact_evidence_line(sf))
        for item in explanation.get("why") or []:
            line = _compact_evidence_line(str(item))
            if line and line not in strongest:
                strongest.append(line)
    if not strongest:
        for item in (result.evidence_positive or [])[:3]:
            line = _compact_evidence_line(str(item))
            if line and line not in strongest:
                strongest.append(line)

    if not weakest:
        wf = str(explanation.get("weakest_factor") or "").strip()
        if wf:
            weakest.append(_compact_evidence_line(wf))
        for item in explanation.get("why_not") or []:
            line = _compact_evidence_line(str(item))
            if line and line not in weakest:
                weakest.append(line)
    if not weakest:
        for item in (result.evidence_negative or [])[:2]:
            line = _compact_evidence_line(str(item))
            if line and line not in weakest:
                weakest.append(line)

    reasons: list[str] = []
    for item in explanation.get("why") or []:
        line = _compact_evidence_line(str(item))
        if line and line not in reasons:
            reasons.append(line)
    for item in explanation.get("why_not") or []:
        line = _compact_evidence_line(str(item))
        if line and line not in reasons:
            reasons.append(line)
    if not reasons:
        for item in (result.summary or [])[:2]:
            line = _compact_evidence_line(str(item))
            if line:
                reasons.append(line)

    warnings: list[str] = []
    for item in weakest[:2]:
        if item and item not in warnings:
            warnings.append(item)
    if checks.get("contradiction"):
        warnings.append("Mixed signals in chart")

    timing_window = _extract_timing_window(result, checks)
    timing_block: dict[str, str] | None = None
    if timing_window:
        timing_block = {"window": timing_window}

    angle = str(checks.get("commitment_angle") or "general_commitment")
    _, timepass_q, genuine_q = _question_angles("", {**checks, "commitment_angle": angle})
    direct_answer = _build_direct_answer(level, timepass_q=timepass_q, genuine_q=genuine_q)
    reason_summary = _build_reason_summary(strongest[:3], weakest[:3], verdict_label)
    practical = _build_practical_guidance(strongest, weakest)
    meaning_note = _build_meaning_note(level, warnings)
    strongest_effects = _effects_from_evidence(strongest, limit=3)
    weakest_effects = _effects_from_evidence(weakest, limit=3)
    scorecard_note = _build_scorecard_note(scorecard)
    confidence_explanation = _build_confidence_explanation(
        score, conf_label, strongest, weakest, scorecard
    )

    payload: dict[str, Any] = {
        "question_type": "commitment",
        "final_verdict": verdict_label,
        "commitment_level": verdict_label,
        "direct_answer": direct_answer,
        "verdict_line": _build_verdict_line(verdict_label),
        "strongest": strongest[:3],
        "weakest": weakest[:2],
        "strongest_effects": strongest_effects,
        "weakest_effects": weakest_effects,
        "reason": reasons[:4],
        "reason_summary": reason_summary,
        "meaning_note": meaning_note,
        "practical_guidance": practical,
        "scorecard": {k: int(v) for k, v in scorecard.items() if isinstance(v, (int, float))},
        "scorecard_note": scorecard_note,
        "confidence": score,
        "confidence_label": conf_label,
        "confidence_explanation": confidence_explanation,
        "forbidden_phrases": list(_ALWAYS_BANNED_WORDS) + [
            "kehna mushkil",
            "ho sakta hai",
            "shayad",
            "feelings samjho",
        ],
        # backward-compatible keys for admin / tests
        "verdict": verdict_label,
        "strongest_factor": strongest[:3],
        "weakest_factor": weakest[:2],
        "warnings": warnings[:3],
    }
    if timing_block:
        payload["timing"] = timing_block
    payload["_meta"] = {
        "commitment_angle": angle,
        "headline": (result.verdict or "").strip(),
        "mode": checks.get("mode") or "static",
    }
    payload["locked_template"] = render_commitment_template_answer(
        {k: v for k, v in payload.items()},
        question=str(checks.get("question") or ""),
    )
    return payload


def commitment_narrator_payload(
    result: EngineResult,
    *,
    wants_explain: bool = False,
    question: str = "",
) -> str:
    """Facts block for LLM — ENGINE_JSON + LOCKED_TEMPLATE (minimal rephrase only)."""
    data = engine_result_to_commitment_json(result)
    meta = data.pop("_meta", {})
    locked = data.pop("locked_template", "")
    json_block = json.dumps(data, indent=2, ensure_ascii=False)

    lines = [
        "ARCHETYPE: commitment",
        "SOURCE_LOCK: ENGINE_JSON_ONLY — you do NOT see the birth chart or kundli.",
        "Narrate ONLY from ENGINE_JSON + LOCKED_TEMPLATE. Never invent planets, houses, dasha, or dates.",
        "",
        "ENGINE_JSON:",
        json_block,
        "",
        f"QUESTION_ANGLE: {meta.get('commitment_angle', 'general_commitment')}",
        f"VERDICT_HEADLINE: {meta.get('headline', '')}",
        "",
        "LOCKED_TEMPLATE (mandatory structure — rephrase lightly in Hinglish, do NOT add/remove facts):",
        locked,
        "",
        "OUTPUT RULES (production — zero freedom):",
        "STEP 1: Direct answer — use direct_answer from JSON; verdict Low → NEVER say 'mushkil hai' / 'ho sakta hai'.",
        "STEP 2: Final Verdict — use verdict_line.",
        "STEP 3: Strongest Reasons — use strongest_effects[] ONLY (real-life effects, NO planet jargon).",
        "STEP 4: Biggest Challenges — use weakest_effects[] ONLY.",
        "STEP 5: Reason — use reason_summary.",
        "STEP 6: Practical meaning — use meaning_note.",
        "STEP 7: Scorecard — use scorecard_note if non-empty.",
        "STEP 8: Timing — ONLY if timing.window exists.",
        "STEP 9: Practical guidance — use practical_guidance ONLY.",
        "FINAL LINE: confidence_explanation from JSON — exact score + kyunki reason.",
        "BANNED: any word in forbidden_phrases[]; clarity; patience; boundaries; feelings samjho.",
        "BANNED: planet/house/lord jargon in user-facing text. Translate to effects only.",
        "BANNED: new sentences not derived from LOCKED_TEMPLATE.",
        "Never change step order. Never contradict final_verdict.",
    ]
    if wants_explain:
        lines.append("LENGTH: expand each step to 1–2 sentences max (120–150 words total).")
    else:
        lines.append("LENGTH: keep LOCKED_TEMPLATE length (85–120 words). Same paragraphs, light Hinglish polish only.")
    return "\n".join(lines)


COMMITMENT_NARRATOR_RULES = """
COMMITMENT NARRATOR (LOCKED TEMPLATE — production):
• You receive ENGINE_JSON + LOCKED_TEMPLATE. Rephrase lightly in Hinglish — same facts, same order, same verdict.
• Explain ONLY strongest_effects[], weakest_effects[], reason_summary, meaning_note, scorecard_note, practical_guidance.
• Translate astrology to real-life meaning — NEVER say "Venus strong" or "7th lord weak"; use effect sentences from JSON.
• Never add astrology beyond JSON. No partner-behaviour guesses. No generic counselling.
• Never use shayad, ho sakta hai, kehna mushkil, lagta hai, maybe, perhaps, might.
• Verdict Low → direct hesitant tone; NEVER "mushkil hai ki serious hain ya timepass" after saying low commitment.
• If timing.window missing — skip timing entirely.
• End EXACTLY with confidence_explanation from JSON (score + kyunki reason).
• BANNED always: clarity, patience, boundaries, feelings samjho, emotional investment, open communication.
""".strip()


def build_commitment_narrator_length_block(
    *,
    wants_explain: bool = False,
    concise: bool = False,
    extra_rules: str = "",
) -> str:
    """Commitment-specific narrator block — plain paragraphs, not Cosmo section headers."""
    from ask_cosmo_narrator import cosmo_ask_word_target

    try:
        lo, hi = cosmo_ask_word_target(wants_explain=wants_explain, concise=concise)
    except TypeError:
        # Older VPS ask_cosmo_narrator.py without batch concise kwarg.
        lo, hi = cosmo_ask_word_target(wants_explain=wants_explain)
    rules = f"\n{extra_rules.strip()}\n" if extra_rules.strip() else ""
    if concise:
        structure = """
STRUCTURE (batch — 2–4 sentences, plain paragraph only):
• Sentence 1: direct haan/nahi/mixed from verdict.
• Sentence 2: one strongest_factor reason.
• Sentence 3 (optional): one warning if present.
• Final: Confidence: {label} ({score}%).
NO headers, NO bullets, NO planet/house jargon.
""".strip()
    elif wants_explain:
        structure = """
STRUCTURE (explain mode — 4–6 short paragraphs, NO section headers):
P1: Direct answer matching verdict + question angle.
P2: Short why — mirror headline tone.
P3–P4: Expand strongest_factor in relatable daily-life language.
P5: Caution from warnings/weakest_factor (delay ≠ no commitment).
P6 (only if timing.window in JSON): timing window in plain words.
P7: One practical guidance line.
Final line: Confidence: {label} ({score}%).
""".strip()
    else:
        structure = """
STRUCTURE (default — follow LOCKED_TEMPLATE paragraph order exactly):
P1: direct_answer (verdict-locked, no hedging).
P2: verdict_line (Final Verdict: …).
P3: Strongest Reasons — only strongest_effects[].
P4: Biggest Challenges — only weakest_effects[].
P5: reason_summary.
P6: meaning_note (practical meaning).
P7 (if scorecard_note): scorecard sentence.
P8 (only if timing.window): timing sentence.
P9: practical_guidance only.
Final line: confidence_explanation — exact from JSON.
NO planet jargon. NO generic relationship advice. NO new factors.
""".strip()

    return f"""
You are "Cosmo Ask" — warm, honest Hinglish (Roman unless Lang says Devanagari).
The commitment engine already decided — narrate ENGINE_JSON only; never recalculate.

{COMMITMENT_NARRATOR_RULES}

{structure}

LENGTH: {lo}–{hi} words total. Topic: commitment.{rules}
""".strip()

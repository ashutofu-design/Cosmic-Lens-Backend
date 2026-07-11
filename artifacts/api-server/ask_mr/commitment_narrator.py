"""Commitment engine narrator — JSON-only facts → natural Hinglish answer.

LLM never sees the kundli. It receives a compact ENGINE_JSON block plus strict
narration rules (direct answer → reasons → caution → timing → practical).
"""
from __future__ import annotations

import json
import re
from typing import Any

from .types import EngineResult
from .user_section_labels import NATURAL_USER_SECTION as _NATURAL_SEC

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
        re.compile(r"\bmoon\b.*(afflict|instab|friction|weak)|moon.*emotional", re.I),
        "Emotional consistency me utar-chadhav dikh sakta hai.",
    ),
    (
        re.compile(r"\bmoon\b", re.I),
        "Emotional consistency me utar-chadhav commitment pace ko affect kar sakti hai.",
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

_COM_RULE_EFFECTS: dict[str, str] = {
    "COM-001": "Partnership axis structurally strong hai — long-term pairing ko backing milti hai.",
    "COM-002": "Long-term stability ko support milne me challenge dikh raha hai.",
    "COM-003": "Commitment structure ko strengthen karne me extra challenge dikh raha hai.",
    "COM-004": "Relationship me warmth aur affection ko support milta hai.",
    "COM-005": "Affection layer me friction ya inconsistency dikh sakti hai.",
    "COM-006": "Long-term faith aur growth orientation commitment ko support karta hai.",
    "COM-007": "Long-term faith aur promise layer me weakness dikh rahi hai.",
}

_USER_SECTION = dict(_NATURAL_SEC)

_TIMING_RX = re.compile(
    r"(?i)(late\s+20\d{2}|early\s+20\d{2}|mid\s+20\d{2}|"
    r"20\d{2}\s*(?:ke\s+)?(?:end|start|mid)|"
    r"timing[:\s]+[^.;]+|window[^.;]+|phase[^.;]+)"
)


def _evidence_to_effect(raw: str, *, rule_id: str = "") -> str:
    """Translate engine evidence → real-life commitment effect (no planet jargon)."""
    rid = (rule_id or "").strip().upper()
    if rid in _COM_RULE_EFFECTS:
        return _COM_RULE_EFFECTS[rid]
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


def _effects_from_evidence(items: list[str], *, limit: int = 3, rule_ids: list[str] | None = None) -> list[str]:
    out: list[str] = []
    rids = rule_ids or []
    for i, raw in enumerate(items):
        rid = rids[i] if i < len(rids) else ""
        eff = _evidence_to_effect(str(raw), rule_id=rid)
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
) -> tuple[list[str], list[str]]:
    """Return (evidence lines, parallel rule_ids)."""
    out: list[str] = []
    rids: list[str] = []
    for rule in rules_fired:
        if not isinstance(rule, dict):
            continue
        if str(rule.get("polarity") or "").strip().lower() != polarity:
            continue
        note = str(rule.get("note") or rule.get("evidence") or rule.get("label") or "").strip()
        line = _compact_evidence_line(note)
        rid = str(rule.get("rule_id") or rule.get("id") or "").strip()
        if line and line not in out:
            out.append(line)
            rids.append(rid)
        if len(out) >= limit:
            break
    return out, rids


def _confidence_label_from_score(score: int) -> str:
    """User-facing certainty bands."""
    if score <= 35:
        return "Low"
    if score <= 65:
        return "Medium"
    if score <= 85:
        return "High"
    return "Very High"


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
    return score, _confidence_label_from_score(score)


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


_ANGLE_OPENINGS: dict[str, dict[str, str]] = {
    "future_planning": {
        "ready": (
            "Haan, chart ke hisaab se partner future ko lekar serious planning karta hai — "
            "long-term direction clear aur stable dikhti hai."
        ),
        "cautious": (
            "Partner future ke baare me sochta hai, lekin planning abhi cautious phase me hai — "
            "intent hai par pace slow ya hesitant dikh sakta hai."
        ),
        "mixed": (
            "Haan, partner future ke baare me sochta hai, lekin uski planning abhi fully stable nahi hai — "
            "long-term intention hai, par delay aur hesitation ke sanket bhi dikhte hain."
        ),
        "low": (
            "Abhi chart ke hisaab se partner ki future planning weak ya inconsistent dikhti hai — "
            "long-term serious planning ka strong support kam hai."
        ),
    },
    "time_pass": {
        "ready": (
            "Chart me sirf timepass ka strong indication nahi milta — "
            "partner genuinely invested dikh raha hai, casual intent dominant nahi."
        ),
        "cautious": (
            "Sirf timepass ka clear signal nahi, lekin commitment abhi cautious phase me hai — "
            "words aur actions dono verify karna zaruri hai."
        ),
        "mixed": (
            "Chart me sirf timepass ka strong indication nahi milta. "
            "Lekin commitment ko lekar mixed signals hain, isliye sirf words nahi, consistent actions bhi dekhein."
        ),
        "low": (
            "Chart ke hisaab se casual / timepass intent zyada dikhta hai — "
            "genuine long-term commitment ka support abhi kam hai."
        ),
    },
    "marriage_serious": {
        "ready": (
            "Haan, chart ke hisaab se partner shaadi ko seriously leta hai — "
            "marriage intent ko strong backing milti hai."
        ),
        "cautious": (
            "Partner me shaadi ke prati interest dikh raha hai, lekin abhi cautious phase me hai — "
            "intent hai par final clarity develop ho rahi hai."
        ),
        "mixed": (
            "Shaadi ke prati interest dikh raha hai, lekin chart ke hisaab se commitment ko practical roop dene me "
            "kuch challenges aur delay ke yog bhi hain."
        ),
        "low": (
            "Abhi chart ke hisaab se shaadi / marriage ke prati serious intent weak dikhta hai — "
            "long-term marriage commitment ka support kam hai."
        ),
    },
    "genuine_intent": {
        "ready": "Chart ke hisaab se partner genuinely invested hai — long-term intent strong dikhta hai.",
        "cautious": "Partner genuinely interested hai, lekin commitment abhi fully settle nahi hua — pace slow hai.",
        "mixed": "Genuine interest hai, lekin consistency aur long-term follow-through abhi mixed phase me hai.",
        "low": "Abhi chart genuine long-term investment ko weak dikhata hai — casual ya distant intent zyada hai.",
    },
    "serious_relationship": {
        "ready": "Haan, partner serious long-term relationship chahta hai — chart is intent ko support karta hai.",
        "cautious": "Serious relationship ka interest hai, par abhi hesitant / slow-moving phase dikh raha hai.",
        "mixed": "Serious relationship ka intent hai, lekin friction ya distance commitment ko test kar raha hai.",
        "low": "Abhi serious long-term relationship intent weak dikhta hai — casual ya non-committal tone zyada hai.",
    },
    "long_term_intent": {
        "ready": "Partner long-term relationship chahta hai — chart long-term intent ko backing deta hai.",
        "cautious": "Long-term intent hai, lekin abhi cautious phase me clarity develop ho rahi hai.",
        "mixed": "Long-term intent dikhta hai, par consistency aur stability abhi fully establish nahi hui.",
        "low": "Long-term intent abhi weak dikhta hai — short-term ya casual approach zyada possible hai.",
    },
    "future_together": {
        "ready": "Haan, partner future aapke saath dekhta hai — long-term togetherness ko chart support karta hai.",
        "cautious": "Future saath ka intent hai, lekin abhi planning / clarity cautious phase me hai.",
        "mixed": "Future saath ka thought hai, par practical planning aur consistency abhi mixed signals de rahi hai.",
        "low": "Abhi future together ka strong intent kam dikhta hai — distance ya hesitation zyada hai.",
    },
    "commitment_ready": {
        "ready": "Haan, chart ke hisaab se partner commitment ke liye ready hai — serious intent strong hai.",
        "cautious": "Commitment readiness dikh rahi hai, lekin abhi final clarity / pace cautious phase me hai.",
        "mixed": "Commitment readiness mixed hai — interest hai par friction ya delay test kar raha hai.",
        "low": "Abhi commitment readiness weak dikhti hai — serious long-term ready phase nahi dikh raha.",
    },
    "loyalty_intent": {
        "ready": "Partner loyal / exclusive rehne ka intent strong dikhta hai.",
        "cautious": "Loyalty ka intent hai, par abhi trust / consistency cautious phase me verify honi chahiye.",
        "mixed": "Loyalty ke supportive aur challenging dono signals hain — actions se verify karein.",
        "low": "Exclusive / loyal intent abhi weak dikhta hai — trust layer challenging hai.",
    },
    "effort_and_maintain": {
        "ready": "Partner relationship me effort aur responsibility lene ke strong signals dikhate hain.",
        "cautious": "Effort dikh raha hai, lekin consistency abhi developing phase me hai.",
        "mixed": "Effort ke signs hain, par long-term maintain / responsibility abhi mixed phase me hai.",
        "low": "Relationship maintain karne ka consistent effort abhi kam dikhta hai.",
    },
    "public_acceptance": {
        "ready": "Partner relationship ko public / family ke saamne accept karne ke supportive signals dikhate hain.",
        "cautious": "Public acceptance possible hai, par abhi hesitant ya slow phase dikh sakta hai.",
        "mixed": "Public / official acceptance ke mixed signals hain — openness aur hesitation dono dikh sakte hain.",
        "low": "Abhi public / family acceptance weak dikhti hai — secret ya distant approach zyada possible hai.",
    },
}


def _resolve_commitment_angle(question: str, checks: dict[str, Any]) -> str:
    from ask_intent_fidelity import infer_partner_commitment_angle

    angle = str(checks.get("commitment_angle") or "").strip().lower()
    if not angle or angle == "general_commitment":
        angle = str(infer_partner_commitment_angle(question) or "general_commitment").strip().lower()
    return angle or "general_commitment"


def _build_angle_direct_answer(
    level: str,
    angle: str,
    *,
    question: str = "",
    timepass_q: bool = False,
    genuine_q: bool = False,
) -> str:
    """Opening paragraph anchored to user intent — not generic verdict boilerplate."""
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_commitment").strip().lower()
    openings = _ANGLE_OPENINGS.get(ang) or {}
    if lv in openings:
        return openings[lv]
    return _build_direct_answer(lv, timepass_q=timepass_q, genuine_q=genuine_q)


def _is_timing_question(question: str, checks: dict[str, Any]) -> bool:
    if str(checks.get("mode") or "").strip().lower() == "timing":
        return True
    return bool(re.search(r"(?ix)\b(kab|when|kitne\s+saal|kis\s+saal|timing|muhurat|date|month|year)\b", question or ""))


def _dasha_timing_support(checks: dict[str, Any], rules_fired: list[Any]) -> str:
    """positive | negative | mixed | unknown from dasha rules/evidence."""
    for rule in rules_fired:
        if not isinstance(rule, dict):
            continue
        blob = " ".join(
            str(rule.get(k) or "")
            for k in ("note", "evidence", "label", "module")
        ).lower()
        if "dasha" not in blob:
            continue
        pol = str(rule.get("polarity") or "").strip().lower()
        if pol == "positive":
            return "positive"
        if pol == "negative":
            return "negative"
        if pol == "mixed":
            return "mixed"
    timing = checks.get("timing") if isinstance(checks.get("timing"), dict) else {}
    for line in timing.get("trigger_planets") or []:
        if "dasha" in str(line).lower():
            return "mixed"
    return "unknown"


def _build_timing_answer(
    *,
    question: str,
    checks: dict[str, Any],
    result: EngineResult,
    level: str,
    angle: str,
) -> dict[str, str]:
    """Dasha-aware timing block for relationship commitment questions."""
    window = _extract_timing_window(result, checks)
    dasha = _dasha_timing_support(checks, list(checks.get("rules_fired") or []))
    lv = (level or "mixed").strip().lower()

    if dasha == "positive":
        lead = "Current dasha (MD/AD) commitment ko support karti hai."
        if window:
            detail = f"Is phase me {window} supportive window dikhta hai — clarity ya planning aage badh sakti hai."
        else:
            detail = "Is dasha phase me serious commitment conversations / planning ke liye better support hai."
    elif dasha == "negative":
        lead = "Current dasha abhi delay, test, ya distance dikha rahi hai."
        if window:
            detail = (
                f"Zyada supportive commitment phase {window} ke around dikh sakta hai — "
                f"tab long-term planning zyada settle ho sakti hai."
            )
        else:
            detail = (
                "Aane wali benefic dasha phase me commitment signals zyada clear hone ke yog hain — "
                "tab planning / clarity better align ho sakti hai."
            )
    elif dasha == "mixed":
        lead = "Current dasha mixed signals de rahi hai — commitment effort se grow karega."
        detail = (
            f"Better alignment {window} ke around dikh sakta hai."
            if window
            else "Consistent actions ke saath next supportive dasha phase me clarity improve ho sakti hai."
        )
    else:
        lead = "Timing layer mixed ya limited signals de rahi hai."
        detail = (
            f"Commitment clarity ke liye {window} supportive phase dikhta hai."
            if window
            else "Abhi exact strong timing window limited hai — dasha change ke baad clarity improve ho sakti hai."
        )

    if ang_focus := _ANGLE_OPENINGS.get(angle, {}).get(lv):
        context = ang_focus.split("—")[0].strip().rstrip(".")
        summary = f"{context}. {lead} {detail}"
    else:
        summary = f"{lead} {detail}"

    return {
        "window": window or "",
        "dasha_support": dasha,
        "summary": summary.strip(),
    }


def _build_verdict_line(verdict_label: str) -> str:
    return f"Final Verdict: {verdict_label} commitment."


def _join_effect_lines(
    items: list[str],
    *,
    prefix: str,
    fallback: str,
    limit: int = 3,
    rule_ids: list[str] | None = None,
) -> str:
    effects = _effects_from_evidence(items, limit=limit, rule_ids=rule_ids)
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
            "Abhi partner ki taraf se long-term serious commitment ka "
            "support kam hai — ye rejection nahi, lekin readiness weak dikh rahi hai."
        )
    if lv == "ready":
        return (
            "Chart long-term serious intent ko backing deta hai — "
            "consistency ke saath verdict aur strong hota hai."
        )
    if lv == "cautious":
        return (
            "Interest hai lekin full stability abhi develop ho rahi hai — "
            "process slow ya hesitant phase me hai."
        )
    return (
        "Interest hai lekin long-term consistency abhi fully establish nahi — "
        "mixed phase me decision evidence aur repeated behaviour se lena better hai."
    )


def _build_practical_guidance(strongest: list[str], weakest: list[str]) -> str:
    """Evidence-tied observation — not generic counselling."""
    blob = " ".join(weakest + strongest).lower()
    if "7th" in blob or "dusthana" in blob or "stability" in blob:
        return (
            "Stability ke challenging signals ke hisaab se partner ke consistent actions "
            "aur long-term planning ko words se zyada verify karein."
        )
    if "saturn" in blob or "delay" in blob or "hesitation" in blob:
        return (
            "Delay ya hesitation ke signals hain — slow progress possible hai, "
            "lekin regular effort aur planning pattern dekhein."
        )
    if "venus" in blob and any(x in blob for x in ("afflict", "debil", "combust", "friction")):
        return (
            "Affection layer me friction signal hai — warmth ko sirf words se nahi, "
            "repeated behaviour se match karein."
        )
    if "moon" in blob:
        return (
            "Emotional consistency ke ups-downs dikh rahe hain — partner ke mood aur "
            "behaviour pattern ko kuch hafton tak observe karein."
        )
    if "jupiter" in blob:
        return (
            "Long-term faith signals supportive hain — lekin partner ke behaviour se "
            "future planning match honi chahiye."
        )
    return (
        "Chart mixed signals de raha hai — partner ke consistent behaviour aur "
        "long-term planning ko observe karein, sirf promises par depend mat karein."
    )


def _build_scorecard_user_note(scorecard: dict[str, Any]) -> str:
    """Natural language only — no raw numbers for end users."""
    if not scorecard:
        return ""
    commit = scorecard.get("commitment")
    trust = scorecard.get("trust")
    comm = scorecard.get("communication")
    try:
        commit_i = int(commit) if commit is not None else None
        trust_i = int(trust) if trust is not None else None
        comm_i = int(comm) if comm is not None else None
    except (TypeError, ValueError):
        return ""
    if comm_i is not None and commit_i is not None and comm_i < commit_i - 5:
        return "Communication ke indicators commitment ke comparison me kam supportive dikhte hain."
    if trust_i is not None and commit_i is not None and trust_i < commit_i - 5:
        return "Trust ke indicators commitment ke comparison me thode kam supportive dikhte hain."
    if commit_i is not None and commit_i < 50:
        return "Long-term commitment ke indicators abhi developing phase me dikhte hain."
    return ""


def _build_scorecard_note(scorecard: dict[str, Any]) -> str:
    """Admin/debugger only — includes numeric scorecard."""
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
    user_note = _build_scorecard_user_note(scorecard)
    return header + "." + (f" {user_note}" if user_note else "")


def _build_confidence_explanation(
    score: int,
    conf_label: str,
    strongest: list[str],
    weakest: list[str],
    scorecard: dict[str, Any],
    *,
    topic: str = "commitment",
) -> str:
    topic_word = (topic or "chart").strip().replace("_", " ") or "chart"
    reasons: list[str] = []
    if strongest and weakest:
        reasons.append("positive aur negative dono tarah ke indicators ek saath mile")
    elif strongest:
        reasons.append(f"zyada tar indicators {topic_word}-supporting direction me hain")
    elif weakest:
        reasons.append(f"zyada tar indicators {topic_word}-challenging direction me hain")

    if strongest and weakest and abs(len(strongest) - len(weakest)) <= 1:
        reasons.append("chart mixed signals de raha hai")

    if topic_word == "commitment":
        comm = scorecard.get("communication")
        commit = scorecard.get("commitment")
        if comm is not None and commit is not None:
            try:
                if int(comm) < int(commit) - 5:
                    reasons.append(
                        "communication ke indicators commitment ke comparison me kam supportive hain"
                    )
            except (TypeError, ValueError):
                pass

    if 36 <= score <= 65 and conf_label == "Medium":
        reasons.append("score mid-range par hai")
    elif score >= 86:
        reasons.append("score bahut strong range me hai")
    elif score >= 66:
        reasons.append("score strong range me hai")

    reason_text = " aur ".join(reasons) if reasons else "chart signals balanced hain"
    return f"Confidence {conf_label} ({score}%) hai kyunki {reason_text}."


def render_commitment_template_answer(
    data: dict[str, Any],
    question: str = "",
    *,
    lang: str = "hn",
) -> str:
    """Deterministic production answer — natural Hinglish flow, effect-based."""
    verdict = str(data.get("final_verdict") or data.get("verdict") or "Mixed")
    level = verdict.strip().lower()
    strongest = list(data.get("strongest") or data.get("strongest_factor") or [])
    weakest = list(data.get("weakest") or data.get("weakest_factor") or [])
    warnings = list(data.get("warnings") or [])
    score = int(data.get("confidence") or 0)
    conf_label = str(data.get("confidence_label") or "Medium")
    timing = data.get("timing") if isinstance(data.get("timing"), dict) else None
    scorecard = data.get("scorecard") if isinstance(data.get("scorecard"), dict) else {}
    strongest_rids = list(data.get("strongest_rule_ids") or [])
    weakest_rids = list(data.get("weakest_rule_ids") or [])

    angle, timepass_q, genuine_q = _question_angles(question, data.get("_checks") or {})
    focus_angle = str(data.get("answer_focus") or data.get("commitment_angle") or angle)

    p1 = str(data.get("direct_answer") or "").strip() or _build_angle_direct_answer(
        level,
        focus_angle,
        question=question,
        timepass_q=timepass_q,
        genuine_q=genuine_q,
    )
    p2 = f"{_USER_SECTION['why_verdict']} {_build_reason_summary(strongest, weakest, verdict)}"
    p3 = _join_effect_lines(
        strongest,
        prefix=_USER_SECTION["positive"],
        fallback=f"{_USER_SECTION['positive']} chart me commitment-supporting indicators mile hain.",
        limit=3,
        rule_ids=strongest_rids,
    )
    p4 = _join_effect_lines(
        weakest,
        prefix=_USER_SECTION["challenges"],
        fallback=f"{_USER_SECTION['challenges']} chart me commitment-challenging indicators bhi mile hain.",
        limit=3,
        rule_ids=weakest_rids,
    )
    meaning = _build_meaning_note(level, warnings)
    scorecard_user = _build_scorecard_user_note(scorecard)
    if scorecard_user:
        meaning = f"{meaning} {scorecard_user}"
    parts = [p1, p2, p3, p4, f"{_USER_SECTION['meaning']} {meaning}"]
    timing = data.get("timing") if isinstance(data.get("timing"), dict) else None
    if timing:
        t_summary = str(timing.get("summary") or timing.get("window") or "").strip()
        if t_summary:
            parts.append(f"Timing: {t_summary}")
    parts.append(f"{_USER_SECTION['focus']} {_build_practical_guidance(strongest, weakest)}")
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
        pos_h = "do strong" if n_pos >= 2 else "ek strong"
        neg_h = "do challenging" if n_neg >= 2 else "ek challenging"
        return (
            f"Chart ke analysis ke hisaab se {pos_h} aur {neg_h} commitment indicators mile hain. "
            f"Isi wajah se final verdict {verdict} hai."
        )
    if n_pos:
        return (
            f"Chart ke analysis ke hisaab se commitment-supporting indicators zyada dikhte hain. "
            f"Isi wajah se final verdict {verdict} hai."
        )
    if n_neg:
        return (
            f"Chart ke analysis ke hisaab se commitment-challenging indicators zyada dikhte hain. "
            f"Isi wajah se final verdict {verdict} hai."
        )
    return f"Chart ke signals mixed hain — isi wajah se final verdict {verdict} hai."


def _all_engine_evidence(result: EngineResult, rules_fired: list[Any]) -> list[tuple[str, str, str]]:
    """(line, polarity, rule_id) from rules + engine evidence pools."""
    seen: set[str] = set()
    out: list[tuple[str, str, str]] = []
    for rule in rules_fired:
        if not isinstance(rule, dict):
            continue
        note = str(rule.get("note") or rule.get("evidence") or rule.get("label") or "").strip()
        line = _compact_evidence_line(note)
        if not line or line in seen:
            continue
        seen.add(line)
        out.append((
            line,
            str(rule.get("polarity") or "neutral").strip().lower(),
            str(rule.get("rule_id") or rule.get("id") or "").strip(),
        ))
    for line in list(result.evidence_positive or []) + list(result.evidence_negative or []) + list(result.evidence or []):
        compact = _compact_evidence_line(str(line))
        if compact and compact not in seen:
            seen.add(compact)
            pol = "negative" if compact in {_compact_evidence_line(str(x)) for x in (result.evidence_negative or [])} else "positive"
            out.append((compact, pol, ""))
    return out


def _promote_moon_to_weakest(weakest: list[str], result: EngineResult) -> list[str]:
    """If Moon evidence exists but was not narrated, surface it in challenges."""
    if any("moon" in str(x).lower() for x in weakest):
        return weakest
    for pool in (result.evidence_negative or [], result.evidence or [], result.evidence_positive or []):
        for line in pool:
            if "moon" in str(line).lower():
                compact = _compact_evidence_line(str(line))
                if compact and compact not in weakest:
                    return weakest + [compact]
    return weakest


def _build_ignored_evidence(
    all_evidence: list[tuple[str, str, str]],
    used_strongest: list[str],
    used_weakest: list[str],
) -> list[dict[str, str]]:
    used = set(used_strongest + used_weakest)
    ignored: list[dict[str, str]] = []
    for line, polarity, rid in all_evidence:
        if line in used:
            continue
        ignored.append({
            "evidence": line,
            "polarity": polarity,
            "rule_id": rid or "",
            "effect": _evidence_to_effect(line, rule_id=rid),
            "reason": "Lower priority than top commitment factors selected for user answer.",
        })
    return ignored[:6]


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

    if "strongest reasons" not in tl and "mukhya sanket" not in tl:
        issues.append("missing_positive_section")
    if "dhyan dene layak" not in tl and "challenges" not in tl:
        issues.append("missing_challenges_section")

    score = int(data.get("confidence") or 0)
    label = str(data.get("confidence_label") or "Medium")
    if not re.search(rf"Confidence\s+{re.escape(label)}\s*\(\s*{score}\s*%\)", t, re.I):
        issues.append("confidence_line")
    if "kyunki" not in tl and "because" not in tl:
        issues.append("confidence_explanation_missing")
    if re.search(r"(?i)\bengine ke hisaab\b", t):
        issues.append("engine_phrase_in_user_text")
    if re.search(r"(?i)scorecard:\s*commitment\s+\d+", t):
        issues.append("scorecard_numbers_in_user_text")

    return len(issues) == 0, issues


def engine_result_to_commitment_json(
    result: EngineResult,
    question: str = "",
) -> dict[str, Any]:
    """Compact narrator JSON — engine evidence only (no chart / no humanize drift)."""
    checks = result.checks or {}
    explanation = checks.get("explanation") or {}
    if not isinstance(explanation, dict):
        explanation = {}

    q = (question or str(checks.get("question") or "")).strip()
    angle = _resolve_commitment_angle(q, checks)
    checks = {**checks, "commitment_angle": angle, "question": q}

    level = str(
        checks.get("commitment_level") or checks.get("level") or ""
    ).strip().lower()
    verdict_label = _VERDICT_LABELS.get(level, level.title() if level else "Mixed")

    scorecard = checks.get("scorecard") or {}
    if not isinstance(scorecard, dict):
        scorecard = {}
    score, conf_label = _resolve_confidence(level, checks, scorecard)

    rules_fired = list(checks.get("rules_fired") or [])
    strongest, strongest_rids = _evidence_from_rules(rules_fired, polarity="positive", limit=3)
    weakest, weakest_rids = _evidence_from_rules(rules_fired, polarity="negative", limit=3)

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
        for item in (result.evidence_negative or [])[:3]:
            line = _compact_evidence_line(str(item))
            if line and line not in weakest:
                weakest.append(line)
                weakest_rids.append("")

    weakest = _promote_moon_to_weakest(weakest[:3], result)[:3]
    all_evidence = _all_engine_evidence(result, rules_fired)
    ignored_evidence = _build_ignored_evidence(all_evidence, strongest[:3], weakest[:3])

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
    is_timing_q = _is_timing_question(q, checks)
    if is_timing_q or timing_window or checks.get("mode") == "timing":
        timing_block = _build_timing_answer(
            question=q,
            checks=checks,
            result=result,
            level=level,
            angle=angle,
        )
    elif timing_window:
        timing_block = {"window": timing_window, "dasha_support": "unknown", "summary": timing_window}

    _, timepass_q, genuine_q = _question_angles(q, checks)
    direct_answer = _build_angle_direct_answer(
        level,
        angle,
        question=q,
        timepass_q=timepass_q,
        genuine_q=genuine_q,
    )
    reason_summary = _build_reason_summary(strongest[:3], weakest[:3], verdict_label)
    practical = _build_practical_guidance(strongest, weakest)
    meaning_note = _build_meaning_note(level, warnings)
    strongest_effects = _effects_from_evidence(strongest, limit=3, rule_ids=strongest_rids)
    weakest_effects = _effects_from_evidence(weakest, limit=3, rule_ids=weakest_rids)
    scorecard_note = _build_scorecard_note(scorecard)
    scorecard_user_note = _build_scorecard_user_note(scorecard)
    confidence_explanation = _build_confidence_explanation(
        score, conf_label, strongest, weakest, scorecard
    )

    payload: dict[str, Any] = {
        "question_type": "commitment",
        "original_question": q,
        "commitment_angle": angle,
        "answer_focus": angle,
        "primary_user_concern": angle,
        "opening_style": angle,
        "is_timing_question": is_timing_q,
        "final_verdict": verdict_label,
        "commitment_level": verdict_label,
        "direct_answer": direct_answer,
        "verdict_line": _build_verdict_line(verdict_label),
        "strongest": strongest[:3],
        "weakest": weakest[:3],
        "strongest_rule_ids": strongest_rids[:3],
        "weakest_rule_ids": weakest_rids[:3],
        "strongest_effects": strongest_effects,
        "weakest_effects": weakest_effects,
        "ignored_evidence": ignored_evidence,
        "reason": reasons[:4],
        "reason_summary": reason_summary,
        "meaning_note": meaning_note,
        "practical_guidance": practical,
        "scorecard": {k: int(v) for k, v in scorecard.items() if isinstance(v, (int, float))},
        "scorecard_note": scorecard_note,
        "scorecard_user_note": scorecard_user_note,
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
        "weakest_factor": weakest[:3],
        "warnings": warnings[:3],
    }
    if timing_block:
        payload["timing"] = timing_block
    payload["_checks"] = checks
    payload["_meta"] = {
        "commitment_angle": angle,
        "headline": (result.verdict or "").strip(),
        "mode": checks.get("mode") or "static",
    }
    payload["locked_template"] = render_commitment_template_answer(
        {k: v for k, v in payload.items()},
        question=q,
    )
    return payload


def commitment_narrator_payload(
    result: EngineResult,
    *,
    wants_explain: bool = False,
    question: str = "",
) -> str:
    """Facts block for LLM — ENGINE_JSON + LOCKED_TEMPLATE (minimal rephrase only)."""
    q = (question or str((result.checks or {}).get("question") or "")).strip()
    data = engine_result_to_commitment_json(result, question=q)
    data.pop("_checks", None)
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
        f"ANSWER_FOCUS: {data.get('answer_focus', meta.get('commitment_angle', 'general_commitment'))}",
        f"ORIGINAL_QUESTION: {data.get('original_question', q)}",
        f"VERDICT_HEADLINE: {meta.get('headline', '')}",
        "",
        "LOCKED_TEMPLATE (mandatory structure — rephrase lightly in Hinglish, do NOT add/remove facts):",
        locked,
        "",
        "OUTPUT RULES (production — zero freedom):",
        "STEP 1: Direct answer — use direct_answer from JSON; it is already anchored to ANSWER_FOCUS / original question.",
        "STEP 1b: Do NOT replace the opening with a generic verdict paragraph.",
        "STEP 2: Kyun ye verdict aaya — use reason_summary.",
        "STEP 3: Mukhya sanket — use strongest_effects[] ONLY (real-life effects, NO planet jargon).",
        "STEP 4: Dhyan dene layak challenges — use weakest_effects[] ONLY.",
        "STEP 5: Practical meaning — use meaning_note + scorecard_user_note if present.",
        "STEP 6: Timing — ONLY if timing.window exists.",
        "STEP 7: Focus line — use practical_guidance ONLY.",
        "FINAL LINE: confidence_explanation from JSON — exact score + kyunki reason.",
        "BANNED: scorecard numbers in user text; 'Engine ke hisaab'; clarity; patience; boundaries.",
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
P1: direct_answer (seedha jawab, verdict-locked).
P2: Kyun ye verdict aaya — reason_summary.
P3: Mukhya sanket — only strongest_effects[].
P4: Dhyan dene layak challenges — only weakest_effects[].
P5: Iska practical matlab — meaning_note + scorecard_user_note (no raw numbers).
P6 (only if timing.window): timing sentence.
P7: Aapko kis baat par dhyan dena chahiye — practical_guidance only.
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

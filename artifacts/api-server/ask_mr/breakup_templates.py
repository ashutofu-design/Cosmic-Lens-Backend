"""Breakup / separation risk engine — intent templates (opening, meaning, practical per angle × level)."""
from __future__ import annotations

from .user_section_labels import NATURAL_USER_SECTION as _NATURAL_SEC

import re
from typing import Any

BREAKUP_LEVELS: tuple[str, ...] = ("low", "moderate", "elevated", "high")

VERDICT_LABELS: dict[str, str] = {
    "low": "Low risk",
    "moderate": "Moderate risk",
    "elevated": "Elevated risk",
    "high": "High risk",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "low": 78,
    "moderate": 62,
    "elevated": 48,
    "high": 32,
}

USER_SECTION = dict(_NATURAL_SEC)
USER_SECTION["repair"] = "Repair outlook —"

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "will_breakup": {
        "low": "Chart ke hisaab se breakup / separation risk abhi low dikhta hai — repair capacity bond ko hold kar sakti hai.",
        "moderate": "Breakup / separation risk moderate dikhta hai — friction active hai, lekin timely repair se outcome shift ho jayega.",
        "elevated": "Breakup / separation risk elevated zone me hai — distance themes bond ko test kar rahi hain.",
        "high": (
            "Breakup / separation ke high-risk indicators active hain — repeated friction bond ko weaken kar sakti hai. "
            "Ye pakka end nahi batata, par repair delay risky hai."
        ),
    },
    "breakup_cause": {
        "low": "Chart me dominant separation driver kam dikhta hai — friction mostly manageable repair topics lagte hain.",
        "moderate": "Breakup / distance ke mixed causes dikh rahe hain — communication + trust friction dono test ho sakte hain.",
        "elevated": "Separation ke sensitive causes active hain — distance, conflict ya trust gaps bond ko strain kar sakte hain.",
        "high": "High-risk separation drivers zyada active hain — repeated conflict, distance ya trust stress core reason zone me dikhte hain.",
    },
    "divorce_risk": {
        "low": "Divorce / talak ke strong indicators abhi dominant nahi — repair window relatively open dikhti hai.",
        "moderate": "Divorce / legal separation ke moderate-risk signals hain — friction ko timely address karna zaruri hai.",
        "elevated": "Divorce / talak ke elevated-risk themes active hain — long unresolved friction legal end ki taraf push kar sakti hai.",
        "high": "Divorce / talak ke high-risk pattern dikh rahe hain — ye final proof nahi, par serious repair + realistic assessment zaruri hai.",
    },
    "separation_risk": {
        "low": "Alag hone / separation ke strong yog abhi kam dikhte hain — bond hold karne ke indicators zyada hain.",
        "moderate": "Separation ke mixed signals hain — distance possible hai par repair se stabilize ho jayega.",
        "elevated": "Separation / alag hone ke sensitive indicators active hain — emotional distance bond ko test karegi.",
        "high": "Separation ke high-risk indicators active hain — repeated distance + friction alag hone ka pressure bana sakte hain.",
    },
    "breakup_timing": {
        "low": "Filhaal strong breakup-timing pressure dominant nahi — repair phase relatively open dikhti hai.",
        "moderate": "Kuch timing-sensitive friction windows dikh rahe hain — in phases me extra care useful rahegi.",
        "elevated": "Timing phase separation ko test kar sakti hai — elevated-risk window me reaction control important hai.",
        "high": "High-risk timing + friction overlap dikh raha hai — is window me repair delay outcome ko worsen kar sakta hai.",
    },
    "avoid_breakup": {
        "low": "Chart me bond hold karne ke supportive indicators zyada dikhte hain — conscious repair se separation risk kam ho jayega.",
        "moderate": "Breakup avoid karna possible hai, par consistent repair effort ke bina friction badh sakti hai.",
        "elevated": "Separation risk elevated hai, par zero repair window nahi — realistic effort + boundaries se damage control possible hai.",
        "high": "High-risk zone hai, par immediate repair + honest assessment se worst-case trajectory slow ho sakti hai — miracle fix nahi, effort matter karta hai.",
    },
    "relationship_survive": {
        "low": "Relationship survive karne ke supportive chart signals zyada dikhte hain — repair capacity present hai.",
        "moderate": "Relationship survive ho sakti hai, par friction factors ko actively address karna hoga.",
        "elevated": "Survival sensitive zone me hai — bina repair changes ke bond weak ho jayega.",
        "high": "Survival ke high-risk pattern active hain — realistic repair plan ke bina bond hold karna mushkil dikhta hai.",
    },
    "toxic_breakup": {
        "low": "Strong toxic-end pattern dominant nahi — friction manageable repair range me dikhti hai.",
        "moderate": "Toxic / unhealthy friction ke mixed signals hain — boundaries + calm communication zaruri hai.",
        "elevated": "Toxic pattern separation ko push kar sakta hai — safety + boundaries priority honi chahiye.",
        "high": "Toxic / high-stress pattern ke high-risk indicators active hain — self-respect + safety realistic assessment ka hissa honi chahiye.",
    },
    "partner_leave": {
        "low": "Partner ke chhodne / leave karne ke strong indicators abhi dominant nahi dikhte.",
        "moderate": "Partner distance ya leave intent ke mixed signals de sakta hai — clarity through calm talk useful hai.",
        "elevated": "Partner ke alag hone / chhodne ke sensitive indicators active hain — reassurance + repair dono test honge.",
        "high": "Partner leave / walk-away ke high-risk indicators active hain — ye guaranteed nahi, par serious repair window narrow dikhti hai.",
    },
    "general_breakup_risk": {
        "low": "Chart ke hisaab se breakup / separation risk mostly low dikhta hai.",
        "moderate": "Breakup / separation risk moderate zone me hai — friction repairable range me dikhti hai.",
        "elevated": "Breakup / separation risk elevated hai — distance themes bond ko test kar rahi hain.",
        "high": "Breakup / separation ke high-risk pattern active hain — repair delay risky hai, par pakka end nahi batata.",
    },
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "will_breakup": {
        "low": "Low risk matlab bond abhi hold ho jayega — small frictions ko ignore mat karein.",
        "moderate": "Moderate risk matlab outcome abhi repair par depend karta hai.",
        "elevated": "Elevated risk matlab distance patterns ko seriously address karna hoga.",
        "high": "High risk matlab worst-case trajectory possible hai, par conscious repair se shift ho jayega.",
    },
    "avoid_breakup": {
        "low": "Repair supportive hai — consistency se separation risk kam ho jayega.",
        "moderate": "Bachna possible hai par effort one-sided nahi hona chahiye.",
        "elevated": "Damage control realistic hai — blind hope se zyada action matter karega.",
        "high": "Serious repair + boundaries dono zaruri — miracle expectation avoid karein.",
    },
    "general_breakup_risk": {
        "low": "Risk low hai — bond maintain karne ke liye basic repair enough ho sakti hai.",
        "moderate": "Risk moderate hai — friction ko time par address karein.",
        "elevated": "Risk elevated hai — ignore karne se situation worsen ho sakti hai.",
        "high": "Risk high hai — realistic plan + repair effort priority honi chahiye.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "will_breakup": {
        "low": "Small frictions ko time par address karein — preventive repair helpful rahegi.",
        "moderate": "Ek calm, fact-based conversation se core issues identify karein.",
        "elevated": "Reaction se pehle pause lein — repeated arguments risk badhate hain.",
        "high": "Serious repair plan banayein — blame game se zyada behaviour change matter karta hai.",
    },
    "breakup_cause": {
        "moderate": "Root cause identify karein — communication, trust ya distance me se kya dominant hai.",
        "elevated": "Pattern repeat ho raha hai ya nahi — facts + examples se assess karein.",
        "high": "Core issue par honest assessment karein — temporary patch se long-term fix nahi aata.",
    },
    "avoid_breakup": {
        "low": "Healthy transparency + small weekly check-in risk ko low rakhega.",
        "moderate": "Dono taraf se equal effort verify karein — one-sided repair fail hoti hai.",
        "elevated": "Boundaries clear karein + toxic loops break karein.",
        "high": "Professional / trusted third-person support consider karein agar loops repeat ho rahe hon.",
    },
    "divorce_risk": {
        "moderate": "Legal end se pehle repair window genuinely try karein — rushed decisions avoid karein.",
        "elevated": "Long-standing issues ko document + discuss karein — clarity future decision me help karegi.",
        "high": "Emotional peak me final decision mat lein — calm phase me realistic assessment karein.",
    },
    "general_breakup_risk": {
        "low": "Consistency maintain karein — bond abhi stable range me hai.",
        "moderate": "Friction ignore mat karein — timely repair outcome improve karti hai.",
        "elevated": "Distance badhne se pehle honest conversation prioritize karein.",
        "high": "Repair plan + self-respect dono — hopeless panic ya blind denial dono avoid karein.",
    },
}

REPAIR_TEMPLATES: dict[str, dict[str, str]] = {
    "low": "Repair capacity supportive dikhti hai — small consistent efforts bond ko strengthen kar sakte hain.",
    "moderate": "Repair possible hai jab dono taraf se honest effort + changed behaviour dikhe.",
    "elevated": "Repair tabhi effective hogi jab core friction (trust, conflict, distance) directly address ho.",
    "high": "High-risk zone me repair narrow window me possible hai — immediate effort + realistic expectations zaruri hain.",
}

BREAKUP_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"separation\s+yoga|separation\s+friction", re.I), "Separation yoga friction ko amplify kar sakta hai."),
    (re.compile(r"reconnection|reconnect|repair", re.I), "Reconnection / repair capacity ke supportive indicators dikhte hain."),
    (re.compile(r"\bsaturn\b.*7th|saturn\s+on\s+7th", re.I), "Saturn 7th par delay aur distance themes la sakta hai."),
    (re.compile(r"\bmars\b.*7th|mars\s+on\s+7th", re.I), "Mars 7th par conflict spikes separation risk badha sakta hai."),
    (re.compile(r"third[\s-]?person|hidden\s+ties", re.I), "Third-person / hidden stress trust fracture ko worsen kar sakta hai."),
    (re.compile(r"moon\s+afflict|moon\s+under|moon\s+in\s+8th", re.I), "Emotional volatility reactions ko escalate kar sakti hai."),
    (re.compile(r"7th\s*lord.*dusthana", re.I), "7th lord weakness partnership stability ko test karta hai."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase separation / repair signals ko colour karti hai."),
]


def detect_breakup_answer_focus(
    question: str,
    *,
    question_dna: dict[str, Any] | None = None,
) -> str:
    """Question + optional DNA → breakup intent angle for template selection."""
    from ask_intent_fidelity import infer_breakup_angle

    q = (question or "").strip()
    angle = infer_breakup_angle(q) or "general_breakup_risk"

    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw

    bucket = str(item.get("bucket") or "").strip().lower()
    intent = str(item.get("intent") or "").strip().lower()

    if bucket == "breakup_separation" and angle == "general_breakup_risk":
        if re.search(r"(?ix)\b(kyun|why|reason|wajah)\b", q):
            angle = "breakup_cause"
        elif re.search(r"(?ix)\b(divorce|talak)\b", q):
            angle = "divorce_risk"
        elif re.search(r"(?ix)\b(bacha|save|avoid)\b", q):
            angle = "avoid_breakup"
        else:
            angle = "will_breakup"
    if "divorce" in intent or "talak" in intent:
        angle = "divorce_risk"
    elif "cause" in intent or "reason" in intent:
        angle = "breakup_cause"
    elif "timing" in intent:
        angle = "breakup_timing"

    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "moderate").strip().lower()
    ang = (angle or "general_breakup_risk").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_breakup_risk"]
    return block.get(lv) or block.get("moderate", block["high"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "moderate").strip().lower()
    ang = (angle or "general_breakup_risk").strip().lower()
    block = MEANING_TEMPLATES.get(ang) or MEANING_TEMPLATES.get("general_breakup_risk") or {}
    return block.get(lv) or MEANING_TEMPLATES["general_breakup_risk"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "moderate").strip().lower()
    ang = (angle or "general_breakup_risk").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES.get("general_breakup_risk") or {}
    return block.get(lv) or PRACTICAL_TEMPLATES["general_breakup_risk"].get(lv, "Friction ko time par address karein — repair delay risky hoti hai.")


def get_repair_outlook(level: str) -> str:
    lv = (level or "moderate").strip().lower()
    return REPAIR_TEMPLATES.get(lv) or REPAIR_TEMPLATES["moderate"]


def breakup_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in BREAKUP_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me separation / repair related factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = breakup_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out

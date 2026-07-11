"""Loyalty / trust engine — intent templates (opening, meaning, practical per angle × level)."""
from __future__ import annotations

from .user_section_labels import NATURAL_USER_SECTION as _NATURAL_SEC

import re
from typing import Any

LOYALTY_LEVELS: tuple[str, ...] = ("moderate", "mixed", "unstable", "risky")

VERDICT_LABELS: dict[str, str] = {
    "moderate": "Moderate",
    "mixed": "Mixed",
    "unstable": "Unstable",
    "risky": "Risky",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "moderate": 78,
    "mixed": 58,
    "unstable": 44,
    "risky": 28,
}

USER_SECTION = dict(_NATURAL_SEC)

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "cheating_risk": {
        "moderate": "Chart me strong cheating signal nahi, lekin trust verify karte waqt consistent behaviour dekhein.",
        "mixed": "Chart me cheating / dhokhe ke mixed signals hain — kuch supportive, kuch challenging indicators dono active hain.",
        "unstable": "Chart ke hisaab se cheating / loyalty par sensitive zone active hai — trust abhi easily test ho sakta hai.",
        "risky": "Chart ke hisaab se cheating / dhokhe ke high-risk indicators active hain — partner loyalty par strong doubt zone dikh raha hai.",
    },
    "is_loyal": {
        "moderate": "Haan — chart ke hisaab se partner mostly loyal / trustworthy dikhta hai.",
        "mixed": "Partner me loyalty ke mixed signals hain — interest hai par friction trust ko test kar sakta hai.",
        "unstable": "Partner ki loyalty abhi sensitive / unstable phase me dikhti hai — vishwas easily shake ho sakta hai.",
        "risky": "Chart ke hisaab se partner ki loyalty abhi high-risk zone me dikhti hai — strong trust assume karna safe nahi.",
    },
    "trust_issues": {
        "moderate": "Trust ke supportive indicators zyada hain — relationship me vishwas mostly stable dikhta hai.",
        "mixed": "Trust ke mixed signals hain — kuch factors support karte hain, kuch distance ya friction test karte hain.",
        "unstable": "Trust layer sensitive hai — chart me vishwas ko weaken karne wale indicators active hain.",
        "risky": "Trust ke high-risk pattern dikh rahe hain — secrecy, impulse ya hidden attention trust ko weak karte hain.",
    },
    "faithfulness": {
        "moderate": "Partner me faithfulness / wafadari ke supportive chart signals zyada dikhte hain.",
        "mixed": "Faithfulness ke mixed phase me hain — loyal intent hai par consistency verify karni chahiye.",
        "unstable": "Wafadari / faithfulness abhi unstable dikhti hai — emotional ups-downs trust test kar sakte hain.",
        "risky": "Faithfulness ke high-risk indicators active hain — impulse ya secrecy loyalty ko weak kar sakte hain.",
    },
    "exclusive": {
        "moderate": "Chart exclusive / sirf-aapke-liye intent ko mostly support karta hai.",
        "mixed": "Exclusive intent ke mixed signals hain — loyalty hai par outside attention ka risk bhi dikh sakta hai.",
        "unstable": "Exclusivity sensitive zone me hai — partner ka focus split hone ke indicators hain.",
        "risky": "Exclusive commitment ke high-risk pattern dikh rahe hain — parallel attention ya impulse blur risk active hai.",
    },
    "secret_relationship": {
        "moderate": "Strong secret-relationship signal nahi — transparency mostly manageable dikhti hai.",
        "mixed": "Secret / hidden attention ke mixed indicators hain — verify karna zaruri hai.",
        "unstable": "Hidden ties ya secret behaviour ke sensitive signals active hain.",
        "risky": "Secret relationship / hidden parallel attention ke high-risk indicators chart me active hain.",
    },
    "multiple_partners": {
        "moderate": "Double-dating / multiple partner ke strong indicators nahi dikhte.",
        "mixed": "Multiple attention / parallel interest ke mixed signals hain.",
        "unstable": "Partner ke multiple / parallel interest ke sensitive indicators active hain.",
        "risky": "Multiple partners / double-dating ke high-risk pattern chart me active dikh rahe hain.",
    },
    "hidden_behavior": {
        "moderate": "Chupke / hidden behaviour ke strong risk signals nahi — transparency mostly ok dikhti hai.",
        "mixed": "Hidden behaviour ke mixed indicators hain — kuch cheezein open nahi ho sakti.",
        "unstable": "Secrecy / hidden behaviour ke sensitive signals trust ko test karte hain.",
        "risky": "Hidden behaviour / secrecy ke high-risk indicators loyalty ko seriously weaken karte hain.",
    },
    "emotional_loyalty": {
        "moderate": "Emotional loyalty ke supportive indicators zyada dikhte hain.",
        "mixed": "Emotional loyalty mixed phase me hai — feelings hain par consistency verify karein.",
        "unstable": "Emotional loyalty unstable dikhti hai — mood swings trust test kar sakte hain.",
        "risky": "Emotional loyalty ke high-risk pattern — attachment aur impulse dono trust ko blur kar sakte hain.",
    },
    "flirt_only": {
        "moderate": "Sirf flirt / casual intent ka dominant signal nahi — deeper loyalty support dikhta hai.",
        "mixed": "Flirt / casual energy aur loyalty ke mixed signals ek saath dikh rahe hain.",
        "unstable": "Casual / flirt intent loyalty ko test kar sakta hai — seriousness verify karein.",
        "risky": "Flirt / casual-over-loyalty pattern high-risk zone me dikhta hai.",
    },
    "general_trust": {
        "moderate": "Chart ke hisaab se trust / loyalty mostly stable dikhti hai.",
        "mixed": "Trust / loyalty ke mixed signals hain — supportive aur challenging dono active hain.",
        "unstable": "Trust / loyalty sensitive phase me hai — vishwas easily test ho sakta hai.",
        "risky": "Trust / loyalty ke high-risk pattern active hain — secrecy ya impulse weak karte hain.",
    },
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "cheating_risk": {
        "risky": "Ye cheating ka final proof nahi, lekin chart loyalty ko weak karne wale factors highlight karta hai.",
        "unstable": "Strong cheating proof nahi, par trust layer abhi sensitive hai.",
        "mixed": "Chart one-sided proof nahi deta — behaviour pattern verify karna zaruri hai.",
        "moderate": "High cheating risk dominant nahi — lekin actions se verify karte rahein.",
    },
    "is_loyal": {
        "risky": "Loyal maanna abhi safe nahi — chart high-risk loyalty pattern dikhata hai.",
        "unstable": "Loyalty possible hai par abhi stable phase nahi dikhta.",
        "mixed": "Loyalty ke signs hain par consistency abhi full nahi.",
        "moderate": "Loyal intent ko chart support karta hai — actions match honi chahiye.",
    },
    "general_trust": {
        "risky": "Vishwas blind mat karein — chart challenging loyalty factors zyada active hain.",
        "unstable": "Trust build ho sakta hai par abhi sensitive window hai.",
        "mixed": "Trust possible hai par friction factors bhi active hain.",
        "moderate": "Trust ke foundation mostly stable dikhte hain.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "cheating_risk": {
        "risky": "Accusation se pehle patterns dekhein — repeated secrecy, distance, ya behaviour change verify karein.",
        "unstable": "Trust verify karte waqt facts aur repeated actions ko priority dein.",
        "mixed": "Words se zyada consistency aur transparency pattern observe karein.",
        "moderate": "Low dominant risk hai — phir bhi open facts se trust maintain karein.",
    },
    "is_loyal": {
        "risky": "Blind trust avoid karein — loyalty claims ko time + actions se match karein.",
        "unstable": "Short-term reassurance par depend kam karein — pattern kuch hafton tak dekhein.",
        "mixed": "Loyalty ke positive signs ko negative friction ke saath balance karke dekhein.",
        "moderate": "Supportive pattern hai — healthy transparency se trust strong rehta hai.",
    },
    "general_trust": {
        "risky": "Trust tabhi badhe jab behaviour consistently transparent ho.",
        "unstable": "Emotional reaction se pehle facts collect karein.",
        "mixed": "Ek honest fact-based check-in helpful rehta hai.",
        "moderate": "Trust maintain karne ke liye consistency enough hai.",
    },
}

TRUST_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"third[\s-]?person|parallel\s+attention|hidden\s+ties", re.I), "Hidden / parallel attention trust ko weaken kar sakta hai."),
    (re.compile(r"rahu.*7th|loyalty\s+lines\s+blur", re.I), "Loyalty boundaries blur hone ke indicators dikh rahe hain."),
    (re.compile(r"venus.*mars|impulse.*loyalty", re.I), "Impulse passion loyalty ko temporarily override kar sakta hai."),
    (re.compile(r"moon.*8th|secrecy", re.I), "Secrecy theme trust tests ko active karta hai."),
    (re.compile(r"7th\s*lord.*debil|loyalty\s+structure", re.I), "Loyalty structure ko strengthen karne me challenge dikh raha hai."),
    (re.compile(r"d9.*loyalty|inner\s+loyalty", re.I), "Long-term inner loyalty layer mixed ya sensitive dikhti hai."),
    (re.compile(r"saturn.*moon|duty[\s-]?bound", re.I), "Duty-bound loyalty support dikh sakta hai."),
    (re.compile(r"dasha|transit", re.I), "Current timing phase loyalty signals ko colour karti hai."),
]


def detect_loyalty_answer_focus(
    question: str,
    *,
    question_dna: dict[str, Any] | None = None,
) -> str:
    """Question + optional DNA → loyalty intent angle for template selection."""
    from ask_intent_fidelity import infer_loyalty_angle

    q = (question or "").strip()
    angle = infer_loyalty_angle(q) or "general_trust"

    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw

    bucket = str(item.get("bucket") or "").strip().lower()
    intent = str(item.get("intent") or "").strip().lower()

    if bucket == "third_person_infidelity" and angle == "general_trust":
        angle = "secret_relationship"
    elif bucket == "trust_loyalty" and angle == "general_trust":
        if re.search(r"(?ix)\b(cheat|dhokha|affair)\b", q):
            angle = "cheating_risk"
        elif re.search(r"(?ix)\b(loyal|faithful|wafad)\b", q):
            angle = "is_loyal"
        else:
            angle = "trust_issues"
    if "cheat" in intent or "affair" in intent:
        angle = "cheating_risk"
    elif "loyal" in intent:
        angle = "is_loyal"

    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_trust").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_trust"]
    return block.get(lv) or block.get("mixed", block["risky"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_trust").strip().lower()
    block = MEANING_TEMPLATES.get(ang) or MEANING_TEMPLATES.get("general_trust") or {}
    return block.get(lv) or MEANING_TEMPLATES["general_trust"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_trust").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES.get("general_trust") or {}
    return block.get(lv) or PRACTICAL_TEMPLATES["general_trust"].get(lv, "")


def trust_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in TRUST_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me trust-related factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = trust_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out

"""Chart-backed proof helpers for health LLM answers."""

from __future__ import annotations

import re
from typing import Any

_PLANET_NAMES = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
_HOUSE_WORDS = {
    1: r"(?:1st|first|pehla|pehle|lagna|pratham)",
    2: r"(?:2nd|second|doosra|dusra|doosre)",
    3: r"(?:3rd|third|teesra|tee?sre)",
    4: r"(?:4th|fourth|chautha|chauthi)",
    5: r"(?:5th|fifth|paanchva|panchva)",
    6: r"(?:6th|sixth|chhatha|chhathi|chhath|rog)",
    7: r"(?:7th|seventh|saatva|saatwi)",
    8: r"(?:8th|eighth|aathva|aathwi|mrityu)",
    9: r"(?:9th|ninth|nauva|navam)",
    10: r"(?:10th|tenth|dasva|dasham)",
    11: r"(?:11th|eleventh|gyarahva)",
    12: r"(?:12th|twelfth|barahva|vyaya)",
}
_RESPiratory_Q_RX = re.compile(
    r"(?ix)(thand|thandi|sardi|cold|khansi|khaansi|saans|breath|chest|zukam|flu|allerg)"
)
_RESPiratory_ARCH = frozenset({
    "respiratory_health", "immune_health", "chronic_tendency", "general_health",
})
_HONEST_LOW_RX = re.compile(
    r"(?ix)("
    r"chart\s+me\s+.*(nahi|kam|mild|minor|zyada\s+strong\s+nahi|itni\s+.*nahi)|"
    r"zyada\s+tension\s+mat|bahut\s+zyada\s+.*nahi|itni\s+strong\s+.*nahi|"
    r"chart\s+support\s+nahi|tendency\s+.*(kam|mild|minor)|"
    r"seedha\s+signal\s+nahi|strong\s+signal\s+nahi"
    r")"
)
_PROOF_LINK_RX = re.compile(
    r"(?ix)(ghar|house|h\s*\d|sign|rashi|afflict|weak|kamzor|dusthana|combust|retro|"
    r"shadbala|lord|lagnesh|malefic|pressure|6th|8th|12th|moon)"
)
_GENERIC_ONLY_RX = re.compile(
    r"(?ix)^(dekh[oie]?|chart\s+me|aapke\s+chart).*(pollution|pranayama|fresh\s+hawa|"
    r"safai|environment|stress\s+bhi\s+kam)"
)
_DISEASE_LIST_Q_RX = re.compile(
    r"(?ix)(kya\s+kya\s+(?:health\s+|sehat\s+|tabiyat\s+)?(?:issue|problem|dikkat|bimari|disease|rog)|"
    r"(?:issue|problem|dikkat|bimari|disease)\s+ho\s+sakt)"
)


def is_disease_list_question(question: str) -> bool:
    return bool(_DISEASE_LIST_Q_RX.search(question or ""))


def _chart_pack(execution: dict[str, Any], key: str) -> dict[str, Any]:
    chart = execution.get(key) if isinstance(execution.get(key), dict) else {}
    return chart if not chart.get("error") else {}


def _collect_d1_signals(d1: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for aff in d1.get("afflictions") or []:
        text = str(aff).strip()
        if text:
            reasons.append(text)

    sub = d1.get("sub_flags") if isinstance(d1.get("sub_flags"), dict) else {}
    if sub.get("moon_afflicted"):
        reasons.append("Moon afflicted (engine flag)")
    if sub.get("chronic_pressure"):
        reasons.append("Chronic pressure flag in chart pack")
    if sub.get("immune_weak"):
        reasons.append("Immune weakness flag in chart pack")

    for row in d1.get("planets") or []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        house = int(row.get("house") or 0)
        dignity = str(row.get("dignity") or "").lower()
        strength = int(row.get("strength_score") or 0)
        if house in (6, 8, 12) and name in _PLANET_NAMES:
            reasons.append(f"{name} in house {house}")
        if name == "Moon" and (strength <= 0 or dignity in ("debilitated", "enemy")):
            reasons.append(f"Moon weak ({dignity or 'low strength'})")
        if name in ("Saturn", "Rahu") and house in (1, 4, 6, 8, 12):
            reasons.append(f"{name} pressure in house {house}")

    for row in d1.get("health_houses") or []:
        if not isinstance(row, dict):
            continue
        hn = int(row.get("house") or 0)
        occ = row.get("occupants") or []
        lord = str(row.get("lord") or (row.get("lord_state") or {}).get("lord") or "").strip()
        if hn in (6, 8, 12):
            if occ:
                reasons.append(f"House {hn} occupants: {', '.join(str(x) for x in occ[:4])}")
            elif lord:
                reasons.append(f"House {hn} lord: {lord}")

    for key in ("preventive_risk", "chronic_tendency", "overall_vitality", "mental_stress"):
        dim = (d1.get("dimensions") or {}).get(key) if isinstance(d1.get("dimensions"), dict) else {}
        if isinstance(dim, dict):
            reason = str(dim.get("reason") or "").strip()
            if reason:
                reasons.append(reason[:140])

    seen: set[str] = set()
    unique: list[str] = []
    for item in reasons:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def chart_support_signals(
    question: str,
    archetype: str,
    execution: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Return whether JSON has citeable chart signals for this question."""
    d1 = _chart_pack(execution, "d1")
    signals = _collect_d1_signals(d1)
    return bool(signals), signals


def answer_cites_chart_proof(answer: str, execution: dict[str, Any]) -> bool:
    """True when answer anchors a claim to a planet/house/sign/affliction from JSON."""
    text = (answer or "").strip()
    if not text:
        return False

    for chart_key in ("d1", "d9"):
        chart = _chart_pack(execution, chart_key)
        for aff in chart.get("afflictions") or []:
            aff_text = str(aff).strip()
            if len(aff_text) >= 12 and aff_text.lower() in text.lower():
                return True
            for planet in _PLANET_NAMES:
                if planet in aff_text and re.search(rf"\b{re.escape(planet)}\b", text, re.I):
                    return True

        for row in chart.get("planets") or []:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            if not name or name == "Ascendant":
                continue
            if not re.search(rf"\b{re.escape(name)}\b", text, re.I):
                continue
            house = int(row.get("house") or 0)
            sign = str(row.get("sign") or "").strip()
            window = text[max(0, text.lower().find(name.lower()) - 80):]
            window += text[text.lower().find(name.lower()):][:120]
            if house and (
                re.search(rf"\b{house}\b", window)
                or (house in _HOUSE_WORDS and re.search(_HOUSE_WORDS[house], window, re.I))
                or re.search(rf"\bH\s*{house}\b", window, re.I)
            ):
                return True
            if sign and len(sign) > 2 and re.search(rf"\b{re.escape(sign)}\b", window, re.I):
                return True
            if _PROOF_LINK_RX.search(window):
                return True

        asc = str(chart.get("ascendant") or "").strip()
        lagnesh = chart.get("lagnesh") if isinstance(chart.get("lagnesh"), dict) else {}
        lord = str(lagnesh.get("lord") or "").strip()
        if lord and re.search(rf"\b{re.escape(lord)}\b", text, re.I) and _PROOF_LINK_RX.search(text):
            return True
        if asc and re.search(rf"\b{re.escape(asc)}\b", text, re.I) and _PROOF_LINK_RX.search(text):
            return True

        for row in chart.get("health_houses") or []:
            if not isinstance(row, dict):
                continue
            hn = int(row.get("house") or 0)
            if hn not in (1, 6, 8, 12):
                continue
            house_pat = _HOUSE_WORDS.get(hn)
            if house_pat and re.search(house_pat, text, re.I) and _PROOF_LINK_RX.search(text):
                return True
            lord = str(row.get("lord") or (row.get("lord_state") or {}).get("lord") or "").strip()
            if lord and re.search(rf"\b{re.escape(lord)}\b", text, re.I) and (
                (house_pat and re.search(house_pat, text, re.I)) or _PROOF_LINK_RX.search(text)
            ):
                return True

    return False


def answer_honest_low_tension(answer: str) -> bool:
    return bool(_HONEST_LOW_RX.search(answer or ""))


def validate_chart_proof_requirement(
    question: str,
    answer: str,
    archetype: str,
    execution: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Enforce proof when chart supports issue; honest downgrade when it does not."""
    issues: list[str] = []
    supported, signals = chart_support_signals(question, archetype, execution)
    has_proof = answer_cites_chart_proof(answer, execution)
    honest_low = answer_honest_low_tension(answer)

    if signals and not has_proof:
        issues.append("missing_chart_proof")
    elif is_disease_list_question(question or "") and not has_proof:
        issues.append("missing_chart_proof")
    elif (
        not honest_low
        and not has_proof
        and _RESPiratory_Q_RX.search(question or "")
    ):
        if re.search(r"(?ix)(weak|kamzor|tendency|problem|issue|allergy|lungs|saans)", answer or ""):
            issues.append("unsupported_claim_without_proof")
    elif _GENERIC_ONLY_RX.search(answer or "") and not has_proof:
        issues.append("generic_advice_without_proof")

    return len(issues) == 0, issues


def proof_retry_hint(signals: list[str], question: str = "") -> str:
    if is_disease_list_question(question):
        return (
            "User ne disease list puchi — specific disease naam (diabetes, cancer, asthma, TB) "
            "mat likho. JSON se vulnerability zones batao: planet + 6th/8th/12th ghar/lord/affliction."
        )
    if not signals:
        return (
            "Chart me is sawal ki strong signal nahi — seedha bolo tendency zyada nahi dikhti, "
            "zyada tension mat lo."
        )
    sample = "; ".join(signals[:3])
    return (
        f"Chart proof zaroori — JSON se cite karo, jaise: {sample}. "
        "Planet + ghar/sign/affliction/weak clearly likho."
    )

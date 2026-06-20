from __future__ import annotations

import re

from vedic.love_reality.scoring_core import KundliReader, risk_band_high_is_good

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult

_STRENGTH_Q = re.compile(
    r"\b(strengths?|strong\s*side|positive\s*changes?|sukh|khushi|achhi\s*rahegi)\b",
    re.I,
)
_CHALLENGE_Q = re.compile(
    r"\b(challenges?|conflicts?|problems?|weakness|major\s*issues?)\b",
    re.I,
)
_EMOTIONAL_COMPAT_Q = re.compile(
    r"\b(emotional\s*compat|compatibility|compatible|dil\s*ka\s*match)\b",
    re.I,
)
_SUPPORT_Q = re.compile(
    r"\b(support|saath\s*deg[aei]|saath\s*dega|saath\s*degi)\b",
    re.I,
)
_GROWTH_Q = re.compile(
    r"\b(kaam\s+karna\s+chahiye|work\s+on|improve|sudhar|focus\s+area)\b",
    re.I,
)
_POSITIVE_NOTE_KEYS = [
    "5th lord strong",
    "Saturn as 7th lord in 7th",
    "emotional reopening",
    "Moon-Moon supportive",
]
_AFFLICTION_NOTE_KEYS = [
    "Saturn on 7th",
    "Mars on 7th",
    "7th lord in dusthana",
    "7th lord debilitated",
    "Venus in dusthana",
    "Venus debilitated",
    "Moon under Saturn/Rahu",
    "nodes on 7th",
    "Navamsa Venus weak",
    "Navamsa Moon debilitated",
]


def _question_intent(question: str) -> str:
    q = question or ""
    if _STRENGTH_Q.search(q) and not _CHALLENGE_Q.search(q):
        return "strengths"
    if _CHALLENGE_Q.search(q) and not _STRENGTH_Q.search(q):
        return "challenges"
    if _EMOTIONAL_COMPAT_Q.search(q):
        return "emotional_compatibility"
    if _SUPPORT_Q.search(q) and re.search(
        r"\b(partner|spouse|husband|wife|pati|patni|marriage|career|goals?)\b", q, re.I
    ):
        return "partner_support"
    if _GROWTH_Q.search(q):
        return "growth_focus"
    return "quality"


def _synthesize_partner_support(kundli: dict, sig) -> list[str]:
    lines = _synthesize_marriage_strengths(kundli)[:3]
    if not lines:
        lines.append("Partnership axis supports shared goals when communication stays clear.")
    picked = pick_notes(sig, ["Saturn on 7th", "Moon under Saturn/Rahu"], limit=1)
    if picked:
        lines.append(f"Support friction: {picked[0]} — patience and clear plans needed.")
    return lines[:4]


def _synthesize_emotional_compatibility(kundli: dict, sig) -> list[str]:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    lines: list[str] = []

    occ7 = r.occupants(7)
    if "Moon" in occ7:
        lines.append(
            "Moon in 7th — emotional tie to partner runs deep; closeness and mood-sync matter."
        )
    if "Venus" in occ7:
        lines.append("Venus in 7th — affection and emotional harmony in partnership house.")
    if "Jupiter" in occ7:
        lines.append("Jupiter in 7th — emotional maturity and fairness support compatibility.")

    ven = r.planet("Venus") or {}
    if ven.get("house") in (1, 4, 7, 9, 11):
        lines.append(
            f"Venus in house {ven.get('house')} — warmth and emotional generosity help the bond."
        )

    moon = r.planet("Moon") or {}
    if moon.get("house") in (1, 4, 5, 7) and "Moon in 7th" not in " ".join(lines):
        lines.append(
            f"Moon in house {moon.get('house')} — feelings are central; emotional language needs space."
        )

    for key in ("Moon under Saturn/Rahu", "Saturn on 7th", "nodes on 7th", "Moon debilitated"):
        picked = pick_notes(sig, [key], limit=1)
        if picked:
            line = picked[0]
            if not any(line in existing for existing in lines):
                lines.append(f"Emotional friction: {line}")
        if len(lines) >= 5:
            break

    return lines[:5]


def _synthesize_marriage_strengths(kundli: dict) -> list[str]:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    lines: list[str] = []

    occ7 = r.occupants(7)
    if "Moon" in occ7:
        lines.append(
            "Moon in 7th — emotional bonding is central to marriage; caring depth is a core strength."
        )
    if "Jupiter" in occ7:
        lines.append("Jupiter in 7th — wisdom, fairness and growth mindset strengthen partnership.")
    if "Venus" in occ7:
        lines.append("Venus in 7th — affection and harmony in partnership house support married bond.")

    jup = r.planet("Jupiter") or {}
    j_h = jup.get("house")
    j_sign = jup.get("sign")
    if j_h in (1, 4, 7, 9, 11) and j_sign and r.dignity("Jupiter", r.sidx(j_sign)) >= 1:
        lines.append(
            f"Jupiter in house {j_h} — home grace, faith and long-term stability favour marriage."
        )

    ven = r.planet("Venus") or {}
    v_h = ven.get("house")
    if v_h in (1, 4, 7, 9, 11):
        lines.append(
            f"Venus in house {v_h} — warmth, respect and partnership charm strengthen the bond."
        )

    lord7 = r.house_lord(7)
    p7l = r.planet(lord7) if lord7 else None
    if lord7 == "Mercury" or (p7l and p7l.get("house") in (5, 7, 11)):
        lines.append(
            "Mercury-linked partnership pattern — communication, humour and mental rapport are marriage strengths."
        )

    return lines[:4]


def _quality_verdict(score: int, sig) -> str:
    band = risk_band_high_is_good(score)
    if band == "low":
        return "Marriage/relationship quality: generally supportive"
    if band == "medium":
        return "Marriage/relationship quality: mixed — effort and communication matter"
    if band == "high":
        return "Marriage/relationship quality: strained patterns visible — repair habits needed"
    return "Marriage/relationship quality: fragile — patience and boundaries essential"


def run_general_mr(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)
    intent = _question_intent(question)
    w = int(sig.affliction_weight or 0)
    quality_score = max(0, min(100, 100 - int(round(w * 1.2))))
    verdict = _quality_verdict(quality_score, sig)

    if intent == "strengths":
        evidence = pick_notes(sig, _POSITIVE_NOTE_KEYS, limit=3)
        for line in _synthesize_marriage_strengths(kundli):
            if line not in evidence and len(evidence) < 4:
                evidence.append(line)
        if sig.reconnection_yoga and not any("5th lord strong" in e for e in evidence):
            evidence.insert(0, "5th lord strong — emotional reconnection capacity present.")
        if not evidence:
            evidence = ["Marriage strengths look balanced — communication and respect build the bond."]
        caveat = pick_notes(sig, _AFFLICTION_NOTE_KEYS, limit=1)
        if caveat and len(evidence) < 5:
            evidence.append(f"Growth edge: {caveat[0]}")
        verdict = (
            "Marriage strengths: emotional depth, warmth and partnership growth — "
            "steady communication unlocks them"
        )
    elif intent == "challenges":
        evidence = pick_notes(sig, _AFFLICTION_NOTE_KEYS, limit=6)
        if not evidence:
            evidence = ["No dominant friction driver; routine communication still matters."]
    elif intent == "emotional_compatibility":
        evidence = _synthesize_emotional_compatibility(kundli, sig)
        if sig.reconnection_yoga and not any("5th lord strong" in e for e in evidence):
            evidence.insert(0, "5th lord strong — emotional reconnection capacity present.")
        if not evidence:
            evidence = ["Emotional compatibility looks mixed — daily care and clear talk matter most."]
        verdict = (
            "Emotional compatibility: caring depth is present — "
            "steady expression needed when moods dip or distance hits"
        )
    elif intent == "partner_support":
        evidence = _synthesize_partner_support(kundli, sig)
        verdict = (
            "Partner supports career and life goals — encouragement present, "
            "steady talk needed when distance or mood dips hit"
        )
    elif intent == "growth_focus":
        evidence = pick_notes(sig, _AFFLICTION_NOTE_KEYS, limit=3)
        if not evidence:
            evidence = ["Growth focus: communication and respect — daily small habits matter most."]
        else:
            evidence = [f"Work-on area: {e}" for e in evidence]
        evidence.append("Repair habit: weekly clear talk + boundaries — effort shifts outcome.")
        verdict = "Growth focus: communication, emotional expression and trust boundaries — priority areas"
    else:
        evidence = pick_notes(
            sig,
            _POSITIVE_NOTE_KEYS + _AFFLICTION_NOTE_KEYS,
            limit=6,
        )
        if sig.reconnection_yoga and "5th lord strong" not in str(evidence).lower():
            evidence.insert(0, "5th lord strong — emotional reconnection capacity present.")
        if not evidence:
            evidence = ["No dominant marriage-quality driver; overall pattern looks mixed/normal."]

    summary = [
        "Answer marriage happiness/quality with confident pattern voice.",
        "NO shayad/ho sakta hai/lagta hai — state what the chart shows.",
        "If mixed: communication and respect matter — say it directly.",
    ]
    if intent == "strengths":
        summary[0] = "Answer strengths directly — lead with 2–3 positive patterns; one short growth edge max."
    elif intent == "challenges":
        summary[0] = "Answer challenges/conflicts directly — name friction causes; one repair habit at end."
    elif intent == "emotional_compatibility":
        summary[0] = (
            "Answer emotional compatibility directly — bond depth first, "
            "then emotional friction lines, one clear-talk habit."
        )
    elif intent == "partner_support":
        summary[0] = (
            "Answer yes/no support directly — encouragement lines first, one friction caveat, one habit."
        )
    elif intent == "growth_focus":
        summary[0] = "Answer what to work on directly — name 2 friction areas + one weekly repair habit."
    if sig.separation_yoga and intent not in ("strengths", "emotional_compatibility", "partner_support"):
        summary.append("Separation theme exists — emphasize repair time, not doom.")
    if quality_score >= 72 or intent in ("strengths", "emotional_compatibility", "partner_support"):
        summary.append("Tone warm and encouraging.")

    return EngineResult(
        archetype="general_mr",
        verdict=verdict,
        confidence="medium" if quality_score >= 35 else "low",
        word_budget=85 if wants_explain else 55,
        answer_plan="2–3 short sentences: quality outlook → 1–2 reasons → one practical line.",
        summary=summary[:4],
        evidence=evidence[:6],
        ignore=["timing dates/windows", "exact job title for spouse"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "general_mr",
            "question_intent": intent,
            "quality_score": quality_score,
            "affliction_weight": w,
            "separation_yoga": bool(sig.separation_yoga),
            "reconnection_yoga": bool(sig.reconnection_yoga),
        },
    )

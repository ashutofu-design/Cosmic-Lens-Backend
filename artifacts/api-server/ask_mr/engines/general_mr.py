from __future__ import annotations

import re

from vedic.love_reality.scoring_core import KundliReader, SIGNS, risk_band_high_is_good

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult


def _dignity_word(r: KundliReader, planet: str, sign: str | None) -> str:
    """Plain strength label for a planet in its sign (best-effort)."""
    if not sign:
        return ""
    try:
        d = r.dignity(planet, r.sidx(sign))
    except Exception:
        return ""
    if d is None:
        return ""
    if d >= 1:
        return "strong"
    if d < 0:
        return "weak"
    return "neutral"


def _build_d1_relationship_snapshot(kundli: dict, sig) -> list[str]:
    """Full D1 relationship picture for OPEN questions that have no dedicated
    engine — the LLM narrator reads these factors and answers the user's exact
    question itself (chart-grounded, not a fixed verdict)."""
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)

    asc = k.get("ascendant") or k.get("lagna") or "Aries"
    asc_i = r.sidx(str(asc))
    sign7 = SIGNS[(asc_i + 6) % 12] if isinstance(asc_i, int) else None
    lord7 = r.house_lord(7)
    p7l = r.planet(lord7) if lord7 else None
    occ7 = r.occupants(7)

    lines: list[str] = [
        f"7th house (marriage/partner) sign: {sign7 or 'unknown'}.",
    ]
    if lord7 and p7l:
        dw = _dignity_word(r, lord7, p7l.get("sign"))
        lines.append(
            f"7th lord {lord7} in house {p7l.get('house')} sign {p7l.get('sign')}"
            + (f" ({dw})" if dw else "")
            + " — how the partnership behaves."
        )
    lines.append(
        f"Planets in 7th house: {', '.join(occ7) if occ7 else 'none'} (direct relationship tone)."
    )
    for planet, role in (
        ("Venus", "love/affection/spouse karak"),
        ("Mars", "passion/drive/temper"),
        ("Moon", "emotions/mind"),
        ("Jupiter", "wisdom/blessing"),
        ("Saturn", "duty/distance/patience"),
        ("Mercury", "communication"),
    ):
        p = r.planet(planet) or {}
        if p.get("house"):
            dw = _dignity_word(r, planet, p.get("sign"))
            lines.append(
                f"{planet} ({role}): house {p.get('house')} sign {p.get('sign')}"
                + (f" ({dw})" if dw else "")
                + "."
            )

    l5 = r.house_lord(5)
    p5 = r.planet(l5) if l5 else None
    if l5 and p5:
        lines.append(f"5th lord (romance/love) {l5} in house {p5.get('house')}.")

    flags: list[str] = []
    if getattr(sig, "saturn_on_7th", False):
        flags.append("Saturn touches 7th (delay/coolness/duty)")
    if getattr(sig, "mars_on_7th", False):
        flags.append("Mars touches 7th (heat/assertive/temper)")
    if getattr(sig, "rahu_on_7th_axis", False):
        flags.append("Rahu on 7th axis (unconventional/sudden shifts)")
    if getattr(sig, "separation_yoga", False):
        flags.append("separation theme (needs repair effort)")
    if getattr(sig, "reconnection_yoga", False):
        flags.append("reconnection capacity present")
    if getattr(sig, "loyalty_risk_high", False):
        flags.append("loyalty needs attention")
    if flags:
        lines.append("Key patterns: " + "; ".join(flags) + ".")

    return lines[:12]

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
    open_chart_qa = False

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
        # OPEN relationship question with no dedicated engine / sub-handler.
        # Hand the LLM the full D1 relationship picture so it answers the
        # user's EXACT question from the chart itself (chart-grounded QA).
        open_chart_qa = True
        evidence = _build_d1_relationship_snapshot(kundli, sig)
        if not evidence:
            evidence = ["D1 relationship data incomplete — answer cautiously from available factors."]
        verdict = (
            "Open relationship question — no fixed verdict; answer from the D1 "
            "relationship factors most relevant to what the user asked."
        )

    summary = [
        "Answer marriage happiness/quality with confident pattern voice.",
        "NO shayad/ho sakta hai/lagta hai — state what the chart shows.",
        "If mixed: communication and respect matter — say it directly.",
    ]
    if open_chart_qa:
        summary = [
            "OPEN question — no dedicated engine. Read the D1 RELATIONSHIP CHART facts and "
            "answer the user's EXACT question directly.",
            "Use ONLY the chart factors relevant to what was asked; ignore the rest. "
            "Give a clear stance + 1–2 plain reasons.",
            "Confident pattern voice — no shayad/ho sakta hai. Plain language, no house/planet "
            "jargon in the reply.",
        ]
    elif intent == "strengths":
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
    if (
        not open_chart_qa
        and sig.separation_yoga
        and intent not in ("strengths", "emotional_compatibility", "partner_support")
    ):
        summary.append("Separation theme exists — emphasize repair time, not doom.")
    if not open_chart_qa and (
        quality_score >= 72
        or intent in ("strengths", "emotional_compatibility", "partner_support")
    ):
        summary.append("Tone warm and encouraging.")

    return EngineResult(
        archetype="general_mr",
        verdict=verdict,
        confidence="medium" if quality_score >= 35 else "low",
        word_budget=(70 if open_chart_qa else 85) if wants_explain else (65 if open_chart_qa else 55),
        answer_plan=(
            "Answer the exact question from the relevant D1 factors → 1–2 plain reasons."
            if open_chart_qa
            else "2–3 short sentences: quality outlook → 1–2 reasons → one practical line."
        ),
        summary=summary[:4],
        evidence=evidence[:12] if open_chart_qa else evidence[:6],
        ignore=["timing dates/windows", "exact job title for spouse"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "general_mr",
            "question_intent": intent,
            "open_chart_qa": open_chart_qa,
            "quality_score": quality_score,
            "affliction_weight": w,
            "separation_yoga": bool(sig.separation_yoga),
            "reconnection_yoga": bool(sig.reconnection_yoga),
        },
    )

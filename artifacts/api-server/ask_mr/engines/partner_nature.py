from __future__ import annotations

from typing import Any

from vedic.love_reality.scoring_core import KundliReader, SIGNS

from ..types import EngineResult


def _gender_from_birth(birth: Any) -> str:
    if not isinstance(birth, dict):
        return "unknown"
    g = str(birth.get("gender") or birth.get("sex") or "").strip().lower()
    if g in ("male", "m", "man", "boy", "ladka"):
        return "male"
    if g in ("female", "f", "woman", "girl", "ladki"):
        return "female"
    return "unknown"


def partner_nature_narrator_payload(result: EngineResult) -> str:
    """Structured facts + mandatory 3-paragraph map for the LLM narrator."""
    lines = [
        "ARCHETYPE: partner_nature",
        f"VERDICT: {result.verdict}",
        "OUTPUT: exactly 3 paragraphs separated by a blank line (90–120 words total).",
        "PARA 1 — social vibe: use ONLY the 7th house sign evidence line.",
        "PARA 2 — emotions + mindset: use ONLY 7th lord + planets-in-7th evidence lines.",
        "PARA 3 — presence in love: use ONLY the partner-karak evidence line.",
    ]
    for item in result.evidence or []:
        lines.append(f"EVIDENCE: {item}")
    return "\n".join(lines)


def run_partner_nature(
    kundli: dict,
    question: str,
    *,
    birth: Any = None,
    wants_explain: bool = False,
) -> EngineResult:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)

    asc = k.get("ascendant") or k.get("lagna") or "Aries"
    asc_i = r.sidx(str(asc))
    sign7 = SIGNS[(asc_i + 6) % 12] if isinstance(asc_i, int) else None
    lord7 = r.house_lord(7)
    p7l = r.planet(lord7) if lord7 else None
    occ7 = r.occupants(7)

    gender = _gender_from_birth(birth)
    karak = "Venus" if gender != "female" else "Jupiter"
    pk = r.planet(karak)

    occ_label = ", ".join(occ7) if occ7 else "none"
    verdict = (
        "Partner nature: social vibe (7H sign), emotional tone in partnership (7H occupants), "
        "mindset in relationship (7L), and overall presence (karak)."
    )

    evidence: list[str] = []
    evidence.append(f"7th house sign baseline: {sign7 or 'unknown'} (partner vibe / social style).")
    if lord7 and p7l:
        evidence.append(
            f"7th lord placement: {lord7} in house {p7l.get('house')} sign {p7l.get('sign')} "
            f"(mindset + how partnership behaves)."
        )
    else:
        evidence.append(f"7th lord: {lord7 or 'unknown'} (placement not available).")
    evidence.append(f"Planets in 7th house: {occ7 or 'none'} (direct behavior tone).")
    if pk:
        evidence.append(
            f"Partner-karak by chart gender: {gender} → {karak} in house {pk.get('house')} sign {pk.get('sign')} "
            f"(presence/attraction style)."
        )
    else:
        evidence.append(f"Partner-karak by chart gender: {gender} → {karak} (placement not available).")

    return EngineResult(
        archetype="partner_nature",
        verdict=verdict,
        confidence="medium",
        word_budget=120,
        answer_plan=(
            "Para1: 7H sign social vibe → Para2: 7L + occupants emotional/mindset → "
            "Para3: karak presence (~90–120 words, blank line between paras)."
        ),
        summary=[
            "User asked partner/spouse nature (non-timing).",
            "Keep it warm and positive; avoid fatalistic wording.",
            f"7H occupants for tone: {occ_label}.",
        ],
        evidence=evidence[:6],
        ignore=[
            "timing dates/windows",
            "love-vs-arranged",
            "spouse profession",
            "manglik (unless asked)",
            "breakup risk (unless asked)",
        ],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "partner_nature",
            "gender": gender,
            "karak": karak,
            "sign7": sign7,
        },
    )

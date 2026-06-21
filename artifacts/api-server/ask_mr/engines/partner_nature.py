from __future__ import annotations

import re
from typing import Any

from vedic.love_reality.scoring_core import KundliReader, SIGNS

from ._person_signals import build_person_signals
from ..types import EngineResult

# Spouse's in-laws / family members (8H = 2nd from 7th) — NOT partner personality (7H).
# Excludes "family background / khandaan" (partner upbringing → 7H + Rahu branch).
_SPOUSE_FAMILY_RX = re.compile(
    r"(?ix)"
    r"(?:"
    r"(?:wife|husband|spouse|partner|pati|patni|biwi)\b"
    r".{0,45}\b(?:"
    r"family\s*wal\w*|ghar\s*wal\w*|ghar\s*ke\s*log|in[\s-]?laws?|"
    r"saas|sasur|sasural|sasuraal|rishtedaar|"
    r"(?:parivaar|parivar|pariwar|family|relatives)\s*(?:kaise|kya|kaisa|kaisi)\b"
    r")|"
    r"(?:saas|sasur|sasural|in[\s-]?laws?)\b"
    r"|"
    r"(?:family\s*wal\w*|ghar\s*wal\w*)\b"
    r".{0,30}\b(?:wife|husband|spouse|partner|pati|patni|biwi)\b"
    r")"
)
_USER_FAMILY_APPROVAL_RX = re.compile(
    r"(?ix)\b(?:mer[ei]|mere|my|parents?|ma\s*baap|papa|mummy|ghar\s*wal\w*)\b"
    r".{0,35}\b(?:manenge|manzoor|accept|swikar|approval|manna|allow)\b"
)


def _is_spouse_family_question(q: str) -> bool:
    if _USER_FAMILY_APPROVAL_RX.search(q or ""):
        return False
    return bool(_SPOUSE_FAMILY_RX.search(q or ""))


def _build_spouse_family_result(
    r: KundliReader,
    sig,
    *,
    wants_explain: bool,
    gender: str,
) -> EngineResult:
    """In-laws / spouse's family — 8th house axis only (not 7H partner personality)."""
    asc_i = r.asc_index()
    sign8 = SIGNS[(asc_i + 7) % 12] if isinstance(asc_i, int) else None
    lord8 = r.house_lord(8)
    p8l = r.planet(lord8) if lord8 else None
    occ8 = r.occupants(8)
    occ_label = ", ".join(occ8) if occ8 else "none"

    evidence: list[str] = [
        f"Spouse-family axis (8th house / 2nd from 7th): sign {sign8 or 'unknown'} — "
        "in-laws / sasural family tone and environment.",
        f"Planets in 8th house: {occ_label} — direct in-law / spouse-family influence.",
    ]
    if lord8 and p8l:
        evidence.append(
            f"8th lord {lord8} in house {p8l.get('house')} sign {p8l.get('sign')} — "
            "how the bond with spouse's family flows."
        )

    # Synthesized in-law tone from 8H occupants (plain language for narrator).
    if "Jupiter" in occ8:
        evidence.append(
            "In-law family tone: Jupiter in 8th — generally supportive, fair and "
            "tradition-respecting elders; wisdom in family matters."
        )
    if "Saturn" in occ8:
        evidence.append(
            "In-law family tone: Saturn in 8th — serious, duty-bound family; "
            "formality and patience needed; distance until trust builds."
        )
    if "Mars" in occ8:
        evidence.append(
            "In-law family tone: Mars in 8th — strong personalities in spouse's family; "
            "direct talk and boundaries help; occasional friction possible."
        )
    if "Moon" in occ8:
        evidence.append(
            "In-law family tone: Moon in 8th — emotionally involved family; "
            "feelings and home rituals matter a lot in sasural."
        )
    if "Rahu" in occ8:
        evidence.append(
            "In-law family tone: Rahu in 8th — different background or unconventional "
            "family setup; expectations may differ from your upbringing."
        )
    if "Venus" in occ8:
        evidence.append(
            "In-law family tone: Venus in 8th — warm, hospitality-oriented family; "
            "respect and pleasant conduct open doors."
        )
    if not any(
        p in occ8 for p in ("Jupiter", "Saturn", "Mars", "Moon", "Rahu", "Venus")
    ):
        evidence.append(
            f"In-law family baseline: {sign8 or 'unknown'} 8th-house sign sets the "
            "general social tone of spouse's family — read from that pattern."
        )

    if p8l and p8l.get("house") in (6, 8, 12):
        evidence.append(
            "8th lord in dusthana — extra effort needed with in-laws; "
            "clear boundaries and steady respect reduce friction."
        )

    verdict = (
        "Spouse's family / in-laws: read from 8th house (2nd from 7th) — "
        "family tone, environment and bond pattern."
    )
    summary = [
        "QUESTION FOCUS: spouse's family / in-laws — NOT partner's own personality.",
        "Use ONLY 8th-house / spouse-family evidence — do NOT use 7th-house partner traits as in-laws.",
        f"8H occupants for in-law tone: {occ_label}.",
        "Answer how spouse's family members are — confident pattern voice, no shayad.",
    ]

    return EngineResult(
        archetype="partner_nature",
        verdict=verdict,
        confidence="medium",
        word_budget=130 if wants_explain else 120,
        answer_plan=(
            "Para1: 8H sign + in-law family social tone → "
            "Para2: 8L + 8H occupants emotional/dynamic → "
            "Para3: one practical line for living with in-laws."
        ),
        summary=summary,
        evidence=evidence[:8],
        ignore=[
            "7th house partner personality (wrong axis for this question)",
            "timing dates/windows",
            "love-vs-arranged",
        ],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "partner_nature",
            "question_focus": "spouse_family",
            "gender": gender,
            "sign8": sign8,
            "occ8": occ_label,
        },
    )


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
    evidence = result.evidence or []
    has_bg = any("Different background theme" in e for e in evidence)
    is_inlaw = (result.checks or {}).get("question_focus") == "spouse_family"
    synth_keys = (
        "partnership style",
        "emotional style",
        "nature blend",
        "feeling depth",
        "care style",
        "respect pattern",
    )
    has_synth = any(any(k in e.lower() for k in synth_keys) for e in evidence)

    lines = [
        "ARCHETYPE: partner_nature",
        f"VERDICT: {result.verdict}",
        "OUTPUT: exactly 3 paragraphs separated by a blank line (90–120 words total).",
        "TONE: confident — state traits as chart pattern (hai/hote hain/rehta hai). NO shayad/ho sakta hai/lagta hai.",
    ]
    if is_inlaw:
        lines.append(
            "QUESTION FOCUS: spouse's family / in-laws ONLY — do NOT describe partner's "
            "7th-house personality as if it were the in-laws."
        )
        lines.append("PARA 1 — in-law family social tone: use 8th house sign + in-law family tone evidence.")
        lines.append(
            "PARA 2 — bond dynamic: use 8th lord + planets-in-8th evidence only."
        )
        lines.append("PARA 3 — one practical line about living with spouse's family.")
    elif has_bg:
        lines.append(
            "PARA 1 — social vibe + family background: use 7th house sign AND Different background theme evidence."
        )
    else:
        lines.append("PARA 1 — social vibe: use ONLY the 7th house sign evidence line.")
    lines.append(
        "PARA 2 — emotions + mindset: use ONLY 7th lord + planets-in-7th evidence lines"
        + (" + any synthesized either/or line." if has_synth else ".")
    )
    lines.append(
        "PARA 3 — presence in love: use ONLY the partner-karak evidence line"
        + (" + respect/care synthesis if present." if has_synth else ".")
    )
    if has_synth:
        lines.append("HINT: Answer the either/or in the question directly using synthesized evidence line(s).")
    for item in result.summary or []:
        if item.startswith("Answer"):
            lines.append(f"HINT: {item}")
    for item in evidence:
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

    q = (question or "").lower()
    sig = build_person_signals(k)

    # In-laws / spouse's family — 8H axis ONLY (before any 7H partner-personality lines).
    if _is_spouse_family_question(q):
        return _build_spouse_family_result(r, sig, wants_explain=wants_explain, gender=gender)

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

    summary_extra: str | None = None

    if re.search(r"\b(express|reserved|emotion|feeling|khul|band)\b", q):
        expressive = bool(occ7 and "Moon" in occ7) or sign7 in ("Gemini", "Libra", "Leo", "Sagittarius", "Aries")
        reserved = bool(sig.saturn_on_7th) or sign7 in ("Capricorn", "Scorpio", "Virgo")
        if expressive and reserved:
            evidence.append(
                "Emotional style: partner caring/expressive side dikhta hai, par poori openness trust ke baad — "
                "pehle thoda guarded, baad mein khul kar expressive."
            )
            summary_extra = (
                "Answer expressive vs reserved directly: mostly expressive after trust, not fully closed."
            )
        elif expressive:
            evidence.append(
                "Emotional style: partner generally expressive — feelings behaviour mein dikhte hain, baat-cheet se closeness banati hai."
            )
            summary_extra = "Answer: partner expressive side zyada — reserved kam."
        elif reserved:
            evidence.append(
                "Emotional style: partner reserved-first — warmth slow but steady; push se nahi, trust se khulta hai."
            )
            summary_extra = "Answer: partner reserved side zyada — openly expressive kam."

    if re.search(
        r"\b(gussa|gusse|gussewala|gusaa|gusail|anger|angry|temper|"
        r"short[-\s]?temper|irritab|aggress|chidchid|naraz|krodh|"
        r"garam\s*dimag|garam[-\s]?mizaj|hot[-\s]?head|tez\s*mizaj)\b",
        q,
    ):
        mars = r.planet("Mars") or {}
        mars_fiery = mars.get("sign") in ("Aries", "Scorpio", "Capricorn")
        angry = (
            bool(sig.mars_on_7th)
            or lord7 == "Mars"
            or bool(occ7 and "Mars" in occ7)
            or bool(occ7 and "Sun" in occ7)
        )
        if angry:
            evidence.append(
                "Temper signal: Mars/aggression ka assar 7th house (rishta) pe hai — partner thoda "
                "garam-dimaag/jaldi react karne wala side rakhta hai"
                + (", aur Mars ki fiery sign isse thoda aur tez karti hai" if mars_fiery else "")
                + ", par baat-cheet se jaldi shaant bhi ho jaata hai."
            )
            summary_extra = (
                "Answer gussa directly: HAAN — Mars assar se partner ka temper/short-temper side "
                "hai, lekin manage ho jaata hai. Yeh baat clearly bolo (bich ya end mein)."
            )
        else:
            evidence.append(
                "Temper signal: 7th house (rishta) pe Mars/aggression ka strong assar nahi — partner "
                "generally calm, patient aur thanda-dimaag nature ka hai."
            )
            summary_extra = (
                "Answer gussa directly: NAHI — koi strong anger pattern nahi, partner zyadatar shaant "
                "rehta hai. Yeh baat clearly bolo (bich ya end mein)."
            )

    if re.search(r"\b(culture|foreign|videsh|city|background|alag\s*shahr)\b", q):
        rahu = r.planet("Rahu") or {}
        evidence.append(
            f"Different background theme: Rahu in house {rahu.get('house')} sign {rahu.get('sign')} — "
            "partner from another city/culture/background fits chart pattern."
        )
        summary_extra = (
            "Answer family/background directly — include Different background theme (Rahu) in Para 1."
        )

    if re.search(r"\b(dominant|cooperative|co-operative|controlling|bossy)\b", q):
        cooperative = sign7 in ("Gemini", "Libra", "Taurus") or bool(occ7 and "Moon" in occ7)
        assertive = (p7l and p7l.get("sign") == "Aries") or lord7 == "Mars"
        if cooperative and assertive:
            evidence.append(
                "Partnership style: cooperative-communicative default — shares decisions; "
                "Mercury Aries streak assertive in ideas, not controlling dominant."
            )
            summary_extra = (
                "Answer dominant vs cooperative: cooperative zyada, assertive kabhi — bossy controlling nahi."
            )
        elif cooperative:
            evidence.append(
                f"Partnership style: cooperative — {sign7 or '7th sign'} / Moon tone prefers talk, "
                "compromise and shared choices."
            )
            summary_extra = "Answer: partner cooperative — dominant controlling pattern kam."
        else:
            evidence.append("Partnership style: can take lead in decisions — direct tone when goals matter.")
            summary_extra = "Answer: partner dominant/assertive side zyada — cooperative bhi situational."

    if re.search(r"\b(love\s*language|care\s*dikhane|affection\s*style)\b", q):
        care_parts: list[str] = []
        if occ7 and "Moon" in occ7:
            care_parts.append("Moon in 7th — emotional presence and acts of care")
        moon = r.planet("Moon") or {}
        if moon.get("house") and not (occ7 and "Moon" in occ7):
            care_parts.append(
                f"Moon in house {moon.get('house')} sign {moon.get('sign')} — emotional care style"
            )
        merc = r.planet("Mercury") or {}
        if merc.get("house"):
            care_parts.append(
                f"Mercury in house {merc.get('house')} sign {merc.get('sign')} — "
                "words, humour and thoughtful talk"
            )
        ven = r.planet("Venus") or {}
        if ven.get("house"):
            care_parts.append(
                f"Venus in house {ven.get('house')} sign {ven.get('sign')} — "
                "warm gestures and quality time"
            )
        if care_parts:
            evidence.append("Care style: " + "; ".join(care_parts) + ".")
        summary_extra = "Answer love language directly from Care style evidence line(s)."

    if re.search(r"\b(spiritual|practical|ambitious|artistic)\b", q):
        blend: list[str] = []
        merc = r.planet("Mercury") or {}
        ven = r.planet("Venus") or {}
        jup = r.planet("Jupiter") or {}
        if merc.get("house"):
            blend.append(
                f"Mercury in house {merc.get('house')} sign {merc.get('sign')} — "
                "practical communication and ideas"
            )
        if ven.get("house"):
            blend.append(
                f"Venus in house {ven.get('house')} sign {ven.get('sign')} — "
                "artistic warmth and creative drive"
            )
        if jup.get("house") in (1, 5, 9, 12):
            blend.append(
                f"Jupiter in house {jup.get('house')} sign {jup.get('sign')} — "
                "spiritual/dharma values touch"
            )
        if sign7:
            blend.append(f"7th house sign {sign7} — social/practical partnership tone")
        if blend:
            evidence.append("Nature blend: " + "; ".join(blend) + ".")
        summary_extra = (
            "Answer nature options from chart placements in Nature blend evidence — not generic labels."
        )

    if re.search(r"\b(gehra|gehri|halki|halka|deep|superficial)\b", q) and re.search(
        r"\b(feelings?|pyaar|emotion)\b", q
    ):
        if occ7 and "Moon" in occ7:
            evidence.append(
                "Feeling depth: Moon in 7th — feelings partner ke saath gehre rehte hain, halki surface bond nahi."
            )
            summary_extra = "Answer gehra vs halki: feelings gehre (Moon 7th), halki nahi."
        else:
            evidence.append(
                "Feeling depth: feelings grow with trust — moderate start, depth builds over time."
            )
            summary_extra = "Answer gehra vs halki: depth trust ke saath badhti hai."

    if re.search(r"\b(respect|izzat|samman)\b", q):
        respect_parts = [f"7th house sign {sign7 or 'unknown'} sets partnership respect tone"]
        if occ7 and "Moon" in occ7:
            respect_parts.append("Moon in 7th — respect through talk and emotional regard")
        ven = r.planet("Venus") or {}
        if ven.get("house"):
            respect_parts.append(
                f"Venus in house {ven.get('house')} sign {ven.get('sign')} — mutual dignity and warmth"
            )
        evidence.append("Respect pattern: " + "; ".join(respect_parts) + ".")
        summary_extra = "Answer partner respect directly from Respect pattern evidence."

    summary = [
        "User asked partner/spouse nature (non-timing).",
        "State traits confidently from evidence — not hedged/shayad tone.",
        f"7H occupants for tone: {occ_label}.",
    ]
    if summary_extra:
        summary.append(summary_extra)

    return EngineResult(
        archetype="partner_nature",
        verdict=verdict,
        confidence="medium",
        word_budget=120,
        answer_plan=(
            "Para1: 7H sign social vibe → Para2: 7L + occupants emotional/mindset → "
            "Para3: karak presence (~90–120 words, blank line between paras)."
        ),
        summary=summary,
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
            "question_focus": "partner_personality",
            "gender": gender,
            "karak": karak,
            "sign7": sign7,
        },
    )

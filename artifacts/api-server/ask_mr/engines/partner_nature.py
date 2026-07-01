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
    question: str,
    wants_explain: bool,
    gender: str,
) -> EngineResult:
    """In-laws / spouse's family — 8th house axis only (not 7H partner personality)."""
    q = (question or "").lower()
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

    if re.search(r"\b(?:saas|sasur|mother[\s-]?in[\s-]?law)\b", q or ""):
        if re.search(r"\b(?:saas|mother[\s-]?in[\s-]?law)\b", q):
            if "Moon" in occ8:
                evidence.append(
                    "Mother-in-law (saas) tone: Moon in 8th — emotionally involved, caring but sensitive sasural elder."
                )
            if "Mars" in occ8:
                evidence.append(
                    "Mother-in-law (saas) tone: Mars in 8th — strong-willed saas; direct talk and respect open doors."
                )
            if "Saturn" in occ8:
                evidence.append(
                    "Mother-in-law (saas) tone: Saturn in 8th — traditional disciplined saas; patience builds trust."
                )
            if not any("Mother-in-law" in e for e in evidence):
                evidence.append(
                    f"Mother-in-law (saas) baseline: 8th house sign {sign8 or 'unknown'} sets sasural elder tone."
                )
        if re.search(r"\b(?:sasur|father[\s-]?in[\s-]?law)\b", q):
            sun = r.planet("Sun") or {}
            if "Sun" in occ8 or sun.get("house") == 8:
                evidence.append(
                    "Father-in-law (sasur) tone: Sun linked to 8th — dignified authority figure in spouse's family."
                )
            if "Saturn" in occ8:
                evidence.append(
                    "Father-in-law (sasur) tone: Saturn in 8th — serious principled sasur; formal respect matters."
                )
            if not any("Father-in-law" in e for e in evidence):
                evidence.append(
                    f"Father-in-law (sasur) baseline: 8th lord {lord8 or '?'} tone shapes sasur behaviour."
                )

    if re.search(r"\b(?:joint\s*family|nuclear\s*family)\b", q or ""):
        sign4 = SIGNS[(asc_i + 3) % 12] if isinstance(asc_i, int) else None
        occ4 = r.occupants(4)
        if re.search(r"\bnuclear\b", q):
            evidence.append(
                f"Nuclear-family tendency: 4th house (home) sign {sign4 or 'unknown'} with occupants "
                f"{occ4 or 'none'} — smaller independent household after marriage fits chart."
            )
        else:
            evidence.append(
                f"Joint-family tendency: 8th house (spouse family) sign {sign8 or 'unknown'} + "
                f"4th home sign {sign4 or 'unknown'} — shared family setup / sasural ghar influence strong."
            )

    if re.search(r"\b(?:interference|tut\s*na|dabang|control)\b", q or ""):
        if "Rahu" in occ8 or (r.planet("Rahu") or {}).get("house") == 8:
            evidence.append(
                "In-law interference: Rahu in 8th — unexpected meddling or strong opinions from spouse's family."
            )
        if "Mars" in occ8 or "Saturn" in occ8:
            evidence.append(
                "In-law interference: Mars/Saturn in 8th — family boundaries tested; clear respectful limits needed."
            )
        if not any("interference" in e for e in evidence):
            evidence.append(
                "In-law interference level: read from 8th house occupants — benefics ease, malefics need boundaries."
            )

    if re.search(r"\b(?:siblings?|devr|jeth|nanad|brother[\s-]?in[\s-]?law|sister[\s-]?in[\s-]?law)\b", q):
        evidence.append(
            f"Spouse's siblings / extended in-laws: 8th house occupants {occ_label} — "
            "extended family member tone in sasural."
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
        evidence=evidence[:10],
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


def _has_spouse_word(q: str) -> bool:
    return bool(re.search(r"\b(partner|spouse|husband|wife|pati|patni|biwi)\b", q or ""))


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
    from ._evidence_split import format_split_evidence_block

    lines.extend(format_split_evidence_block(evidence))
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
        return _build_spouse_family_result(
            r, sig, question=question, wants_explain=wants_explain, gender=gender
        )

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

    attachment_q = bool(
        re.search(
            r"(?ix)\b("
            r"emotional\s+attachment|attachment\s+kaisa|lagav\s+kaisa|"
            r"bond\s+kaisa|rishte\s+ka\s+gehra|dono\s+ka\s+attachment"
            r")\b",
            q,
        )
    )
    if attachment_q:
        verdict = (
            "Partnership emotional attachment: bond depth from 7H Moon + 7L placement + karak — "
            "weigh supportive vs affliction evidence."
        )
        if occ7 and "Moon" in occ7 and not sig.moon_afflicted:
            evidence.append(
                "Partnership attachment positive: Moon in 7th — emotional closeness and caring bond tone."
            )
        if sign7 in ("Gemini", "Libra", "Leo", "Sagittarius"):
            evidence.append(
                f"Partnership attachment positive: communicative 7th sign {sign7} — "
                "attachment stays alive through talk and sharing."
            )
        if pk and pk.get("sign") in ("Leo", "Taurus", "Libra", "Pisces"):
            evidence.append(
                f"Partnership attachment positive: {karak} in {pk.get('sign')} "
                f"(house {pk.get('house')}) — warmth and expressive affection in the relationship."
            )
        if p7l and int(p7l.get("house") or 0) in (6, 8, 12):
            evidence.append(
                f"Partnership attachment affliction: 7th lord in house {p7l.get('house')} "
                f"sign {p7l.get('sign')} — hidden distance, tests, or emotional withdrawal phases possible."
            )
        if sig.saturn_on_7th or sig.rahu_on_7th_axis:
            evidence.append(
                "Partnership attachment affliction: Saturn/Rahu stress on 7th axis — "
                "bond needs patience; cooling or distance phases possible."
            )
        if sig.moon_afflicted or sig.moon_debil:
            evidence.append(
                "Partnership attachment affliction: Moon afflicted/debilitated — "
                "mood swings can affect felt closeness between you."
            )
        summary_extra = (
            "Answer attachment quality first: strong / mixed / cautious — match positive vs affliction balance."
        )

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
                f"assertive streak from {lord7 or '7th lord'} placement, not controlling dominant."
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

    if re.search(r"\b(introvert|extrovert|antar\s*mukhi|bahar\s*mukhi)\b", q):
        extro = sign7 in ("Gemini", "Leo", "Libra", "Sagittarius", "Aries") or bool(
            occ7 and ("Moon" in occ7 or "Mercury" in occ7)
        )
        intro = sign7 in ("Cancer", "Scorpio", "Capricorn", "Virgo", "Pisces") or bool(sig.saturn_on_7th)
        if extro and not intro:
            evidence.append(
                "Social energy: extrovert-leaning partner — open talkative social vibe from 7th sign/occupants."
            )
            summary_extra = "Answer introvert vs extrovert: extrovert side zyada."
        elif intro and not extro:
            evidence.append(
                "Social energy: introvert-leaning partner — private thoughtful vibe; opens up with trust."
            )
            summary_extra = "Answer introvert vs extrovert: introvert side zyada."
        else:
            evidence.append(
                "Social energy: ambivert mix — social in familiar circles, reserved in new settings."
            )
            summary_extra = "Answer introvert vs extrovert: mix — situational."

    if re.search(r"\b(romantic|romance)\b", q) and _has_spouse_word(q):
        ven = r.planet("Venus") or {}
        if "Venus" in occ7 or ven.get("house") in (5, 7):
            evidence.append(
                "Romantic nature: Venus on love/partnership axis — partner gestures, dates and warmth naturally romantic."
            )
        else:
            evidence.append(
                f"Romantic nature: Venus in house {ven.get('house')} — romance style through practical steady affection."
            )
        summary_extra = "Answer romantic directly from Romantic nature evidence."

    if re.search(r"\b(caring|care\s*karega|care\s*karegi)\b", q):
        if occ7 and "Moon" in occ7:
            evidence.append("Caring nature: Moon in 7th — partner emotionally attentive and nurturing in daily life.")
        elif (r.planet("Moon") or {}).get("house") in (4, 5, 7):
            evidence.append("Caring nature: Moon on emotional houses — partner shows care through presence and support.")
        else:
            evidence.append("Caring nature: care builds steadily — partner shows concern through actions over time.")
        summary_extra = "Answer caring directly from Caring nature evidence."

    if re.search(r"\b(humor|humour|funny|mazaak)\b", q):
        merc = r.planet("Mercury") or {}
        jup = r.planet("Jupiter") or {}
        if merc.get("house") in (3, 5, 7) or "Mercury" in occ7:
            evidence.append(
                f"Humour style: Mercury in house {merc.get('house')} sign {merc.get('sign')} — witty talk, teasing humour."
            )
        if jup.get("house") in (5, 7, 9):
            evidence.append(
                f"Humour style: Jupiter in house {jup.get('house')} — warm optimistic humour, lightens mood."
            )
        summary_extra = "Answer humorous directly from Humour style evidence."

    if re.search(r"\b(honest|imandaar|sach\s*bol)\b", q):
        jup = r.planet("Jupiter") or {}
        if jup.get("house") in (1, 7, 9) or "Jupiter" in occ7:
            evidence.append(
                f"Honesty pattern: Jupiter in house {jup.get('house')} — fair principled talk, values truth in relationship."
            )
        elif lord7 == "Mercury" or (p7l and p7l.get("sign") in ("Sagittarius", "Aries")):
            evidence.append("Honesty pattern: direct Mercury/Jupiter tone — partner speaks straight, dislikes long pretence.")
        else:
            evidence.append("Honesty pattern: honesty grows with trust — partner may guard feelings early then opens up.")
        summary_extra = "Answer honest directly from Honesty pattern evidence."

    if re.search(r"\b(practical|emotional)\b", q) and _has_spouse_word(q):
        merc = r.planet("Mercury") or {}
        moon = r.planet("Moon") or {}
        practical = (merc.get("house") in (2, 3, 6, 10) or sign7 in ("Virgo", "Capricorn", "Gemini"))
        emotional = bool(occ7 and "Moon" in occ7) or moon.get("house") in (4, 5, 7)
        if practical and emotional:
            evidence.append(
                "Practical vs emotional: partner mixes practical planning with emotional care — head + heart both active."
            )
            summary_extra = "Answer practical vs emotional: dono mix, thoda practical thoda emotional."
        elif practical:
            evidence.append(
                f"Practical vs emotional: Mercury/sign {sign7 or '?'} tone — partner practical grounded, shows love through actions."
            )
            summary_extra = "Answer: partner practical side zyada."
        else:
            evidence.append(
                "Practical vs emotional: Moon-led partnership tone — partner emotional, feelings drive closeness."
            )
            summary_extra = "Answer: partner emotional side zyada."

    if re.search(r"\b(manipulat|dhokhebaaz|mind\s*game)\b", q):
        rahu = r.planet("Rahu") or {}
        if sig.rahu_on_7th_axis or rahu.get("house") in (7, 8) or "Rahu" in occ7:
            evidence.append(
                f"Manipulation risk: Rahu on partnership axis (house {rahu.get('house')}) — "
                "mind-games or mixed signals possible; clarity and boundaries protect you."
            )
        elif (r.planet("Mercury") or {}).get("house") in (6, 8, 12):
            evidence.append(
                "Manipulation risk: Mercury in dusthana tone — indirect talk at times; ask directly when confused."
            )
        else:
            evidence.append(
                "Manipulation risk: no strong manipulation driver — partner generally straightforward; trust but verify."
            )
        summary_extra = "Answer manipulation directly from Manipulation risk evidence."

    summary = [
        "User asked partner/spouse nature (non-timing).",
        "State traits confidently from evidence — not hedged/shayad tone.",
        f"7H occupants for tone: {occ_label}.",
    ]
    if attachment_q:
        summary.insert(
            0,
            "User asked emotional attachment between user and partner — "
            "open with honest strong/mixed/cautious verdict; use POSITIVE + NEGATIVE evidence.",
        )
    if summary_extra:
        summary.append(summary_extra)

    checks: dict = {
        "slice_type": "mr_engine_v1",
        "archetype": "partner_nature",
        "question_focus": "partnership_attachment" if attachment_q else "partner_personality",
        "gender": gender,
        "karak": karak,
        "sign7": sign7,
    }

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
        evidence=evidence[:12],
        ignore=[
            "timing dates/windows",
            "love-vs-arranged",
            "spouse profession",
            "manglik (unless asked)",
            "breakup risk (unless asked)",
        ],
        checks=checks,
    )

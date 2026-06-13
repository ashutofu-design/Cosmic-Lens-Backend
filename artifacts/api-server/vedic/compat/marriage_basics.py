"""
Deterministic Kundli Milan Basic — marriage chart intelligence (no LLM).

Per partner: D1 7th axis, D9 7th depth, Darakaraka, Upapada, KP 7th CSL,
gender-aware karaka (Venus for male / Jupiter for female), friction + remedy.

Couple: structural marriage band from engine scores only.
"""
from __future__ import annotations

from typing import Any, Literal

from karakas import compute_karakas
from jaimini import compute_arudha_padas, compute_upapada
from vedic.compat.d9_marriage import _per_partner as d9_per_partner
from vedic.compat.kp_marriage_promise import compute_kp_marriage_promise
from vedic.love_reality.relationship_signals import _analyze_person
from vedic.love_reality.scoring_core import (
    BENEFIC,
    DUSTHANA,
    KundliReader,
    MALEFIC,
    SIGN_LORDS,
    SIGNS,
)

Gender = Literal["male", "female", "unknown"]
Band = Literal["Strong", "Moderate", "Strained"]
CoupleBand = Literal["Promising", "Workable", "High Effort"]
KpVerdict = Literal["STRONG", "PARTIAL", "WEAK", "UNAVAILABLE"]

_MALE = frozenset({"m", "male", "man", "boy", "ladka", "son", "husband"})
_FEMALE = frozenset({"f", "female", "woman", "girl", "ladki", "daughter", "wife"})


def normalize_gender(raw: str | None) -> Gender:
    g = str(raw or "").strip().lower()
    if not g:
        return "unknown"
    base = g.split()[0].rstrip(".")
    if base in _MALE or ("male" in base and "female" not in base):
        return "male"
    if base in _FEMALE or "female" in base or "woman" in base or "girl" in base:
        return "female"
    return "unknown"


def _houses_ruled_by(k: KundliReader, planet: str) -> list[int]:
    asc = k.asc_index()
    out: list[int] = []
    for hi, lord in enumerate(SIGN_LORDS):
        if lord == planet:
            out.append(((hi - asc) % 12) + 1)
    return sorted(out)


def _lord_strength_word(dignity: int, house: int | None) -> str:
    score = dignity
    if house in DUSTHANA:
        score -= 2
    elif house in {1, 4, 5, 7, 9, 10, 11}:
        score += 1
    if score >= 2:
        return "strong"
    if score >= 0:
        return "moderate"
    return "weak"


def _band_from_score(score: int) -> Band:
    if score >= 68:
        return "Strong"
    if score >= 48:
        return "Moderate"
    return "Strained"


def _couple_band(score: int) -> CoupleBand:
    if score >= 65:
        return "Promising"
    if score >= 48:
        return "Workable"
    return "High Effort"


def _d9_band(maturity: float) -> str:
    if maturity >= 7:
        return "Supportive"
    if maturity >= 5:
        return "Mixed"
    return "Weak"


def _kp_depth(verdict: str) -> str:
    return {
        "STRONG": "strong",
        "PARTIAL": "partial",
        "WEAK": "weak",
        "UNAVAILABLE": "unavailable",
    }.get(verdict, "unavailable")


def _lordship_note(lord: str, houses: list[int]) -> str:
    if not houses:
        return f"{lord} lordship data unavailable."
    htxt = ", ".join(str(h) for h in houses)
    marriage_h = 7 in houses
    if marriage_h and len(houses) == 1:
        return f"{lord} rules only the 7th — marriage themes dominate this planet's expression."
    if marriage_h:
        return f"{lord} rules houses {htxt} — partnership links with other life areas (not isolated)."
    return f"{lord} rules houses {htxt} — marriage flows through those house themes."


def _karaka_planet(gender: Gender) -> str:
    if gender == "female":
        return "Jupiter"
    if gender == "male":
        return "Venus"
    return "Venus"


def _friction_and_remedy(
    k: KundliReader,
    gender: Gender,
    sig_notes: list[str],
    kp: dict[str, Any],
    ul: dict[str, Any],
) -> tuple[str, str, list[str], list[str]]:
    pressures: list[str] = []
    strengths: list[str] = []

    h7l = k.house_lord(7)
    p7l = k.planet(h7l)
    h7_occ = k.occupants(7)
    malefics = [p for p in h7_occ if p in MALEFIC]
    benefics = [p for p in h7_occ if p in BENEFIC]

    if benefics:
        strengths.append(f"Benefics in 7th ({', '.join(benefics)}) support partnership warmth.")
    if malefics:
        pressures.append(f"Malefic pressure in 7th ({', '.join(malefics)}) — conflict or delay themes.")
    if p7l and p7l.get("house") in DUSTHANA:
        pressures.append(f"7th lord {h7l} in dusthana house {p7l.get('house')} — bond needs structural patience.")
    elif p7l and p7l.get("house") in {1, 4, 5, 7, 10, 11}:
        strengths.append(f"7th lord {h7l} in supportive house {p7l.get('house')}.")

    if k.manglik():
        pressures.append("Mars manglik pattern — heated arguments unless consciously cooled.")

    if gender == "female":
        jup = k.planet("Jupiter")
        if jup:
            jd = k.dignity("Jupiter", k.sidx(jup["sign"]))
            if jd >= 1:
                strengths.append("Jupiter (husband karaka) well placed — pati-significator supportive.")
            elif jd <= -2:
                pressures.append("Jupiter debilitated — husband-significator needs remedy support.")
    elif gender == "male":
        ven = k.planet("Venus")
        if ven:
            vd = k.dignity("Venus", k.sidx(ven["sign"]))
            if vd >= 1:
                strengths.append("Venus (wife karaka) well placed — spouse-significator supportive.")
            elif vd <= -2:
                pressures.append("Venus debilitated — wife-significator needs conscious nurture.")

    kv = kp.get("verdict")
    if kv == "WEAK":
        pressures.append("KP 7th cusp chain weak — commitment may need time to solidify.")
    elif kv == "STRONG":
        strengths.append("KP 7th cusp supports marriage promise on structural level.")

    ul_v = str(ul.get("verdict") or "")
    if "STRAINED" in ul_v.upper():
        pressures.append("Upapada shows strain — marriage manifestation needs realistic pacing.")
    elif "STABLE" in ul_v.upper():
        strengths.append("Upapada supports stable marriage manifestation.")

    for n in sig_notes[:3]:
        if any(w in n.lower() for w in ("weak", "debilitated", "dusthana", "distance", "fight", "confusion")):
            pressures.append(n)
        elif any(w in n.lower() for w in ("strong", "supportive", "harmony", "aligned", "loyalty")):
            strengths.append(n)

    friction = pressures[0] if pressures else "No major structural friction flagged — still nurture communication daily."
    remedy = _pick_remedy(k, gender, pressures)
    return friction, remedy, strengths[:4], pressures[:5]


def _pick_remedy(k: KundliReader, gender: Gender, pressures: list[str]) -> str:
    blob = " ".join(pressures).lower()
    if "saturn" in blob or "distance" in blob or "delay" in blob:
        return "Saturday discipline: sesame-oil lamp, patience rituals, no ultimatums on Saturdays."
    if "mars" in blob or "manglik" in blob or "fight" in blob:
        return "Tuesday Hanuman Chalisa; cool-down rule before replying in anger."
    if "rahu" in blob or "ketu" in blob or "confusion" in blob:
        return "Thursday Vishnu quiet time; reduce impulsive relationship decisions."
    if "venus" in blob and gender == "male":
        return "Friday white sweets + Venus mantra; express appreciation without score-keeping."
    if "jupiter" in blob and gender == "female":
        return "Thursday yellow charity; honour wisdom and elders in partner choices."
    if "debilitated" in blob or "dusthana" in blob:
        return "Strengthen 7th lord day (planet weekday) with simple daan + consistent boundaries."
    h7l = k.house_lord(7)
    weekday = {
        "Sun": "Sunday", "Moon": "Monday", "Mars": "Tuesday", "Mercury": "Wednesday",
        "Jupiter": "Thursday", "Venus": "Friday", "Saturn": "Saturday",
    }.get(h7l, "Friday")
    return f"{weekday} light for 7th lord {h7l}; joint ritual with partner weekly."


def _analyze_partner(kundli: dict, *, name: str, gender: Gender) -> dict[str, Any]:
    k = KundliReader({**kundli, "name": name})
    asc = k.asc_index()
    h7_sign = SIGNS[(asc + 6) % 12]
    h7l = k.house_lord(7)
    p7l = k.planet(h7l)
    h7_occ = k.occupants(7)
    asp7 = k.aspects_house(7)
    benefics = [p for p in h7_occ if p in BENEFIC]
    malefics = [p for p in h7_occ if p in MALEFIC]
    lord_houses = _houses_ruled_by(k, h7l)

    dignity = 0
    lord_sign = None
    lord_house = None
    if p7l:
        lord_sign = p7l.get("sign")
        lord_house = p7l.get("house")
        dignity = k.dignity(h7l, k.sidx(lord_sign or "Aries"))

    d9 = d9_per_partner(kundli)
    kp = compute_kp_marriage_promise(kundli)
    sig = _analyze_person(k)

    karakas = compute_karakas(kundli.get("planets") or [])
    dk_planet = karakas.get("DK")
    dk_block: dict[str, Any] = {"planet": dk_planet, "sign": None, "house": None, "note": "Darakaraka unavailable."}
    if dk_planet:
        dk_p = k.planet(dk_planet)
        if dk_p:
            dk_block = {
                "planet": dk_planet,
                "sign": dk_p.get("sign"),
                "house": dk_p.get("house"),
                "dignity": k.dignity_word(k.dignity(dk_planet, k.sidx(dk_p.get("sign") or "Aries"))),
                "note": f"Darakaraka {dk_planet} in {dk_p.get('sign')} house {dk_p.get('house')} — spouse nature signature.",
            }

    arudha = compute_arudha_padas(kundli.get("planets") or [], kundli.get("ascendant"))
    ul = compute_upapada(arudha, kundli.get("planets") or []) if arudha else {}
    ul_stability = "neutral"
    if ul:
        vs = str(ul.get("verdict") or "")
        if "STABLE" in vs.upper():
            ul_stability = "stable"
        elif "STRAINED" in vs.upper():
            ul_stability = "strained"
        elif "MIXED" in vs.upper():
            ul_stability = "mixed"

    karaka_name = _karaka_planet(gender)
    karaka_p = k.planet(karaka_name)
    karaka_block: dict[str, Any] = {
        "primary": karaka_name,
        "role": "wife karaka" if gender == "male" else "husband karaka" if gender == "female" else "relationship karaka",
        "sign": None,
        "house": None,
        "dignity": "unknown",
        "strength": "unknown",
        "note": f"{karaka_name} data unavailable.",
    }
    if karaka_p:
        kd = k.dignity(karaka_name, k.sidx(karaka_p.get("sign") or "Aries"))
        karaka_block.update({
            "sign": karaka_p.get("sign"),
            "house": karaka_p.get("house"),
            "dignity": k.dignity_word(kd),
            "strength": _lord_strength_word(kd, karaka_p.get("house")),
            "note": f"{karaka_name} ({karaka_block['role']}) in {karaka_p.get('sign')} house {karaka_p.get('house')}.",
        })

    score = 52
    if benefics:
        score += 6 * len(benefics)
    if malefics:
        score -= 9 * len(malefics)
    for a in asp7:
        if a in MALEFIC:
            score -= 5
        elif a in BENEFIC:
            score += 3

    score += {2: 12, 1: 7, 0: 0, -2: -14}.get(dignity, 0)
    if lord_house in DUSTHANA:
        score -= 10
    elif lord_house in {1, 4, 5, 7, 9, 10, 11}:
        score += 6

    if d9.get("available"):
        score += int(round((float(d9.get("marriage_maturity_0_10") or 5) - 5) * 3))

    kv = kp.get("verdict")
    if kv == "STRONG":
        score += 10
    elif kv == "PARTIAL":
        score += 4
    elif kv == "WEAK":
        score -= 8

    if ul_stability == "stable":
        score += 6
    elif ul_stability == "strained":
        score -= 8

    if karaka_p:
        kd = k.dignity(karaka_name, k.sidx(karaka_p.get("sign") or "Aries"))
        if kd >= 1:
            score += 8
        elif kd <= -2:
            score -= 10

    score -= min(20, sig.affliction_weight // 2)
    score = max(0, min(100, score))

    friction, remedy, strengths, pressures = _friction_and_remedy(k, gender, sig.notes, kp, ul)

    gender_flags: list[str] = []
    if k.manglik():
        gender_flags.append("Manglik Mars pattern active")
    if gender == "female" and karaka_p and k.dignity("Jupiter", k.sidx(karaka_p.get("sign") or "Aries")) <= -2:
        gender_flags.append("Jupiter husband-karaka under pressure")
    if gender == "male" and karaka_p and k.dignity("Venus", k.sidx(karaka_p.get("sign") or "Aries")) <= -2:
        gender_flags.append("Venus wife-karaka under pressure")
    if sig.seventh_lord_dusthana:
        gender_flags.append("7th lord in dusthana")
    if sig.saturn_on_7th:
        gender_flags.append("Saturn on 7th axis")

    return {
        "name": name,
        "gender": gender,
        "readiness_score": score,
        "readiness_band": _band_from_score(score),
        "d1": {
            "seventh_house_sign": h7_sign,
            "planets_in_seventh": h7_occ,
            "benefics_in_seventh": benefics,
            "malefics_in_seventh": malefics,
            "aspects_on_seventh": asp7,
            "seventh_lord": h7l,
            "seventh_lord_house": lord_house,
            "seventh_lord_sign": lord_sign,
            "seventh_lord_dignity": k.dignity_word(dignity),
            "seventh_lord_strength": _lord_strength_word(dignity, lord_house),
            "lordship_houses": lord_houses,
            "lordship_note": _lordship_note(h7l, lord_houses),
        },
        "d9": {
            "available": bool(d9.get("available")),
            "seventh_house_sign": d9.get("d9_7h_sign"),
            "seventh_lord": d9.get("d9_7h_lord"),
            "seventh_lord_sign": d9.get("d9_7l_sign"),
            "seventh_lord_house": d9.get("d9_7l_house"),
            "maturity_0_10": d9.get("marriage_maturity_0_10"),
            "band": _d9_band(float(d9.get("marriage_maturity_0_10") or 5)),
            "venus_dignity": d9.get("d9_venus_dignity"),
            "jupiter_dignity": d9.get("d9_jupiter_dignity"),
        },
        "darakaraka": dk_block,
        "upapada": {
            "available": bool(ul),
            "ul_sign": ul.get("ul_sign"),
            "ul_lord": ul.get("ul_lord"),
            "ul_lord_house_from_ul": ul.get("ul_lord_house"),
            "stability": ul_stability,
            "verdict": ul.get("verdict"),
            "occupants_ul": ul.get("occupants_ul") or [],
        },
        "kp": {
            "available": bool(kp.get("available")),
            "verdict": kp.get("verdict"),
            "commitment_depth": _kp_depth(str(kp.get("verdict") or "UNAVAILABLE")),
            "seven_csl": kp.get("seven_csl"),
            "signified_houses": kp.get("signified_houses") or [],
            "promise_hits": kp.get("promise_hits", 0),
            "negation_hits": kp.get("negation_hits", 0),
        },
        "karaka": karaka_block,
        "gender_flags": gender_flags,
        "friction": friction,
        "remedy": remedy,
        "strengths": strengths,
        "pressures": pressures,
    }


def _couple_verdict(band: CoupleBand, p1: dict, p2: dict) -> str:
    if band == "Promising":
        return (
            "Both marriage axes show supportive structure — if these two marry, "
            "long-term direction can grow well with steady effort."
        )
    if band == "Workable":
        return (
            "Marriage is workable but not effortless — strengths exist on both sides; "
            "friction points need conscious handling after wedding."
        )
    return (
        "High effort match — marriage is possible but demands patience, remedies, "
        "and realistic expectations on both charts."
    )


def compute_marriage_basics(
    kundli_p1: dict,
    kundli_p2: dict,
    *,
    p1_name: str = "Partner A",
    p2_name: str = "Partner B",
    p1_gender: str | None = None,
    p2_gender: str | None = None,
) -> dict[str, Any]:
    """Full deterministic Basic marriage payload for a couple."""
    g1 = normalize_gender(p1_gender)
    g2 = normalize_gender(p2_gender)
    person1 = _analyze_partner(kundli_p1, name=p1_name, gender=g1)
    person2 = _analyze_partner(kundli_p2, name=p2_name, gender=g2)

    d9_1 = float(person1["d9"].get("maturity_0_10") or 5)
    d9_2 = float(person2["d9"].get("maturity_0_10") or 5)
    d9_sync_bonus = int(round((min(d9_1, d9_2) - 5) * 2))

    kp_bonus = 0
    for p in (person1, person2):
        v = p["kp"].get("verdict")
        if v == "STRONG":
            kp_bonus += 4
        elif v == "PARTIAL":
            kp_bonus += 2
        elif v == "WEAK":
            kp_bonus -= 3

    structural = int(round((person1["readiness_score"] + person2["readiness_score"]) / 2))
    structural = max(0, min(100, structural + d9_sync_bonus + kp_bonus))
    couple_band = _couple_band(structural)

    return {
        "engine": "marriage_basics_v1",
        "couple": {
            "structural_score": structural,
            "structural_band": couple_band,
            "future_verdict": _couple_verdict(couple_band, person1, person2),
            "d9_sync_note": (
                f"D9 depth sync: partner A {d9_1}/10 · partner B {d9_2}/10"
            ),
        },
        "p1": person1,
        "p2": person2,
    }

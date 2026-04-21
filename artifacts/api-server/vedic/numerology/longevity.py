"""Tier 16 — Health, Longevity & 8th House (Ayur Bhava) Deep Audit.

Ayur Bhava (8th house) governs longevity (ayurdaya), chronic illness,
sudden events, surgery, accidents, transformation, occult/research, and
inheritance. This engine produces 7 chart-locked blocks: Ayur Bhava
strength, Health Karakas (Sun=vitality, Moon=mind/fluids, Mars=blood/
surgery, Saturn=chronic/bones, Rahu=mystery-illness, Ketu=
diagnostic-blindspot), Ayurdaya tier (Alpa/Madhya/Purna via Pinda
heuristic), Maraka audit (2L+7L houses + Saturn placement), Sudden-
Event timing window (current dasha vs 8L/Saturn/Mars/Rahu activators),
Roga signatures (chronic-disease karmic flags), and Synthesis with
longevity-tier + body-system focus + remedy plan.

Hard data gate: ascendant + 9 grahas. Dasha is soft-gated.
Note: This engine produces karmic insight, NOT medical advice. All
prose layers downstream MUST include "consult a qualified physician"
disclaimer language.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}
EXALT = {"Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
         "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
         "Saturn": "Libra"}
DEBIL = {"Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
         "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo",
         "Saturn": "Aries"}
OWN = {"Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
       "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
       "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"]}
KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}
DUSTHANA = {6, 8, 12}
MARAKA_HOUSES = {2, 7}  # classical maraka sthanas

# 8th-sign body-system focus (BPHS / Sarvartha Chintamani lineage)
EIGHTH_SIGN_BODY: Dict[str, str] = {
    "Aries": "head/brain — migraines, head injuries, hot-blood disorders, accidents involving head; cool-pitta diet.",
    "Taurus": "throat/neck/thyroid — voice issues, thyroid imbalance, neck stiffness; protect throat in winter.",
    "Gemini": "lungs/shoulders/nerves — respiratory issues, anxiety, nervous-exhaustion; pranayama essential.",
    "Cancer": "chest/stomach/lymph — emotional-eating, gastric issues, breast/chest care; soft-diet + stress-detox.",
    "Leo": "heart/spine — cardiac strain under ego-pressure, spine alignment; daily walking + bhastrika.",
    "Virgo": "intestines/digestion — IBS, food-allergies, OCD-anxiety somatised in gut; probiotics + meditation.",
    "Libra": "kidneys/lower-back/skin — relationship-stress hits kidneys, lower-back pain; hydration + balance.",
    "Scorpio": "reproductive/excretory — hormonal/sexual-health, hidden chronic conditions; periodic check-ups.",
    "Sagittarius": "hips/thighs/liver — liver-detox, hip mobility, weight on thighs; turmeric + walking.",
    "Capricorn": "knees/joints/skeletal — arthritis early, calcium absorption, joint stiffness; vitamin-D + yoga.",
    "Aquarius": "ankles/circulation/nervous — circulation issues, ankle injuries, nervous-system strain; warmth.",
    "Pisces": "feet/lymph/immune — water-retention, foot/lymph issues, immune-fluctuation; warm-oil massage.",
}

# Body-system focus by 8L sign (chronic predisposition)
EIGHTH_LORD_SIGN_BODY: Dict[str, str] = {
    "Aries": "fire-element overflow — inflammation, ulcers, headaches; cooling herbs (amla, coriander).",
    "Taurus": "earth-stagnation — weight gain, thyroid sluggishness; brisk walking, kapha-pacifying diet.",
    "Gemini": "air-imbalance — anxiety, dry skin, nervous restlessness; abhyanga + pranayama.",
    "Cancer": "water-emotional — fluid retention, breast/stomach concerns; emotional release work.",
    "Leo": "fire-cardiac — heart strain, blood pressure under stress; ego-management + cardio.",
    "Virgo": "earth-detail-anxiety — IBS, food sensitivities; gentle digestive routine.",
    "Libra": "air-relational — kidney/skin under partnership stress; harmony + hydration.",
    "Scorpio": "water-hidden — reproductive/hormonal mysteries; specialist screening.",
    "Sagittarius": "fire-liver — liver heat, hip strain from weight; detox + mobility.",
    "Capricorn": "earth-skeletal — joint/bone density, slow metabolism; vitamin-D + resistance.",
    "Aquarius": "air-circulatory — nerve/circulation oddities; warmth + circulation work.",
    "Pisces": "water-immune — immune fluctuation, foot/lymph; rest + warm-oil care.",
}

SYNTHESIS_TOKENS = {
    "blessed": "BLESSED-LONGEVITY-PATH",
    "moderate": "MODERATE-VITAL-PATH",
    "karmic": "KARMIC-HEALTH-PATH",
    "transformation": "TRANSFORMATION-FOCUSED",
}

AYURDAYA_TIERS = {
    "purna": ("PURNA-AYU tier (HIGHER vitality-resilience signature, classical full-tier per "
              "BPHS Pinda heuristic) — karmic indicator only, NOT a lifespan prediction."),
    "madhya": ("MADHYA-AYU tier (MEDIUM vitality-resilience signature, normal-tier with extra "
               "care in maraka periods) — karmic indicator only, NOT a lifespan prediction."),
    "alpa": ("ALPA-AYU tier (LOWER vitality-resilience signature; intensive lifestyle + "
             "preventive care + remedies recommended) — karmic indicator only, NOT a lifespan "
             "prediction. Always consult a qualified physician."),
}


# ── helpers ─────────────────────────────────────────────────────
def _planet(planets: List[Dict], name: str) -> Optional[Dict]:
    for p in planets:
        if isinstance(p, dict) and p.get("name") == name:
            return p
    return None


def _planet_lon(planets: List[Dict], name: str) -> Optional[float]:
    p = _planet(planets, name)
    if p and isinstance(p.get("longitude"), (int, float)):
        return float(p["longitude"]) % 360.0
    return None


def _planet_sign(planets: List[Dict], name: str) -> Optional[str]:
    p = _planet(planets, name)
    if not p:
        return None
    s = p.get("sign")
    if s in SIGNS:
        return s
    lon = _planet_lon(planets, name)
    return SIGNS[int(lon // 30)] if lon is not None else None


def _planet_house(planets: List[Dict], asc_sign: str) -> Dict[str, int]:
    if asc_sign not in SIGNS:
        return {}
    asc_idx = SIGNS.index(asc_sign)
    out: Dict[str, int] = {}
    for p in planets:
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        if p.get("house") and isinstance(p["house"], int):
            out[nm] = p["house"]
            continue
        sgn = _planet_sign(planets, nm) if nm else None
        if sgn:
            out[nm] = ((SIGNS.index(sgn) - asc_idx) % 12) + 1
    return out


def _occupants(planets: List[Dict], asc_sign: str, house_num: int) -> List[str]:
    h = _planet_house(planets, asc_sign)
    return sorted([nm for nm, hn in h.items() if hn == house_num])


def _dignity(planet: str, sign: Optional[str]) -> str:
    if not sign or planet not in EXALT:
        return "neutral"
    if sign == EXALT.get(planet):
        return "exalted"
    if sign == DEBIL.get(planet):
        return "debilitated"
    if sign in OWN.get(planet, []):
        return "own-sign"
    return "neutral"


def _has_aspect(planets: List[Dict], asc_sign: str, src: str, target_house: int) -> bool:
    src_house = _planet_house(planets, asc_sign).get(src, 0)
    if not src_house:
        return False
    diff = ((target_house - src_house) % 12) + 1
    aspects = {7}
    if src == "Mars":
        aspects |= {4, 8}
    elif src == "Jupiter":
        aspects |= {5, 9}
    elif src == "Saturn":
        aspects |= {3, 10}
    elif src in ("Rahu", "Ketu"):
        aspects |= {5, 9}
    return diff in aspects


# ── Maraka audit ────────────────────────────────────────────────
def _maraka_audit(planets: List[Dict], asc_sign: str) -> Dict[str, Any]:
    """2L and 7L are classical maraka (death-inflicting) lords. This audit
    flags their placements + Saturn (universal time-lord) for awareness of
    health-vulnerable dasha periods. NOT a death-prediction; a karmic-care map.
    """
    asc_idx = SIGNS.index(asc_sign)
    second_lord = SIGN_LORD[SIGNS[(asc_idx + 1) % 12]]
    seventh_lord = SIGN_LORD[SIGNS[(asc_idx + 6) % 12]]
    p_house = _planet_house(planets, asc_sign)
    sec_h = p_house.get(second_lord, 0)
    sev_h = p_house.get(seventh_lord, 0)
    sat_h = p_house.get("Saturn", 0)

    flags: List[str] = []
    severity_score = 0

    if sec_h in DUSTHANA:
        flags.append(f"2L {second_lord} in H{sec_h} (Dusthana) — maraka karma activated; "
                     f"family-asset / nourishment dasha needs extra health-care.")
        severity_score += 15
    if sev_h in DUSTHANA:
        flags.append(f"7L {seventh_lord} in H{sev_h} (Dusthana) — partnership-related "
                     f"stress impacts vitality; relational-shanti recommended.")
        severity_score += 15
    if sat_h in (6, 8, 12):
        flags.append(f"Saturn in H{sat_h} — slow karmic-time-lord influence; chronic patterns "
                     f"unfold during Shani dasha/antardasha; preventive care wins.")
        severity_score += 10
    if second_lord == seventh_lord:
        flags.append(f"2L = 7L = {second_lord} — single maraka concentration; one karmic "
                     f"period carries dual maraka load; attentive lifestyle in its dasha.")
        severity_score += 10

    return {
        "second_lord": second_lord,
        "seventh_lord": seventh_lord,
        "second_lord_house": sec_h,
        "seventh_lord_house": sev_h,
        "saturn_house": sat_h,
        "maraka_flags": flags[:6],
        "severity_score": min(100, severity_score),
        "note": ("Maraka houses (2 + 7) are KARMIC time-keepers per BPHS; this audit informs "
                 "health-vigilance windows, NOT death prediction. Always consult a physician."),
    }


# ── Ayurdaya Pinda (longevity tier heuristic) ───────────────────
def _ayurdaya_tier(planets: List[Dict], asc_sign: str,
                    eighth_lord: str) -> Dict[str, Any]:
    """BPHS-style Pinda Ayurdaya is exhaustive (sphuta-based). This is a
    PROXY heuristic that combines: 8L strength, Saturn dignity, Lagna
    strength, malefics in Lagna/8th, Jupiter-on-Lagna/8th aspect, and
    moon-Sun strength. Result: ALPA / MADHYA / PURNA tier indicator only.
    """
    p_house = _planet_house(planets, asc_sign)
    score = 50

    # 8L strength
    el_house = p_house.get(eighth_lord, 0)
    el_sign = _planet_sign(planets, eighth_lord)
    el_dignity = _dignity(eighth_lord, el_sign)
    if el_dignity == "exalted":
        score += 12
    elif el_dignity == "own-sign":
        score += 8
    elif el_dignity == "debilitated":
        score -= 12
    if el_house in KENDRA | TRIKONA:
        score += 5
    elif el_house == 8:
        score += 8  # 8L in own 8th = stable longevity
    elif el_house in DUSTHANA:
        score -= 5

    # Saturn (time-lord) strength → general longevity
    sat_sign = _planet_sign(planets, "Saturn")
    sat_dignity = _dignity("Saturn", sat_sign)
    sat_house = p_house.get("Saturn", 0)
    if sat_dignity in ("exalted", "own-sign"):
        score += 10
    elif sat_dignity == "debilitated":
        score -= 10
    if sat_house in KENDRA:
        score += 5

    # Lagna strength: lord placement + occupants
    lagna_lord = SIGN_LORD[asc_sign]
    ll_house = p_house.get(lagna_lord, 0)
    ll_sign = _planet_sign(planets, lagna_lord)
    ll_dignity = _dignity(lagna_lord, ll_sign)
    if ll_dignity in ("exalted", "own-sign"):
        score += 10
    elif ll_dignity == "debilitated":
        score -= 10
    if ll_house in KENDRA | TRIKONA:
        score += 5
    elif ll_house in DUSTHANA:
        score -= 8

    # Malefics in Lagna or 8th (vitality-drain)
    lagna_occ = _occupants(planets, asc_sign, 1)
    eighth_occ = _occupants(planets, asc_sign, 8)
    malefics = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
    lagna_malefics = [m for m in lagna_occ if m in malefics]
    eighth_malefics = [m for m in eighth_occ if m in malefics]
    score -= len(lagna_malefics) * 5
    score -= len(eighth_malefics) * 4

    # Jupiter aspect on Lagna or 8th = blessing
    if _has_aspect(planets, asc_sign, "Jupiter", 1):
        score += 8
    if _has_aspect(planets, asc_sign, "Jupiter", 8):
        score += 6

    # Moon in good shape = vitality
    moon_sign = _planet_sign(planets, "Moon")
    moon_dignity = _dignity("Moon", moon_sign)
    if moon_dignity == "exalted":
        score += 6
    elif moon_dignity == "debilitated":
        score -= 8

    score = max(0, min(100, score))

    if score >= 65:
        tier_key = "purna"
    elif score >= 40:
        tier_key = "madhya"
    else:
        tier_key = "alpa"

    return {
        "score": score,
        "tier_key": tier_key,
        "tier_label": AYURDAYA_TIERS[tier_key],
        "eighth_lord_dignity": el_dignity,
        "eighth_lord_house": el_house,
        "saturn_dignity": sat_dignity,
        "lagna_lord": lagna_lord,
        "lagna_lord_dignity": ll_dignity,
        "lagna_malefic_count": len(lagna_malefics),
        "eighth_malefic_count": len(eighth_malefics),
        "jupiter_lagna_aspect": _has_aspect(planets, asc_sign, "Jupiter", 1),
        "jupiter_eighth_aspect": _has_aspect(planets, asc_sign, "Jupiter", 8),
        "method_note": ("Heuristic Pinda-Ayurdaya proxy combining 8L + Lagna + Saturn + "
                        "Jupiter-aspect + Moon strength. NOT a precise lifespan calculation; "
                        "use as karmic-vitality indicator. Consult physicians for medical care."),
    }


# ── Sudden-Event Timing ─────────────────────────────────────────
def _sudden_event_timing(kundli: Dict, planets: List[Dict], asc_sign: str,
                          eighth_lord: str) -> Dict[str, Any]:
    """Current MD/AD vs 8L + Mars + Saturn + Rahu (sudden-event activators).
    Used to flag windows where extra preventive health-care + driving-care +
    surgery-postponement (if elective) is wise.
    """
    dasha = kundli.get("dasha") or kundli.get("currentDasha") or {}
    md_lord = (dasha.get("mahaDasha") or dasha.get("md") or {}).get("planet") \
              if isinstance(dasha, dict) else None
    ad_lord = (dasha.get("antarDasha") or dasha.get("ad") or {}).get("planet") \
              if isinstance(dasha, dict) else None
    if not md_lord:
        md_lord = dasha.get("mahadasha_lord") if isinstance(dasha, dict) else None
        ad_lord = dasha.get("antardasha_lord") if isinstance(dasha, dict) else None

    activators = {eighth_lord, "Mars", "Saturn", "Rahu", "Ketu"}
    occ_8 = _occupants(planets, asc_sign, 8)
    for p in occ_8:
        activators.add(p)
    activators.discard("—")

    md_active = md_lord in activators if md_lord else False
    ad_active = ad_lord in activators if ad_lord else False

    if md_active and ad_active:
        window_status = "HIGH-VIGILANCE WINDOW"
        window_note = (f"Both MD ({md_lord}) and AD ({ad_lord}) activate the 8th-house karmic "
                       f"axis — heightened vigilance recommended on health, driving, surgery-"
                       f"timing; postpone elective surgeries if chart-locked alternative exists.")
    elif md_active:
        window_status = "ELEVATED-CARE WINDOW"
        window_note = (f"MD lord {md_lord} is an 8th-house activator — chronic patterns may "
                       f"surface; preventive screening + lifestyle discipline yields outsized "
                       f"benefit; watch for AD/PD of Mars/Saturn for acute sub-windows.")
    elif ad_active:
        window_status = "TACTICAL-CARE WINDOW"
        window_note = (f"AD lord {ad_lord} is an 8th-house activator inside non-aligned MD "
                       f"({md_lord or 'unknown'}) — short-term sub-window for extra care; "
                       f"avoid risky travel/surgery in this antardasha if possible.")
    else:
        window_status = "STABLE WINDOW"
        window_note = (f"Neither MD ({md_lord or 'unknown'}) nor AD ({ad_lord or 'unknown'}) "
                       f"is an 8th-house activator — stable health window; use this period to "
                       f"build vitality-reserves through yoga, diet, and preventive screening.")

    return {
        "current_md": md_lord or "—",
        "current_ad": ad_lord or "—",
        "activators": sorted(activators),
        "eighth_lord": eighth_lord,
        "md_is_activator": md_active,
        "ad_is_activator": ad_active,
        "window_status": window_status,
        "window_note": window_note,
    }


# ── Roga / Karmic Health Signatures ─────────────────────────────
def _roga_signatures(planets: List[Dict], asc_sign: str,
                      eighth_lord: str) -> Dict[str, Any]:
    p_house = _planet_house(planets, asc_sign)
    sixth_occ = _occupants(planets, asc_sign, 6)
    eighth_occ = _occupants(planets, asc_sign, 8)
    twelfth_occ = _occupants(planets, asc_sign, 12)

    flags: List[str] = []
    score = 0

    if "Saturn" in eighth_occ:
        flags.append("Roga-Shani signature — Saturn in 8th: chronic conditions surface slowly, "
                     "joint/skeletal/longevity work; daily yoga + Shani-shanti recommended.")
        score += 12
    if "Mars" in eighth_occ:
        flags.append("Roga-Mangal signature — Mars in 8th: surgery / accident / blood-related "
                     "events possible in Mangal-dasha; Hanuman Chalisa + driving-vigilance.")
        score += 10
    if "Rahu" in eighth_occ:
        flags.append("Roga-Rahu signature — Rahu in 8th: hidden / mystery-illness karma; "
                     "may need multiple specialist opinions; Rahu shanti + clean diet.")
        score += 10
    if "Ketu" in eighth_occ:
        flags.append("Roga-Ketu signature — Ketu in 8th: diagnostic-blindspot karma; subtle "
                     "symptoms may be missed early; periodic full-body screening helps.")
        score += 8
    if "Sun" in eighth_occ:
        flags.append("Roga-Surya signature — Sun in 8th: cardiac/spine/bone karma; ego-stress "
                     "translates to health; Aditya Hridaya stotram + cardio routine.")
        score += 6
    if "Saturn" in sixth_occ and "Mars" in sixth_occ:
        flags.append("Sat+Mars in 6th — strong roga-resilience BUT prone to inflammation "
                     "+ chronic-acute alternation; balance heating/cooling foods.")
        score += 5
    if p_house.get(eighth_lord) in DUSTHANA and p_house.get(eighth_lord) != 8:
        flags.append(f"8L {eighth_lord} in another Dusthana — chronic-karma layered across "
                     f"multiple body systems; integrative approach (medicine + yoga + diet).")
        score += 8

    moon_dignity = _dignity("Moon", _planet_sign(planets, "Moon"))
    if moon_dignity == "debilitated":
        flags.append("Debilitated Moon — emotional/mental health needs ongoing care; therapy, "
                     "Sri Suktam, water-charged-with-silver, regular sleep rhythm essential.")
        score += 8

    if score >= 30:
        karmic_verdict = "STRONG-ROGA-KARMA"
    elif score >= 15:
        karmic_verdict = "MODERATE-KARMIC"
    else:
        karmic_verdict = "LIGHT-KARMIC"

    # Transformation-axis: heavy 8th occupancy + Scorpio/Pisces signatures
    transformation_focus = (len(eighth_occ) >= 2
                             or _planet_sign(planets, "Ketu") == "Scorpio"
                             or _planet_sign(planets, "Saturn") in ("Scorpio",))

    return {
        "sixth_occupants": sixth_occ,
        "eighth_occupants": eighth_occ,
        "twelfth_occupants": twelfth_occ,
        "saturn_in_8th": "Saturn" in eighth_occ,
        "mars_in_8th": "Mars" in eighth_occ,
        "rahu_in_8th": "Rahu" in eighth_occ,
        "transformation_focus": transformation_focus,
        "karmic_score": min(100, score),
        "karmic_verdict": karmic_verdict,
        "flags": flags[:7],
    }


# ── main ────────────────────────────────────────────────────────
def compute_longevity_bundle(kundli: Dict[str, Any], dob: str,
                              driver: int, conductor: int) -> Dict[str, Any]:
    """T16 Longevity/Ayur bundle. Hard data gate; never fabricates.
    Asc + 9 grahas required. Dasha is soft-gated.

    NOTE: This is karmic insight, NOT medical advice. All downstream prose
    layers MUST include physician-consultation disclaimer language.
    """
    out: Dict[str, Any] = {"available": False}
    if not isinstance(kundli, dict):
        out["reason"] = "no kundli"
        return out
    asc = kundli.get("ascendant")
    planets = kundli.get("planets", []) or []
    if not asc or asc not in SIGNS:
        out["reason"] = f"ascendant missing ({asc!r})"
        return out
    if not isinstance(planets, list) or len(planets) < 9:
        out["reason"] = "planets list incomplete"
        return out
    required = {"Sun", "Moon", "Jupiter", "Mars", "Venus", "Mercury", "Saturn", "Rahu", "Ketu"}
    pn = {p.get("name") for p in planets if isinstance(p, dict)}
    missing = required - pn
    if missing:
        out["reason"] = f"missing grahas: {sorted(missing)}"
        return out

    asc_idx = SIGNS.index(asc)
    p_house = _planet_house(planets, asc)

    # ── 1. Ayur Bhava (8th house) ──────────────────────────────
    eighth_sign = SIGNS[(asc_idx + 7) % 12]
    eighth_lord = SIGN_LORD[eighth_sign]
    el_house = p_house.get(eighth_lord, 0)
    el_sign = _planet_sign(planets, eighth_lord) or "—"
    el_dignity = _dignity(eighth_lord, el_sign)
    eighth_occupants = _occupants(planets, asc, 8)

    el_strength = 50
    if el_house in KENDRA | TRIKONA:
        el_strength += 18
    elif el_house == 8:
        el_strength += 12  # 8L in own 8th = stable longevity karma
    elif el_house in DUSTHANA:
        el_strength -= 12
    if el_dignity == "exalted":
        el_strength += 25
    elif el_dignity == "own-sign":
        el_strength += 15
    elif el_dignity == "debilitated":
        el_strength -= 25
    el_strength = max(0, min(100, el_strength))

    if el_strength >= 70:
        el_verdict = "STRONG Ayur-foundation — vitality-reserve well-supported"
    elif el_strength >= 40:
        el_verdict = "MODERATE Ayur-foundation — workable with disciplined health-care"
    else:
        el_verdict = "FRAGILE Ayur-foundation — sustained remedies + lifestyle vital"

    ayur_bhava = {
        "eighth_sign": eighth_sign,
        "eighth_lord": eighth_lord,
        "lord_house": el_house,
        "lord_sign": el_sign,
        "lord_dignity": el_dignity,
        "occupants": eighth_occupants,
        "strength_score": el_strength,
        "verdict": el_verdict,
        "body_focus_by_sign": EIGHTH_SIGN_BODY.get(eighth_sign, "—"),
        "body_focus_by_lord_sign": EIGHTH_LORD_SIGN_BODY.get(el_sign, "—"),
    }

    # ── 2. Health Karakas ──────────────────────────────────────
    sun_sign = _planet_sign(planets, "Sun") or "—"
    sun_house = p_house.get("Sun", 0)
    sun_dignity = _dignity("Sun", sun_sign)
    moon_sign = _planet_sign(planets, "Moon") or "—"
    moon_house = p_house.get("Moon", 0)
    moon_dignity = _dignity("Moon", moon_sign)
    mars_sign = _planet_sign(planets, "Mars") or "—"
    mars_house = p_house.get("Mars", 0)
    mars_dignity = _dignity("Mars", mars_sign)
    sat_sign = _planet_sign(planets, "Saturn") or "—"
    sat_house = p_house.get("Saturn", 0)
    sat_dignity = _dignity("Saturn", sat_sign)
    rahu_sign = _planet_sign(planets, "Rahu") or "—"
    rahu_house = p_house.get("Rahu", 0)
    ketu_sign = _planet_sign(planets, "Ketu") or "—"
    ketu_house = p_house.get("Ketu", 0)

    karakas = {
        "vitality_karaka": "Sun",
        "sun_sign": sun_sign,
        "sun_house": sun_house,
        "sun_dignity": sun_dignity,
        "mind_fluids_karaka": "Moon",
        "moon_sign": moon_sign,
        "moon_house": moon_house,
        "moon_dignity": moon_dignity,
        "blood_surgery_karaka": "Mars",
        "mars_sign": mars_sign,
        "mars_house": mars_house,
        "mars_dignity": mars_dignity,
        "chronic_bones_karaka": "Saturn",
        "saturn_sign": sat_sign,
        "saturn_house": sat_house,
        "saturn_dignity": sat_dignity,
        "mystery_illness_karaka": "Rahu",
        "rahu_sign": rahu_sign,
        "rahu_house": rahu_house,
        "diagnostic_blindspot_karaka": "Ketu",
        "ketu_sign": ketu_sign,
        "ketu_house": ketu_house,
        "note": ("Sun = vitality/spine/heart, Moon = mind/fluids/lymph, Mars = blood/muscle/"
                 "surgery, Saturn = chronic/bones/joints, Rahu = mystery/foreign-illness, "
                 "Ketu = subtle/diagnostic-blindspot. Sun+Moon dignity = primary vitality-pulse."),
    }

    # ── 3. Ayurdaya Tier (Pinda heuristic) ─────────────────────
    ayurdaya = _ayurdaya_tier(planets, asc, eighth_lord)

    # ── 4. Maraka Audit ────────────────────────────────────────
    maraka = _maraka_audit(planets, asc)

    # ── 5. Sudden-Event Timing ─────────────────────────────────
    timing = _sudden_event_timing(kundli, planets, asc, eighth_lord)

    # ── 6. Roga / Karmic Signatures ────────────────────────────
    roga = _roga_signatures(planets, asc, eighth_lord)

    # ── 7. Synthesis ───────────────────────────────────────────
    # Decision tree (priority order):
    # 1. KARMIC if ayurdaya=ALPA OR roga=STRONG-ROGA-KARMA
    # 2. TRANSFORMATION if 2+ planets in 8th OR strong Scorpio-Saturn signature
    #    AND not karmic-overloaded
    # 3. BLESSED if ayurdaya=PURNA AND roga=LIGHT-KARMIC AND maraka_score < 20
    # 4. MODERATE otherwise
    if ayurdaya["tier_key"] == "alpa" or roga["karmic_verdict"] == "STRONG-ROGA-KARMA":
        verdict_token = SYNTHESIS_TOKENS["karmic"]
    elif (roga["transformation_focus"]
            and roga["karmic_verdict"] != "STRONG-ROGA-KARMA"
            and ayurdaya["tier_key"] != "alpa"):
        verdict_token = SYNTHESIS_TOKENS["transformation"]
    elif (ayurdaya["tier_key"] == "purna"
            and roga["karmic_verdict"] == "LIGHT-KARMIC"
            and maraka["severity_score"] < 20):
        verdict_token = SYNTHESIS_TOKENS["blessed"]
    else:
        verdict_token = SYNTHESIS_TOKENS["moderate"]

    summary_lines = [
        f"8th house {eighth_sign} (lord {eighth_lord} in H{el_house}, {el_dignity}) — "
        f"strength {el_strength}/100.",
        f"Health karakas: Sun in {sun_sign} H{sun_house} ({sun_dignity}); "
        f"Moon in {moon_sign} H{moon_house} ({moon_dignity}); "
        f"Mars in {mars_sign} H{mars_house}; Saturn in {sat_sign} H{sat_house}.",
        f"Ayurdaya tier: {ayurdaya['tier_key'].upper()} (proxy score {ayurdaya['score']}/100).",
        f"Maraka audit: 2L {maraka['second_lord']} H{maraka['second_lord_house']}, "
        f"7L {maraka['seventh_lord']} H{maraka['seventh_lord_house']}, "
        f"severity {maraka['severity_score']}/100.",
        f"Sudden-event window: {timing['window_status']} "
        f"(MD={timing['current_md']}, AD={timing['current_ad']}).",
        f"Roga signatures: {roga['karmic_verdict']} (score {roga['karmic_score']}/100).",
        f"Synthesis verdict: {verdict_token}.",
    ]

    profile_lines = [
        f"Body-system focus from 8th sign ({eighth_sign}): "
        f"{EIGHTH_SIGN_BODY.get(eighth_sign, '—')}",
        f"Chronic-tendency from 8L {eighth_lord} in {el_sign}: "
        f"{EIGHTH_LORD_SIGN_BODY.get(el_sign, '—')}",
        f"Ayurdaya tier indication: {AYURDAYA_TIERS[ayurdaya['tier_key']]}",
    ]

    action_plan: List[str] = []
    if roga["karmic_verdict"] == "STRONG-ROGA-KARMA":
        action_plan.append("Roga-karma is heavy: build a daily wellness rhythm (yoga + pranayama "
                            "+ early sleep + clean diet); annual full-body screening with a "
                            "qualified physician is non-negotiable.")
    if roga.get("saturn_in_8th"):
        action_plan.append("Saturn in 8th: chronic-pattern care — joint/skeletal mobility daily "
                            "(surya namaskar + walking), Shani-shanti (Saturday simplicity, "
                            "sesame oil donation); consult a physician for bone-density baseline.")
    if roga.get("mars_in_8th"):
        action_plan.append("Mars in 8th: avoid risky physical activity in Mars-MD/AD; carry "
                            "comprehensive health insurance with surgical cover; Hanuman "
                            "Chalisa daily; postpone elective surgery when an alternative exists.")
    if roga.get("rahu_in_8th"):
        action_plan.append("Rahu in 8th: take multiple specialist opinions for unusual "
                            "symptoms; Rahu-mantra (Om Rahave Namaha 108x Saturdays); avoid "
                            "self-medication and unverified online remedies.")
    if ayurdaya["tier_key"] == "alpa":
        action_plan.append("Ayurdaya proxy = ALPA-tier: prioritise lifestyle longevity-builders "
                            "(low-stress work rhythm, regular check-ups, Ayur-rasayana herbs "
                            "under qualified guidance); see a physician for a full vitality panel.")
    if maraka["severity_score"] >= 25:
        action_plan.append(f"Maraka load elevated: extra health-vigilance during dasha/AD of "
                            f"{maraka['second_lord']} (2L) and {maraka['seventh_lord']} (7L); "
                            f"preventive screening before those windows is wise.")
    action_plan.append(f"Best dasha-window planets to watch for sudden-event vigilance: "
                        f"{', '.join(timing['activators'])}.")
    action_plan.append("ALWAYS consult a qualified physician for medical decisions. This Ayur "
                       "Bhava audit is a karmic-vitality map only, not a medical diagnosis.")

    out.update({
        "available": True,
        "ascendant": asc,
        "ayur_bhava": ayur_bhava,
        "karakas": karakas,
        "ayurdaya": ayurdaya,
        "maraka": maraka,
        "timing": timing,
        "roga": roga,
        "synthesis": {
            "verdict_token": verdict_token,
            "summary_lines": summary_lines,
            "profile_lines": profile_lines,
            "action_plan": action_plan[:7],
            "disclaimer": ("This Ayur Bhava audit is a karmic-vitality map, NOT a medical "
                           "diagnosis or lifespan prediction. Always consult a qualified "
                           "physician for medical concerns."),
        },
    })
    return out

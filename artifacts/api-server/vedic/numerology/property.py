"""Tier 14 — Property, Vehicles, Assets & Comforts Deep Audit engine.

Chart-based property/asset prognosis: Sukha Bhava (4th house + lord),
Bhumi/Vahana karakas (Mars = land, Venus = vehicles & comforts, Saturn =
real-estate/agricultural land, Mercury = small properties), D4 Chaturthamsa
picture (the property chart), classical Bhumi-prapti / Vahana yogas +
obstructions audit, current dasha acquisition-timing window, karmic /
Vastu signatures (Rahu/Ketu/Saturn in 4th + Mata-doshas), and a synthesis
with property profile + vehicle indication + 6-step action plan.

Hard data gate: ascendant + 9 grahas. Dasha is soft-gated (timing block
degrades gracefully to PREP-WINDOW if MD/AD absent). D4 is also soft-gated
(D4 picture renders explicit "data not available" fallback message).
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
BENEFICS = {"Jupiter", "Venus", "Mercury"}
MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}
DUSTHANA = {6, 8, 12}

# Property/comfort temperament by 4th-house sign (BPHS / Phaladeepika lineage)
FOURTH_SIGN_PROPERTY: Dict[str, str] = {
    "Aries": "small but active properties; lands near hills, military zones, or new-development areas; bold, fast acquisitions; risk of disputes.",
    "Taurus": "fertile agricultural land, fixed assets, beautiful homes; slow but solid acquisitions; gardens, dairy farms, luxury property.",
    "Gemini": "multiple small properties, urban apartments, commercial shops; properties tied to communication, media, or trade.",
    "Cancer": "ancestral home, water-front property, family-inherited land; deep mother-bond with home; emotional attachment to dwelling.",
    "Leo": "prestigious bungalow, royal-style architecture, properties in elevated areas; status-symbol homes; dramatic entrance.",
    "Virgo": "compact efficient homes, rental properties for income, medical-related buildings; perfectionist about maintenance.",
    "Libra": "beautiful designer homes, partnership-property, art-filled spaces; harmony-focused interiors; jointly held assets.",
    "Scorpio": "transformative property history (purchased after struggle), basement/underground spaces, properties with hidden value; secretive about holdings.",
    "Sagittarius": "large open homes, properties near temples or universities, foreign-land holdings, philosophical/spiritual abode.",
    "Capricorn": "old/heritage property, government quarters, slow-built homes, mountainous-area land; mature acquisition after 30.",
    "Aquarius": "unconventional homes (eco/tech/community), urban apartments, properties tied to networks or social causes; futuristic design.",
    "Pisces": "homes near water, ashram-like spiritual retreats, charitable-trust properties; dreamy/artistic interiors; foreign-land tendency.",
}

# Vehicle indication by Venus sign (Vahana karaka)
VENUS_SIGN_VEHICLE: Dict[str, str] = {
    "Aries": "fast/sporty vehicles, red-toned, two-wheelers; bold styling.",
    "Taurus": "luxury sedans, comfort-first vehicles, fully-loaded models; classical aesthetic.",
    "Gemini": "multiple vehicles, light/compact cars, communication-focused (commercial vans, EVs).",
    "Cancer": "family SUVs, water-craft, white/silver tones; emotional attachment to vehicle.",
    "Leo": "luxury or status vehicles, golden/cream tones, premium brands; show-stoppers.",
    "Virgo": "fuel-efficient compact cars, well-maintained, practical models; service-oriented vehicles.",
    "Libra": "beautiful designer cars, partnership-vehicles (joint-purchase), aesthetic-first.",
    "Scorpio": "powerful SUVs, deep-toned (black/maroon), high-performance, transformative purchases.",
    "Sagittarius": "long-distance touring vehicles, off-roaders, foreign-brand cars; travel-ready.",
    "Capricorn": "mature/classic vehicles, durable workhorses, second-hand-but-solid acquisitions.",
    "Aquarius": "EVs, futuristic models, community/shared vehicles, unusual brands.",
    "Pisces": "boats/water-vehicles, dreamy designs, foreign-imported; spiritual-mobility (pilgrimage cars).",
}

SYNTHESIS_TOKENS = {
    "blessed": "BLESSED-PROPERTY-PATH",
    "delayed": "DELAYED-DHARMIC-ACQUISITION",
    "karmic": "KARMIC-PROPERTY-PATH",
    "vastu": "VASTU-CLEANSING-REQUIRED",
}


# ── helpers ──────────────────────────────────────────────────────
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


def _d4_data(kundli: Dict) -> Dict[str, Any]:
    """D4 Chaturthamsa = property/asset chart. Falls back to empty if absent."""
    dc = kundli.get("divisionalCharts") or {}
    d4 = dc.get("D4") or dc.get("d4") or {}
    if not isinstance(d4, dict):
        return {}
    asc_d4 = d4.get("ascendant") or d4.get("Ascendant")
    plist = []
    for k in ("planets", "Planets"):
        if isinstance(d4.get(k), list):
            plist = d4[k]
            break
    return {"ascendant": asc_d4, "planets": plist}


def _planet_sign_in_chart(plist: List[Dict], name: str) -> Optional[str]:
    for p in plist:
        if isinstance(p, dict) and p.get("name") == name:
            s = p.get("sign")
            if s in SIGNS:
                return s
    return None


def _has_aspect(planets: List[Dict], asc_sign: str, src: str, target_house: int) -> bool:
    """Vedic aspect: all planets aspect 7th from self; Mars also 4,8;
    Jupiter 5,9; Saturn 3,10; Rahu/Ketu 5,7,9."""
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


# ── Property Yogas audit ─────────────────────────────────────────
def _property_yogas_audit(planets: List[Dict], asc_sign: str,
                            fourth_lord: str) -> Dict[str, Any]:
    """Detect classical Bhumi-prapti / Vahana yogas + obstructions."""
    p_house = _planet_house(planets, asc_sign)
    asc_idx = SIGNS.index(asc_sign)
    ninth_lord = SIGN_LORD[SIGNS[(asc_idx + 8) % 12]]
    eleventh_lord = SIGN_LORD[SIGNS[(asc_idx + 10) % 12]]

    fourth_occ = _occupants(planets, asc_sign, 4)
    fl_house = p_house.get(fourth_lord, 0)
    mars_house = p_house.get("Mars", 0)
    venus_house = p_house.get("Venus", 0)
    saturn_house = p_house.get("Saturn", 0)
    moon_house = p_house.get("Moon", 0)

    mars_dignity = _dignity("Mars", _planet_sign(planets, "Mars"))
    venus_dignity = _dignity("Venus", _planet_sign(planets, "Venus"))

    yogas: List[str] = []

    # 1. 4L + 9L combo (Bhagya-Sukha yoga — fortunate property acquisition)
    if fourth_lord == ninth_lord or p_house.get(fourth_lord) == p_house.get(ninth_lord):
        yogas.append(f"4L–9L Bhagya-Sukha yoga (4L & 9L = {fourth_lord}/{ninth_lord}) — "
                     f"fortunate Bhumi-prapti combo per BPHS.")

    # 2. Mars (Bhumi karaka) in own/exalted in 4th
    if mars_house == 4 and mars_dignity in ("exalted", "own-sign"):
        yogas.append(f"Mars ({mars_dignity}) in 4th — premium Bhumi karaka placement; "
                     f"strong land/property indicator.")
    elif mars_house == 4:
        yogas.append("Mars in 4th — Bhumi-karaka in Sukha Bhava; basic land yoga active.")

    # 3. Venus (Vahana karaka) in 4th
    if venus_house == 4 and venus_dignity in ("exalted", "own-sign"):
        yogas.append(f"Venus ({venus_dignity}) in 4th — premium Vahana/luxury yoga; "
                     f"vehicles, comforts, beautiful homes flow naturally.")
    elif venus_house == 4:
        yogas.append("Venus in 4th — Vahana karaka in Sukha Bhava; comforts and "
                     "vehicle acquisition supported.")

    # 4. Jupiter aspects 4th house (Guru-drishti = blessing)
    if _has_aspect(planets, asc_sign, "Jupiter", 4):
        yogas.append("Jupiter aspects the 4th — Guru-drishti on Sukha Bhava; "
                     "noble/auspicious property and protected home life.")

    # 5. 4L in Kendra or Trikona (well-placed lord)
    if fl_house in (KENDRA | TRIKONA):
        yogas.append(f"4L {fourth_lord} in H{fl_house} (Kendra/Trikona) — "
                     f"property/comfort lord well-placed.")

    # 6. 4L + 11L combo (gain-of-property)
    if fourth_lord == eleventh_lord or p_house.get(fourth_lord) == p_house.get(eleventh_lord):
        yogas.append(f"4L–11L combo (4L {fourth_lord}, 11L {eleventh_lord}) — "
                     f"property-yoga via gain-house; multiple acquisitions likely.")

    # 7. Moon in 4th in own/exalted (Chandra in Sukha = mother + property bliss)
    if moon_house == 4 and _dignity("Moon", _planet_sign(planets, "Moon")) in ("exalted", "own-sign"):
        yogas.append("Moon (exalted/own) in 4th — Chandra-Sukha yoga; emotional "
                     "comfort, mother-blessings, and beautiful home environment.")

    obstructions: List[str] = []

    if "Saturn" in fourth_occ:
        obstructions.append("Saturn in 4th — DELAY signature for property (often after 35); "
                            "old/heritage homes, cold living spaces, mother-distance risk.")
    if "Rahu" in fourth_occ:
        obstructions.append("Rahu in 4th — unconventional property path (foreign land, "
                            "litigation-prone purchases); Vastu-dosha risk; clear ownership essential.")
    if "Ketu" in fourth_occ:
        obstructions.append("Ketu in 4th — past-life-completed property karma; detachment "
                            "from home; risk of repeated relocations.")
    if "Sun" in fourth_occ:
        obstructions.append("Sun in 4th — ego-conflict with home/mother; less property "
                            "satisfaction; government-quarters indication.")
    if "Mars" in fourth_occ and mars_dignity == "debilitated":
        obstructions.append("Mars debilitated in 4th — Bhumi karaka afflicted; property "
                            "disputes, boundary fights; needs Mangal-shanti.")
    if fl_house in DUSTHANA:
        obstructions.append(f"4L {fourth_lord} in H{fl_house} (Dusthana) — "
                            f"property/comfort karma needs purification.")
    if mars_dignity == "debilitated":
        obstructions.append("Mars debilitated overall — Bhumi karaka weak; do Mars remedies "
                            "(Mangal mantra, red lentil donation Tuesdays) before any major "
                            "land purchase.")

    yoga_count = len(yogas)
    obs_count = len(obstructions)
    score = max(0, min(100, 50 + (yoga_count * 12) - (obs_count * 10)))

    if score >= 70 and obs_count <= 1:
        severity = "BLESSED"
        verdict = ("Multiple Bhumi-Vahana yogas active with minimal obstruction — "
                   "natural acquisition path with classical blessings.")
    elif score >= 50:
        severity = "MODERATE"
        verdict = ("Mixed signals — yogas present but some obstructions; conscious "
                   "Vastu-care + correct timing will produce results.")
    elif score >= 30:
        severity = "CHALLENGED"
        verdict = ("Obstructions outweigh yogas — significant property-karma work "
                   "required; verify titles meticulously and use classical remedies.")
    else:
        severity = "DENSE-KARMA"
        verdict = ("Heavy property-karma signature — Vastu-shanti, Bhumi-puja before "
                   "purchase, and patient timing-of-dasha strongly indicated.")

    return {
        "yogas": yogas[:7],
        "obstructions": obstructions[:7],
        "yoga_count": yoga_count,
        "obstruction_count": obs_count,
        "score": score,
        "severity": severity,
        "verdict": verdict,
        "fourth_occupants": fourth_occ,
        "fourth_lord_house": fl_house,
        "mars_house": mars_house,
        "venus_house": venus_house,
    }


# ── Acquisition Timing Window ────────────────────────────────────
def _acquisition_timing(kundli: Dict, planets: List[Dict], asc_sign: str,
                          fourth_lord: str) -> Dict[str, Any]:
    dasha = kundli.get("dasha") or kundli.get("currentDasha") or {}
    md_lord = (dasha.get("mahaDasha") or dasha.get("md") or {}).get("planet") \
              if isinstance(dasha, dict) else None
    ad_lord = (dasha.get("antarDasha") or dasha.get("ad") or {}).get("planet") \
              if isinstance(dasha, dict) else None
    if not md_lord:
        md_lord = dasha.get("mahadasha_lord") if isinstance(dasha, dict) else None
        ad_lord = dasha.get("antardasha_lord") if isinstance(dasha, dict) else None

    asc_idx = SIGNS.index(asc_sign)
    second_lord = SIGN_LORD[SIGNS[(asc_idx + 1) % 12]]   # accumulated wealth → property
    eleventh_lord = SIGN_LORD[SIGNS[(asc_idx + 10) % 12]]  # gain
    occ_4th = _occupants(planets, asc_sign, 4)

    activators = {fourth_lord, "Mars", "Venus", second_lord, eleventh_lord}
    for p in occ_4th:
        activators.add(p)
    activators.discard("—")

    md_active = md_lord in activators if md_lord else False
    ad_active = ad_lord in activators if ad_lord else False

    if md_active and ad_active:
        window_status = "ACTIVE ACQUISITION WINDOW"
        window_note = (f"Both MD ({md_lord}) and AD ({ad_lord}) are property-activators — "
                       f"this is a strongly supportive acquisition window per dasha logic.")
    elif md_active:
        window_status = "WARM ACQUISITION WINDOW"
        window_note = (f"MD lord {md_lord} is a property-activator — primary timing pull alive; "
                       f"watch for AD/PD of Mars/Venus/4L/11L to lock the deal.")
    elif ad_active:
        window_status = "TACTICAL WINDOW"
        window_note = (f"AD lord {ad_lord} is a property-activator inside non-aligned MD "
                       f"({md_lord or 'unknown'}) — short opportunity window; act decisively.")
    else:
        window_status = "PREP WINDOW"
        window_note = (f"Neither MD ({md_lord or 'unknown'}) nor AD ({ad_lord or 'unknown'}) "
                       f"is a primary property-activator — use this period for Vastu-shanti, "
                       f"savings, and title research; avoid major purchases.")

    return {
        "current_md": md_lord or "—",
        "current_ad": ad_lord or "—",
        "activators": sorted(activators),
        "fourth_lord": fourth_lord,
        "second_lord": second_lord,
        "eleventh_lord": eleventh_lord,
        "md_is_activator": md_active,
        "ad_is_activator": ad_active,
        "window_status": window_status,
        "window_note": window_note,
    }


# ── Karmic / Vastu Signatures ────────────────────────────────────
def _vastu_signatures(planets: List[Dict], asc_sign: str,
                       fourth_lord: str) -> Dict[str, Any]:
    """Detect karmic / Vastu-dosha signatures affecting Sukha Bhava."""
    p_house = _planet_house(planets, asc_sign)
    fourth_occ = _occupants(planets, asc_sign, 4)

    flags: List[str] = []

    if "Rahu" in fourth_occ:
        flags.append("Vastu-dosha indicator — Rahu in 4th: hidden boundary disputes, "
                     "title confusion, foreign-tenant risk; perform Vastu-shanti, "
                     "place a Vastu-yantra in the north-east before moving in.")
    if "Ketu" in fourth_occ:
        flags.append("Vastu-dosha indicator — Ketu in 4th: spiritual-detachment from home, "
                     "risk of repeated relocations; install Ganesha at entrance, "
                     "regular Bhoomi-puja recommended.")
    if "Saturn" in fourth_occ:
        flags.append("Saturn-dosha indicator — Saturn in 4th: cold/heavy living spaces, "
                     "mother-distance, slow construction; Shani-shanti (sesame oil donation, "
                     "iron-pot food to needy on Saturdays).")
    if "Mars" in fourth_occ and _dignity("Mars", _planet_sign(planets, "Mars")) == "debilitated":
        flags.append("Bhumi-dosha indicator — debilitated Mars in 4th: boundary fights, "
                     "construction delays, fire/electrical risks; Mangal-shanti before "
                     "any structural work.")

    # 4L + Rahu/Ketu conjunction = title-karma
    if p_house.get("Rahu") == p_house.get(fourth_lord) and p_house.get("Rahu"):
        flags.append(f"Title-karma indicator — Rahu conjunct 4L ({fourth_lord}); "
                     f"verify all property documents through legal counsel before purchase.")
    if p_house.get("Ketu") == p_house.get(fourth_lord) and p_house.get("Ketu"):
        flags.append(f"Detachment-karma indicator — Ketu conjunct 4L ({fourth_lord}); "
                     f"property may not deliver expected emotional satisfaction; "
                     f"build temple/charity-space within home for blessing.")

    # Matru-dosha — Moon afflicted (already covered in T13 but tied to 4th here)
    moon_h = p_house.get("Moon", 0)
    if moon_h in (4, 8, 12) and _dignity("Moon", _planet_sign(planets, "Moon")) == "debilitated":
        flags.append(f"Matru-dosha indicator — debilitated Moon in H{moon_h}; honour mother, "
                     f"recite Sri Suktam before home-related decisions.")

    # Karmic load score
    score = (
        (15 if "Rahu" in fourth_occ else 0)
        + (10 if "Ketu" in fourth_occ else 0)
        + (15 if "Saturn" in fourth_occ else 0)
        + (10 if "Mars" in fourth_occ and
            _dignity("Mars", _planet_sign(planets, "Mars")) == "debilitated" else 0)
        + (10 if p_house.get("Rahu") == p_house.get(fourth_lord) and p_house.get("Rahu") else 0)
    )

    if score >= 30:
        karmic_verdict = "STRONG-VASTU-DOSHA"
    elif score >= 15:
        karmic_verdict = "MODERATE-KARMIC"
    else:
        karmic_verdict = "LIGHT-KARMIC"

    return {
        "fourth_occupants": fourth_occ,
        "rahu_in_4th": "Rahu" in fourth_occ,
        "ketu_in_4th": "Ketu" in fourth_occ,
        "saturn_in_4th": "Saturn" in fourth_occ,
        "mars_in_4th": "Mars" in fourth_occ,
        "karmic_score": score,
        "karmic_verdict": karmic_verdict,
        "flags": flags[:6],
    }


# ── main ─────────────────────────────────────────────────────────
def compute_property_bundle(kundli: Dict[str, Any], dob: str,
                             driver: int, conductor: int) -> Dict[str, Any]:
    """T14 Property bundle. Hard data gate; never fabricates."""
    out: Dict[str, Any] = {"available": False}
    if not isinstance(kundli, dict):
        out["reason"] = "no kundli"
        return out
    asc = kundli.get("ascendant")
    planets = kundli.get("planets", []) or []
    if not asc or asc not in SIGNS:
        out["reason"] = f"ascendant missing or unknown ({asc!r})"
        return out
    if not isinstance(planets, list) or len(planets) < 9:
        out["reason"] = f"planets list incomplete (n={len(planets) if isinstance(planets, list) else 0})"
        return out
    required = {"Sun", "Moon", "Jupiter", "Mars", "Venus", "Mercury", "Saturn", "Rahu", "Ketu"}
    pn = {p.get("name") for p in planets if isinstance(p, dict)}
    missing = required - pn
    if missing:
        out["reason"] = f"missing required grahas: {sorted(missing)}"
        return out

    asc_idx = SIGNS.index(asc)
    p_house = _planet_house(planets, asc)

    # ── 1. Sukha Bhava (4th house + lord) ──────────────────────
    fourth_sign = SIGNS[(asc_idx + 3) % 12]
    fourth_lord = SIGN_LORD[fourth_sign]
    fl_house = p_house.get(fourth_lord, 0)
    fl_sign = _planet_sign(planets, fourth_lord) or "—"
    fl_dignity = _dignity(fourth_lord, fl_sign)
    fourth_occupants = _occupants(planets, asc, 4)

    fl_strength = 50
    if fl_house in KENDRA | TRIKONA:
        fl_strength += 20
    elif fl_house in DUSTHANA:
        fl_strength -= 25
    if fl_dignity == "exalted":
        fl_strength += 25
    elif fl_dignity == "own-sign":
        fl_strength += 15
    elif fl_dignity == "debilitated":
        fl_strength -= 25
    fl_strength = max(0, min(100, fl_strength))

    if fl_strength >= 70:
        fl_verdict = "STRONG property-foundation — Sukha karma well-supported"
    elif fl_strength >= 40:
        fl_verdict = "MODERATE property-foundation — workable with Vastu-care + remedies"
    else:
        fl_verdict = "FRAGILE property-foundation — sustained remedies + careful timing essential"

    sukha_bhava = {
        "fourth_sign": fourth_sign,
        "fourth_lord": fourth_lord,
        "lord_house": fl_house,
        "lord_sign": fl_sign,
        "lord_dignity": fl_dignity,
        "occupants": fourth_occupants,
        "strength_score": fl_strength,
        "verdict": fl_verdict,
        "property_indication": FOURTH_SIGN_PROPERTY.get(fourth_sign, "—"),
    }

    # ── 2. Bhumi/Vahana Karakas ────────────────────────────────
    mars_sign = _planet_sign(planets, "Mars") or "—"
    mars_house = p_house.get("Mars", 0)
    mars_dignity = _dignity("Mars", mars_sign)
    venus_sign = _planet_sign(planets, "Venus") or "—"
    venus_house = p_house.get("Venus", 0)
    venus_dignity = _dignity("Venus", venus_sign)
    saturn_sign = _planet_sign(planets, "Saturn") or "—"
    saturn_house = p_house.get("Saturn", 0)
    saturn_dignity = _dignity("Saturn", saturn_sign)

    karakas = {
        "bhumi_karaka": "Mars",
        "mars_sign": mars_sign,
        "mars_house": mars_house,
        "mars_dignity": mars_dignity,
        "vahana_karaka": "Venus",
        "venus_sign": venus_sign,
        "venus_house": venus_house,
        "venus_dignity": venus_dignity,
        "land_karaka_secondary": "Saturn",
        "saturn_sign": saturn_sign,
        "saturn_house": saturn_house,
        "saturn_dignity": saturn_dignity,
        "vehicle_indication": VENUS_SIGN_VEHICLE.get(venus_sign, "—"),
        "note": ("Mars = Bhumi-karaka (land/property), Venus = Vahana-karaka "
                 "(vehicles & comforts), Saturn = secondary land-karaka "
                 "(real-estate, agricultural land, old buildings)."),
    }

    # ── 3. D4 Chaturthamsa Picture ─────────────────────────────
    d4 = _d4_data(kundli)
    d4_asc = d4.get("ascendant")
    d4_plist = d4.get("planets", []) or []
    d4_fourth_sign = None
    d4_fourth_lord = "—"
    d4_fourth_occ: List[str] = []
    if d4_asc in SIGNS:
        d4_fourth_sign = SIGNS[(SIGNS.index(d4_asc) + 3) % 12]
        d4_fourth_lord = SIGN_LORD.get(d4_fourth_sign, "—")
        if d4_plist:
            for p in d4_plist:
                if isinstance(p, dict) and p.get("sign") == d4_fourth_sign:
                    d4_fourth_occ.append(p.get("name", ""))
            d4_fourth_occ = sorted([x for x in d4_fourth_occ if x])

    mars_d4_sign = _planet_sign_in_chart(d4_plist, "Mars") if d4_plist else None

    d4_picture = {
        "d4_ascendant": d4_asc or "—",
        "d4_fourth_sign": d4_fourth_sign or "—",
        "d4_fourth_lord": d4_fourth_lord,
        "d4_fourth_occupants": d4_fourth_occ,
        "mars_d4_sign": mars_d4_sign or "—",
        "available": bool(d4_asc and d4_plist),
        "note": ("D4 Chaturthamsa is the classical property/asset chart. "
                 "D4 Lagna shows essence of fortunes; D4-4th refines property-strength; "
                 "Mars in D4 fine-tunes the Bhumi-karaka reading."),
    }

    # ── 4. Property Yogas Audit ────────────────────────────────
    yogas_audit = _property_yogas_audit(planets, asc, fourth_lord)

    # ── 5. Acquisition Timing Window ───────────────────────────
    timing = _acquisition_timing(kundli, planets, asc, fourth_lord)

    # ── 6. Karmic / Vastu Signatures ───────────────────────────
    karmic = _vastu_signatures(planets, asc, fourth_lord)

    # ── 7. Synthesis ───────────────────────────────────────────
    if karmic["karmic_verdict"] == "STRONG-VASTU-DOSHA":
        verdict_token = SYNTHESIS_TOKENS["vastu"]
    elif yogas_audit["severity"] == "BLESSED" and karmic["karmic_verdict"] == "LIGHT-KARMIC":
        verdict_token = SYNTHESIS_TOKENS["blessed"]
    elif "Saturn" in fourth_occupants or yogas_audit["severity"] in ("MODERATE", "CHALLENGED"):
        verdict_token = SYNTHESIS_TOKENS["delayed"]
    else:
        verdict_token = SYNTHESIS_TOKENS["karmic"]

    summary_lines = [
        f"4th house {fourth_sign} (lord {fourth_lord} in H{fl_house}, {fl_dignity}) — "
        f"strength {fl_strength}/100.",
        f"Bhumi karaka Mars in {mars_sign} H{mars_house} ({mars_dignity}); "
        f"Vahana karaka Venus in {venus_sign} H{venus_house} ({venus_dignity}).",
        f"D4 Chaturthamsa: Lagna {d4_picture['d4_ascendant']}, 4th = "
        f"{d4_picture['d4_fourth_sign']} (lord {d4_picture['d4_fourth_lord']}).",
        f"Property Yogas: {yogas_audit['yoga_count']} active, "
        f"{yogas_audit['obstruction_count']} obstructions — {yogas_audit['severity']} "
        f"({yogas_audit['score']}/100).",
        f"Karmic load: {karmic['karmic_verdict']} (score {karmic['karmic_score']}/100).",
        f"Current dasha: {timing['current_md']} → {timing['current_ad']} — "
        f"{timing['window_status']}.",
    ]

    profile_lines = [
        f"Property profile from 4th sign ({fourth_sign}): {FOURTH_SIGN_PROPERTY.get(fourth_sign, '—')}",
        f"Vehicle indication from Venus in {venus_sign}: {VENUS_SIGN_VEHICLE.get(venus_sign, '—')}",
    ]
    if d4_picture["available"]:
        profile_lines.append(
            f"Refinement via D4 Lagna ({d4_picture['d4_ascendant']}): the soul-essence of "
            f"your property fortunes resonates with {d4_picture['d4_ascendant']} qualities — "
            f"this is the deeper Sukha-karma signature of this lifetime."
        )

    action_plan: List[str] = []
    if karmic["karmic_verdict"] == "STRONG-VASTU-DOSHA":
        action_plan.append("Vastu-shanti before any major property move: north-east Vastu-yantra, "
                            "Bhoomi-puja before construction, neutralise Vastu-doshas with "
                            "professional Vastu consultation.")
    if karmic["saturn_in_4th"]:
        action_plan.append("Saturn in 4th: avoid hasty pre-35 property purchases; Shani-shanti "
                            "(Saturday fasts, sesame oil donation, iron-pot meals to needy).")
    if karmic["rahu_in_4th"]:
        action_plan.append("Rahu in 4th: triple-verify property titles and chain-of-ownership "
                            "through legal counsel; never buy under family pressure.")
    if mars_dignity == "debilitated":
        action_plan.append("Strengthen Mars (Bhumi karaka): Mangal mantra (108x Tuesdays), "
                            "donate red lentils + jaggery, Hanuman Chalisa daily.")
    if venus_dignity == "debilitated":
        action_plan.append("Strengthen Venus (Vahana karaka): Lakshmi mantra Fridays, white "
                            "clothes, donate ghee/sweets to women, postpone vehicle purchase to "
                            "supportive Venus dasha-bhukti.")
    action_plan.append(f"Best dasha-window planets to watch for property/vehicle: "
                        f"{', '.join(timing['activators'])}.")
    action_plan.append(f"Property direction (per 4th sign {fourth_sign}): "
                        f"{FOURTH_SIGN_PROPERTY.get(fourth_sign, '—')}")

    synthesis = {
        "verdict_token": verdict_token,
        "summary_lines": summary_lines,
        "profile_lines": profile_lines,
        "action_plan": action_plan[:6],
    }

    out["available"] = True
    out["sukha_bhava"] = sukha_bhava
    out["karakas"] = karakas
    out["d4_picture"] = d4_picture
    out["yogas_audit"] = yogas_audit
    out["timing"] = timing
    out["karmic"] = karmic
    out["synthesis"] = synthesis
    return out

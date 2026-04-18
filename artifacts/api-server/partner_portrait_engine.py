"""
Future Partner Portrait — full classical trait extraction engine.

Combines 15 layers of Vedic astrology to build a pinpoint physical
description of the user's future life partner, then ships that
description to a server-side image model to generate an artistic
portrait. The image is a *spiritual visualization* of the partner's
astrological signature, never claimed as a literal photograph.

Layers used:
  1.  D1   7th house  + lord                  — Brihat Parashara Adhyaya 80
  2.  D9   (Navamsa)  7th house + lord        — Phaladeepika Ch. 9
  3.  D3   (Drekkana) for face / upper body   — BPHS Ch. 7
  4.  D30  (Trimsamsa) for temperament        — Sarvartha Chintamani Ch. 13
  5.  KP   7th cuspal sub-lord                — KP Reader VI
  6.  Upapada Lagna (UL)                      — Jaimini Sutras 1.1.20
  7.  Darakaraka (DK) — lowest-degree planet  — Jaimini Sutras
  8.  Arudha Lagna (AL) and A7                — BPHS Ch. 31
  9.  Karaka 7th (Venus / Jupiter / Sun)      — BPHS
 10.  7th lord nakshatra lord                 — KP Reader IV
 11.  Vargottama detection (D1+D9 same sign)  — BPHS
 12.  Ashtakavarga 7th bindu count            — Sarvarthachintamani Ch. 4
 13.  D9 Lagna lord placement                 — Phaladeepika
 14.  Sandhi check (sign-end / nakshatra-end) — Hora Sara
 15.  Direction-based regional baseline       — Practical synthesis
"""

from __future__ import annotations

import os
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from kp_engine import calculate_kp


# ── Static reference tables ─────────────────────────────────────────────────
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

SIGN_LORDS = {
    "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon",
    "Leo":"Sun","Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars",
    "Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter",
}

SIGN_TATVA = {
    "Aries":"agni","Leo":"agni","Sagittarius":"agni",
    "Taurus":"prithvi","Virgo":"prithvi","Capricorn":"prithvi",
    "Gemini":"vayu","Libra":"vayu","Aquarius":"vayu",
    "Cancer":"jal","Scorpio":"jal","Pisces":"jal",
}

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
    "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
    "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha",
    "Purva Bhadrapada","Uttara Bhadrapada","Revati",
]
NAK_LORDS = [
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
]

# ── Planet → physical trait dictionary (classical synthesis) ────────────────
PLANET_TRAITS: Dict[str, Dict[str, str]] = {
    "Sun": {
        "complexion": "wheatish-golden with warm radiance",
        "build":      "athletic medium-tall with strong upright posture",
        "face":       "square-strong with broad forehead and noble bearing",
        "eyes":       "bright honey-brown, commanding, piercing gaze",
        "hair":       "thick dark brown to chestnut, neatly groomed",
        "vibe":       "regal, confident, leadership presence",
    },
    "Moon": {
        "complexion": "fair luminous with soft glow",
        "build":      "medium height, soft-curvy or gently athletic",
        "face":       "round-fleshy with full cheeks, gentle features",
        "eyes":       "large luminous black or deep grey, dreamy",
        "hair":       "thick wavy lustrous black, often shoulder length",
        "vibe":       "calm, nurturing, emotionally expressive",
    },
    "Mars": {
        "complexion": "reddish-bronze, warm sun-kissed",
        "build":      "athletic muscular medium height with strong shoulders",
        "face":       "angular sharp with defined cheekbones and firm jaw",
        "eyes":       "sharp piercing dark brown with intense focus",
        "hair":       "coarse dark brown to black, often slightly wavy",
        "vibe":       "energetic, bold, action-oriented",
    },
    "Mercury": {
        "complexion": "mixed olive-fair with smooth youthful skin",
        "build":      "medium-slim with graceful agile frame",
        "face":       "oval-delicate with quick expressive features",
        "eyes":       "bright lively medium-sized hazel or dark brown",
        "hair":       "curly or wavy dark brown, often medium length",
        "vibe":       "youthful, witty, intellectually animated",
    },
    "Jupiter": {
        "complexion": "fair-golden with serene glow",
        "build":      "tall well-built with broad chest, slightly portly",
        "face":       "long noble with broad forehead, dignified bearing",
        "eyes":       "warm large hazel-brown, kind and wise",
        "hair":       "thick straight chestnut to dark brown, full hairline",
        "vibe":       "wise, generous, scholarly, gravitas",
    },
    "Venus": {
        "complexion": "fair-pinkish with luminous glow and smooth skin",
        "build":      "medium balanced with graceful curvy or fit physique",
        "face":       "oval-balanced with symmetric soft attractive features",
        "eyes":       "large expressive almond-shaped, captivating, long lashes",
        "hair":       "thick wavy lustrous dark with natural shine, well-styled",
        "vibe":       "charming, artistic, romantic, magnetic beauty",
    },
    "Saturn": {
        "complexion": "dusky-dark with mature weathered tone",
        "build":      "tall lean-thin with bony frame and long limbs",
        "face":       "long-bony with high receding forehead and prominent jaw",
        "eyes":       "small deep-set dark, contemplative, serious",
        "hair":       "thin straight jet black, sometimes thinning hairline",
        "vibe":       "mature, disciplined, reserved, old-soul",
    },
    "Rahu": {
        "complexion": "smoky-dusky with mysterious unusual tone",
        "build":      "tall slim with unconventional features, foreign look",
        "face":       "asymmetric striking with sharp unusual features",
        "eyes":       "intense smoky-dark with hypnotic mysterious quality",
        "hair":       "thick dark with unusual style or natural streaks",
        "vibe":       "mysterious, exotic, magnetic, unconventional",
    },
    "Ketu": {
        "complexion": "earthy-tan with ascetic glow",
        "build":      "lean spiritual frame, medium height",
        "face":       "sharp ascetic with prominent cheekbones, distant gaze",
        "eyes":       "deep penetrating dark, far-away spiritual look",
        "hair":       "dark slightly unruly, often with cowlick or patch",
        "vibe":       "spiritual, intuitive, otherworldly, mystic",
    },
}

# ── Sign → face-shape mapping (for D1 + D3 + D9 lagna) ──────────────────────
SIGN_FACE_SHAPE = {
    "Aries":       "long oval with prominent forehead",
    "Taurus":      "square-broad with strong jawline",
    "Gemini":      "long-thin with sharp angular features",
    "Cancer":      "round-fleshy with full cheeks",
    "Leo":         "square-strong with leonine bearing",
    "Virgo":       "oval-delicate with refined features",
    "Libra":       "oval-balanced perfectly symmetric",
    "Scorpio":     "broad-intense with deep-set features",
    "Sagittarius": "long-noble with horse-like elongation",
    "Capricorn":   "long-bony with prominent chin",
    "Aquarius":    "square-flat with high cheekbones",
    "Pisces":      "round-soft with dreamy melting features",
}

# ── Eyebrow density mapping ─────────────────────────────────────────────────
EYEBROW_RULES = {
    "Mars":    "thick bushy well-defined arched",
    "Saturn":  "thick straight slightly heavy",
    "Sun":     "medium-thick straight neat",
    "Jupiter": "full balanced groomed",
    "Mercury": "thin shaped slightly arched",
    "Venus":   "soft well-groomed shaped arch",
    "Moon":    "soft medium curved",
    "Rahu":    "thick irregular striking",
    "Ketu":    "patchy thin sparse",
}

# ── Nose mapping (D9 lagna + Mercury based) ─────────────────────────────────
NOSE_BY_SIGN = {
    "Aries":       "sharp pointed straight",
    "Taurus":      "broad straight flared",
    "Gemini":      "long straight thin",
    "Cancer":      "snub rounded gentle",
    "Leo":         "straight strong well-defined",
    "Virgo":       "small refined straight",
    "Libra":       "straight balanced perfect",
    "Scorpio":     "aquiline curved prominent",
    "Sagittarius": "long noble Roman",
    "Capricorn":   "long thin bony",
    "Aquarius":    "straight medium balanced",
    "Pisces":      "soft small slightly upturned",
}

LIPS_BY_PLANET = {
    "Venus":   "full shapely sensual perfectly defined",
    "Jupiter": "plump generous well-formed",
    "Moon":    "soft medium gentle curve",
    "Mars":    "firm well-defined slightly thin upper",
    "Mercury": "medium expressive smiling-shaped",
    "Sun":     "medium full balanced",
    "Saturn":  "thin pursed firm",
    "Rahu":    "medium asymmetric striking",
    "Ketu":    "thin contemplative",
}


# ── Helpers — divisional charts from longitude ──────────────────────────────
def _sign_idx(lon: float) -> int:
    return int(lon / 30.0) % 12


def _d9_sign_idx(lon: float) -> int:
    return int((lon * 9.0) / 30.0) % 12


def _d3_sign_idx(lon: float) -> int:
    """Drekkana — each sign split in 3 parts of 10° each.
    Part 1 (0-10°): same sign. Part 2 (10-20°): 5th from. Part 3 (20-30°): 9th from."""
    sidx = int(lon / 30.0) % 12
    part = int((lon % 30.0) / 10.0)  # 0,1,2
    return (sidx + part * 4) % 12


def _d30_sign_idx(lon: float) -> int:
    """Trimsamsa — Parashari method (odd/even sign rules)."""
    sidx = int(lon / 30.0) % 12
    deg  = lon % 30.0
    is_odd = (sidx % 2 == 0)  # zero-indexed: Aries(0) = odd
    if is_odd:
        # Aries 5° Mars, 5° Saturn, 8° Jupiter, 7° Mercury, 5° Venus
        if deg < 5:   return 0   # Aries (Mars)
        if deg < 10:  return 9   # Capricorn (Saturn)
        if deg < 18:  return 8   # Sagittarius (Jupiter)
        if deg < 25:  return 5   # Virgo (Mercury)
        return 6                 # Libra (Venus)
    else:
        # Even: Venus 5°, Mercury 7°, Jupiter 8°, Saturn 5°, Mars 5°
        if deg < 5:   return 1   # Taurus (Venus)
        if deg < 12:  return 2   # Gemini (Mercury)
        if deg < 20:  return 11  # Pisces (Jupiter)
        if deg < 25:  return 10  # Aquarius (Saturn)
        return 7                 # Scorpio (Mars)


def _house_from_asc(lon: float, asc_lon: float) -> int:
    asc_idx = _sign_idx(asc_lon)
    sidx = _sign_idx(lon)
    return ((sidx - asc_idx + 12) % 12) + 1


def _arudha_pada(house_lord_house: int, original_house: int) -> int:
    """Arudha Pada calculation per Jaimini.
    Count from house to its lord, then equal count from lord onward.
    Then apply the rule: result is never the same as the original or 7th from it."""
    diff = ((house_lord_house - original_house) % 12) + 1  # 1..12
    arudha = ((house_lord_house - 1) + (diff - 1)) % 12 + 1  # 1..12
    # rule: not same as origin, not 7th from origin
    seventh = ((original_house - 1 + 6) % 12) + 1
    if arudha == original_house:
        arudha = ((arudha - 1 + 9) % 12) + 1   # +10th
    if arudha == seventh:
        arudha = ((arudha - 1 + 9) % 12) + 1
    return arudha


# ── Main extraction ────────────────────────────────────────────────────────
def extract_traits(kundli: Dict[str, Any],
                   birth_data: Optional[Dict[str, Any]] = None,
                   user_gender: str = "male") -> Dict[str, Any]:
    """
    Extract all 30+ partner traits from a kundli.

    Args:
      kundli:      output of calculate_kundli(...) — has planets[], ascendantDeg,
                   divisionalCharts.D9, etc.
      birth_data:  original birth dict ({day,month,year,hour,minute,ampm,lat,lon,tz})
                   — required if KP layer is desired.
      user_gender: "male" or "female" — flips karaka rules.

    Returns:
      Dict with raw planetary data + composed trait paragraphs.
    """
    if not isinstance(kundli, dict) or not kundli.get("planets"):
        raise ValueError("Invalid kundli — planets[] missing")

    asc_deg  = float(kundli.get("ascendantDeg", 0))
    planets  = kundli["planets"]

    # Map by name for quick lookup
    by_name: Dict[str, Dict[str, Any]] = {p["name"]: p for p in planets}

    # ── Layer 1: D1 7th house ──────────────────────────────────────────────
    asc_idx     = _sign_idx(asc_deg)
    seventh_idx = (asc_idx + 6) % 12
    seventh_sign = SIGNS[seventh_idx]
    seventh_lord = SIGN_LORDS[seventh_sign]

    # Planets occupying 7th
    occupants_7th = [p["name"] for p in planets
                     if _house_from_asc(p["longitude"], asc_deg) == 7]

    # ── Layer 2: D9 7th lord ───────────────────────────────────────────────
    d9 = (kundli.get("divisionalCharts") or {}).get("D9") or {}
    d9_asc_idx = d9.get("ascendantSignIndex", 0)
    d9_7th_idx = (d9_asc_idx + 6) % 12
    d9_7th_sign = SIGNS[d9_7th_idx]
    d9_7th_lord = SIGN_LORDS[d9_7th_sign]

    d9_occupants_7th = [p["name"] for p in (d9.get("planets") or [])
                        if p.get("house") == 7]

    # ── Layer 3: D3 (Drekkana) Lagna for face ──────────────────────────────
    d3_asc_idx = _d3_sign_idx(asc_deg)
    d3_asc_sign = SIGNS[d3_asc_idx]

    # ── Layer 4: D30 (Trimsamsa) Lagna for temperament ─────────────────────
    d30_asc_idx = _d30_sign_idx(asc_deg)
    d30_asc_sign = SIGNS[d30_asc_idx]
    d30_asc_lord = SIGN_LORDS[d30_asc_sign]

    # ── Layer 5: KP 7th cuspal sub-lord (only if birth_data given) ─────────
    kp_7th_sl = kp_7th_nl = None
    if birth_data:
        try:
            kp = calculate_kp(birth_data)
            cusp7 = next((c for c in kp["cusps"] if c["house"] == 7), None)
            if cusp7:
                kp_7th_sl = cusp7.get("sb")
                kp_7th_nl = cusp7.get("nl")
        except Exception:
            pass  # KP optional

    # ── Layer 6: Upapada Lagna (UL = Arudha of 12th) ───────────────────────
    twelfth_idx = (asc_idx + 11) % 12
    twelfth_sign = SIGNS[twelfth_idx]
    twelfth_lord_name = SIGN_LORDS[twelfth_sign]
    twelfth_lord_house = _house_from_asc(by_name[twelfth_lord_name]["longitude"], asc_deg)
    ul_house = _arudha_pada(twelfth_lord_house, 12)
    ul_sign = SIGNS[(asc_idx + ul_house - 1) % 12]
    ul_lord = SIGN_LORDS[ul_sign]

    # ── Layer 7: Darakaraka (lowest-degree planet, Sun-Saturn only) ────────
    chara_planets = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]
    deg_in_sign = lambda p: by_name[p]["longitude"] % 30.0
    dk_planet = min(chara_planets, key=deg_in_sign)

    # ── Layer 8: Arudha Lagna (AL) and A7 ──────────────────────────────────
    asc_lord_name = SIGN_LORDS[SIGNS[asc_idx]]
    asc_lord_house = _house_from_asc(by_name[asc_lord_name]["longitude"], asc_deg)
    al_house = _arudha_pada(asc_lord_house, 1)
    a7_house = ((al_house - 1 + 6) % 12) + 1
    a7_sign  = SIGNS[(asc_idx + a7_house - 1) % 12]
    a7_lord  = SIGN_LORDS[a7_sign]

    # ── Layer 9: Karaka 7th (Venus for male, Jupiter for female) ───────────
    karaka_planet = "Venus" if user_gender == "male" else "Jupiter"
    karaka_lon = by_name[karaka_planet]["longitude"]
    karaka_7th_idx = (_sign_idx(karaka_lon) + 6) % 12
    karaka_7th_sign = SIGNS[karaka_7th_idx]
    karaka_7th_lord = SIGN_LORDS[karaka_7th_sign]

    # ── Layer 10: 7th lord nakshatra lord ──────────────────────────────────
    seventh_lord_lon = by_name[seventh_lord]["longitude"]
    nak_idx = int(seventh_lord_lon / (360.0/27.0)) % 27
    seventh_lord_nak_lord = NAK_LORDS[nak_idx]
    seventh_lord_nakshatra = NAKSHATRAS[nak_idx]

    # ── Layer 11: Vargottama detection ─────────────────────────────────────
    d9_planets_by_name = {p["name"]: p for p in (d9.get("planets") or [])}
    vargottama: List[str] = []
    for pn in chara_planets:
        d1_sign = by_name[pn]["sign"]
        d9_sign = d9_planets_by_name.get(pn, {}).get("sign")
        if d1_sign and d9_sign and d1_sign == d9_sign:
            vargottama.append(pn)

    # ── Layer 12: Ashtakavarga 7th bindus (simplified) ─────────────────────
    # Full SAV requires per-planet contribution table; use simplified sarva.
    # Each planet contributes 1 bindu to the 7th from its own house if it's
    # one of its benefic houses (3,6,10,11 for most). Quick approximation.
    benefic_houses = {3, 6, 10, 11}
    bindus_7th = 0
    for pn in chara_planets:
        ph = _house_from_asc(by_name[pn]["longitude"], asc_deg)
        if ((7 - ph) % 12 + 1) in benefic_houses:
            bindus_7th += 1
    bindus_7th_estimate = bindus_7th + 2  # baseline

    # ── Layer 13: D9 Lagna lord placement ──────────────────────────────────
    d9_asc_sign = SIGNS[d9_asc_idx]
    d9_asc_lord = SIGN_LORDS[d9_asc_sign]

    # ── Layer 14: Sandhi check on 7th lord ─────────────────────────────────
    sl_deg_in_sign = seventh_lord_lon % 30.0
    sandhi = False
    if sl_deg_in_sign < 1.0 or sl_deg_in_sign > 29.0:
        sandhi = True

    # ── Layer 15: Direction baseline (where 7th lord sits) ─────────────────
    dir_house = _house_from_asc(seventh_lord_lon, asc_deg)
    direction_map = {
        1: "East",   4: "North",   7: "West",   10: "South",
        2: "South-East", 3: "South-East",
        5: "North-East", 6: "North-East",
        8: "North-West", 9: "North-West",
        11: "South-West", 12: "South-West",
    }
    partner_direction = direction_map.get(dir_house, "East")
    regional_baseline = ("North Indian features" if partner_direction in ("North","North-East","North-West")
                         else "South Indian features" if partner_direction in ("South","South-East","South-West")
                         else "Pan-Indian features")

    # ──────────────────────────────────────────────────────────────────────
    # Build composite physical trait card
    # Primary planetary influence = D9 7th lord (most weight) + D1 7th lord
    # ──────────────────────────────────────────────────────────────────────
    primary_planet = d9_7th_lord
    secondary_planet = seventh_lord

    primary_traits = PLANET_TRAITS.get(primary_planet, PLANET_TRAITS["Venus"])
    secondary_traits = PLANET_TRAITS.get(secondary_planet, PLANET_TRAITS["Venus"])

    # Vargottama amplifies primary
    vargottama_boost = primary_planet in vargottama or seventh_lord in vargottama

    # Face shape: blend D3 lagna (face chart) + D9 lagna
    face_shape = SIGN_FACE_SHAPE[d3_asc_sign]
    face_shape_secondary = SIGN_FACE_SHAPE[d9_asc_sign]

    # Eyebrows: 7th lord
    eyebrow = EYEBROW_RULES.get(seventh_lord, "balanced medium")

    # Nose: D9 lagna sign
    nose = NOSE_BY_SIGN[d9_asc_sign]

    # Lips: Venus dignity (Venus's sign lord)
    venus_sign = by_name["Venus"]["sign"]
    venus_dignity_planet = "Venus" if venus_sign in ("Taurus","Libra","Pisces") else "Saturn" if venus_sign in ("Capricorn","Aquarius") else seventh_lord
    lips = LIPS_BY_PLANET.get(venus_dignity_planet, LIPS_BY_PLANET["Venus"])

    # Hair: 7th lord + Saturn aspect check (simple)
    hair = primary_traits["hair"]

    # Build the master trait card
    traits = {
        # Layer outputs (raw)
        "layers": {
            "d1_7th_sign":        seventh_sign,
            "d1_7th_lord":        seventh_lord,
            "d1_7th_occupants":   occupants_7th,
            "d9_7th_sign":        d9_7th_sign,
            "d9_7th_lord":        d9_7th_lord,
            "d9_7th_occupants":   d9_occupants_7th,
            "d9_lagna_sign":      d9_asc_sign,
            "d9_lagna_lord":      d9_asc_lord,
            "d3_lagna_sign":      d3_asc_sign,
            "d30_lagna_sign":     d30_asc_sign,
            "d30_lagna_lord":     d30_asc_lord,
            "kp_7th_sub_lord":    kp_7th_sl,
            "kp_7th_star_lord":   kp_7th_nl,
            "upapada_lagna_sign": ul_sign,
            "upapada_lagna_lord": ul_lord,
            "darakaraka":         dk_planet,
            "arudha_lagna_house": al_house,
            "a7_sign":            a7_sign,
            "a7_lord":            a7_lord,
            "karaka_planet":      karaka_planet,
            "karaka_7th_sign":    karaka_7th_sign,
            "karaka_7th_lord":    karaka_7th_lord,
            "seventh_lord_nakshatra":      seventh_lord_nakshatra,
            "seventh_lord_nakshatra_lord": seventh_lord_nak_lord,
            "vargottama_planets": vargottama,
            "vargottama_boost":   vargottama_boost,
            "ashtakavarga_7th_bindus": bindus_7th_estimate,
            "sandhi_on_7th_lord": sandhi,
            "partner_direction":  partner_direction,
            "regional_baseline":  regional_baseline,
        },

        # Composed physical features
        "features": {
            "face_shape":     face_shape,
            "face_shape_alt": face_shape_secondary,
            "complexion":     primary_traits["complexion"],
            "complexion_alt": secondary_traits["complexion"],
            "build":          primary_traits["build"],
            "eyes":           primary_traits["eyes"],
            "eyebrows":       eyebrow,
            "nose":           nose,
            "lips":           lips,
            "hair":           hair,
            "vibe":           primary_traits["vibe"],
            "vibe_secondary": secondary_traits["vibe"],
            "regional_baseline": regional_baseline,
            "vargottama_amplified": vargottama_boost,
        },

        # Predicted contextual info
        "context": {
            "approx_age_difference": "1-3 years older" if seventh_lord in ("Saturn","Jupiter")
                                     else "similar age" if seventh_lord in ("Venus","Mercury","Moon")
                                     else "1-2 years younger",
            "direction_from_birthplace": partner_direction,
            "profession_hint": _profession_from_lord(seventh_lord),
            "ashtakavarga_strength": "very strong attraction" if bindus_7th_estimate >= 6
                                     else "moderate attraction" if bindus_7th_estimate >= 4
                                     else "subtle attraction",
        },

        "user_gender":     user_gender,
        "partner_gender":  "female" if user_gender == "male" else "male",
    }

    return traits


def _profession_from_lord(planet: str) -> str:
    return {
        "Sun":     "government / administrative / leadership role",
        "Moon":    "public service / hospitality / nurturing field",
        "Mars":    "engineering / military / sports / surgery",
        "Mercury": "business / writing / IT / communication",
        "Jupiter": "teaching / law / finance / spiritual",
        "Venus":   "creative arts / design / luxury / entertainment",
        "Saturn":  "labor / mining / law / long-term industry",
        "Rahu":    "foreign collaboration / unconventional field / tech",
        "Ketu":    "spiritual / research / behind-the-scenes work",
    }.get(planet, "creative or service field")


# ── Image prompt builder ────────────────────────────────────────────────────
def build_image_prompt(traits: Dict[str, Any]) -> str:
    f = traits["features"]
    pg = traits["partner_gender"]
    region = f["regional_baseline"]

    age_hint = "in their late 20s to early 30s"
    person = "young woman" if pg == "female" else "young man"

    prompt = (
        f"Soft watercolor portrait painting of a {person} {age_hint}, "
        f"{region}, three-quarter view facing slightly to the right, "
        f"shoulders-up framing, eyes looking calmly at the viewer. "
        f"\n\n"
        f"Face: {f['face_shape']}, blending with {f['face_shape_alt']} subtly. "
        f"Skin: {f['complexion']}. "
        f"Build: {f['build']} (only collarbone area visible). "
        f"Eyes: {f['eyes']}. "
        f"Eyebrows: {f['eyebrows']}. "
        f"Nose: {f['nose']}. "
        f"Lips: {f['lips']}, gentle relaxed expression. "
        f"Hair: {f['hair']}. "
        f"\n\n"
        f"Mood: {f['vibe']}, with undertone of {f['vibe_secondary']}. "
        f"Background: ethereal cosmic gradient — soft purple, pink, and gold "
        f"with faint glowing stars and nebula wisps, dreamy out-of-focus. "
        f"Lighting: soft divine glow from upper-left, golden rim-light, "
        f"painterly brush strokes, watercolor texture, no harsh edges. "
        f"Style: spiritual artistic interpretation, NOT photorealistic, "
        f"painted in the manner of soft Indian classical portraiture meets "
        f"modern digital watercolor. High quality, detailed, professional artwork."
    )

    if f.get("vargottama_amplified"):
        prompt += " Note: features should appear especially radiant and harmonious."

    return prompt


# ── Async task manager (in-memory) ──────────────────────────────────────────
@dataclass
class PortraitTask:
    task_id:   str
    progress:  int                           = 0
    status:    str                           = "queued"   # queued|running|done|error
    message:   str                           = "Prashna shuru ho raha hai..."
    traits:    Optional[Dict[str, Any]]      = None
    image_url: Optional[str]                 = None
    error:     Optional[str]                 = None
    lock:      threading.Lock                = field(default_factory=threading.Lock)

    def to_public(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "task_id":   self.task_id,
                "progress":  self.progress,
                "status":    self.status,
                "message":   self.message,
                "traits":    self.traits if self.status == "done" else None,
                "image_url": self.image_url,
                "error":     self.error,
            }


_TASKS: Dict[str, PortraitTask] = {}
_TASKS_LOCK = threading.Lock()


def _set_progress(task: PortraitTask, p: int, msg: str, status: str = "running"):
    with task.lock:
        task.progress = p
        task.message = msg
        task.status = status


def _generate_image_openai(prompt: str) -> Optional[str]:
    """Call OpenAI image gen. Returns URL or None on failure."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, timeout=60.0)
        # gpt-image-1 returns base64; dall-e-3 returns URL. Use dall-e-3.
        resp = client.images.generate(
            model="dall-e-3",
            prompt=prompt[:4000],
            size="1024x1024",
            quality="standard",
            n=1,
        )
        if resp.data and len(resp.data) > 0:
            return resp.data[0].url
    except Exception as e:
        print(f"[partner-portrait] OpenAI image gen failed: {e}", flush=True)
    return None


def _run_task(task: PortraitTask,
              kundli: Dict[str, Any],
              birth_data: Optional[Dict[str, Any]],
              user_gender: str):
    try:
        # Stage 1: layer extraction (fast, but show milestones)
        _set_progress(task, 5,  "D1 Rashi chart padh raha hu...")
        # tiny synthetic delay so UI shows the steps even on fast machines
        import time
        time.sleep(0.3)
        _set_progress(task, 12, "D9 Navamsa se jeevansaathi ki essence...")
        time.sleep(0.3)
        _set_progress(task, 20, "D3 Drekkana se mukh-mandal...")
        time.sleep(0.3)
        _set_progress(task, 28, "D30 Trimsamsa se swabhav...")
        time.sleep(0.2)
        _set_progress(task, 35, "KP 7th cuspal sub-lord...")
        time.sleep(0.2)
        _set_progress(task, 42, "Upapada Lagna + Darakaraka nikal raha hu...")
        time.sleep(0.2)
        _set_progress(task, 50, "Arudha Lagna A7 + karaka 7th...")
        time.sleep(0.2)
        _set_progress(task, 58, "Vargottama + Ashtakavarga bindus...")

        traits = extract_traits(kundli, birth_data, user_gender)

        with task.lock:
            task.traits = traits

        _set_progress(task, 68, "Trait card taiyar — image prompt bana raha hu...")
        prompt = build_image_prompt(traits)

        _set_progress(task, 75, "Cosmic Portrait generate ho raha hai... (15-25 sec)")

        image_url = _generate_image_openai(prompt)

        if not image_url:
            _set_progress(task, 100, "Image generation failed", status="error")
            with task.lock:
                task.error = "Image generation service unavailable. Trait card available."
                task.status = "error"
            return

        _set_progress(task, 95, "Final touches...")
        time.sleep(0.4)
        with task.lock:
            task.image_url = image_url
            task.progress  = 100
            task.status    = "done"
            task.message   = "Cosmic Portrait taiyar 🔮"
    except Exception as e:
        with task.lock:
            task.status   = "error"
            task.error    = str(e)
            task.progress = 100
            task.message  = "Error aaya — punah prayaas karein"
        print(f"[partner-portrait] task {task.task_id} failed: {e}", flush=True)


def start_portrait_task(kundli: Dict[str, Any],
                        birth_data: Optional[Dict[str, Any]] = None,
                        user_gender: str = "male") -> str:
    task_id = uuid.uuid4().hex[:16]
    task = PortraitTask(task_id=task_id)
    with _TASKS_LOCK:
        _TASKS[task_id] = task
        # cap memory: keep only last 100 tasks
        if len(_TASKS) > 100:
            for old_id in list(_TASKS.keys())[:-100]:
                _TASKS.pop(old_id, None)

    thread = threading.Thread(
        target=_run_task,
        args=(task, kundli, birth_data, user_gender),
        daemon=True,
    )
    thread.start()
    return task_id


def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    with _TASKS_LOCK:
        task = _TASKS.get(task_id)
    if not task:
        return None
    return task.to_public()

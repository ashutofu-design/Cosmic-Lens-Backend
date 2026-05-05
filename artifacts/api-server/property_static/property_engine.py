"""Property facts engine — deterministic 4-dim computation from kundli.

ZERO LLM inference. Pure rule-based Vedic logic.

Output shape:
  {
    "dimensions": {
      "yog":       {"verdict": "STRONG|MODERATE|WEAK", "score": int, "reason": str},
      "capacity":  {"verdict": "STRONG|MODERATE|WEAK", "score": int, "reason": str},
      "risk":      {"verdict": "CLEAN|CAUTION|HIGH_RISK", "score": int, "reason": str},
      "type_fit":  {"best": str, "alt": str, "reason": str},
    },
    "engine_version": "P1.0",
    "scope": "non_timing",
  }

Internal facts (planet/house/sign) are NEVER exposed in the `reason`
fields — those use plain Hinglish ("ghar/zameen ka base", "wealth flow",
"documentation caution") so the signal-pack can be sent to LLM safely.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

ENGINE_VERSION = "P1.0"
SCOPE = "non_timing"

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn",
         "Aquarius", "Pisces"]
_SIGN_IDX = {s.lower(): i for i, s in enumerate(SIGNS)}

SIGN_LORD = {
    "Aries": "Mars",       "Taurus": "Venus",     "Gemini": "Mercury",
    "Cancer": "Moon",      "Leo": "Sun",          "Virgo": "Mercury",
    "Libra": "Venus",      "Scorpio": "Mars",     "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn",  "Pisces": "Jupiter",
}

EXALT = {"Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
         "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
         "Saturn": "Libra"}
DEBIL = {"Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
         "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo",
         "Saturn": "Aries"}
OWN = {
    "Sun": {"Leo"}, "Moon": {"Cancer"},
    "Mars": {"Aries", "Scorpio"},
    "Mercury": {"Gemini", "Virgo"},
    "Jupiter": {"Sagittarius", "Pisces"},
    "Venus": {"Taurus", "Libra"},
    "Saturn": {"Capricorn", "Aquarius"},
}

# Karakas
KARAKA_LAND     = "Mars"     # land/plot
KARAKA_HOME     = "Moon"     # home / family / ancestral
KARAKA_REALEST  = "Saturn"   # immovable assets, rentals, old property
KARAKA_LUXURY   = "Venus"    # luxury, comfort, decoration
KARAKA_WEALTH   = "Jupiter"  # wealth, growth
KARAKA_PROPERTY_HOUSES = (4, 2, 11)  # 4=home, 2=accumulated assets, 11=gains

DUSTHANA = {6, 8, 12}
KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────
def _canon_sign(s: Any) -> str:
    if not s:
        return ""
    s = str(s).strip().title()
    # Common Sanskrit names → English
    sanskrit = {
        "Mesh": "Aries", "Mesha": "Aries",
        "Vrish": "Taurus", "Vrishabh": "Taurus", "Vrushabh": "Taurus",
        "Mithun": "Gemini",
        "Kark": "Cancer", "Karka": "Cancer",
        "Singh": "Leo", "Simha": "Leo",
        "Kanya": "Virgo",
        "Tula": "Libra",
        "Vrishchik": "Scorpio", "Vrischik": "Scorpio",
        "Dhanu": "Sagittarius",
        "Makar": "Capricorn",
        "Kumbh": "Aquarius",
        "Meen": "Pisces",
    }
    return sanskrit.get(s, s)


def _ascendant_sign(kundli: dict) -> str:
    asc = kundli.get("ascendant") or kundli.get("lagna")
    if isinstance(asc, dict):
        asc = asc.get("sign", "")
    return _canon_sign(asc)


def _planet_index(planets: List[dict]) -> Dict[str, dict]:
    """Build {PlanetName: {house, sign, retrograde, ...}} dict."""
    out: Dict[str, dict] = {}
    for p in planets or []:
        if not isinstance(p, dict):
            continue
        name = str(p.get("name", "")).strip().title()
        if not name:
            continue
        out[name] = {
            "house":      p.get("house"),
            "sign":       _canon_sign(p.get("sign")),
            "retrograde": bool(p.get("retrograde")),
        }
    return out


def _sign_at_house(asc_sign: str, house: int) -> str:
    """Whole-sign: sign at Nth house from given lagna."""
    idx = _SIGN_IDX.get(asc_sign.lower())
    if idx is None:
        return ""
    return SIGNS[(idx + house - 1) % 12]


def _house_lord(asc_sign: str, house: int) -> str:
    sign = _sign_at_house(asc_sign, house)
    return SIGN_LORD.get(sign, "")


def _dignity(planet: str, sign: str) -> str:
    """Returns: exalted | debilitated | own | neutral | ''."""
    if not planet or not sign:
        return ""
    if EXALT.get(planet) == sign:
        return "exalted"
    if DEBIL.get(planet) == sign:
        return "debilitated"
    if sign in OWN.get(planet, set()):
        return "own"
    return "neutral"


def _planet_house(pidx: dict, planet: str) -> Optional[int]:
    p = pidx.get(planet) or {}
    h = p.get("house")
    return int(h) if isinstance(h, int) else None


def _planet_sign(pidx: dict, planet: str) -> str:
    p = pidx.get(planet) or {}
    return p.get("sign", "")


def _occupants_of(pidx: dict, house: int) -> List[str]:
    return [p for p, d in pidx.items()
            if d.get("house") == house and p in {
                "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                "Saturn", "Rahu", "Ketu",
            }]


# ──────────────────────────────────────────────────────────────────────
# DIM 1 — YOG (4H foundation + land/home karaka + Saturn for stability)
# ──────────────────────────────────────────────────────────────────────
def _compute_yog(asc: str, pidx: dict) -> dict:
    score = 0
    notes: List[str] = []

    # 4H lord position + dignity
    l4 = _house_lord(asc, 4)
    if l4:
        h_l4 = _planet_house(pidx, l4)
        s_l4 = _planet_sign(pidx, l4)
        dig = _dignity(l4, s_l4)
        if dig == "exalted":
            score += 3; notes.append("4H_LORD_EXALTED")
        elif dig == "own":
            score += 2; notes.append("4H_LORD_OWN")
        elif dig == "debilitated":
            score -= 2; notes.append("4H_LORD_DEBIL")
        if h_l4 in KENDRA or h_l4 in TRIKONA:
            score += 2; notes.append(f"4H_LORD_IN_GOOD_HOUSE_{h_l4}")
        elif h_l4 in DUSTHANA:
            score -= 2; notes.append(f"4H_LORD_IN_DUSTHANA_{h_l4}")

    # 4H occupants — benefics good, malefics afflict
    occ4 = _occupants_of(pidx, 4)
    benefics = {"Jupiter", "Venus", "Mercury"}
    malefics = {"Mars", "Saturn", "Rahu", "Ketu"}
    for p in occ4:
        if p in benefics:
            dig = _dignity(p, _planet_sign(pidx, p))
            if dig in ("exalted", "own"):
                score += 2; notes.append(f"4H_BENEFIC_{p}_STRONG")
            elif dig != "debilitated":
                score += 1; notes.append(f"4H_BENEFIC_{p}")
            else:
                notes.append(f"4H_BENEFIC_{p}_DEBIL")
        elif p in malefics:
            dig = _dignity(p, _planet_sign(pidx, p))
            if p == "Mars" and dig in ("exalted", "own"):
                # Strong Mars in 4H = land karaka active (mixed but
                # treated mildly positive for plot/land Qs)
                score += 1; notes.append("4H_MARS_STRONG_LAND_KARAKA")
            else:
                score -= 1; notes.append(f"4H_MALEFIC_{p}")

    # Land karaka Mars dignity
    s_mars = _planet_sign(pidx, "Mars")
    dig_mars = _dignity("Mars", s_mars)
    if dig_mars == "exalted":
        score += 2; notes.append("MARS_EXALTED")
    elif dig_mars == "own":
        score += 1; notes.append("MARS_OWN")
    elif dig_mars == "debilitated":
        score -= 1; notes.append("MARS_DEBIL")

    # Saturn (immovable assets) dignity
    s_sat = _planet_sign(pidx, "Saturn")
    dig_sat = _dignity("Saturn", s_sat)
    if dig_sat == "exalted":
        score += 2; notes.append("SATURN_EXALTED_STABILITY")
    elif dig_sat == "own":
        score += 1; notes.append("SATURN_OWN_STABILITY")
    elif dig_sat == "debilitated":
        score -= 1; notes.append("SATURN_DEBIL_INSTABILITY")

    # Verdict
    if score >= 4:
        v = "STRONG"
        reason = "Ghar/zameen ka base supportive hai, foundation stable hai."
    elif score >= 0:
        v = "MODERATE"
        reason = "Ghar/zameen ka base mixed hai, kuch support kuch caution."
    else:
        v = "WEAK"
        reason = "Ghar/zameen ka base abhi weak hai, foundation me kami."
    return {"verdict": v, "score": score, "reason": reason,
            "_notes": notes}


# ──────────────────────────────────────────────────────────────────────
# DIM 2 — CAPACITY (2H accumulated wealth + 11H gains + Jupiter)
# ──────────────────────────────────────────────────────────────────────
def _compute_capacity(asc: str, pidx: dict) -> dict:
    score = 0
    notes: List[str] = []

    # 2H lord (accumulated wealth)
    l2 = _house_lord(asc, 2)
    if l2:
        h_l2 = _planet_house(pidx, l2)
        dig = _dignity(l2, _planet_sign(pidx, l2))
        if dig == "exalted": score += 3; notes.append("2H_LORD_EXALTED")
        elif dig == "own":   score += 2; notes.append("2H_LORD_OWN")
        elif dig == "debilitated": score -= 2; notes.append("2H_LORD_DEBIL")
        if h_l2 in KENDRA or h_l2 in TRIKONA: score += 2
        elif h_l2 in DUSTHANA:                score -= 2

    # 11H lord (gains, income flow)
    l11 = _house_lord(asc, 11)
    if l11:
        h_l11 = _planet_house(pidx, l11)
        dig = _dignity(l11, _planet_sign(pidx, l11))
        if dig == "exalted": score += 3; notes.append("11H_LORD_EXALTED")
        elif dig == "own":   score += 2; notes.append("11H_LORD_OWN")
        elif dig == "debilitated": score -= 2; notes.append("11H_LORD_DEBIL")
        if h_l11 in KENDRA or h_l11 in TRIKONA: score += 2
        elif h_l11 in DUSTHANA:                 score -= 2

    # Jupiter dignity (wealth karaka)
    dig_jup = _dignity("Jupiter", _planet_sign(pidx, "Jupiter"))
    if dig_jup == "exalted": score += 2; notes.append("JUPITER_EXALTED")
    elif dig_jup == "own":   score += 1; notes.append("JUPITER_OWN")
    elif dig_jup == "debilitated": score -= 1; notes.append("JUPITER_DEBIL")

    # Dhana yoga: 2L+11L conjunct or mutual aspect (simplified: same house)
    if l2 and l11 and l2 != l11:
        h2, h11 = _planet_house(pidx, l2), _planet_house(pidx, l11)
        if h2 and h11 and h2 == h11:
            score += 2; notes.append("DHANA_YOGA_2L_11L_CONJ")

    # Lakshmi yoga: 9L in own/exalted (simplified)
    l9 = _house_lord(asc, 9)
    if l9:
        dig = _dignity(l9, _planet_sign(pidx, l9))
        if dig in ("exalted", "own"):
            score += 1; notes.append(f"9H_LORD_{dig.upper()}_LAKSHMI")

    if score >= 5:
        v = "STRONG"
        reason = "Wealth flow aur saving capacity supportive hai."
    elif score >= 0:
        v = "MODERATE"
        reason = "Capacity moderate hai, planning ke saath chal sakta hai."
    else:
        v = "WEAK"
        reason = "Capacity abhi weak hai, foundation pehle mazboot karein."
    return {"verdict": v, "score": score, "reason": reason,
            "_notes": notes}


# ──────────────────────────────────────────────────────────────────────
# DIM 3 — RISK (6H/8H/12H influence on 4H + Rahu/Ketu in 4H + affliction)
# ──────────────────────────────────────────────────────────────────────
def _compute_risk(asc: str, pidx: dict) -> dict:
    risk = 0
    notes: List[str] = []

    # Dusthana lords (6/8/12) sitting in 4H?
    for hn in (6, 8, 12):
        ld = _house_lord(asc, hn)
        if ld and _planet_house(pidx, ld) == 4:
            risk += 2; notes.append(f"DUSTHANA_LORD_{hn}_IN_4H")

    # 4H lord in dusthana (own house weakened)
    l4 = _house_lord(asc, 4)
    if l4:
        h_l4 = _planet_house(pidx, l4)
        if h_l4 in DUSTHANA:
            risk += 2; notes.append(f"4H_LORD_IN_DUSTHANA_{h_l4}")
        # 4H lord debilitated
        if _dignity(l4, _planet_sign(pidx, l4)) == "debilitated":
            risk += 1; notes.append("4H_LORD_DEBIL_RISK")

    # Rahu/Ketu in 4H — sudden disputes / unconventional asset
    occ4 = _occupants_of(pidx, 4)
    if "Rahu" in occ4: risk += 2; notes.append("RAHU_IN_4H")
    if "Ketu" in occ4: risk += 2; notes.append("KETU_IN_4H")

    # Mars-Saturn affliction on 4H — both must occupy or cast a special
    # aspect on 4H (authentic Vedic aspect rules):
    #   Mars special aspects: 4th, 7th, 8th from itself
    #     → Mars in house H aspects 4H if H in {4, 1, 10, 9}
    #       (i.e. 4-3=1, 4-6=10 wraps, 4-7=9 wraps)
    #   Saturn special aspects: 3rd, 7th, 10th from itself
    #     → Saturn in house H aspects 4H if H in {4, 2, 10, 7}
    #       (i.e. 4-2=2, 4-6=10 wraps, 4-9=7 wraps)
    mars_h = _planet_house(pidx, "Mars")
    sat_h  = _planet_house(pidx, "Saturn")
    mars_hits_4h = mars_h in (4, 1, 9, 10)
    sat_hits_4h  = sat_h  in (4, 2, 7, 10)
    if mars_hits_4h and sat_hits_4h:
        risk += 2; notes.append("MARS_SATURN_AFFLICT_4H")

    # Sun in 4H — heart of home weakened (mild risk)
    if "Sun" in occ4:
        risk += 1; notes.append("SUN_IN_4H_MILD")

    if risk >= 5:
        v = "HIGH_RISK"
        reason = ("Dispute/legal aur documentation me extra dhyan zaroori, "
                  "risk visible hai.")
    elif risk >= 2:
        v = "CAUTION"
        reason = ("Documentation, legal verification aur planning me "
                  "caution zaroori.")
    else:
        v = "CLEAN"
        reason = "Major risk indicator nahi dikh raha, base clean hai."
    return {"verdict": v, "score": risk, "reason": reason,
            "_notes": notes}


# ──────────────────────────────────────────────────────────────────────
# DIM 4 — TYPE_FIT (which property style fits best)
# ──────────────────────────────────────────────────────────────────────
def _compute_type_fit(asc: str, pidx: dict) -> dict:
    """Mars dominant → plot/land; Venus → luxury; Saturn → old/rental;
    Moon → ancestral/family home; balanced → new home."""
    weights = {"plot": 0, "luxury": 0, "rental": 0,
               "ancestral": 0, "new_home": 1}  # mild default
    notes: List[str] = []

    def _strength(planet: str) -> int:
        s = _planet_sign(pidx, planet)
        h = _planet_house(pidx, planet)
        score = 0
        dig = _dignity(planet, s)
        if dig == "exalted": score += 3
        elif dig == "own":   score += 2
        elif dig == "debilitated": score -= 2
        if h in KENDRA or h in TRIKONA: score += 1
        if h in DUSTHANA:               score -= 1
        return score

    mars_s = _strength("Mars")
    venus_s = _strength("Venus")
    sat_s = _strength("Saturn")
    moon_s = _strength("Moon")

    weights["plot"]      += max(0, mars_s)
    weights["luxury"]    += max(0, venus_s)
    weights["rental"]    += max(0, sat_s)
    weights["ancestral"] += max(0, moon_s)

    # 4H occupants influence
    occ4 = _occupants_of(pidx, 4)
    if "Mars" in occ4:    weights["plot"] += 1; notes.append("MARS_IN_4H")
    if "Venus" in occ4:   weights["luxury"] += 1; notes.append("VENUS_IN_4H")
    if "Saturn" in occ4:  weights["rental"] += 1; notes.append("SATURN_IN_4H")
    if "Moon" in occ4:    weights["ancestral"] += 1; notes.append("MOON_IN_4H")
    if "Jupiter" in occ4: weights["new_home"] += 1; notes.append("JUPITER_IN_4H")

    sorted_types = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
    best = sorted_types[0][0]
    alt  = sorted_types[1][0] if len(sorted_types) > 1 else best

    type_label = {
        "plot":      "plot/zameen",
        "new_home":  "new home/flat",
        "luxury":    "luxury/spacious home",
        "rental":    "rental/old property",
        "ancestral": "ancestral/family home",
    }
    reason = (f"Aapke chart me {type_label.get(best, best)} ka indication "
              f"sabse strong hai.")
    return {"best": best, "alt": alt, "reason": reason,
            "_weights": weights, "_notes": notes}


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────
def compute_property_facts(kundli: dict) -> dict:
    """Returns deterministic 4-dim property facts.

    Defensive: if kundli is missing critical fields, returns a
    failsafe dict with all dims = WEAK/CAUTION/etc and a reason
    explaining the data gap (caller decides how to surface this)."""
    if not isinstance(kundli, dict):
        return _failsafe("Kundli data missing.")
    asc = _ascendant_sign(kundli)
    planets = kundli.get("planets") or []
    if not asc or not planets:
        return _failsafe("Lagna ya planet data missing.")

    pidx = _planet_index(planets)

    yog      = _compute_yog(asc, pidx)
    capacity = _compute_capacity(asc, pidx)
    risk     = _compute_risk(asc, pidx)
    type_fit = _compute_type_fit(asc, pidx)

    return {
        "dimensions": {
            "yog":      yog,
            "capacity": capacity,
            "risk":     risk,
            "type_fit": type_fit,
        },
        "engine_version": ENGINE_VERSION,
        "scope": SCOPE,
    }


def _failsafe(msg: str) -> dict:
    return {
        "dimensions": {
            "yog":      {"verdict": "UNKNOWN", "score": 0,
                         "reason": "Data gap — clear analysis nahi mil rahi."},
            "capacity": {"verdict": "UNKNOWN", "score": 0,
                         "reason": "Data gap — clear analysis nahi mil rahi."},
            "risk":     {"verdict": "UNKNOWN", "score": 0,
                         "reason": "Data gap — caution default."},
            "type_fit": {"best": "new_home", "alt": "plot",
                         "reason": "Default fit (data limited)."},
        },
        "engine_version": ENGINE_VERSION,
        "scope": SCOPE,
        "failsafe_reason": msg,
    }

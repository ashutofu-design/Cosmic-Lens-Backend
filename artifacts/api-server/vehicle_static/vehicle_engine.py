"""Vehicle facts engine — deterministic dims from kundli (4H/Venus/Mars/11H)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

ENGINE_VERSION = "V1.0"
SCOPE = "non_timing"

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_SIGN_IDX = {s.lower(): i for i, s in enumerate(SIGNS)}

SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

EXALT = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
    "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
    "Saturn": "Libra",
}
DEBIL = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
    "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo",
    "Saturn": "Aries",
}
OWN = {
    "Sun": {"Leo"}, "Moon": {"Cancer"},
    "Mars": {"Aries", "Scorpio"},
    "Mercury": {"Gemini", "Virgo"},
    "Jupiter": {"Sagittarius", "Pisces"},
    "Venus": {"Taurus", "Libra"},
    "Saturn": {"Capricorn", "Aquarius"},
}

DUSTHANA = {6, 8, 12}
KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}

_COLOUR_MAP = {
    "Venus": ["white", "silver", "cream", "pastel"],
    "Mars": ["red", "maroon", "copper"],
    "Saturn": ["black", "dark grey", "navy"],
    "Sun": ["gold", "copper", "orange"],
    "Moon": ["white", "pearl", "light blue"],
    "Mercury": ["green", "silver"],
    "Jupiter": ["yellow", "gold", "cream"],
}


def _canon_sign(s: Any) -> str:
    if not s:
        return ""
    s = str(s).strip().title()
    sanskrit = {
        "Mesh": "Aries", "Vrish": "Taurus", "Mithun": "Gemini",
        "Kark": "Cancer", "Singh": "Leo", "Kanya": "Virgo",
        "Tula": "Libra", "Vrishchik": "Scorpio", "Dhanu": "Sagittarius",
        "Makar": "Capricorn", "Kumbh": "Aquarius", "Meen": "Pisces",
    }
    return sanskrit.get(s, s)


def _ascendant_sign(kundli: dict) -> str:
    asc = kundli.get("ascendant") or kundli.get("lagna")
    if isinstance(asc, dict):
        asc = asc.get("sign", "")
    return _canon_sign(asc)


def _planet_index(planets: List[dict]) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for p in planets or []:
        if not isinstance(p, dict):
            continue
        name = str(p.get("name", "")).strip().title()
        if not name:
            continue
        out[name] = {
            "house": p.get("house"),
            "sign": _canon_sign(p.get("sign")),
            "retrograde": bool(p.get("retrograde")),
        }
    return out


def _sign_at_house(asc_sign: str, house: int) -> str:
    idx = _SIGN_IDX.get(asc_sign.lower())
    if idx is None:
        return ""
    return SIGNS[(idx + house - 1) % 12]


def _house_lord(asc_sign: str, house: int) -> str:
    return SIGN_LORD.get(_sign_at_house(asc_sign, house), "")


def _dignity(planet: str, sign: str) -> str:
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
    h = (pidx.get(planet) or {}).get("house")
    return int(h) if isinstance(h, int) else None


def _planet_sign(pidx: dict, planet: str) -> str:
    return (pidx.get(planet) or {}).get("sign", "")


def _dignity_score(planet: str, pidx: dict) -> int:
    dig = _dignity(planet, _planet_sign(pidx, planet))
    if dig == "exalted":
        return 3
    if dig == "own":
        return 2
    if dig == "debilitated":
        return -2
    return 0


def _compute_readiness(asc: str, pidx: dict) -> dict:
    score = 0
    l4 = _house_lord(asc, 4)
    l11 = _house_lord(asc, 11)
    for lord in (l4, l11):
        if not lord:
            continue
        score += _dignity_score(lord, pidx)
        h = _planet_house(pidx, lord)
        if h in KENDRA or h in TRIKONA:
            score += 2
        elif h in DUSTHANA:
            score -= 2
    score += _dignity_score("Venus", pidx)
    score += _dignity_score("Mars", pidx) // 2
    if score >= 5:
        v, reason = "STRONG", "Gaadi lene ki readiness supportive hai — 4H/11H + Shukra tone achha."
    elif score >= 1:
        v, reason = "MODERATE", "Readiness mixed hai — budget plan aur loan check dono zaroori."
    else:
        v, reason = "WEAK", "Abhi capacity tight dikhti hai — pehle savings/EMI plan mazboot karein."
    return {"verdict": v, "score": score, "reason": reason}


def _compute_safety(asc: str, pidx: dict) -> dict:
    risk = 0
    for hn in (6, 8, 12):
        ld = _house_lord(asc, hn)
        if ld and _planet_house(pidx, ld) == 4:
            risk += 2
    l4 = _house_lord(asc, 4)
    if l4 and _planet_house(pidx, l4) in DUSTHANA:
        risk += 2
    for p in ("Mars", "Rahu", "Saturn"):
        if _planet_house(pidx, p) == 4:
            risk += 1
    if _dignity("Mars", _planet_sign(pidx, "Mars")) == "debilitated":
        risk += 1
    if risk >= 4:
        v, reason = "HIGH_CAUTION", "Vehicle safety axis me extra caution — rash driving avoid, insurance strong rakhein."
    elif risk >= 2:
        v, reason = "MODERATE", "Mixed safety tone — discipline aur regular maintenance dono important."
    else:
        v, reason = "CLEAN", "Safety axis relatively clean — phir bhi practical driving discipline rakhein."
    return {"verdict": v, "score": risk, "reason": reason}


def _compute_luxury(asc: str, pidx: dict) -> dict:
    score = _dignity_score("Venus", pidx)
    h_ven = _planet_house(pidx, "Venus")
    if h_ven in KENDRA or h_ven in TRIKONA:
        score += 2
    l11 = _house_lord(asc, 11)
    if l11:
        score += _dignity_score(l11, pidx)
    if score >= 5:
        v, tier, reason = "STRONG", "luxury_premium", "Luxury/premium vehicle ka sukh chart me possible hai."
    elif score >= 2:
        v, tier, reason = "MODERATE", "mid_range", "Mid-range comfortable vehicle zyada fit dikhta hai."
    else:
        v, tier, reason = "BUDGET", "budget_practical", "Budget/practical vehicle chart ke saath zyada aligned hai."
    return {"verdict": v, "tier": tier, "score": score, "reason": reason}


def _compute_type_choice(asc: str, pidx: dict) -> dict:
    ven = _dignity_score("Venus", pidx)
    sat = _dignity_score("Saturn", pidx)
    mar = _dignity_score("Mars", pidx)
    mer = _dignity_score("Mercury", pidx)
    new_vs_used = "new" if ven >= 2 and sat >= 0 else "used_or_budget"
    two_vs_four = "four_wheeler" if ven + mar >= 3 else "two_wheeler_first"
    ev_vs_fuel = "ev_friendly" if mer >= 1 and ven >= 1 else "petrol_diesel_practical"
    return {
        "new_vs_used": new_vs_used,
        "two_vs_four": two_vs_four,
        "ev_vs_fuel": ev_vs_fuel,
        "reason": (
            f"Type fit heuristic: {'naya' if new_vs_used == 'new' else 'second-hand/budget'}; "
            f"{'4W' if two_vs_four == 'four_wheeler' else '2W pehle'}; "
            f"{'EV' if ev_vs_fuel == 'ev_friendly' else 'petrol/diesel'} — infra/budget decide karega."
        ),
    }


def _compute_colour(pidx: dict) -> dict:
    scores: Dict[str, int] = {}
    for planet in ("Venus", "Mars", "Saturn", "Sun", "Moon", "Mercury", "Jupiter"):
        scores[planet] = _dignity_score(planet, pidx)
        h = _planet_house(pidx, planet)
        if h in KENDRA:
            scores[planet] += 1
    best_planet = max(scores, key=lambda k: scores[k])
    colours = _COLOUR_MAP.get(best_planet, ["white", "silver"])
    alt_planet = sorted(scores, key=lambda k: scores[k], reverse=True)[1]
    alt = _COLOUR_MAP.get(alt_planet, ["silver"])[0]
    return {
        "best": colours[0],
        "alt": alt,
        "palette": colours[:3],
        "reason": (
            f"Colour tone: {colours[0]}/{alt} palette — aesthetic axis; lucky-shade guarantee nahi."
        ),
    }


def _compute_commercial(asc: str, pidx: dict) -> dict:
    score = 0
    for lord_h in (3, 10):
        ld = _house_lord(asc, lord_h)
        if ld:
            score += _dignity_score(ld, pidx)
    score += _dignity_score("Mercury", pidx)
    score += _dignity_score("Mars", pidx) // 2
    if score >= 4:
        v, reason = "SUITABLE", "Commercial vehicle/taxi-truck business ka yog mixed-supportive hai."
    elif score >= 1:
        v, reason = "MIXED", "Commercial use possible — license, route aur cashflow plan pehle clear karein."
    else:
        v, reason = "CAUTION", "Personal use pe focus better — commercial risk abhi zyada dikhta hai."
    return {"verdict": v, "score": score, "reason": reason}


def _compute_ownership(pidx: dict) -> dict:
    ven_score = _dignity_score("Venus", pidx)
    h_ven = _planet_house(pidx, "Venus")
    if ven_score >= 2 and h_ven not in DUSTHANA:
        mode, reason = "self_name", "Apne naam par gaadi lena chart se aligned dikhta hai."
    elif ven_score <= -1 or h_ven in DUSTHANA:
        mode, reason = "alternate_name", "Shukra weak/afflicted — family/business naam par option practical ho sakta hai."
    else:
        mode, reason = "either_ok", "Self ya company naam dono chal sakte hain — tax/legal advisor se confirm karein."
    return {"mode": mode, "reason": reason}


def compute_vehicle_facts(kundli: dict) -> dict:
    asc = _ascendant_sign(kundli if isinstance(kundli, dict) else {})
    planets = (kundli or {}).get("planets") or []
    pidx = _planet_index(planets if isinstance(planets, list) else [])
    return {
        "dimensions": {
            "readiness": _compute_readiness(asc, pidx),
            "safety": _compute_safety(asc, pidx),
            "luxury": _compute_luxury(asc, pidx),
            "type_choice": _compute_type_choice(asc, pidx),
            "colour": _compute_colour(pidx),
            "commercial": _compute_commercial(asc, pidx),
            "ownership": _compute_ownership(pidx),
        },
        "engine_version": ENGINE_VERSION,
        "scope": SCOPE,
    }

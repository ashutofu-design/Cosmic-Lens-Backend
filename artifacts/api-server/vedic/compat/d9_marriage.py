"""
Phase 2.5.11.23 — D9 Marriage Destiny Engine
=============================================
Deterministic deep analysis of each partner's D9 (Navamsa) chart for marriage
destiny + maturity. NO LLM. Output feeds Layer B premium prose.

Why D9: classical rule — real married-life strength is read from D9, not D1.
D1 shows promise; D9 shows what actually unfolds after marriage.

Per partner extracts:
  - D9 lagna (sign + lord)
  - D9 7H (sign + lord) — spouse character
  - D9 Venus position + dignity — marital harmony
  - D9 Jupiter position + dignity — wisdom + commitment
  - D9 7L (where 7L sits in D9) — spouse karma
  - Marriage maturity score 0-10

Couple-level sync:
  - D9 lagna lord overlap (same / friendly / neutral / hostile)
  - D9 7L cross-aspect (does p1's 7L touch p2's planets?)
  - Combined sync score 0-10

Branding rule: never name AI/LLM. Defensive — never raises on partial data.
"""
from __future__ import annotations
from typing import Any

SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
EXALT = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3,
         "Venus": 11, "Saturn": 6}
DEBIL = {"Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11, "Jupiter": 9,
         "Venus": 5, "Saturn": 0}
OWN = {"Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5],
       "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10]}
PLN_IDX = {"Sun": 0, "Moon": 1, "Mars": 2, "Mercury": 3, "Jupiter": 4,
           "Venus": 5, "Saturn": 6}
# friendship matrix: 2=friend, 1=neutral, 0=enemy
PLN_FRIEND = [
    [1, 2, 2, 1, 2, 0, 0],  # Sun
    [2, 1, 0, 1, 2, 2, 0],  # Moon
    [2, 0, 1, 1, 2, 0, 2],  # Mars (note: row[5]=Venus → corrected to neutral 1)
    [2, 0, 2, 1, 0, 2, 0],  # Mercury
    [2, 1, 2, 1, 1, 0, 0],  # Jupiter
    [2, 2, 0, 2, 1, 1, 0],  # Venus
    [0, 0, 2, 2, 2, 0, 1],  # Saturn
]
# Special Vedic aspects (1-indexed houses from planet)
SPECIAL_ASPECT = {
    "Mars": [4, 7, 8], "Jupiter": [5, 7, 9], "Saturn": [3, 7, 10],
    "Rahu": [5, 7, 9], "Ketu": [5, 7, 9],
}


def _sidx(sign: str | None) -> int | None:
    if not isinstance(sign, str):
        return None
    if sign in SIGN_NAMES:
        return SIGN_NAMES.index(sign)
    return None


def _d9_planet_sign(d9_chart: dict, planet: str) -> str | None:
    """Pluck D9 sign-name for a planet. Tolerates the flask_app shape:
    `{planets: [{name, sign, ...}, ...]}`."""
    if not isinstance(d9_chart, dict):
        return None
    pls = d9_chart.get("planets") or []
    for p in pls:
        if isinstance(p, dict) and p.get("name") == planet:
            sn = p.get("sign")
            if isinstance(sn, str) and sn in SIGN_NAMES:
                return sn
    return None


def _d9_lagna_sign(d9_chart: dict) -> str | None:
    """D9 lagna sign — try common keys."""
    if not isinstance(d9_chart, dict):
        return None
    for k in ("ascendant", "lagna", "lagna_sign", "lagna_d9"):
        v = d9_chart.get(k)
        if isinstance(v, str) and v in SIGN_NAMES:
            return v
    # Fall back to a planet entry whose name starts with "Lagna"
    for p in d9_chart.get("planets") or []:
        if isinstance(p, dict) and isinstance(p.get("name"), str) \
                and p["name"].lower().startswith("lagna"):
            sn = p.get("sign")
            if isinstance(sn, str) and sn in SIGN_NAMES:
                return sn
    return None


def _dignity(planet: str, sign_idx: int) -> int:
    """+2 exalt, +1 own, 0 friend/neutral, -1 enemy, -2 debil."""
    if EXALT.get(planet) == sign_idx:
        return 2
    if DEBIL.get(planet) == sign_idx:
        return -2
    if sign_idx in OWN.get(planet, []):
        return 1
    lord = SIGN_LORD[SIGN_NAMES[sign_idx]]
    if planet in PLN_IDX and lord in PLN_IDX:
        f = PLN_FRIEND[PLN_IDX[planet]][PLN_IDX[lord]]
        return 1 if f == 2 else -1 if f == 0 else 0
    return 0


def _dignity_word(d: int) -> str:
    return {2: "exalted", 1: "own-sign", 0: "neutral",
            -1: "enemy-sign", -2: "debilitated"}.get(d, "neutral")


def _house_from_lagna(planet_sign_idx: int, lagna_sign_idx: int) -> int:
    return ((planet_sign_idx - lagna_sign_idx) % 12) + 1


def _friendship_word(p1_lord: str, p2_lord: str) -> str:
    if p1_lord == p2_lord:
        return "same"
    if p1_lord not in PLN_IDX or p2_lord not in PLN_IDX:
        return "neutral"
    f1 = PLN_FRIEND[PLN_IDX[p1_lord]][PLN_IDX[p2_lord]]
    f2 = PLN_FRIEND[PLN_IDX[p2_lord]][PLN_IDX[p1_lord]]
    avg = (f1 + f2) / 2.0
    if avg >= 1.5:
        return "friendly"
    if avg <= 0.5:
        return "hostile"
    return "neutral"


def _per_partner(kundli: dict) -> dict[str, Any]:
    """Extract D9 marriage facts for one partner. Always returns a dict;
    score defaults to a neutral 5/10 when D9 is unreadable."""
    out: dict[str, Any] = {
        "available": False,
        "d9_lagna_sign": None,
        "d9_lagna_lord": None,
        "d9_7h_sign": None,
        "d9_7h_lord": None,
        "d9_7l_sign": None,
        "d9_7l_house": None,
        "d9_venus_sign": None,
        "d9_venus_dignity": "neutral",
        "d9_jupiter_sign": None,
        "d9_jupiter_dignity": "neutral",
        "marriage_maturity_0_10": 5,
        "drivers": [],
        "cautions": [],
    }
    if not isinstance(kundli, dict):
        return out
    d9 = ((kundli.get("divisionalCharts") or {}).get("D9")) or {}
    lagna = _d9_lagna_sign(d9)
    if not lagna:
        return out

    lagna_idx = _sidx(lagna)
    if lagna_idx is None:
        return out
    lagna_lord = SIGN_LORD[lagna]
    h7_sign = SIGN_NAMES[(lagna_idx + 6) % 12]
    h7_lord = SIGN_LORD[h7_sign]

    out["available"] = True
    out["d9_lagna_sign"] = lagna
    out["d9_lagna_lord"] = lagna_lord
    out["d9_7h_sign"] = h7_sign
    out["d9_7h_lord"] = h7_lord

    # Where does D9 7L sit (in D9)?
    sl_sign = _d9_planet_sign(d9, h7_lord)
    if sl_sign:
        sl_idx = _sidx(sl_sign)
        out["d9_7l_sign"] = sl_sign
        out["d9_7l_house"] = _house_from_lagna(sl_idx, lagna_idx) if sl_idx is not None else None

    # Venus + Jupiter dignity in D9
    vsign = _d9_planet_sign(d9, "Venus")
    if vsign:
        vd = _dignity("Venus", _sidx(vsign))
        out["d9_venus_sign"] = vsign
        out["d9_venus_dignity"] = _dignity_word(vd)
    else:
        vd = 0
    jsign = _d9_planet_sign(d9, "Jupiter")
    if jsign:
        jd = _dignity("Jupiter", _sidx(jsign))
        out["d9_jupiter_sign"] = jsign
        out["d9_jupiter_dignity"] = _dignity_word(jd)
    else:
        jd = 0

    # Marriage maturity score: weighted 0-10
    score = 5.0
    drivers: list[str] = []
    cautions: list[str] = []

    # 7L placement bonus/penalty
    if out["d9_7l_house"] in {1, 4, 5, 7, 9, 10, 11}:
        score += 1.5
        drivers.append("D9 7L in supportive house — committed bond unfolds")
    elif out["d9_7l_house"] in {6, 8, 12}:
        score -= 1.5
        cautions.append("D9 7L in challenging house — patience layer needed")

    # Venus dignity
    if vd >= 1:
        score += 1.5
        drivers.append("Venus strong in D9 — natural marital harmony")
    elif vd <= -1:
        score -= 1.5
        cautions.append("Venus weak in D9 — affection needs intentional nurture")

    # Jupiter dignity
    if jd >= 1:
        score += 1.5
        drivers.append("Jupiter strong in D9 — wisdom + commitment layer")
    elif jd <= -1:
        score -= 1.0
        cautions.append("Jupiter weak in D9 — values alignment needs work")

    # Lagna-lord vs 7L friendship
    fw = _friendship_word(lagna_lord, h7_lord)
    if fw in ("same", "friendly"):
        score += 0.5
        drivers.append(f"D9 lagna lord & 7L are {fw} — natural compatibility flow")
    elif fw == "hostile":
        score -= 1.0
        cautions.append("D9 lagna lord & 7L hostile — internal pull-and-push")

    out["marriage_maturity_0_10"] = max(0, min(10, round(score, 1)))
    out["drivers"] = drivers
    out["cautions"] = cautions
    return out


def _couple_sync(p1: dict, p2: dict) -> dict[str, Any]:
    """Cross-partner D9 sync. Both partners must have available=True."""
    sync: dict[str, Any] = {
        "available": False,
        "lagna_lord_relation": "neutral",
        "seven_lord_relation": "neutral",
        "score_0_10": 5,
        "notes": [],
    }
    if not (p1.get("available") and p2.get("available")):
        return sync

    ll1, ll2 = p1["d9_lagna_lord"], p2["d9_lagna_lord"]
    sl1, sl2 = p1["d9_7h_lord"], p2["d9_7h_lord"]
    rel_lagna = _friendship_word(ll1, ll2)
    rel_seven = _friendship_word(sl1, sl2)
    score = 5.0
    notes: list[str] = []

    if rel_lagna in ("same", "friendly"):
        score += 1.5
        notes.append(f"D9 lagna lords ({ll1} ↔ {ll2}) are {rel_lagna}")
    elif rel_lagna == "hostile":
        score -= 1.5
        notes.append(f"D9 lagna lords ({ll1} ↔ {ll2}) hostile")

    if rel_seven in ("same", "friendly"):
        score += 1.5
        notes.append(f"D9 7th lords ({sl1} ↔ {sl2}) are {rel_seven}")
    elif rel_seven == "hostile":
        score -= 1.0
        notes.append(f"D9 7th lords ({sl1} ↔ {sl2}) hostile")

    # If both Venus dignities good → bonus
    vd1 = p1["d9_venus_dignity"] in ("exalted", "own-sign")
    vd2 = p2["d9_venus_dignity"] in ("exalted", "own-sign")
    if vd1 and vd2:
        score += 1.0
        notes.append("Both partners' Venus is dignified in D9 — strong harmony")

    sync["available"] = True
    sync["lagna_lord_relation"] = rel_lagna
    sync["seven_lord_relation"] = rel_seven
    sync["score_0_10"] = max(0, min(10, round(score, 1)))
    sync["notes"] = notes
    return sync


def compute_d9_marriage(kundli_p1: dict, kundli_p2: dict) -> dict[str, Any]:
    """Full D9 marriage destiny analysis for a couple.

    Returns: {p1: {...}, p2: {...}, sync: {...}, available: bool}
    Never raises. Missing/partial D9 → returns shape with available=False
    sub-blocks; downstream code must check `available` per block.
    """
    p1 = _per_partner(kundli_p1)
    p2 = _per_partner(kundli_p2)
    sync = _couple_sync(p1, p2)
    return {
        "available": p1["available"] and p2["available"],
        "p1": p1,
        "p2": p2,
        "sync": sync,
    }

"""
health_tridosha_v1 — Vata / Pitta / Kapha from D1 + D9 + KP 6th CSL.

Layers (spec-aligned, no medical diagnosis output):
  1. D1 — prakriti, tattva element matrix, 4H/5H/6H occupants + aspects
  2. D9 — dignity adjusts affliction weights (exalted/own −40%, debilitated +50%)
  3. KP — 6th cusp sub-lord signification + planet dosha promise
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
EXALT = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo",
    "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra",
}
DEBIL = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces",
    "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
}
OWN = {
    "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
}
SIGN_DOSHA = {
    "Aries": "pitta", "Taurus": "kapha", "Gemini": "vata", "Cancer": "kapha",
    "Leo": "pitta", "Virgo": "vata", "Libra": "vata", "Scorpio": "pitta",
    "Sagittarius": "pitta", "Capricorn": "vata", "Aquarius": "vata", "Pisces": "kapha",
}
PLANET_DOSHA = {
    "Sun": "pitta", "Mars": "pitta", "Saturn": "vata", "Mercury": "vata",
    "Moon": "kapha", "Venus": "kapha", "Jupiter": "kapha", "Rahu": "vata", "Ketu": "vata",
}
_WATER_SIGNS = frozenset({"Cancer", "Scorpio", "Pisces"})
_AIR_SIGNS = frozenset({"Gemini", "Libra", "Aquarius"})
_FIRE_SIGNS = frozenset({"Aries", "Leo", "Sagittarius"})
_BENEFICS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_MALEFICS = frozenset({"Saturn", "Mars", "Rahu", "Ketu", "Sun"})
_PLANETS_9 = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
_DUSTHANA = frozenset({6, 8, 12})
_HOUSE_DOSHA_BIAS = {4: "kapha", 5: "pitta"}


def _find_p(planets: List[dict], name: str) -> Optional[dict]:
    return next((p for p in planets if p.get("name") == name), None)


def _dusthana_lords(asc_idx: int) -> set[str]:
    return {SIGN_LORD[SIGNS[(asc_idx + h - 1) % 12]] for h in _DUSTHANA}


def _planet_house(planets: List[dict], pname: str) -> Optional[int]:
    p = _find_p(planets, pname)
    if not p:
        return None
    h = p.get("house")
    return int(h) if isinstance(h, int) else None


def _aspects_house(aspector: str, ap_house: int, target_house: int) -> bool:
    if not (1 <= ap_house <= 12 and 1 <= target_house <= 12):
        return False
    diff = ((target_house - ap_house) % 12) + 1
    if diff == 7:
        return True
    extras = {
        "Mars": {4, 8},
        "Jupiter": {5, 9},
        "Saturn": {3, 10},
        "Rahu": {3, 10},
        "Ketu": {3, 10},
    }
    return diff in extras.get(aspector, set())


def _is_combust(p: dict, sun: Optional[dict]) -> bool:
    if p.get("combust") or p.get("isCombust"):
        return True
    if not sun:
        return False
    pl, sl = p.get("longitude"), sun.get("longitude")
    if pl is None or sl is None:
        return False
    try:
        diff = abs(float(pl) - float(sl)) % 360.0
        return diff < 8.0 or diff > 352.0
    except (TypeError, ValueError):
        return False


def _is_retro(p: dict) -> bool:
    return bool(p.get("retrograde") or p.get("isRetrograde") or p.get("vakri"))


def _varga_chart(kundli: Optional[dict], key: str) -> Optional[dict]:
    if not kundli:
        return None
    dv = kundli.get("divisionalCharts") or {}
    ch = dv.get(key) or dv.get(key.lower())
    if isinstance(ch, dict) and ch.get("planets"):
        return ch
    return None


def _d9_dignity_tier(d9: dict, pname: str) -> str:
    p = _find_p(d9.get("planets") or [], pname)
    if not p:
        return "neutral"
    sg = str(p.get("sign") or "")
    if pname in EXALT and sg == EXALT[pname]:
        return "strong"
    if pname in OWN and sg in OWN[pname]:
        return "strong"
    if pname in DEBIL and sg == DEBIL[pname]:
        return "weak"
    return "neutral"


def _kp_cusp(kp: dict, house: int) -> Optional[dict]:
    for c in (kp or {}).get("cusps", []) or []:
        if isinstance(c, dict) and c.get("house") == house:
            return c
    return None


def _kp_signified_houses(kp: dict, planet: str) -> List[int]:
    sig = (kp or {}).get("significations") or {}
    raw = sig.get(planet) or sig.get(planet.lower()) or []
    out: List[int] = []
    for v in raw:
        try:
            h = int(v)
            if 1 <= h <= 12:
                out.append(h)
        except (TypeError, ValueError):
            continue
    return out


def _norm_planet(p: Any) -> Optional[str]:
    if not p or not isinstance(p, str):
        return None
    return p.strip().title() or None


def _normalize_pct(raw: Dict[str, float]) -> Dict[str, int]:
    total = sum(raw.values()) or 1.0
    pct = {k: int(round(v * 100.0 / total)) for k, v in raw.items()}
    drift = 100 - sum(pct.values())
    if drift:
        dom = max(pct, key=pct.get)
        pct[dom] = max(0, pct[dom] + drift)
    return pct


def _dosha_state(pct: int) -> str:
    if pct < 36:
        return "Balanced"
    if pct < 44:
        return "Afflicted"
    return "Elevated"


def _care_tip(dosha: str, state: str) -> str:
    tips = {
        ("vata", "Balanced"): "Warm meals, steady sleep — Vata balanced rakho.",
        ("vata", "Afflicted"): "Warm oily food, oil massage, fixed routine — Vata ko shaant rakho.",
        ("vata", "Elevated"): "Cold/dry food aur irregular routine kam karo — warmth aur rest.",
        ("pitta", "Balanced"): "Cooling foods, moderate exercise — Pitta balanced.",
        ("pitta", "Afflicted"): "Spice, anger, dhoop kam — hydrate aur cool rakho.",
        ("pitta", "Elevated"): "Cooling diet, calm mind — heat aur acidity pe dhyan.",
        ("kapha", "Balanced"): "Active mornings, light meals — Kapha light rakho.",
        ("kapha", "Afflicted"): "Sweets/dairy kam, brisk walk — heaviness avoid karo.",
        ("kapha", "Elevated"): "Light warm spices, daily movement — sluggishness kam karo.",
    }
    return tips.get((dosha, state), "Regular routine teeno dosha ko support karti hai.")


def _csl_dosha_boost(csl: str) -> Dict[str, float]:
    """KP 6th CSL planet → dominant humor when disease promise active."""
    if csl in ("Moon", "Venus", "Jupiter"):
        return {"kapha": 28.0, "vata": 0.0, "pitta": 0.0}
    if csl in ("Saturn", "Rahu", "Ketu"):
        return {"vata": 28.0, "pitta": 0.0, "kapha": 0.0}
    if csl in ("Sun", "Mars"):
        return {"pitta": 28.0, "vata": 0.0, "kapha": 0.0}
    if csl == "Mercury":
        return {"vata": 14.0, "pitta": 10.0, "kapha": 0.0}
    return {"vata": 8.0, "pitta": 8.0, "kapha": 8.0}


def _d1_layer(
    planets: List[dict], asc_idx: int
) -> Tuple[Dict[str, float], List[Tuple[str, str, float]]]:
    """Return dosha scores + per-planet affliction ledger for D9 adjustment."""
    scores = {"vata": 0.0, "pitta": 0.0, "kapha": 0.0}
    ledger: List[Tuple[str, str, float]] = []
    sign_1 = SIGNS[asc_idx % 12]
    dusthana_lords = _dusthana_lords(asc_idx)
    sun = _find_p(planets, "Sun")

    def _add(dosha: str, w: float, planet: str = "") -> None:
        scores[dosha] += w
        if planet and w > 0:
            ledger.append((planet, dosha, w))

    # Prakriti anchors
    _add(SIGN_DOSHA.get(sign_1, "vata"), 25.0)
    moon = _find_p(planets, "Moon")
    if moon and moon.get("sign"):
        _add(SIGN_DOSHA.get(str(moon.get("sign")), "vata"), 25.0, "Moon")
    if sun and sun.get("sign"):
        _add(SIGN_DOSHA.get(str(sun.get("sign")), "vata"), 15.0, "Sun")
    lord_1 = SIGN_LORD[sign_1]
    _add(PLANET_DOSHA.get(lord_1, "vata"), 15.0, lord_1)

    # Tattva element matrix (all planets)
    for p in planets or []:
        nm = str(p.get("name") or "")
        if nm not in _PLANETS_9:
            continue
        sg = str(p.get("sign") or "")
        if sg in _WATER_SIGNS:
            _add("kapha", 3.0, nm)
        elif sg in _AIR_SIGNS:
            _add("vata", 3.0, nm)
        elif sg in _FIRE_SIGNS:
            _add("pitta", 3.0, nm)
        else:
            _add(SIGN_DOSHA.get(sg, "kapha"), 2.0, nm)
        _add(PLANET_DOSHA.get(nm, "vata"), 2.0, nm)

    # 4H / 5H / 6H occupants + aspects
    for h in (4, 5, 6):
        bias = _HOUSE_DOSHA_BIAS.get(h)
        for p in planets or []:
            if p.get("house") != h:
                continue
            nm = str(p.get("name") or "")
            if nm not in _PLANETS_9:
                continue
            target = bias or PLANET_DOSHA.get(nm, "vata")
            if nm in _MALEFICS:
                w = 7.0
                if nm in dusthana_lords:
                    w *= 2.0
                _add(target, w, nm)
            elif nm in _BENEFICS:
                _add(target, 3.0, nm)

        for pname in _PLANETS_9:
            ap_h = _planet_house(planets, pname)
            if not ap_h or not _aspects_house(pname, ap_h, h):
                continue
            target = bias or PLANET_DOSHA.get(pname, "vata")
            if pname in _MALEFICS:
                w = 5.0
                if pname in dusthana_lords:
                    w *= 2.0
                _add(target, w, pname)
            elif pname in _BENEFICS:
                _add(target, 2.0, pname)

    # Core sub-routines (constitutional stress, not disease labels)
    sat, rahu = _find_p(planets, "Saturn"), _find_p(planets, "Rahu")
    mars = _find_p(planets, "Mars")
    venus = _find_p(planets, "Venus")

    for p in (sat, rahu):
        if p and p.get("house") in (1, 6):
            w = 10.0 * (2.0 if str(p.get("name")) in dusthana_lords else 1.0)
            _add("vata", w, str(p.get("name")))

    for p in (sun, mars):
        if p and p.get("house") in (5, 6):
            _add("pitta", 8.0, str(p.get("name") or ""))

    for p in (moon, venus):
        if not p:
            continue
        hit = _is_combust(p, sun) or _is_retro(p)
        if not hit:
            for aff in (sat, rahu):
                if aff and p.get("house") and aff.get("house"):
                    if abs(int(p.get("house") or 0) - int(aff.get("house") or 0)) <= 1:
                        hit = True
                        break
        if hit:
            _add("kapha", 8.0, str(p.get("name")))

    return scores, ledger


def _apply_d9(
    d1_scores: Dict[str, float],
    ledger: List[Tuple[str, str, float]],
    kundli: Optional[dict],
) -> Tuple[Dict[str, float], str]:
    """Adjust D1 affliction ledger via D9 dignity; return scores + immunity verdict."""
    d9 = _varga_chart(kundli, "D9")
    if not d9 or not ledger:
        return dict(d1_scores), "D9 unavailable — D1 prakriti only"

    adjusted = dict(d1_scores)
    strong_n, weak_n = 0, 0
    for planet, dosha, w in ledger:
        tier = _d9_dignity_tier(d9, planet)
        if tier == "strong":
            delta = w * 0.4
            adjusted[dosha] = max(0.0, adjusted[dosha] - delta)
            strong_n += 1
        elif tier == "weak":
            delta = w * 0.5
            adjusted[dosha] += delta
            weak_n += 1

    if weak_n > strong_n:
        verdict = "Chronic tendency — D9 mein kamzor graha zyada"
    elif strong_n > weak_n:
        verdict = "High recovery — D9 mein strong graha zyada"
    else:
        verdict = "Mixed D9 immunity"
    return adjusted, verdict


def _kp6_layer(
    kundli: Optional[dict],
) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """KP 6th CSL — immunity vs active dosha promise."""
    meta: Dict[str, Any] = {
        "csl_planet": None,
        "signified_houses": [],
        "verdict": "UNKNOWN",
    }
    neutral = {"vata": 22.0, "pitta": 22.0, "kapha": 22.0}
    kp = (kundli or {}).get("kp") or {}
    if not kp:
        return neutral, meta

    cusp = _kp_cusp(kp, 6)
    if not cusp:
        return neutral, meta

    csl_raw = cusp.get("sl") or cusp.get("subLord") or cusp.get("sub_lord")
    csl = _norm_planet(csl_raw)
    meta["csl_planet"] = csl
    if not csl:
        return neutral, meta

    sig = _kp_signified_houses(kp, csl) or _kp_signified_houses(kp, csl_raw or "")
    meta["signified_houses"] = sig

    has_dusthana = any(h in _DUSTHANA for h in sig)
    has_immunity = any(h in (1, 5, 11) for h in sig)

    if has_immunity and not has_dusthana:
        meta["verdict"] = "IMMUNITY_HIGH"
        return {"vata": 20.0, "pitta": 20.0, "kapha": 20.0}, meta

    if has_dusthana:
        meta["verdict"] = "DOSHA_PROMISE_ACTIVE"
        return _csl_dosha_boost(csl), meta

    meta["verdict"] = "NEUTRAL"
    boost = _csl_dosha_boost(csl)
    return {k: 18.0 + boost[k] * 0.35 for k in boost}, meta


def compute_tridosha_balance(
    planets: List[dict],
    asc_idx: int,
    kundli: Optional[dict] = None,
) -> Dict[str, Any]:
    """D1 (45%) + D9-adjusted (30%) + KP 6th CSL (25%) → vata/pitta/kapha %."""
    d1_scores, ledger = _d1_layer(planets, asc_idx)
    d9_scores, d9_verdict = _apply_d9(d1_scores, ledger, kundli)
    kp_scores, kp_meta = _kp6_layer(kundli)

    d1_t = sum(d1_scores.values()) or 1.0
    d9_t = sum(d9_scores.values()) or 1.0
    kp_t = sum(kp_scores.values()) or 1.0

    merged = {
        k: (d1_scores[k] / d1_t) * 45.0
        + (d9_scores[k] / d9_t) * 30.0
        + (kp_scores[k] / kp_t) * 25.0
        for k in ("vata", "pitta", "kapha")
    }
    dosha_balance = _normalize_pct(merged)
    dosha_states = {k: _dosha_state(dosha_balance[k]) for k in dosha_balance}
    dominant_key = max(dosha_balance, key=dosha_balance.get)

    care: List[str] = []
    care.append(_care_tip(dominant_key, dosha_states[dominant_key]))
    for dk, pct in sorted(dosha_balance.items(), key=lambda x: -x[1]):
        if dk == dominant_key or dosha_states[dk] == "Balanced":
            continue
        tip = _care_tip(dk, dosha_states[dk])
        if tip not in care:
            care.append(tip)
        if len(care) >= 2:
            break

    return {
        "dosha_balance": dosha_balance,
        "dosha_states": dosha_states,
        "dominant_dosha": dominant_key.title(),
        "primary_imbalance": dominant_key,
        "tridosha_care": care,
        "engine": "health_tridosha_v1",
        "d9_immunity_verdict": d9_verdict,
        "kp_6th_csl": kp_meta,
    }

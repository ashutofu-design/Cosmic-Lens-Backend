"""Travel deterministic fact pack — D1/D9 Engine Execution (non-timing).

Dimensions:
  • foreign_travel   — long-distance / abroad movement (9H/3H + Rahu)
  • settlement       — permanent abroad basna (12H/9H + Saturn)
  • visa_luck        — visa/passport/PR tone (Jupiter/9H)
  • short_travel     — trips / tours (3H + Mercury/Moon)
  • travel_risk      — delay / obstacle / risk (malefics on 3/9/12)

Public:
  compute_travel_facts(kundli) -> dict
  compute_travel_engine_execution(kundli, ...) -> dict
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from stock_engine.stock_facts import (
    _DIGNITY_SCORE,
    _aspects,
    _house_lord,
    _is_combust,
    _planet_by_name,
    _planet_dignity,
    _planets_in_house,
    _sign_idx,
)

_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
_MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
_DUSTHANA = (6, 8, 12)
_TRAVEL_HOUSES = (3, 4, 7, 9, 12)
_FOREIGN_HOUSES = (3, 9, 12)
_SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
_PLANET_TRAVEL_ROLES = {
    "Sun": ["authority travel", "official trips"],
    "Moon": ["movement", "water travel", "mind on journey"],
    "Mars": ["courage travel", "risk on road"],
    "Mercury": ["short trips", "tickets", "communication abroad"],
    "Jupiter": ["visa luck", "sacred travel", "foreign grace"],
    "Venus": ["comfort travel", "tourism"],
    "Saturn": ["long stay", "immigration delay", "arduous journey"],
    "Rahu": ["foreign lands", "unconventional abroad", "visa twists"],
    "Ketu": ["pilgrimage", "detachment travel", "sudden exit"],
}
_HOUSE_TRAVEL_ROLES = {
    3: ["short travel", "courage", "siblings abroad"],
    4: ["home anchor", "homeland pull"],
    7: ["partner abroad", "travel with others"],
    9: ["long distance", "foreign luck", "dharma travel"],
    12: ["foreign lands", "settlement", "expenses abroad"],
}


def _tier(verdict: str, strong: bool = False, weak: bool = False) -> str:
    if verdict == "GREEN":
        return "high"
    if verdict == "RED":
        return "none"
    if weak:
        return "low"
    if strong:
        return "moderate"
    return "moderate"


def _verdict_from_score(score: int) -> str:
    if score >= 2:
        return "GREEN"
    if score <= -1:
        return "RED"
    return "YELLOW"


def _lord_state(planets: List[dict], asc_si: int, house: int) -> dict:
    lord = _house_lord(asc_si, house)
    p = _planet_by_name(planets, lord) if lord else None
    lh = (p or {}).get("house") or 0
    dig = _planet_dignity(planets, lord) if lord else "?"
    return {
        "lord": lord or "?",
        "lord_sign": (p or {}).get("sign") or "?",
        "lord_house": lh,
        "lord_dignity": dig,
        "lord_strength_score": _DIGNITY_SCORE.get(dig, 0),
        "lord_retrograde": bool(
            (p or {}).get("retrograde")
            or (p or {}).get("isRetrograde")
            or (p or {}).get("is_retrograde")
        ),
        "lord_in_dusthana": lh in _DUSTHANA,
        "lord_in_foreign": lh in _FOREIGN_HOUSES,
    }


def _karaka(planets: List[dict], name: str, sun_long: float = 0.0) -> dict:
    p = _planet_by_name(planets, name)
    if not p:
        return {"name": name, "house": 0, "dignity": "?", "sign": "?"}
    dig = _planet_dignity(planets, name)
    return {
        "name": name,
        "sign": p.get("sign") or "?",
        "house": p.get("house") or 0,
        "dignity": dig,
        "strength_score": _DIGNITY_SCORE.get(dig, 0),
        "retro": bool(p.get("retrograde") or p.get("isRetrograde") or p.get("is_retrograde")),
        "combust": _is_combust(p, sun_long) if p else False,
        "travel_roles": list(_PLANET_TRAVEL_ROLES.get(name, [])),
    }


def _detect_foreign_yog(planets: List[dict], asc_si: int) -> bool:
    """9L or 12L in foreign houses, or Rahu in 3/9/12."""
    rahu = _planet_by_name(planets, "Rahu")
    if rahu and int(rahu.get("house") or 0) in _FOREIGN_HOUSES:
        return True
    for hn in (9, 12):
        lord = _house_lord(asc_si, hn)
        p = _planet_by_name(planets, lord) if lord else None
        if p and int(p.get("house") or 0) in _FOREIGN_HOUSES:
            return True
    return False


def _detect_parivartana_9_12(planets: List[dict], asc_si: int) -> bool:
    l9 = _house_lord(asc_si, 9)
    l12 = _house_lord(asc_si, 12)
    if not l9 or not l12 or l9 == l12:
        return False
    p9 = _planet_by_name(planets, l9)
    p12 = _planet_by_name(planets, l12)
    if not p9 or not p12:
        return False
    return int(p9.get("house") or 0) == 12 and int(p12.get("house") or 0) == 9


def _detect_rahu_jupiter_link(planets: List[dict]) -> bool:
    rahu = _planet_by_name(planets, "Rahu")
    jup = _planet_by_name(planets, "Jupiter")
    if not rahu or not jup:
        return False
    rh = int(rahu.get("house") or 0)
    jh = int(jup.get("house") or 0)
    if not rh or not jh:
        return False
    if rh == jh:
        return True
    return bool(_aspects("Jupiter", jh, rh) or _aspects("Rahu", rh, jh))


def _dim_foreign_travel(lords: dict, karakas: dict, yogas: List[str]) -> dict:
    score = 0
    h9 = lords.get("h9") or {}
    h3 = lords.get("h3") or {}
    rahu = karakas.get("Rahu") or {}
    jup = karakas.get("Jupiter") or {}
    score += int(h9.get("lord_strength_score") or 0)
    score += int(h3.get("lord_strength_score") or 0)
    if h9.get("lord_in_foreign"):
        score += 1
    if int(rahu.get("house") or 0) in _FOREIGN_HOUSES:
        score += 2
    if int(jup.get("house") or 0) in (1, 5, 9, 11, 12):
        score += 1
    if "Foreign-Yog" in yogas:
        score += 2
    if h9.get("lord_in_dusthana") and h3.get("lord_in_dusthana"):
        score -= 2
    v = _verdict_from_score(score - 1)
    reasons = {
        "GREEN": "9H/3H + Rahu foreign axis strong — abroad travel support",
        "YELLOW": "Foreign travel mixed — paperwork and planning matter",
        "RED": "Foreign travel needs patience — build 9H/12H capacity first",
    }
    return {
        "verdict": v,
        "reason": reasons[v],
        "tier": _tier(v, strong=("Foreign-Yog" in yogas), weak=score <= 0),
        "score": score,
    }


def _dim_settlement(lords: dict, karakas: dict) -> dict:
    score = 0
    h12 = lords.get("h12") or {}
    h9 = lords.get("h9") or {}
    h4 = lords.get("h4") or {}
    sat = karakas.get("Saturn") or {}
    rahu = karakas.get("Rahu") or {}
    score += int(h12.get("lord_strength_score") or 0)
    score += int(h9.get("lord_strength_score") or 0)
    if h12.get("lord_in_foreign") or int(h12.get("lord_house") or 0) in (1, 9, 10, 11):
        score += 1
    if int(rahu.get("house") or 0) in (9, 12):
        score += 1
    if int(sat.get("house") or 0) in (9, 12, 10):
        score += 1
    # Strong 4L in own home pulls against permanent settlement
    if int(h4.get("lord_house") or 0) in (4, 2) and int(h4.get("lord_strength_score") or 0) >= 1:
        score -= 1
    if h12.get("lord_in_dusthana") and h9.get("lord_in_dusthana"):
        score -= 2
    v = _verdict_from_score(score - 1)
    reasons = {
        "GREEN": "12H/9H settlement axis supportive — long-stay abroad possible with planning",
        "YELLOW": "Settlement possible — legal route, finances and home-anchor both matter",
        "RED": "Permanent abroad shift needs structured effort — strengthen 12H/9H first",
    }
    return {
        "verdict": v,
        "reason": reasons[v],
        "tier": _tier(v, weak=score <= 0),
        "score": score,
    }


def _dim_visa_luck(lords: dict, karakas: dict, yogas: List[str]) -> dict:
    score = 0
    h9 = lords.get("h9") or {}
    jup = karakas.get("Jupiter") or {}
    mer = karakas.get("Mercury") or {}
    score += int(h9.get("lord_strength_score") or 0)
    score += int(jup.get("strength_score") or 0)
    if int(jup.get("house") or 0) in (1, 5, 9, 11):
        score += 1
    if "Rahu-Jupiter" in yogas:
        score += 1
    if jup.get("combust") or h9.get("lord_in_dusthana"):
        score -= 1
    if int(mer.get("strength_score") or 0) <= -1:
        score -= 1
    v = _verdict_from_score(score - 1)
    reasons = {
        "GREEN": "Jupiter/9H visa-luck tone supportive — documents + timing still matter",
        "YELLOW": "Visa theme mixed — prepare strong paperwork, expect reviews",
        "RED": "Visa path needs patience — strengthen 9H/Jupiter before filing",
    }
    return {
        "verdict": v,
        "reason": reasons[v],
        "tier": _tier(v, weak=score <= 0),
        "score": score,
    }


def _dim_short_travel(lords: dict, karakas: dict) -> dict:
    score = 0
    h3 = lords.get("h3") or {}
    mer = karakas.get("Mercury") or {}
    moon = karakas.get("Moon") or {}
    score += int(h3.get("lord_strength_score") or 0)
    score += int(mer.get("strength_score") or 0)
    if int(mer.get("house") or 0) in (1, 3, 5, 9, 11):
        score += 1
    if int(moon.get("house") or 0) in (3, 9, 12):
        score += 1
    if h3.get("lord_in_dusthana"):
        score -= 1
    v = _verdict_from_score(score - 1)
    reasons = {
        "GREEN": "3H/Mercury short-travel support — trips and tours favoured",
        "YELLOW": "Short travel mixed — plan logistics, avoid rushed bookings",
        "RED": "Short trips need care — 3H axis weak, prefer local/safe routes",
    }
    return {
        "verdict": v,
        "reason": reasons[v],
        "tier": _tier(v, weak=score <= 0),
        "score": score,
    }


def _dim_travel_risk(lords: dict, karakas: dict, afflictions: List[str]) -> dict:
    """GREEN = low risk; RED = higher caution (inverse of support)."""
    pressure = 0
    for key in ("h3", "h9", "h12"):
        st = lords.get(key) or {}
        if st.get("lord_in_dusthana") or str(st.get("lord_dignity") or "") in (
            "debilitated", "enemy",
        ):
            pressure += 1
    mars = karakas.get("Mars") or {}
    sat = karakas.get("Saturn") or {}
    if int(mars.get("house") or 0) in _FOREIGN_HOUSES and int(mars.get("strength_score") or 0) <= 0:
        pressure += 1
    if int(sat.get("house") or 0) in (3, 9) and str(sat.get("dignity") or "") == "debilitated":
        pressure += 1
    pressure += min(2, len(afflictions) // 2)
    if pressure >= 3:
        v = "RED"
        reason = "Travel risk elevated — malefic pressure on 3/9/12; plan carefully"
    elif pressure >= 1:
        v = "YELLOW"
        reason = "Travel risk moderate — delays/docs possible; keep buffers"
    else:
        v = "GREEN"
        reason = "Travel risk tone calm — still use common-sense safety"
    return {
        "verdict": v,
        "reason": reason,
        "tier": _tier(v, weak=pressure >= 2),
        "score": -pressure,
    }


def compute_travel_facts(kundli: dict) -> Dict[str, Any]:
    if not isinstance(kundli, dict):
        return {"error": "no kundli"}
    planets: List[dict] = kundli.get("planets") or []
    if not planets:
        return {"error": "no planets in kundli"}
    asc_sign = kundli.get("ascendant", "")
    asc_si = _sign_idx(asc_sign)
    if asc_si is None:
        return {"error": f"unknown ascendant sign: {asc_sign}"}

    sun = _planet_by_name(planets, "Sun")
    sun_long = float(sun.get("longitude", 0) or 0) if sun else 0.0

    lord_states: Dict[str, dict] = {}
    for hn in (1, 3, 4, 6, 7, 8, 9, 10, 11, 12):
        lord_states[f"h{hn}"] = _lord_state(planets, asc_si, hn)

    karakas: Dict[str, dict] = {}
    for k in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
        karakas[k] = _karaka(planets, k, sun_long)

    house_occupants: Dict[int, List[str]] = {
        hn: _planets_in_house(planets, hn) for hn in range(1, 13)
    }

    travel_yogas: List[str] = []
    if _detect_foreign_yog(planets, asc_si):
        travel_yogas.append("Foreign-Yog")
    if _detect_parivartana_9_12(planets, asc_si):
        travel_yogas.append("9-12-Parivartana")
    if _detect_rahu_jupiter_link(planets):
        travel_yogas.append("Rahu-Jupiter")

    afflictions: List[str] = []
    for hn in _FOREIGN_HOUSES:
        mal = [n for n in house_occupants.get(hn, []) if n in _MALEFICS]
        if mal:
            afflictions.append(f"Malefics in H{hn}: {', '.join(mal)}")
    for key in ("h9", "h12", "h3"):
        st = lord_states.get(key) or {}
        if st.get("lord_in_dusthana"):
            afflictions.append(
                f"H{key[1:]} lord ({st.get('lord')}) in dusthana H{st.get('lord_house')}"
            )
    rahu = karakas.get("Rahu") or {}
    if int(rahu.get("house") or 0) == 4:
        afflictions.append("Rahu in H4 — home vs abroad pull conflict")

    dimensions = {
        "foreign_travel": _dim_foreign_travel(lord_states, karakas, travel_yogas),
        "settlement": _dim_settlement(lord_states, karakas),
        "visa_luck": _dim_visa_luck(lord_states, karakas, travel_yogas),
        "short_travel": _dim_short_travel(lord_states, karakas),
        "travel_risk": _dim_travel_risk(lord_states, karakas, afflictions),
    }

    ft = dimensions["foreign_travel"]["verdict"]
    stl = dimensions["settlement"]["verdict"]
    vl = dimensions["visa_luck"]["verdict"]
    risk = dimensions["travel_risk"]["verdict"]
    sub_flags = {
        "foreign_yog_active": "Foreign-Yog" in travel_yogas,
        "settlement_strong": stl == "GREEN",
        "visa_supportive": vl == "GREEN",
        "travel_strong": ft == "GREEN",
        "risk_elevated": risk == "RED",
        "home_anchor_strong": int((lord_states.get("h4") or {}).get("lord_house") or 0) in (4, 2),
    }

    # Composite 0–100 travel strength (legacy-compatible label)
    composite = 48
    if ft == "GREEN":
        composite += 14
    elif ft == "RED":
        composite -= 10
    if stl == "GREEN":
        composite += 8
    if vl == "GREEN":
        composite += 6
    if risk == "RED":
        composite -= 8
    elif risk == "GREEN":
        composite += 4
    composite += min(10, len(travel_yogas) * 4)
    composite = max(18, min(92, composite))
    if composite >= 68:
        strength_label = "strong foreign/travel support"
    elif composite >= 52:
        strength_label = "moderate foreign/travel support — planning and paperwork matter"
    else:
        strength_label = "foreign/travel needs patience, documents and repeated effort"

    travel_houses = []
    for hn in _TRAVEL_HOUSES:
        st = lord_states.get(f"h{hn}") or {}
        travel_houses.append({
            "house": hn,
            "roles": list(_HOUSE_TRAVEL_ROLES.get(hn, [])),
            "lord": st.get("lord"),
            "lord_house": st.get("lord_house"),
            "lord_sign": st.get("lord_sign"),
            "lord_dignity": st.get("lord_dignity"),
            "occupants": house_occupants.get(hn) or [],
        })

    return {
        "ascendant": asc_sign,
        "house_lords": lord_states,
        "karakas": karakas,
        "house_occupants": house_occupants,
        "travel_yogas": travel_yogas,
        "afflictions": afflictions,
        "dimensions": dimensions,
        "sub_flags": sub_flags,
        "travel_houses": travel_houses,
        "composite_score": composite,
        "strength_label": strength_label,
        "engine_version": "travel_facts_v1",
    }


def _normalize_planet_list(raw: Any) -> List[dict]:
    out: List[dict] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("planet") or "").strip()
        if not name or name.lower() in ("ascendant", "lagna"):
            continue
        canon = {
            "surya": "Sun", "chandra": "Moon", "mangal": "Mars", "budh": "Mercury",
            "budha": "Mercury", "guru": "Jupiter", "brihaspati": "Jupiter",
            "shukra": "Venus", "shani": "Saturn",
        }.get(name.lower(), name)
        if canon[:1].islower():
            canon = canon[:1].upper() + canon[1:]
        row = dict(item)
        row["name"] = canon
        if not row.get("house") and row.get("House"):
            row["house"] = row.get("House")
        out.append(row)
    return out


def _resolve_d9_chart(
    kundli: dict,
) -> Tuple[Optional[List[dict]], Optional[int], Optional[str], Optional[str]]:
    if not isinstance(kundli, dict):
        return None, None, None, "invalid kundli"
    divs = kundli.get("divisionalCharts") or kundli.get("divisional_charts") or {}
    d9_chart = None
    if isinstance(divs, dict):
        d9_chart = divs.get("D9")
    if not isinstance(d9_chart, dict):
        d9_chart = kundli.get("D9") or kundli.get("navamsa") or kundli.get("D-9")
    if not isinstance(d9_chart, dict):
        # Fallback: compute D9 from D1 longitudes when available
        try:
            from divisional_charts import compute_d9  # type: ignore

            raw_planets = kundli.get("planets") or []
            lagna_lon = kundli.get("ascendantDeg") or kundli.get("ascendant_lon")
            if raw_planets and lagna_lon is not None:
                d9_map = compute_d9(raw_planets, float(lagna_lon))
                if isinstance(d9_map, dict) and d9_map:
                    rows = []
                    for pname, info in d9_map.items():
                        if not isinstance(info, dict):
                            continue
                        rows.append({
                            "name": pname,
                            "sign": info.get("sign"),
                            "house": info.get("house"),
                            "longitude": info.get("longitude") or info.get("lon"),
                        })
                    if rows:
                        # Infer D9 lagna from first available or D1 asc
                        asc_si = _sign_idx(str(kundli.get("ascendant") or ""))
                        if asc_si is None:
                            asc_si = 0
                        for planet in rows:
                            if planet.get("house"):
                                continue
                            sign_idx = _sign_idx(str(planet.get("sign") or ""))
                            if sign_idx is not None:
                                planet["house"] = ((sign_idx - asc_si) % 12) + 1
                        return rows, asc_si, _SIGN_NAMES[asc_si], None
        except Exception:
            pass
        return None, None, None, "d9 missing"

    asc_si: Optional[int] = None
    asc_sign: Optional[str] = None
    for key in ("ascendantSignIndex", "ascendantSignIdx", "ascendant", "lagna", "lagnaSign"):
        v = d9_chart.get(key)
        if isinstance(v, int):
            asc_si = int(v) % 12
            asc_sign = _SIGN_NAMES[asc_si]
            break
        if isinstance(v, str):
            asc_si = _sign_idx(v)
            if asc_si is not None:
                asc_sign = v if v in _SIGN_NAMES else _SIGN_NAMES[asc_si]
                break
    if asc_si is None:
        return None, None, None, "d9 lagna missing"

    planets = _normalize_planet_list(d9_chart.get("planets") or [])
    if not planets:
        return None, None, None, "d9 planets missing"

    for planet in planets:
        if planet.get("house"):
            continue
        sign_idx = _sign_idx(str(planet.get("sign") or ""))
        if sign_idx is None:
            raw_idx = planet.get("signIndex") or planet.get("sign_idx")
            if isinstance(raw_idx, int):
                sign_idx = int(raw_idx) % 12
        if sign_idx is not None:
            planet["house"] = ((sign_idx - asc_si) % 12) + 1
            if not planet.get("sign"):
                planet["sign"] = _SIGN_NAMES[sign_idx]
    return planets, asc_si, asc_sign, None


def _planet_rows_from_karakas(facts: Dict[str, Any]) -> List[dict]:
    rows: List[dict] = []
    for name, k in (facts.get("karakas") or {}).items():
        if not isinstance(k, dict):
            continue
        rows.append({
            "name": name,
            "sign": k.get("sign"),
            "house": k.get("house"),
            "dignity": k.get("dignity"),
            "retrograde": bool(k.get("retro")),
            "combust": bool(k.get("combust")),
            "travel_roles": list(k.get("travel_roles") or []),
        })
    return rows


def _tag_travel_chart_pack(facts: Dict[str, Any], *, chart: str) -> Dict[str, Any]:
    if not isinstance(facts, dict):
        return {
            "error": "invalid facts",
            "chart": chart,
            "schema_version": f"travel_{chart.lower()}_facts_v1",
        }
    if facts.get("error"):
        out = dict(facts)
        out["chart"] = chart
        out["schema_version"] = f"travel_{chart.lower()}_facts_v1"
        return out
    out = dict(facts)
    out["chart"] = chart
    out["schema_version"] = (
        "travel_d1_facts_v1" if chart == "D1" else "travel_d9_facts_v1"
    )
    out["planets"] = _planet_rows_from_karakas(out)
    out["lagnesh"] = (out.get("house_lords") or {}).get("h1") or {}
    return out


def compute_d9_travel_facts(kundli: dict) -> Dict[str, Any]:
    planets, asc_si, asc_sign, err = _resolve_d9_chart(kundli)
    if err:
        return {"error": err, "chart": "D9", "schema_version": "travel_d9_facts_v1"}
    d9_kundli: Dict[str, Any] = {
        "ascendant": asc_sign or (kundli.get("ascendant") if isinstance(kundli, dict) else None),
        "planets": planets,
    }
    pack = compute_travel_facts(d9_kundli)
    return _tag_travel_chart_pack(pack, chart="D9")


def compute_travel_engine_execution(
    kundli: dict,
    *,
    question: str = "",
    routing_label: str = "",
    llm_intent: Optional[dict] = None,
) -> Dict[str, Any]:
    """Fixed D1 + D9 travel pack for admin Engine Execution and LLM context."""
    chart = kundli if isinstance(kundli, dict) else {}
    d1_raw = compute_travel_facts(chart)
    d1 = _tag_travel_chart_pack(d1_raw, chart="D1")
    d9 = compute_d9_travel_facts(chart)

    d1_map = {
        str(p.get("name") or ""): p
        for p in (d1.get("planets") or [])
        if p.get("name")
    }
    d9_map = {
        str(p.get("name") or ""): p
        for p in (d9.get("planets") or [])
        if p.get("name") and not d9.get("error")
    }
    vargottama_details: List[dict] = []
    for name, d1p in d1_map.items():
        d9p = d9_map.get(name)
        if not d9p:
            continue
        is_vargottama = d1p.get("sign") == d9p.get("sign")
        vargottama_details.append({
            "planet": name,
            "d1_sign": d1p.get("sign"),
            "d1_house": d1p.get("house"),
            "d9_sign": d9p.get("sign"),
            "d9_house": d9p.get("house"),
            "vargottama": is_vargottama,
        })

    pack: Dict[str, Any] = {
        "schema_version": "travel_engine_execution_v1",
        "d1": d1,
        "d9": d9,
        "lagnesh": {
            "d1": d1.get("lagnesh") or (d1.get("house_lords") or {}).get("h1") or {},
            "d9": d9.get("lagnesh") or (d9.get("house_lords") or {}).get("h1") or {},
        },
        "vargottama_planets": [
            row["planet"] for row in vargottama_details if row.get("vargottama")
        ],
        "vargottama_details": vargottama_details,
        "dimensions": d1.get("dimensions") or {},
        "travel_yogas": d1.get("travel_yogas") or [],
        "sub_flags": d1.get("sub_flags") or {},
        "afflictions": d1.get("afflictions") or [],
        "composite_score": d1.get("composite_score"),
        "strength_label": d1.get("strength_label"),
        "routing_label": (routing_label or "").strip().lower(),
        "question": (question or "").strip()[:400],
    }
    if llm_intent and isinstance(llm_intent, dict):
        pack["intent_domain"] = str(
            llm_intent.get("routed_domain") or llm_intent.get("domain") or ""
        ).strip().lower()
    if (question or "").strip():
        try:
            from ask_travel.dasha_compact import maybe_attach_dasha_compact

            maybe_attach_dasha_compact(
                pack, chart, question, llm_intent=llm_intent,
            )
        except Exception:
            pass
    from ask_engine_execution_common import attach_modules_checked

    return attach_modules_checked(pack)

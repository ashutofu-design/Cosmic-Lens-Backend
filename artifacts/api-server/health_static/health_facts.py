"""Health deterministic fact pack — multi-dimensional verdict (non-timing).

Dimensions:
  • overall_vitality   — constitution / energy / immunity tone
  • chronic_tendency   — long-term / 8H / Saturn-Rahu pressure
  • mental_stress      — Moon / 4H / mind-body link
  • surgery_risk_tone  — Mars-Saturn / 6-8 axis caution (NOT muhurat)
  • preventive_risk    — vulnerability zones to monitor
  • recovery_capacity  — resistance + healing support (NOT recovery date)

Public:
  compute_health_facts(kundli) -> dict
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from stock_engine.stock_facts import (
    _DIGNITY_SCORE,
    _SIGN_NAMES,
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
_KENDRA = (1, 4, 7, 10)
_HEALTH_HOUSES = (1, 3, 4, 5, 6, 8, 12)
_PLANET_HEALTH_ROLES = {
    "Sun": ["vitality", "heart", "circulation", "bones"],
    "Moon": ["mind", "fluids", "sleep", "emotional regulation"],
    "Mars": ["muscles", "blood", "inflammation", "injury"],
    "Mercury": ["nerves", "skin", "digestion", "coordination"],
    "Jupiter": ["recovery", "growth", "liver", "metabolism"],
    "Venus": ["reproductive system", "kidneys", "hormonal balance", "skin"],
    "Saturn": ["chronic tendency", "bones", "joints", "degeneration"],
    "Rahu": ["toxicity", "unusual symptoms", "amplification"],
    "Ketu": ["hidden sensitivity", "sudden detachment", "diagnostic ambiguity"],
}
_HOUSE_HEALTH_ROLES = {
    1: ["constitution", "body", "vitality"],
    3: ["breath", "nerves", "shoulders"],
    4: ["chest", "heart", "emotional baseline"],
    5: ["digestion", "metabolism", "reproductive support"],
    6: ["disease tendency", "immunity response", "treatment"],
    8: ["chronic tendency", "surgery", "hidden vulnerability"],
    12: ["hospitalisation", "sleep", "recovery isolation"],
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
    }


def _karaka(planets: List[dict], name: str) -> dict:
    p = _planet_by_name(planets, name)
    if not p:
        return {"name": name, "house": 0, "dignity": "?"}
    return {
        "name": name,
        "sign": p.get("sign") or "?",
        "house": p.get("house") or 0,
        "dignity": _planet_dignity(planets, name),
        "strength_score": _DIGNITY_SCORE.get(_planet_dignity(planets, name), 0),
        "health_roles": list(_PLANET_HEALTH_ROLES.get(name, [])),
    }


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compute_shadbala_rows(planets: List[dict], asc_si: int) -> dict:
    try:
        from shadbala import compute_shadbala

        normalized = [
            {
                "name": p.get("name"),
                "lon": _as_float(p.get("longitude")),
                "house": int(p.get("house") or 0),
                "retrograde": bool(
                    p.get("retrograde")
                    or p.get("isRetrograde")
                    or p.get("is_retrograde")
                ),
            }
            for p in planets
            if p.get("name") and p.get("name") != "Ascendant"
        ]
        return compute_shadbala(normalized, asc_si) or {}
    except Exception:
        return {}


def _planet_fact_rows(planets: List[dict], shadbala: dict) -> List[dict]:
    sun = _planet_by_name(planets, "Sun") or {}
    sun_longitude = _as_float(sun.get("longitude"))
    rows: List[dict] = []
    for planet in planets:
        name = str(planet.get("name") or "").strip()
        if not name or name == "Ascendant":
            continue
        longitude = _as_float(planet.get("longitude"))
        degree = _as_float(
            planet.get("degree")
            if planet.get("degree") is not None
            else planet.get("degree_in_sign")
        )
        if degree is None and longitude is not None:
            degree = longitude % 30
        dignity = _planet_dignity(planets, name)
        retrograde = bool(
            planet.get("retrograde")
            or planet.get("isRetrograde")
            or planet.get("is_retrograde")
        )
        combust = (
            _is_combust(planet, sun_longitude)
            if sun_longitude is not None
            else bool(planet.get("combust") or planet.get("isCombust"))
        )
        rows.append({
            "name": name,
            "sign": planet.get("sign") or "?",
            "house": int(planet.get("house") or 0),
            "degree": round(degree, 3) if degree is not None else None,
            "longitude": round(longitude, 3) if longitude is not None else None,
            "dignity": dignity,
            "strength_score": _DIGNITY_SCORE.get(dignity, 0),
            "shadbala": shadbala.get(name),
            "retrograde": retrograde,
            "combust": bool(combust),
            "health_roles": list(_PLANET_HEALTH_ROLES.get(name, [])),
        })
    return rows


def _aspect_rows(planets: List[dict], target_houses: tuple[int, ...]) -> List[dict]:
    rows: List[dict] = []
    for planet in planets:
        name = str(planet.get("name") or "").strip()
        source_house = int(planet.get("house") or 0)
        if not name or name == "Ascendant" or not source_house:
            continue
        for target_house in target_houses:
            if _aspects(name, source_house, target_house):
                rows.append({
                    "planet": name,
                    "from_house": source_house,
                    "to_house": target_house,
                    "polarity": (
                        "supportive"
                        if name in _BENEFICS
                        else "pressure"
                        if name in _MALEFICS
                        else "neutral"
                    ),
                })
    return rows


def _house_fact_rows(
    planets: List[dict],
    asc_si: int,
    lord_states: dict,
    aspects: List[dict],
) -> List[dict]:
    rows: List[dict] = []
    for house in range(1, 13):
        sign_idx = (asc_si + house - 1) % 12
        received = [a for a in aspects if a.get("to_house") == house]
        rows.append({
            "house": house,
            "sign": _SIGN_NAMES[sign_idx],
            "lord": (lord_states.get(f"h{house}") or {}).get("lord") or "?",
            "lord_state": lord_states.get(f"h{house}") or {},
            "occupants": _planets_in_house(planets, house),
            "aspects_received": received,
            "health_roles": list(_HOUSE_HEALTH_ROLES.get(house, [])),
            "health_relevant": house in _HEALTH_HOUSES,
        })
    return rows


def _malefics_in(house: int, planets: List[dict]) -> List[str]:
    return [n for n in _planets_in_house(planets, house) if n in _MALEFICS]


def _benefic_aspect_on_house(planets: List[dict], target_house: int) -> bool:
    for b in _BENEFICS:
        bp = _planet_by_name(planets, b)
        if not bp:
            continue
        bh = bp.get("house") or 0
        if bh == target_house:
            return True
        if _aspects(b, bh, target_house):
            return True
    return False


def _afflicts_moon(planets: List[dict]) -> List[str]:
    moon = _planet_by_name(planets, "Moon")
    if not moon:
        return []
    mh = moon.get("house") or 0
    aff = []
    for m in ("Saturn", "Rahu", "Ketu", "Mars", "Sun"):
        mp = _planet_by_name(planets, m)
        if not mp:
            continue
        m_h = mp.get("house") or 0
        if m_h == mh:
            aff.append(f"{m} conjunct Moon")
        elif _aspects(m, m_h, mh):
            aff.append(f"{m} aspects Moon")
    return aff


def _compute_overall_vitality(
    lord_states: dict,
    karakas: dict,
    vitality_score: int,
    afflictions: List[str],
) -> Tuple[str, str, str, int]:
    score = 0
    if vitality_score >= 70:
        score += 2
    elif vitality_score >= 50:
        score += 1
    else:
        score -= 1

    h1 = lord_states.get("h1") or {}
    if _DIGNITY_SCORE.get(h1.get("lord_dignity", ""), 0) >= 2:
        score += 1
    elif h1.get("lord_in_dusthana"):
        score -= 1

    sun_d = _DIGNITY_SCORE.get((karakas.get("Sun") or {}).get("dignity", ""), 0)
    moon_d = _DIGNITY_SCORE.get((karakas.get("Moon") or {}).get("dignity", ""), 0)
    score += min(1, sun_d // 2) + min(1, moon_d // 2)

    if len(afflictions) >= 3:
        score -= 1

    v = _verdict_from_score(score)
    if v == "GREEN":
        reason = f"Vitality score {vitality_score}/100 with supportive Lagnesh + Sun-Moon base"
    elif v == "RED":
        reason = f"Vitality score {vitality_score}/100 with multiple drain signals on constitution"
    else:
        reason = f"Mixed vitality ({vitality_score}/100) — strong pockets with some weak zones"
    return v, reason, _tier(v), score


def _compute_chronic_tendency(
    lord_states: dict,
    karakas: dict,
    planets: List[dict],
) -> Tuple[str, str, str, int]:
    score = 0
    h8_m = _malefics_in(8, planets)
    if len(h8_m) >= 2:
        score -= 2
    elif h8_m:
        score -= 1

    h8 = lord_states.get("h8") or {}
    if h8.get("lord_in_dusthana"):
        score -= 1
    if _DIGNITY_SCORE.get(h8.get("lord_dignity", ""), 0) >= 2:
        score += 1

    sat_h = (karakas.get("Saturn") or {}).get("house") or 0
    rahu_h = (karakas.get("Rahu") or {}).get("house") or 0
    if sat_h in (1, 6, 8) or rahu_h in (1, 6, 8):
        score -= 1

    v = _verdict_from_score(score)
    if v == "GREEN":
        reason = "Chronic-pressure axis relatively light — maintenance lifestyle enough"
    elif v == "RED":
        reason = "8H/Saturn-Rahu cluster suggests long-term tendency needs active management"
    else:
        reason = "Some chronic-vulnerability signals — lifestyle vigilance helps"
    return v, reason, _tier(v, weak=(v == "RED")), score


def _compute_mental_stress(
    karakas: dict,
    lord_states: dict,
    planets: List[dict],
) -> Tuple[str, str, str, int]:
    score = 0
    moon = karakas.get("Moon") or {}
    moon_d = _DIGNITY_SCORE.get(moon.get("dignity", ""), 0)
    if moon_d >= 2:
        score += 2
    elif moon_d == 0:
        score -= 1

    moon_h = moon.get("house") or 0
    if moon_h in _DUSTHANA:
        score -= 1

    h4 = lord_states.get("h4") or {}
    if h4.get("lord_in_dusthana"):
        score -= 1
    elif _DIGNITY_SCORE.get(h4.get("lord_dignity", ""), 0) >= 2:
        score += 1

    aff = _afflicts_moon(planets)
    score -= min(2, len(aff))

    v = _verdict_from_score(score)
    if v == "GREEN":
        reason = "Moon + 4H relatively calm — emotional resilience supported"
    elif v == "RED":
        reason = "Moon under pressure — stress/anxiety tendency needs active care"
    else:
        reason = "Mixed mind-body pattern — stress spikes possible under pressure"
    return v, reason, _tier(v), score


def _compute_surgery_risk_tone(
    karakas: dict,
    lord_states: dict,
    planets: List[dict],
) -> Tuple[str, str, str, int]:
    score = 0
    mars_h = (karakas.get("Mars") or {}).get("house") or 0
    sat_h = (karakas.get("Saturn") or {}).get("house") or 0

    if mars_h in (1, 6, 8) and sat_h in (1, 6, 8):
        score -= 2
    elif mars_h in (6, 8) or sat_h in (6, 8):
        score -= 1

    h6 = lord_states.get("h6") or {}
    h8 = lord_states.get("h8") or {}
    if h6.get("lord_in_dusthana") or h8.get("lord_in_dusthana"):
        score -= 1

    if _benefic_aspect_on_house(planets, 1):
        score += 1

    v = _verdict_from_score(score)
    if v == "GREEN":
        reason = "Surgical/invasive caution tone low — routine medical guidance enough"
    elif v == "RED":
        reason = "Mars-Saturn + 6-8 pressure — extra caution tone if surgery ever needed"
    else:
        reason = "Moderate surgical-risk tone — second opinion + surgeon choice matter"
    return v, reason, _tier(v), score


def _compute_preventive_risk(
    lord_states: dict,
    planets: List[dict],
) -> Tuple[str, str, str, int]:
    score = 0
    for key in ("h6", "h8", "h12"):
        st = lord_states.get(key) or {}
        lh = st.get("lord_house") or 0
        if lh == 1:
            score -= 1

    if _malefics_in(1, planets):
        score -= 1
    if _malefics_in(6, planets):
        score -= 1

    if _benefic_aspect_on_house(planets, 1):
        score += 1
    if _benefic_aspect_on_house(planets, 5):
        score += 1

    v = _verdict_from_score(score)
    if v == "GREEN":
        reason = "Preventive vulnerability relatively low — routine checkups sufficient"
    elif v == "RED":
        reason = "Multiple risk-zone signals — preventive habits + screenings important"
    else:
        reason = "Some zones to monitor — prevention beats late reaction"
    return v, reason, _tier(v), score


def _compute_recovery_capacity(
    lord_states: dict,
    karakas: dict,
    planets: List[dict],
) -> Tuple[str, str, str, int]:
    score = 0
    h6 = lord_states.get("h6") or {}
    if _DIGNITY_SCORE.get(h6.get("lord_dignity", ""), 0) >= 2:
        score += 2
    elif h6.get("lord_in_dusthana"):
        score -= 1

    jup_h = (karakas.get("Jupiter") or {}).get("house") or 0
    mer_h = (karakas.get("Mercury") or {}).get("house") or 0
    if jup_h in (1, 6, 8) or _aspects("Jupiter", jup_h, 1):
        score += 1
    if mer_h in (1, 6) or _DIGNITY_SCORE.get((karakas.get("Mercury") or {}).get("dignity", ""), 0) >= 1:
        score += 1

    if _malefics_in(6, planets) and not _benefic_aspect_on_house(planets, 6):
        score -= 1

    v = _verdict_from_score(score)
    if v == "GREEN":
        reason = "Recovery resistance supported — doctor compliance + rest work well"
    elif v == "RED":
        reason = "Recovery axis weak — slow healing tendency, extra medical follow-up"
    else:
        reason = "Average recovery capacity — patience + treatment adherence key"
    return v, reason, _tier(v), score


def _normalize_planet_list(raw_planets: List[Any]) -> List[dict]:
    planets: List[dict] = []
    for raw in raw_planets:
        if not isinstance(raw, dict):
            continue
        planet = dict(raw)
        if planet.get("house") is None:
            planet["house"] = (
                planet.get("houseNumber")
                or planet.get("house_number")
                or planet.get("bhava")
            )
        if not planet.get("sign"):
            sign_idx = planet.get("signIndex") or planet.get("sign_idx")
            if isinstance(sign_idx, int):
                planet["sign"] = _SIGN_NAMES[int(sign_idx) % 12]
            else:
                longitude = _as_float(planet.get("longitude"))
                if longitude is not None:
                    planet["sign"] = _SIGN_NAMES[int(longitude // 30) % 12]
        planets.append(planet)
    return planets


def _resolve_d1_chart(kundli: dict) -> Tuple[Optional[List[dict]], Optional[int], Optional[str]]:
    if not isinstance(kundli, dict):
        return None, None, "invalid kundli"
    raw_planets = kundli.get("planets") or []
    if not raw_planets:
        return None, None, "planets missing"
    planets = _normalize_planet_list(raw_planets)
    if not planets:
        return None, None, "valid planets missing"

    asc = kundli.get("ascendant")
    asc_sign = (
        str(asc.get("sign") or asc.get("name") or "").strip()
        if isinstance(asc, dict)
        else asc
        if isinstance(asc, str)
        else ""
    )
    asc_si = _sign_idx(asc_sign) if asc_sign else None
    if asc_si is None:
        for key in ("lagna", "lagnaSign", "ascendant_sign", "ascendantSignIndex"):
            v = kundli.get(key)
            if isinstance(v, dict):
                v = v.get("sign") or v.get("name")
            if isinstance(v, str):
                asc_si = _sign_idx(v)
            elif isinstance(v, int):
                asc_si = int(v) % 12
            if asc_si is not None:
                break
    if asc_si is None:
        return None, None, "lagna missing"
    return planets, asc_si, None


def _resolve_d9_chart(kundli: dict) -> Tuple[Optional[List[dict]], Optional[int], Optional[str]]:
    if not isinstance(kundli, dict):
        return None, None, "invalid kundli"
    divs = kundli.get("divisionalCharts") or kundli.get("divisional_charts") or {}
    d9_chart = divs.get("D9") if isinstance(divs, dict) else None
    if not isinstance(d9_chart, dict):
        return None, None, "d9 missing"

    asc_si: Optional[int] = None
    for key in ("ascendantSignIndex", "ascendantSignIdx", "ascendant", "lagna", "lagnaSign"):
        v = d9_chart.get(key)
        if isinstance(v, int):
            asc_si = int(v) % 12
            break
        if isinstance(v, str):
            asc_si = _sign_idx(v)
            if asc_si is not None:
                break
    if asc_si is None:
        return None, None, "d9 lagna missing"

    raw_planets = d9_chart.get("planets") or []
    if not raw_planets:
        return None, None, "d9 planets missing"
    planets = _normalize_planet_list(raw_planets)
    if not planets:
        return None, None, "d9 valid planets missing"

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
    return planets, asc_si, None


def _build_chart_health_pack(
    planets: List[dict],
    asc_si: int,
    *,
    chart: str,
    kundli: Optional[dict] = None,
    with_dimensions: bool = True,
    with_shadbala: bool = True,
) -> Dict[str, Any]:
    schema_version = "health_d1_facts_v1" if chart == "D1" else "health_d9_facts_v1"
    lord_states = {
        f"h{hn}": _lord_state(planets, asc_si, hn)
        for hn in range(1, 13)
    }
    karakas = {n: _karaka(planets, n) for n in (
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
    )}

    vitality_score = 50
    vitality_risk = "Moderate"
    if with_dimensions and isinstance(kundli, dict):
        try:
            from vedic.health_vitality_score_v1 import compute_health_vitality_score

            vs = compute_health_vitality_score(kundli)
            vitality_score = int(vs.get("score") or 50)
            vitality_risk = str(vs.get("risk") or "Moderate")
        except Exception:
            pass

    afflictions: List[str] = []
    for hn in (1, 6, 8, 12):
        mal = _malefics_in(hn, planets)
        if mal:
            afflictions.append(f"Malefics in H{hn}: {', '.join(mal)}")
    for key in ("h6", "h8", "h12"):
        st = lord_states.get(key) or {}
        if st.get("lord_in_dusthana"):
            afflictions.append(
                f"H{key[1:]} lord ({st.get('lord')}) in dusthana H{st.get('lord_house')}"
            )
    moon_aff = _afflicts_moon(planets)
    afflictions.extend(moon_aff[:3])

    dimensions: Dict[str, Any] = {}
    sub_flags: Dict[str, Any] = {}
    if with_dimensions:
        ov_v, ov_r, ov_t, ov_s = _compute_overall_vitality(
            lord_states, karakas, vitality_score, afflictions,
        )
        ch_v, ch_r, ch_t, ch_s = _compute_chronic_tendency(lord_states, karakas, planets)
        ms_v, ms_r, ms_t, ms_s = _compute_mental_stress(karakas, lord_states, planets)
        sr_v, sr_r, sr_t, sr_s = _compute_surgery_risk_tone(karakas, lord_states, planets)
        pr_v, pr_r, pr_t, pr_s = _compute_preventive_risk(lord_states, planets)
        rc_v, rc_r, rc_t, rc_s = _compute_recovery_capacity(lord_states, karakas, planets)
        dimensions = {
            "overall_vitality": {"verdict": ov_v, "reason": ov_r, "tier": ov_t, "score": ov_s},
            "chronic_tendency": {"verdict": ch_v, "reason": ch_r, "tier": ch_t, "score": ch_s},
            "mental_stress": {"verdict": ms_v, "reason": ms_r, "tier": ms_t, "score": ms_s},
            "surgery_risk_tone": {"verdict": sr_v, "reason": sr_r, "tier": sr_t, "score": sr_s},
            "preventive_risk": {"verdict": pr_v, "reason": pr_r, "tier": pr_t, "score": pr_s},
            "recovery_capacity": {"verdict": rc_v, "reason": rc_r, "tier": rc_t, "score": rc_s},
        }
        sub_flags = {
            "vitality_score": vitality_score,
            "vitality_risk": vitality_risk,
            "moon_afflicted": bool(moon_aff),
            "chronic_pressure": ch_v == "RED",
            "mental_pressure": ms_v == "RED",
            "surgery_caution": sr_v == "RED",
            "immune_weak": ov_v == "RED",
        }

    aspect_rows = _aspect_rows(planets, tuple(range(1, 13)))
    shadbala = _compute_shadbala_rows(planets, asc_si) if with_shadbala else {}
    for state in lord_states.values():
        state["lord_shadbala"] = shadbala.get(state.get("lord"))
    for name, state in karakas.items():
        state["shadbala"] = shadbala.get(name)
    planet_rows = _planet_fact_rows(planets, shadbala)
    house_rows = _house_fact_rows(planets, asc_si, lord_states, aspect_rows)
    ascendant_sign = _SIGN_NAMES[asc_si]
    health_house_rows = [row for row in house_rows if row["health_relevant"]]
    lagnesh = dict(lord_states.get("h1") or {})
    lagnesh["chart"] = chart

    out: Dict[str, Any] = {
        "schema_version": schema_version,
        "chart": chart,
        "ascendant": ascendant_sign,
        "asc_si": asc_si,
        "lagnesh": lagnesh,
        "planets": planet_rows,
        "houses": house_rows,
        "health_houses": health_house_rows,
        "house_lords": lord_states,
        "karakas": karakas,
        "shadbala": shadbala,
        "aspects": aspect_rows,
        "afflictions": afflictions[:8],
    }
    if with_dimensions:
        out["dimensions"] = dimensions
        out["sub_flags"] = sub_flags
        out["vitality_score"] = vitality_score
        out["vitality_risk"] = vitality_risk
    return out


def compute_health_facts(kundli: dict) -> Dict[str, Any]:
    planets, asc_si, err = _resolve_d1_chart(kundli)
    if err:
        return {"error": err, "chart": "D1", "schema_version": "health_d1_facts_v1"}
    return _build_chart_health_pack(
        planets,
        asc_si,
        chart="D1",
        kundli=kundli,
        with_dimensions=True,
        with_shadbala=True,
    )


def compute_d9_health_facts(kundli: dict) -> Dict[str, Any]:
    planets, asc_si, err = _resolve_d9_chart(kundli)
    if err:
        return {"error": err, "chart": "D9", "schema_version": "health_d9_facts_v1"}
    return _build_chart_health_pack(
        planets,
        asc_si,
        chart="D9",
        with_dimensions=False,
        with_shadbala=False,
    )


def compute_health_engine_execution(
    kundli: dict,
    *,
    question: str = "",
    llm_intent: Optional[dict] = None,
) -> Dict[str, Any]:
    """Fixed D1 + D9 health chart pack for admin Engine Execution and LLM context.

    Timing questions only: also attaches ``dasha_timing_compact`` (current MD/AD/PD
    + top windows from a 10y internal scan — not the full dasha tree).
    """
    chart = kundli if isinstance(kundli, dict) else {}
    d1 = compute_health_facts(chart)
    d9 = compute_d9_health_facts(chart)

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
        "schema_version": "health_engine_execution_v1",
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
    }
    if (question or "").strip():
        try:
            from ask_health.dasha_compact import maybe_attach_dasha_compact

            maybe_attach_dasha_compact(
                pack, chart, question, llm_intent=llm_intent,
            )
        except Exception:
            pass
    from ask_engine_execution_common import attach_modules_checked

    return attach_modules_checked(pack)

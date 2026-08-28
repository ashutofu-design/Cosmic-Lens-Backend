"""Generic D1/D9 engine-execution facts for ask_unified domains."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from stock_engine.stock_facts import (
    _DIGNITY_SCORE,
    _house_lord,
    _is_combust,
    _planet_by_name,
    _planet_dignity,
    _planets_in_house,
    _sign_idx,
)

from ask_unified.specs import DomainSpec, get_domain_spec

_DUSTHANA = (6, 8, 12)
_SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def _verdict_from_score(score: int) -> str:
    if score >= 2:
        return "GREEN"
    if score <= -1:
        return "RED"
    return "YELLOW"


def _tier(verdict: str) -> str:
    return {"GREEN": "high", "RED": "none"}.get(verdict, "moderate")


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
        "lord_in_dusthana": lh in _DUSTHANA,
    }


def _karaka(planets: List[dict], name: str, sun_long: float = 0.0) -> dict:
    if name == "Ascendant":
        return {"name": name, "house": 1, "dignity": "lagna", "sign": "?"}
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
        "retro": bool(p.get("retrograde") or p.get("isRetrograde")),
        "combust": _is_combust(p, sun_long) if p else False,
    }


def _dim_for_houses(lords: dict, houses: tuple[int, ...], label: str) -> dict:
    score = 0
    for h in houses:
        st = lords.get(f"h{h}") or {}
        score += int(st.get("lord_strength_score") or 0)
        if st.get("lord_in_dusthana"):
            score -= 1
    v = _verdict_from_score(score - max(0, len(houses) - 1))
    reasons = {
        "GREEN": f"{label} supportive from chart houses",
        "YELLOW": f"{label} mixed — effort and planning matter",
        "RED": f"{label} needs patience — strengthen focus houses first",
    }
    return {"verdict": v, "reason": reasons[v], "tier": _tier(v), "score": score}


def compute_domain_facts(kundli: dict, spec: DomainSpec) -> Dict[str, Any]:
    if not isinstance(kundli, dict):
        return {"error": "no kundli"}
    planets: List[dict] = kundli.get("planets") or []
    if not planets:
        return {"error": "no planets in kundli"}
    asc_sign = kundli.get("ascendant", "")
    asc_si = _sign_idx(asc_sign)
    if asc_si is None:
        return {"error": f"unknown ascendant: {asc_sign}"}

    sun = _planet_by_name(planets, "Sun")
    sun_long = float(sun.get("longitude", 0) or 0) if sun else 0.0

    houses_needed = sorted(set((1,) + spec.focus_houses + (6, 8, 12)))
    lord_states = {f"h{h}": _lord_state(planets, asc_si, h) for h in houses_needed}

    planet_names = [p for p in spec.focus_planets if p != "Ascendant"]
    for extra in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
        if extra not in planet_names:
            planet_names.append(extra)
    karakas = {n: _karaka(planets, n, sun_long) for n in planet_names}

    house_occupants = {hn: _planets_in_house(planets, hn) for hn in range(1, 13)}

    afflictions: List[str] = []
    for h in spec.focus_houses:
        mal = [n for n in house_occupants.get(h, []) if n in ("Saturn", "Mars", "Rahu", "Ketu")]
        if mal:
            afflictions.append(f"Malefics in H{h}: {', '.join(mal)}")
        st = lord_states.get(f"h{h}") or {}
        if st.get("lord_in_dusthana"):
            afflictions.append(
                f"H{h} lord ({st.get('lord')}) in dusthana H{st.get('lord_house')}"
            )

    dimensions: Dict[str, Any] = {}
    for dim in spec.dimensions:
        houses = spec.dim_house_map.get(dim) or spec.focus_houses[:2]
        dimensions[dim] = _dim_for_houses(lord_states, tuple(houses), dim)

    greens = sum(1 for d in dimensions.values() if d.get("verdict") == "GREEN")
    reds = sum(1 for d in dimensions.values() if d.get("verdict") == "RED")
    composite = max(18, min(92, 50 + greens * 10 - reds * 10))
    if composite >= 68:
        strength_label = f"strong {spec.topic_label} support"
    elif composite >= 52:
        strength_label = f"moderate {spec.topic_label} — planning matters"
    else:
        strength_label = f"{spec.topic_label} needs patience and structured effort"

    domain_houses = []
    for h in spec.focus_houses:
        st = lord_states.get(f"h{h}") or {}
        domain_houses.append({
            "house": h,
            "lord": st.get("lord"),
            "lord_house": st.get("lord_house"),
            "lord_sign": st.get("lord_sign"),
            "lord_dignity": st.get("lord_dignity"),
            "occupants": house_occupants.get(h) or [],
        })

    return {
        "ascendant": asc_sign,
        "house_lords": lord_states,
        "karakas": karakas,
        "house_occupants": house_occupants,
        "afflictions": afflictions,
        "dimensions": dimensions,
        "domain_houses": domain_houses,
        "composite_score": composite,
        "strength_label": strength_label,
        "yogas": [],
        "sub_flags": {
            "support_strong": greens >= 2,
            "pressure_high": reds >= 2,
        },
        "engine_version": f"{spec.key}_facts_v1",
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
        row = dict(item)
        row["name"] = name[:1].upper() + name[1:] if name else name
        out.append(row)
    return out


def _resolve_d9(
    kundli: dict,
) -> Tuple[Optional[List[dict]], Optional[int], Optional[str], Optional[str]]:
    if not isinstance(kundli, dict):
        return None, None, None, "invalid kundli"
    divs = kundli.get("divisionalCharts") or kundli.get("divisional_charts") or {}
    d9_chart = divs.get("D9") if isinstance(divs, dict) else None
    if not isinstance(d9_chart, dict):
        d9_chart = kundli.get("D9") or kundli.get("navamsa") or kundli.get("D-9")
    if not isinstance(d9_chart, dict):
        try:
            from divisional_charts import compute_d9  # type: ignore

            raw = kundli.get("planets") or []
            lagna_lon = kundli.get("ascendantDeg") or kundli.get("ascendant_lon")
            if raw and lagna_lon is not None:
                d9_map = compute_d9(raw, float(lagna_lon))
                if isinstance(d9_map, dict) and d9_map:
                    rows = []
                    for pname, info in d9_map.items():
                        if isinstance(info, dict):
                            rows.append({
                                "name": pname,
                                "sign": info.get("sign"),
                                "house": info.get("house"),
                            })
                    asc_si = _sign_idx(str(kundli.get("ascendant") or "")) or 0
                    for planet in rows:
                        if not planet.get("house"):
                            si = _sign_idx(str(planet.get("sign") or ""))
                            if si is not None:
                                planet["house"] = ((si - asc_si) % 12) + 1
                    return rows, asc_si, _SIGN_NAMES[asc_si], None
        except Exception:
            pass
        return None, None, None, "d9 missing"

    asc_si = None
    asc_sign = None
    for key in ("ascendantSignIndex", "ascendant", "lagna", "lagnaSign"):
        v = d9_chart.get(key)
        if isinstance(v, int):
            asc_si = int(v) % 12
            asc_sign = _SIGN_NAMES[asc_si]
            break
        if isinstance(v, str):
            asc_si = _sign_idx(v)
            if asc_si is not None:
                asc_sign = _SIGN_NAMES[asc_si]
                break
    if asc_si is None:
        return None, None, None, "d9 lagna missing"
    planets = _normalize_planet_list(d9_chart.get("planets") or [])
    if not planets:
        return None, None, None, "d9 planets missing"
    for planet in planets:
        if planet.get("house"):
            continue
        si = _sign_idx(str(planet.get("sign") or ""))
        if si is not None:
            planet["house"] = ((si - asc_si) % 12) + 1
            planet.setdefault("sign", _SIGN_NAMES[si])
    return planets, asc_si, asc_sign, None


def _planet_rows(facts: Dict[str, Any]) -> List[dict]:
    rows = []
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
        })
    return rows


def _tag(facts: Dict[str, Any], *, chart: str, spec: DomainSpec) -> Dict[str, Any]:
    if not isinstance(facts, dict):
        return {"error": "invalid", "chart": chart}
    if facts.get("error"):
        out = dict(facts)
        out["chart"] = chart
        return out
    out = dict(facts)
    out["chart"] = chart
    out["schema_version"] = f"{spec.key}_{chart.lower()}_facts_v1"
    out["planets"] = _planet_rows(out)
    out["lagnesh"] = (out.get("house_lords") or {}).get("h1") or {}
    return out


def compute_domain_engine_execution(
    kundli: dict,
    *,
    domain: str,
    question: str = "",
    routing_label: str = "",
    llm_intent: Optional[dict] = None,
) -> Dict[str, Any]:
    spec = get_domain_spec(domain)
    if not spec:
        return {"error": f"unknown domain: {domain}"}
    chart = kundli if isinstance(kundli, dict) else {}
    d1_raw = compute_domain_facts(chart, spec)
    d1 = _tag(d1_raw, chart="D1", spec=spec)

    planets, _asc_si, asc_sign, err = _resolve_d9(chart)
    if err:
        d9: Dict[str, Any] = {"error": err, "chart": "D9"}
    else:
        d9_kundli = {"ascendant": asc_sign or chart.get("ascendant"), "planets": planets}
        d9 = _tag(compute_domain_facts(d9_kundli, spec), chart="D9", spec=spec)

    domain_division = (spec.divisional or "D9").upper()
    if domain_division == "D9":
        divisional = d9
    else:
        try:
            from event_timing._shared.universal_timing_formula import _divisional_chart

            div_chart = _divisional_chart(chart, domain_division)
            if div_chart.get("planets") and div_chart.get("ascendant"):
                divisional = _tag(
                    compute_domain_facts(div_chart, spec),
                    chart=domain_division,
                    spec=spec,
                )
            else:
                divisional = {
                    "error": f"{domain_division.lower()} missing",
                    "chart": domain_division,
                }
        except Exception as exc:
            divisional = {
                "error": f"{domain_division.lower()} unavailable: {str(exc)[:120]}",
                "chart": domain_division,
            }

    d1_map = {str(p.get("name") or ""): p for p in (d1.get("planets") or []) if p.get("name")}
    d9_map = {
        str(p.get("name") or ""): p
        for p in (d9.get("planets") or [])
        if p.get("name") and not d9.get("error")
    }
    vargottama_details = []
    for name, d1p in d1_map.items():
        d9p = d9_map.get(name)
        if not d9p:
            continue
        same = d1p.get("sign") == d9p.get("sign")
        vargottama_details.append({
            "planet": name,
            "d1_sign": d1p.get("sign"), "d1_house": d1p.get("house"),
            "d9_sign": d9p.get("sign"), "d9_house": d9p.get("house"),
            "vargottama": same,
        })

    pack: Dict[str, Any] = {
        "schema_version": spec.schema_version,
        "domain": spec.key,
        "d1": d1,
        "d9": d9,
        "divisional_chart_tag": domain_division,
        "divisional_chart": divisional,
        "charts_used": ["D1", "D9"] + (
            [domain_division] if domain_division != "D9" else []
        ),
        "lagnesh": {
            "d1": d1.get("lagnesh") or {},
            "d9": d9.get("lagnesh") or {},
            domain_division.lower(): divisional.get("lagnesh") or {},
        },
        "vargottama_planets": [r["planet"] for r in vargottama_details if r.get("vargottama")],
        "vargottama_details": vargottama_details,
        "dimensions": d1.get("dimensions") or {},
        "afflictions": d1.get("afflictions") or [],
        "sub_flags": d1.get("sub_flags") or {},
        "yogas": d1.get("yogas") or [],
        "composite_score": d1.get("composite_score"),
        "strength_label": d1.get("strength_label"),
        "routing_label": (routing_label or "").strip().lower(),
        "question": (question or "").strip()[:400],
    }
    if llm_intent and isinstance(llm_intent, dict):
        pack["intent_domain"] = str(
            llm_intent.get("routed_domain") or llm_intent.get("domain") or ""
        ).strip().lower()
    from ask_engine_execution_common import attach_modules_checked

    return attach_modules_checked(pack)

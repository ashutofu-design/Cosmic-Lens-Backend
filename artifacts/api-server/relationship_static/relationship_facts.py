"""Relationship deterministic fact pack — unified Engine Execution (D1 + D9).

Public:
  compute_relationship_facts(kundli) -> dict          # D1
  compute_d9_relationship_facts(kundli) -> dict       # D9
  compute_relationship_engine_execution(kundli, ...) -> dict  # pack for LLM/admin
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
_REL_HOUSES = (1, 5, 7, 8, 12)
_KARAKA_NAMES = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
_PLANET_REL_ROLES = {
    "Sun": ["self", "authority", "ego in bond"],
    "Moon": ["emotion", "attachment", "mood"],
    "Mars": ["desire", "conflict", "manglik axis"],
    "Mercury": ["communication", "negotiation"],
    "Jupiter": ["blessing", "marriage support", "counsel"],
    "Venus": ["love", "romance", "pleasure"],
    "Saturn": ["duty", "delay", "commitment weight"],
    "Rahu": ["obsession", "unconventional bond", "amplify"],
    "Ketu": ["detachment", "past bond", "withdraw"],
}
_HOUSE_REL_ROLES = {
    1: ["self", "identity in relationship"],
    5: ["romance", "dating", "attraction"],
    7: ["partnership", "spouse", "marriage"],
    8: ["intimacy", "shared crisis", "transformation"],
    12: ["bed pleasures", "foreign/secret", "losses"],
}
_MANGLIK_HOUSES = {1, 4, 7, 8, 12}


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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
        # Canonical English names used by dignity helpers
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
        if isinstance(v, dict):
            v = v.get("sign") or v.get("name")
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
        if sign_idx is not None and asc_si is not None:
            planet["house"] = ((sign_idx - asc_si) % 12) + 1
    return planets, asc_si, None


def _lord_state(planets: List[dict], asc_si: int, house: int) -> dict:
    lord = _house_lord(asc_si, house)
    p = _planet_by_name(planets, lord) if lord else None
    lh = int((p or {}).get("house") or 0)
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
        "lord_in_dusthana": lh in (6, 8, 12),
    }


def _karaka(planets: List[dict], name: str) -> dict:
    p = _planet_by_name(planets, name)
    if not p:
        return {"name": name, "house": 0, "dignity": "?", "rel_roles": list(_PLANET_REL_ROLES.get(name, []))}
    dig = _planet_dignity(planets, name)
    return {
        "name": name,
        "sign": p.get("sign") or "?",
        "house": int(p.get("house") or 0),
        "dignity": dig,
        "strength_score": _DIGNITY_SCORE.get(dig, 0),
        "retrograde": bool(
            p.get("retrograde") or p.get("isRetrograde") or p.get("is_retrograde")
        ),
        "rel_roles": list(_PLANET_REL_ROLES.get(name, [])),
    }


def _planet_fact_rows(planets: List[dict]) -> List[dict]:
    sun = _planet_by_name(planets, "Sun") or {}
    sun_longitude = _as_float(sun.get("longitude"))
    rows: List[dict] = []
    for planet in planets:
        name = str(planet.get("name") or "").strip()
        if not name:
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
            "dignity": dignity,
            "strength_score": _DIGNITY_SCORE.get(dignity, 0),
            "retrograde": bool(
                planet.get("retrograde")
                or planet.get("isRetrograde")
                or planet.get("is_retrograde")
            ),
            "combust": bool(combust),
            "rel_roles": list(_PLANET_REL_ROLES.get(name, [])),
        })
    return rows


def _aspect_rows(planets: List[dict], target_houses: tuple[int, ...]) -> List[dict]:
    rows: List[dict] = []
    for planet in planets:
        name = str(planet.get("name") or "").strip()
        source_house = int(planet.get("house") or 0)
        if not name or not source_house:
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
            "rel_roles": list(_HOUSE_REL_ROLES.get(house, [])),
            "relationship_relevant": house in _REL_HOUSES,
        })
    return rows


def _relationship_axes(planets: List[dict], asc_si: int, lord_states: dict) -> dict:
    h7 = lord_states.get("h7") or {}
    h5 = lord_states.get("h5") or {}
    h1 = lord_states.get("h1") or {}
    venus = _karaka(planets, "Venus")
    moon = _karaka(planets, "Moon")
    mars = _karaka(planets, "Mars")
    jupiter = _karaka(planets, "Jupiter")
    saturn = _karaka(planets, "Saturn")
    return {
        "lagna_lord": h1,
        "fifth_lord": h5,
        "seventh_lord": h7,
        "seventh_house_occupants": _planets_in_house(planets, 7),
        "fifth_house_occupants": _planets_in_house(planets, 5),
        "venus": venus,
        "moon": moon,
        "mars": mars,
        "jupiter": jupiter,
        "saturn": saturn,
        "saturn_on_7th": saturn.get("house") == 7,
        "mars_on_7th": mars.get("house") == 7,
        "rahu_on_7th": bool(_planet_by_name(planets, "Rahu") and int((_planet_by_name(planets, "Rahu") or {}).get("house") or 0) == 7),
    }


def _manglik_block(planets: List[dict]) -> dict:
    mars = _planet_by_name(planets, "Mars") or {}
    house = int(mars.get("house") or 0) or None
    return {
        "mars_house": house,
        "is_manglik": bool(house in _MANGLIK_HOUSES) if house else False,
        "classic_houses": sorted(_MANGLIK_HOUSES),
    }


def _signals_block(kundli: dict) -> dict:
    """PersonSignals flags — routing/LLM context, not per-archetype score engines."""
    try:
        from ask_mr.engines._person_signals import build_person_signals

        sig = build_person_signals(kundli if isinstance(kundli, dict) else {})
        keys = (
            "venus_debil", "moon_debil", "venus_d9_weak", "moon_afflicted",
            "fifth_lord_weak", "seventh_lord_dusthana", "seventh_lord_debil",
            "saturn_on_7th", "mars_on_7th", "rahu_on_7th_axis", "ketu_detachment",
            "third_person_risk", "separation_yoga", "reconnection_yoga",
            "emotional_instability", "moon_d9_debil", "d9_seventh_lord_weak",
            "venus_d9_exalted", "moon_d9_exalted", "venus_afflicted",
            "loyalty_risk_high", "affliction_weight",
        )
        out = {k: getattr(sig, k, None) for k in keys}
        out["notes"] = list(sig.notes or [])[:12]
        return out
    except Exception as exc:
        return {"error": str(exc)[:160]}


def _build_chart_relationship_pack(
    planets: List[dict],
    asc_si: int,
    *,
    chart: str,
) -> Dict[str, Any]:
    schema_version = (
        "relationship_d1_facts_v1" if chart == "D1" else "relationship_d9_facts_v1"
    )
    lord_states = {f"h{hn}": _lord_state(planets, asc_si, hn) for hn in range(1, 13)}
    karakas = {n: _karaka(planets, n) for n in _KARAKA_NAMES}
    aspect_rows = _aspect_rows(planets, tuple(range(1, 13)))
    planet_rows = _planet_fact_rows(planets)
    house_rows = _house_fact_rows(planets, asc_si, lord_states, aspect_rows)
    rel_houses = [row for row in house_rows if row["relationship_relevant"]]
    axes = _relationship_axes(planets, asc_si, lord_states)
    lagnesh = dict(lord_states.get("h1") or {})
    lagnesh["chart"] = chart
    afflictions: List[str] = []
    for hn in _REL_HOUSES:
        mal = [n for n in _planets_in_house(planets, hn) if n in _MALEFICS]
        if mal:
            afflictions.append(f"Malefics in H{hn}: {', '.join(mal)}")
    for key in ("h5", "h7", "h8", "h12"):
        st = lord_states.get(key) or {}
        if st.get("lord_in_dusthana"):
            afflictions.append(
                f"H{key[1:]} lord ({st.get('lord')}) in dusthana H{st.get('lord_house')}"
            )
    return {
        "schema_version": schema_version,
        "chart": chart,
        "ascendant": _SIGN_NAMES[asc_si],
        "asc_si": asc_si,
        "lagnesh": lagnesh,
        "planets": planet_rows,
        "houses": house_rows,
        "relationship_houses": rel_houses,
        "house_lords": lord_states,
        "karakas": karakas,
        "aspects": aspect_rows,
        "axes": axes,
        "manglik": _manglik_block(planets),
        "afflictions": afflictions[:10],
    }


def compute_relationship_facts(kundli: dict) -> Dict[str, Any]:
    planets, asc_si, err = _resolve_d1_chart(kundli)
    if err:
        return {"error": err, "chart": "D1", "schema_version": "relationship_d1_facts_v1"}
    return _build_chart_relationship_pack(planets, asc_si, chart="D1")


def compute_d9_relationship_facts(kundli: dict) -> Dict[str, Any]:
    planets, asc_si, err = _resolve_d9_chart(kundli)
    if err:
        return {"error": err, "chart": "D9", "schema_version": "relationship_d9_facts_v1"}
    return _build_chart_relationship_pack(planets, asc_si, chart="D9")


def compute_relationship_engine_execution(
    kundli: dict,
    *,
    question: str = "",
    routing_label: str = "",
    llm_intent: Optional[dict] = None,
) -> Dict[str, Any]:
    """Fixed D1 + D9 relationship pack for admin Engine Execution and LLM context.

    Timing questions only: also attaches ``dasha_timing_compact`` (current MD/AD/PD
    + top windows from a 10y internal scan — not the full dasha tree).
    """
    chart = kundli if isinstance(kundli, dict) else {}
    d1 = compute_relationship_facts(chart)
    d9 = compute_d9_relationship_facts(chart)

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
        "schema_version": "relationship_engine_execution_v1",
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
        "relationship_signals": _signals_block(chart),
        "manglik": (d1.get("manglik") if isinstance(d1, dict) else {}) or {},
        "routing_label": (routing_label or "").strip().lower(),
        "question": (question or "").strip()[:400],
    }
    if llm_intent and isinstance(llm_intent, dict):
        pack["intent_domain"] = str(
            llm_intent.get("routed_domain") or llm_intent.get("domain") or ""
        ).strip().lower()
    if (question or "").strip():
        try:
            from ask_mr.dasha_compact import maybe_attach_dasha_compact

            maybe_attach_dasha_compact(
                pack, chart, question, llm_intent=llm_intent,
            )
        except Exception:
            pass
    from ask_engine_execution_common import attach_modules_checked

    return attach_modules_checked(pack)

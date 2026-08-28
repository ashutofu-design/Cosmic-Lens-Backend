"""Compute general_chart_engine_execution_v1 — full D1 + D9 + dasha."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from stock_engine.stock_facts import (
    _DIGNITY_SCORE,
    _house_lord,
    _is_combust,
    _planet_by_name,
    _planet_dignity,
    _planets_in_house,
    _sign_idx,
)

_ALL_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
_DUSTHANA = (6, 8, 12)


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


def _chart_facts(kundli: dict, *, chart: str) -> Dict[str, Any]:
    if not isinstance(kundli, dict):
        return {"error": "no kundli", "chart": chart}
    planets: List[dict] = list(kundli.get("planets") or [])
    if not planets:
        return {"error": "no planets", "chart": chart}
    asc_sign = kundli.get("ascendant", "")
    asc_si = _sign_idx(asc_sign)
    if asc_si is None:
        return {"error": f"unknown ascendant: {asc_sign}", "chart": chart}

    sun = _planet_by_name(planets, "Sun")
    sun_long = float(sun.get("longitude", 0) or 0) if sun else 0.0
    lords = {f"h{h}": _lord_state(planets, asc_si, h) for h in range(1, 13)}
    karakas = {n: _karaka(planets, n, sun_long) for n in _ALL_PLANETS}
    occupants = {h: _planets_in_house(planets, h) for h in range(1, 13)}
    planet_rows = []
    for n in _ALL_PLANETS:
        k = karakas[n]
        planet_rows.append({
            "name": n,
            "sign": k.get("sign"),
            "house": k.get("house"),
            "dignity": k.get("dignity"),
            "retro": k.get("retro"),
            "combust": k.get("combust"),
        })
    afflictions = []
    for h in _DUSTHANA:
        mal = [n for n in (occupants.get(h) or []) if n in ("Saturn", "Mars", "Rahu", "Ketu")]
        if mal:
            afflictions.append(f"Malefics in H{h}: {', '.join(mal)}")
    lagnesh = lords.get("h1") or {}
    return {
        "chart": chart,
        "schema_version": f"general_{chart.lower()}_facts_v1",
        "ascendant": asc_sign,
        "lagnesh": lagnesh,
        "house_lords": lords,
        "karakas": karakas,
        "planets": planet_rows,
        "house_occupants": occupants,
        "afflictions": afflictions,
    }


def _resolve_d9(kundli: dict) -> tuple[Optional[list], Optional[str], Optional[str]]:
    """Return (planets, asc_sign, err)."""
    divs = kundli.get("divisionalCharts") or kundli.get("divisionals") or {}
    d9 = None
    if isinstance(divs, dict):
        d9 = divs.get("D9")
    if not isinstance(d9, dict):
        d9 = kundli.get("D9") or kundli.get("navamsa") or kundli.get("D-9")
    if not isinstance(d9, dict):
        try:
            from divisional_charts import compute_d9  # type: ignore

            raw = kundli.get("planets") or []
            lagna_lon = kundli.get("ascendantLongitude") or kundli.get("lagnaLongitude")
            if lagna_lon is None and isinstance(kundli.get("ascendant"), dict):
                lagna_lon = kundli["ascendant"].get("longitude")
            if lagna_lon is not None and raw:
                d9_map = compute_d9(raw, float(lagna_lon))
                if isinstance(d9_map, dict) and d9_map:
                    planets = []
                    for pname, info in d9_map.items():
                        if not isinstance(info, dict):
                            continue
                        planets.append({
                            "name": pname,
                            "sign": info.get("sign"),
                            "house": info.get("house"),
                            "longitude": info.get("longitude"),
                            "retrograde": info.get("retrograde"),
                        })
                    asc = str(d9_map.get("ascendant") or d9_map.get("Lagna") or "")
                    if not asc:
                        # first try lagna entry
                        for k, v in d9_map.items():
                            if str(k).lower() in ("lagna", "ascendant") and isinstance(v, dict):
                                asc = str(v.get("sign") or "")
                                break
                    return planets, asc or kundli.get("ascendant"), None
        except Exception as exc:
            return None, None, f"d9 unavailable: {type(exc).__name__}"
        return None, None, "d9 missing"
    planets = d9.get("planets") or []
    if not isinstance(planets, list) or not planets:
        return None, None, "d9 planets missing"
    asc = d9.get("ascendant") or kundli.get("ascendant")
    return list(planets), str(asc or ""), None


def compute_general_chart_execution(
    kundli: dict,
    *,
    question: str = "",
    llm_intent: Optional[dict] = None,
) -> Dict[str, Any]:
    chart = kundli if isinstance(kundli, dict) else {}
    d1 = _chart_facts(chart, chart="D1")
    planets9, asc9, err9 = _resolve_d9(chart)
    if err9 or not planets9:
        d9: Dict[str, Any] = {"error": err9 or "d9 missing", "chart": "D9"}
    else:
        d9 = _chart_facts(
            {"ascendant": asc9 or chart.get("ascendant"), "planets": planets9},
            chart="D9",
        )

    # Always attach real current + upcoming dasha for general chart LLM.
    dasha: Dict[str, Any] = {}
    try:
        from ask_finance.dasha_compact import compute_finance_dasha_compact

        dasha = compute_finance_dasha_compact(chart)
    except Exception as exc:
        dasha = {"error": f"dasha:{type(exc).__name__}", "current": None, "top_windows": []}

    today = datetime.utcnow()
    from ask_engine_execution_common import attach_modules_checked

    return attach_modules_checked({
        "schema_version": "general_chart_engine_execution_v1",
        "domain": "general",
        "mode": "llm_general_chart",
        "d1": d1,
        "d9": d9,
        "dasha_timing_compact": dasha,
        "charts_used": ["D1", "D9", "DASHA"],
        "today": today.strftime("%d %b %Y"),
        "question": (question or "")[:200],
        "llm_note": (
            "GENERAL CHART: no domain engine. Study D1 + D9 + dasha. "
            "Use Question DNA + QUESTION_PRIORITY_FACTS. Do not invent placements or dates."
        ),
        "routing_label": "general_chart",
    })

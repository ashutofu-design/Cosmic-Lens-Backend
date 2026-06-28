"""Love transit layer — Jupiter/Venus on 5H/7H/11H + dasha intersection."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional


def _moon_sign_idx(kundli: dict) -> int:
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    for p in kundli.get("planets") or []:
        if isinstance(p, dict) and p.get("name") == "Moon":
            si = p.get("sign_idx")
            if isinstance(si, int):
                return si % 12
            s = p.get("sign")
            if s in signs:
                return signs.index(s)
    ms = kundli.get("moonSign")
    if ms in signs:
        return signs.index(ms)
    return -1


def assess_love_transits(kundli: dict, lagna_si: int) -> dict:
    moon_si = _moon_sign_idx(kundli)
    out: dict[str, Any] = {"moon_sign_idx": moon_si if moon_si >= 0 else None}
    if lagna_si < 0:
        return out
    try:
        from transit_engine import (
            intersect_window_with_jupiter,
            love_jupiter_trigger_windows,
            love_venus_trigger_windows,
            venus_is_retrograde,
        )
        jup = love_jupiter_trigger_windows(lagna_si, moon_si if moon_si >= 0 else None)
        ven = love_venus_trigger_windows(lagna_si, moon_si if moon_si >= 0 else None)
        out["jupiter"] = jup
        out["venus"] = ven
        out["venus_retrograde_now"] = venus_is_retrograde()
        natal_v = next(
            (p for p in (kundli.get("planets") or [])
             if isinstance(p, dict) and p.get("name") == "Venus"),
            None,
        )
        if isinstance(natal_v, dict):
            out["natal_venus_retrograde"] = bool(natal_v.get("retrograde"))
    except Exception:
        pass
    return out


def merge_transit_directive(timing: dict, transits: dict, bucket: str) -> str:
    """Append Jupiter/Venus transit lock to dasha directive when available."""
    base = (timing or {}).get("llm_directive") or ""
    parts = [base] if base else []
    jup = (transits or {}).get("jupiter") or {}
    ven = (transits or {}).get("venus") or {}
    active_j = jup.get("active_window")
    if active_j:
        parts.append(
            f"Jupiter gochar ACTIVE on {', '.join(active_j.get('hits') or [])} "
            f"({active_j.get('sign')}, till {active_j.get('end')}) — romance trigger ON."
        )
    up_j = (jup.get("upcoming_windows") or [])[:1]
    if up_j and not active_j:
        w = up_j[0]
        parts.append(
            f"NEXT Jupiter love trigger: {w.get('sign')} "
            f"({w.get('start')}→{w.get('end')}) hits {', '.join(w.get('hits') or [])}."
        )
    active_v = ven.get("active_window")
    if active_v:
        parts.append(
            f"Venus gochar ACTIVE on {', '.join(active_v.get('hits') or [])} "
            f"({active_v.get('sign')}) — meeting/attraction month window."
        )
    elif (ven.get("upcoming_windows") or [])[:1]:
        w = ven["upcoming_windows"][0]
        parts.append(
            f"NEXT Venus romance window: {w.get('sign')} ({w.get('start')}→{w.get('end')})."
        )
    if bucket == "reconciliation" and transits.get("venus_retrograde_now"):
        parts.append("Vakri Shukra (retrograde Venus) ACTIVE — ex/reunion theme classically stronger.")
    rec = (timing or {}).get("recommended_window")
    if rec and jup.get("all_windows"):
        try:
            from transit_engine import intersect_window_with_jupiter
            hit = intersect_window_with_jupiter(rec, jup.get("all_windows") or [])
            if hit:
                parts.append(
                    f"DASHA+JUPITER LOCK: {hit.get('start')}→{hit.get('end')} "
                    f"({hit.get('jupiter_sign')}, {', '.join(hit.get('jupiter_hits') or [])})."
                )
        except Exception:
            pass
    return " ".join(p for p in parts if p)


def assess_d9_love_overlay(kundli: dict, intel: dict) -> dict:
    """Light D9 check — Venus + 7L strength for love/marriage promise."""
    why: list[str] = []
    score = 0
    try:
        from divisional_charts import compute_d9
        from event_timing.career.govt_job_engine_v1 import _house_lord

        lagna_lon = kundli.get("lagnaLongitude") or kundli.get("ascendantLongitude")
        planets = kundli.get("planets") or []
        if lagna_lon is None:
            return {"available": False}
        d9 = compute_d9(planets, float(lagna_lon))
        if not d9:
            return {"available": False}
        lagna_d9 = d9.get("_lagna") or {}
        lagna_si = lagna_d9.get("sign_idx")
        if lagna_si is None:
            return {"available": False}
        seventh_lord = _house_lord(intel, 7)

        def _d9_house(planet: str) -> Optional[int]:
            info = d9.get(planet)
            if not isinstance(info, dict):
                return None
            psi = info.get("sign_idx")
            if psi is None:
                return None
            return ((int(psi) - int(lagna_si)) % 12) + 1

        vh = _d9_house("Venus")
        if vh in {1, 5, 7, 11}:
            score += 8
            why.append(f"D9 Venus in {vh}H — marital harmony support (+8)")
        if seventh_lord:
            h7 = _d9_house(seventh_lord)
            if h7 in {1, 5, 7, 11}:
                score += 6
                why.append(f"D9 7L {seventh_lord} in {h7}H — partnership locked (+6)")
        return {"available": True, "score": score, "why": why}
    except Exception:
        return {"available": False}

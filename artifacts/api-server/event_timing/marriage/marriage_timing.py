"""
event_timing/marriage/marriage_timing.py
========================================
SHIM — old VIVAH-7 engine (4887 lines, KP-first 7-step) was permanently
removed on May 6 2026 per user direction. Replaced by Marriage Engine v2
(FILTER → VERIFY → ACTIVATE → TRIGGER, 8-step pipeline) per locked spec.

This file now does TWO things:
  1. Re-export `compute_timing_window` from `marriage_engine_v2` so all
     30+ external import sites (openai_helper, locked_facts, numerology,
     __init__) keep working without change.
  2. Provide thin back-compat aliases for symbols that the legacy
     `validator.py` QA module still imports. Helpers that no longer
     exist as free functions in v2 become safe no-op stubs that return
     None / empty — validator.py degrades gracefully instead of
     crashing on import.

For the actual engine, see `marriage_engine_v2.py`.

Public API (preserved):
    compute_timing_window(kundli, intel, kp, birth) -> dict
"""
from __future__ import annotations

from typing import Any, Optional

from .marriage_engine_v2 import (
    compute_timing_window,
    # Real helpers re-exported (validator.py uses these):
    _SIGNS,
    _SIGN_LORDS,
    _planet_sign_idx,
)

# ── Back-compat stubs for removed VIVAH-7 internals ──────────────────
# validator.py imports these names. They no longer exist as standalone
# functions in v2 (their logic is folded into the orchestrator). Stubs
# return safe defaults so QA tooling can import the module — any path
# that actually calls these gets a no-op response, NOT a crash.

def _planet_house_local(planets: list, name: str) -> Optional[int]:
    """Back-compat: simple planet-house lookup."""
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == name:
            h = p.get("house")
            if isinstance(h, int):
                return h
    return None


def _get_d9_chart(kundli: dict) -> dict:
    """Back-compat: returns D9 chart via external divisional_charts helper."""
    try:
        from divisional_charts import compute_d9  # type: ignore
        planets = (kundli or {}).get("planets") or []
        lagna_lon = (kundli or {}).get("ascendantDeg") or (kundli or {}).get("ascendantLongitude")
        try:
            lagna_lon = float(lagna_lon) if lagna_lon is not None else None
        except (TypeError, ValueError):
            lagna_lon = None
        return compute_d9(planets, lagna_lon=lagna_lon) or {}
    except Exception:
        return {}


def _get_transits_at(*_a: Any, **_kw: Any) -> dict:
    """Back-compat stub — old transit-at-date helper. Returns {} so any
    legacy validator path becomes a no-op rather than crashing."""
    return {}


def _jup_sat_marriage_cluster_check(*_a: Any, **_kw: Any) -> bool:
    """Back-compat stub — Jupiter+Saturn DT logic now lives inside
    `marriage_engine_v2._step6_double_transit`. Returns False (neutral)."""
    return False


def _dtt_score_window(*_a: Any, **_kw: Any) -> float:
    """Back-compat stub — DTT scoring now folded into v2 STEP 6.
    Returns 0.0 (neutral)."""
    return 0.0


def _extract_birth_year(birth: Any) -> Optional[int]:
    """Back-compat: best-effort birth-year extraction."""
    if isinstance(birth, dict):
        for k in ("year", "birthYear", "yearOfBirth"):
            v = birth.get(k)
            if isinstance(v, int) and 1900 <= v <= 2100:
                return v
        dob = birth.get("dob") or birth.get("birthDate")
        if isinstance(dob, str) and len(dob) >= 4:
            try:
                return int(dob[:4])
            except ValueError:
                pass
    return None


def _is_jupiter_aspect(ap_si: int, target_si: int) -> bool:
    """Back-compat: Jupiter 5/7/9 aspects."""
    diff = (target_si - ap_si) % 12 + 1
    return diff in (5, 7, 9)


def _is_saturn_aspect(ap_si: int, target_si: int) -> bool:
    """Back-compat: Saturn 3/7/10 aspects."""
    diff = (target_si - ap_si) % 12 + 1
    return diff in (3, 7, 10)


def _is_mars_aspect(ap_si: int, target_si: int) -> bool:
    """Back-compat: Mars 4/7/8 aspects."""
    diff = (target_si - ap_si) % 12 + 1
    return diff in (4, 7, 8)


__all__ = [
    "compute_timing_window",
    "_SIGNS", "_SIGN_LORDS", "_planet_sign_idx",
    "_planet_house_local", "_get_d9_chart", "_get_transits_at",
    "_jup_sat_marriage_cluster_check", "_dtt_score_window",
    "_extract_birth_year", "_is_jupiter_aspect", "_is_saturn_aspect",
    "_is_mars_aspect",
]

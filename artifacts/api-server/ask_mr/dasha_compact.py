"""Compact relationship dasha for Engine Execution + LLM (timing asks only).

Scans up to ``horizon_years`` internally; returns only current MD/AD/PD
plus a few ranked upcoming windows so prompt tokens stay small.
Sensitive lords = 1/5/7/8/12 occupants + those house lords + Venus.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

_SENSITIVE_HOUSES = frozenset({1, 5, 7, 8, 12})


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if isinstance(dt, datetime) else None


def _fmt_window(start: datetime | None, end: datetime | None) -> str:
    if not start or not end:
        return ""
    try:
        from event_timing.health.health_engine_v1 import _format_window

        return str(_format_window(start, end) or "")
    except Exception:
        return f"{start.date().isoformat()} → {end.date().isoformat()}"


def _norm_planet(name: str) -> str:
    return str(name or "").strip().title()


def _sensitive_planets(kundli: dict) -> set[str]:
    """1/5/7/8/12 occupants + house lords + Venus (relationship karaka)."""
    out: set[str] = {"Venus"}
    planets = kundli.get("planets") or []
    if not isinstance(planets, list):
        return out
    lagna_si = None
    asc = kundli.get("ascendant")
    if isinstance(asc, str):
        try:
            from stock_engine.stock_facts import _sign_idx

            lagna_si = _sign_idx(asc)
        except Exception:
            lagna_si = None
    if lagna_si is not None:
        try:
            from stock_engine.stock_facts import _house_lord

            for h in sorted(_SENSITIVE_HOUSES):
                lord = _house_lord(lagna_si, h)
                if lord:
                    out.add(_norm_planet(lord))
        except Exception:
            pass
    for p in planets:
        if not isinstance(p, dict):
            continue
        name = _norm_planet(p.get("name") or "")
        if not name:
            continue
        try:
            house = int(p.get("house") or 0)
        except (TypeError, ValueError):
            house = 0
        if house in _SENSITIVE_HOUSES:
            out.add(name)
    return out


def _window_score(w: dict[str, Any], sensitive: set[str]) -> float:
    score = 0.0
    for slot, weight in (("pd", 3.0), ("ad", 2.0), ("md", 1.0)):
        lord = _norm_planet(w.get(slot) or "")
        if lord and lord in sensitive:
            score += weight
    return score


def compute_relationship_dasha_compact(
    kundli: dict,
    *,
    horizon_years: int = 10,
    max_windows: int = 5,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Internal 10y scan → current + top windows only (token-safe for LLM)."""
    if not isinstance(kundli, dict) or not kundli:
        return {
            "schema_version": "relationship_dasha_compact_v1",
            "error": "empty_kundli",
            "current": None,
            "top_windows": [],
        }

    try:
        from event_timing.health.health_engine_v1 import (
            _current_dasha_lords,
            _flatten_dasha_chain,
        )
    except Exception as exc:
        return {
            "schema_version": "relationship_dasha_compact_v1",
            "error": f"import:{type(exc).__name__}",
            "current": None,
            "top_windows": [],
        }

    now_dt = now or datetime.utcnow()
    horizon = max(1, int(horizon_years or 10))
    limit = max(1, min(8, int(max_windows or 5)))
    horizon_end = now_dt + timedelta(days=365 * horizon)

    chain = _flatten_dasha_chain(kundli)
    current_lords = _current_dasha_lords(chain, now_dt) if chain else {}
    sensitive = _sensitive_planets(kundli)

    current_row: dict[str, Any] | None = None
    scored: list[tuple[float, dict[str, Any]]] = []

    for w in chain:
        if not isinstance(w, dict):
            continue
        start, end = w.get("start"), w.get("end")
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            continue
        if end < now_dt or start > horizon_end:
            continue
        row = {
            "md": w.get("md"),
            "ad": w.get("ad"),
            "pd": w.get("pd"),
            "window": _fmt_window(start, end),
            "start_iso": _iso(start),
            "end_iso": _iso(end),
        }
        if start <= now_dt <= end and current_row is None:
            current_row = {
                **row,
                "role": "current",
                "why": "active MD/AD/PD now",
            }
        score = _window_score(w, sensitive)
        scored.append((score, row))

    scored.sort(
        key=lambda pair: (
            -pair[0],
            pair[1].get("start_iso") or "",
        )
    )

    top: list[dict[str, Any]] = []
    seen: set[tuple] = set()
    for score, row in scored:
        key = (row.get("md"), row.get("ad"), row.get("pd"), row.get("start_iso"))
        if key in seen:
            continue
        seen.add(key)
        role = "sensitive" if score > 0 else "upcoming"
        top.append({
            **row,
            "role": role,
            "score": round(score, 1),
            "why": (
                "1/5/7/8/12 or Venus active in MD/AD/PD"
                if score > 0
                else "next window in horizon"
            ),
        })
        if len(top) >= limit:
            break

    if current_row is None and current_lords:
        current_row = {
            "md": current_lords.get("md"),
            "ad": current_lords.get("ad"),
            "pd": current_lords.get("pd"),
            "window": None,
            "start_iso": None,
            "end_iso": None,
            "role": "current",
            "why": "active MD/AD/PD now",
        }

    return {
        "schema_version": "relationship_dasha_compact_v1",
        "horizon_years": horizon,
        "max_windows": limit,
        "scanned_chain_windows": len(chain),
        "current": current_row,
        "top_windows": top,
        "llm_note": (
            "Timing-only compact dasha: use current + top_windows for WHEN asks. "
            "Do not invent dates outside these windows."
        ),
    }


def maybe_attach_dasha_compact(
    pack: dict[str, Any],
    kundli: dict,
    question: str,
    *,
    llm_intent: Optional[dict] = None,
) -> dict[str, Any]:
    """Attach dasha_timing_compact only for relationship timing questions."""
    if not isinstance(pack, dict):
        return pack
    q = (question or "").strip()
    if not q:
        return pack
    try:
        from ask_mr.timing_registry import question_requests_timing

        if not question_requests_timing(q, llm_intent):
            pack.pop("dasha_timing_compact", None)
            return pack
    except Exception:
        return pack

    pack["dasha_timing_compact"] = compute_relationship_dasha_compact(kundli)
    return pack

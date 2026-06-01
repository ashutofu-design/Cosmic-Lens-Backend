"""Load KP from kundli chart_data (DB cache) — marriage engine must not recompute only from birth."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

log = logging.getLogger(__name__)


def _valid_kp(kp: Any) -> bool:
    if not isinstance(kp, dict):
        return False
    cusps = kp.get("cusps")
    sigs = kp.get("significations")
    planets = kp.get("planets")
    return (
        isinstance(cusps, list)
        and len(cusps) == 12
        and isinstance(planets, list)
        and len(planets) == 9
        and isinstance(sigs, dict)
        and len(sigs) > 0
    )


def _merge_birth(
    birth: Any,
    kundli: Optional[dict],
    kundli_row: Any = None,
) -> Optional[dict]:
    """Build birth dict for kp_engine.calculate_kp fallback."""
    try:
        from reply_cosmo.engine_locked_to_llm.kp_locked_facts import _to_kp_input

        row_birth: dict = {}
        if kundli_row is not None:
            for k in ("dob", "tob", "time", "lat", "lon", "tz", "place"):
                v = getattr(kundli_row, k, None)
                if v is not None:
                    row_birth[k] = v
            if row_birth.get("tob") and not row_birth.get("time"):
                row_birth["time"] = row_birth["tob"]
        merged = dict(birth) if isinstance(birth, dict) else {}
        for k, v in row_birth.items():
            if merged.get(k) in (None, ""):
                merged[k] = v
        return _to_kp_input(merged, kundli)
    except Exception as exc:
        log.warning("[kp_from_chart] birth merge failed: %s", exc)
        return None


def resolve_kp(
    kundli: Optional[dict],
    kp: Optional[dict] = None,
    birth: Any = None,
    kundli_row: Any = None,
) -> dict:
    """KP resolution order: explicit arg → kundli['kp'] (DB) → compute from birth.

    Uses kp_engine.get_or_compute_kp which reads chart_data baked at kundli compute.
    """
    if _valid_kp(kp):
        return kp  # type: ignore[return-value]

    if _valid_kp((kundli or {}).get("kp")):
        log.debug("[kp_from_chart] using kundli['kp'] from chart_data/DB")
        return kundli["kp"]  # type: ignore[index]

    try:
        from kp_engine import get_or_compute_kp

        bd = _merge_birth(birth, kundli, kundli_row)
        out = get_or_compute_kp(kundli, bd) or {}
        if _valid_kp(out):
            src = "computed" if bd else "cache"
            log.info("[kp_from_chart] KP loaded via get_or_compute_kp (%s)", src)
            if isinstance(kundli, dict) and "kp" not in kundli:
                kundli["kp"] = out
            return out
    except Exception as exc:
        log.warning("[kp_from_chart] get_or_compute_kp failed: %s", exc)

    return {}


def ensure_kp_on_kundli(
    chart: dict,
    birth: Any = None,
    user: Any = None,
) -> dict:
    """Ensure chart dict carries kundli['kp'] from DB; repair chart_data if missing."""
    if not isinstance(chart, dict):
        return chart
    row = getattr(user, "kundli", None) if user is not None else None
    kp = resolve_kp(chart, chart.get("kp"), birth, row)
    if _valid_kp(kp):
        chart["kp"] = kp
    return chart

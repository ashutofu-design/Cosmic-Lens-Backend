"""Dasha NOW vs upcoming + KP CSL ↔ active MD/AD/PD cross-check (shared timing layer)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from event_timing._shared.generic_timing_engine import _flatten_dasha_chain


def _norm_planet(name: Any) -> str:
    if not name or not isinstance(name, str):
        return ""
    return name.strip().title()


def _lords_tuple(w: dict | None) -> tuple[str, ...]:
    if not isinstance(w, dict):
        return ()
    return tuple(x for x in (_norm_planet(w.get("md")), _norm_planet(w.get("ad")), _norm_planet(w.get("pd"))) if x)


def _window_active_now(w: dict, now: datetime) -> bool:
    start = w.get("start")
    end = w.get("end")
    if isinstance(start, str):
        try:
            start = datetime.fromisoformat(start.replace("Z", ""))
        except ValueError:
            start = None
    if isinstance(end, str):
        try:
            end = datetime.fromisoformat(end.replace("Z", ""))
        except ValueError:
            end = None
    if start and end:
        return start <= now <= end
    si = w.get("start_iso")
    ei = w.get("end_iso")
    if si and ei:
        try:
            s = datetime.fromisoformat(str(si).split("T")[0])
            e = datetime.fromisoformat(str(ei).split("T")[0])
            return s <= now <= e
        except ValueError:
            pass
    return False


def _find_running_dasha(kundli: dict, now: datetime) -> dict | None:
    chain = _flatten_dasha_chain(kundli if isinstance(kundli, dict) else {})
    matches = [w for w in chain if w["start"] <= now <= w["end"]]
    if not matches:
        return None
    with_pd = [w for w in matches if w.get("pd")]
    pool = with_pd if with_pd else matches
    w = min(pool, key=lambda row: (row["end"] - row["start"]).days)
    return {
        "md": w.get("md"),
        "ad": w.get("ad"),
        "pd": w.get("pd"),
        "start_iso": w["start"].strftime("%Y-%m-%d"),
        "end_iso": w["end"].strftime("%Y-%m-%d"),
        "is_running_now": True,
        "lords": "/".join(_lords_tuple(w)),
    }


def _next_csl_dasha_windows(
    kundli: dict,
    csl_lord: str,
    now: datetime,
    limit: int = 2,
) -> list[dict]:
    lord = _norm_planet(csl_lord)
    if not lord:
        return []
    out: list[dict] = []
    for w in _flatten_dasha_chain(kundli if isinstance(kundli, dict) else {}):
        if w["end"] < now:
            continue
        roles = []
        if _norm_planet(w.get("md")) == lord:
            roles.append("MD")
        if _norm_planet(w.get("ad")) == lord:
            roles.append("AD")
        if _norm_planet(w.get("pd")) == lord:
            roles.append("PD")
        if not roles:
            continue
        out.append({
            "planet": lord,
            "roles": roles,
            "md": w.get("md"),
            "ad": w.get("ad"),
            "pd": w.get("pd"),
            "start_iso": w["start"].strftime("%Y-%m-%d"),
            "end_iso": w["end"].strftime("%Y-%m-%d"),
            "is_running_now": w["start"] <= now <= w["end"],
            "days_until_start": max(0, (w["start"] - now).days),
        })
        if len(out) >= limit:
            break
    return out


def attach_dasha_kp_sync(
    raw: dict,
    kundli: dict,
    kp: Optional[dict],
) -> dict:
    """Enrich timing raw dict with running dasha + KP CSL sync tags."""
    now = datetime.utcnow()
    factors = list(raw.get("factors") or [])

    running = _find_running_dasha(kundli, now)
    cw = raw.get("current_window") if isinstance(raw.get("current_window"), dict) else None
    ts = str(raw.get("timing_source") or "")
    if cw and ts == "current_dasha_active":
        raw["dasha_running_now"] = {
            "md": cw.get("md"),
            "ad": cw.get("ad"),
            "pd": cw.get("pd"),
            "start_iso": cw.get("start_iso"),
            "end_iso": cw.get("end_iso"),
            "is_running_now": True,
            "lords": cw.get("lords")
            or "/".join(_lords_tuple(cw)),
        }
    elif running:
        raw["dasha_running_now"] = running
    else:
        raw["dasha_running_now"] = None

    running = raw.get("dasha_running_now") if isinstance(raw.get("dasha_running_now"), dict) else running

    kp_layer = raw.get("kp_layer") if isinstance(raw.get("kp_layer"), dict) else {}
    cusps = kp_layer.get("cusps") if isinstance(kp_layer.get("cusps"), dict) else {}
    csl_map: dict[str, int] = {}
    for h, v in cusps.items():
        csl = _norm_planet(v)
        if csl:
            try:
                csl_map[csl] = int(h)
            except (TypeError, ValueError):
                pass

    running_lords: set[str] = set()
    if running:
        running_lords = set(_lords_tuple(running))

    kp_active_now: list[dict] = []
    kp_upcoming: list[dict] = []
    for csl, house in csl_map.items():
        entry = {"house": house, "csl": csl}
        if csl in running_lords:
            matches = []
            if _norm_planet(running.get("md")) == csl:
                matches.append("MD")
            if _norm_planet(running.get("ad")) == csl:
                matches.append("AD")
            if _norm_planet(running.get("pd")) == csl:
                matches.append("PD")
            entry["status"] = "ACTIVE_NOW"
            entry["matches"] = matches
            kp_active_now.append(entry)
        else:
            nxt = _next_csl_dasha_windows(kundli, csl, now, limit=1)
            if nxt:
                entry["status"] = "UPCOMING"
                entry["next_window"] = nxt[0]
                kp_upcoming.append(entry)
            else:
                entry["status"] = "NOT_IN_CHAIN"
                kp_upcoming.append(entry)

    raw["kp_dasha_sync"] = {
        "cusp_sub_lords": {f"{h}H": csl for csl, h in csl_map.items()},
        "active_now": kp_active_now,
        "upcoming": kp_upcoming,
    }

    if running:
        factors.append(
            f"STEP5a RUNNING_NOW MD/AD/PD={running.get('lords')} "
            f"{running.get('start_iso')}→{running.get('end_iso')}"
        )
    else:
        factors.append("STEP5a RUNNING_NOW none in dasha chain")

    if kp_active_now:
        factors.append(
            "STEP3 KP-CSL ACTIVE="
            + ", ".join(f"{x['house']}H={x['csl']}" for x in kp_active_now)
        )
    if kp_upcoming:
        sample = kp_upcoming[0]
        nw = (sample.get("next_window") or {}) if sample.get("status") == "UPCOMING" else {}
        if nw:
            factors.append(
                f"STEP3 KP-CSL NEXT {sample.get('csl')} "
                f"{nw.get('start_iso')}→{nw.get('end_iso')} "
                f"roles={nw.get('roles')}"
            )

    tagged_windows: list[dict] = []
    for w in raw.get("next_3_windows") or []:
        if not isinstance(w, dict):
            continue
        row = dict(w)
        active = _window_active_now(row, now)
        row["is_active_now"] = active
        row["is_upcoming"] = not active
        lords = set(_lords_tuple(row))
        row["kp_csl_hits"] = sorted(
            f"{h}H={csl}" for csl, h in csl_map.items() if csl in lords
        )
        tagged_windows.append(row)
    raw["next_3_windows"] = tagged_windows

    cw = raw.get("current_window") if isinstance(raw.get("current_window"), dict) else None
    if cw:
        cw = dict(cw)
        cw["is_active_now"] = _window_active_now(cw, now)
        cw["is_upcoming"] = not cw["is_active_now"]
        cw["kp_csl_hits"] = sorted(
            f"{h}H={csl}" for csl, h in csl_map.items() if csl in set(_lords_tuple(cw))
        )
        raw["current_window"] = cw
    elif tagged_windows:
        raw["best_upcoming_window"] = tagged_windows[0]

    raw["factors"] = factors
    return raw

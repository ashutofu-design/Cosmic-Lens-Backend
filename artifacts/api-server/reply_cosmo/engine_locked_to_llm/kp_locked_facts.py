"""
kp_locked_facts.py
──────────────────
Adapter that turns the rich `kp_engine.calculate_kp()` output into a compact
"KP CROSS-CHECK" block for the LOCKED FACTS prompt.

KP (Krishnamurti Paddhati) Cuspal Sub-Lord rule — short version:
  For an event under house H to FRUCTIFY, the SUB-LORD of cusp H must
  SIGNIFY house H (i.e. that sub-lord must occupy and/or own a house in
  the relevant set for that event). If it does NOT signify, KP says the
  event is unlikely or substantially delayed regardless of what the natal
  D1 chart promises.

This module surfaces, for the houses that matter most:
   H1  — self / vitality
   H5  — children, romance, speculation
   H7  — marriage / partnership
   H10 — career / public status
   H11 — gains, fulfilment of desires

For each, it emits:
   • cusp sub-lord (planet)
   • whether that sub-lord signifies the cusp's house
   • a one-line VERDICT — "KP confirms" / "KP denies" / "KP partial"

Robustness
──────────
Returns "" (empty) if birth data is insufficient for cusp computation.
NEVER raises — KP block is best-effort enrichment, not core path.
"""
from __future__ import annotations
from typing import Any
import re

# Houses we always cross-check (most question topics map to one of these)
_KEY_HOUSES = (1, 2, 5, 7, 10, 11)

# Per-event "signification set" — which house being in the sub-lord's
# significations counts as KP PROMISE for that event.
# (Standard KP convention from K.S. Krishnamurti's writings.)
_EVENT_HOUSES = {
    1:  {1, 5, 9, 11},          # self, vitality, fortune
    2:  {2, 6, 10, 11},         # money / accumulation
    5:  {2, 5, 11},             # children, speculation gains
    7:  {2, 7, 11},             # marriage (classical KP triplet)
    10: {2, 6, 10, 11},         # career fruition
    11: {2, 6, 10, 11},         # gains
}

# "Negative / denial" houses per event — if sub-lord signifies these AND
# none of the event-houses, KP says STRONG denial. If it signifies BOTH
# event AND denial houses, the verdict softens to PARTIAL (obstruction).
_NEGATIVE_HOUSES = {
    1:  {6, 8, 12},
    2:  {8, 12},
    5:  {1, 4, 8, 10, 12},      # 4=loss-of-5, 8=loss-of-12-from-5 etc.
    7:  {1, 6, 10, 12},         # classical Krishnamurti negation set for marriage
    10: {3, 5, 9},               # 12-from-each-of-the-event houses
    11: {5, 8, 12},
}

# AM/PM string patterns
_AMPM_RE = re.compile(r"\b(AM|PM|am|pm)\b")


def _missing(v) -> bool:
    """True only when v is None or an empty string. Treats numeric 0 as VALID
    (e.g. tz=0 for UTC, lat=0 at the equator)."""
    return v is None or (isinstance(v, str) and v.strip() == "")


def _to_kp_input(birth: dict | None, kundli: dict | None) -> dict | None:
    """
    Build the dict that calculate_kp() expects:
      day, month, year, hour, minute, ampm, lat, lon, tz
    Tries `birth` first (structured), then falls back to parsing kundli's
    `dob` ("15 Jan 1990"), `time` ("06:30 AM"), and lat/lon/tz fields.
    Returns None if anything critical is missing.
    """
    src: dict[str, Any] = dict(birth or {})
    kdict: dict = kundli if isinstance(kundli, dict) else {}

    # If birth doesn't have lat/lon/tz, try kundli (saved kundlis carry these)
    for k in ("lat", "lon", "tz"):
        if _missing(src.get(k)):
            v = kdict.get(k)
            if not _missing(v):
                src[k] = v

    # Direct structured fields
    if all(not _missing(src.get(k)) for k in
           ("day", "month", "year", "hour", "minute", "ampm", "lat", "lon", "tz")):
        try:
            return {
                "day":    int(src["day"]),
                "month":  int(src["month"]),
                "year":   int(src["year"]),
                "hour":   int(src["hour"]),
                "minute": int(src["minute"]),
                "ampm":   str(src["ampm"]).upper(),
                "lat":    float(src["lat"]),
                "lon":    float(src["lon"]),
                "tz":     float(src["tz"]),
            }
        except (TypeError, ValueError):
            pass

    # Fallback: parse from string fields (works even if kundli is None — birth.dob/time alone is OK)
    dob_s  = kdict.get("dob")  or src.get("dob")
    time_s = kdict.get("time") or src.get("time")
    lat = src.get("lat") if not _missing(src.get("lat")) else kdict.get("lat")
    lon = src.get("lon") if not _missing(src.get("lon")) else kdict.get("lon")
    tz  = src.get("tz")  if not _missing(src.get("tz"))  else kdict.get("tz")
    if _missing(dob_s) or _missing(time_s) or _missing(lat) or _missing(lon) or _missing(tz):
        return None

    # dob "15 Jan 1990"
    try:
        from datetime import datetime
        dt = datetime.strptime(str(dob_s).strip(), "%d %b %Y")
    except ValueError:
        try:
            dt = datetime.strptime(str(dob_s).strip(), "%Y-%m-%d")
        except ValueError:
            return None

    # time "06:30 AM"
    t = str(time_s).strip()
    m = _AMPM_RE.search(t)
    ampm = (m.group(1).upper() if m else "AM")
    t_clean = _AMPM_RE.sub("", t).strip()
    try:
        hh, mm = t_clean.split(":")[:2]
        hour, minute = int(hh), int(mm)
    except Exception:
        return None

    return {
        "day": dt.day, "month": dt.month, "year": dt.year,
        "hour": hour, "minute": minute, "ampm": ampm,
        "lat": float(lat), "lon": float(lon), "tz": float(tz),
    }


def _verdict_for(house: int, sub_lord: str, sigs: dict) -> tuple[str, list[int], list[int]]:
    """
    Classical-KP gating (K.S. Krishnamurti):
       - PROMISE = sub-lord signifies ANY house in the event set.
       - DENIAL  = sub-lord signifies houses ONLY in the negative set
                   (no overlap with event set at all).
       - OBSTRUCTION (PARTIAL) = sub-lord signifies BOTH event AND negative
                                 houses, indicating fructification with delay/struggle.
    Returns (verdict, event_overlap, negative_overlap).
    """
    if not isinstance(sigs, dict):
        return "UNKNOWN", [], []
    sig_planet = sigs.get(sub_lord) or {}
    if not isinstance(sig_planet, dict):
        return "UNKNOWN", [], []
    pl_raw = sig_planet.get("pl") or []
    pl_houses = {int(x) for x in pl_raw if isinstance(x, (int, float))}
    needed   = _EVENT_HOUSES.get(house, {house})
    negative = _NEGATIVE_HOUSES.get(house, set())
    ev_over  = sorted(pl_houses & needed)
    neg_over = sorted(pl_houses & negative)

    if not ev_over:
        return "DENIES", [], neg_over
    if neg_over:
        return "PARTIAL", ev_over, neg_over
    # No negative-house involvement AND at least one event-house signified → strong promise
    return "CONFIRMS", ev_over, neg_over


def compute_kp_summary(birth: dict | None, kundli: dict | None) -> dict[str, Any]:
    inp = _to_kp_input(birth, kundli)
    if not inp:
        return {}
    try:
        # Phase 2.8.58: prefer cached kundli["kp"] over Swiss Ephemeris recompute.
        # get_or_compute_kp validates the cached payload (12 cusps, >=7 planets)
        # and falls back to fresh calculate_kp(inp) if cache is missing/malformed.
        from kp_engine import get_or_compute_kp  # type: ignore
        kp = get_or_compute_kp(kundli, inp)
        if not kp:
            return {}
    except Exception as exc:  # noqa: BLE001
        print(f"[kp_locked_facts] get_or_compute_kp failed: {exc}")
        return {}

    cusps_raw = kp.get("cusps") if isinstance(kp, dict) else None
    sigs      = kp.get("significations") if isinstance(kp, dict) else None
    sigs      = sigs if isinstance(sigs, dict) else {}
    cusps: dict = {}
    if isinstance(cusps_raw, list):
        for c in cusps_raw:
            if isinstance(c, dict) and isinstance(c.get("house"), int):
                cusps[c["house"]] = c

    out: dict[int, dict[str, Any]] = {}
    for h in _KEY_HOUSES:
        c = cusps.get(h)
        if not isinstance(c, dict):
            continue
        sb = c.get("sb")
        if not isinstance(sb, str):
            continue
        verdict, ev_over, neg_over = _verdict_for(h, sb, sigs)
        out[h] = {
            "cusp_sign":  c.get("sign"),
            "cusp_deg":   c.get("degree"),
            "sub_lord":   sb,
            "verdict":    verdict,
            "signifies":  ev_over,
            "obstructs":  neg_over,
        }
    return {"houses": out, "ayanamsa": kp.get("ayanamsa") if isinstance(kp, dict) else None}


def format_kp_summary(kp_summary: dict) -> str:
    if not isinstance(kp_summary, dict):
        return ""
    houses = kp_summary.get("houses") if isinstance(kp_summary.get("houses"), dict) else {}
    if not houses:
        return ""
    lines = ["▸ KP CROSS-CHECK (Cuspal Sub-Lord — Krishnamurti Paddhati):"]
    label = {1: "Self/vitality", 2: "Money", 5: "Children/speculation",
             7: "Marriage", 10: "Career", 11: "Gains/fulfilment"}
    for h in (1, 2, 5, 7, 10, 11):
        info = houses.get(h)
        if not isinstance(info, dict):
            continue
        ev = info.get("signifies") or []
        ng = info.get("obstructs") or []
        ev_txt = ("event-houses H" + ", H".join(str(x) for x in ev)) if ev else "no event-house"
        ng_txt = (" / negative H" + ", H".join(str(x) for x in ng)) if ng else ""
        lines.append(
            f"   ▸ H{h} ({label[h]}): cusp sub-lord = {info.get('sub_lord')} "
            f"→ {info.get('verdict')} (signifies {ev_txt}{ng_txt})"
        )
    lines.append("   Legend: CONFIRMS = clean promise (event-houses signified, no negative);  "
                 "PARTIAL = promise WITH obstruction (delay/struggle);  "
                 "DENIES = no event-house signified (unlikely / substantially delayed).")
    return "\n".join(lines)

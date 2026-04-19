"""
transit_engine.py — Live planetary transit windows (sidereal/Lahiri).

Used by marriage_engine to find the Jupiter "trigger" — periods when
Jupiter sidereally transits houses 1, 5, or 7 from the natal Lagna or
natal Moon. These houses are classically considered marriage-trigger
positions for Jupiter (kalyana karaka — the universal benefic for
auspicious life events). Intersecting these with the next favourable
Maha-Antardasha window tightens the timing prediction substantially.

Pure stateless functions. Uses pyswisseph in sidereal Lahiri mode
(already set globally in kundli_engine — but we set it again defensively
in case this module is imported first).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import swisseph as swe

# Defensive — match kundli_engine's ayanamsa setting.
swe.set_sid_mode(swe.SIDM_LAHIRI)

_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL


def _to_jd(d: datetime) -> float:
    return swe.julday(d.year, d.month, d.day, d.hour + d.minute / 60.0)


def _sidereal_lon(planet_id: int, when: datetime) -> float:
    jd = _to_jd(when)
    pos, _ = swe.calc_ut(jd, planet_id, _FLAGS)
    return float(pos[0]) % 360.0


def _sign_idx(lon: float) -> int:
    return int(lon / 30.0) % 12


def jupiter_sign_changes(start: datetime, years_ahead: int = 5) -> list[dict]:
    """
    Walk forward in 5-day steps; whenever Jupiter's sign-index changes,
    record the transition. Returns a list of {start, end, sign_idx} where
    each entry is one continuous occupancy of a sign.

    Jupiter spends ~12-13 months per sign, so a 5-day grid has ample
    resolution for month-precision marriage timing.
    """
    end_dt = start + timedelta(days=int(365.25 * years_ahead))
    cursor = start
    cur_sign = _sign_idx(_sidereal_lon(swe.JUPITER, cursor))
    seg_start = cursor

    out: list[dict] = []
    step = timedelta(days=5)
    while cursor < end_dt:
        nxt = cursor + step
        new_sign = _sign_idx(_sidereal_lon(swe.JUPITER, nxt))
        if new_sign != cur_sign:
            # Binary-search the day-precise transition between cursor and nxt.
            lo, hi = cursor, nxt
            for _ in range(8):
                mid = lo + (hi - lo) / 2
                if _sign_idx(_sidereal_lon(swe.JUPITER, mid)) == cur_sign:
                    lo = mid
                else:
                    hi = mid
            out.append({
                "start":    seg_start.strftime("%Y-%m-%d"),
                "end":      hi.strftime("%Y-%m-%d"),
                "sign_idx": cur_sign,
            })
            seg_start = hi
            cur_sign = new_sign
        cursor = nxt

    out.append({
        "start":    seg_start.strftime("%Y-%m-%d"),
        "end":      end_dt.strftime("%Y-%m-%d"),
        "sign_idx": cur_sign,
    })
    return out


def jupiter_marriage_trigger_windows(lagna_sign_idx: int,
                                     moon_sign_idx: Optional[int],
                                     start: Optional[datetime] = None,
                                     years_ahead: int = 3) -> list[dict]:
    """
    Return Jupiter transit segments where Jupiter occupies a sign that is
    the 1st, 5th, or 7th *from* the natal Lagna or the natal Moon.

    These are the classical "marriage trigger" houses for Jupiter:
      - 7th from Lagna  → directly activates the marriage house
      - 7th from Moon   → activates the emotional/partnership axis
      - 5th from Lagna/Moon → progeny + romance house
      - 1st from Lagna/Moon → personal renewal / new chapter

    Output: list of {start, end, sign, hits[]} where hits names which
    references it satisfies (e.g. ["L7", "M5"]).
    """
    SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
             "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    start = start or datetime.utcnow()
    target_offsets = {0, 4, 6}  # 1st, 5th, 7th (0-indexed)

    targets: dict[int, list[str]] = {}
    for off in target_offsets:
        s_l = (lagna_sign_idx + off) % 12
        targets.setdefault(s_l, []).append(f"L{off + 1}")
        if moon_sign_idx is not None:
            s_m = (moon_sign_idx + off) % 12
            targets.setdefault(s_m, []).append(f"M{off + 1}")

    segments = jupiter_sign_changes(start, years_ahead=years_ahead)
    out: list[dict] = []
    for seg in segments:
        sidx = seg["sign_idx"]
        if sidx in targets:
            out.append({
                "start": seg["start"],
                "end":   seg["end"],
                "sign":  SIGNS[sidx],
                "hits":  sorted(set(targets[sidx])),
            })
    return out


def _date(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.split("T")[0])
    except Exception:
        return None


def intersect_window_with_jupiter(dasha_window: dict,
                                  jup_windows: list[dict]) -> Optional[dict]:
    """
    Intersect a Dasha window {start: 'YYYY-MM', end: 'YYYY-MM'} with the
    list of Jupiter trigger windows. Returns the single intersection
    block (in YYYY-MM-DD precision) along with which Jupiter hit caused it,
    or None if no intersection exists.
    """
    if not dasha_window:
        return None
    d_s = _date((dasha_window.get("start") or "") + "-01")
    d_e_raw = (dasha_window.get("end") or "") + "-28"
    d_e = _date(d_e_raw)
    if not d_s or not d_e:
        return None

    best: Optional[dict] = None
    for jw in (jup_windows or []):
        j_s = _date(jw.get("start") or "")
        j_e = _date(jw.get("end") or "")
        if not j_s or not j_e:
            continue
        a = max(d_s, j_s)
        b = min(d_e, j_e)
        if a >= b:
            continue
        cand = {
            "start": a.strftime("%Y-%m-%d"),
            "end":   b.strftime("%Y-%m-%d"),
            "jupiter_sign": jw.get("sign"),
            "jupiter_hits": jw.get("hits"),
            "days":  (b - a).days,
        }
        if best is None or cand["days"] > best["days"]:
            best = cand
    return best

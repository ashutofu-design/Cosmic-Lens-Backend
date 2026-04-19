"""
Sprint 27 — Special Lagnas (computable without birth lat/lon)

Buildable from natal longitudes only:
  • Sree Lagna  — Jaimini wealth/prosperity ascendant
  • Indu Lagna  — wealth ascendant (Chandra Yogini)
  • Bhrigu Bindu — Rahu-Moon midpoint (event/timing point)
  • Karakamsa Lagna — sign of Atmakaraka in D9
  • Pada Lagna of all 12 houses verification

Deferred (need sunrise → lat/lon): Bhava Lagna, Hora Lagna, Ghati Lagna,
Vighati Lagna, Pranapada Lagna — all require Ishtakaal from sunrise.
"""
from __future__ import annotations
from typing import Any

SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORD = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
             "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
INDU_KALA = {"Sun": 30, "Moon": 16, "Mars": 6, "Mercury": 8,
             "Jupiter": 10, "Venus": 12, "Saturn": 1}
NAKSHATRA_LEN = 360.0 / 27.0  # 13.3333°


def _planet_lon(planets: list, name: str) -> float | None:
    for p in planets:
        if isinstance(p, dict) and p.get("name") == name:
            v = p.get("longitude")
            try:
                return float(v) % 360.0
            except Exception:
                return None
    return None


def _planet_sign_idx(planets: list, name: str) -> int | None:
    for p in planets:
        if isinstance(p, dict) and p.get("name") == name:
            sn = p.get("sign")
            if isinstance(sn, str) and sn in SIGN_NAMES:
                return SIGN_NAMES.index(sn)
    return None


def _lagna_longitude(kundli: dict) -> float | None:
    """Try to derive lagna longitude from sign + degrees fields."""
    asc = kundli.get("ascendant")
    if not isinstance(asc, str) or asc not in SIGN_NAMES:
        return None
    base = SIGN_NAMES.index(asc) * 30.0
    # Try ascendantDeg (string like "12°34'")
    deg_str = kundli.get("ascendantDeg") or kundli.get("ascendant_degrees")
    if isinstance(deg_str, str):
        try:
            d = deg_str.split("°")[0].strip()
            m = "0"
            if "°" in deg_str and "'" in deg_str:
                m = deg_str.split("°")[1].split("'")[0].strip() or "0"
            return base + float(d) + float(m) / 60.0
        except Exception:
            pass
    # Try numeric
    al = kundli.get("ascendant_longitude") or kundli.get("ascendantLongitude")
    try:
        if al is not None:
            return float(al) % 360.0
    except Exception:
        pass
    return base + 15.0  # mid-sign fallback


def compute_sree_lagna(kundli: dict) -> dict[str, Any]:
    """Sree Lagna = Lagna longitude + (Moon's progress within its nakshatra) × 27
    Sree Lagna degree = (Moon_lon mod 13.333°) × 27 + Lagna_lon, mod 360°."""
    moon_lon = _planet_lon(kundli.get("planets") or [], "Moon")
    lag_lon = _lagna_longitude(kundli)
    if moon_lon is None or lag_lon is None:
        return {"available": False}
    nak_progress = moon_lon % NAKSHATRA_LEN  # 0..13.333°
    sl_lon = (lag_lon + nak_progress * 27.0) % 360.0
    sign_idx = int(sl_lon // 30)
    return {
        "available": True,
        "longitude": round(sl_lon, 4),
        "sign": SIGN_NAMES[sign_idx],
        "degree_in_sign": round(sl_lon - sign_idx * 30, 4),
        "lord": SIGN_LORD[sign_idx],
        "interpretation": "Wealth-prosperity ascendant; lord placement & strength → financial growth",
    }


def compute_indu_lagna(kundli: dict) -> dict[str, Any]:
    """Indu Lagna (BPHS):
       Step 1: 9th house from Lagna → its lord → its kala
       Step 2: 9th house from Moon → its lord → its kala
       Step 3: Sum kalas, mod 12 → count signs from Moon (this is Indu Lagna)."""
    planets = kundli.get("planets") or []
    asc = kundli.get("ascendant")
    if not isinstance(asc, str) or asc not in SIGN_NAMES:
        return {"available": False}
    moon_si = _planet_sign_idx(planets, "Moon")
    if moon_si is None:
        return {"available": False}
    lag_si = SIGN_NAMES.index(asc)
    ninth_lag = (lag_si + 8) % 12
    ninth_moon = (moon_si + 8) % 12
    lord_lag = SIGN_LORD[ninth_lag]
    lord_moon = SIGN_LORD[ninth_moon]
    k1 = INDU_KALA.get(lord_lag, 0)
    k2 = INDU_KALA.get(lord_moon, 0)
    total = (k1 + k2) % 12
    if total == 0:
        total = 12
    indu_si = (moon_si + total - 1) % 12
    return {
        "available": True,
        "ninth_from_lagna": SIGN_NAMES[ninth_lag],
        "ninth_from_lagna_lord": lord_lag,
        "kala_from_lagna_lord": k1,
        "ninth_from_moon": SIGN_NAMES[ninth_moon],
        "ninth_from_moon_lord": lord_moon,
        "kala_from_moon_lord": k2,
        "total_kala_mod_12": total,
        "indu_lagna_sign": SIGN_NAMES[indu_si],
        "indu_lagna_lord": SIGN_LORD[indu_si],
        "interpretation": "Wealth-yoga ascendant; planets in/aspecting Indu Lagna → financial gains",
    }


def compute_bhrigu_bindu(kundli: dict) -> dict[str, Any]:
    """Bhrigu Bindu = midpoint of Rahu and Moon (shorter arc).
    Highly sensitive event-trigger point (transits over BB activate karma)."""
    planets = kundli.get("planets") or []
    rahu = _planet_lon(planets, "Rahu")
    moon = _planet_lon(planets, "Moon")
    if rahu is None or moon is None:
        return {"available": False}
    diff = (moon - rahu) % 360.0
    if diff > 180:
        bb = (rahu - (360 - diff) / 2) % 360
    else:
        bb = (rahu + diff / 2) % 360
    sign_idx = int(bb // 30)
    return {
        "available": True,
        "longitude": round(bb, 4),
        "sign": SIGN_NAMES[sign_idx],
        "degree_in_sign": round(bb - sign_idx * 30, 4),
        "lord": SIGN_LORD[sign_idx],
        "interpretation": "Sensitive karmic event-trigger point (Rahu-Moon midpoint); "
                          "transits of major planets over this degree activate destined events",
    }


def compute_karakamsa_lagna(kundli: dict) -> dict[str, Any]:
    """Karakamsa = sign of Atmakaraka in D9 (Navamsha).
    Reveals soul-purpose/dharma."""
    planets = kundli.get("planets") or []
    karakas = []
    for p in planets:
        nm = p.get("name")
        lon = _planet_lon(planets, nm) if nm else None
        if nm in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn") and lon is not None:
            deg_in_sign = lon % 30
            karakas.append((nm, deg_in_sign))
    if not karakas:
        return {"available": False}
    karakas.sort(key=lambda x: x[1], reverse=True)
    ak_name = karakas[0][0]
    # Find AK in D9
    d9 = kundli.get("divisionalCharts", {}).get("D9") or kundli.get("divisionalCharts", {}).get("d9")
    if isinstance(d9, dict):
        for plist_key in ("planets", "Planets"):
            plist = d9.get(plist_key)
            if isinstance(plist, list):
                for pp in plist:
                    if isinstance(pp, dict) and pp.get("name") == ak_name:
                        ks = pp.get("sign")
                        if ks in SIGN_NAMES:
                            return {
                                "available": True,
                                "atmakaraka": ak_name,
                                "karakamsa_sign": ks,
                                "karakamsa_lord": SIGN_LORD[SIGN_NAMES.index(ks)],
                                "interpretation": "Soul's dharmic theme; planets in/aspecting Karakamsa show "
                                                  "spiritual inclination & life mission",
                            }
    return {"available": True, "atmakaraka": ak_name,
            "karakamsa_sign": None, "note": "D9 placement of AK not found in divisionalCharts"}


def compute_special_lagnas(kundli: dict) -> dict[str, Any]:
    return {
        "available": True,
        "sree_lagna": compute_sree_lagna(kundli),
        "indu_lagna": compute_indu_lagna(kundli),
        "bhrigu_bindu": compute_bhrigu_bindu(kundli),
        "karakamsa": compute_karakamsa_lagna(kundli),
        "deferred": ["Bhava Lagna", "Hora Lagna", "Ghati Lagna",
                     "Vighati Lagna", "Pranapada Lagna"],
        "deferred_reason": "Need sunrise → birth lat/lon to compute Ishtakaal",
    }


def format_special_lagnas_summary(r: dict) -> str:
    if not isinstance(r, dict) or not r.get("available"):
        return ""
    lines = ["── SPECIAL LAGNAS (Sprint 27) ──"]
    sl = r.get("sree_lagna") or {}
    if sl.get("available"):
        lines.append(f"Sree Lagna (wealth): {sl['sign']} {sl['degree_in_sign']:.2f}° "
                     f"(lord {sl['lord']}) — financial prosperity ascendant")
    il = r.get("indu_lagna") or {}
    if il.get("available"):
        lines.append(f"Indu Lagna (wealth-yoga): {il['indu_lagna_sign']} "
                     f"(lord {il['indu_lagna_lord']}) — kala-sum from "
                     f"{il['ninth_from_lagna_lord']}({il['kala_from_lagna_lord']}) + "
                     f"{il['ninth_from_moon_lord']}({il['kala_from_moon_lord']}) = "
                     f"{il['total_kala_mod_12']}")
    bb = r.get("bhrigu_bindu") or {}
    if bb.get("available"):
        lines.append(f"Bhrigu Bindu (event-trigger): {bb['sign']} {bb['degree_in_sign']:.2f}° "
                     f"(Rahu-Moon midpoint) — transits here activate destiny")
    ka = r.get("karakamsa") or {}
    if ka.get("available"):
        ks = ka.get("karakamsa_sign")
        if ks:
            lines.append(f"Karakamsa (soul-dharma): AK={ka['atmakaraka']} in D9 {ks} "
                         f"(lord {ka.get('karakamsa_lord')})")
        else:
            lines.append(f"Karakamsa: AK={ka['atmakaraka']} (D9 sign unavailable)")
    lines.append(f"Deferred (need lat/lon): {', '.join(r.get('deferred', []))}")
    return "\n".join(lines)

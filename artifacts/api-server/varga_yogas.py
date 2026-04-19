"""
Sprint 15 — Per-varga yoga / dosha detection
==============================================
Scans key divisional charts (D1, D9, D10, D24, D60) for classical yogas:

  • Pancha Mahapurusha Yoga
        Mars / Mercury / Jupiter / Venus / Saturn in OWN or EXALTATION sign,
        placed in a kendra (1/4/7/10) from the varga lagna.
        →  Ruchaka (Mars), Bhadra (Merc), Hamsa (Jup),
           Malavya (Venus), Sasa (Saturn)

  • Simplified Raj Yoga (per varga)
        A kendra-lord AND a trikona-lord (1/5/9) of the varga conjunct in
        the same varga sign.

  • Vipreet Raj Yoga (per varga)
        Two of {6L, 8L, 12L} of the varga conjunct in 6th, 8th or 12th
        of the varga (mutual exchange in dusthanas).

Output is a per-varga list of yoga dicts, plus a summary string for the
LOCKED FACTS block.
"""
from typing import Any

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]

# Pancha Mahapurusha rules
PMP = {
    "Mars":    {"yoga": "Ruchaka",  "own": {"Aries", "Scorpio"},      "exalt": "Capricorn"},
    "Mercury": {"yoga": "Bhadra",   "own": {"Gemini", "Virgo"},       "exalt": "Virgo"},
    "Jupiter": {"yoga": "Hamsa",    "own": {"Sagittarius", "Pisces"}, "exalt": "Cancer"},
    "Venus":   {"yoga": "Malavya",  "own": {"Taurus", "Libra"},       "exalt": "Pisces"},
    "Saturn":  {"yoga": "Sasa",     "own": {"Capricorn", "Aquarius"}, "exalt": "Libra"},
}

KENDRAS  = {1, 4, 7, 10}
TRIKONAS = {1, 5, 9}
DUSTHANA = {6, 8, 12}


def _house_from(planet_idx: int, lagna_idx: int) -> int:
    return ((planet_idx - lagna_idx) % 12) + 1


def detect_pancha_mahapurusha(chart: dict, varga_label: str) -> list[dict]:
    """A varga chart shape: {planet: {sign, sign_idx}, "_lagna": {sign_idx}}"""
    if not isinstance(chart, dict):
        return []
    lagna = chart.get("_lagna") or {}
    lagna_idx = lagna.get("sign_idx")
    if lagna_idx is None:
        return []
    found = []
    for planet, rules in PMP.items():
        info = chart.get(planet)
        if not isinstance(info, dict):
            continue
        sign_name = info.get("sign")
        sign_idx  = info.get("sign_idx")
        if sign_idx is None:
            continue
        is_own_or_exalt = (sign_name in rules["own"]
                           or sign_name == rules["exalt"])
        if not is_own_or_exalt:
            continue
        house = _house_from(sign_idx, lagna_idx)
        if house in KENDRAS:
            placement = "Exalted" if sign_name == rules["exalt"] else "Own sign"
            found.append({
                "yoga":    f"{rules['yoga']} Yoga",
                "planet":  planet,
                "sign":    sign_name,
                "house":   house,
                "varga":   varga_label,
                "via":     placement,
            })
    return found


def detect_raj_yoga(chart: dict, varga_label: str) -> list[dict]:
    """Kendra-lord and trikona-lord conjunct in same varga sign."""
    if not isinstance(chart, dict):
        return []
    lagna = chart.get("_lagna") or {}
    lagna_idx = lagna.get("sign_idx")
    if lagna_idx is None:
        return []
    # find kendra-lords and trikona-lords (varga lords of houses 1/4/5/7/9/10)
    kendra_lords  = set()
    trikona_lords = set()
    for h in (1, 4, 7, 10):
        kendra_lords.add(SIGN_LORDS[(lagna_idx + h - 1) % 12])
    for h in (1, 5, 9):
        trikona_lords.add(SIGN_LORDS[(lagna_idx + h - 1) % 12])

    # group planets by their sign in varga
    by_sign: dict[int, list[str]] = {}
    for planet, info in chart.items():
        if planet == "_lagna" or not isinstance(info, dict):
            continue
        idx = info.get("sign_idx")
        if idx is None:
            continue
        by_sign.setdefault(idx, []).append(planet)

    found = []
    for idx, planets_in_sign in by_sign.items():
        ks = [p for p in planets_in_sign if p in kendra_lords]
        ts = [p for p in planets_in_sign if p in trikona_lords]
        # Need at least one kendra-lord + one trikona-lord, NOT the same planet
        pairs = [(k, t) for k in ks for t in ts if k != t]
        if pairs:
            k, t = pairs[0]
            found.append({
                "yoga":    "Raj Yoga",
                "planets": sorted({k, t}),
                "sign":    SIGNS[idx],
                "house":   _house_from(idx, lagna_idx),
                "varga":   varga_label,
                "note":    f"{k} (kendra-lord) + {t} (trikona-lord) conjunct",
            })
    return found


def detect_vipreet_raj_yoga(chart: dict, varga_label: str) -> list[dict]:
    """Two of {6L, 8L, 12L} conjunct in a dusthana (6/8/12)."""
    if not isinstance(chart, dict):
        return []
    lagna = chart.get("_lagna") or {}
    lagna_idx = lagna.get("sign_idx")
    if lagna_idx is None:
        return []
    dust_lords = {SIGN_LORDS[(lagna_idx + h - 1) % 12] for h in DUSTHANA}

    by_sign: dict[int, list[str]] = {}
    for planet, info in chart.items():
        if planet == "_lagna" or not isinstance(info, dict):
            continue
        idx = info.get("sign_idx")
        if idx is None:
            continue
        by_sign.setdefault(idx, []).append(planet)

    found = []
    for idx, planets_in_sign in by_sign.items():
        if _house_from(idx, lagna_idx) not in DUSTHANA:
            continue
        dls = sorted(p for p in planets_in_sign if p in dust_lords)
        if len(dls) >= 2:
            found.append({
                "yoga":    "Vipreet Raj Yoga",
                "planets": dls,
                "sign":    SIGNS[idx],
                "house":   _house_from(idx, lagna_idx),
                "varga":   varga_label,
                "note":    f"dusthana-lords {', '.join(dls)} mutual exchange "
                           f"(adversity → unexpected rise)",
            })
    return found


def detect_all_varga_yogas(planets: list, lagna_lon: float | None,
                           lagna_sign: str | None = None) -> dict:
    """
    Run all yoga detectors across D1, D9, D10, D24, D60 vargas.
    Returns:
      {
        "pancha_mahapurusha": [...],
        "raj_yoga":           [...],
        "vipreet_raj_yoga":   [...],
        "by_varga": {"D1": [...all yogas...], ...}
      }
    """
    try:
        from divisional_charts import (compute_d9, compute_d10,  # type: ignore
                                       compute_d24, compute_d60,
                                       _compute_chart, _sign_idx_from_lon,
                                       _SIGN_NAMES)
    except Exception:
        return {}

    if not planets:
        return {}

    # Resolve D1 lagna sign idx (from longitude OR fallback to sign string)
    d1_lagna_idx = None
    if isinstance(lagna_lon, (int, float)):
        d1_lagna_idx = _sign_idx_from_lon(float(lagna_lon))
    elif lagna_sign:
        try:
            d1_lagna_idx = SIGNS.index(str(lagna_sign).strip().capitalize())
        except ValueError:
            d1_lagna_idx = None
    if d1_lagna_idx is None:
        return {}

    # Build D1 from raw planet longitudes (sign-only fallback if lon missing)
    d1: dict[str, Any] = {}
    for p in planets:
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        lon = p.get("longitude")
        sign = p.get("sign") or p.get("sign_name")
        if not nm:
            continue
        if isinstance(lon, (int, float)):
            s_idx = _sign_idx_from_lon(float(lon))
        elif sign:
            try:
                s_idx = SIGNS.index(str(sign).strip().capitalize())
            except ValueError:
                continue
        else:
            continue
        d1[nm] = {"sign": SIGNS[s_idx], "sign_idx": s_idx}
    d1["_lagna"] = {"sign": SIGNS[d1_lagna_idx], "sign_idx": d1_lagna_idx}

    charts: dict = {"D1": d1}
    # Higher vargas need real longitude — only attempt if lagna_lon present
    if isinstance(lagna_lon, (int, float)):
        charts["D9"]  = compute_d9(planets, lagna_lon)
        charts["D10"] = compute_d10(planets, lagna_lon)
        charts["D24"] = compute_d24(planets, lagna_lon)
        charts["D60"] = compute_d60(planets, lagna_lon)

    pmp_all, raj_all, vip_all, by_varga = [], [], [], {}
    for label, ch in charts.items():
        pmp = detect_pancha_mahapurusha(ch, label)
        raj = detect_raj_yoga(ch, label)
        vip = detect_vipreet_raj_yoga(ch, label)
        pmp_all.extend(pmp); raj_all.extend(raj); vip_all.extend(vip)
        all_in = pmp + raj + vip
        if all_in:
            by_varga[label] = all_in

    return {
        "pancha_mahapurusha": pmp_all,
        "raj_yoga":           raj_all,
        "vipreet_raj_yoga":   vip_all,
        "by_varga":           by_varga,
    }


def format_varga_yogas_summary(result: dict) -> str:
    if not result:
        return ""
    lines = []
    if result.get("pancha_mahapurusha"):
        lines.append(
            "   ▸ Pancha Mahapurusha: "
            + "; ".join(
                f"{y['yoga']} ({y['planet']} {y['via']} in {y['sign']}, "
                f"H{y['house']} of {y['varga']})"
                for y in result["pancha_mahapurusha"][:5]
            )
        )
    if result.get("raj_yoga"):
        lines.append(
            "   ▸ Raj Yoga: "
            + "; ".join(
                f"{', '.join(y['planets'])} in {y['sign']} "
                f"(H{y['house']} of {y['varga']})"
                for y in result["raj_yoga"][:5]
            )
        )
    if result.get("vipreet_raj_yoga"):
        lines.append(
            "   ▸ Vipreet Raj Yoga: "
            + "; ".join(
                f"{', '.join(y['planets'])} in {y['sign']} "
                f"(H{y['house']} of {y['varga']})"
                for y in result["vipreet_raj_yoga"][:5]
            )
        )
    if not lines:
        return ""
    return ("▸ PER-VARGA YOGAS (classical Mahapurusha / Raj / Vipreet "
            "across D1, D9, D10, D24, D60):\n" + "\n".join(lines))

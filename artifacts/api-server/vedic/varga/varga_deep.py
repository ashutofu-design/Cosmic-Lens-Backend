"""
Sprint 22 — Per-Varga Deep Analytics
Builds on existing 16 varga charts (D1..D60).

Adds three new layers per major varga (D9 Marriage, D10 Career, D24 Education,
D60 Karma — the four "drekkana of strength" beyond D1):

  1) varga_aspects(varga_chart)   — Parashari planet-to-planet drishti within
     that varga (7th full + special 4/8 Mars, 5/9 Jupiter, 3/10 Saturn).

  2) varga_ashtakavarga(varga)    — BAV/SAV bindus computed using each
     planet's varga sign (reuses existing compute_ashtakavarga engine).

  3) varga_lagna_lord_matrix(...) — for each major varga, identifies the
     varga-Lagna sign, its lord, and where the lord sits in that varga.
"""
from __future__ import annotations
from typing import Any

SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

# Parashari special aspects (1-indexed house from planet)
SPECIAL_ASPECTS = {
    "Mars":    [4, 7, 8],
    "Jupiter": [5, 7, 9],
    "Saturn":  [3, 7, 10],
    # Rahu/Ketu — many traditions use 5/7/9 like Jupiter
    "Rahu":    [5, 7, 9],
    "Ketu":    [5, 7, 9],
}
DEFAULT_ASPECT = [7]  # 7th is universal


def _planet_sign_idx(varga_chart: dict, planet: str) -> int | None:
    info = varga_chart.get(planet)
    if not isinstance(info, dict):
        return None
    si = info.get("sign_idx")
    if isinstance(si, int) and 0 <= si <= 11:
        return si
    sn = info.get("sign")
    if isinstance(sn, str) and sn in SIGN_NAMES:
        return SIGN_NAMES.index(sn)
    return None


# ---------------------------------------------------------------------------
# 1) Per-Varga Aspects
# ---------------------------------------------------------------------------
def compute_varga_aspects(varga_chart: dict, varga_label: str = "D9") -> dict[str, Any]:
    """Returns planet-to-planet aspect map within a varga chart."""
    if not isinstance(varga_chart, dict):
        return {"available": False}
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
               "Venus", "Saturn", "Rahu", "Ketu"]
    positions = {p: _planet_sign_idx(varga_chart, p) for p in planets}

    aspects: dict[str, list[dict]] = {p: [] for p in planets}
    for src in planets:
        s = positions[src]
        if s is None:
            continue
        houses = SPECIAL_ASPECTS.get(src, DEFAULT_ASPECT)
        for h in houses:
            target_sign = (s + (h - 1)) % 12
            for tgt in planets:
                if tgt == src:
                    continue
                if positions[tgt] == target_sign:
                    aspects[src].append({
                        "aspects": tgt,
                        "by_house": h,
                        "in_sign": SIGN_NAMES[target_sign],
                    })

    # Count incoming aspects per planet (strength indicator)
    incoming: dict[str, int] = {p: 0 for p in planets}
    for src, lst in aspects.items():
        for a in lst:
            incoming[a["aspects"]] += 1

    most_aspected = max(incoming.items(), key=lambda x: x[1])
    return {
        "available": True,
        "varga": varga_label,
        "aspects": {p: lst for p, lst in aspects.items() if lst},
        "incoming_count": incoming,
        "most_aspected": {"planet": most_aspected[0], "count": most_aspected[1]},
    }


# ---------------------------------------------------------------------------
# 2) Per-Varga Ashtakavarga
# ---------------------------------------------------------------------------
def compute_varga_ashtakavarga(varga_chart: dict, varga_label: str = "D9") -> dict[str, Any]:
    """Builds planet list with varga sign indices and runs ashtakavarga."""
    try:
        from ashtakavarga import compute_ashtakavarga  # type: ignore
    except Exception:
        return {"available": False, "reason": "ashtakavarga module missing"}
    if not isinstance(varga_chart, dict):
        return {"available": False}

    planets_payload = []
    for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        si = _planet_sign_idx(varga_chart, p)
        if si is not None:
            planets_payload.append({"name": p, "sign_idx": si})

    # Find varga lagna
    lagna_key = None
    for k in varga_chart.keys():
        if isinstance(k, str) and k.startswith("lagna_"):
            lagna_key = k
            break
    lagna_sign_idx = None
    if lagna_key:
        ln = varga_chart.get(lagna_key)
        if isinstance(ln, str) and ln in SIGN_NAMES:
            lagna_sign_idx = SIGN_NAMES.index(ln)

    if lagna_sign_idx is None or len(planets_payload) < 7:
        return {"available": False, "reason": "incomplete chart"}

    av = compute_ashtakavarga(planets_payload, lagna_sign_idx)
    if not av:
        return {"available": False}
    sav = av.get("sav") or av.get("SAV") or []
    if isinstance(sav, dict):
        sav_total = sum(sav.values())
    elif isinstance(sav, list):
        sav_total = sum(sav)
    else:
        sav_total = None
    return {
        "available": True,
        "varga": varga_label,
        "bav": av.get("bav") or av.get("BAV", {}),
        "sav": sav,
        "sav_total": sav_total,
    }


# ---------------------------------------------------------------------------
# 3) Varga-Lagna-Lord Matrix
# ---------------------------------------------------------------------------
def compute_varga_lagna_lord_matrix(vargas: dict[str, dict]) -> dict[str, Any]:
    """For each provided varga, identify lagna sign, lagna lord, and where
    the lord sits in that varga."""
    out = {}
    for label, chart in vargas.items():
        if not isinstance(chart, dict):
            continue
        lagna_key = next((k for k in chart if isinstance(k, str)
                          and k.startswith("lagna_")), None)
        if not lagna_key:
            continue
        lagna_sign = chart.get(lagna_key)
        if not isinstance(lagna_sign, str) or lagna_sign not in SIGN_NAMES:
            continue
        lord = SIGN_LORD[lagna_sign]
        lord_si = _planet_sign_idx(chart, lord)
        lord_sign = SIGN_NAMES[lord_si] if lord_si is not None else None
        # House of lord from varga lagna (1-indexed)
        lagna_si = SIGN_NAMES.index(lagna_sign)
        lord_house = ((lord_si - lagna_si) % 12) + 1 if lord_si is not None else None
        out[label] = {
            "lagna_sign": lagna_sign,
            "lagna_lord": lord,
            "lord_in_sign": lord_sign,
            "lord_in_house": lord_house,
        }
    return {"available": bool(out), "vargas": out}


# ---------------------------------------------------------------------------
# Master orchestrator
# ---------------------------------------------------------------------------
def compute_varga_deep_all(planets: list, lagna_lon: float | None) -> dict[str, Any]:
    """Computes per-varga deep analytics for the four most-used vargas:
    D9 (Marriage), D10 (Career), D24 (Education), D60 (Karma)."""
    try:
        from divisional_charts import (compute_d9, compute_d10,  # type: ignore
                                       compute_d24, compute_d60)
    except Exception as e:
        return {"available": False, "reason": f"divisional_charts: {e}"}

    vargas = {
        "D9":  compute_d9(planets, lagna_lon),
        "D10": compute_d10(planets, lagna_lon),
        "D24": compute_d24(planets, lagna_lon),
        "D60": compute_d60(planets, lagna_lon),
    }

    aspects_per_varga = {
        label: compute_varga_aspects(chart, label)
        for label, chart in vargas.items()
    }
    ashtaka_per_varga = {
        label: compute_varga_ashtakavarga(chart, label)
        for label, chart in vargas.items()
    }
    lagna_lord_matrix = compute_varga_lagna_lord_matrix(vargas)

    return {
        "available": True,
        "system": "Per-Varga Deep (Sprint 22)",
        "vargas_analyzed": list(vargas.keys()),
        "aspects": aspects_per_varga,
        "ashtakavarga": ashtaka_per_varga,
        "lagna_lord_matrix": lagna_lord_matrix,
    }


def format_varga_deep_summary(result: dict) -> str:
    """Compact narrative summary for AI prompt injection."""
    if not isinstance(result, dict) or not result.get("available"):
        return ""
    lines = ["── PER-VARGA DEEP (Sprint 22) ──"]
    llm = result.get("lagna_lord_matrix", {}).get("vargas", {})
    if llm:
        lines.append("Varga Lagna-Lord Matrix:")
        for v, d in llm.items():
            lines.append(f"  {v}: Lagna {d['lagna_sign']}, Lord {d['lagna_lord']} "
                         f"in {d['lord_in_sign']} (H{d['lord_in_house']})")
    asp = result.get("aspects", {})
    if asp:
        lines.append("Most-Aspected Planet per Varga:")
        for v, a in asp.items():
            if a.get("available"):
                ma = a.get("most_aspected", {})
                lines.append(f"  {v}: {ma.get('planet')} (×{ma.get('count')} aspects)")
    av = result.get("ashtakavarga", {})
    if av:
        lines.append("Per-Varga SAV Total (max 337):")
        for v, a in av.items():
            if a.get("available") and a.get("sav_total") is not None:
                lines.append(f"  {v}: SAV={a['sav_total']}")
    return "\n".join(lines)

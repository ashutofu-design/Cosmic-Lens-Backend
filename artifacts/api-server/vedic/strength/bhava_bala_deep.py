"""
Bhava Bala Deep — full BPHS 4-fold per-house strength (12 houses × 4 = 48 calc).

Per BPHS Ch.28 ("Bhava Bala Adhyaya"), each of the 12 bhavas has FOUR
independent strength components (in virupas, 60 = 1 rupa):

  1. BHAVADHIPATI BALA (House Lord Strength)
       The Shadbala total of the planet that rules the house's sign cusp.
       Source: shadbala.compute_shadbala() totals.
       Range: 0–600+ virupas (typically 200–500).

  2. BHAVA DIGBALA (Directional Strength of the House)
       Each bhava receives directional strength based on house TYPE:
         Kendra  (1/4/7/10) → 60 virupas (full)
         Panapara(2/5/8/11) → 30 virupas (half)
         Apoklima(3/6/9/12) → 15 virupas (quarter)

  3. BHAVA DRISHTI BALA (Aspectual Strength on the House Cusp)
       Sum of benefic aspects on the house cusp minus malefic aspects.
       Per BPHS:
         Jupiter aspect = +60v, Mercury/Venus = +45v, Moon = +30v
         Mars/Saturn  = -60v, Sun = -30v, Rahu/Ketu = -30v
       Net range: typically -100v to +120v.

  4. BHAVA NAISARGIKA BALA (Natural Strength of House Lord)
       Fixed natural strength of the ruling planet:
         Sun=60, Moon=51.43, Venus=42.86, Jupiter=34.29,
         Mercury=25.71, Mars=17.14, Saturn=8.57
       (Same table as planetary Naisargika; assigned to the house via lord.)

TOTAL Bhava Bala (deep) = sum of all four.
Required minimum per BPHS: ~300 virupas for a "fully-strong" house.

Public API
──────────
    compute_bhava_bala_deep(intel, shadbala, aspects) -> {
        "houses": {1..12: {
            "adhipati_bala": float, "dig_bala": float,
            "drishti_bala": float, "naisargika": float,
            "total": float, "required": float, "verdict": str
        }},
        "rankings": {"top_3": [..], "bottom_3": [..]}
    }
    format_bhava_bala_deep_summary(bbd) -> str
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


# Sign rulers (0=Aries .. 11=Pisces)
_SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
               "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]

# House type → directional strength
_KENDRA   = {1, 4, 7, 10}
_PANAPARA = {2, 5, 8, 11}
_APOKLIMA = {3, 6, 9, 12}

# Naisargika Bala (BPHS table — virupas)
_NAISARGIKA = {
    "Sun": 60.0, "Moon": 51.43, "Venus": 42.86, "Jupiter": 34.29,
    "Mercury": 25.71, "Mars": 17.14, "Saturn": 8.57,
    "Rahu": 5.0, "Ketu": 5.0,
}

# Aspect virupas on bhava cusp
_ASPECT_VIRUPAS = {
    "Jupiter": 60.0, "Mercury": 45.0, "Venus": 45.0, "Moon": 30.0,
    "Sun": -30.0, "Mars": -60.0, "Saturn": -60.0,
    "Rahu": -30.0, "Ketu": -30.0,
}

# Required minimum (BPHS Ch.28 sloka 17) — virupas needed per house type
_REQUIRED_MIN = {
    1: 475, 2: 350, 3: 300, 4: 500, 5: 400, 6: 350,
    7: 425, 8: 300, 9: 500, 10: 550, 11: 350, 12: 300,
}


def _house_type_dig_bala(house: int) -> float:
    if house in _KENDRA:   return 60.0
    if house in _PANAPARA: return 30.0
    if house in _APOKLIMA: return 15.0
    return 0.0


def compute_bhava_bala_deep(intel: Optional[Dict[str, Any]],
                            shadbala: Optional[Dict[str, Any]],
                            aspects: Optional[Dict[str, Any]],
                            lagna_sign_idx: Optional[int] = None
                            ) -> Dict[str, Any]:
    """
    Compute full 4-fold Bhava Bala per BPHS Ch.28.

    intel:    chart intelligence dict with house_lords list
    shadbala: {planet: {"total": v, ...}} from compute_shadbala()
    aspects:  {"on_house": {1..12: [planet_names]}} from aspects engine
    lagna_sign_idx: 0-11; if intel.house_lords is missing, derive from this
    """
    if not isinstance(intel, dict):
        intel = {}

    # Build house_lord map: {house: lord_planet}
    house_lord_map: Dict[int, str] = {}
    for hl in (intel.get("house_lords") or []):
        h = hl.get("house") if isinstance(hl, dict) else None
        l = hl.get("lord")  if isinstance(hl, dict) else None
        if isinstance(h, int) and l:
            house_lord_map[h] = l

    # Fallback: derive from lagna sign if intel missing
    if not house_lord_map and lagna_sign_idx is not None:
        for h in range(1, 13):
            sign_idx = (lagna_sign_idx + h - 1) % 12
            house_lord_map[h] = _SIGN_LORDS[sign_idx]

    # Shadbala lookup
    sb_total: Dict[str, float] = {}
    if isinstance(shadbala, dict):
        for p, data in shadbala.items():
            if isinstance(data, dict):
                sb_total[p] = float(data.get("total", 0.0) or 0.0)

    # Aspect lookup
    on_house: Dict[int, List[str]] = {}
    if isinstance(aspects, dict):
        raw = aspects.get("on_house") or {}
        for k, v in raw.items():
            try:
                on_house[int(k)] = list(v) if v else []
            except (TypeError, ValueError):
                continue

    houses_out: Dict[int, Dict[str, Any]] = {}
    for h in range(1, 13):
        lord = house_lord_map.get(h)

        # 1. Adhipati Bala (lord's Shadbala total)
        adhipati = sb_total.get(lord, 0.0) if lord else 0.0

        # 2. Bhava Digbala (house-type-based)
        dig = _house_type_dig_bala(h)

        # 3. Bhava Drishti Bala (sum of aspect virupas on cusp)
        drishti = 0.0
        for asp_planet in on_house.get(h, []):
            drishti += _ASPECT_VIRUPAS.get(asp_planet, 0.0)

        # 4. Naisargika Bala (lord's natural strength)
        naisargika = _NAISARGIKA.get(lord, 0.0) if lord else 0.0

        total = round(adhipati + dig + drishti + naisargika, 2)
        required = float(_REQUIRED_MIN.get(h, 400))
        verdict = "STRONG" if total >= required else (
            "MODERATE" if total >= required * 0.7 else "WEAK"
        )

        houses_out[h] = {
            "lord": lord,
            "adhipati_bala": round(adhipati, 2),
            "dig_bala": round(dig, 2),
            "drishti_bala": round(drishti, 2),
            "naisargika": round(naisargika, 2),
            "total": total,
            "required": required,
            "verdict": verdict,
            "ratio": round(total / required, 2) if required else 0.0,
        }

    # Rankings: top/bottom 3 by ratio (so bigger houses don't always dominate)
    ranked = sorted(houses_out.items(), key=lambda kv: -kv[1]["ratio"])
    top_3    = [h for h, _ in ranked[:3]]
    bottom_3 = [h for h, _ in ranked[-3:]]

    return {
        "houses": houses_out,
        "rankings": {"top_3": top_3, "bottom_3": bottom_3},
    }


def format_bhava_bala_deep_summary(bbd: Dict[str, Any]) -> str:
    """LOCKED FACTS block formatter."""
    if not bbd or "houses" not in bbd:
        return ""
    lines = ["▸ BHAVA BALA DEEP (BPHS 4-fold per house — 48 calculations):"]
    lines.append("   Components per house: Adhipati(lord-Shadbala) + Digbala(house-type)"
                 " + Drishti(aspects) + Naisargika(lord-natural)")
    # Compact table-style summary for all 12 houses
    parts = []
    for h in range(1, 13):
        info = bbd["houses"].get(h, {})
        v = info.get("verdict", "?")[:1]
        t = info.get("total", 0)
        r = info.get("ratio", 0)
        parts.append(f"H{h}={t:.0f}v({r:.2f}x,{v})")
    lines.append("   " + "  ".join(parts[:6]))
    lines.append("   " + "  ".join(parts[6:]))

    rk = bbd.get("rankings") or {}
    if rk.get("top_3"):
        # Show top-3 detailed breakdown
        lines.append("   ▸ STRONGEST 3 houses (by required-ratio):")
        for h in rk["top_3"]:
            info = bbd["houses"][h]
            lines.append(
                f"      H{h} (lord {info.get('lord','?')}): total {info['total']}v"
                f" / req {info['required']}v ({info['ratio']}x, {info['verdict']})"
                f" — Adhipati {info['adhipati_bala']}v, Dig {info['dig_bala']}v,"
                f" Drishti {info['drishti_bala']:+.0f}v, Naisargika {info['naisargika']}v"
            )
    if rk.get("bottom_3"):
        lines.append("   ▸ WEAKEST 3 houses (by required-ratio):")
        for h in rk["bottom_3"]:
            info = bbd["houses"][h]
            lines.append(
                f"      H{h} (lord {info.get('lord','?')}): total {info['total']}v"
                f" / req {info['required']}v ({info['ratio']}x, {info['verdict']})"
                f" — Adhipati {info['adhipati_bala']}v, Dig {info['dig_bala']}v,"
                f" Drishti {info['drishti_bala']:+.0f}v, Naisargika {info['naisargika']}v"
            )
    return "\n".join(lines)

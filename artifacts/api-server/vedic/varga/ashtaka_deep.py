"""
Sprint 23 — Tier 7 Ashtakavarga Deep
Adds the four classical reduction & application techniques on top of
existing BAV/SAV from ashtakavarga.py:

  1) Trikona Shodhana    — column reduction within each trine (1-5-9, 2-6-10,
                           3-7-11, 4-8-12). Subtract the lowest of each trine
                           from all three signs in that trine.
  2) Ekadhipatya Shodhana — when one planet rules two signs, reduce per BPHS:
                           if either has 0, both → 0; else subtract the lower
                           from both (or set the one with planet present to 0
                           per Parashara classical rule).
  3) Sodhya Pinda         — multiplied bindus (rashi-pinda × graha-pinda) per
                           planet → planetary potency for prediction.
  4) Transit overlay      — given current planetary positions, evaluate each
                           transit against natal BAV bindus in that sign.
"""
from __future__ import annotations
from typing import Any
from datetime import datetime

SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

# Classical Rashi Pinda values (Parashara BPHS Ch.66)
RASHI_PINDA = {
    "Aries": 7, "Taurus": 10, "Gemini": 8, "Cancer": 4, "Leo": 10, "Virgo": 6,
    "Libra": 7, "Scorpio": 8, "Sagittarius": 9, "Capricorn": 5,
    "Aquarius": 11, "Pisces": 12,
}
# Classical Graha Pinda values (per BPHS)
GRAHA_PINDA = {
    "Sun": 5, "Moon": 5, "Mars": 8, "Mercury": 5,
    "Jupiter": 10, "Venus": 7, "Saturn": 5,
}
# Sign rulership (for Ekadhipatya — each planet rules 2 signs except Sun/Moon)
PLANET_RULES: dict[str, list[int]] = {
    "Sun":     [4],         # Leo
    "Moon":    [3],         # Cancer
    "Mars":    [0, 7],      # Aries, Scorpio
    "Mercury": [2, 5],      # Gemini, Virgo
    "Jupiter": [8, 11],     # Sagittarius, Pisces
    "Venus":   [1, 6],      # Taurus, Libra
    "Saturn":  [9, 10],     # Capricorn, Aquarius
}
TRINES = [(0, 4, 8), (1, 5, 9), (2, 6, 10), (3, 7, 11)]


# ---------------------------------------------------------------------------
# 1) Trikona Shodhana
# ---------------------------------------------------------------------------
def trikona_shodhana(bav: dict[str, list[int]]) -> dict[str, list[int]]:
    """For each planet's BAV row, reduce within each trine: subtract the
    minimum of the trine from all three signs in that trine."""
    out: dict[str, list[int]] = {}
    for planet, row in bav.items():
        if not isinstance(row, list) or len(row) != 12:
            out[planet] = row
            continue
        new_row = list(row)
        for trine in TRINES:
            mn = min(new_row[i] for i in trine)
            if mn > 0:
                # Set the minimum sign to 0, subtract mn from others
                for i in trine:
                    new_row[i] = new_row[i] - mn
            # If any is 0, all stay (BPHS rule)
        out[planet] = new_row
    return out


# ---------------------------------------------------------------------------
# 2) Ekadhipatya Shodhana
# ---------------------------------------------------------------------------
def ekadhipatya_shodhana(bav: dict[str, list[int]],
                          planet_signs: dict[str, int]) -> dict[str, list[int]]:
    """For planets ruling 2 signs, apply BPHS Ekadhipatya:
       - If either of the 2 signs has 0 bindus → both become 0.
       - Else if one sign has a planet → that one becomes 0; other unchanged.
       - Else → subtract the lower from both (lower becomes 0)."""
    out = {p: list(row) if isinstance(row, list) else row for p, row in bav.items()}
    for planet, ruled in PLANET_RULES.items():
        if len(ruled) < 2:
            continue
        s1, s2 = ruled
        for p_row_owner, row in out.items():
            if not isinstance(row, list) or len(row) != 12:
                continue
            v1, v2 = row[s1], row[s2]
            if v1 == 0 or v2 == 0:
                row[s1] = 0
                row[s2] = 0
            else:
                # Check if any planet occupies these signs
                occ1 = any(sg == s1 for sg in planet_signs.values())
                occ2 = any(sg == s2 for sg in planet_signs.values())
                if occ1 and not occ2:
                    row[s1] = 0
                elif occ2 and not occ1:
                    row[s2] = 0
                else:
                    mn = min(v1, v2)
                    row[s1] = v1 - mn
                    row[s2] = v2 - mn
    return out


# ---------------------------------------------------------------------------
# 3) Sodhya Pinda
# ---------------------------------------------------------------------------
def sodhya_pinda(reduced_bav: dict[str, list[int]],
                 planet_signs: dict[str, int]) -> dict[str, dict[str, Any]]:
    """Compute Rashi Pinda + Graha Pinda + Sodhya Pinda for each planet.
       Sodhya = Rashi Pinda + Graha Pinda."""
    out: dict[str, dict[str, Any]] = {}
    for planet, row in reduced_bav.items():
        if not isinstance(row, list) or len(row) != 12:
            continue
        # Rashi Pinda — sum over (bindu × rashi-pinda-of-sign)
        rp = sum(row[i] * RASHI_PINDA[SIGN_NAMES[i]] for i in range(12))
        # Graha Pinda — for each planet sitting in a sign, multiply that
        # sign's bindu count (in this planet's BAV) by graha-pinda of occupant
        gp = 0
        for occ_planet, occ_sign in planet_signs.items():
            if occ_planet in GRAHA_PINDA and 0 <= occ_sign <= 11:
                gp += row[occ_sign] * GRAHA_PINDA[occ_planet]
        out[planet] = {
            "rashi_pinda": rp,
            "graha_pinda": gp,
            "sodhya_pinda": rp + gp,
        }
    # Verdict: highest sodhya = strongest planet
    if out:
        ranked = sorted(out.items(), key=lambda x: -x[1]["sodhya_pinda"])
        return {
            "per_planet": out,
            "ranked": [{"planet": p, "sodhya": d["sodhya_pinda"]} for p, d in ranked],
            "strongest": ranked[0][0],
            "weakest": ranked[-1][0],
        }
    return {"per_planet": {}, "ranked": [], "strongest": None, "weakest": None}


# ---------------------------------------------------------------------------
# 4) Transit overlay through Ashtakavarga
# ---------------------------------------------------------------------------
def transit_overlay(bav: dict[str, list[int]],
                    transit_signs: dict[str, int]) -> dict[str, Any]:
    """For each transiting planet's current sign, evaluate bindus in its own
    BAV row → indicates result quality of this transit.
    Convention:  >=4 favourable, 3 average, <=2 weak."""
    out: dict[str, dict[str, Any]] = {}
    for planet, sign_idx in transit_signs.items():
        if planet not in bav:
            continue
        row = bav[planet]
        if not isinstance(row, list) or len(row) != 12:
            continue
        if not (0 <= sign_idx <= 11):
            continue
        bindus = row[sign_idx]
        if bindus >= 5:
            verdict = "EXCELLENT"
        elif bindus == 4:
            verdict = "FAVOURABLE"
        elif bindus == 3:
            verdict = "AVERAGE"
        elif bindus in (1, 2):
            verdict = "WEAK"
        else:
            verdict = "ADVERSE"
        out[planet] = {
            "transit_sign": SIGN_NAMES[sign_idx],
            "bindus_in_own_bav": bindus,
            "verdict": verdict,
        }
    return {"per_planet": out, "evaluated_at": datetime.utcnow().strftime("%Y-%m-%d")}


# ---------------------------------------------------------------------------
# Master orchestrator
# ---------------------------------------------------------------------------
def compute_ashtaka_deep(planets: list, lagna_sign_idx: int | None,
                          transit_signs: dict[str, int] | None = None) -> dict[str, Any]:
    """Runs all 4 Tier-7 reductions on the natal ashtakavarga and (optionally)
    overlays current transits."""
    try:
        from ashtakavarga import compute_ashtakavarga  # type: ignore
    except Exception as e:
        return {"available": False, "reason": f"ashtakavarga: {e}"}

    if lagna_sign_idx is None:
        return {"available": False, "reason": "missing lagna"}

    av = compute_ashtakavarga(planets, lagna_sign_idx)
    if not av or not av.get("bav"):
        return {"available": False, "reason": "BAV unavailable"}

    bav = av["bav"]
    sav = av.get("sav", [])

    # Build planet→sign_idx map
    planet_signs: dict[str, int] = {}
    for p in planets:
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        if nm not in PLANET_RULES and nm not in ("Sun", "Moon"):
            continue
        s = p.get("sign_idx")
        if s is None and isinstance(p.get("sign"), str) and p["sign"] in SIGN_NAMES:
            s = SIGN_NAMES.index(p["sign"])
        if isinstance(s, int):
            planet_signs[nm] = s

    # 1) Trikona shodhana
    after_trikona = trikona_shodhana(bav)
    # 2) Ekadhipatya on top of trikona-reduced
    after_ekadhi = ekadhipatya_shodhana(after_trikona, planet_signs)
    # 3) Sodhya Pinda
    pinda = sodhya_pinda(after_ekadhi, planet_signs)
    # 4) Transit overlay (optional)
    transit = transit_overlay(bav, transit_signs or {}) if transit_signs else None

    return {
        "available": True,
        "system": "Ashtakavarga Deep (Sprint 23)",
        "natal_bav": bav,
        "natal_sav": sav,
        "natal_sav_total": av.get("sav_total"),
        "after_trikona_shodhana": after_trikona,
        "after_ekadhipatya_shodhana": after_ekadhi,
        "sodhya_pinda": pinda,
        "transit_overlay": transit,
    }


def format_ashtaka_deep_summary(result: dict) -> str:
    if not isinstance(result, dict) or not result.get("available"):
        return ""
    lines = ["── ASHTAKAVARGA DEEP (Sprint 23) ──"]
    sp = result.get("sodhya_pinda", {})
    if sp.get("ranked"):
        lines.append("Sodhya Pinda Ranking (BPHS Ch.66):")
        for r in sp["ranked"]:
            lines.append(f"  {r['planet']}: {r['sodhya']}")
        lines.append(f"  → Strongest: {sp.get('strongest')}, "
                     f"Weakest: {sp.get('weakest')}")
    # Show one example reduced row to confirm engine works
    ek = result.get("after_ekadhipatya_shodhana", {})
    if ek:
        sun_row = ek.get("Sun")
        if isinstance(sun_row, list):
            lines.append(f"Sun BAV after Trikona+Ekadhipatya: {sun_row} "
                         f"(was {result['natal_bav']['Sun']})")
    tr = result.get("transit_overlay")
    if tr and tr.get("per_planet"):
        lines.append("Current Transit Verdicts (own-BAV bindus):")
        for p, d in tr["per_planet"].items():
            lines.append(f"  {p} in {d['transit_sign']}: {d['bindus_in_own_bav']} → {d['verdict']}")
    return "\n".join(lines)

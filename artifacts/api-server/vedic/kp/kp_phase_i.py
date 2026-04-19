"""
Sprint 34 / Phase I — KP Advanced gap fill.
Adds I2 Cuspal Interlinks (CIL) + I5 KP Marriage Matching.
I1, I3, I4, I6 are already implemented in kp_deep.py.
"""
from __future__ import annotations
from typing import Any

from .kp_deep import kp_full_lords, significators_4_level

SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
              "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_LORD = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
             "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]


def _equal_house_cusp_lon(lagna_lon: float, house: int) -> float:
    """Equal-house cusp in degrees (KP simplified — actual Placidus needs lat/lon)."""
    return (lagna_lon + (house - 1) * 30.0) % 360.0


def _planet_house_significations(planet_name: str,
                                  planets: list[dict],
                                  lagna_si: int) -> list[int]:
    """Houses signified by a planet (KP ladder):
       1) house occupied
       2) house owned
       3) house occupied by its star-lord
       4) house owned by its star-lord
    """
    sig: list[int] = []
    target = next((p for p in planets if isinstance(p, dict)
                   and p.get("name") == planet_name), None)
    if not target: return sig
    lon = target.get("longitude")
    if not isinstance(lon, (int, float)): return sig
    occ_si = int(lon // 30)
    occ_house = ((occ_si - lagna_si) % 12) + 1
    sig.append(occ_house)
    # Houses owned (sign(s) ruled by planet from Lagna)
    for si, lord in enumerate(SIGN_LORD):
        if lord == planet_name:
            h = ((si - lagna_si) % 12) + 1
            if h not in sig: sig.append(h)
    # Star-lord
    lords = kp_full_lords(lon)
    star = lords.get("star_lord")
    if star and star != planet_name:
        star_p = next((p for p in planets if isinstance(p, dict)
                       and p.get("name") == star), None)
        if star_p and isinstance(star_p.get("longitude"), (int, float)):
            slon = star_p["longitude"]
            so_si = int(slon // 30)
            so_h = ((so_si - lagna_si) % 12) + 1
            if so_h not in sig: sig.append(so_h)
        for si, lord in enumerate(SIGN_LORD):
            if lord == star:
                h = ((si - lagna_si) % 12) + 1
                if h not in sig: sig.append(h)
    return sorted(sig)


def cuspal_interlinks(planets: list[dict],
                       lagna_lon: float,
                       lagna_si: int) -> dict[str, Any]:
    """I2 — Cuspal Interlinks (CIL):
       For each of 12 cusps, return its sub-lord and the houses that
       sub-lord signifies. Promise = whether the cusp's purpose is
       supported by its sub-lord's significations.
    """
    PURPOSE_HOUSES = {
        1: ("Self/Health",      [1, 6, 11]),
        2: ("Wealth/Family",    [2, 6, 11]),
        3: ("Courage/Sibling",  [3, 6, 11]),
        4: ("Home/Mother",      [4, 11]),
        5: ("Children/Romance", [2, 5, 11]),
        6: ("Service/Disease",  [6, 10, 11]),
        7: ("Marriage/Partner", [2, 7, 11]),
        8: ("Longevity/Occult", [1, 5, 11]),
        9: ("Fortune/Father",   [9, 5, 11]),
        10: ("Career/Status",   [2, 6, 10, 11]),
        11: ("Gains/Friends",   [2, 6, 11]),
        12: ("Loss/Moksha",     [12, 5, 8]),
    }
    out: list[dict] = []
    for h in range(1, 13):
        cusp_lon = _equal_house_cusp_lon(lagna_lon, h)
        lords = kp_full_lords(cusp_lon)
        sub = lords["sub_lord"]
        sig_houses = _planet_house_significations(sub, planets, lagna_si)
        purpose, fav_houses = PURPOSE_HOUSES[h]
        match = sorted(set(sig_houses) & set(fav_houses))
        verdict = ("PROMISED" if match else
                   "DENIED"   if sig_houses else
                   "UNCLEAR")
        out.append({
            "house": h,
            "purpose": purpose,
            "cusp_sub_lord": sub,
            "sub_lord_signifies_houses": sig_houses,
            "favourable_for_purpose": fav_houses,
            "matching_houses": match,
            "verdict": verdict,
        })
    return {"available": True, "cusps": out}


def kp_marriage_matching(planets: list[dict],
                          lagna_lon: float,
                          lagna_si: int) -> dict[str, Any]:
    """I5 — KP Marriage Matching:
       Marriage is promised if the SUB-LORDS of cusps 2, 7, 11
       collectively signify the trio (2, 7, 11).
       Marriage is denied if they instead signify (1, 6, 10).
    """
    favour = {2, 7, 11}
    deny = {1, 6, 10}
    cusp_data = []
    all_sig: set[int] = set()
    for h in (2, 7, 11):
        cusp_lon = _equal_house_cusp_lon(lagna_lon, h)
        sub = kp_full_lords(cusp_lon)["sub_lord"]
        sigs = _planet_house_significations(sub, planets, lagna_si)
        all_sig.update(sigs)
        cusp_data.append({
            "cusp": h,
            "sub_lord": sub,
            "signifies_houses": sigs,
            "supports_marriage": bool(set(sigs) & favour),
            "denies_marriage": bool(set(sigs) & deny),
        })
    fav_hits = all_sig & favour
    deny_hits = all_sig & deny
    if len(fav_hits) >= 2 and len(deny_hits) <= 1:
        verdict = "MARRIAGE STRONGLY PROMISED"
    elif fav_hits and not deny_hits:
        verdict = "MARRIAGE PROMISED"
    elif deny_hits and not fav_hits:
        verdict = "MARRIAGE DENIED / DELAYED"
    elif fav_hits and deny_hits:
        verdict = "MARRIAGE WITH OBSTACLES"
    else:
        verdict = "UNCLEAR / WEAK PROMISE"
    return {
        "available": True,
        "method": "KP cusp sub-lord rule (2-7-11 vs 1-6-10)",
        "cusp_2_7_11": cusp_data,
        "favourable_signified": sorted(fav_hits),
        "denying_signified": sorted(deny_hits),
        "verdict": verdict,
    }


def compute_kp_phase_i(kundli: dict) -> dict[str, Any]:
    planets = kundli.get("planets") or []
    lagna_sign = kundli.get("ascendant") or kundli.get("lagna")
    lagna_lon = (kundli.get("ascendantDeg") or kundli.get("lagnaDeg")
                 or kundli.get("lagna_lon"))
    if isinstance(lagna_sign, str) and lagna_sign in SIGN_NAMES:
        lagna_si = SIGN_NAMES.index(lagna_sign)
    else:
        return {"available": False, "reason": "lagna sign missing"}
    if not isinstance(lagna_lon, (int, float)):
        # Fallback: use sign-start as lagna lon (degraded but functional)
        lagna_lon = lagna_si * 30.0
    return {
        "available": True,
        "cuspal_interlinks": cuspal_interlinks(planets, float(lagna_lon), lagna_si),
        "marriage": kp_marriage_matching(planets, float(lagna_lon), lagna_si),
    }


def format_kp_phase_i_summary(result: dict) -> str:
    if not result or not result.get("available"):
        return f"▸ KP PHASE-I: ❌ {result.get('reason','n/a') if result else 'n/a'}"
    lines = ["▸ KP PHASE-I (Sprint-34): I2 Cuspal Interlinks + I5 Marriage Matching"]
    cil = result.get("cuspal_interlinks", {}).get("cusps", [])
    if cil:
        lines.append("  ── I2 CUSPAL INTERLINKS (CIL) — promise per house ──")
        for c in cil:
            mark = ("✓" if c["verdict"] == "PROMISED"
                    else "✗" if c["verdict"] == "DENIED" else "?")
            lines.append(f"    {mark} H{c['house']:>2} {c['purpose']:<22} "
                          f"sub-lord {c['cusp_sub_lord']:<8} → "
                          f"signifies {c['sub_lord_signifies_houses']} "
                          f"(needs {c['favourable_for_purpose']}) → {c['verdict']}")
    m = result.get("marriage", {})
    if m and m.get("available"):
        lines.append("  ── I5 KP MARRIAGE MATCHING (cusp 2-7-11 sub-lord rule) ──")
        for c in m["cusp_2_7_11"]:
            lines.append(f"    Cusp H{c['cusp']:>2} sub-lord {c['sub_lord']:<8} → "
                          f"signifies {c['signifies_houses']}")
        lines.append(f"    Favourable houses (2,7,11) hit: {m['favourable_signified']}")
        lines.append(f"    Denying houses (1,6,10) hit:    {m['denying_signified']}")
        lines.append(f"    → VERDICT: {m['verdict']}")
    return "\n".join(lines)

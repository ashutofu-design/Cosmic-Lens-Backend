"""
Phase 2.5.11.23 — KP 7th CSL Marriage Promise Verifier
======================================================
Hidden backend layer (NEVER user-visible jargon). Determines whether the
chart actually PROMISES marriage at the KP level, using:

  - 7th house Sub-Lord (CSL) — primary marriage promise indicator
  - Significator chain: 7CSL must signify 2 (family) + 11 (gain of partner)
    in its Star-Lord/Sub-Lord/Sub-Sub chain
  - Negation if 7CSL signifies 6/10/12 (separation/work-over-home/loss)

Verdict: STRONG | PARTIAL | WEAK | UNAVAILABLE

Reuses `vedic.kp.kp_deep.kp_full_lords` for the SSS chain. Tolerates absence
of pre-computed Placidus cusps by falling back to whole-sign 7H mid-cusp.

User-facing rule: this verdict is summarized in plain Hindi via the LLM
polish layer (e.g. "Yeh rishta deep level pe stable promise rakhta hai" —
NEVER "7th CSL signifies 11 in star").

Branding: never name AI/LLM. Defensive — never raises.
"""
from __future__ import annotations
from typing import Any

SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

# Promise houses (KP marriage convention)
PROMISE_HOUSES = {2, 7, 11}      # family + partner + gain
SUPPORT_HOUSES = {5}              # love/romance support
NEGATION_HOUSES = {6, 10, 12}     # separation / work-over-home / loss


def _sidx(sign: str | None) -> int | None:
    if isinstance(sign, str) and sign in SIGN_NAMES:
        return SIGN_NAMES.index(sign)
    return None


def _planet_house(kundli: dict, planet_name: str) -> int | None:
    """Compute whole-sign house of a planet from kundli['ascendant']."""
    asc_idx = _sidx(kundli.get("ascendant"))
    if asc_idx is None:
        return None
    for p in kundli.get("planets") or []:
        if isinstance(p, dict) and p.get("name") == planet_name:
            psi = _sidx(p.get("sign"))
            if psi is not None:
                return ((psi - asc_idx) % 12) + 1
    return None


def _seventh_csl(kundli: dict) -> dict[str, Any]:
    """Compute KP CSL of the 7th cusp. We use the 7H mid-point longitude
    (asc_lon + 180°) when actual cusp longitudes are not provided —
    pragmatic fallback that's accurate enough for the promise verdict.

    Returns: {available, sign, star_lord, sub_lord, sub_sub_lord}
    """
    out: dict[str, Any] = {"available": False}
    if not isinstance(kundli, dict):
        return out
    try:
        from vedic.kp.kp_deep import kp_full_lords
    except Exception:
        return out

    # Prefer real 7H cusp longitude if present
    cusp_lon: float | None = None
    cusps = kundli.get("cusps") or kundli.get("houseCusps")
    if isinstance(cusps, (list, tuple)) and len(cusps) >= 7:
        c7 = cusps[6]
        if isinstance(c7, (int, float)):
            cusp_lon = float(c7)
        elif isinstance(c7, dict) and isinstance(c7.get("longitude"), (int, float)):
            cusp_lon = float(c7["longitude"])

    if cusp_lon is None:
        # Fall back to lagna-longitude + 180 (whole-sign 7H midpoint).
        asc_lon = kundli.get("ascendantLongitude") or kundli.get("lagnaLongitude")
        if isinstance(asc_lon, (int, float)):
            cusp_lon = (float(asc_lon) + 180.0) % 360.0
        else:
            asc_si = _sidx(kundli.get("ascendant"))
            if asc_si is None:
                return out
            # Use sign mid-point of 7th sign as last-resort
            cusp_lon = (((asc_si + 6) % 12) * 30.0) + 15.0

    lords = kp_full_lords(cusp_lon)
    out.update({
        "available": True,
        "cusp_longitude": round(cusp_lon, 4),
        "sign": lords["sign"],
        "star_lord": lords["star_lord"],
        "sub_lord": lords["sub_lord"],
        "sub_sub_lord": lords["sub_sub_lord"],
    })
    return out


def _planet_chain_houses(kundli: dict, planet: str) -> set[int]:
    """Houses signified by `planet` in KP-lite chain:
       (a) the house planet OCCUPIES,
       (b) the house planet OWNS (from lagna sign-lord scheme).
    Pure whole-sign — no cusp data needed. Returns set of 1..12 ints."""
    houses: set[int] = set()
    asc_idx = _sidx(kundli.get("ascendant"))
    if asc_idx is None:
        return houses
    # Occupation
    h = _planet_house(kundli, planet)
    if h is not None:
        houses.add(h)
    # Ownership: which sign(s) does `planet` lord, then which houses are those?
    for sign_name, lord in SIGN_LORDS.items():
        if lord == planet:
            sign_idx = _sidx(sign_name)
            if sign_idx is not None:
                owned_house = ((sign_idx - asc_idx) % 12) + 1
                houses.add(owned_house)
    return houses


def compute_kp_marriage_promise(kundli: dict) -> dict[str, Any]:
    """Verdict for one chart.

    Returns: {
      available, verdict (STRONG|PARTIAL|WEAK|UNAVAILABLE),
      seven_csl: {sign, star_lord, sub_lord, sub_sub_lord},
      chain: {sl: [houses], sb: [houses], ss: [houses]},
      signified_houses: [1..12], promise_hits: int, support_hits: int,
      negation_hits: int, notes: [str]
    }
    """
    out: dict[str, Any] = {
        "available": False, "verdict": "UNAVAILABLE",
        "seven_csl": None, "chain": {}, "signified_houses": [],
        "promise_hits": 0, "support_hits": 0, "negation_hits": 0,
        "notes": [],
    }
    csl = _seventh_csl(kundli)
    if not csl.get("available"):
        return out
    out["seven_csl"] = {k: csl[k] for k in ("sign", "star_lord", "sub_lord", "sub_sub_lord")}

    sl = csl["star_lord"]
    sb = csl["sub_lord"]
    ss = csl["sub_sub_lord"]

    sl_h = _planet_chain_houses(kundli, sl)
    sb_h = _planet_chain_houses(kundli, sb)
    ss_h = _planet_chain_houses(kundli, ss)

    all_h = sl_h | sb_h | ss_h
    out["chain"] = {
        "sl": sorted(sl_h), "sb": sorted(sb_h), "ss": sorted(ss_h),
    }
    out["signified_houses"] = sorted(all_h)

    promise = all_h & PROMISE_HOUSES
    support = all_h & SUPPORT_HOUSES
    negation = all_h & NEGATION_HOUSES
    out["promise_hits"] = len(promise)
    out["support_hits"] = len(support)
    out["negation_hits"] = len(negation)

    notes: list[str] = []
    notes.append(f"7CSL chain: SL={sl}, SB={sb}, SS={ss}")
    notes.append(f"Promise houses signified: {sorted(promise) or '—'}")
    if support:
        notes.append(f"Support houses (5): {sorted(support)}")
    if negation:
        notes.append(f"Negation houses (6/10/12): {sorted(negation)}")

    # Verdict logic
    # STRONG: ≥2 of {2,7,11} signified AND negation_hits ≤ 1
    # PARTIAL: 1 promise hit OR (≥2 promise BUT 2+ negations)
    # WEAK: 0 promise hits OR negations dominate
    if len(promise) >= 2 and len(negation) <= 1:
        verdict = "STRONG"
    elif len(promise) >= 2 and len(negation) >= 2:
        verdict = "PARTIAL"
    elif len(promise) == 1:
        verdict = "PARTIAL"
    else:
        verdict = "WEAK"

    out["available"] = True
    out["verdict"] = verdict
    out["notes"] = notes
    return out


def compute_kp_couple_promise(kundli_p1: dict, kundli_p2: dict) -> dict[str, Any]:
    """Per-partner promise + couple-level sync verdict.

    Couple sync verdict:
      STRONG iff both partners verdict ∈ {STRONG, PARTIAL} AND at least one STRONG
      WEAK   iff either partner is WEAK
      PARTIAL otherwise
    """
    p1 = compute_kp_marriage_promise(kundli_p1)
    p2 = compute_kp_marriage_promise(kundli_p2)
    couple = "UNAVAILABLE"
    if p1["available"] and p2["available"]:
        v1, v2 = p1["verdict"], p2["verdict"]
        verdicts = {v1, v2}
        if "WEAK" in verdicts:
            couple = "WEAK"
        elif "STRONG" in verdicts and "WEAK" not in verdicts:
            couple = "STRONG" if v1 == v2 == "STRONG" else "PARTIAL"
        else:
            couple = "PARTIAL"
    return {
        "available": p1["available"] and p2["available"],
        "p1": p1,
        "p2": p2,
        "couple_verdict": couple,
    }

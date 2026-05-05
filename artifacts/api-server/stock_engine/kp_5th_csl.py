"""Phase 2.10.7 P6 — KP 5th Cuspal Sub-Lord (CSL) module.

Pure deterministic. ZERO LLM. Same kundli → same verdict forever.

KP rule (speculation / stock market):
  5th house = speculation. The 5th cusp's Sub-Lord (CSL) tells whether
  the native should enter the market.

  Significations of CSL = union of:
    1. House occupied by CSL planet
    2. Houses owned by CSL planet (sign-lordship)
    3. House occupied by CSL's nakshatra-lord (star-lord)
    4. Houses owned by CSL's nakshatra-lord

  Verdict:
    GREEN  — signifies 2/6/11 (gain trio) AND no 8/12
    AMBER  — partial gain signal, OR 5 alone (speculation active but weak)
    RED    — signifies 8 or 12 (loss/drain) — KP says AVOID
    NEUTRAL — no clear signal

  Score weight (added to stock_facts composite 0-12 scale):
    GREEN  → +3
    AMBER  → +1
    NEUTRAL→  0
    RED    → -4

Public:
  compute_kp_5th_csl(kundli) -> dict | None  (None if KP cusps missing)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

# Nakshatra lord sequence (Vimshottari) — 9 lords × 3 cycles = 27 nakshatras
_NAK_LORDS: List[str] = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
] * 3
_NAK_SIZE: float = 360.0 / 27.0  # 13.3333°

# Sign → owning planet (Vedic, Rahu/Ketu excluded — they are nodes)
_SIGN_NAMES: List[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn",
    "Aquarius", "Pisces",
]
_SIGN_IDX: Dict[str, int] = {s: i for i, s in enumerate(_SIGN_NAMES)}
_SIGN_LORDS: Dict[int, str] = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun",
    5: "Mercury", 6: "Venus", 7: "Mars", 8: "Jupiter",
    9: "Saturn", 10: "Saturn", 11: "Jupiter",
}

# KP houses for stock market verdict
_GAIN_HOUSES: Set[int] = {2, 6, 11}
_LOSS_HOUSES: Set[int] = {8, 12}
_SPECULATION_HOUSE: int = 5


# ── Helpers ─────────────────────────────────────────────────────────
def _nak_lord_of(longitude: float) -> str:
    """Vimshottari nakshatra lord from sidereal longitude."""
    nak_idx = int((float(longitude) % 360.0) / _NAK_SIZE) % 27
    return _NAK_LORDS[nak_idx]


def _planet_by_name(planets: List[dict], name: str) -> Optional[dict]:
    for p in planets or []:
        if p.get("name") == name:
            return p
    return None


def _houses_owned_by(asc_si: int, planet: str) -> List[int]:
    """Return list of house numbers (1-12) whose sign-lord is `planet`."""
    out: List[int] = []
    for h in range(1, 13):
        si = (asc_si + h - 1) % 12
        if _SIGN_LORDS.get(si) == planet:
            out.append(h)
    return out


def _house_of_planet(planets: List[dict], name: str) -> Optional[int]:
    p = _planet_by_name(planets, name)
    if not p:
        return None
    h = p.get("house")
    return int(h) if h else None


def _csl_signification_chain(
    csl_planet: str,
    planets: List[dict],
    asc_si: int,
) -> Dict[str, Any]:
    """Compute the full KP signification chain for the CSL planet.

    Phase 2.8.81 — Node Dispositor extension:
      Rahu/Ketu, being shadow nodes, do NOT own signs. Per KP tradition
      they "act through" the lord of the sign they occupy (dispositor).
      So when the CSL planet is Rahu or Ketu, we additionally include
      the dispositor's house + ownership in the signification chain.

    Returns dict with:
      - csl_house: house occupied by CSL planet
      - csl_owns: houses owned by CSL planet (empty for nodes)
      - star_lord: nakshatra lord of CSL planet
      - star_lord_house: house occupied by star-lord
      - star_lord_owns: houses owned by star-lord
      - dispositor: sign-lord of CSL planet's sign (only for Rahu/Ketu)
      - dispositor_house: house occupied by dispositor
      - dispositor_owns: houses owned by dispositor
      - signified: sorted list of all unique houses signified
    """
    # Step 1+2: CSL planet placement and ownership
    csl_house = _house_of_planet(planets, csl_planet)
    csl_owns = (_houses_owned_by(asc_si, csl_planet)
                if csl_planet not in ("Rahu", "Ketu") else [])

    # Step 3+4: CSL's star-lord (nakshatra lord) placement and ownership
    csl_p = _planet_by_name(planets, csl_planet)
    star_lord: Optional[str] = None
    star_lord_house: Optional[int] = None
    star_lord_owns: List[int] = []
    if csl_p and csl_p.get("longitude") is not None:
        try:
            star_lord = _nak_lord_of(float(csl_p["longitude"]))
            star_lord_house = _house_of_planet(planets, star_lord)
            if star_lord not in ("Rahu", "Ketu"):
                star_lord_owns = _houses_owned_by(asc_si, star_lord)
        except (TypeError, ValueError):
            pass

    # Step 5 (Phase 2.8.81): Node dispositor — Rahu/Ketu act through
    # the lord of the sign they occupy.
    dispositor: Optional[str] = None
    dispositor_house: Optional[int] = None
    dispositor_owns: List[int] = []
    if csl_planet in ("Rahu", "Ketu") and csl_p:
        sign_name = csl_p.get("sign")
        si = _SIGN_IDX.get(sign_name) if sign_name else None
        if si is not None:
            dispositor = _SIGN_LORDS.get(si)
            if dispositor:
                dispositor_house = _house_of_planet(planets, dispositor)
                if dispositor not in ("Rahu", "Ketu"):
                    dispositor_owns = _houses_owned_by(asc_si, dispositor)

    signified: Set[int] = set()
    if csl_house:
        signified.add(csl_house)
    signified.update(csl_owns)
    if star_lord_house:
        signified.add(star_lord_house)
    signified.update(star_lord_owns)
    if dispositor_house:
        signified.add(dispositor_house)
    signified.update(dispositor_owns)

    return {
        "csl_house": csl_house,
        "csl_owns": csl_owns,
        "star_lord": star_lord,
        "star_lord_house": star_lord_house,
        "star_lord_owns": star_lord_owns,
        "dispositor": dispositor,
        "dispositor_house": dispositor_house,
        "dispositor_owns": dispositor_owns,
        "signified": sorted(signified),
    }


# ── Public API ──────────────────────────────────────────────────────
def compute_kp_5th_csl(kundli: dict) -> Optional[Dict[str, Any]]:
    """Compute KP 5th-CSL stock-market verdict. Returns None if KP
    cusps are missing from the kundli (graceful no-op — caller must
    check and treat as 'KP unavailable').
    """
    if not isinstance(kundli, dict):
        return None

    kp = kundli.get("kp") or {}
    cusps = kp.get("cusps") if isinstance(kp, dict) else None
    if not isinstance(cusps, list) or len(cusps) < 5:
        return None

    # Find 5th cusp
    cusp5 = None
    for c in cusps:
        if isinstance(c, dict) and c.get("house") == 5:
            cusp5 = c
            break
    if not cusp5:
        return None

    # Phase 2.8.81 FIELD FIX (CRITICAL):
    # The kundli engine stores cusp data as:
    #   sl = SIGN lord (e.g. Capricorn → Saturn)  ← NOT sub-lord
    #   sb = SUB-lord (canonical KP CSL)          ← THIS is what we want
    #   ss = sub-sub-lord
    # Earlier versions read `sl` and got sign-lord by mistake, producing
    # systematically wrong CSL verdicts (validated against Astrosage on
    # P40: stored sb matches canonical math 12/12; sl was sign-lord).
    csl_planet = (cusp5.get("sb") or cusp5.get("subLord")
                  or cusp5.get("sub_lord"))
    if not csl_planet or not isinstance(csl_planet, str):
        return None

    planets = kundli.get("planets") or []
    asc_sign = kundli.get("ascendant", "")
    asc_si = _SIGN_IDX.get(asc_sign)
    if asc_si is None or not planets:
        return None

    chain = _csl_signification_chain(csl_planet, planets, asc_si)
    signified: Set[int] = set(chain["signified"])

    gain_hits: List[int] = sorted(signified & _GAIN_HOUSES)
    loss_hits: List[int] = sorted(signified & _LOSS_HOUSES)
    speculation_active: bool = _SPECULATION_HOUSE in signified

    # ── Verdict (KP-purist rules) ───────────────────────────────────
    # KP school: ANY signification of 8 or 12 by 5th CSL = stocks-avoid.
    # Even mixed {2, 8} → RED, since loss house contamination is decisive.
    if len(loss_hits) >= 1:
        verdict = "RED"
        score_weight = -4
        reason = (f"5th CSL {csl_planet} signifies loss house(s) "
                  f"{loss_hits}"
                  + (f" alongside gain {gain_hits}" if gain_hits else "")
                  + " — KP says AVOID stock market (8/12 contamination).")
    elif len(gain_hits) >= 2 and not loss_hits:
        verdict = "GREEN"
        score_weight = 3
        reason = (f"5th CSL {csl_planet} signifies gain trio {gain_hits} "
                  f"with no 8/12 — KP confirms market entry.")
    elif (len(gain_hits) >= 1 and not loss_hits) or speculation_active:
        verdict = "AMBER"
        score_weight = 1
        reason = (f"5th CSL {csl_planet} signifies "
                  f"{gain_hits or [_SPECULATION_HOUSE]} — partial signal, "
                  f"small/disciplined entry only.")
    else:
        verdict = "NEUTRAL"
        score_weight = 0
        reason = (f"5th CSL {csl_planet} gives no clear stock signal "
                  f"(signified: {chain['signified']}).")

    return {
        "csl_planet": csl_planet,
        "cusp5_longitude": cusp5.get("longitude"),
        "cusp5_sign": cusp5.get("sign"),
        "chain": chain,
        "gain_hits": gain_hits,
        "loss_hits": loss_hits,
        "speculation_active": speculation_active,
        "verdict": verdict,         # GREEN | AMBER | NEUTRAL | RED
        "score_weight": score_weight,  # +3 | +1 | 0 | -4
        "reason": reason,
        "engine_version": "kp_5th_csl_v1.1_sb_node_dispositor",
    }

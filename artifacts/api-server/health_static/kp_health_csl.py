"""Phase H1 — KP Cuspal Sub-Lord (CSL) layer for HEALTH (non-timing).

Pure deterministic. ZERO LLM. Same kundli → same verdict forever.

KP rule (health / vitality-disease-chronic):
  1st cusp = vitality controller   (body strength, life-force channel)
  6th cusp = disease/recovery controller (immunity, fight against illness)
  8th cusp = chronic / longevity controller (long-term affliction channel)

  Each cusp's Sub-Lord (CSL) tells whether the channel is supported
  (signifies 1/5/11 — vitality/recovery/fulfilment) or contaminated
  (signifies 6/8/12 — disease/chronic/hospital).

  Significations of a CSL = union of:
    1. House occupied by CSL planet
    2. Houses owned by CSL planet (sign-lordship)
    3. House occupied by CSL's nakshatra-lord (star-lord)
    4. Houses owned by CSL's nakshatra-lord
    5. (Phase 2.8.81 helper) Node dispositor for Rahu/Ketu CSLs

  Score per cusp:
    +2 per house in {1, 5, 11}  (gain/strength trio)
    -3 per house in {6, 8, 12}  (loss/disease/chronic — decisive)

  Verdict per cusp:
    GREEN  — 2+ gain houses signified AND no 6/8/12 contamination
    RED    — any 6/8/12 signification (KP-purist: contamination decisive)
    YELLOW — partial / weak / mixed (everything else)

Integration policy (Option B — weighted nudge, NOT hard override):
  Used by health_facts.compute_health_facts to apply small ±1/±2 nudges
  to vitality / disease_resistance / chronic_risk dimension scores.
  Never overrides Vedic verdict on its own; meant as confirming /
  disconfirming signal layer. KP-Vedic conflict resolver in
  health_facts handles strong disagreement → demote with conflict_flag.

Public:
  compute_kp_health_csl(kundli) -> dict | None
      None when KP cusps absent → caller treats as "KP unavailable" and
      proceeds with pure-Vedic verdicts.

ADD-ONLY: REUSES the chain helper from stock_engine.kp_5th_csl —
node-dispositor support already there since Phase 2.8.81. Stock_engine
untouched.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from stock_engine.kp_5th_csl import (  # noqa: E402
    _SIGN_IDX,
    _csl_signification_chain,
)

# KP houses for HEALTH (vitality/recovery vs disease/chronic)
_GAIN_HOUSES: Set[int] = {1, 5, 11}    # vitality, recovery, fulfilment
_LOSS_HOUSES: Set[int] = {6, 8, 12}    # disease, chronic, hospital — decisive

_GAIN_WEIGHT: int = 2
_LOSS_WEIGHT: int = -3


def _evaluate_cusp(
    cusp: dict,
    planets: List[dict],
    asc_si: int,
    label: str,
) -> Optional[Dict[str, Any]]:
    """Compute signification chain + verdict for one cusp."""
    # `sb` is the canonical KP sub-lord (CSL). Same field-name fix
    # as Phase 2.8.81 finance — `sl` is sign-lord, NOT sub-lord.
    csl_planet = (cusp.get("sb") or cusp.get("subLord")
                  or cusp.get("sub_lord"))
    if not csl_planet or not isinstance(csl_planet, str):
        return None

    chain = _csl_signification_chain(csl_planet, planets, asc_si)
    signified: Set[int] = set(chain.get("signified") or [])

    gain_hits: List[int] = sorted(signified & _GAIN_HOUSES)
    loss_hits: List[int] = sorted(signified & _LOSS_HOUSES)

    score = (_GAIN_WEIGHT * len(gain_hits)) + (_LOSS_WEIGHT * len(loss_hits))

    # Verdict — KP-purist: any 6/8/12 = RED (contamination decisive)
    if loss_hits:
        verdict = "RED"
        reason = (f"{label} CSL {csl_planet} signifies disease-zone "
                  f"house(s) {loss_hits}"
                  + (f" alongside support {gain_hits}" if gain_hits else "")
                  + " — contamination by 6/8/12.")
    elif len(gain_hits) >= 2:
        verdict = "GREEN"
        reason = (f"{label} CSL {csl_planet} signifies support houses "
                  f"{gain_hits} with no 6/8/12 — clean health channel.")
    elif gain_hits:
        verdict = "YELLOW"
        reason = (f"{label} CSL {csl_planet} signifies {gain_hits} only "
                  "— partial / weak signal.")
    else:
        verdict = "YELLOW"
        reason = (f"{label} CSL {csl_planet} gives no clear "
                  f"support/contamination signal "
                  f"(signified: {sorted(signified)}).")

    return {
        "cusp_house": cusp.get("house"),
        "cusp_sign": cusp.get("sign"),
        "cusp_longitude": cusp.get("longitude"),
        "csl_planet": csl_planet,
        "chain": chain,
        "gain_hits": gain_hits,
        "loss_hits": loss_hits,
        "score": score,
        "verdict": verdict,
        "reason": reason,
    }


# ── Public API ──────────────────────────────────────────────────────
def compute_kp_health_csl(kundli: dict) -> Optional[Dict[str, Any]]:
    """Compute KP 1st-CSL + 6th-CSL + 8th-CSL health verdict.

    Returns dict with h1 + h6 + h8 sub-blocks plus aggregate flags + nudges,
    OR None when KP cusps are missing (caller proceeds with Vedic-only).
    """
    if not isinstance(kundli, dict):
        return None

    kp = kundli.get("kp") or {}
    cusps = kp.get("cusps") if isinstance(kp, dict) else None
    if not isinstance(cusps, list) or len(cusps) < 8:
        return None

    cusp1 = next((c for c in cusps
                  if isinstance(c, dict) and c.get("house") == 1), None)
    cusp6 = next((c for c in cusps
                  if isinstance(c, dict) and c.get("house") == 6), None)
    cusp8 = next((c for c in cusps
                  if isinstance(c, dict) and c.get("house") == 8), None)
    if not cusp1 or not cusp6 or not cusp8:
        return None

    planets = kundli.get("planets") or []
    asc_sign = kundli.get("ascendant", "")
    asc_si = _SIGN_IDX.get(asc_sign)
    if asc_si is None or not planets:
        return None

    h1 = _evaluate_cusp(cusp1, planets, asc_si, "1st")
    h6 = _evaluate_cusp(cusp6, planets, asc_si, "6th")
    h8 = _evaluate_cusp(cusp8, planets, asc_si, "8th")
    if not h1 or not h6 or not h8:
        return None

    # ── Aggregate flags consumed by health_facts dimension scorers ──
    # kp_vitality_support : 1st CSL clean GREEN
    # kp_recovery_support : 6th CSL clean GREEN (immunity channel clean)
    # kp_chronic_signal   : 8th CSL contaminated by 6/8/12 (chronic risk active)
    # kp_disease_signal   : 6th CSL contaminated by 6/8/12 (disease channel hot)
    kp_vitality_support = (h1["verdict"] == "GREEN")
    kp_recovery_support = (h6["verdict"] == "GREEN")
    kp_chronic_signal = bool(h8["loss_hits"])
    kp_disease_signal = bool(h6["loss_hits"])

    # Vitality nudge — based on 1st cusp score (cap ±2).
    v_score = h1["score"]
    if v_score >= 4:
        vitality_nudge = 2
    elif v_score >= 2:
        vitality_nudge = 1
    elif v_score <= -4:
        vitality_nudge = -2
    elif v_score <= -2:
        vitality_nudge = -1
    else:
        vitality_nudge = 0

    # Disease-resistance nudge — based on 6th cusp.
    # 6th cusp GREEN = clean recovery channel = +nudge to disease_resistance
    # 6th cusp RED   = disease channel hot    = -nudge
    d_score = h6["score"]
    if d_score >= 4:
        disease_nudge = 2
    elif d_score >= 2:
        disease_nudge = 1
    elif d_score <= -4:
        disease_nudge = -2
    elif d_score <= -2:
        disease_nudge = -1
    else:
        disease_nudge = 0

    # Chronic-risk nudge — based on 8th cusp. NOTE: chronic_risk
    # semantics are INVERTED (RED verdict = high risk / bad). So 8th
    # cusp contamination should INCREASE chronic_risk raw score
    # (i.e. nudge toward RED). 8th cusp GREEN should DECREASE risk.
    c_score = h8["score"]
    if c_score <= -4:
        chronic_nudge = 2     # +2 to risk score (worse)
    elif c_score <= -2:
        chronic_nudge = 1
    elif c_score >= 4:
        chronic_nudge = -2    # -2 to risk score (better)
    elif c_score >= 2:
        chronic_nudge = -1
    else:
        chronic_nudge = 0

    return {
        "h1": h1,
        "h6": h6,
        "h8": h8,
        "kp_vitality_support": kp_vitality_support,
        "kp_recovery_support": kp_recovery_support,
        "kp_chronic_signal": kp_chronic_signal,
        "kp_disease_signal": kp_disease_signal,
        "vitality_nudge": vitality_nudge,        # → vitality dim
        "disease_nudge": disease_nudge,          # → disease_resistance dim
        "chronic_nudge": chronic_nudge,          # → chronic_risk dim (inverted)
        "engine_version": "kp_health_csl_v1.0_h1_h6_h8",
    }

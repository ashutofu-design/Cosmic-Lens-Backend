"""Phase 2.8.80 — KP Cuspal Sub-Lord (CSL) layer for FINANCE (non-timing).

Pure deterministic. ZERO LLM. Same kundli → same verdict forever.

KP rule (finance / wealth-flow):
  2nd cusp  = wealth-house controller (savings, accumulated dhana)
  11th cusp = gains-house controller  (income flow, fulfillment of desires)

  Each cusp's Sub-Lord (CSL) tells whether the native's wealth/gain channel
  is supported (signifies 2/6/11) or contaminated (signifies 8/12).

  Significations of a CSL = union of:
    1. House occupied by CSL planet
    2. Houses owned by CSL planet (sign-lordship)
    3. House occupied by CSL's nakshatra-lord (star-lord)
    4. Houses owned by CSL's nakshatra-lord

  Score per cusp:
    +2 per house in {2, 6, 11}  (gain trio)
    -3 per house in {8, 12}     (loss/drain)

  Verdict per cusp:
    GREEN  — score >= 2 AND no 8/12 contamination
    RED    — any 8 or 12 signification (KP-purist: contamination decisive)
    YELLOW — partial / weak / mixed (everything else)

Integration policy (Option B — weighted nudge, NOT hard override):
  Used by finance_facts.compute_finance_facts to apply small ±1 nudges to
  wealth_potential + risk_leak scores. Never overrides Vedic verdict on its
  own; meant as a confirming/disconfirming signal layer.

Public:
  compute_kp_finance_csl(kundli) -> dict | None
      None when KP cusps absent → caller treats as "KP unavailable" and
      proceeds with pure-Vedic verdicts.

NOTE: This module REUSES the chain helper from stock_engine.kp_5th_csl —
that helper already computes all 4 components correctly (including
nakshatra-lord chain via longitude). ADD-ONLY: stock_engine untouched.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

# Reuse battle-tested helpers from stock-side KP module (read-only import).
from stock_engine.kp_5th_csl import (  # noqa: E402
    _SIGN_IDX,
    _csl_signification_chain,
)

# KP houses for FINANCE (wealth + gains)
_GAIN_HOUSES: Set[int] = {2, 6, 11}   # accumulation, effort/competition-win, gain
_LOSS_HOUSES: Set[int] = {8, 12}      # sudden-loss/transformation, expense/drain

_GAIN_WEIGHT: int = 2    # +2 per gain-house signified
_LOSS_WEIGHT: int = -3   # -3 per loss-house signified  (contamination decisive)


def _evaluate_cusp(
    cusp: dict,
    planets: List[dict],
    asc_si: int,
    label: str,
) -> Optional[Dict[str, Any]]:
    """Compute signification chain + verdict for one cusp."""
    csl_planet = (cusp.get("sl") or cusp.get("subLord")
                  or cusp.get("sub_lord"))
    if not csl_planet or not isinstance(csl_planet, str):
        return None

    chain = _csl_signification_chain(csl_planet, planets, asc_si)
    signified: Set[int] = set(chain.get("signified") or [])

    gain_hits: List[int] = sorted(signified & _GAIN_HOUSES)
    loss_hits: List[int] = sorted(signified & _LOSS_HOUSES)

    score = (_GAIN_WEIGHT * len(gain_hits)) + (_LOSS_WEIGHT * len(loss_hits))

    # Verdict — KP-purist: any 8/12 = RED (contamination decisive)
    if loss_hits:
        verdict = "RED"
        reason = (f"{label} CSL {csl_planet} signifies loss house(s) "
                  f"{loss_hits}"
                  + (f" alongside gain {gain_hits}" if gain_hits else "")
                  + " — contamination by 8/12.")
    elif len(gain_hits) >= 2:
        verdict = "GREEN"
        reason = (f"{label} CSL {csl_planet} signifies gain houses "
                  f"{gain_hits} with no 8/12 — clean support.")
    elif gain_hits:
        verdict = "YELLOW"
        reason = (f"{label} CSL {csl_planet} signifies {gain_hits} only — "
                  "partial / weak signal.")
    else:
        verdict = "YELLOW"
        reason = (f"{label} CSL {csl_planet} gives no clear gain/loss "
                  f"signal (signified: {sorted(signified)}).")

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
def compute_kp_finance_csl(kundli: dict) -> Optional[Dict[str, Any]]:
    """Compute KP 2nd-CSL + 11th-CSL finance verdict.

    Returns dict with h2 + h11 sub-blocks plus aggregate flags, OR None
    when KP cusps are missing (caller proceeds with Vedic-only).
    """
    if not isinstance(kundli, dict):
        return None

    kp = kundli.get("kp") or {}
    cusps = kp.get("cusps") if isinstance(kp, dict) else None
    if not isinstance(cusps, list) or len(cusps) < 11:
        return None

    cusp2 = next((c for c in cusps
                  if isinstance(c, dict) and c.get("house") == 2), None)
    cusp11 = next((c for c in cusps
                   if isinstance(c, dict) and c.get("house") == 11), None)
    if not cusp2 or not cusp11:
        return None

    planets = kundli.get("planets") or []
    asc_sign = kundli.get("ascendant", "")
    asc_si = _SIGN_IDX.get(asc_sign)
    if asc_si is None or not planets:
        return None

    h2 = _evaluate_cusp(cusp2, planets, asc_si, "2nd")
    h11 = _evaluate_cusp(cusp11, planets, asc_si, "11th")
    if not h2 or not h11:
        return None

    # ── Aggregate flags consumed by finance_facts dimension scorers ──
    # kp_wealth_support: 2nd CSL clean-positive AND no 8/12 contamination.
    # kp_gain_support  : 11th CSL clean-positive AND no 8/12 contamination.
    # kp_leak_signal   : EITHER cusp shows 8/12 contamination.
    kp_wealth_support = (h2["verdict"] == "GREEN")
    kp_gain_support = (h11["verdict"] == "GREEN")
    kp_leak_signal = bool(h2["loss_hits"] or h11["loss_hits"])

    # Combined nudge for wealth_potential dimension (cap ±2 for safety).
    combined = (h2["score"] + h11["score"]) / 2.0
    if combined >= 2:
        wealth_nudge = 2
    elif combined >= 1:
        wealth_nudge = 1
    elif combined <= -2:
        wealth_nudge = -2
    elif combined <= -1:
        wealth_nudge = -1
    else:
        wealth_nudge = 0

    # Risk-leak nudge (raises raw leak signal if either CSL contaminated).
    risk_nudge = 1 if kp_leak_signal else 0

    return {
        "h2": h2,
        "h11": h11,
        "kp_wealth_support": kp_wealth_support,
        "kp_gain_support": kp_gain_support,
        "kp_leak_signal": kp_leak_signal,
        "wealth_nudge": wealth_nudge,    # added to wealth_potential score
        "risk_nudge": risk_nudge,        # added to risk_leak raw count
        "engine_version": "kp_finance_csl_v1.0_deterministic",
    }

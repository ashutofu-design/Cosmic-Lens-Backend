"""User-facing marriage pipeline rules (Steps 0–8).

Code mapping (marriage_engine_v2.py):
  User STEP 6 (Dasha)     → _step5_* + _select_top_3 (no transit in ranking)
  User STEP 7 (Transit)   → _attach_transit_to_window + _step7_ashtakavarga (final only)
"""

from __future__ import annotations

# ── STEP 6 — Vimshottari Dasha (EXACT MD · AD · PD) ───────────────────────
STEP_6_DASHA_RULES = """
STEP 6 — Dasha timing (Mahadasha · Antardasha · Pratyantardasha)

MANDATORY DATA (no guesswork for final month/year):
  • Source: kundli['dashas'] tree from kp_engine / calc_vimshottari_dasha.
  • Each window MUST be one real PD chunk: {MD, AD, PD, startDate, endDate}.
  • Prefer chart's nested subDashas → subDashas (exact PD dates).
  • If PD list missing only then synthesize 9 PDs inside AD (Vimshottari
    proportions) — mark pd_synthesized=true; never invent AD/MD lords.

SCAN (every future PD one-by-one):
  1. Build flat chain via _flatten_dasha_chain (all MD-AD-PD rows).
  2. Filter: end > now-30d; within scan horizon (BCP/Step-0 may bias sort only).
  3. target_lords = Step 1–5 significators + D1/D9 7L (always kept).

ACTIVATION SCORE (per PD window):
  • MD in target_lords  → +1
  • AD in target_lords  → +5
  • PD in target_lords  → +6
  • D9 7L in MD/AD/PD   → +2 bonus
  • Minimum to qualify: AD_score + PD_score ≥ 5
    (AD alone = 5 OK; PD alone = 6 OK; MD-only does NOT qualify)

STEP 0 INTEGRATION:
  • late_marriage + BCP focus_ages (e.g. 31,34,36) → sort/boost only;
    do NOT skip far years when BCP says late.
  • primary_reference_age from Step 0 aligns dasha windows near BCP year.
  • bcp_age_hits tagged on each window (user age span inside PD).

OUTPUT (per candidate):
  md, ad, pd, start_iso, end_iso, score, ad_supports, pd_supports,
  pd_only_activation, bcp_age_hits, covers_current_age.

CURRENT MD-AD-PD: _step5_dasha_activation at datetime.utcnow().
"""

# ── STEP 7 — Double transit on FINAL dasha window only ──────────────────
STEP_7_TRANSIT_RULES = """
STEP 7 — Transit check (simple): final dasha ke exact time par support?

NOT applied to every AD/PD in the chain.

FLOW:
  1. STEP 6 picks the final dasha window (MD·AD·PD + start/end dates)
     using significators + BCP sort only — NO transit filter.
  2. STEP 7 runs ONE double-transit check on THAT final window only:
     • Check date = midpoint of the final PD period (start+end)/2.
     • Swiss Ephemeris sidereal (Lahiri): Jupiter + Saturn.

TARGET SIGNS (7H / 7L / top significators / D9 7L sign):
  • 7th house sign from lagna
  • 7th lord's natal sign
  • Top ranked planet signs (Step 5)
  • D9 7th lord natal sign

JUPITER: on target sign OR 5th/7th/9th aspect.
SATURN:  on target sign OR 3rd/7th/10th aspect.

ANSWER (verification only — does not re-pick dasha):
  • double_transit (dt)     = BOTH Jupiter AND Saturn hit any target.
  • transit_support         = at least ONE of Jupiter OR Saturn hits.
  • Dasha window stays final either way; transit only confirms/obstructs.

Optional: 7H Ashtakavarga bindus on final window (smooth vs delay note).

FINAL month/year = Step 6 window dates; Step 7 says whether Guru+Shani
support that exact period.
"""

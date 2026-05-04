"""
event_timing/marriage/marriage_timing_v2.py
===========================================
ENGINE B — Phase 2.9.0 SIMPLIFIED MARRIAGE TIMING (ADD-ONLY).

User-locked refactor per master prompt (May 4 2026):
  Filter -> Tighten -> Prioritize -> Score -> Rank
  (NOT: Filter -> Expand -> Expand -> Expand)

Goal: reduce noise, improve signal clarity, target ~90% real-world accuracy.

Architecture:
  - This file does NOT replace marriage_timing.py (frozen).
  - Reuses helpers from marriage_timing.py for KP, D1/D9 link, dasha scan,
    transit ephemeris — all already-validated logic stays.
  - Implements 15-step simplified pipeline.

Key differences from Engine A (2.8.83.1):
  - Transit: NO REJECTION — pure scoring (max +4)
  - target_lords: HARD CAP at 5 via tier1 priority
  - D9: only 7H + 7L (no aspect expansion, no co-karak)
  - AD AND PD must both be in target_lords (strict)
  - Age boost: ±2 based on urgency
  - Score formula: simplified (5 components vs 12)
  - Window threshold: 2.5 (same)

Public function:
  compute_timing_window_v2(kundli, intel, kp, birth) -> dict

Output dict has same shape as Engine A for drop-in comparison.
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

# Reuse all primitives from frozen Engine A
from .marriage_timing import (
    _SIGNS, _SIGN_LORDS, _MARRIAGE_HOUSES,
    _KP_PLANET_NAMES,
    _kp_sublord_filter_planet,
    compute_step2_link_filter,
    _scan_cluster_ads, _project_pds,
    _get_transits_at, _transit_sign_idx,
    _is_jupiter_aspect, _is_saturn_aspect, _is_mars_aspect,
    _dasha_lord_strength,
    _planet_sign_idx, _planet_is_retrograde,
    _extract_birth_year, _extract_birth_date, _extract_gender,
    _compute_current_age,
    _parse_dt, _format_window, _merge_adjacent_windows,
    _AGE_HARD_BLOCK,
    _step0_late_early_tendency,
)

# v2 thresholds
_V2_WINDOW_MIN_SCORE = 2.5
_V2_WINDOW_STRONG = 5.0
_V2_WINDOW_MEDIUM = 3.5
_V2_TARGET_LORDS_MAX = 5

# Age urgency thresholds (for STEP 11 age boost)
_V2_LATE_AGE_FEMALE = 30
_V2_LATE_AGE_MALE = 33
_V2_EARLY_AGE_FEMALE = 22
_V2_EARLY_AGE_MALE = 24


# ════════════════════════════════════════════════════════════════════
# STEP 5 — Priority builder
# ════════════════════════════════════════════════════════════════════
def _v2_build_priority_tiers(step2: dict) -> Tuple[List[str], List[str], List[str]]:
    """Build tier1/tier2/tier3 from STEP 2 link-filter output.

    tier1 = KP=STRONG and link=BOTH      (both D1+D9 link)
    tier2 = KP=STRONG and link=ONE  OR  KP=MIXED and link!=NONE
    tier3 = everything else (KP=WEAK or link=NONE)
    """
    tier1: List[str] = []
    tier2: List[str] = []
    tier3: List[str] = []
    per_planet = step2.get("per_planet") or []
    for entry in per_planet:
        planet = entry.get("planet")
        kp_v = entry.get("step1_verdict") or "UNKNOWN"
        link = entry.get("link_strength") or "NONE"
        if kp_v == "STRONG" and link == "BOTH":
            tier1.append(planet)
        elif kp_v == "STRONG" and link in ("D1", "D9"):
            tier2.append(planet)
        elif kp_v == "MIXED" and link != "NONE":
            tier2.append(planet)
        else:
            tier3.append(planet)
    return tier1, tier2, tier3


# ════════════════════════════════════════════════════════════════════
# STEP 6 — Target lords build (MAX 5)
# ════════════════════════════════════════════════════════════════════
def _v2_build_target_lords(tier1: List[str], tier2: List[str],
                            seventh_lord: Optional[str]) -> List[str]:
    """Build target_lords list. MAX 5 per master prompt.

    Order: top 3 from tier1 -> Venus -> Jupiter -> 7L if missing -> tier2 fill.
    """
    lords: List[str] = []
    seen: Set[str] = set()

    def _add(p: Optional[str]):
        if p and p not in seen and len(lords) < _V2_TARGET_LORDS_MAX:
            lords.append(p)
            seen.add(p)

    for p in tier1[:3]:
        _add(p)
    _add("Venus")
    _add("Jupiter")
    if seventh_lord:
        _add(seventh_lord)
    # Fill remaining slots from tier2 if room
    for p in tier2:
        _add(p)
    return lords


# ════════════════════════════════════════════════════════════════════
# STEP 8 — Transit scoring (NO REJECTION)
# ════════════════════════════════════════════════════════════════════
def _v2_transit_score(transit: dict, h7_si: Optional[int],
                      seventh_lord_si: Optional[int]) -> Tuple[float, List[str]]:
    """Pure scoring. NEVER rejects.
    Jupiter active (on 7H or aspect 7L)  -> +2
    Saturn  active (on 7H or aspect 7L)  -> +1
    Both active                          -> +1 bonus
    """
    if h7_si is None:
        return (0.0, [])
    score = 0.0
    notes: List[str] = []
    jup_si = _transit_sign_idx(transit, "Jupiter")
    sat_si = _transit_sign_idx(transit, "Saturn")
    jup_active = False
    sat_active = False
    if jup_si is not None:
        if jup_si == h7_si:
            jup_active = True; notes.append(f"Jup in 7H ({_SIGNS[h7_si]})")
        elif seventh_lord_si is not None and _is_jupiter_aspect(jup_si, seventh_lord_si):
            jup_active = True; notes.append(f"Jup aspect 7L ({_SIGNS[seventh_lord_si]})")
    if sat_si is not None:
        if sat_si == h7_si:
            sat_active = True; notes.append(f"Sat in 7H ({_SIGNS[h7_si]})")
        elif seventh_lord_si is not None and _is_saturn_aspect(sat_si, seventh_lord_si):
            sat_active = True; notes.append(f"Sat aspect 7L ({_SIGNS[seventh_lord_si]})")
    if jup_active:
        score += 2.0
    if sat_active:
        score += 1.0
    if jup_active and sat_active:
        score += 1.0
        notes.append("DT bonus")
    return (score, notes)


# ════════════════════════════════════════════════════════════════════
# STEP 9 — Mars trigger
# ════════════════════════════════════════════════════════════════════
def _v2_mars_trigger(transit: dict, h7_si: Optional[int],
                     venus_si: Optional[int],
                     seventh_lord_si: Optional[int]) -> Tuple[float, str]:
    """Mars +1 if activates (conj/aspect) 7H, 7L, or Venus."""
    mars_si = _transit_sign_idx(transit, "Mars")
    if mars_si is None:
        return (0.0, "")
    targets: List[Tuple[str, int]] = []
    if h7_si is not None: targets.append(("7H", h7_si))
    if seventh_lord_si is not None: targets.append(("7L", seventh_lord_si))
    if venus_si is not None: targets.append(("Venus", venus_si))
    for label, t_si in targets:
        if mars_si == t_si:
            return (1.0, f"Mars conj {label}")
        if _is_mars_aspect(mars_si, t_si):
            return (1.0, f"Mars aspect {label}")
    return (0.0, "")


# ════════════════════════════════════════════════════════════════════
# STEP 10 — Strength multiplier (clamp 0.7..1.3)
# ════════════════════════════════════════════════════════════════════
def _v2_strength_mult(planets: list, md: str, ad: str, pd: str) -> float:
    """Per master prompt: 0.7..1.3 multiplier from dignity+placement.
    Reuses _dasha_lord_strength (already returns 0.5..1.3) but clamped to 0.7..1.3.
    Averaged across MD/AD/PD."""
    parts = []
    for lord in (md, ad, pd):
        if lord:
            s = _dasha_lord_strength(planets, lord)
            parts.append(max(0.7, min(1.3, s)))
    if not parts:
        return 1.0
    return sum(parts) / len(parts)


# ════════════════════════════════════════════════════════════════════
# STEP 11 — Age priority boost
# ════════════════════════════════════════════════════════════════════
def _v2_age_boost(age: Optional[float], gender: str, tendency: str,
                  window_start: datetime, today: datetime) -> Tuple[float, str]:
    """Age boost per master prompt:
      LATE + age >= late_threshold:
          window <= 1yr  -> +2 (urgency)
          else           -> -1 (already too far)
      EARLY + young:
          window <= 1yr  -> +2
    """
    if age is None:
        return (0.0, "")
    g = (gender or "").strip().lower()
    late_thr = _V2_LATE_AGE_FEMALE if g.startswith("f") else _V2_LATE_AGE_MALE
    early_thr = _V2_EARLY_AGE_FEMALE if g.startswith("f") else _V2_EARLY_AGE_MALE
    years_out = max(0.0, (window_start - today).days / 365.25)
    if tendency == "LATE" and age >= late_thr:
        if years_out <= 1.0:
            return (2.0, f"AGE-URGENT (LATE+{age:.0f}+window<=1yr)")
        return (-1.0, f"AGE-FAR (LATE+{age:.0f}+window>1yr)")
    if tendency == "EARLY" and age <= early_thr and years_out <= 1.0:
        return (2.0, f"AGE-EARLY (EARLY+{age:.0f}+window<=1yr)")
    return (0.0, "")


# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════
def _resolve_lagna_etc(kundli: dict, intel: dict) -> Dict[str, Any]:
    planets = kundli.get("planets") or []
    asc_sign = (intel.get("lagna_sign") or kundli.get("ascendant") or "").strip()
    lagna_si = _SIGNS.index(asc_sign) if asc_sign in _SIGNS else None
    h7_si = ((lagna_si + 6) % 12) if lagna_si is not None else None
    venus_si = _planet_sign_idx(planets, "Venus")
    moon_si = _planet_sign_idx(planets, "Moon")
    seventh_lord = None
    for hl in (intel.get("house_lords") or []):
        if isinstance(hl, dict) and hl.get("house") == 7:
            seventh_lord = hl.get("lord"); break
    if not seventh_lord and h7_si is not None:
        seventh_lord = _SIGN_LORDS.get(h7_si)
    seventh_lord_si = _planet_sign_idx(planets, seventh_lord) if seventh_lord else None
    return {
        "planets": planets, "lagna_si": lagna_si, "h7_si": h7_si,
        "venus_si": venus_si, "moon_si": moon_si,
        "seventh_lord": seventh_lord, "seventh_lord_si": seventh_lord_si,
    }


# ════════════════════════════════════════════════════════════════════
# MAIN — compute_timing_window_v2
# ════════════════════════════════════════════════════════════════════
def compute_timing_window_v2(kundli: dict, intel: dict, kp: dict,
                              birth: Optional[Any] = None) -> dict:
    """Engine B v2.9.0 — simplified marriage timing.

    Returns dict with same shape as Engine A for drop-in comparison.
    """
    factors: List[str] = ["[ENGINE B v2.9.0]"]

    def _empty(reason: str) -> dict:
        return {
            "verdict": "UNKNOWN", "band": "WEAK",
            "primary_window": None, "backup_window": None,
            "key_trigger": None, "confluence_strength": None,
            "ul_outlook": None, "risk_flag": None, "risk_flags": [],
            "factors": factors + [reason],
            "top_3_windows": [],
            "step0_tendency": {"verdict": "BALANCED", "score": 0, "reasons": []},
            "engine_version": "2.9.0",
        }

    if not isinstance(kundli, dict) or not isinstance(intel, dict):
        return _empty("Insufficient input: missing kundli/intel")

    ctx = _resolve_lagna_etc(kundli, intel)
    planets = ctx["planets"]
    if not planets or ctx["lagna_si"] is None:
        return _empty("Insufficient input: no planets/lagna")
    lagna_si = ctx["lagna_si"]
    h7_si = ctx["h7_si"]
    moon_si = ctx["moon_si"]
    venus_si = ctx["venus_si"]
    seventh_lord = ctx["seventh_lord"]
    seventh_lord_si = ctx["seventh_lord_si"]

    gender = _extract_gender(birth, intel)
    age = _compute_current_age(birth)
    factors.append(f"7L: {seventh_lord} | Lagna: {_SIGNS[lagna_si]} | "
                   f"7H: {_SIGNS[h7_si]} | Age: {age} {gender}")

    # ─── STEP 1 — Age hard block
    if age is not None and age < _AGE_HARD_BLOCK:
        return _empty(f"BLOCK: age {age:.1f} < {_AGE_HARD_BLOCK}")

    # ─── STEP 2 — Early/Late tendency + mode
    step0 = _step0_late_early_tendency(
        planets, intel, kp, lagna_si, h7_si, seventh_lord, venus_si,
        gender, age) or {"verdict": "BALANCED", "score": 0, "reasons": []}
    tendency = step0.get("verdict", "BALANCED")
    g = (gender or "").lower()
    late_thr = _V2_LATE_AGE_FEMALE if g.startswith("f") else _V2_LATE_AGE_MALE
    early_thr = _V2_EARLY_AGE_FEMALE if g.startswith("f") else _V2_EARLY_AGE_MALE
    if tendency == "LATE" and age is not None and age >= late_thr:
        mode = "URGENT"
    elif tendency == "EARLY" and age is not None and age <= early_thr:
        mode = "EARLY_WINDOW"
    else:
        mode = "NORMAL"
    factors.append(f"STEP 2: tendency={tendency} mode={mode}")

    # ─── STEP 3 + 4 — KP filter + D1/D9 link
    step2 = compute_step2_link_filter(kundli, kp) or {}
    per_planet = step2.get("per_planet") or []
    kept = [e for e in per_planet
            if (e.get("step1_verdict") in ("STRONG", "MIXED")
                and e.get("link_strength") in ("BOTH", "D1", "D9"))]
    dropped_kp = [e["planet"] for e in per_planet if e.get("step1_verdict") == "WEAK"]
    dropped_link = [e["planet"] for e in per_planet
                    if e.get("link_strength") == "NONE"]
    factors.append(f"STEP 3/4 KP+LINK: kept={len(kept)}, "
                   f"dropped_KP_weak={dropped_kp}, dropped_no_link={dropped_link}")

    # ─── STEP 5 — Priority tiers
    tier1, tier2, tier3 = _v2_build_priority_tiers(step2)
    factors.append(f"STEP 5 TIERS: t1={tier1} t2={tier2} t3={tier3}")

    # ─── STEP 6 — Target lords (MAX 5)
    target_lords = _v2_build_target_lords(tier1, tier2, seventh_lord)
    target_set: Set[str] = set(target_lords)
    factors.append(f"STEP 6 TARGET_LORDS (max {_V2_TARGET_LORDS_MAX}): {target_lords}")

    if not target_lords:
        return _empty("No qualifying target lords (KP+link filtered all)")

    # ─── STEP 7 — Dasha scan (AD AND PD both in target_lords)
    _ALL = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
            "Saturn", "Rahu", "Ketu"}
    candidate_ads = _scan_cluster_ads(kundli, _ALL, lookback_days=30)

    today = datetime.utcnow()
    raw_windows: List[dict] = []
    skip_ad = 0; skip_pd = 0

    for ad_blk in candidate_ads:
        md = ad_blk.get("md") or ad_blk.get("md_lord")
        ad = ad_blk.get("ad") or ad_blk.get("ad_lord")
        ad_start = _parse_dt(ad_blk.get("start"))
        ad_end = _parse_dt(ad_blk.get("end"))
        if not (md and ad and ad_start and ad_end):
            continue

        # STRICT: AD must be in target_lords
        if ad not in target_set:
            skip_ad += 1
            continue

        from_dt = max(today, ad_start)
        if from_dt >= ad_end:
            continue
        ad_months = max(3, int((ad_end - ad_start).days / 30) + 1)
        pds = _project_pds(md, ad, ad_start, ad_end, from_dt=from_dt,
                           months_needed=ad_months)

        for pd_blk in pds:
            pd_start = pd_blk.get("start"); pd_end = pd_blk.get("end")
            pd_lord = pd_blk.get("pd")
            if not (isinstance(pd_start, datetime) and isinstance(pd_end, datetime)):
                continue

            # STRICT: PD must be in target_lords
            if pd_lord not in target_set:
                skip_pd += 1
                continue

            mid = pd_start + (pd_end - pd_start) / 2
            wf: List[str] = []

            # ─── STEP 7 cluster: dasha alignment score
            # MD bonus +1 if in target, AD always +2 (already filtered),
            # PD always +3 (already filtered)
            md_pts = 1 if md in target_set else 0
            dasha_align = float(md_pts + 2 + 3)  # 5 or 6
            triple = (md_pts == 1)
            wf.append(f"+{dasha_align} cluster (MD={md}{'✓' if md_pts else 'x'} "
                      f"AD={ad}✓ PD={pd_lord}✓)" + (" TRIPLE" if triple else ""))

            # ─── STEP 8 — Transit scoring (NO REJECTION)
            transit = _get_transits_at(lagna_si, moon_si, when=mid) or {}
            tscore, tnotes = _v2_transit_score(transit, h7_si, seventh_lord_si)
            for n in tnotes: wf.append(f"+T {n}")

            # ─── STEP 9 — Mars trigger
            mscore, mnote = _v2_mars_trigger(transit, h7_si, venus_si, seventh_lord_si)
            if mnote: wf.append(f"+{mscore} {mnote}")

            # ─── STEP 10 — Strength multiplier
            smult = _v2_strength_mult(planets, md, ad, pd_lord)

            # ─── STEP 11 — Age boost
            abonus, anote = _v2_age_boost(age, gender, tendency, pd_start, today)
            if anote: wf.append(f"{abonus:+} {anote}")

            # ─── STEP 12 — Final score
            # (dasha_alignment + transit + mars) * strength + age
            base = dasha_align + tscore + mscore
            score = (base * smult) + abonus

            if score < _V2_WINDOW_MIN_SCORE:
                continue

            raw_windows.append({
                "start": pd_start, "end": pd_end,
                "score": round(score, 2),
                "md": md, "ad": ad, "pd": pd_lord,
                "strength_mult": round(smult, 2),
                "transit": tscore, "mars": mscore, "age_bonus": abonus,
                "factors": wf,
            })

    factors.append(f"STEP 7 SCAN: AD-skipped={skip_ad}, PD-skipped={skip_pd}, "
                   f"raw_windows={len(raw_windows)}")

    # ─── STEP 13 already inline (score>=2.5 filter)
    # Merge adjacent windows (single event clusters)
    pre_merge = len(raw_windows)
    windows = _merge_adjacent_windows(raw_windows, gap_days=15)
    if pre_merge != len(windows):
        factors.append(f"MERGE: {pre_merge} -> {len(windows)} adjacent merged")

    # ─── STEP 14 — Sort & select top 3 (different ADs)
    windows.sort(key=lambda w: (-float(w.get("score", 0)), w["start"]))
    top_3: List[dict] = []
    used_ads: Set[str] = set()
    for w in windows:
        if not top_3:
            top_3.append(w); used_ads.add(w.get("ad")); continue
        if len(top_3) >= 3: break
        if w.get("ad") not in used_ads:
            top_3.append(w); used_ads.add(w.get("ad"))
    # If <3 distinct ADs, fill with next highest regardless
    if len(top_3) < 3:
        for w in windows:
            if len(top_3) >= 3: break
            if w not in top_3:
                top_3.append(w)

    # ─── STEP 15 — Output
    if not top_3:
        verdict = "DENIED"
        strength = "WEAK"
        primary_w = backup_w = None
        ktrig = None
    else:
        p = top_3[0]
        # Verdict logic
        if mode == "URGENT":
            # LATE + URGENT: any qualifying window = DELAYED (not denied)
            verdict = "DELAYED" if p["score"] >= _V2_WINDOW_MEDIUM else "DENIED"
        else:
            verdict = "PROMISED"
        if p["score"] >= _V2_WINDOW_STRONG:
            strength = "STRONG"
        elif p["score"] >= _V2_WINDOW_MEDIUM:
            strength = "MODERATE"
        else:
            strength = "WEAK"
        primary_w = _format_window(p["start"], p["end"])
        backup_w = (_format_window(top_3[1]["start"], top_3[1]["end"])
                    if len(top_3) >= 2 else None)
        ktrig = (f"{p['md']}/{p['ad']}/{p['pd']} "
                 f"(score {p['score']}, mult {p['strength_mult']})")

    top_3_serial = [{
        "window": _format_window(w["start"], w["end"]),
        "start": w["start"].strftime("%Y-%m-%d"),
        "end": w["end"].strftime("%Y-%m-%d"),
        "score": w["score"],
        "md": w["md"], "ad": w["ad"], "pd": w["pd"],
        "strength_mult": w.get("strength_mult", 1.0),
        "transit": w.get("transit", 0),
        "mars": w.get("mars", 0),
        "age_bonus": w.get("age_bonus", 0),
        "factors": w.get("factors", []),
    } for w in top_3]

    return {
        "verdict": verdict,
        "band": "MEDIUM" if strength == "MODERATE" else strength,
        "primary_window": primary_w,
        "backup_window": backup_w,
        "key_trigger": ktrig,
        "confluence_strength": strength,
        "ul_outlook": None,
        "risk_flag": None,
        "risk_flags": [],
        "factors": factors,
        "top_3_windows": top_3_serial,
        "step0_tendency": step0,
        "engine_version": "2.9.0",
        "mode": mode,
        "tier1": tier1, "tier2": tier2, "tier3": tier3,
        "target_lords": target_lords,
    }


def assess_marriage_v2(kundli: dict, intel: dict, kp: dict,
                       birth: Optional[Any] = None,
                       question: str = "") -> dict:
    """Engine B top-level assess function (mirrors assess_marriage shape)."""
    return compute_timing_window_v2(kundli, intel, kp, birth) or {}

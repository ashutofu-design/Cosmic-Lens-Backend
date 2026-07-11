"""Promotion timing engine v1 — classical 7-step checklist + AD/PD-first dasha.

Flow (astrologer serial):
  1 D1 10H/10L → 2 Sun+Saturn → 3 D10 → 4 6H+11H → 5 Dasha (AD/PD priority)
  6 Transit note → 7 Ashtakvarga 28+ gate
  [BCP 11L+10L parallel — dasha boost only, not lead narrative]

Timing rule: agar current dasha (AD/PD) support na kare → next supportive
AD/PD window scan karke wahi timing batao; current mat bolo.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from event_timing.career.bcp_promotion_ages import (
    compute_bcp_promotion_ages,
    format_bcp_promotion_age_list,
)
from event_timing.career.govt_job_engine_v1 import (
    _aspect_houses,
    _dasha_lords,
    _divisional_planets,
    _house_lord,
    _is_strong_dignity,
    _parse_iso,
    _planet_dignity,
    _planet_house,
    _planet_sign,
    _sign_lord,
)

_STRONG_DIGNITY = frozenset({"exalted", "own-sign", "moolatrikona", "own sign", "moola-trikona"})
_KENDRA_TRIKONA = frozenset({1, 4, 5, 7, 9, 10, 11})
_BENEFIC_PROMO = frozenset({"Jupiter", "Sun", "Venus", "Mercury", "Moon"})
_AV_SMOOTH_MIN = 28
_PROMO_SCAN_YEARS = 8
_SCORE_PD_CORE = 9
_SCORE_AD_CORE = 7
_SCORE_PD_BENEFIC = 5
_SCORE_AD_BENEFIC = 4
_SCORE_MD_CORE = 2
_SCORE_AD_PD_CONFLUENCE = 4
_MIN_PROMO_CHUNK = 6

_VIMS_ORDER = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]
_VIMS_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}


def _lords_mutual_link(
    planets: list,
    lord_a: str,
    lord_b: str,
    chart_label: str,
) -> tuple[int, list[str], list[str]]:
    score = 0
    why: list[str] = []
    flags: list[str] = []
    ha = _planet_house(planets, lord_a)
    hb = _planet_house(planets, lord_b)
    if not ha or not hb:
        return 0, why, flags

    if ha == hb:
        score += 22
        flags.append(f"{lord_a}_{lord_b}_conjunct_{chart_label}")
        why.append(
            f"{lord_a}-{lord_b} conjunct in {ha}H ({chart_label}) — karma-labha yoga (+22)"
        )
    elif abs(ha - hb) == 6:
        score += 18
        flags.append(f"{lord_a}_{lord_b}_7th_{chart_label}")
        why.append(
            f"{lord_a}-{lord_b} mutual 7th ({chart_label}) — recognition-gains link (+18)"
        )

    sign_a = _planet_sign(planets, lord_a)
    sign_b = _planet_sign(planets, lord_b)
    if (
        sign_a and sign_b
        and _sign_lord(sign_a) == lord_b
        and _sign_lord(sign_b) == lord_a
    ):
        score += 20
        flags.append(f"{lord_a}_{lord_b}_parivartana_{chart_label}")
        why.append(f"{lord_a}-{lord_b} parivartana ({chart_label}) — promotion exchange (+20)")
    return score, why, flags


def _assess_ashtakvarga_gate(kundli: dict, lagna_si: int) -> dict:
    """Step 7 — 10H + 11H SAV; 28+ smooth, below = delay risk."""
    out: dict = {
        "step": 7,
        "tenth_house_sav": None,
        "eleventh_house_sav": None,
        "smooth_promotion": None,
        "delay_risk": False,
        "why": [],
    }
    if lagna_si < 0:
        out["why"].append("Ashtakvarga unavailable — lagna missing")
        return out
    try:
        from ashtakavarga import compute_ashtakavarga  # type: ignore
        av = compute_ashtakavarga(kundli.get("planets") or [], lagna_si) or {}
    except Exception:
        out["why"].append("Ashtakvarga module unavailable")
        return out

    sav = av.get("sav") or av.get("SAV")
    if not isinstance(sav, list):
        out["why"].append("SAV data missing")
        return out

    tenth_si = (lagna_si + 9) % 12
    eleventh_si = (lagna_si + 10) % 12
    s10 = sav[tenth_si] if tenth_si < len(sav) else None
    s11 = sav[eleventh_si] if eleventh_si < len(sav) else None
    out["tenth_house_sav"] = s10
    out["eleventh_house_sav"] = s11

    smooth = True
    if isinstance(s10, int):
        if s10 >= _AV_SMOOTH_MIN:
            out["why"].append(f"10H SAV={s10} (≥{_AV_SMOOTH_MIN}) — smooth career rise")
        else:
            smooth = False
            out["delay_risk"] = True
            out["why"].append(
                f"10H SAV={s10} (<{_AV_SMOOTH_MIN}) — promotion delay/obstruction risk"
            )
    if isinstance(s11, int):
        if s11 >= _AV_SMOOTH_MIN:
            out["why"].append(f"11H SAV={s11} (≥{_AV_SMOOTH_MIN}) — gains increment supportive")
        else:
            smooth = False
            out["delay_risk"] = True
            out["why"].append(
                f"11H SAV={s11} (<{_AV_SMOOTH_MIN}) — hike may stall at last moment"
            )
    out["smooth_promotion"] = smooth if (s10 is not None or s11 is not None) else None
    return out


def run_promotion_bcp_parallel(
    kundli: dict,
    lagna_si: int,
    *,
    user_age: Optional[int] = None,
    years_ahead: int = 8,
) -> dict:
    """BCP 11L+10L — parallel timing boost (not classical step 1)."""
    bcp = compute_bcp_promotion_ages(kundli, lagna_si, user_age=user_age)
    d1 = bcp.get("d1_bcp") or {}
    all_ages = bcp.get("all_promotion_ages") or []
    priority = bcp.get("future_priority_ages") or []

    areas: list[dict] = []
    for src in bcp.get("sources") or []:
        kind = str(src.get("source") or "")
        role = "11L" if kind.startswith("11") else "10L"
        typ = "placement" if kind.endswith("_placement") else (
            "dual_sign" if "dual" in kind else "aspect"
        )
        if typ == "placement":
            areas.append({
                "lord": src.get("lord"), "role": role, "type": typ,
                "house": src.get("house"), "ages": src.get("ages") or [],
                "label": src.get("label"),
            })
        else:
            for entry in src.get("houses") or []:
                areas.append({
                    "lord": src.get("lord"), "role": role, "type": typ,
                    "house": entry.get("house"), "ages": entry.get("ages") or [],
                    "label": entry.get("label"),
                })

    hi = (user_age + years_ahead) if user_age is not None else years_ahead + 30
    bcp_next = [a for a in (priority or all_ages) if user_age is None or user_age <= a <= hi][:10]

    return {
        "bcp_parallel": True,
        "eleventh_lord": bcp.get("eleventh_lord"),
        "eleventh_lord_house": bcp.get("eleventh_lord_house"),
        "tenth_lord": bcp.get("tenth_lord"),
        "tenth_lord_house": bcp.get("tenth_lord_house"),
        "aspect_houses_11l": bcp.get("aspect_houses_11l"),
        "aspect_houses_10l": bcp.get("aspect_houses_10l"),
        "promotion_areas": areas,
        "bcp_promotion_ages": bcp,
        "bcp_age_list": format_bcp_promotion_age_list(d1),
        "all_promotion_ages": all_ages,
        "future_priority_ages": priority,
        "bcp_ages_next_years": bcp_next,
        "next_activation_age": bcp.get("next_activation_age"),
        "timing_mode": bcp.get("timing_mode"),
    }


# Back-compat alias for career_timing step_audit
run_promotion_step1_bcp = run_promotion_bcp_parallel


def assess_promotion_promise(
    kundli: dict,
    intel: dict,
    *,
    lagna_si: int = -1,
    karakas_d: Optional[dict] = None,
    kp_assist: Optional[dict] = None,
) -> dict:
    """Classical steps 1–4 + 7 natal; returns ordered checklist."""
    planets = kundli.get("planets") or []
    d9 = _divisional_planets(kundli, "D9")
    d10 = _divisional_planets(kundli, "D10")

    score = 0
    why: list[str] = []
    flags: list[str] = []
    checklist: dict[str, dict] = {}

    tenth_lord = _house_lord(intel, 10)
    eleventh_lord = _house_lord(intel, 11)
    sixth_lord = _house_lord(intel, 6)

    tl_h = _planet_house(planets, tenth_lord) if tenth_lord else None
    el_h = _planet_house(planets, eleventh_lord) if eleventh_lord else None
    sl_h = _planet_house(planets, sixth_lord) if sixth_lord else None
    tl_dgn = _planet_dignity(intel, tenth_lord) if tenth_lord else None
    el_dgn = _planet_dignity(intel, eleventh_lord) if eleventh_lord else None
    sl_dgn = _planet_dignity(intel, sixth_lord) if sixth_lord else None

    step1_why: list[str] = []
    # ── Step 1: D1 10H base ─────────────────────────────────────────────
    if tl_h in _KENDRA_TRIKONA and _is_strong_dignity(tl_dgn):
        score += 18
        flags.append("10l_strong_kendra")
        step1_why.append(f"10L {tenth_lord} {tl_dgn} in {tl_h}H — career graph up (+18)")
    elif tl_h == 10 and _is_strong_dignity(tl_dgn):
        score += 18
        flags.append("10l_strong_10h")
        step1_why.append(f"10L {tenth_lord} {tl_dgn} in 10H — authority axis (+18)")
    elif tl_h:
        step1_why.append(f"10L {tenth_lord} in {tl_h}H ({tl_dgn or 'neutral'})")
    checklist["step1_10th_house"] = {"tenth_lord": tenth_lord, "house": tl_h, "why": step1_why}
    why.extend(step1_why)

    # ── Step 2: Sun + Saturn drivers ────────────────────────────────────
    step2_why: list[str] = []
    sun_h = _planet_house(planets, "Sun")
    sun_dgn = _planet_dignity(intel, "Sun")
    sat_h = _planet_house(planets, "Saturn")
    sat_dgn = _planet_dignity(intel, "Saturn")

    if sun_h == 10:
        score += 14
        flags.append("sun_digbali_10h")
        step2_why.append("Sun in 10H (Digbali) — authority/manager post (+14)")
    elif sun_h in {10, 11} and _is_strong_dignity(sun_dgn):
        score += 12
        flags.append("sun_strong_10_11")
        step2_why.append(f"Sun {sun_dgn} in {sun_h}H — boss recognition (+12)")

    if sat_h in _KENDRA_TRIKONA and _is_strong_dignity(sat_dgn):
        score += 12
        flags.append("saturn_strong_kendra")
        step2_why.append(f"Saturn {sat_dgn} in {sat_h}H — loyalty/long-term reward (+12)")
    elif sat_h == 10 and _is_strong_dignity(sat_dgn):
        score += 14
        flags.append("saturn_strong_10h")
        step2_why.append(f"Saturn {sat_dgn} in 10H — disciplined rise (+14)")
    elif sat_h in {6, 10, 11}:
        step2_why.append(f"Saturn in {sat_h}H — service axis tone")

    checklist["step2_sun_saturn"] = {"sun_house": sun_h, "saturn_house": sat_h, "why": step2_why}
    why.extend(step2_why)

    # ── Step 3: D10 verify ──────────────────────────────────────────────
    step3_why: list[str] = []
    d10_lagna_strong = False
    if d10:
        tl_d10_h = _planet_house(d10, tenth_lord) if tenth_lord else None
        el_d10_h = _planet_house(d10, eleventh_lord) if eleventh_lord else None
        if tl_d10_h in {10, 11}:
            score += 12
            flags.append("d10_10l_strong")
            step3_why.append(f"D10: 10L in {tl_d10_h}H — professional level shift (+12)")
            d10_lagna_strong = True
        if el_d10_h == 11:
            score += 10
            flags.append("d10_11l_11h")
            step3_why.append("D10: 11L in 11H — sustained gains in dashamsha (+10)")
    checklist["step3_d10"] = {"confirmed": d10_lagna_strong, "why": step3_why}
    why.extend(step3_why)

    # ── Step 4: 6H rivals + 11H hike ──────────────────────────────────
    step4_why: list[str] = []
    if el_h == 11:
        score += 20
        flags.append("11l_in_11h")
        step4_why.append(f"11L {eleventh_lord} in 11H — solid increment potential (+20)")
    elif el_h in _KENDRA_TRIKONA and _is_strong_dignity(el_dgn):
        score += 14
        step4_why.append(f"11L {eleventh_lord} {el_dgn} in {el_h}H — gains support (+14)")
    if el_h == 10:
        score += 16
        step4_why.append("11L in 10H — hike via designation (+16)")

    if sl_h == 6 and _is_strong_dignity(sl_dgn):
        score += 12
        flags.append("6l_strong_6h")
        step4_why.append(f"6L {sixth_lord} strong in 6H — beat office politics (+12)")
    elif sl_h in {10, 11}:
        score += 8
        step4_why.append(f"6L in {sl_h}H — service converts to rise (+8)")

    if tenth_lord and eleventh_lord:
        pts, msgs, f = _lords_mutual_link(planets, tenth_lord, eleventh_lord, "D1")
        score += pts
        step4_why.extend(msgs)
        flags.extend(f)

    jup_h = _planet_house(planets, "Jupiter")
    if jup_h in {10, 11}:
        score += 10
        step4_why.append(f"Jupiter in {jup_h}H — labha expansion (+10)")
    elif jup_h and (10 in _aspect_houses("Jupiter", jup_h) or 11 in _aspect_houses("Jupiter", jup_h)):
        score += 6
        step4_why.append("Jupiter aspects 10H/11H — promotion grace (+6)")

    checklist["step4_6h_11h"] = {
        "sixth_lord": sixth_lord, "sixth_lord_house": sl_h,
        "eleventh_lord": eleventh_lord, "eleventh_lord_house": el_h,
        "why": step4_why,
    }
    why.extend(step4_why)

    # D9 overlay (supporting)
    el_d9_h = _planet_house(d9, eleventh_lord) if eleventh_lord and d9 else None
    tl_d9_h = _planet_house(d9, tenth_lord) if tenth_lord and d9 else None
    if el_d9_h in {1, 4, 5, 9, 10, 11}:
        score += 8
        why.append(f"D9: 11L favourable in {el_d9_h}H (+8)")
    if tl_d9_h in {10, 11}:
        score += 6
        why.append(f"D9: 10L in {tl_d9_h}H (+6)")

    amk = (karakas_d or {}).get("AmK")
    if amk in ("Jupiter", "Sun", "Venus"):
        score += 8
        why.append(f"AmK = {amk} — growth/recognition aligned (+8)")

    if isinstance(kp_assist, dict) and kp_assist.get("score"):
        kp_sc = int(kp_assist.get("score") or 0)
        if kp_sc > 0:
            score += min(kp_sc, 10)
            why.extend((kp_assist.get("why") or [])[:2])
            flags.append("kp_confirms")

    # ── Step 7: Ashtakvarga gate ───────────────────────────────────────
    av_gate = _assess_ashtakvarga_gate(kundli, lagna_si)
    checklist["step7_ashtakvarga"] = av_gate
    if av_gate.get("smooth_promotion") is True:
        score += 6
        why.append("Ashtakvarga 10H+11H ≥28 — smooth promotion path (+6)")
    elif av_gate.get("delay_risk"):
        score -= 4
        why.append("Ashtakvarga <28 on 10H/11H — last-moment delay risk (-4)")
    why.extend((av_gate.get("why") or [])[:2])

    promise_score = min(100, max(0, score))
    if promise_score >= 50:
        level = "high"
    elif promise_score >= 28:
        level = "moderate"
    else:
        level = "low"

    return {
        "fired": True,
        "engine": "promotion_engine_v1",
        "score": min(40, promise_score // 2),
        "promise_score": promise_score,
        "promotion_promise_level": level,
        "why": why,
        "flags": flags,
        "checklist": checklist,
        "tenth_lord": tenth_lord,
        "eleventh_lord": eleventh_lord,
        "sixth_lord": sixth_lord,
        "amk": amk,
        "kp_summary": (kp_assist or {}).get("summary") if isinstance(kp_assist, dict) else None,
        "ashtakvarga_gate": av_gate,
    }


def _fmt_dasha_date(dt: Optional[datetime]) -> Optional[str]:
    if not isinstance(dt, datetime):
        return None
    return dt.strftime("%Y-%m")


_PROMO_WINDOWS_TOP_N = 3


def _promo_window_key(w: dict) -> tuple[str, str, str]:
    return (
        str(w.get("lords") or "").strip(),
        str(w.get("start") or w.get("start_label") or "").strip(),
        str(w.get("end") or w.get("end_label") or "").strip(),
    )


def _promo_window_row(
    *,
    md: Any = None,
    ad: Any = None,
    pd: Any = None,
    lords: Any = None,
    start: Any = None,
    end: Any = None,
    score: Any = None,
    reason: Any = None,
    timing_source: Any = None,
    bcp_aligned: bool = False,
) -> dict:
    lords_s = str(lords or "").strip() or "/".join(x for x in (md, ad, pd) if x)
    return {
        "md": md,
        "ad": ad,
        "pd": pd,
        "lords": lords_s or None,
        "start": start,
        "end": end,
        "score": score,
        "reason": reason,
        "timing_source": timing_source,
        "bcp_aligned": bcp_aligned,
    }


def _merge_promotion_windows_top3(
    ranked: list[dict],
    chain: list[dict],
    core: set[str],
    today: datetime,
    *,
    bcp_ages: Optional[set] = None,
) -> list[dict]:
    """Up to 3 future promotion windows — #1 is PRIMARY (answer)."""
    out: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    bcp_ages = bcp_ages or set()

    def _push(row: dict) -> None:
        if len(out) >= _PROMO_WINDOWS_TOP_N:
            return
        key = _promo_window_key(row)
        if not key[0] or key in seen:
            return
        seen.add(key)
        out.append(row)

    for w in ranked:
        end_raw = w.get("end")
        if isinstance(end_raw, datetime) and end_raw < today:
            continue
        _push(_promo_window_row(
            md=w.get("md"),
            ad=w.get("ad"),
            pd=w.get("pd"),
            lords=w.get("lords"),
            start=w.get("start_label"),
            end=w.get("end_label"),
            score=w.get("score"),
            reason=" · ".join(w.get("detail") or []) if isinstance(w.get("detail"), list) else w.get("detail"),
            timing_source="ranked_window",
            bcp_aligned=bool(bcp_ages),
        ))

    if len(out) < _PROMO_WINDOWS_TOP_N:
        for chunk in chain:
            if chunk.get("end") and chunk["end"] < today:
                continue
            ad = str(chunk.get("ad") or "")
            pd = str(chunk.get("pd") or "")
            if not (ad in core or pd in core or ad in _BENEFIC_PROMO or pd in _BENEFIC_PROMO):
                continue
            sc, det, _ = _score_promo_chunk(
                chunk.get("md", ""), ad, pd, core,
            )
            _push(_promo_window_row(
                md=chunk.get("md"),
                ad=ad,
                pd=pd,
                lords="/".join(x for x in (chunk.get("md"), ad, pd) if x),
                start=_fmt_dasha_date(chunk["start"]),
                end=_fmt_dasha_date(chunk["end"]),
                score=sc,
                reason=" · ".join(det or []) or f"AD/PD watch {ad}/{pd}",
                timing_source="dasha_scan",
                bcp_aligned=bool(bcp_ages),
            ))
            if len(out) >= _PROMO_WINDOWS_TOP_N:
                break

    for i, row in enumerate(out):
        row["rank"] = i + 1
        row["band"] = "PRIMARY" if i == 0 else "BACKUP"
    return out


def _flatten_promotion_dasha_chain(kundli: dict) -> list[dict]:
    """MD·AD·PD flat chain for promotion scan."""
    out: list[dict] = []
    today = datetime.utcnow()
    horizon = today + timedelta(days=365 * _PROMO_SCAN_YEARS)

    for md_row in kundli.get("dashas") or []:
        if not isinstance(md_row, dict):
            continue
        md = str(md_row.get("planet") or md_row.get("lord") or md_row.get("mahadasha") or "").strip()
        if not md:
            continue
        for ad_row in (md_row.get("subDashas") or md_row.get("antardashas") or []):
            if not isinstance(ad_row, dict):
                continue
            ad = str(ad_row.get("planet") or ad_row.get("lord") or ad_row.get("antardasha") or "").strip()
            ad_start = _parse_iso(ad_row.get("startDate") or ad_row.get("start"))
            ad_end = _parse_iso(ad_row.get("endDate") or ad_row.get("end"))
            if not (ad and ad_start and ad_end):
                continue
            if ad_end < today - timedelta(days=30) or ad_start > horizon:
                continue

            pd_list = ad_row.get("subDashas") or ad_row.get("pratyantar_dashas") or []
            if pd_list and isinstance(pd_list, list):
                for pd_row in pd_list:
                    if not isinstance(pd_row, dict):
                        continue
                    pd = str(
                        pd_row.get("planet") or pd_row.get("lord")
                        or pd_row.get("pratyantardasha") or pd_row.get("pratyantar") or ""
                    ).strip()
                    pd_start = _parse_iso(pd_row.get("startDate") or pd_row.get("start"))
                    pd_end = _parse_iso(pd_row.get("endDate") or pd_row.get("end"))
                    if not (pd and pd_start and pd_end) or pd_end < today - timedelta(days=30):
                        continue
                    out.append({
                        "md": md, "ad": ad, "pd": pd,
                        "start": pd_start, "end": pd_end,
                    })
            elif ad in _VIMS_ORDER:
                ad_secs = (ad_end - ad_start).total_seconds()
                if ad_secs <= 0:
                    continue
                total = float(sum(_VIMS_YEARS.values()))
                start_idx = _VIMS_ORDER.index(ad)
                cursor = ad_start
                for k in range(9):
                    pd = _VIMS_ORDER[(start_idx + k) % 9]
                    frac = _VIMS_YEARS[pd] / total
                    pd_end = cursor + timedelta(seconds=ad_secs * frac)
                    if pd_end >= today - timedelta(days=30):
                        out.append({
                            "md": md, "ad": ad, "pd": pd,
                            "start": cursor, "end": pd_end,
                        })
                    cursor = pd_end

    out.sort(key=lambda c: c["start"])
    return out


def _promo_core_set(promise: dict) -> set[str]:
    core: set[str] = set()
    for key in ("tenth_lord", "eleventh_lord", "sixth_lord"):
        v = promise.get(key)
        if v:
            core.add(str(v))
    amk = promise.get("amk")
    if amk:
        core.add(str(amk))
    return core


def _score_promo_chunk(
    md: str,
    ad: str,
    pd: str,
    core: set[str],
) -> tuple[int, list[str], bool]:
    """AD/PD weighted; returns (score, detail, ad_or_pd_core_hit)."""
    score = 0
    detail: list[str] = []
    ad = ad or ""
    pd = pd or ""
    md = md or ""

    if pd in core:
        score += _SCORE_PD_CORE
        detail.append(f"PD {pd} (10L/11L/6L axis) +{_SCORE_PD_CORE}")
    elif pd in _BENEFIC_PROMO:
        score += _SCORE_PD_BENEFIC
        detail.append(f"PD {pd} (benefic trigger) +{_SCORE_PD_BENEFIC}")

    if ad in core:
        score += _SCORE_AD_CORE
        detail.append(f"AD {ad} (10L/11L/6L axis) +{_SCORE_AD_CORE}")
    elif ad in _BENEFIC_PROMO:
        score += _SCORE_AD_BENEFIC
        detail.append(f"AD {ad} (benefic support) +{_SCORE_AD_BENEFIC}")

    if md in core:
        score += _SCORE_MD_CORE
        detail.append(f"MD {md} (background) +{_SCORE_MD_CORE}")

    if ad in core and pd in core:
        score += _SCORE_AD_PD_CONFLUENCE
        detail.append(f"AD+PD core confluence +{_SCORE_AD_PD_CONFLUENCE}")

    ad_pd_core = (ad in core) or (pd in core)
    return score, detail, ad_pd_core


def assess_promotion_timing(
    kundli: dict,
    intel: dict,
    promise: dict,
    *,
    bcp: Optional[dict] = None,
) -> dict:
    """Step 5 — AD/PD-first dasha; skip current if unsupported → next window."""
    level = str(promise.get("promotion_promise_level") or "low")
    deferred_low = level == "low"
    low_message = (
        "Promotion promise weak — pehle performance/build; timing secondary."
        if deferred_low
        else ""
    )

    core = _promo_core_set(promise)
    md, ad, pd = _dasha_lords(kundli)
    current_lords = "/".join(x for x in (md, ad, pd) if x)
    today = datetime.utcnow()

    cur_score, cur_detail, cur_core_hit = _score_promo_chunk(md, ad, pd, core)
    current_supports = cur_core_hit and cur_score >= _MIN_PROMO_CHUNK

    chain = _flatten_promotion_dasha_chain(kundli)
    ranked: list[dict] = []
    for chunk in chain:
        sc, det, core_hit = _score_promo_chunk(
            chunk.get("md", ""), chunk.get("ad", ""), chunk.get("pd", ""), core,
        )
        if not core_hit or sc < _MIN_PROMO_CHUNK:
            continue
        ranked.append({
            **chunk,
            "score": sc,
            "detail": det,
            "lords": "/".join(x for x in (chunk.get("md"), chunk.get("ad"), chunk.get("pd")) if x),
            "start_label": _fmt_dasha_date(chunk["start"]),
            "end_label": _fmt_dasha_date(chunk["end"]),
        })

    ranked.sort(key=lambda w: (-w["score"], w["start"]))

    recommended: Optional[dict] = None
    timing_source = "none"
    skip_current_reason = ""

    if current_supports:
        for w in ranked:
            if w["start"] <= today <= w["end"]:
                recommended = w
                timing_source = "current_dasha"
                break
        if recommended is None:
            recommended = {
                "md": md, "ad": ad, "pd": pd,
                "start": today, "end": today,
                "score": cur_score,
                "detail": cur_detail,
                "lords": current_lords,
                "start_label": "current",
                "end_label": "current",
            }
            timing_source = "current_dasha"
    else:
        skip_current_reason = (
            f"Current dasha {current_lords} promotion ko AD/PD level par support nahi karti "
            f"(score {cur_score}, need AD/PD = 10L/11L/6L)."
        )
        for w in ranked:
            if w["end"] < today:
                continue
            if w["start"] <= today <= w["end"] and current_supports:
                continue
            recommended = w
            timing_source = "next_dasha"
            break

    if not recommended:
        for w in ranked:
            if w.get("end") and w["end"] >= today:
                recommended = w
                timing_source = "next_dasha_candidate"
                break

    if not recommended:
        for chunk in chain:
            if chunk.get("end") and chunk["end"] < today:
                continue
            ad = str(chunk.get("ad") or "")
            pd = str(chunk.get("pd") or "")
            if not (ad in core or pd in core or ad in _BENEFIC_PROMO or pd in _BENEFIC_PROMO):
                continue
            sc, det, _ = _score_promo_chunk(
                chunk.get("md", ""), ad, pd, core,
            )
            recommended = {
                **chunk,
                "score": sc,
                "detail": det,
                "lords": "/".join(
                    x for x in (chunk.get("md"), chunk.get("ad"), chunk.get("pd")) if x
                ),
                "start_label": _fmt_dasha_date(chunk["start"]),
                "end_label": _fmt_dasha_date(chunk["end"]),
            }
            timing_source = "upcoming_watch"
            break

    if not recommended:
        seen_ad: set[str] = set()
        for chunk in chain:
            if chunk.get("end") and chunk["end"] < today:
                continue
            ad = str(chunk.get("ad") or "")
            if not ad or ad not in core or ad in seen_ad:
                continue
            seen_ad.add(ad)
            sc, det, _ = _score_promo_chunk(
                chunk.get("md", ""), ad, str(chunk.get("pd") or ""), core,
            )
            recommended = {
                **chunk,
                "score": sc,
                "detail": det or [f"Next career AD {ad} (10L/11L/6L/AmK axis)"],
                "lords": "/".join(
                    x for x in (chunk.get("md"), ad, chunk.get("pd")) if x
                ),
                "start_label": _fmt_dasha_date(chunk["start"]),
                "end_label": _fmt_dasha_date(chunk["end"]),
            }
            timing_source = "next_career_ad"
            break

    bcp_ages = set((bcp or {}).get("future_priority_ages") or [])
    windows_out = _merge_promotion_windows_top3(ranked, chain, core, today, bcp_ages=bcp_ages)

    step5 = {
        "status": "ready",
        "current_lords": current_lords,
        "current_score": cur_score,
        "current_supports_promotion": current_supports,
        "ad_pd_priority": True,
        "core_lords": sorted(core),
        "skip_current_reason": skip_current_reason or None,
        "timing_source": timing_source,
        "recommended_window": None,
    }

    if windows_out:
        w0 = windows_out[0]
        step5["recommended_window"] = {
            "lords": w0.get("lords"),
            "md": w0.get("md"),
            "ad": w0.get("ad"),
            "pd": w0.get("pd"),
            "start": w0.get("start"),
            "end": w0.get("end"),
            "score": w0.get("score"),
            "reason": w0.get("reason"),
            "timing_source": w0.get("timing_source") or timing_source,
        }
    elif recommended:
        step5["recommended_window"] = {
            "lords": recommended.get("lords"),
            "md": recommended.get("md"),
            "ad": recommended.get("ad"),
            "pd": recommended.get("pd"),
            "start": recommended.get("start_label"),
            "end": recommended.get("end_label"),
            "score": recommended.get("score"),
            "reason": " · ".join(recommended.get("detail") or []),
            "timing_source": timing_source,
        }

    directive = ""
    if timing_source == "current_dasha" and recommended:
        directive = (
            f"CURRENT dasha support hai — AD/PD focus: {recommended.get('ad')}/{recommended.get('pd')} "
            f"({recommended.get('start_label')}→{recommended.get('end_label')})."
        )
    elif timing_source == "next_dasha" and recommended:
        directive = (
            f"Current dasha support NAHI — NEXT promotion window: "
            f"{recommended.get('lords')} ({recommended.get('start_label')}→{recommended.get('end_label')}). "
            f"Isi period ko timing batao; abhi mat bolo."
        )
    elif timing_source in ("next_dasha_candidate", "upcoming_watch", "next_career_ad") and recommended:
        directive = (
            f"Promotion timeline (candidate — AD/PD watch): "
            f"{recommended.get('lords')} ({recommended.get('start_label')}→{recommended.get('end_label')}). "
            f"Current weak — is upcoming window ko primary timing batao."
        )
    elif skip_current_reason:
        directive = skip_current_reason + " Abhi koi strong future AD/PD window scan mein nahi mili."
    if windows_out:
        primary = windows_out[0]
        directive = (
            f"PRIMARY promotion window (#1 ONLY — user ko yahi batao): "
            f"{primary.get('lords')} ({primary.get('start')}→{primary.get('end')})."
        )
        if len(windows_out) > 1:
            backup_lines = [
                f"#{w.get('rank')}: {w.get('lords')} {w.get('start')}→{w.get('end')}"
                for w in windows_out[1:]
            ]
            directive += (
                " Backup windows (admin reference — user ko mat bolo unless puche): "
                + " | ".join(backup_lines)
            )
    if deferred_low and low_message:
        directive = (directive + " " if directive else "") + low_message

    status = "ready" if recommended else "no_window_found"
    if deferred_low and recommended:
        status = "deferred_low_promise"

    return {
        "status": status,
        "message": low_message or None,
        "deferred_low_promise": deferred_low,
        "current_lords": current_lords,
        "active_now": current_supports,
        "current_supports": current_supports,
        "timing_source": timing_source,
        "recommended_window": step5.get("recommended_window"),
        "windows": windows_out,
        "dasha_targets": sorted(core | set(_BENEFIC_PROMO)),
        "bcp_next_ages": list(bcp_ages)[:6] if bcp_ages else [],
        "step5_dasha": step5,
        "llm_directive": directive,
    }


def assess_promotion(
    kundli: dict,
    intel: dict,
    *,
    lagna_si: int = -1,
    karakas_d: Optional[dict] = None,
    kp: Optional[dict] = None,
    kp_assist_fn: Any = None,
    user_age: Optional[int] = None,
) -> dict:
    """Full promotion engine: classical checklist → BCP parallel → AD/PD dasha."""
    kp_assist = None
    if callable(kp_assist_fn) and kp:
        try:
            kp_assist = kp_assist_fn(kp)
        except Exception:
            kp_assist = None

    bcp_block = {}
    if lagna_si >= 0:
        bcp_block = run_promotion_bcp_parallel(kundli, lagna_si, user_age=user_age)

    promise = assess_promotion_promise(
        kundli, intel, lagna_si=lagna_si,
        karakas_d=karakas_d, kp_assist=kp_assist,
    )

    timing = assess_promotion_timing(
        kundli, intel, promise,
        bcp=bcp_block.get("bcp_promotion_ages") if bcp_block else None,
    )

    return {
        "step1_bcp": bcp_block,
        "bcp_parallel": bcp_block,
        "promise": promise,
        "timing": timing,
        "checklist": promise.get("checklist") or {},
        "promotion_promise_level": promise.get("promotion_promise_level"),
        "promise_score": promise.get("promise_score"),
        "verdict_label": _verdict_label(promise, timing),
        "strategy": _strategy(promise, timing, bcp_block),
    }


def _verdict_label(promise: dict, timing: dict) -> str:
    level = promise.get("promotion_promise_level")
    if level == "high" and timing.get("current_supports"):
        return "PROMOTION_STRONG_NOW"
    if level == "high" and timing.get("timing_source") == "next_dasha":
        return "PROMOTION_STRONG_UPCOMING"
    if level == "high":
        return "PROMOTION_STRONG"
    if level == "moderate":
        return "PROMOTION_MODERATE"
    return "PROMOTION_WEAK"


def _strategy(promise: dict, timing: dict, bcp_block: dict) -> str:
    level = promise.get("promotion_promise_level")
    if level == "low":
        return (
            "Chart mein promotion signature kamzor — pehle delivery + visibility; "
            "timing abhi secondary."
        )

    if timing.get("llm_directive"):
        base = timing["llm_directive"]
    else:
        base = "Moderate promotion promise — right AD/PD window par focus karein."

    av = (promise.get("ashtakvarga_gate") or {})
    if av.get("delay_risk"):
        base += " Ashtakvarga <28 — last moment delay possible."

    nxt_bcp = bcp_block.get("next_activation_age")
    if nxt_bcp:
        base += f" (BCP background age {nxt_bcp} — dasha align check.)"

    return base


def format_promotion_block_for_prompt(result: dict, question: str = "") -> str:
    """LOCKED narrator block — classical steps first, BCP last."""
    if not isinstance(result, dict):
        return ""
    promise = result.get("promise") if isinstance(result.get("promise"), dict) else result
    timing = result.get("timing") if isinstance(result.get("timing"), dict) else {}
    bcp = result.get("bcp_parallel") or result.get("step1_bcp") or {}
    checklist = promise.get("checklist") or {}

    lines = [
        "=== PROMOTION ENGINE v1 (LOCKED) ===",
        f"Promise: {promise.get('promotion_promise_level')} ({promise.get('promise_score')}/100)",
        f"Verdict: {result.get('verdict_label') or _verdict_label(promise, timing)}",
        "",
        "▸ CLASSICAL CHECKLIST (serial):",
    ]

    for step_key, label in (
        ("step1_10th_house", "Step1 — D1 10H/10L"),
        ("step2_sun_saturn", "Step2 — Sun + Saturn"),
        ("step3_d10", "Step3 — D10 verify"),
        ("step4_6h_11h", "Step4 — 6H rivals + 11H hike"),
    ):
        block = checklist.get(step_key) or {}
        for w in (block.get("why") or [])[:3]:
            lines.append(f"  {label}: {w}")

    step5 = timing.get("step5_dasha") or {}
    lines.append("  Step5 — Dasha (AD/PD priority):")
    lines.append(f"    Current: {step5.get('current_lords') or timing.get('current_lords')}")
    lines.append(
        f"    Current supports promotion: {step5.get('current_supports_promotion', timing.get('current_supports'))}"
    )
    rec = timing.get("recommended_window") or step5.get("recommended_window")
    if rec:
        lines.append(
            f"    PRIMARY TIMING (#1 — answer yahi): "
            f"{rec.get('lords')} {rec.get('start')}→{rec.get('end')}"
        )
        if rec.get("reason"):
            lines.append(f"    Why: {rec['reason']}")
    win_list = timing.get("windows") if isinstance(timing.get("windows"), list) else []
    for w in win_list[1:3]:
        if not isinstance(w, dict):
            continue
        lines.append(
            f"    Backup #{w.get('rank', '?')}: {w.get('lords')} "
            f"{w.get('start')}→{w.get('end')} (admin only — user ko mat bolo)"
        )
    if step5.get("skip_current_reason"):
        lines.append(f"    ⚠ {step5['skip_current_reason']}")

    av = checklist.get("step7_ashtakvarga") or promise.get("ashtakvarga_gate") or {}
    lines.append("  Step7 — Ashtakvarga:")
    for w in (av.get("why") or [])[:2]:
        lines.append(f"    {w}")

    if bcp:
        lines.append("")
        lines.append("▸ BCP (parallel — dasha boost only, lead narrative mat banao):")
        lines.append(
            f"  11L@{bcp.get('eleventh_lord_house')}H · 10L@{bcp.get('tenth_lord_house')}H"
        )
        pri = bcp.get("future_priority_ages") or []
        if pri:
            lines.append(f"  Priority ages: {pri[:6]}")

    lines.append("")
    if timing.get("llm_directive"):
        lines.append(f"▸ TIMING DIRECTIVE: {timing['llm_directive']}")
    lines.append(f"Strategy: {result.get('strategy') or _strategy(promise, timing, bcp)}")
    lines.append("GUARD: Promotion NEVER guaranteed — performance + org politics matter.")
    lines.append(
        "RULE: Agar current dasha support NAHI → sirf NEXT window batao; abhi mat bolo."
    )
    try:
        from event_timing._shared.timing_window_pick import locked_window_instruction

        lock = locked_window_instruction(result, question)
        if lock:
            lines.append(lock)
    except Exception:
        pass
    return "\n".join(lines)

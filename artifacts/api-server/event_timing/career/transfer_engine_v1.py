"""Transfer engine v1 (lean) — 3H/12H/10H + AD/PD dasha + 3L+12L BCP parallel.

Modes: timing | general
Timing rule: current AD/PD transfer support na ho → next supportive window only.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Optional

from event_timing.career.bcp_transfer_ages import (
    compute_bcp_transfer_ages,
    format_bcp_transfer_age_list,
)
from event_timing.career.govt_job_engine_v1 import (
    _dasha_lords,
    _divisional_planets,
    _house_lord,
    _parse_iso,
    _planet_house,
)

_MOVE_HOUSES = frozenset({3, 9, 10, 12})
_AV_SMOOTH_MIN = 28
_TRANSFER_SCAN_YEARS = 8
_SCORE_PD = 9
_SCORE_AD = 7
_SCORE_MD = 2
_SCORE_CONFLUENCE = 4
_MIN_CHUNK = 6

_VIMS_ORDER = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]
_VIMS_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

_TIMING_RE = re.compile(
    r"(?i)\b(kab|when|kitne|timing|posting\s*kab|transfer\s*kab|milegi|milega|"
    r"kab\s*ho|kab\s*hogi|kab\s*hoga)\b",
)


def detect_transfer_mode(question: str) -> str:
    return "timing" if _TIMING_RE.search(question or "") else "general"


def run_transfer_bcp_parallel(
    kundli: dict,
    lagna_si: int,
    *,
    user_age: Optional[int] = None,
) -> dict:
    bcp = compute_bcp_transfer_ages(kundli, lagna_si, user_age=user_age)
    d1 = bcp.get("d1_bcp") or {}
    areas: list[dict] = []
    for src in bcp.get("sources") or []:
        kind = str(src.get("source") or "")
        role = "3L" if kind.startswith("3") else "12L"
        typ = "placement" if kind.endswith("_placement") else ("dual_sign" if "dual" in kind else "aspect")
        if typ == "placement":
            areas.append({
                "lord": src.get("lord"), "role": role, "type": typ,
                "house": src.get("house"), "ages": src.get("ages") or [],
            })
        else:
            for entry in src.get("houses") or []:
                areas.append({
                    "lord": src.get("lord"), "role": role, "type": typ,
                    "house": entry.get("house"), "ages": entry.get("ages") or [],
                })
    return {
        "bcp_parallel": True,
        "third_lord": bcp.get("third_lord"),
        "third_lord_house": bcp.get("third_lord_house"),
        "twelfth_lord": bcp.get("twelfth_lord"),
        "twelfth_lord_house": bcp.get("twelfth_lord_house"),
        "transfer_areas": areas,
        "bcp_transfer_ages": bcp,
        "bcp_age_list": format_bcp_transfer_age_list(d1),
        "all_transfer_ages": bcp.get("all_transfer_ages") or [],
        "future_priority_ages": bcp.get("future_priority_ages") or [],
        "next_activation_age": bcp.get("next_activation_age"),
        "aspect_houses_3l": bcp.get("aspect_houses_3l"),
        "aspect_houses_12l": bcp.get("aspect_houses_12l"),
    }


def _assess_ashtakvarga_transfer(kundli: dict, lagna_si: int) -> dict:
    out: dict = {"third_house_sav": None, "tenth_house_sav": None, "smooth": None, "why": []}
    if lagna_si < 0:
        return out
    try:
        from ashtakavarga import compute_ashtakavarga  # type: ignore
        av = compute_ashtakavarga(kundli.get("planets") or [], lagna_si) or {}
    except Exception:
        out["why"].append("Ashtakvarga unavailable")
        return out
    sav = av.get("sav") or av.get("SAV")
    if not isinstance(sav, list):
        return out
    si3 = (lagna_si + 2) % 12
    si10 = (lagna_si + 9) % 12
    s3, s10 = sav[si3], sav[si10]
    out["third_house_sav"], out["tenth_house_sav"] = s3, s10
    if isinstance(s3, int):
        out["why"].append(
            f"3H SAV={s3} — {'smooth move' if s3 >= _AV_SMOOTH_MIN else 'relocation friction'}"
        )
    if isinstance(s10, int):
        out["why"].append(
            f"10H SAV={s10} — {'posting lands well' if s10 >= _AV_SMOOTH_MIN else 'posting delay risk'}"
        )
    out["smooth"] = (
        isinstance(s3, int) and s3 >= _AV_SMOOTH_MIN
        and isinstance(s10, int) and s10 >= _AV_SMOOTH_MIN
    )
    return out


def assess_transfer_likelihood(
    kundli: dict,
    intel: dict,
    *,
    lagna_si: int = -1,
    saturn_t: Optional[dict] = None,
    kp_assist: Optional[dict] = None,
) -> dict:
    planets = kundli.get("planets") or []
    d10 = _divisional_planets(kundli, "D10")
    score = 0
    why: list[str] = []
    flags: list[str] = []
    checklist: dict[str, dict] = {}

    third_lord = _house_lord(intel, 3)
    twelfth_lord = _house_lord(intel, 12)
    tenth_lord = _house_lord(intel, 10)

    tl3_h = _planet_house(planets, third_lord) if third_lord else None
    tl12_h = _planet_house(planets, twelfth_lord) if twelfth_lord else None
    tl10_h = _planet_house(planets, tenth_lord) if tenth_lord else None

    s1: list[str] = []
    if tl3_h in _MOVE_HOUSES:
        score += 12
        s1.append(f"3L {third_lord} in {tl3_h}H — move initiation active (+12)")
        flags.append("3l_move_house")
    checklist["step1_3rd_house"] = {"third_lord": third_lord, "house": tl3_h, "why": s1}
    why.extend(s1)

    s2: list[str] = []
    if tl12_h in _MOVE_HOUSES:
        score += 10
        s2.append(f"12L {twelfth_lord} in {tl12_h}H — place-change karma (+10)")
        flags.append("12l_relocation")
    checklist["step2_12th_house"] = {"twelfth_lord": twelfth_lord, "house": tl12_h, "why": s2}
    why.extend(s2)

    s3: list[str] = []
    if tl10_h in {10, 11, 3, 9}:
        score += 8
        s3.append(f"10L {tenth_lord} in {tl10_h}H — posting axis linked (+8)")
    checklist["step3_10th_house"] = {"tenth_lord": tenth_lord, "house": tl10_h, "why": s3}
    why.extend(s3)

    s4: list[str] = []
    rahu_h = _planet_house(planets, "Rahu")
    if rahu_h in {3, 12, 10}:
        score += 6
        s4.append(f"Rahu in {rahu_h}H — sudden posting axis (+6)")
        flags.append("rahu_move")
    if isinstance(saturn_t, dict) and (saturn_t.get("on_tenth") or saturn_t.get("aspecting_tenth")):
        score += 5
        s4.append("Saturn on/aspecting 10H — bureaucratic posting cycle (+5)")
    checklist["step4_rahu_saturn"] = {"why": s4}
    why.extend(s4)

    if d10 and third_lord:
        tl3_d10 = _planet_house(d10, third_lord)
        if tl3_d10 in _MOVE_HOUSES:
            score += 6
            why.append(f"D10: 3L in {tl3_d10}H — dashamsha confirms move (+6)")

    if isinstance(kp_assist, dict) and kp_assist.get("score"):
        score += int(kp_assist.get("score") or 0)
        why.extend((kp_assist.get("why") or [])[:2])

    av = _assess_ashtakvarga_transfer(kundli, lagna_si)
    checklist["ashtakvarga"] = av
    if av.get("smooth"):
        score += 4
    elif av.get("third_house_sav") is not None or av.get("tenth_house_sav") is not None:
        score -= 3
    why.extend((av.get("why") or [])[:2])

    score = max(0, min(100, score))
    if score >= 28:
        verdict = "STRONG_TRANSFER_LIKELY"
        level = "high"
    elif score >= 16:
        verdict = "moderate_chance"
        level = "moderate"
    elif score >= 6:
        verdict = "low_chance"
        level = "low"
    else:
        verdict = "stay_put"
        level = "low"

    return {
        "fired": True,
        "engine": "transfer_engine_v1",
        "transfer_likelihood": level,
        "transfer_verdict": verdict,
        "score": score,
        "why": why,
        "flags": flags,
        "checklist": checklist,
        "third_lord": third_lord,
        "twelfth_lord": twelfth_lord,
        "tenth_lord": tenth_lord,
        "ashtakvarga_gate": av,
        "kp_summary": (kp_assist or {}).get("summary") if isinstance(kp_assist, dict) else None,
    }


def _transfer_core_set(likelihood: dict) -> set[str]:
    core: set[str] = set()
    for key in ("third_lord", "twelfth_lord", "tenth_lord"):
        v = likelihood.get(key)
        if v:
            core.add(str(v))
    return core


def _fmt_dasha_date(dt: Optional[datetime]) -> Optional[str]:
    return dt.strftime("%Y-%m") if isinstance(dt, datetime) else None


def _flatten_transfer_dasha_chain(kundli: dict) -> list[dict]:
    out: list[dict] = []
    today = datetime.utcnow()
    horizon = today + timedelta(days=365 * _TRANSFER_SCAN_YEARS)
    for md_row in kundli.get("dashas") or []:
        if not isinstance(md_row, dict):
            continue
        md = str(md_row.get("planet") or md_row.get("lord") or md_row.get("mahadasha") or "").strip()
        for ad_row in (md_row.get("subDashas") or md_row.get("antardashas") or []):
            if not isinstance(ad_row, dict):
                continue
            ad = str(ad_row.get("planet") or ad_row.get("lord") or ad_row.get("antardasha") or "").strip()
            ad_start = _parse_iso(ad_row.get("startDate") or ad_row.get("start"))
            ad_end = _parse_iso(ad_row.get("endDate") or ad_row.get("end"))
            if not (ad and ad_start and ad_end) or ad_end < today - timedelta(days=30) or ad_start > horizon:
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
                    if pd and pd_start and pd_end and pd_end >= today - timedelta(days=30):
                        out.append({"md": md, "ad": ad, "pd": pd, "start": pd_start, "end": pd_end})
            elif ad in _VIMS_ORDER:
                ad_secs = (ad_end - ad_start).total_seconds()
                if ad_secs <= 0:
                    continue
                total = float(sum(_VIMS_YEARS.values()))
                cursor = ad_start
                for k in range(9):
                    pd = _VIMS_ORDER[(_VIMS_ORDER.index(ad) + k) % 9]
                    pd_end = cursor + timedelta(seconds=ad_secs * (_VIMS_YEARS[pd] / total))
                    if pd_end >= today - timedelta(days=30):
                        out.append({"md": md, "ad": ad, "pd": pd, "start": cursor, "end": pd_end})
                    cursor = pd_end
    out.sort(key=lambda c: c["start"])
    return out


def _score_transfer_chunk(md: str, ad: str, pd: str, core: set[str]) -> tuple[int, list[str], bool]:
    score = 0
    detail: list[str] = []
    ad, pd, md = ad or "", pd or "", md or ""
    if pd in core:
        score += _SCORE_PD
        detail.append(f"PD {pd} (3L/12L/10L move) +{_SCORE_PD}")
    if ad in core:
        score += _SCORE_AD
        detail.append(f"AD {ad} (transfer lord) +{_SCORE_AD}")
    if ad in core and pd in core:
        score += _SCORE_CONFLUENCE
        detail.append(f"AD+PD transfer confluence +{_SCORE_CONFLUENCE}")
    if md in core:
        score += _SCORE_MD
        detail.append(f"MD {md} (background) +{_SCORE_MD}")
    hit = (ad in core) or (pd in core)
    return score, detail, hit


def assess_transfer_timing(
    kundli: dict,
    likelihood: dict,
    *,
    bcp: Optional[dict] = None,
) -> dict:
    core = _transfer_core_set(likelihood)
    md, ad, pd = _dasha_lords(kundli)
    current_lords = "/".join(x for x in (md, ad, pd) if x)
    today = datetime.utcnow()

    cur_score, cur_detail, cur_hit = _score_transfer_chunk(md, ad, pd, core)
    current_supports = cur_hit and cur_score >= _MIN_CHUNK

    ranked: list[dict] = []
    for chunk in _flatten_transfer_dasha_chain(kundli):
        sc, det, hit = _score_transfer_chunk(
            chunk.get("md", ""), chunk.get("ad", ""), chunk.get("pd", ""), core,
        )
        if not hit or sc < _MIN_CHUNK:
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
    skip_reason = ""

    if current_supports:
        for w in ranked:
            if w["start"] <= today <= w["end"]:
                recommended = w
                timing_source = "current_dasha"
                break
        if recommended is None:
            recommended = {
                "md": md, "ad": ad, "pd": pd,
                "score": cur_score, "detail": cur_detail, "lords": current_lords,
                "start_label": "current", "end_label": "current",
            }
            timing_source = "current_dasha"
    else:
        skip_reason = (
            f"Current dasha {current_lords} transfer ko AD/PD level par support nahi karti "
            f"(score {cur_score})."
        )
        for w in ranked:
            if w["end"] < today:
                continue
            recommended = w
            timing_source = "next_dasha"
            break

    directive = ""
    if timing_source == "current_dasha" and recommended:
        directive = (
            f"CURRENT transfer window — AD/PD {recommended.get('ad')}/{recommended.get('pd')} "
            f"({recommended.get('start_label')}→{recommended.get('end_label')})."
        )
    elif timing_source == "next_dasha" and recommended:
        directive = (
            f"Abhi transfer push mat karo — NEXT window: {recommended.get('lords')} "
            f"({recommended.get('start_label')}→{recommended.get('end_label')})."
        )
    elif skip_reason:
        directive = skip_reason + " Strong future transfer AD/PD scan mein nahi mili."

    return {
        "status": "ready" if recommended else "no_window_found",
        "current_lords": current_lords,
        "current_supports_transfer": current_supports,
        "timing_source": timing_source,
        "recommended_window": {
            "lords": recommended.get("lords"),
            "md": recommended.get("md"),
            "ad": recommended.get("ad"),
            "pd": recommended.get("pd"),
            "start": recommended.get("start_label"),
            "end": recommended.get("end_label"),
            "score": recommended.get("score"),
            "reason": " · ".join(recommended.get("detail") or []),
            "timing_source": timing_source,
        } if recommended else None,
        "windows": [{
            "lords": w.get("lords"), "start": w.get("start_label"), "end": w.get("end_label"),
            "score": w.get("score"), "reason": " · ".join(w.get("detail") or []),
        } for w in ranked[:4]],
        "transfer_core_lords": sorted(core),
        "bcp_next_ages": list((bcp or {}).get("future_priority_ages") or [])[:5],
        "llm_directive": directive,
    }


def assess_transfer(
    kundli: dict,
    intel: dict,
    *,
    question: str = "",
    lagna_si: int = -1,
    saturn_t: Optional[dict] = None,
    kp: Optional[dict] = None,
    kp_assist_fn: Any = None,
    user_age: Optional[int] = None,
) -> dict:
    mode = detect_transfer_mode(question)
    kp_assist = None
    if callable(kp_assist_fn) and kp:
        try:
            kp_assist = kp_assist_fn(kp)
        except Exception:
            pass

    bcp_block = run_transfer_bcp_parallel(kundli, lagna_si, user_age=user_age) if lagna_si >= 0 else {}
    likelihood = assess_transfer_likelihood(
        kundli, intel, lagna_si=lagna_si, saturn_t=saturn_t, kp_assist=kp_assist,
    )
    timing = assess_transfer_timing(
        kundli, likelihood,
        bcp=bcp_block.get("bcp_transfer_ages") if bcp_block else None,
    )

    return {
        "question_mode": mode,
        "bcp_parallel": bcp_block,
        "likelihood": likelihood,
        "timing": timing,
        "checklist": likelihood.get("checklist") or {},
        "transfer_verdict": likelihood.get("transfer_verdict"),
        "transfer_likelihood": likelihood.get("transfer_likelihood"),
        "verdict_label": _verdict_label(likelihood, timing),
        "strategy": _strategy(likelihood, timing, mode, bcp_block),
    }


def _verdict_label(likelihood: dict, timing: dict) -> str:
    v = likelihood.get("transfer_verdict")
    if v == "stay_put":
        return "TRANSFER_STAY_PUT"
    if timing.get("current_supports_transfer"):
        return "TRANSFER_WINDOW_OPEN"
    if timing.get("timing_source") == "next_dasha":
        return "TRANSFER_NEXT_WINDOW"
    if v == "STRONG_TRANSFER_LIKELY":
        return "TRANSFER_LIKELY_WAIT_CYCLE"
    return "TRANSFER_MODERATE"


def _strategy(likelihood: dict, timing: dict, mode: str, bcp: dict) -> str:
    parts: list[str] = []
    v = likelihood.get("transfer_verdict")
    if v == "stay_put":
        parts.append("Abhi transfer-request push mat karo — current posting consolidate karo.")
    elif v == "STRONG_TRANSFER_LIKELY":
        parts.append("Transfer signals strong — HR ko formal request + documents ready rakho.")
    elif v == "moderate_chance":
        parts.append("Mixed signals — 6-12 mahine performance + networking, phir request.")

    if mode == "timing" and timing.get("llm_directive"):
        parts.append(timing["llm_directive"])
    elif not timing.get("current_supports_transfer") and mode == "general":
        parts.append("Dasha abhi transfer support kam — timing puche to next window dekho.")

    nxt = bcp.get("next_activation_age")
    if nxt:
        parts.append(f"(BCP background move age {nxt}.)")
    return " ".join(parts) if parts else "Mixed — patience + formal process follow karein."


def format_transfer_block_for_prompt(result: dict, question: str = "") -> str:
    if not isinstance(result, dict):
        return ""
    lik = result.get("likelihood") if isinstance(result.get("likelihood"), dict) else {}
    timing = result.get("timing") if isinstance(result.get("timing"), dict) else {}
    bcp = result.get("bcp_parallel") or {}
    checklist = lik.get("checklist") or {}
    mode = result.get("question_mode") or "general"

    lines = [
        "=== TRANSFER ENGINE v1 (LOCKED — lean) ===",
        f"Mode: {mode}",
        f"Likelihood: {lik.get('transfer_verdict')} (score {lik.get('score')})",
        f"Verdict: {result.get('verdict_label') or _verdict_label(lik, timing)}",
        "",
        "▸ CLASSICAL (4 steps):",
    ]
    for key, label in (
        ("step1_3rd_house", "3H move"),
        ("step2_12th_house", "12H place-change"),
        ("step3_10th_house", "10H posting"),
        ("step4_rahu_saturn", "Rahu/Saturn"),
    ):
        for w in (checklist.get(key) or {}).get("why") or []:
            lines.append(f"  {label}: {w}")
    av = checklist.get("ashtakvarga") or lik.get("ashtakvarga_gate") or {}
    for w in (av.get("why") or [])[:2]:
        lines.append(f"  AV: {w}")

    if mode == "timing" or timing.get("llm_directive"):
        lines.append("  Dasha (AD/PD 3L/12L/10L priority):")
        lines.append(f"    Current: {timing.get('current_lords')} · supports={timing.get('current_supports_transfer')}")
        rec = timing.get("recommended_window")
        if rec:
            lines.append(
                f"    WINDOW ({rec.get('timing_source', timing.get('timing_source'))}): "
                f"{rec.get('lords')} {rec.get('start')}→{rec.get('end')}"
            )

    if bcp:
        lines.append("")
        lines.append("▸ BCP parallel (3L+12L — background only):")
        lines.append(f"  3L@{bcp.get('third_lord_house')}H · 12L@{bcp.get('twelfth_lord_house')}H")

    lines.append("")
    if timing.get("llm_directive"):
        lines.append(f"▸ TIMING: {timing['llm_directive']}")
    lines.append(f"Strategy: {result.get('strategy') or _strategy(lik, timing, mode, bcp)}")
    lines.append("GUARD: no pakka transfer, no exact city. Forced posting → adapt tone.")
    lines.append("RULE: current dasha NAHI support → sirf NEXT AD/PD window.")
    return "\n".join(lines)

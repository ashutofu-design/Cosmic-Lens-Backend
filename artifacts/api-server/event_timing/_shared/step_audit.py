"""Universal timing step_audit + timing_audit — dasha-first admin pipeline for all domains."""
from __future__ import annotations

from typing import Any

from event_timing.domain_specs import get_domain_spec

TIMING_STEP_ORDER: tuple[str, ...] = (
    "step0",
    "step1",
    "step2",
    "step3",
    "step4",
    "step5",
    "step6",
    "step7",
    "step8",
)

DOMAIN_ENGINE_IDS: dict[str, str] = {
    "travel": "travel_timing_v1",
    "finance": "finance_timing_v1",
    "health": "health_timing_v1",
    "children": "children_timing_v1",
    "love": "love_timing_v1",
    "education": "education_timing_v1",
    "foreign_education": "foreign_education_timing_v1",
    "property": "property_timing_v1",
    "litigation": "litigation_timing_v1",
    "career": "career_timing_v1",
    "marriage": "marriage_timing_m17",
    "spiritual": "spiritual_timing_v1",
    "fame": "fame_timing_v1",
    "network": "network_timing_v1",
    "universal": "universal_timing_v1",
}

_RANKED_KEYS = (
    "top_planets",
    "top_travel_planets",
    "top_finance_planets",
    "top_health_planets",
    "top_child_planets",
)


def engine_id_for_domain(domain: str) -> str:
    return DOMAIN_ENGINE_IDS.get(domain, f"{domain}_timing_v1")


def slice_for_domain(domain: str) -> str:
    return engine_id_for_domain(domain)


def _lords_from_window(w: dict | None) -> str:
    if not isinstance(w, dict):
        return ""
    parts = [str(x) for x in (w.get("md"), w.get("ad"), w.get("pd")) if x]
    return "/".join(parts)


def _window_range(w: dict | None) -> str:
    if not isinstance(w, dict):
        return ""
    start = w.get("start_iso") or w.get("start") or ""
    end = w.get("end_iso") or w.get("end") or ""
    if start and end:
        return f"{start}→{end}"
    return str(start or end or "")


def _extract_ranked(result: dict) -> list[dict]:
    for key in _RANKED_KEYS:
        rows = result.get(key)
        if isinstance(rows, list) and rows:
            return [r for r in rows if isinstance(r, dict)]
    return []


def _factors_step(factors: list[str], step: str) -> list[str]:
    prefix = step.upper()
    return [f for f in factors if f.upper().startswith(prefix)]


def _divisional_summary(result: dict, factors: list[str]) -> str:
    bits: list[str] = []
    for tag in ("D9", "D4", "D7", "D10", "D24", "D30"):
        hits = [f for f in factors if tag in f.upper()]
        if hits:
            bits.append(f"{tag}: {hits[0][:80]}")
    breakdown = result.get("weighted_breakdown")
    if isinstance(breakdown, dict) and breakdown:
        sample = next(iter(breakdown.values()), {})
        if isinstance(sample, dict):
            for k in ("d9", "d4", "d7", "d10"):
                if sample.get(k) is not None:
                    bits.append(f"{k.upper()} layer present")
    d7 = result.get("d7_picture")
    if isinstance(d7, dict) and d7:
        bits.append("D7 progeny verify")
    return " · ".join(bits[:4]) or "divisional scan"


def _transit_detail(result: dict, factors: list[str]) -> tuple[list[str], str]:
    why: list[str] = _factors_step(factors, "STEP6")[:4]
    dt = result.get("double_transit") if isinstance(result.get("double_transit"), dict) else {}
    if dt.get("verdict"):
        why.append(f"double-transit {dt.get('verdict')} active={dt.get('active')}")
    transits = result.get("transits") if isinstance(result.get("transits"), dict) else {}
    for t in transits.get("active_triggers") or []:
        if isinstance(t, (list, tuple)) and t:
            why.append(str(t[0])[:100])
        elif isinstance(t, str):
            why.append(t[:100])
    cw = result.get("current_window") if isinstance(result.get("current_window"), dict) else {}
    nested_dt = cw.get("double_transit") if isinstance(cw.get("double_transit"), dict) else {}
    if nested_dt.get("verdict") and not dt:
        why.append(f"current DT {nested_dt.get('verdict')}")
    detail = " · ".join(why[:4]) or "transit scan"
    return why, detail


def build_step_audit_from_timing_result(result: dict, domain: str) -> dict:
    """Build step0–step8 audit from any timing engine result dict."""
    if not isinstance(result, dict):
        return {}

    spec = get_domain_spec(domain)
    label = str(spec.get("label") or domain)
    houses = spec.get("houses") or []
    lords = spec.get("lords") or []
    dasha_targets = spec.get("dasha_targets") or []
    bucket = str(result.get("bucket") or "general")
    factors = [str(f) for f in (result.get("factors") or [])]
    ranked = _extract_ranked(result)
    top_names = [str(r.get("name") or "") for r in ranked[:5] if r.get("name")]
    kp = result.get("kp_layer") if isinstance(result.get("kp_layer"), dict) else {}
    cw = result.get("current_window") if isinstance(result.get("current_window"), dict) else {}
    next3 = result.get("next_3_windows") if isinstance(result.get("next_3_windows"), list) else []
    next_win = result.get("next_child_window") if isinstance(result.get("next_child_window"), dict) else {}
    if not next_win and next3 and isinstance(next3[0], dict):
        next_win = next3[0]

    cur_lords = _lords_from_window(cw)
    dasha_why = list(cw.get("triggers") or [])[:6]
    if not dasha_why:
        dasha_why = _factors_step(factors, "STEP5")[:6]

    transit_why, transit_detail = _transit_detail(result, factors)
    div_detail = _divisional_summary(result, factors)
    filter_detail = " · ".join(_factors_step(factors, "STEP1")[:3])
    if not filter_detail and top_names:
        filter_detail = f"top targets: {', '.join(top_names[:3])}"
    if not filter_detail:
        filter_detail = f"{label} — houses {houses[:4]}"

    kp_score = kp.get("score")
    if kp_score is None and kp:
        kp_score = sum(1 for v in kp.values() if v) * 2

    return {
        "step0": {
            "name": "User demand + bucket",
            "status": "DONE",
            "domain": domain,
            "bucket": bucket,
            "detail": f"{label} · bucket {bucket}",
        },
        "step1": {
            "name": f"D1 significators ({', '.join(lords[:3]) or 'topic houses'})",
            "status": "DONE" if top_names or filter_detail else "PARTIAL",
            "target_houses": houses,
            "target_lords": lords,
            "top_planets": top_names[:5],
            "detail": filter_detail or f"houses {houses}",
        },
        "step2": {
            "name": "Divisional verify",
            "status": "DONE" if div_detail != "divisional scan" else "PARTIAL",
            "detail": div_detail,
        },
        "step3": {
            "name": "KP cusp / significator",
            "status": "DONE" if kp else "SKIPPED",
            "kp_score": kp_score,
            "kp_cusps": spec.get("kp_cusps") or [],
            "detail": (
                f"KP score {kp_score}"
                if kp_score is not None
                else (" · ".join(_factors_step(factors, "STEP3")[:2]) or "KP partial")
            ),
        },
        "step4": {
            "name": "Natal rank (weighted score)",
            "status": "DONE" if ranked else "PARTIAL",
            "ranked_top": ranked[:5],
            "detail": (
                f"top {', '.join(top_names[:3])}"
                if top_names
                else (" · ".join(_factors_step(factors, "STEP4")[:2]) or "rank pending")
            ),
        },
        "step5": {
            "name": "Dasha activation (MD/AD/PD) — PRIMARY",
            "status": "DONE" if cur_lords else "MISSING",
            "current_lords": cur_lords,
            "current_start": cw.get("start_iso") or cw.get("start"),
            "current_end": cw.get("end_iso") or cw.get("end"),
            "dasha_targets": dasha_targets,
            "why": dasha_why,
            "detail": (
                f"MD/AD/PD {cur_lords or '—'}"
                + (f" · {_window_range(cw)}" if cur_lords else "")
                + (f" · {dasha_why[0]}" if dasha_why else "")
            ).strip(),
        },
        "step6": {
            "name": "Transit + double-transit",
            "status": "DONE" if transit_why else "NEUTRAL",
            "why": transit_why,
            "double_transit": result.get("double_transit") or cw.get("double_transit"),
            "detail": transit_detail,
        },
        "step7": {
            "name": "Window merge (next favourable AD)",
            "status": "DONE" if next_win else "NONE_FOUND",
            "next_ad": next_win.get("ad"),
            "next_md": next_win.get("md"),
            "next_start": next_win.get("start_iso") or next_win.get("start"),
            "next_end": next_win.get("end_iso") or next_win.get("end"),
            "score": next_win.get("score"),
            "detail": (
                f"next {next_win.get('ad') or next_win.get('md') or '—'}"
                + (f" · {_window_range(next_win)}" if next_win else "")
                + (f" · score {next_win.get('score')}" if next_win.get("score") is not None else "")
            ).strip(),
        },
        "step8": {
            "name": "Verdict + guards",
            "status": "DONE",
            "verdict": result.get("verdict"),
            "band": result.get("band"),
            "brand_safety_warnings": (result.get("brand_safety_warnings") or [])[:4],
            "detail": (
                f"{result.get('verdict') or '—'} · band {result.get('band') or '—'}"
            ),
        },
    }


def build_timing_audit_from_result(result: dict, step_audit: dict, domain: str) -> dict:
    """Marriage-style timing checks — dasha first."""
    s5 = step_audit.get("step5") or {}
    s6 = step_audit.get("step6") or {}
    s7 = step_audit.get("step7") or {}
    issues: list[str] = []
    checks: list[dict[str, Any]] = []

    dasha_ok = bool(s5.get("current_lords"))
    checks.append({
        "name": "dasha_trace",
        "ok": dasha_ok,
        "detail": str(s5.get("detail") or ""),
    })
    if not dasha_ok:
        issues.append("current MD/AD/PD not resolved from chart dasha chain")

    dasha_active = bool(s5.get("why")) or bool(s5.get("current_lords"))
    checks.append({
        "name": "dasha_domain_activation",
        "ok": dasha_active,
        "detail": f"lords {s5.get('current_lords') or '—'} · targets {s5.get('dasha_targets')}",
    })
    if not dasha_active:
        issues.append(f"current dasha weak for {domain} significator activation")

    transit_ok = bool(s6.get("why"))
    checks.append({
        "name": "transit_support",
        "ok": transit_ok,
        "detail": str(s6.get("detail") or "neutral"),
    })

    next_win = bool(s7.get("next_ad") or s7.get("next_md"))
    checks.append({
        "name": "next_timing_window",
        "ok": next_win,
        "detail": str(s7.get("detail") or "no upcoming AD window in horizon"),
    })

    checks.append({
        "name": "verdict_lock",
        "ok": bool(result.get("verdict")),
        "detail": str(result.get("verdict") or "")[:160],
    })

    strategy = ""
    for key in ("strategy", "recommendation_tier"):
        if result.get(key):
            strategy = str(result[key])[:200]
            break

    return {
        "status": "PASS" if not issues else "WARN",
        "issues": issues,
        "domain": domain,
        "primary_dasha": {
            "lords": s5.get("current_lords"),
            "start": s5.get("current_start"),
            "end": s5.get("current_end"),
        },
        "next_window": {
            "ad": s7.get("next_ad"),
            "md": s7.get("next_md"),
            "start": s7.get("next_start"),
            "end": s7.get("next_end"),
        },
        "transit": {"detail": s6.get("detail"), "double_transit": s6.get("double_transit")},
        "checks": checks,
        "expected_reply": strategy or str(result.get("verdict") or "")[:200],
    }


def attach_timing_pipeline_audit(result: dict, domain: str) -> dict:
    """Attach step_audit + timing_audit if not already present (career/marriage custom)."""
    if not isinstance(result, dict):
        return result
    if isinstance(result.get("step_audit"), dict) and result["step_audit"]:
        if not isinstance(result.get("timing_audit"), dict):
            result["timing_audit"] = build_timing_audit_from_result(
                result, result["step_audit"], domain,
            )
        if not result.get("step_order"):
            result["step_order"] = list(TIMING_STEP_ORDER)
        return result

    step_audit = build_step_audit_from_timing_result(result, domain)
    result["step_audit"] = step_audit
    result["step_order"] = list(TIMING_STEP_ORDER)
    result["timing_audit"] = build_timing_audit_from_result(result, step_audit, domain)
    result.setdefault("domain", domain)
    return result


def _timing_evidence_from_result(result: dict) -> list[str]:
    out: list[str] = []
    sa = result.get("step_audit") if isinstance(result.get("step_audit"), dict) else {}
    s5 = sa.get("step5") or {}
    s6 = sa.get("step6") or {}
    s7 = sa.get("step7") or {}
    for block in (s5, s6, s7):
        for w in block.get("why") or []:
            if w and w not in out:
                out.append(str(w))
        d = block.get("detail")
        if d and d not in out:
            out.append(str(d))
    if len(out) < 4:
        for f in (result.get("factors") or []):
            fs = str(f)
            if any(tok in fs.upper() for tok in ("STEP5", "STEP6", "DASHA", "MD", "AD", "TRANSIT")):
                if fs not in out:
                    out.append(fs)
            if len(out) >= 8:
                break
    return out[:8]


def build_domain_timing_slice_meta(result: dict, domain: str) -> dict[str, Any]:
    """Admin slice_meta for non-career/non-marriage timing domains."""
    result = attach_timing_pipeline_audit(dict(result), domain)
    timing_evidence = _timing_evidence_from_result(result)
    s5 = (result.get("step_audit") or {}).get("step5") or {}
    return {
        "slice": slice_for_domain(domain),
        "topic": domain,
        "archetype": result.get("bucket"),
        "verdict": result.get("verdict"),
        "summary": [str(result.get("verdict") or "")[:200]],
        "evidence": timing_evidence,
        "timing_evidence": timing_evidence,
        "dasha_trace": {
            "current_lords": s5.get("current_lords"),
            "current_start": s5.get("current_start"),
            "current_end": s5.get("current_end"),
            "dasha_targets": s5.get("dasha_targets"),
        },
        "checks": {
            "bucket": result.get("bucket"),
            "band": result.get("band"),
            "domain": domain,
        },
        "step_audit": result.get("step_audit"),
        "timing_audit": result.get("timing_audit"),
        "narrator_mode": "engine_facts_only",
    }


def build_domain_timing_engine_trace(result: dict, domain: str) -> dict[str, Any]:
    """Admin engine_trace for any timing domain."""
    if not isinstance(result, dict):
        return {}
    result = attach_timing_pipeline_audit(dict(result), domain)
    s5 = (result.get("step_audit") or {}).get("step5") or {}
    cw = result.get("current_window") if isinstance(result.get("current_window"), dict) else {}
    next3 = result.get("next_3_windows") if isinstance(result.get("next_3_windows"), list) else []
    primary = ""
    if cw:
        primary = _window_range(cw)
    elif next3 and isinstance(next3[0], dict):
        primary = _window_range(next3[0])

    return {
        "engine": engine_id_for_domain(domain),
        "domain": domain,
        "verdict": result.get("verdict"),
        "band": result.get("band"),
        "bucket": result.get("bucket"),
        "primary_window": primary,
        "step_audit": result.get("step_audit"),
        "step_order": list(result.get("step_order") or TIMING_STEP_ORDER),
        "timing_audit": result.get("timing_audit"),
        "dasha_trace": {
            "current_lords": s5.get("current_lords") or _lords_from_window(cw),
            "current_start": s5.get("current_start") or cw.get("start_iso"),
            "current_end": s5.get("current_end") or cw.get("end_iso"),
            "dasha_targets": s5.get("dasha_targets"),
        },
        "next_3_windows": next3[:3],
        "factors": list(result.get("factors") or [])[:20],
    }

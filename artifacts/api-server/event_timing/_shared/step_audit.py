"""Universal timing step_audit + timing_audit — dasha-first admin pipeline for all domains."""
from __future__ import annotations

from typing import Any

from event_timing.domain_specs import get_domain_spec

# Dasha-first admin pipeline — step1 is ALWAYS running MD/AD/PD now (not recommended window).
TIMING_STEP_ORDER: tuple[str, ...] = (
    "step1",
    "step2",
    "step3",
    "step4",
    "step5",
    "step6",
)

# Legacy marriage/career engines may still emit step0–step8; admin merges both.
LEGACY_TIMING_STEP_ORDER: tuple[str, ...] = (
    "step0",
    "step0a",
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


def _running_dasha_from_result(result: dict) -> dict:
    """Chart's active MD/AD/PD now — never the upcoming recommendation window."""
    running = result.get("dasha_running_now")
    if isinstance(running, dict) and (running.get("md") or running.get("lords")):
        return running
    if str(result.get("timing_source") or "") == "current_dasha_active":
        cw = result.get("current_window") if isinstance(result.get("current_window"), dict) else {}
        if cw.get("md") or cw.get("ad"):
            return cw
    cw = result.get("current_window") if isinstance(result.get("current_window"), dict) else {}
    if cw.get("is_active_now"):
        return cw
    return {}


def build_step_audit_from_timing_result(result: dict, domain: str) -> dict:
    """Dasha-first audit: step1 = running dasha now, then domain activation → window."""
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

    running = _running_dasha_from_result(result)
    run_lords = running.get("lords") or _lords_from_window(running)
    run_start = running.get("start_iso") or running.get("start") or ""
    run_end = running.get("end_iso") or running.get("end") or ""

    rec = result.get("current_window") if isinstance(result.get("current_window"), dict) else {}
    next_win = result.get("next_child_window") if isinstance(result.get("next_child_window"), dict) else {}
    if not next_win:
        next3 = result.get("next_3_windows") if isinstance(result.get("next_3_windows"), list) else []
        for w in next3:
            if isinstance(w, dict) and w.get("start_iso") != rec.get("start_iso"):
                next_win = w
                break

    timing_source = str(result.get("timing_source") or "")
    current_supports = bool(result.get("current_supports"))
    activation = rec.get("activation_score")
    min_activation = float(result.get("min_current_activation") or 9.0)
    running_activation = result.get("current_running_activation_score")

    kp_sync = result.get("kp_dasha_sync") if isinstance(result.get("kp_dasha_sync"), dict) else {}
    kp_active = kp_sync.get("active_now") or []
    kp_upcoming = kp_sync.get("upcoming") or []

    step5_primary = [f for f in factors if "STEP5 PRIMARY" in f.upper()]
    activation_detail = step5_primary[0] if step5_primary else ""
    if not activation_detail:
        if timing_source == "current_dasha_active":
            activation_detail = (
                f"Current AD/PD active for {domain} · score={activation or '?'} "
                f"(min {min_activation})"
            )
        elif timing_source == "next_dasha_scan":
            if running_activation is not None:
                activation_detail = (
                    f"Current AD/PD score {running_activation} < min {min_activation} "
                    f"for {domain} — forward scan window used"
                )
            else:
                activation_detail = (
                    f"Current AD/PD weak for {domain} (< {min_activation}) — next scan window"
                )
        else:
            activation_detail = f"Scan source={timing_source or 'unknown'}"

    kp_detail_parts: list[str] = []
    if kp_active:
        kp_detail_parts.append(
            "ACTIVE NOW: "
            + ", ".join(f"{x.get('house')}H CSL {x.get('csl')}" for x in kp_active[:3])
        )
    elif kp_upcoming:
        up = kp_upcoming[0] if isinstance(kp_upcoming[0], dict) else {}
        nw = up.get("next_window") if isinstance(up.get("next_window"), dict) else {}
        if nw.get("start_iso"):
            kp_detail_parts.append(
                f"NEXT CSL {up.get('csl')} · {nw.get('start_iso')}→{nw.get('end_iso')}"
            )
    kp_layer = result.get("kp_layer") if isinstance(result.get("kp_layer"), dict) else {}
    if not kp_detail_parts and kp_layer.get("score") is not None:
        kp_detail_parts.append(f"KP cusp score {kp_layer.get('score')}")

    rec_lords = _lords_from_window(rec)
    transit_why, transit_detail = _transit_detail(result, factors)
    prac = result.get("practicality") if isinstance(result.get("practicality"), dict) else {}
    prac_bit = ""
    if prac:
        prac_bit = (
            f" · practical age={prac.get('user_age')} min={prac.get('min_purchase_age')} "
            f"afford={prac.get('affordability')}"
        )
        if prac.get("too_young_now"):
            prac_bit += " · too_young=YES"

    return {
        "step1": {
            "name": "Active dasha — abhi kya chal raha hai",
            "status": "DONE" if run_lords else "MISSING",
            "md": running.get("md"),
            "ad": running.get("ad"),
            "pd": running.get("pd"),
            "current_lords": run_lords,
            "current_start": run_start,
            "current_end": run_end,
            "detail": (
                f"RUNNING MD/AD/PD {run_lords or '—'}"
                + (f" · {run_start}→{run_end}" if run_start and run_end else "")
                + (f" · kab tak: {run_end}" if run_end else "")
            ).strip(),
        },
        "step2": {
            "name": f"Current AD/PD — {label} houses ({', '.join(lords[:3]) or 'topic'}) active?",
            "status": "DONE" if current_supports else "WEAK",
            "timing_source": timing_source,
            "current_supports": current_supports,
            "activation_score": activation,
            "running_activation_score": running_activation,
            "min_activation": min_activation,
            "dasha_targets": dasha_targets,
            "top_planets": top_names[:5],
            "detail": activation_detail,
        },
        "step3": {
            "name": "KP — current dasha + cusp sub-lords",
            "status": "DONE" if kp_active or kp_detail_parts else "PARTIAL",
            "kp_active_now": kp_active,
            "kp_upcoming": kp_upcoming[:2],
            "detail": " · ".join(kp_detail_parts) or "KP partial — no CSL match in running lords",
        },
        "step4": {
            "name": "Primary answer window (event timing)",
            "status": "DONE" if rec_lords else "NONE_FOUND",
            "current_lords": rec_lords,
            "current_start": rec.get("start_iso") or rec.get("start"),
            "current_end": rec.get("end_iso") or rec.get("end"),
            "is_active_now": bool(rec.get("is_active_now") or timing_source == "current_dasha_active"),
            "why": list(rec.get("triggers") or [])[:4],
            "detail": (
                f"{'ACTIVE NOW' if timing_source == 'current_dasha_active' else 'UPCOMING'} "
                f"MD/AD/PD {rec_lords or '—'}"
                + (f" · {_window_range(rec)}" if rec_lords else "")
            ).strip(),
        },
        "step5": {
            "name": "Next favourable window (forward scan)",
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
        "step6": {
            "name": "Verdict + transit",
            "status": "DONE",
            "verdict": result.get("verdict"),
            "band": result.get("band"),
            "bucket": bucket,
            "domain": domain,
            "transit_detail": transit_detail,
            "double_transit": result.get("double_transit"),
            "brand_safety_warnings": (result.get("brand_safety_warnings") or [])[:4],
            "detail": (
                f"{result.get('verdict') or '—'} · band {result.get('band') or '—'}"
                + (f" · {transit_detail[:80]}" if transit_detail else "")
                + prac_bit
            ),
        },
    }


def build_timing_audit_from_result(result: dict, step_audit: dict, domain: str) -> dict:
    """Marriage-style timing checks — running dasha first (step1)."""
    s1 = step_audit.get("step1") or {}
    s2 = step_audit.get("step2") or {}
    s4 = step_audit.get("step4") or {}
    s5 = step_audit.get("step5") or {}
    s6 = step_audit.get("step6") or step_audit.get("step8") or {}
    issues: list[str] = []
    checks: list[dict[str, Any]] = []

    dasha_ok = bool(s1.get("current_lords"))
    checks.append({
        "name": "dasha_running_now",
        "ok": dasha_ok,
        "detail": str(s1.get("detail") or ""),
    })
    if not dasha_ok:
        issues.append("running MD/AD/PD not resolved from chart dasha chain")

    dasha_active = bool(s2.get("current_supports")) or str(s2.get("status") or "").upper() == "DONE"
    checks.append({
        "name": "dasha_domain_activation",
        "ok": dasha_active,
        "detail": str(s2.get("detail") or f"targets {s2.get('dasha_targets')}"),
    })
    if not dasha_active:
        issues.append(f"current AD/PD weak for {domain} significator activation")

    rec_ok = bool(s4.get("current_lords"))
    checks.append({
        "name": "primary_event_window",
        "ok": rec_ok,
        "detail": str(s4.get("detail") or "no recommendation window"),
    })

    next_win = bool(s5.get("next_ad") or s5.get("next_md"))
    checks.append({
        "name": "next_timing_window",
        "ok": next_win,
        "detail": str(s5.get("detail") or "no upcoming window in horizon"),
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
        "running_dasha": {
            "lords": s1.get("current_lords"),
            "md": s1.get("md"),
            "ad": s1.get("ad"),
            "pd": s1.get("pd"),
            "start": s1.get("current_start"),
            "end": s1.get("current_end"),
        },
        "primary_dasha": {
            "lords": s4.get("current_lords"),
            "start": s4.get("current_start"),
            "end": s4.get("current_end"),
        },
        "next_window": {
            "ad": s5.get("next_ad"),
            "md": s5.get("next_md"),
            "start": s5.get("next_start"),
            "end": s5.get("next_end"),
        },
        "transit": {"detail": s6.get("transit_detail") or s6.get("detail"), "double_transit": s6.get("double_transit")},
        "checks": checks,
        "expected_reply": strategy or str(result.get("verdict") or "")[:200],
    }


def attach_timing_pipeline_audit(result: dict, domain: str) -> dict:
    """Attach dasha-first step_audit — step1 is always running MD/AD/PD now."""
    if not isinstance(result, dict):
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
    for key in ("step1", "step2", "step4", "step5"):
        block = sa.get(key) or {}
        d = block.get("detail")
        if d and d not in out:
            out.append(str(d))
    if len(out) < 4:
        for f in (result.get("factors") or []):
            fs = str(f)
            if any(tok in fs.upper() for tok in ("STEP5", "RUNNING", "PRIMARY", "DASHA")):
                if fs not in out:
                    out.append(fs)
            if len(out) >= 8:
                break
    return out[:8]


def build_domain_timing_slice_meta(result: dict, domain: str) -> dict[str, Any]:
    """Admin slice_meta for non-career/non-marriage timing domains."""
    result = attach_timing_pipeline_audit(dict(result), domain)
    timing_evidence = _timing_evidence_from_result(result)
    s1 = (result.get("step_audit") or {}).get("step1") or {}
    s4 = (result.get("step_audit") or {}).get("step4") or {}
    return {
        "slice": slice_for_domain(domain),
        "topic": domain,
        "archetype": result.get("bucket"),
        "verdict": result.get("verdict"),
        "summary": [str(result.get("verdict") or "")[:200]],
        "evidence": timing_evidence,
        "timing_evidence": timing_evidence,
        "dasha_trace": {
            "running_lords": s1.get("current_lords"),
            "running_start": s1.get("current_start"),
            "running_end": s1.get("current_end"),
            "recommended_lords": s4.get("current_lords"),
            "recommended_start": s4.get("current_start"),
            "recommended_end": s4.get("current_end"),
            "dasha_targets": (result.get("step_audit") or {}).get("step2", {}).get("dasha_targets"),
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
    s1 = (result.get("step_audit") or {}).get("step1") or {}
    s4 = (result.get("step_audit") or {}).get("step4") or {}
    running = result.get("dasha_running_now") if isinstance(result.get("dasha_running_now"), dict) else {}
    rec = result.get("current_window") if isinstance(result.get("current_window"), dict) else {}
    next3 = result.get("next_3_windows") if isinstance(result.get("next_3_windows"), list) else []
    running_range = _window_range(s1) or _window_range(running)
    primary = _window_range(s4) or _window_range(rec)
    if not primary and next3 and isinstance(next3[0], dict):
        primary = _window_range(next3[0])

    return {
        "engine": engine_id_for_domain(domain),
        "domain": domain,
        "pipeline_version": "dasha_first_v2",
        "verdict": result.get("verdict"),
        "band": result.get("band"),
        "bucket": result.get("bucket"),
        "running_dasha_window": running_range,
        "running_dasha": {
            "md": s1.get("md") or running.get("md"),
            "ad": s1.get("ad") or running.get("ad"),
            "pd": s1.get("pd") or running.get("pd"),
            "lords": s1.get("current_lords") or _lords_from_window(running),
            "start": s1.get("current_start") or running.get("start_iso"),
            "end": s1.get("current_end") or running.get("end_iso"),
        },
        "primary_window": primary,
        "step_audit": result.get("step_audit"),
        "step_order": list(result.get("step_order") or TIMING_STEP_ORDER),
        "timing_audit": result.get("timing_audit"),
        "dasha_trace": {
            "running_lords": s1.get("current_lords") or _lords_from_window(running),
            "running_start": s1.get("current_start") or running.get("start_iso"),
            "running_end": s1.get("current_end") or running.get("end_iso"),
            "recommended_lords": s4.get("current_lords") or _lords_from_window(rec),
            "recommended_start": s4.get("current_start") or rec.get("start_iso"),
            "recommended_end": s4.get("current_end") or rec.get("end_iso"),
            "dasha_targets": (result.get("step_audit") or {}).get("step2", {}).get("dasha_targets"),
        },
        "next_3_windows": next3[:3],
        "factors": list(result.get("factors") or [])[:20],
    }

"""Admin-only debug payload — what chart/context was sent to the Ask LLM."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

_MAX_DB_CHARS = 80_000
# Bulky prompt blobs are omitted on DB save (sizes.*_chars retains lengths).
_DB_STRIP_KEYS = ("chart_text", "system_prompt", "user_payload", "extra_rules")

_ANSWER_PATH_LABELS = {
    "engine_only": "Engine only (no LLM)",
    "engine_then_llm": "Engine → LLM",
    "direct_llm": "Direct LLM (no engine facts)",
    "unknown": "Unknown path",
}


def derive_answer_path(
    *,
    llm_called: bool,
    skip_reason: str = "",
    checks: dict[str, Any] | None = None,
    slice_meta: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Return (code, human label) for admin: how the user answer was produced."""
    checks = checks or {}
    slice_meta = slice_meta or {}
    skip = (skip_reason or "").strip().lower()

    slice_type = str(checks.get("slice_type") or "")
    if checks.get("direct_llm_bypass") or slice_type in (
        "llm_no_engine_v1",
        "controlled_fallback_v1",
    ):
        return "direct_llm", _ANSWER_PATH_LABELS["direct_llm"]
    sl = str(slice_meta.get("slice") or "")
    has_verdict = bool(slice_meta.get("verdict"))
    has_evidence = bool(slice_meta.get("evidence"))
    mr_v1 = (
        slice_meta.get("slice") == "mr_engine_v1"
        or checks.get("mr_engine") == "v1"
        or slice_type == "mr_engine_v1"
    )
    mr_static = bool(checks.get("is_mr_static"))
    marriage_engine = bool(checks.get("is_marriage_engine"))
    career_engine = bool(checks.get("is_career_engine"))
    timing_engine = slice_type in (
        "timing_marriage_engine",
        "timing_marriage_engine_alt",
        "timing_career_engine",
    )
    domain_engine_slice = sl in (
        "mr_engine_v1",
        "marriage_timing_m17",
        "career_engine_v1",
        "career_timing_v1",
        "education_engine_v1",
        "children_engine_v1",
        "property_engine_v1",
        "travel_engine_v1",
        "litigation_engine_v1",
        "luck_engine_v1",
        "network_engine_v1",
        "siblings_engine_v1",
        "parents_engine_v1",
        "enemies_engine_v1",
        "spiritual_engine_v1",
        "fame_engine_v1",
        "personality_engine_v1",
        "dreams_engine_v1",
        "anger_engine_v1",
        "remedy_engine_v1",
        "charity_engine_v1",
        "settlement_engine_v1",
        "vastu_engine_v1",
        "pets_engine_v1",
        "wellness_engine_v1",
        "controlled_fallback_v1",
        "finance_engine_v1",
        "health_engine_v1",
        "travel_timing_v1",
        "finance_timing_v1",
        "health_timing_v1",
        "children_timing_v1",
        "love_timing_v1",
        "education_timing_v1",
        "property_timing_v1",
        "litigation_timing_v1",
        "vehicle_timing_v1",
        "vehicle_engine_v1",
    )
    dcr_love_buckets = sl == "marriage_relationship" and bool(slice_meta.get("buckets"))
    has_engine_facts = (
        has_verdict
        or has_evidence
        or domain_engine_slice
        or dcr_love_buckets
        or mr_v1
        or (mr_static and (has_verdict or has_evidence or domain_engine_slice))
        or (marriage_engine and (has_verdict or has_evidence or domain_engine_slice))
        or (career_engine and (has_verdict or has_evidence or domain_engine_slice))
        or timing_engine
    )

    if not llm_called:
        if skip in ("mr_engine_template", "marriage_timing_deterministic") or checks.get("skip_llm"):
            return "engine_only", _ANSWER_PATH_LABELS["engine_only"]
        if has_engine_facts:
            return "engine_only", _ANSWER_PATH_LABELS["engine_only"]
        return "unknown", _ANSWER_PATH_LABELS["unknown"]

    if has_engine_facts and (
        mr_v1
        or (mr_static and (has_verdict or has_evidence or domain_engine_slice))
        or (marriage_engine and (has_verdict or has_evidence or domain_engine_slice))
        or (career_engine and (has_verdict or has_evidence or domain_engine_slice))
        or timing_engine
        or dcr_love_buckets
    ):
        return "engine_then_llm", _ANSWER_PATH_LABELS["engine_then_llm"]
    if has_verdict or has_evidence:
        return "engine_then_llm", _ANSWER_PATH_LABELS["engine_then_llm"]
    return "direct_llm", _ANSWER_PATH_LABELS["direct_llm"]


_MARRIAGE_TRACE_STEP_ORDER = (
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


def _transit_ctx_from_trace(trace: dict[str, Any], s7: Optional[dict[str, Any]] = None) -> Optional[dict[str, Any]]:
    ctx = trace.get("transit_chart_context")
    if isinstance(ctx, dict) and ctx.get("h7_si") is not None:
        return ctx
    try:
        from event_timing.marriage.marriage_engine_v2 import transit_ctx_from_public_chart
    except Exception:
        return None
    if s7 is None:
        step_audit = trace.get("step_audit")
        if isinstance(step_audit, dict):
            s7 = step_audit.get("step7")
    if isinstance(s7, dict):
        rebuilt = transit_ctx_from_public_chart(s7.get("chart_context"))
        if rebuilt:
            return rebuilt
    return None


def _finalize_step7_transit(s7: dict[str, Any], trace: dict[str, Any]) -> None:
    try:
        from event_timing.marriage.marriage_engine_v2 import _build_step7_transit_package
    except Exception:
        return

    window: dict[str, Any] = {}
    wins = trace.get("top_3_windows") or []
    if wins and isinstance(wins[0], dict):
        window = dict(wins[0])
    window.setdefault("transit_confirmed", s7.get("transit_confirmed"))
    window.setdefault("jup", s7.get("jupiter_hit", s7.get("jup")))
    window.setdefault("sat", s7.get("saturn_hit", s7.get("sat")))
    window.setdefault("dt", s7.get("double_transit", s7.get("dt")))
    if s7.get("detail") and not window.get("dt_detail"):
        window["dt_detail"] = s7.get("detail")

    pkg = _build_step7_transit_package(
        window, _transit_ctx_from_trace(trace, s7),
    )
    s7["detail"] = pkg.get("detail")
    s7["months"] = pkg.get("months")
    s7["by_month"] = pkg.get("by_month")
    s7["transit_type"] = pkg.get("transit_type")
    s7["transit_type_label"] = pkg.get("transit_type_label")
    s7["chart_context"] = pkg.get("chart_context")
    s7["jupiter_hit"] = pkg.get("jupiter_hit")
    s7["saturn_hit"] = pkg.get("saturn_hit")
    s7["double_transit"] = pkg.get("double_transit")
    s7.pop("samples", None)


def normalize_engine_trace_transit_months(trace: dict[str, Any] | None) -> dict[str, Any] | None:
    """Rewrite step7 / timing_audit transit — month + Guru/Shani rashi."""
    if not isinstance(trace, dict):
        return trace
    try:
        from event_timing.marriage.marriage_engine_v2 import (
            _build_step7_transit_package,
            _monthify_verbose_transit_detail,
        )
    except Exception:
        return trace

    transit_ctx = _transit_ctx_from_trace(trace)

    step_audit = trace.get("step_audit")
    if isinstance(step_audit, dict):
        s7 = step_audit.get("step7")
        if isinstance(s7, dict):
            _finalize_step7_transit(s7, trace)

    timing_audit = trace.get("timing_audit")
    if isinstance(timing_audit, dict):
        transit = timing_audit.get("transit")
        if isinstance(transit, dict):
            window = wins[0] if (wins := trace.get("top_3_windows") or []) and isinstance(wins[0], dict) else {}
            pkg = _build_step7_transit_package(window, transit_ctx)
            transit["detail"] = pkg.get("detail")
            transit["months"] = pkg.get("months")
            transit["by_month"] = pkg.get("by_month")
            transit["transit_type"] = pkg.get("transit_type")
            transit["transit_type_label"] = pkg.get("transit_type_label")
            transit["chart_context"] = pkg.get("chart_context")
            transit.pop("samples", None)

        for check in timing_audit.get("checks") or []:
            if not isinstance(check, dict):
                continue
            if check.get("name") == "transit_support" and isinstance(check.get("detail"), str):
                check["detail"] = _monthify_verbose_transit_detail(
                    check["detail"], transit_ctx,
                )

    for win in trace.get("top_3_windows") or []:
        if isinstance(win, dict):
            pkg = _build_step7_transit_package(win, transit_ctx)
            win["dt_detail"] = pkg.get("detail")
            win["transit_months"] = pkg.get("months")
            win["transit_by_month"] = pkg.get("by_month")
            win.pop("transit_samples", None)

    return trace


def _aspect_house_nums(block: dict[str, Any] | None) -> list[int]:
    if not isinstance(block, dict):
        return []
    out: list[int] = []
    for row in block.get("aspect_houses") or []:
        if isinstance(row, dict):
            h = row.get("house")
            if isinstance(h, int):
                out.append(h)
    return sorted(set(out))


def _marriage_bcp_linkage_snapshot(engine_result: dict[str, Any]) -> dict[str, Any]:
    """D1/D9 7L placement + aspect houses for admin Step 2."""
    bcp = engine_result.get("bcp_marriage_ages")
    if not isinstance(bcp, dict):
        s0a = engine_result.get("step0a")
        bcp = (s0a.get("bcp_marriage_ages") if isinstance(s0a, dict) else None) or {}
    if not isinstance(bcp, dict):
        bcp = {}
    d9_bcp = bcp.get("d9_bcp") if isinstance(bcp.get("d9_bcp"), dict) else {}
    dasha_scan: dict[str, Any] = {}
    s0a = engine_result.get("step0a")
    if isinstance(s0a, dict) and isinstance(s0a.get("dasha_scan_plan"), dict):
        dasha_scan = s0a["dasha_scan_plan"]
    elif isinstance(engine_result.get("dasha_scan_plan"), dict):
        dasha_scan = engine_result["dasha_scan_plan"]
    step0a_audit: dict[str, Any] = {}
    step_audit = engine_result.get("step_audit")
    if isinstance(step_audit, dict) and isinstance(step_audit.get("step0a"), dict):
        step0a_audit = step_audit["step0a"]

    d1_asp = _aspect_house_nums(bcp) or list(step0a_audit.get("d1_7l_aspect_houses") or [])
    d9_asp = _aspect_house_nums(d9_bcp) or list(step0a_audit.get("d9_7l_aspect_houses") or [])
    d1_sit = bcp.get("seventh_lord_house")
    if d1_sit is None:
        d1_sit = step0a_audit.get("d1_7l_placement_house")
    d9_sit = d9_bcp.get("seventh_lord_house")
    if d9_sit is None:
        d9_sit = step0a_audit.get("d9_7l_placement_house")

    shared = sorted(set(bcp.get("shared_7l_linkage_houses") or []))
    if not shared and d1_asp and d9_asp:
        shared = sorted(set(d1_asp) & set(d9_asp))
    if not shared and isinstance(d1_sit, int) and d1_sit == d9_sit:
        shared = [d1_sit]

    user_age = engine_result.get("user_age")
    if user_age is None and isinstance(step0a_audit.get("user_age"), (int, float)):
        user_age = int(step0a_audit["user_age"])
    house_display = bcp.get("bcp_admin_display")
    if not isinstance(house_display, dict) or not house_display.get("d1"):
        try:
            from event_timing.marriage.bcp_marriage_ages import build_bcp_admin_linkage_display

            house_display = build_bcp_admin_linkage_display(
                {
                    "seventh_lord": bcp.get("seventh_lord") or engine_result.get("d1_seventh_lord"),
                    "seventh_lord_house": d1_sit,
                    "aspect_houses": [{"house": h} for h in d1_asp],
                    "d9_bcp": {
                        "seventh_lord": d9_bcp.get("seventh_lord") or engine_result.get("d9_seventh_lord"),
                        "seventh_lord_house": d9_sit,
                        "aspect_houses": [{"house": h} for h in d9_asp],
                    },
                    "shared_7l_linkage_houses": shared,
                    "user_age": user_age,
                },
                user_age=int(user_age) if user_age is not None else None,
            )
        except Exception:
            house_display = {}

    return {
        "d1_seventh_lord": bcp.get("seventh_lord") or engine_result.get("d1_seventh_lord"),
        "d9_seventh_lord": d9_bcp.get("seventh_lord") or engine_result.get("d9_seventh_lord"),
        "d1_7l_placement_house": d1_sit,
        "d1_7l_aspect_houses": d1_asp,
        "d9_7l_placement_house": d9_sit,
        "d9_7l_aspect_houses": d9_asp,
        "d1_7l_linkage_houses": sorted(set(bcp.get("d1_7l_linkage_houses") or [])),
        "d9_7l_linkage_houses": sorted(set(bcp.get("d9_7l_linkage_houses") or [])),
        "shared_7l_linkage_houses": shared,
        "shared_house_priority_ages": list(bcp.get("shared_house_priority_ages") or []),
        "bcp_house_display": house_display,
        "bcp_ages_next_years": list(
            step0a_audit.get("bcp_ages_next_years")
            or dasha_scan.get("bcp_ages_next_years")
            or []
        )[:4],
        "focus_ages": list(
            step0a_audit.get("focus_ages") or dasha_scan.get("bcp_focus_ages") or []
        ),
        "timing_mode": step0a_audit.get("timing_mode") or dasha_scan.get("timing_mode"),
    }


def _bcp_linkage_evidence_lines(linkage: dict[str, Any]) -> list[str]:
    try:
        from event_timing.marriage.bcp_marriage_ages import bcp_linkage_admin_lines

        fake = {
            "seventh_lord": linkage.get("d1_seventh_lord"),
            "seventh_lord_house": linkage.get("d1_7l_placement_house"),
            "aspect_houses": [
                {"house": h} for h in (linkage.get("d1_7l_aspect_houses") or [])
            ],
            "d9_bcp": {
                "seventh_lord": linkage.get("d9_seventh_lord"),
                "seventh_lord_house": linkage.get("d9_7l_placement_house"),
                "aspect_houses": [
                    {"house": h} for h in (linkage.get("d9_7l_aspect_houses") or [])
                ],
            },
            "shared_7l_linkage_houses": linkage.get("shared_7l_linkage_houses") or [],
        }
        lines = bcp_linkage_admin_lines(fake)
        if lines:
            return lines
    except Exception:
        pass
    lines: list[str] = []
    d1l = linkage.get("d1_seventh_lord")
    d1p = linkage.get("d1_7l_placement_house")
    d1a = linkage.get("d1_7l_aspect_houses") or []
    if d1l and d1p is not None:
        asp = ",".join(str(x) for x in d1a)
        lines.append(f"BCP_LINKAGE D1 7L={d1l} placement={d1p} aspects={asp}")
    d9l = linkage.get("d9_seventh_lord")
    d9p = linkage.get("d9_7l_placement_house")
    d9a = linkage.get("d9_7l_aspect_houses") or []
    if d9l and d9p is not None:
        asp = ",".join(str(x) for x in d9a)
        lines.append(f"BCP_LINKAGE D9 7L={d9l} placement={d9p} aspects={asp}")
    shared = linkage.get("shared_7l_linkage_houses") or []
    if shared:
        lines.append(f"BCP_SHARED_HOUSES {','.join(str(h) for h in shared)}")
    return lines


def _parse_bcp_linkage_from_evidence(evidence: list[str] | None) -> dict[str, Any]:
    import re

    out: dict[str, Any] = {}
    if not evidence:
        return out
    for line in evidence:
        s = str(line)
        m = re.search(
            r"BCP_LINKAGE\s+D1\s+7L=(\w+)\s+placement=(\d+)\s+aspects=([\d,]*)",
            s,
            re.I,
        )
        if m:
            out["d1_seventh_lord"] = m.group(1)
            out["d1_7l_placement_house"] = int(m.group(2))
            out["d1_7l_aspect_houses"] = [
                int(x) for x in m.group(3).split(",") if x.strip().isdigit()
            ]
            continue
        m = re.search(
            r"BCP_LINKAGE\s+D9\s+7L=(\w+)\s+placement=(\d+)\s+aspects=([\d,]*)",
            s,
            re.I,
        )
        if m:
            out["d9_seventh_lord"] = m.group(1)
            out["d9_7l_placement_house"] = int(m.group(2))
            out["d9_7l_aspect_houses"] = [
                int(x) for x in m.group(3).split(",") if x.strip().isdigit()
            ]
            continue
        m = re.search(r"BCP-D1:\s+7L\s+(\w+)@(\d+)H", s, re.I)
        if m:
            out.setdefault("d1_seventh_lord", m.group(1))
            out.setdefault("d1_7l_placement_house", int(m.group(2)))
        m = re.search(r"BCP-D9:\s+7L\s+(\w+)@(\d+)H", s, re.I)
        if m:
            out.setdefault("d9_seventh_lord", m.group(1))
            out.setdefault("d9_7l_placement_house", int(m.group(2)))
        m = re.search(r"D1\s+7L=([A-Za-z]+)", s)
        if m:
            out.setdefault("d1_seventh_lord", m.group(1))
        m = re.search(r"D9\s+7L=([A-Za-z]+)", s)
        if m:
            out.setdefault("d9_seventh_lord", m.group(1))
        m = re.search(r"BCP_SHARED_HOUSES\s+([\d,]+)", s, re.I)
        if m:
            out["shared_7l_linkage_houses"] = [
                int(x) for x in m.group(1).split(",") if x.strip().isdigit()
            ]
        m = re.search(
            r"BCP_HOUSE\s+(D1|D9)\s+(placement|aspect)=(\d+)\s+ages=([\d,]*)",
            s,
            re.I,
        )
        if m:
            div = m.group(1).upper()
            kind = m.group(2).lower()
            house = int(m.group(3))
            ages = [int(x) for x in m.group(4).split(",") if x.strip().isdigit()]
            key = "d1" if div == "D1" else "d9"
            if kind == "placement":
                out[f"{key}_7l_placement_house"] = house
                if key == "d1":
                    out.setdefault("d1_placement_ages", ages)
                else:
                    out.setdefault("d9_placement_ages", ages)
            else:
                asp_key = f"{key}_7l_aspect_houses"
                cur = list(out.get(asp_key) or [])
                if house not in cur:
                    cur.append(house)
                out[asp_key] = sorted(cur)
    return out


def _rebuild_bcp_house_display(linkage: dict[str, Any], user_age: int | None) -> dict[str, Any]:
    if linkage.get("bcp_house_display") and isinstance(linkage["bcp_house_display"], dict):
        disp = linkage["bcp_house_display"]
        if disp.get("d1", {}).get("items"):
            return disp
    try:
        from event_timing.marriage.bcp_marriage_ages import build_bcp_admin_linkage_display

        return build_bcp_admin_linkage_display(
            {
                "seventh_lord": linkage.get("d1_seventh_lord"),
                "seventh_lord_house": linkage.get("d1_7l_placement_house"),
                "aspect_houses": [
                    {"house": h} for h in (linkage.get("d1_7l_aspect_houses") or [])
                ],
                "d9_bcp": {
                    "seventh_lord": linkage.get("d9_seventh_lord"),
                    "seventh_lord_house": linkage.get("d9_7l_placement_house"),
                    "aspect_houses": [
                        {"house": h} for h in (linkage.get("d9_7l_aspect_houses") or [])
                    ],
                },
                "shared_7l_linkage_houses": linkage.get("shared_7l_linkage_houses") or [],
                "user_age": user_age,
            },
            user_age=user_age,
        )
    except Exception:
        return {}


def _merge_bcp_linkage_into_step0a(
    step0a: dict[str, Any],
    linkage: dict[str, Any],
) -> dict[str, Any]:
    out = dict(step0a or {})
    for key, val in linkage.items():
        if val is None:
            continue
        if isinstance(val, list) and not val and out.get(key):
            continue
        if out.get(key) in (None, "", [], {}):
            out[key] = val
    return out


_BCP_LINKAGE_FORCE_KEYS = (
    "d1_seventh_lord",
    "d9_seventh_lord",
    "d1_7l_placement_house",
    "d1_7l_aspect_houses",
    "d9_7l_placement_house",
    "d9_7l_aspect_houses",
    "d1_7l_linkage_houses",
    "d9_7l_linkage_houses",
    "shared_7l_linkage_houses",
    "shared_house_priority_ages",
    "bcp_house_display",
    "bcp_ages_next_years",
    "focus_ages",
    "timing_mode",
)


def _force_merge_bcp_linkage_into_step0a(
    step0a: dict[str, Any],
    linkage: dict[str, Any],
) -> dict[str, Any]:
    out = dict(step0a or {})
    for key in _BCP_LINKAGE_FORCE_KEYS:
        if key in linkage and linkage[key] is not None:
            out[key] = linkage[key]
    return out


def ensure_marriage_step_audit_on_result(
    engine_result: dict[str, Any],
    kundli: dict[str, Any],
    kp: dict[str, Any] | None = None,
    birth: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Guarantee step_audit Steps 0–3 on every M17 engine return (even KP/dasha gate)."""
    if not isinstance(engine_result, dict):
        return engine_result
    chart = prepare_kundli_for_marriage_engine(kundli) or kundli
    lagna_si = _resolve_lagna_si_for_admin(chart)
    if lagna_si is None:
        print(
            "[ensure_marriage_step_audit] skip lagna_si "
            f"asc={chart.get('ascendant')!r} ascDeg={chart.get('ascendantDeg')!r}",
            flush=True,
        )
        return engine_result
    try:
        from event_timing.marriage.kp_from_chart import resolve_kp

        kp_resolved = resolve_kp(
            chart,
            kp if isinstance(kp, dict) else {},
            birth,
        )
    except Exception:
        kp_resolved = kp if isinstance(kp, dict) else {}

    audit = dict(engine_result.get("step_audit") or {})
    try:
        from event_timing.marriage.marriage_spec_pipeline import safe_natal_step_audit

        natal = safe_natal_step_audit(chart, kp_resolved or {}, lagna_si)
        for key, block in natal.items():
            if isinstance(block, dict):
                audit[key] = {**(audit.get(key) or {}), **block}
    except Exception as exc:
        print(
            f"[ensure_marriage_step_audit] natal failed: {type(exc).__name__}: {str(exc)[:160]}",
            flush=True,
        )

    if not audit.get("step0") or not audit.get("step0a"):
        try:
            from event_timing.marriage.marriage_engine_v2 import compute_timing_window_fallback

            fb = compute_timing_window_fallback(
                chart, {}, kp_resolved or {}, birth,
            ) or {}
            fb_sa = fb.get("step_audit") if isinstance(fb.get("step_audit"), dict) else {}
            for key in ("step0", "step0a"):
                if isinstance(fb_sa.get(key), dict):
                    audit[key] = {**(audit.get(key) or {}), **fb_sa[key]}
        except Exception as exc:
            print(
                f"[ensure_marriage_step_audit] fallback failed: {type(exc).__name__}: {str(exc)[:160]}",
                flush=True,
            )

    existing_s6 = audit.get("step6") if isinstance(audit.get("step6"), dict) else {}
    if not (existing_s6.get("selected_windows") or []):
        try:
            from event_timing.marriage.marriage_engine_v2 import build_marriage_step6_audit

            step6 = build_marriage_step6_audit(
                chart, step_audit=audit, birth=birth,
            )
            if step6.get("selected_windows"):
                audit["step6"] = step6
        except Exception as exc:
            print(
                f"[ensure_marriage_step_audit] step6 failed: "
                f"{type(exc).__name__}: {str(exc)[:160]}",
                flush=True,
            )

    if audit:
        engine_result["step_audit"] = audit
        s1 = ((audit.get("step1") or {}).get("result") or {})
        print(
            "[ensure_marriage_step_audit] ok "
            f"step0={bool(audit.get('step0'))} step0a={bool(audit.get('step0a'))} "
            f"step3={bool(audit.get('step3'))} step6={bool((audit.get('step6') or {}).get('selected_windows'))} "
            f"d1_7L={s1.get('seventh_lord')!r}",
            flush=True,
        )
    return engine_result


_MARRIAGE_Q_KW = (
    "shaadi", "shadi", "shādi", "marriage", "vivah", "wedding", "byah",
    "विवाह", "शादी", "विवाह कब", "marry",
)


def _is_marriage_question_text(q: str) -> bool:
    ql = (q or "").lower()
    return any(k in ql for k in _MARRIAGE_Q_KW)


def _should_recompute_marriage_admin(
    ctx: dict[str, Any],
    *,
    question_text: str = "",
    topic: str = "",
) -> bool:
    if _is_marriage_timing_admin_ctx(ctx):
        return True
    if _is_marriage_question_text(question_text):
        return True
    tl = (topic or "").strip().lower()
    if tl in ("marriage", "timing", "vivah"):
        return True
    return False


def _bootstrap_marriage_admin_ctx(
    ctx: dict[str, Any] | None,
    *,
    question_text: str = "",
    topic: str = "",
) -> dict[str, Any]:
    """Ensure saved rows have enough metadata for marriage admin recompute."""
    out = dict(ctx) if isinstance(ctx, dict) else {}
    if question_text and not out.get("question"):
        out["question"] = question_text[:2000]
    if not out.get("is_timing"):
        if (topic or "").lower() in ("timing", "marriage", "vivah"):
            out["is_timing"] = True
        elif _is_marriage_question_text(question_text):
            out["is_timing"] = True
    checks = dict(out.get("checks") or {}) if isinstance(out.get("checks"), dict) else {}
    if not checks.get("slice_type"):
        checks["slice_type"] = "timing_marriage_engine"
    checks["is_marriage_engine"] = True
    out["checks"] = checks
    sm = dict(out.get("slice_meta") or {}) if isinstance(out.get("slice_meta"), dict) else {}
    if not sm.get("slice"):
        sm["slice"] = "marriage_timing_m17"
    out["slice_meta"] = sm
    return out


def _is_marriage_timing_admin_ctx(ctx: dict[str, Any]) -> bool:
    slice_meta = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    checks = ctx.get("checks") if isinstance(ctx.get("checks"), dict) else {}
    sl = str(slice_meta.get("slice") or checks.get("slice_type") or "")
    if "marriage_timing" in sl or sl == "timing_marriage_engine":
        return True
    if checks.get("is_marriage_engine"):
        return True
    blocks = ctx.get("blocks") if isinstance(ctx.get("blocks"), dict) else {}
    trace = blocks.get("engine_trace") or blocks.get("marriage_engine_trace")
    if isinstance(trace, dict) and str(trace.get("engine") or "") == "marriage_timing_m17":
        return True
    intent = ctx.get("llm_intent") if isinstance(ctx.get("llm_intent"), dict) else {}
    topic = str(intent.get("topic") or ctx.get("topic") or "").lower()
    q = str(
        ctx.get("question")
        or intent.get("question_normalized")
        or intent.get("question_raw")
        or ""
    ).lower()
    marriage_q = any(k in q for k in ("shaadi", "shadi", "shādi", "marriage", "vivah", "wedding", "byah"))
    if marriage_q and (
        bool(ctx.get("is_timing") or ctx.get("question_type") == "TIMING")
        or topic in ("marriage", "timing")
        or checks.get("dasha_included")
    ):
        return True
    return False


_RASHI_NAME_TO_SI = {
    "aries": 0, "taurus": 1, "gemini": 2, "cancer": 3, "leo": 4, "virgo": 5,
    "libra": 6, "scorpio": 7, "sagittarius": 8, "capricorn": 9, "aquarius": 10, "pisces": 11,
    "mesh": 0, "vrishabh": 1, "mithun": 2, "kark": 3, "karka": 3, "simha": 4, "singh": 4,
    "kanya": 5, "tula": 6, "vrishchik": 7, "vrishchika": 7, "dhanu": 8, "makar": 9,
    "kumbh": 10, "meen": 11, "mīn": 11,
}


def _sign_si_from_value(val: Any) -> int | None:
    if isinstance(val, int) and 0 <= val < 12:
        return val
    if isinstance(val, str):
        key = val.strip().lower().replace(" ", "")
        if key in _RASHI_NAME_TO_SI:
            return _RASHI_NAME_TO_SI[key]
        try:
            from event_timing.marriage.marriage_engine_v2 import _sign_idx

            si = _sign_idx(val)
            if si is not None:
                return si
        except Exception:
            pass
    return None


_PLANET_NAME_CANON: dict[str, str] = {
    "sun": "Sun", "surya": "Sun", "सूर्य": "Sun",
    "moon": "Moon", "chandra": "Moon", "चंद्र": "Moon", "चन्द्र": "Moon",
    "mars": "Mars", "mangal": "Mars", "मंगल": "Mars",
    "mercury": "Mercury", "budh": "Mercury", "बुध": "Mercury",
    "jupiter": "Jupiter", "guru": "Jupiter", "बृहस्पति": "Jupiter",
    "venus": "Venus", "shukra": "Venus", "शुक्र": "Venus",
    "saturn": "Saturn", "shani": "Saturn", "शनि": "Saturn",
    "rahu": "Rahu", "राहु": "Rahu",
    "ketu": "Ketu", "केतु": "Ketu",
}


def _coerce_planets_for_engine(raw: Any) -> list[dict[str, Any]] | None:
    """Normalize planets list/dict for marriage M17 (names + int houses)."""
    items: list[Any] = []
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        for key, val in raw.items():
            if isinstance(val, dict):
                row = dict(val)
                row.setdefault("name", key)
                items.append(row)
    if not items:
        return None
    out: list[dict[str, Any]] = []
    for p in items:
        if not isinstance(p, dict):
            continue
        name = p.get("name") or p.get("planet") or p.get("graha")
        if not isinstance(name, str) or not name.strip():
            continue
        canon = _PLANET_NAME_CANON.get(name.strip().lower(), name.strip())
        house = p.get("house")
        if house is not None and not isinstance(house, int):
            try:
                house = int(float(house))
            except (TypeError, ValueError):
                house = None
        row = dict(p)
        row["name"] = canon
        if house is not None:
            row["house"] = house
        out.append(row)
    return out if len(out) >= 7 else None


def normalize_kundli_chart_payload(raw: Any) -> dict[str, Any] | None:
    """Unwrap + normalize chart JSON for admin BCP recompute."""
    if not isinstance(raw, dict):
        return None
    chart = raw
    for key in ("kundli", "chart", "chart_data", "natal", "data"):
        nested = chart.get(key)
        if isinstance(nested, str):
            try:
                import json as _json

                nested = _json.loads(nested)
            except Exception:
                nested = None
        if isinstance(nested, dict):
            nested_planets = nested.get("planets")
            if isinstance(nested_planets, (list, dict)) and nested_planets:
                chart = nested
                break
    planets = _coerce_planets_for_engine(chart.get("planets"))
    if not planets:
        return None
    out = dict(chart)
    out["planets"] = planets
    return out


def coerce_chart_for_marriage_engine(raw: Any) -> dict[str, Any] | None:
    """Strict chart coerce for M17 ask-time (unwrap + planet normalize)."""
    if not isinstance(raw, dict):
        return None
    norm = normalize_kundli_chart_payload(raw)
    if norm is not None:
        return norm
    for key in ("kundli", "chart", "chart_data", "natal", "data"):
        nested = raw.get(key)
        if isinstance(nested, str):
            try:
                import json as _json

                nested = _json.loads(nested)
            except Exception:
                continue
        if isinstance(nested, dict):
            norm = normalize_kundli_chart_payload(nested)
            if norm is not None:
                return norm
    return None


def prepare_kundli_for_marriage_engine(raw: Any) -> dict[str, Any] | None:
    """Coerce chart + infer planet houses from lagna/sign (ask-time + admin)."""
    chart = coerce_chart_for_marriage_engine(raw)
    if chart is None:
        return None
    # Normalize dashas key (dasha → dashas) before any marriage engine read.
    raw_dashas = chart.get("dashas") or chart.get("dasha") or []
    if isinstance(raw_dashas, list) and raw_dashas and not chart.get("dashas"):
        chart = dict(chart)
        chart["dashas"] = raw_dashas
    lagna_si = _resolve_lagna_si_for_admin(chart)
    if lagna_si is None:
        return chart
    return _normalize_planet_houses(chart, lagna_si)


def _lagna_si_from_kundli(kundli: dict[str, Any]) -> int | None:
    for key in (
        "ascendantSignIndex", "ascendantSignIdx", "ascendant_sign_idx",
        "lagna_sign_idx", "lagnaSignIdx", "lagnaSignIndex",
    ):
        si = _sign_si_from_value(kundli.get(key))
        if si is not None:
            return si
    asc = kundli.get("ascendant") or kundli.get("lagna") or kundli.get("lagnaSign")
    if isinstance(asc, dict):
        for key in ("signIndex", "sign_idx", "signIdx", "sign"):
            si = _sign_si_from_value(asc.get(key))
            if si is not None:
                return si
    else:
        si = _sign_si_from_value(asc)
        if si is not None:
            return si
    for key in ("lagnaSign", "ascendant_sign", "ascendantSign"):
        si = _sign_si_from_value(kundli.get(key))
        if si is not None:
            return si
    for key in ("ascendantDeg", "ascendantLon", "ascendantLongitude", "lagnaLon"):
        v = kundli.get(key)
        if v is not None:
            try:
                return int(float(v) / 30.0) % 12
            except (TypeError, ValueError):
                pass
    return None


def _resolve_lagna_si_for_admin(chart: dict[str, Any]) -> int | None:
    """Lagna index for admin recompute — same fallbacks as marriage engine."""
    si = _lagna_si_from_kundli(chart)
    if si is not None:
        return si
    try:
        from event_timing.marriage.marriage_engine_v2 import _resolve_lagna_si_from_kundli

        return _resolve_lagna_si_from_kundli(chart)
    except Exception:
        return None


def _build_marriage_step_audit_from_chart(
    chart: dict[str, Any],
    birth: dict[str, Any] | None,
    user_age: int | None,
    *,
    bcp: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Steps 0–3 from saved chart (admin load when ask-time trace missing)."""
    lagna_si = _resolve_lagna_si_for_admin(chart)
    if lagna_si is None:
        return {}
    chart = _normalize_planet_houses(chart, lagna_si)
    try:
        from event_timing.marriage.kp_from_chart import resolve_kp

        kp = resolve_kp(
            chart,
            chart.get("kp") if isinstance(chart.get("kp"), dict) else {},
            birth,
        )
    except Exception:
        kp = {}

    audit: dict[str, Any] = {}

    try:
        from datetime import datetime

        from event_timing.marriage.marriage_engine_v2 import (
            _compute_age_at,
            _extract_dob_dt,
            _infer_birth_dt_from_age,
        )
        from event_timing.marriage.marriage_step0 import run_marriage_step0

        now = datetime.utcnow()
        age = user_age
        if age is None:
            age = _compute_age_at(birth or {}, now, kundli=chart)
        birth_dt = _extract_dob_dt(birth, kundli=chart)
        if birth_dt is None and age is not None:
            birth_dt = _infer_birth_dt_from_age(int(age), now)
        step0 = run_marriage_step0(
            chart, lagna_si, user_age=age, birth_dt=birth_dt, kp=kp, years_ahead=5,
        )
        audit["step0"] = {
            "name": "Early/Late + age context",
            "status": "DONE",
            "result": step0.get("step0_tendency") or {},
            "user_age": age,
            "recomputed_from_chart": True,
        }
    except Exception:
        pass

    try:
        from event_timing.marriage.marriage_spec_pipeline import safe_natal_step_audit

        for key, block in safe_natal_step_audit(chart, kp, lagna_si).items():
            if isinstance(block, dict):
                audit[key] = {**block, "recomputed_from_chart": True}
    except Exception:
        pass

    existing_s6 = audit.get("step6") if isinstance(audit.get("step6"), dict) else {}
    if not (existing_s6.get("selected_windows") or []):
        try:
            from event_timing.marriage.marriage_engine_v2 import build_marriage_step6_audit

            step6 = build_marriage_step6_audit(
                chart, step_audit=audit, birth=birth,
            )
            if step6.get("selected_windows"):
                audit["step6"] = {**step6, "recomputed_from_chart": True}
        except Exception:
            pass

    if isinstance(bcp, dict) and bcp:
        d9_bcp = bcp.get("d9_bcp") if isinstance(bcp.get("d9_bcp"), dict) else {}
        audit["step0a"] = {
            "name": "BCP ages + dasha scan plan",
            "status": "DONE",
            "d1_seventh_lord": bcp.get("seventh_lord"),
            "d9_seventh_lord": d9_bcp.get("seventh_lord"),
            "d1_7l_placement_house": bcp.get("seventh_lord_house"),
            "d1_7l_aspect_houses": _aspect_house_nums(bcp),
            "d9_7l_placement_house": d9_bcp.get("seventh_lord_house"),
            "d9_7l_aspect_houses": _aspect_house_nums(d9_bcp),
            "bcp_ages_next_years": list(bcp.get("future_priority_ages") or [])[:4],
            "focus_ages": list(bcp.get("focus_ages") or bcp.get("priority_marriage_ages") or [])[:6],
            "priority_ages": bcp.get("priority_marriage_ages") or [],
            "future_priority_ages": bcp.get("future_priority_ages") or [],
            "user_age": user_age,
            "recomputed_from_chart": True,
        }
    return audit


def _normalize_planet_houses(kundli: dict[str, Any], lagna_si: int) -> dict[str, Any]:
    out = dict(kundli)
    planets_out: list[dict[str, Any]] = []
    for p in kundli.get("planets") or []:
        if not isinstance(p, dict):
            continue
        row = dict(p)
        house = row.get("house")
        if not isinstance(house, int) or not (1 <= house <= 12):
            si = _sign_si_from_value(row.get("sign_idx") or row.get("signIndex"))
            if si is None:
                si = _sign_si_from_value(row.get("sign"))
            if si is not None:
                row["house"] = ((si - lagna_si) % 12) + 1
                row.setdefault("sign_idx", si)
        planets_out.append(row)
    out["planets"] = planets_out
    return out


def _resolve_d9_for_bcp(kundli: dict[str, Any]) -> tuple[int | None, list[dict[str, Any]]]:
    divs = kundli.get("divisionalCharts") or kundli.get("divisional_charts") or {}
    d9_chart = divs.get("D9") if isinstance(divs, dict) else None
    if isinstance(d9_chart, dict) and isinstance(d9_chart.get("planets"), list):
        d9_lagna = _sign_si_from_value(
            d9_chart.get("ascendantSignIndex")
            or d9_chart.get("ascendantSignIdx")
            or d9_chart.get("ascendant")
        )
        if d9_lagna is not None:
            d9_planets: list[dict[str, Any]] = []
            for p in d9_chart.get("planets") or []:
                if not isinstance(p, dict) or not p.get("name"):
                    continue
                row = dict(p)
                si = _sign_si_from_value(row.get("signIndex") or row.get("sign_idx") or row.get("sign"))
                if si is not None:
                    row.setdefault("sign_idx", si)
                    if not isinstance(row.get("house"), int):
                        row["house"] = ((si - d9_lagna) % 12) + 1
                d9_planets.append(row)
            if d9_planets:
                return d9_lagna, d9_planets
    try:
        from event_timing.marriage.marriage_step0 import _load_d9_planets

        return _load_d9_planets(kundli)
    except Exception:
        return None, []


def _user_age_from_admin_ctx(
    ctx: dict[str, Any],
    birth: dict[str, Any] | None,
    kundli: dict[str, Any],
) -> int | None:
    slice_meta = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    checks = ctx.get("checks") if isinstance(ctx.get("checks"), dict) else {}
    sm_checks = slice_meta.get("checks") if isinstance(slice_meta.get("checks"), dict) else {}
    for src in (sm_checks, checks):
        if isinstance(src, dict) and src.get("user_age") is not None:
            try:
                return int(src["user_age"])
            except (TypeError, ValueError):
                pass
    step_audit = slice_meta.get("step_audit") if isinstance(slice_meta.get("step_audit"), dict) else {}
    for key in ("step0", "step0a"):
        block = step_audit.get(key) if isinstance(step_audit, dict) else None
        if isinstance(block, dict) and block.get("user_age") is not None:
            try:
                return int(block["user_age"])
            except (TypeError, ValueError):
                pass
    try:
        from datetime import datetime

        from event_timing.marriage.marriage_engine_v2 import _compute_age_at

        return _compute_age_at(birth or {}, datetime.utcnow(), kundli=kundli)
    except Exception:
        return None


def _apply_bcp_recompute_to_ctx(
    ctx: dict[str, Any],
    linkage: dict[str, Any],
    evidence_lines: list[str],
    extra_step_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = dict(ctx)
    slice_meta = dict(out.get("slice_meta") or {}) if isinstance(out.get("slice_meta"), dict) else {}
    engine_facts = dict(out.get("engine_facts") or {}) if isinstance(out.get("engine_facts"), dict) else {}
    blocks = dict(out.get("blocks") or {}) if isinstance(out.get("blocks"), dict) else {}

    step_audit = dict(
        slice_meta.get("step_audit")
        or engine_facts.get("step_audit")
        or (blocks.get("engine_trace") or {}).get("step_audit")
        or {}
    )
    step0a = _force_merge_bcp_linkage_into_step0a(
        step_audit.get("step0a") if isinstance(step_audit.get("step0a"), dict) else {},
        linkage,
    )
    step_audit["step0a"] = step0a
    if isinstance(extra_step_audit, dict):
        for key, block in extra_step_audit.items():
            if not isinstance(block, dict):
                continue
            if key == "step0a":
                step_audit["step0a"] = _force_merge_bcp_linkage_into_step0a(
                    {**step_audit.get("step0a", {}), **block},
                    linkage,
                )
            else:
                existing = step_audit.get(key)
                if isinstance(existing, dict) and existing:
                    merged = dict(existing)
                    for fk, fv in block.items():
                        if fv is not None and merged.get(fk) in (None, "", [], {}):
                            merged[fk] = fv
                    if block.get("recomputed_from_chart"):
                        merged["recomputed_from_chart"] = True
                    step_audit[key] = merged
                else:
                    step_audit[key] = block
    slice_meta["step_audit"] = step_audit
    slice_meta["bcp_linkage"] = {**dict(slice_meta.get("bcp_linkage") or {}), **linkage}
    engine_facts["step_audit"] = step_audit

    trace = blocks.get("engine_trace") or blocks.get("marriage_engine_trace")
    if isinstance(trace, dict):
        trace = dict(trace)
        trace["step_audit"] = step_audit
        blocks["engine_trace"] = trace

    ev = list(engine_facts.get("evidence") or slice_meta.get("evidence") or [])
    for line in evidence_lines:
        if line and line not in ev:
            ev.append(line)
    if ev:
        engine_facts["evidence"] = ev
        slice_meta["evidence"] = ev

    out["slice_meta"] = slice_meta
    out["engine_facts"] = engine_facts
    out["blocks"] = blocks
    return out


def recompute_marriage_bcp_from_kundli(
    ctx: dict[str, Any],
    kundli: dict[str, Any],
    birth: dict[str, Any] | None = None,
    *,
    question_text: str = "",
    topic: str = "",
) -> dict[str, Any]:
    """Admin load: recompute Steps 0–3 from saved primary chart."""
    ctx = _bootstrap_marriage_admin_ctx(
        ctx if isinstance(ctx, dict) else {},
        question_text=question_text,
        topic=topic,
    )
    chart = prepare_kundli_for_marriage_engine(kundli) or coerce_chart_for_marriage_engine(kundli) or normalize_kundli_chart_payload(kundli)
    if chart is None:
        print(
            "[marriage_admin_recompute] skip: chart normalize failed "
            f"q={(question_text or ctx.get('question') or '')[:50]!r}",
            flush=True,
        )
        return ctx
    if not _should_recompute_marriage_admin(
        ctx, question_text=question_text, topic=topic,
    ):
        return ctx
    lagna_si = _resolve_lagna_si_for_admin(chart)
    if lagna_si is None:
        print(
            "[marriage_admin_recompute] skip: lagna_si missing "
            f"asc={chart.get('ascendant')!r} ascDeg={chart.get('ascendantDeg')!r} "
            f"q={(question_text or '')[:50]!r}",
            flush=True,
        )
        return ctx
    chart = _normalize_planet_houses(chart, lagna_si)
    user_age = _user_age_from_admin_ctx(ctx, birth, chart)
    bcp: dict[str, Any] | None = None
    linkage: dict[str, Any] = {}
    evidence_lines: list[str] = []
    try:
        from event_timing.marriage.bcp_marriage_ages import (
            bcp_linkage_admin_lines,
            compute_bcp_marriage_ages,
        )

        d9_lagna, d9_planets = _resolve_d9_for_bcp(chart)
        bcp = compute_bcp_marriage_ages(
            chart,
            lagna_si,
            user_age=user_age,
            d9_lagna_si=d9_lagna,
            d9_planets=d9_planets or None,
        )
        if user_age is not None:
            bcp["user_age"] = user_age
        d9_bcp = bcp.get("d9_bcp") if isinstance(bcp.get("d9_bcp"), dict) else {}
        fake: dict[str, Any] = {
            "bcp_marriage_ages": bcp,
            "user_age": user_age,
            "d1_seventh_lord": bcp.get("seventh_lord"),
            "d9_seventh_lord": d9_bcp.get("seventh_lord"),
            "step_audit": {
                "step0a": {
                    "d1_7l_placement_house": bcp.get("seventh_lord_house"),
                    "d1_7l_aspect_houses": _aspect_house_nums(bcp),
                    "d9_7l_placement_house": d9_bcp.get("seventh_lord_house"),
                    "d9_7l_aspect_houses": _aspect_house_nums(d9_bcp),
                    "bcp_ages_next_years": list(bcp.get("future_priority_ages") or [])[:4],
                    "user_age": user_age,
                }
            },
        }
        linkage = _marriage_bcp_linkage_snapshot(fake)
        evidence_lines = bcp_linkage_admin_lines(bcp) or _bcp_linkage_evidence_lines(linkage)
    except Exception as exc:
        print(
            f"[marriage_admin_recompute] BCP partial fail: {type(exc).__name__}: {str(exc)[:160]}",
            flush=True,
        )

    extra_audit = _build_marriage_step_audit_from_chart(
        chart, birth, user_age, bcp=bcp,
    )
    if not extra_audit:
        print(
            "[marriage_admin_recompute] step_audit empty after chart build "
            f"planets={len(chart.get('planets') or [])}",
            flush=True,
        )
        return ctx
    out = _apply_bcp_recompute_to_ctx(ctx, linkage, evidence_lines, extra_audit)
    sa = (
        (out.get("slice_meta") or {}).get("step_audit")
        if isinstance(out.get("slice_meta"), dict)
        else {}
    )
    print(
        "[marriage_admin_recompute] ok "
        f"step0={bool(sa.get('step0'))} step0a={bool(sa.get('step0a'))} "
        f"step3={bool(sa.get('step3'))} "
        f"step6={bool((sa.get('step6') or {}).get('selected_windows'))} "
        f"q={(question_text or '')[:40]!r}",
        flush=True,
    )
    return out


def _format_bcp_step2_lines_for_admin(
    step0a: dict[str, Any],
    user_age: int | None,
) -> list[str]:
    """Human-readable D1/D9 7L house + BCP age lines for admin Step 2."""
    try:
        from event_timing.marriage.bcp_marriage_ages import _future_ages_for_house
    except Exception:
        _future_ages_for_house = None  # type: ignore

    def _ages(house: int) -> list[int]:
        if _future_ages_for_house is not None:
            return list(_future_ages_for_house(house, user_age))
        ages = [house + 12 * i for i in range(8) if house + 12 * i <= 96]
        if user_age is not None:
            ages = [a for a in ages if a >= user_age]
        return ages[:4]

    display = step0a.get("bcp_house_display") if isinstance(step0a.get("bcp_house_display"), dict) else {}
    lines: list[str] = []
    for prefix, div_key, lord_key, sit_key, asp_key in (
        ("D1", "d1", "d1_seventh_lord", "d1_7l_placement_house", "d1_7l_aspect_houses"),
        ("D9", "d9", "d9_seventh_lord", "d9_7l_placement_house", "d9_7l_aspect_houses"),
    ):
        div = display.get(div_key) if isinstance(display.get(div_key), dict) else {}
        lord = step0a.get(lord_key) or div.get("seventh_lord") or "7L"
        chunks: list[str] = []
        items = div.get("items") if isinstance(div.get("items"), list) else []
        if items:
            for it in items:
                if not isinstance(it, dict) or not isinstance(it.get("house"), int):
                    continue
                h = int(it["house"])
                ages = it.get("ages") if isinstance(it.get("ages"), list) and it.get("ages") else _ages(h)
                age_str = ", ".join(str(a) for a in ages) if ages else "—"
                if it.get("type") == "placement":
                    chunks.append(f"baitha {h}H → ages {age_str}")
                else:
                    chunks.append(f"aspect {h}H → ages {age_str}")
        else:
            sit = step0a.get(sit_key)
            if sit is not None:
                try:
                    h = int(sit)
                    ages = _ages(h)
                    chunks.append(f"baitha {h}H → ages {', '.join(str(a) for a in ages) or '—'}")
                except (TypeError, ValueError):
                    pass
            asp = step0a.get(asp_key)
            if isinstance(asp, list):
                for h_raw in asp:
                    try:
                        h = int(h_raw)
                        ages = _ages(h)
                        chunks.append(f"aspect {h}H → ages {', '.join(str(a) for a in ages) or '—'}")
                    except (TypeError, ValueError):
                        continue
        lines.append(f"{prefix} {lord}: " + (" · ".join(chunks) if chunks else "—"))
    return lines


def build_marriage_bcp_step2_admin_payload(
    ctx: dict[str, Any],
    kundli: dict[str, Any],
    birth: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Top-level admin API block — Step 2 BCP houses + ages (chart recompute)."""
    merged = recompute_marriage_bcp_from_kundli(ctx, kundli, birth)
    step0a = {}
    slice_meta = merged.get("slice_meta") if isinstance(merged.get("slice_meta"), dict) else {}
    step_audit = slice_meta.get("step_audit") if isinstance(slice_meta.get("step_audit"), dict) else {}
    if isinstance(step_audit.get("step0a"), dict):
        step0a = step_audit["step0a"]
    if not step0a.get("d1_7l_placement_house") and not step0a.get("d9_7l_placement_house"):
        return None
    chart = normalize_kundli_chart_payload(kundli) or {}
    user_age = _user_age_from_admin_ctx(merged, birth, chart)
    linkage_lines = _format_bcp_step2_lines_for_admin(step0a, user_age)
    ages = list(step0a.get("bcp_ages_next_years") or step0a.get("focus_ages") or [])[:4]
    if not ages and user_age is not None:
        try:
            from event_timing.marriage.bcp_marriage_ages import _future_ages_for_house

            pool: list[int] = []
            for key in ("d1_7l_placement_house",):
                h = step0a.get(key)
                if isinstance(h, int):
                    pool.extend(_future_ages_for_house(h, user_age))
            for h in step0a.get("d1_7l_aspect_houses") or []:
                if isinstance(h, int):
                    pool.extend(_future_ages_for_house(h, user_age))
            ages = sorted({int(a) for a in pool if a >= user_age})[:4]
        except Exception:
            pass
    age_label = ", ".join(str(a) for a in ages) if ages else "—"
    detail = (
        f"age {user_age} se → {age_label}"
        if user_age is not None
        else age_label
    )
    return {
        "title": "Step 2 — BCP ages",
        "detail": detail,
        "ages": ages,
        "linkage_lines": linkage_lines,
        "user_age": user_age,
        "step0a": step0a,
        "recomputed_from_chart": True,
    }


def _enrich_step_audit_bcp_linkage(
    step_audit: dict[str, Any],
    engine_result: dict[str, Any],
) -> dict[str, Any]:
    linkage = _marriage_bcp_linkage_snapshot(engine_result)
    out = dict(step_audit or {})
    s0a = out.get("step0a") if isinstance(out.get("step0a"), dict) else {}
    out["step0a"] = _merge_bcp_linkage_into_step0a(s0a, linkage)
    return out


def _hydrate_marriage_bcp_linkage(ctx: dict[str, Any]) -> dict[str, Any]:
    """Fill Step 2 BCP house linkage for admin (incl. older saved rows)."""
    slice_meta = dict(ctx.get("slice_meta") or {}) if isinstance(ctx.get("slice_meta"), dict) else {}
    engine_facts = dict(ctx.get("engine_facts") or {}) if isinstance(ctx.get("engine_facts"), dict) else {}
    evidence = list(engine_facts.get("evidence") or slice_meta.get("evidence") or [])
    linkage = dict(slice_meta.get("bcp_linkage") or {})
    parsed = _parse_bcp_linkage_from_evidence(evidence)
    for key, val in parsed.items():
        if val is not None and not linkage.get(key):
            linkage[key] = val

    blocks = dict(ctx.get("blocks") or {}) if isinstance(ctx.get("blocks"), dict) else {}
    trace = blocks.get("engine_trace") if isinstance(blocks.get("engine_trace"), dict) else {}
    step_audit = dict(
        slice_meta.get("step_audit")
        or engine_facts.get("step_audit")
        or trace.get("step_audit")
        or {}
    )
    user_age = None
    checks = ctx.get("checks") if isinstance(ctx.get("checks"), dict) else {}
    sm_checks = slice_meta.get("checks") if isinstance(slice_meta.get("checks"), dict) else {}
    for src in (sm_checks, checks):
        if isinstance(src, dict) and src.get("user_age") is not None:
            try:
                user_age = int(src["user_age"])
                break
            except (TypeError, ValueError):
                pass
    step0 = step_audit.get("step0") if isinstance(step_audit.get("step0"), dict) else {}
    if user_age is None and step0.get("user_age") is not None:
        try:
            user_age = int(step0["user_age"])
        except (TypeError, ValueError):
            pass

    house_display = _rebuild_bcp_house_display(linkage, user_age)
    if house_display:
        linkage["bcp_house_display"] = house_display

    step0a = _merge_bcp_linkage_into_step0a(
        step_audit.get("step0a") if isinstance(step_audit.get("step0a"), dict) else {},
        linkage,
    )
    if step0a:
        step_audit["step0a"] = step0a
        slice_meta["step_audit"] = step_audit
        engine_facts["step_audit"] = step_audit
        if trace:
            trace = dict(trace)
            trace["step_audit"] = step_audit
            blocks["engine_trace"] = trace
    if linkage:
        slice_meta["bcp_linkage"] = linkage

    out = dict(ctx)
    out["slice_meta"] = slice_meta
    out["engine_facts"] = engine_facts
    out["blocks"] = blocks
    return out


def build_marriage_engine_trace(engine_result: dict[str, Any] | None) -> dict[str, Any] | None:
    """Trimmed marriage M17 audit for admin panel (step-by-step pipeline)."""
    if not isinstance(engine_result, dict) or not engine_result:
        return None
    step_audit = engine_result.get("step_audit")
    if not isinstance(step_audit, dict):
        step_audit = {}
    else:
        step_audit = _enrich_step_audit_bcp_linkage(step_audit, engine_result)
    timing_audit = engine_result.get("timing_audit")
    if not isinstance(timing_audit, dict):
        timing_audit = {}
    top_windows = engine_result.get("top_3_windows") or []
    if not isinstance(top_windows, list):
        top_windows = []
    factors = engine_result.get("factors") or []
    if not isinstance(factors, list):
        factors = []
    return normalize_engine_trace_transit_months({
        "engine": "marriage_timing_m17",
        "primary_window": engine_result.get("primary_window"),
        "backup_window": engine_result.get("backup_window"),
        "key_trigger": engine_result.get("key_trigger"),
        "verdict": engine_result.get("verdict"),
        "band": engine_result.get("band"),
        "user_age": engine_result.get("user_age"),
        "too_young_for_marriage": engine_result.get("too_young_for_marriage"),
        "transit_chart_context": engine_result.get("transit_chart_context"),
        "step_audit": step_audit,
        "step_order": list(_MARRIAGE_TRACE_STEP_ORDER),
        "timing_audit": timing_audit,
        "top_3_windows": top_windows[:3],
        "factors": factors[:50],
        "risk_flags": list(engine_result.get("risk_flags") or [])[:20],
    })


def _marriage_calculation_steps(engine_result: dict[str, Any]) -> list[str]:
    """High-signal lines for admin: how primary window was chosen."""
    out: list[str] = []
    top = (engine_result.get("top_3_windows") or [{}])[0]
    if isinstance(top, dict) and top.get("md"):
        out.append(
            f"Selected dasha: {top.get('md')}-{top.get('ad')}-{top.get('pd')} "
            f"({top.get('start_iso')} → {top.get('end_iso')}) "
            f"score={top.get('score')}"
        )
    pw = str(engine_result.get("primary_window") or "").strip()
    if pw:
        out.append(f"Answer window: {pw}")
    kt = str(engine_result.get("key_trigger") or "").strip()
    if kt:
        out.append(f"Trigger: {kt}")
    priority_keys = (
        "BCP_FLOOR", "BCP_ANCHOR", "BCP primary", "STEP0A BCP",
        "STEP0 verdict", "STEP0 age", "late_urgent", "AGE birth_dt",
        "STEP7", "STEP5.5", "STEP5 current",
    )
    for f in engine_result.get("factors") or []:
        fs = str(f).strip()
        if fs and any(k in fs for k in priority_keys) and fs not in out:
            out.append(fs)
    s0a = (engine_result.get("step0a") or {}).get("dasha_scan_plan") or {}
    if isinstance(s0a, dict):
        mode = s0a.get("timing_mode")
        pref = s0a.get("primary_reference_age")
        focus = s0a.get("bcp_focus_ages")
        if mode or pref:
            out.append(
                f"BCP plan: mode={mode} primary_age={pref} "
                f"focus={focus} late_urgent={s0a.get('late_urgent_scan')}"
            )
    return out[:24]


def _marriage_timing_evidence(engine_result: dict[str, Any]) -> list[str]:
    """Dasha/BCP/transit lines for admin evidence panel (M17 marriage timing)."""
    out: list[str] = []
    pw = str(engine_result.get("primary_window") or "").strip()
    if pw:
        out.append(f"Primary window: {pw}")
    linkage = _marriage_bcp_linkage_snapshot(engine_result)
    linkage_lines: list[str] = []
    try:
        from event_timing.marriage.bcp_marriage_ages import bcp_linkage_admin_lines

        bcp_raw = engine_result.get("bcp_marriage_ages")
        if not isinstance(bcp_raw, dict):
            s0a = engine_result.get("step0a")
            bcp_raw = (s0a.get("bcp_marriage_ages") if isinstance(s0a, dict) else None) or {}
        if isinstance(bcp_raw, dict) and bcp_raw.get("seventh_lord_house") is not None:
            linkage_lines = bcp_linkage_admin_lines(bcp_raw) or []
    except Exception:
        linkage_lines = []
    if not linkage_lines:
        linkage_lines = _bcp_linkage_evidence_lines(linkage)
    for line in linkage_lines:
        if line and line not in out:
            out.append(line)
    calc = _marriage_calculation_steps(engine_result)
    for line in calc:
        if line not in out:
            out.append(line)
    bw = str(engine_result.get("backup_window") or "").strip()
    if bw:
        out.append(f"Backup window: {bw}")
    kt = str(engine_result.get("key_trigger") or "").strip()
    if kt:
        out.append(f"Key trigger: {kt}")
    for f in engine_result.get("factors") or []:
        fs = str(f).strip()
        if fs and fs not in out:
            out.append(fs)
    timing_audit = engine_result.get("timing_audit")
    if isinstance(timing_audit, dict):
        for chk in timing_audit.get("checks") or []:
            if not isinstance(chk, dict):
                continue
            name = str(chk.get("name") or "check")
            detail = str(chk.get("detail") or chk.get("why") or "").strip()
            if detail:
                line = f"{name}: {detail}"
                if line not in out:
                    out.append(line)
        tr = timing_audit.get("transit")
        if isinstance(tr, dict) and tr.get("detail"):
            line = f"Transit: {tr['detail']}"
            if line not in out:
                out.append(str(line)[:240])
    step_audit = engine_result.get("step_audit")
    if isinstance(step_audit, dict):
        for key in _MARRIAGE_TRACE_STEP_ORDER:
            step = step_audit.get(key)
            if not isinstance(step, dict) or step.get("status") == "SKIP":
                continue
            parts: list[str] = []
            if step.get("name"):
                parts.append(str(step["name"]))
            for fld in ("detail", "verdict", "band"):
                if step.get(fld):
                    parts.append(str(step[fld]))
            if parts:
                line = f"{key}: " + " · ".join(parts)
                if line not in out:
                    out.append(line[:240])
            if len(out) >= 30:
                break
    return out[:40]


def build_marriage_timing_slice_meta(engine_result: dict[str, Any] | None) -> dict[str, Any]:
    """Admin slice_meta for marriage M17 timing (engine-only passthrough)."""
    if not isinstance(engine_result, dict) or not engine_result:
        return {}
    evidence = _marriage_timing_evidence(engine_result)
    calc_steps = _marriage_calculation_steps(engine_result)
    pw = str(engine_result.get("primary_window") or "").strip()
    verdict = str(engine_result.get("verdict") or engine_result.get("band") or "").strip()
    summary: list[str] = []
    if pw:
        summary.append(f"Marriage timing: {pw}")
    meta: dict[str, Any] = {
        "slice": "marriage_timing_m17",
        "topic": "marriage",
        "archetype": engine_result.get("bucket") or "general_mr",
        "verdict": verdict or ("answered:timing" if pw else ""),
        "summary": summary,
        "evidence": evidence,
        "timing_evidence": evidence,
        "calculation_steps": calc_steps,
        "checks": {
            "bucket": engine_result.get("bucket"),
            "band": engine_result.get("band"),
            "user_age": engine_result.get("user_age"),
        },
        "narrator_mode": "engine_only",
    }
    if isinstance(engine_result.get("step_audit"), dict):
        meta["step_audit"] = _enrich_step_audit_bcp_linkage(
            engine_result["step_audit"], engine_result,
        )
    linkage = _marriage_bcp_linkage_snapshot(engine_result)
    if linkage.get("d1_7l_placement_house") or linkage.get("d9_7l_placement_house"):
        meta["bcp_linkage"] = linkage
    if isinstance(engine_result.get("timing_audit"), dict):
        meta["timing_audit"] = engine_result["timing_audit"]
    return meta


def build_marriage_unavailable_admin_meta(
    *,
    partial_engine: dict[str, Any] | None = None,
    failure: str = "engine_empty",
    planets_count: int = 0,
) -> dict[str, Any]:
    """Admin slice_meta when M17 block is empty but we still want evidence lines."""
    if isinstance(partial_engine, dict) and partial_engine:
        meta = build_marriage_timing_slice_meta(partial_engine)
    else:
        meta = {
            "slice": "marriage_timing_m17",
            "topic": "marriage",
            "archetype": "general_mr",
            "verdict": "",
            "summary": [],
            "evidence": [],
            "timing_evidence": [],
            "calculation_steps": [],
            "narrator_mode": "engine_only",
        }
    diag: list[str] = []
    if failure == "chart_missing":
        diag.append(
            "Kundli/planets missing — marriage timing engine connect nahi ho paya. "
            "Profile me birth date, time aur place save karke dubara puchein."
        )
    else:
        diag.append(
            f"Marriage timing engine ne koi window return nahi ki "
            f"(planets={planets_count}). Server par latest code + restart check karein."
        )
    merged_evidence = diag + list(meta.get("evidence") or [])
    meta["evidence"] = merged_evidence[:50]
    meta["timing_evidence"] = merged_evidence[:50]
    meta["engine_unavailable"] = True
    meta["failure_reason"] = failure
    if not meta.get("summary"):
        meta["summary"] = [diag[0][:200]]
    return meta


def _enrich_engine_facts_from_blocks(
    engine_facts: dict[str, Any],
    blocks: dict[str, Any] | None,
) -> dict[str, Any]:
    """Fill engine_facts from engine_trace when slice_meta was empty (timing passthrough)."""
    if not isinstance(blocks, dict):
        return engine_facts
    trace = blocks.get("engine_trace") or blocks.get("marriage_engine_trace")
    if not isinstance(trace, dict):
        return engine_facts
    out = dict(engine_facts)
    pw = str(trace.get("primary_window") or "").strip()
    verdict = str(trace.get("verdict") or trace.get("band") or "").strip()
    if verdict and not out.get("verdict"):
        out["verdict"] = verdict
    elif pw and not out.get("verdict"):
        out["verdict"] = "answered:timing"
    evidence = list(out.get("evidence") or [])
    seen = set(evidence)
    if pw and f"Primary window: {pw}" not in seen:
        evidence.insert(0, f"Primary window: {pw}")
        seen.add(f"Primary window: {pw}")
    for f in trace.get("factors") or []:
        fs = str(f).strip()
        if fs and fs not in seen:
            evidence.append(fs)
            seen.add(fs)
    if len(evidence) < 3:
        fake = {
            "primary_window": pw,
            "factors": trace.get("factors") or [],
            "step_audit": trace.get("step_audit"),
            "timing_audit": trace.get("timing_audit"),
            "verdict": verdict,
            "band": trace.get("band"),
            "bcp_marriage_ages": trace.get("bcp_marriage_ages"),
            "step0a": (trace.get("step_audit") or {}).get("step0a"),
        }
        for line in _marriage_timing_evidence(fake):
            if line not in seen:
                evidence.append(line)
                seen.add(line)
    if evidence:
        out["evidence"] = evidence[:50]
        out["timing_evidence"] = evidence[:50]
    if pw and not out.get("summary"):
        out["summary"] = [f"Marriage timing: {pw}"]
    if trace.get("step_audit") and not out.get("step_audit"):
        out["step_audit"] = trace["step_audit"]
    return out


def build_engine_facts_snapshot(
    *,
    checks: dict[str, Any] | None = None,
    slice_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Structured engine facts the LLM was told to use (admin-only)."""
    checks = checks or {}
    slice_meta = slice_meta or {}
    nested = slice_meta.get("checks") if isinstance(slice_meta.get("checks"), dict) else {}
    out = {
        "archetype": slice_meta.get("archetype") or checks.get("archetype"),
        "verdict": slice_meta.get("verdict"),
        "summary": list(slice_meta.get("summary") or []),
        "evidence": list(slice_meta.get("evidence") or []),
        "evidence_positive": list(slice_meta.get("evidence_positive") or []),
        "evidence_negative": list(slice_meta.get("evidence_negative") or []),
        "evidence_neutral": list(slice_meta.get("evidence_neutral") or []),
        "ignore": list(slice_meta.get("ignore") or []),
        "love_score": nested.get("love_score"),
        "arrange_score": nested.get("arrange_score"),
        "verdict_public": nested.get("verdict_public"),
        "confidence_ratio": nested.get("confidence_ratio"),
    }
    if slice_meta.get("dasha_trace"):
        out["dasha_trace"] = slice_meta.get("dasha_trace")
    if not out["evidence"] and slice_meta.get("timing_evidence"):
        out["evidence"] = list(slice_meta.get("timing_evidence") or [])
    if slice_meta.get("timing_evidence"):
        out["timing_evidence"] = list(slice_meta.get("timing_evidence") or [])
    if slice_meta.get("calculation_steps"):
        out["calculation_steps"] = list(slice_meta.get("calculation_steps") or [])
    if slice_meta.get("step_audit"):
        out["step_audit"] = slice_meta.get("step_audit")
    return out


def _engine_ran_from_context(
    intent: dict[str, Any] | None,
    checks: dict[str, Any] | None,
) -> str | None:
    if isinstance(intent, dict):
        ran = str(intent.get("engine_ran") or "").strip()
        if ran:
            return ran
    er = checks.get("engine_route") if isinstance(checks, dict) else None
    if isinstance(er, dict):
        key = str(er.get("engine_key") or "").strip()
        return key or None
    return None


def _engine_route_reason_from_context(
    intent: dict[str, Any] | None,
    checks: dict[str, Any] | None,
) -> str | None:
    if isinstance(intent, dict):
        reason = str(intent.get("engine_route_reason") or "").strip()
        if reason:
            return reason
    er = checks.get("engine_route") if isinstance(checks, dict) else None
    if isinstance(er, dict):
        reason = str(er.get("reason") or "").strip()
        return reason or None
    return None


def _build_engine_verification_summary_for_ctx(
    question: str,
    *,
    llm_intent: dict[str, Any] | None,
    slice_meta: dict[str, Any] | None,
    checks: dict[str, Any] | None,
    is_timing: bool = False,
) -> dict[str, Any] | None:
    try:
        from ask_engine_verification import build_engine_verification_admin_summary

        er = checks.get("engine_route") if isinstance(checks, dict) else None
        intent = llm_intent if isinstance(llm_intent, dict) else {}
        return build_engine_verification_admin_summary(
            question,
            llm_intent=llm_intent,
            slice_meta=slice_meta,
            engine_route=er if isinstance(er, dict) else None,
            is_timing=is_timing or bool(intent.get("routed_timing")),
        )
    except Exception:
        return None


def build_admin_llm_context(
    *,
    question: str,
    route: str = "raw_passthrough",
    question_type: str = "STATIC",
    is_timing: bool = False,
    checks: dict[str, Any] | None = None,
    chart_text: str = "",
    system_prompt: str = "",
    extra_rules: str = "",
    user_payload: str = "",
    model: str = "",
    max_tokens: int | None = None,
    slice_meta: dict[str, Any] | None = None,
    blocks: dict[str, Any] | None = None,
    llm_called: bool = True,
    skip_reason: str = "",
    intent_source: str = "regex",
    llm_intent: dict[str, Any] | None = None,
    question_raw: str = "",
    question_normalized: str = "",
) -> dict[str, Any]:
    """Structured snapshot for admin panel (never shown to end users)."""
    _checks = checks or {}
    _slice_meta = slice_meta or {}
    answer_path, answer_path_label = derive_answer_path(
        llm_called=llm_called,
        skip_reason=skip_reason,
        checks=_checks,
        slice_meta=_slice_meta,
    )
    engine_facts = build_engine_facts_snapshot(checks=_checks, slice_meta=_slice_meta)
    engine_facts = _enrich_engine_facts_from_blocks(engine_facts, blocks or {})
    has_engine_facts = bool(
        engine_facts.get("verdict")
        or (engine_facts.get("evidence") or [])
        or (_slice_meta.get("verdict"))
        or (_slice_meta.get("evidence"))
        or (blocks or {}).get("engine_trace")
    )
    _intent = llm_intent if isinstance(llm_intent, dict) else {}
    try:
        from ask_question_understand import ensure_question_understanding

        _intent = ensure_question_understanding(
            question_normalized or question or "",
            _intent,
            force_llm=False,
            question_raw=question_raw or str(_intent.get("question_raw") or question or ""),
        )
    except Exception:
        if not _intent.get("question_summary"):
            try:
                from ask_intent_fidelity import summarize_question_one_line

                _intent = {**_intent, "question_summary": summarize_question_one_line(question, _intent)}
            except Exception:
                pass
    llm_intent = _intent or llm_intent
    _raw = str(
        question_raw or (_intent.get("question_raw") if isinstance(_intent, dict) else "") or question or ""
    ).strip()
    _norm = str(
        question_normalized
        or (_intent.get("question_normalized") if isinstance(_intent, dict) else "")
        or question
        or ""
    ).strip()
    _meaning = str(
        (_intent.get("question_meaning") if isinstance(_intent, dict) else "")
        or (_intent.get("question_summary") if isinstance(_intent, dict) else "")
        or ""
    ).strip()
    _typo_corrected = bool(_raw and _norm and _raw.lower() != _norm.lower())
    _understanding_source = str(
        (_intent.get("understanding_source") if isinstance(_intent, dict) else "") or ""
    ).strip() or None
    try:
        from ask_intent_fidelity import (
            build_question_understanding_detail,
            build_question_understanding_line,
            resolve_question_understood,
        )

        _engine_arch = str(_slice_meta.get("archetype") or engine_facts.get("archetype") or "")
        question_understood = resolve_question_understood(
            question,
            llm_intent,
            skip_reason=skip_reason,
            intent_source=intent_source,
            has_engine_facts=has_engine_facts,
            engine_archetype=_engine_arch,
        )
        understanding_line = build_question_understanding_line(
            question,
            llm_intent,
            skip_reason=skip_reason,
            intent_source=intent_source,
            has_engine_facts=has_engine_facts,
            engine_archetype=_engine_arch,
        )
        understanding_detail = build_question_understanding_detail(
            question,
            llm_intent,
            skip_reason=skip_reason,
            intent_source=intent_source,
            engine_archetype=_engine_arch,
        )
    except Exception:
        question_understood = ""
        understanding_line = ""
        understanding_detail = ""
    ctx_out = {
        "version": 1,
        "route": route,
        "question": (_norm or question or "")[:2000],
        "question_raw": (_raw[:2000] if _raw else None),
        "question_normalized": (_norm[:2000] if _typo_corrected else None),
        "question_meaning": (
            str(_intent.get("question_meaning") or _meaning or "").strip()[:2000] or None
        ),
        "question_scope": (
            str(_intent.get("question_scope") or "").strip().lower() or None
        ),
        "typo_corrected": _typo_corrected,
        "routed_domain": _intent.get("routed_domain") if isinstance(_intent, dict) else None,
        "routed_archetype": _intent.get("routed_archetype") if isinstance(_intent, dict) else None,
        "routed_timing": (_intent.get("routed_timing") if isinstance(_intent, dict) else None),
        "engine_ran": _engine_ran_from_context(
            _intent if isinstance(_intent, dict) else None,
            _checks,
        ),
        "engine_route_reason": _engine_route_reason_from_context(
            _intent if isinstance(_intent, dict) else None,
            _checks,
        ),
        "engine_verification": (
            _intent.get("engine_verification")
            if isinstance(_intent, dict) and _intent.get("engine_verification")
            else None
        ),
        "engine_verification_recovered": (
            _intent.get("engine_verification_recovered")
            if isinstance(_intent, dict)
            else None
        ),
        "engine_verification_summary": _build_engine_verification_summary_for_ctx(
            question,
            llm_intent=_intent if isinstance(_intent, dict) else None,
            slice_meta=_slice_meta,
            checks=_checks,
            is_timing=bool(is_timing),
        ),
        "understanding_source": _understanding_source,
        "question_type": question_type,
        "is_timing": bool(is_timing),
        "intent_source": intent_source or "regex",
        "question_understood": question_understood or None,
        "understanding_line": understanding_line,
        "understanding_detail": understanding_detail or None,
        "llm_intent": llm_intent or None,
        "llm_called": bool(llm_called),
        "answer_path": answer_path,
        "answer_path_label": answer_path_label,
        "engine_facts": engine_facts,
        "skip_reason": (skip_reason or "")[:200] or None,
        "checks": _checks,
        "slice_meta": _slice_meta,
        "blocks": blocks or {},
        "chart_text": chart_text or "",
        "extra_rules": extra_rules or "",
        "system_prompt": system_prompt or "",
        "user_payload": user_payload or "",
        "model": model or None,
        "max_tokens": max_tokens,
        "sizes": {
            "chart_chars": len(chart_text or ""),
            "system_prompt_chars": len(system_prompt or ""),
            "extra_rules_chars": len(extra_rules or ""),
            "user_payload_chars": len(user_payload or ""),
        },
    }
    try:
        from ask_engine_catalog import enrich_admin_context_engine_display

        ctx_out = enrich_admin_context_engine_display(ctx_out, llm_intent=_intent if isinstance(_intent, dict) else None)
    except Exception:
        pass
    return ctx_out


def _slim_marriage_step_audit_for_db(step_audit: dict[str, Any]) -> dict[str, Any]:
    """Keep marriage step_audit small enough for DB — never drop step3 planet list."""
    out: dict[str, Any] = {}
    for key in _MARRIAGE_TRACE_STEP_ORDER:
        step = step_audit.get(key)
        if not isinstance(step, dict):
            continue
        if key == "step3":
            planets = step.get("marriage_giving_planets") or []
            out[key] = {
                "name": step.get("name"),
                "status": step.get("status"),
                "merged_count": step.get("merged_count"),
                "common_planets": step.get("common_planets"),
                "planet_names": step.get("planet_names"),
                "marriage_giving_planets": planets[:16] if isinstance(planets, list) else [],
                "top_merged": (step.get("top_merged") or [])[:10],
            }
        elif key == "step4":
            out[key] = {
                "name": step.get("name"),
                "status": step.get("status"),
                "common_planets": step.get("common_planets") or [],
            }
        elif key == "step7":
            out[key] = {
                "name": step.get("name"),
                "status": step.get("status"),
                "transit_confirmed": step.get("transit_confirmed"),
                "double_transit": step.get("double_transit"),
                "transit_type": step.get("transit_type"),
                "transit_type_label": step.get("transit_type_label"),
                "chart_context": step.get("chart_context"),
                "jupiter_hit": step.get("jupiter_hit"),
                "saturn_hit": step.get("saturn_hit"),
                "months": step.get("months"),
                "detail": str(step.get("detail") or "")[:600],
            }
        elif key in ("step1", "step2"):
            out[key] = {
                "name": step.get("name"),
                "status": step.get("status"),
                "result": step.get("result") or {},
            }
        elif key == "step5":
            ranked = step.get("ranked_top") or []
            out[key] = {
                "name": step.get("name"),
                "status": step.get("status"),
                "weight_note": step.get("weight_note"),
                "ranked_top": ranked[:12] if isinstance(ranked, list) else [],
            }
        elif key == "step6":
            wins = step.get("selected_windows") or []
            out[key] = {
                "name": step.get("name"),
                "status": step.get("status"),
                "selected_windows": wins[:3] if isinstance(wins, list) else [],
                "future_candidates_count": step.get("future_candidates_count"),
                "current_activation": step.get("current_activation"),
            }
        else:
            out[key] = step
    return out


def _apply_slim_step_audit_to_ctx(payload: dict[str, Any]) -> dict[str, Any]:
    """Slim step_audit in all ctx locations before DB serialize."""
    out = dict(payload)
    for container_key in ("slice_meta",):
        container = out.get(container_key)
        if isinstance(container, dict) and isinstance(container.get("step_audit"), dict):
            c = dict(container)
            c["step_audit"] = _slim_marriage_step_audit_for_db(c["step_audit"])
            out[container_key] = c
    ef = out.get("engine_facts")
    if isinstance(ef, dict) and isinstance(ef.get("step_audit"), dict):
        ef = dict(ef)
        ef["step_audit"] = _slim_marriage_step_audit_for_db(ef["step_audit"])
        out["engine_facts"] = ef
    blocks = out.get("blocks")
    if isinstance(blocks, dict):
        blocks = dict(blocks)
        for trace_key in ("engine_trace", "marriage_engine_trace"):
            trace = blocks.get(trace_key)
            if isinstance(trace, dict) and isinstance(trace.get("step_audit"), dict):
                t = dict(trace)
                t["step_audit"] = _slim_marriage_step_audit_for_db(t["step_audit"])
                blocks[trace_key] = t
        out["blocks"] = blocks
    return out


def _compact_ctx_for_db(ctx: dict[str, Any]) -> dict[str, Any]:
    """Drop huge prompt blobs so blocks.engine_trace + evidence survive DB save."""
    out = _apply_slim_step_audit_to_ctx(ctx)
    out = dict(out)
    sizes = dict(out.get("sizes") or {})
    for key in _DB_STRIP_KEYS:
        val = str(out.get(key) or "")
        if val:
            sizes[f"{key}_chars"] = sizes.get(f"{key}_chars") or len(val)
            out[key] = ""
    out["sizes"] = sizes

    blocks = out.get("blocks")
    if isinstance(blocks, dict):
        blocks = dict(blocks)
        blocks.pop("chart_context", None)
        me = blocks.get("marriage_engine")
        if isinstance(me, str) and len(me) > 1500:
            blocks["marriage_engine"] = me[:1500] + "…"
        out["blocks"] = blocks

    ef = out.get("engine_facts")
    if isinstance(ef, dict):
        ef = dict(ef)
        for key in ("evidence", "timing_evidence"):
            arr = ef.get(key)
            if isinstance(arr, list) and len(arr) > 40:
                ef[key] = arr[:40]
        out["engine_facts"] = ef

    sm = out.get("slice_meta")
    if isinstance(sm, dict):
        sm = dict(sm)
        for key in ("evidence", "timing_evidence"):
            arr = sm.get(key)
            if isinstance(arr, list) and len(arr) > 40:
                sm[key] = arr[:40]
        out["slice_meta"] = sm

    return out


def _salvage_truncated_json(raw: str) -> dict[str, Any] | None:
    """Best-effort parse when an older row was truncated mid-string."""
    s = raw.strip()
    if not s.startswith("{"):
        return None
    try:
        data = json.loads(s)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    for suffix in ('"]}', '"}]}', '"}]}}', '"}]}}}', "}", ""):
        try:
            data = json.loads(s + suffix)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue
    return None


def _synthesize_engine_trace_from_meta(ctx: dict[str, Any]) -> dict[str, Any] | None:
    """Rebuild admin engine_trace when blocks were lost but slice_meta survived."""
    slice_meta = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    engine_facts = ctx.get("engine_facts") if isinstance(ctx.get("engine_facts"), dict) else {}
    checks = ctx.get("checks") if isinstance(ctx.get("checks"), dict) else {}
    step_audit = slice_meta.get("step_audit") or engine_facts.get("step_audit")
    timing_audit = slice_meta.get("timing_audit") or engine_facts.get("timing_audit")
    if not step_audit and not timing_audit:
        return None

    sl = str(
        slice_meta.get("slice")
        or checks.get("slice_type")
        or "marriage_timing_m17"
    ).strip()
    if sl == "timing_marriage_engine":
        sl = "marriage_timing_m17"

    pw = ""
    for item in (slice_meta.get("summary") or engine_facts.get("summary") or []):
        text = str(item)
        if "Marriage timing:" in text:
            pw = text.split("Marriage timing:", 1)[-1].strip()
            break
        if "–" in text or "-" in text:
            pw = text.strip()
            break
    if not pw:
        for line in (engine_facts.get("evidence") or slice_meta.get("evidence") or []):
            ls = str(line)
            if ls.lower().startswith("primary window:"):
                pw = ls.split(":", 1)[-1].strip()
                break
            if "Answer window:" in ls:
                pw = ls.split(":", 1)[-1].strip()
                break

    factors: list[str] = []
    for line in (engine_facts.get("evidence") or slice_meta.get("evidence") or []):
        fs = str(line).strip()
        if fs and fs not in factors:
            factors.append(fs)

    return normalize_engine_trace_transit_months({
        "engine": sl,
        "primary_window": pw or None,
        "backup_window": None,
        "verdict": slice_meta.get("verdict") or engine_facts.get("verdict"),
        "band": (slice_meta.get("checks") or {}).get("band") if isinstance(slice_meta.get("checks"), dict) else None,
        "step_audit": step_audit if isinstance(step_audit, dict) else {},
        "step_order": list(_MARRIAGE_TRACE_STEP_ORDER),
        "timing_audit": timing_audit if isinstance(timing_audit, dict) else {},
        "factors": factors[:50],
        "synthesized_from_meta": True,
    })


def _hydrate_admin_context_on_load(ctx: dict[str, Any]) -> dict[str, Any]:
    """Fill missing engine_trace / verification when loading saved rows."""
    out = dict(ctx)
    blocks = dict(out.get("blocks") or {}) if isinstance(out.get("blocks"), dict) else {}
    trace = blocks.get("engine_trace") or blocks.get("marriage_engine_trace")
    if not isinstance(trace, dict) or not (trace.get("step_audit") or trace.get("timing_audit")):
        synth = _synthesize_engine_trace_from_meta(out)
        if synth:
            blocks["engine_trace"] = synth
            out["blocks"] = blocks

    ev = out.get("engine_verification_summary")
    if not (isinstance(ev, dict) and ev.get("label")):
        slice_meta = out.get("slice_meta") if isinstance(out.get("slice_meta"), dict) else {}
        checks = out.get("checks") if isinstance(out.get("checks"), dict) else {}
        intent = out.get("llm_intent") if isinstance(out.get("llm_intent"), dict) else {}
        rebuilt = _build_engine_verification_summary_for_ctx(
            str(out.get("question") or intent.get("question_normalized") or ""),
            llm_intent=intent,
            slice_meta=slice_meta,
            checks=checks,
            is_timing=bool(out.get("is_timing") or out.get("question_type") == "TIMING"),
        )
        if rebuilt:
            out["engine_verification_summary"] = rebuilt

    try:
        from ask_engine_catalog import enrich_admin_context_engine_display

        intent = out.get("llm_intent") if isinstance(out.get("llm_intent"), dict) else {}
        out = enrich_admin_context_engine_display(out, llm_intent=intent)
    except Exception:
        pass
    return _hydrate_marriage_bcp_linkage(out)


def serialize_llm_context_for_db(ctx: Any) -> str | None:
    if not ctx:
        return None
    payload = ctx
    if isinstance(ctx, dict):
        payload = _compact_ctx_for_db(ctx)
    try:
        raw = json.dumps(payload, ensure_ascii=False, default=str)
    except Exception:
        return None
    if len(raw) > _MAX_DB_CHARS:
        if isinstance(payload, dict):
            payload = _compact_ctx_for_db(payload)
            try:
                raw = json.dumps(payload, ensure_ascii=False, default=str)
            except Exception:
                return None
        if len(raw) > _MAX_DB_CHARS and isinstance(payload, dict):
            payload = _apply_slim_step_audit_to_ctx(payload)
            blocks = payload.get("blocks")
            if isinstance(blocks, dict):
                blocks = dict(blocks)
                trace = blocks.get("engine_trace")
                if isinstance(trace, dict):
                    t = dict(trace)
                    t.pop("factors", None)
                    t.pop("top_3_windows", None)
                    blocks["engine_trace"] = t
                payload["blocks"] = blocks
            try:
                raw = json.dumps(payload, ensure_ascii=False, default=str)
            except Exception:
                return None
        if len(raw) > _MAX_DB_CHARS:
            return raw[: _MAX_DB_CHARS - 1] + "…"
    return raw


def refresh_stored_llm_context_understanding(ctx: dict[str, Any]) -> dict[str, Any]:
    """Re-run understanding repair when admin loads a saved row (no DB write)."""
    if not isinstance(ctx, dict):
        return ctx
    q = str(
        ctx.get("question_normalized")
        or ctx.get("question")
        or ""
    ).strip()
    intent = ctx.get("llm_intent") if isinstance(ctx.get("llm_intent"), dict) else {}
    if not q and isinstance(intent, dict):
        q = str(intent.get("question_normalized") or intent.get("question_echo") or "").strip()
    if not q:
        return ctx
    raw = str(ctx.get("question_raw") or intent.get("question_raw") or q).strip()
    try:
        from ask_question_understand import ensure_question_understanding

        refreshed = ensure_question_understanding(q, dict(intent), force_llm=False, question_raw=raw)
    except Exception:
        return ctx
    out = dict(ctx)
    out["llm_intent"] = refreshed
    for key in (
        "question_meaning",
        "question_scope",
        "understanding_line",
        "understanding_detail",
        "understanding_source",
        "question_understood",
        "question_summary",
    ):
        if refreshed.get(key) is not None:
            out[key] = refreshed.get(key)
    try:
        from ask_engine_catalog import enrich_admin_context_engine_display

        out = enrich_admin_context_engine_display(out, llm_intent=refreshed)
    except Exception:
        pass
    return _hydrate_admin_context_on_load(out)


def parse_llm_context_from_db(
    raw: str | None,
    *,
    refresh_understanding: bool = False,
) -> dict[str, Any] | None:
    if not raw or not str(raw).strip():
        return None
    try:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = _salvage_truncated_json(str(raw))
            if not data:
                salvaged = _salvage_truncated_json(str(raw)[:79_999])
                if salvaged:
                    data = salvaged
                else:
                    return {"raw": str(raw)[:8000]}
        if not isinstance(data, dict):
            return None
        blocks = data.get("blocks")
        if isinstance(blocks, dict):
            for key in ("engine_trace", "marriage_engine_trace"):
                tr = blocks.get(key)
                if isinstance(tr, dict):
                    blocks[key] = normalize_engine_trace_transit_months(tr)
        data = _hydrate_admin_context_on_load(data)
        if refresh_understanding:
            return refresh_stored_llm_context_understanding(data)
        return data
    except Exception:
        salvaged = _salvage_truncated_json(str(raw))
        if salvaged:
            return _hydrate_admin_context_on_load(salvaged)
        return {"raw": str(raw)[:8000]}

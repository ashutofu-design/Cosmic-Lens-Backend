"""Vivah-style Kaal Pipeline shell — step0–step8 for all 16 timing domains.

Marriage M17 already emits a full audit; generic engines use dasha-first step1–6
and this module adds step0, step0a, step7, step8 (saal/mahina) for admin parity.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from event_timing._shared.step_audit import (
    GENERIC_KAAL_STEP_ORDER,
    kaal_step_order_for_domain,
    prune_generic_kaal_steps,
    _lords_from_window,
    _window_range,
)
from event_timing.domain_specs import get_domain_spec

KAAL_PIPELINE_STEP_ORDER: tuple[str, ...] = GENERIC_KAAL_STEP_ORDER

KAAL_PIPELINE_DOMAINS: tuple[str, ...] = (
    "marriage",
    "love",
    "career",
    "travel",
    "property",
    "vehicle",
    "finance",
    "health",
    "children",
    "education",
    "foreign_education",
    "litigation",
    "spiritual",
    "fame",
    "network",
    "universal",
)

_MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def is_kaal_pipeline_domain(domain: str) -> bool:
    return str(domain or "").strip().lower() in KAAL_PIPELINE_DOMAINS


def parse_iso_month_year(iso: str) -> tuple[Optional[str], Optional[int]]:
    """Return (month_name, year) from YYYY-MM or YYYY-MM-DD."""
    raw = str(iso or "").strip()
    if len(raw) < 7:
        return None, None
    try:
        if len(raw) >= 10:
            dt = datetime.strptime(raw[:10], "%Y-%m-%d")
        else:
            dt = datetime.strptime(raw[:7], "%Y-%m")
        return _MONTH_NAMES[dt.month - 1], dt.year
    except ValueError:
        return None, None


def human_month_year(iso: str) -> str:
    month, year = parse_iso_month_year(iso)
    if month and year:
        return f"{month} {year}"
    return str(iso or "").strip()


def _event_kab_label(domain: str) -> str:
    spec = get_domain_spec(domain)
    label = str(spec.get("label") or domain).split("/")[0].strip()
    if domain == "marriage":
        return "Marriage kab"
    return f"{label} kab"


def _pick_primary_window(result: dict, step_audit: dict) -> tuple[str, str, str]:
    """Return (primary_window, start_iso, end_iso)."""
    pw = str(result.get("primary_window") or "").strip()
    answer = result.get("answer_window") if isinstance(result.get("answer_window"), dict) else {}
    cw = result.get("current_window") if isinstance(result.get("current_window"), dict) else {}
    s4 = step_audit.get("step4") if isinstance(step_audit.get("step4"), dict) else {}
    s6 = step_audit.get("step6") if isinstance(step_audit.get("step6"), dict) else {}
    s8 = step_audit.get("step8") if isinstance(step_audit.get("step8"), dict) else {}

    start_iso = (
        str(answer.get("start_iso") or answer.get("start") or "")
        or str(s8.get("primary_dasha", {}).get("start_iso") or "")
        or str(s4.get("current_start") or "")
        or str(cw.get("start_iso") or cw.get("start") or "")
        or str(s6.get("next_start") or "")
    ).strip()
    end_iso = (
        str(answer.get("end_iso") or answer.get("end") or "")
        or str(s8.get("primary_dasha", {}).get("end_iso") or "")
        or str(s4.get("current_end") or "")
        or str(cw.get("end_iso") or cw.get("end") or "")
        or str(s6.get("next_end") or "")
    ).strip()

    if not pw:
        pw = _window_range(answer) or _window_range(s4) or _window_range(cw)
        if not pw and start_iso and end_iso:
            pw = f"{start_iso}→{end_iso}"
        elif not pw and start_iso:
            pw = human_month_year(start_iso) or start_iso

    return pw, start_iso, end_iso


def build_kaal_step0(result: dict, domain: str) -> dict[str, Any]:
    spec = get_domain_spec(domain)
    prac = result.get("practicality") if isinstance(result.get("practicality"), dict) else {}
    user_age = result.get("user_age") or prac.get("user_age")
    bucket = str(result.get("bucket") or "general")
    detail_parts = [
        f"{spec.get('label', domain)} · bucket={bucket}",
    ]
    if user_age is not None:
        detail_parts.append(f"age {user_age}")
    if result.get("verdict"):
        detail_parts.append(str(result.get("verdict")))

    return {
        "name": f"Step 0 — {spec.get('label', domain)} context",
        "status": "DONE",
        "user_age": user_age,
        "bucket": bucket,
        "domain": domain,
        "result": {
            "verdict": result.get("verdict"),
            "band": result.get("band"),
            "domain": domain,
            "bucket": bucket,
        },
        "detail": " · ".join(detail_parts).strip(),
    }


def build_kaal_step0a(result: dict, domain: str, step_audit: dict) -> dict[str, Any]:
    """Marriage-only BCP focus ages (7L D1+D9). Other domains must not use vivah BCP."""
    spec = get_domain_spec(domain)
    s2 = step_audit.get("step2") if isinstance(step_audit.get("step2"), dict) else {}
    targets = s2.get("dasha_targets") or spec.get("dasha_targets") or []
    prac = result.get("practicality") if isinstance(result.get("practicality"), dict) else {}

    focus: list[Any] = []
    bcp_raw: dict[str, Any] = {}
    if domain == "marriage":
        bcp_raw = result.get("bcp_marriage_ages")
        if not isinstance(bcp_raw, dict):
            s0a = result.get("step0a")
            bcp_raw = (s0a.get("bcp_marriage_ages") if isinstance(s0a, dict) else None) or {}
        if isinstance(bcp_raw, dict):
            for key in ("d1_bcp_ages", "d9_bcp_ages", "focus_ages", "future_priority_ages"):
                ages = bcp_raw.get(key)
                if isinstance(ages, list) and ages:
                    focus.extend(ages[:12])
    if not focus and prac.get("min_purchase_age") is not None:
        focus = [prac.get("min_purchase_age")]

    return {
        "name": f"Step 0a — Focus ages / BCP ({domain})" if domain == "marriage" else f"Step 0a — Focus ages ({domain})",
        "status": "DONE" if focus or targets else "PARTIAL",
        "dasha_targets": list(targets)[:8],
        "focus_ages": sorted({int(a) for a in focus if a is not None})[:16] if focus else [],
        "timing_mode": (bcp_raw or {}).get("timing_mode") if isinstance(bcp_raw, dict) else None,
        "detail": (
            f"targets {', '.join(str(t) for t in targets[:5]) or '—'}"
            + (
                f" · focus ages {', '.join(str(a) for a in sorted({int(a) for a in focus if a is not None})[:8])}"
                if focus
                else ""
            )
        ).strip(),
    }


_MARRIAGE_ONLY_STEP8_KEYS = (
    "marriage_period",
    "marriage_month_year",
    "marriage_year",
    "marriage_month",
    "late_chart_bcp_locked",
    "d1_bcp_ages",
    "d9_bcp_ages",
    "predicted_bcp_age",
    "next_dasha_window",
    "dasha_transit_month",
    "step5_aligned_lords",
)


def _strip_marriage_step8_fields(step8: dict[str, Any]) -> dict[str, Any]:
    out = dict(step8)
    for key in _MARRIAGE_ONLY_STEP8_KEYS:
        out.pop(key, None)
    return out


def build_kaal_step7(result: dict, domain: str, step_audit: dict) -> dict[str, Any]:
    existing = step_audit.get("step7")
    if isinstance(existing, dict) and (
        existing.get("transit_confirmed") is not None
        or existing.get("chart_context")
        or existing.get("by_month")
    ):
        return existing

    dt = result.get("double_transit") if isinstance(result.get("double_transit"), dict) else {}
    s6 = step_audit.get("step6") if isinstance(step_audit.get("step6"), dict) else {}
    transit_detail = str(s6.get("transit_detail") or s6.get("detail") or "").strip()
    spec = get_domain_spec(domain)
    transits = spec.get("transits") or []

    return {
        "name": f"Step 7 — Transit verify ({domain})",
        "status": "DONE" if dt or transit_detail else "PARTIAL",
        "transit_confirmed": bool(dt.get("active")),
        "double_transit": dt,
        "transit_rules": transits[:4],
        "detail": transit_detail or f"double-transit {dt.get('verdict', 'scan')}",
    }


def build_kaal_step8(result: dict, domain: str, step_audit: dict) -> dict[str, Any]:
    existing = step_audit.get("step8")
    if isinstance(existing, dict) and (
        existing.get("marriage_month_year")
        or existing.get("event_month_year")
        or existing.get("final_prediction")
    ):
        out = dict(existing)
        if domain == "marriage":
            if not out.get("event_month_year") and out.get("marriage_month_year"):
                out["event_month_year"] = out["marriage_month_year"]
            if not out.get("event_year") and out.get("marriage_year"):
                out["event_year"] = out["marriage_year"]
            if not out.get("event_month") and out.get("marriage_month"):
                out["event_month"] = out["marriage_month"]
        else:
            out = _strip_marriage_step8_fields(out)
        return out

    pw, start_iso, end_iso = _pick_primary_window(result, step_audit)
    answer = result.get("answer_window") if isinstance(result.get("answer_window"), dict) else {}
    if domain != "marriage" and answer.get("start_iso"):
        start_iso = str(answer["start_iso"])
        end_iso = str(answer.get("end_iso") or end_iso or "")
        month, year = parse_iso_month_year(start_iso)
        month_year = human_month_year(start_iso) if month and year else pw
    else:
        month, year = parse_iso_month_year(start_iso)
        month_year = human_month_year(start_iso) if month and year else pw

    cw = result.get("current_window") if isinstance(result.get("current_window"), dict) else {}
    answer = result.get("answer_window") if isinstance(result.get("answer_window"), dict) else {}
    s4 = step_audit.get("step4") if isinstance(step_audit.get("step4"), dict) else {}
    primary_dasha = {
        "md": answer.get("md") or cw.get("md") or s4.get("md"),
        "ad": answer.get("ad") or cw.get("ad") or s4.get("ad"),
        "pd": answer.get("pd") or cw.get("pd") or s4.get("pd"),
        "lords": _lords_from_window(answer) or _lords_from_window(cw) or s4.get("current_lords"),
        "start_iso": start_iso or None,
        "end_iso": end_iso or None,
        "window": pw or _window_range(answer) or _window_range(cw) or _window_range(s4),
    }

    dt = result.get("double_transit") if isinstance(result.get("double_transit"), dict) else {}
    event_label = _event_kab_label(domain)

    out: dict[str, Any] = {
        "name": f"Step 8 — Final Kaal ({domain})",
        "status": "DONE" if month_year else "PARTIAL",
        "verdict": result.get("verdict"),
        "band": result.get("band"),
        "domain": domain,
        "primary_window": pw,
        "event_month_year": month_year,
        "event_year": year,
        "event_month": month,
        "primary_dasha": primary_dasha,
        "transit_confirmed": bool(dt.get("active")),
        "final_prediction": (
            f"{primary_dasha.get('lords') or '—'} → {month_year or pw or '—'}"
            if primary_dasha.get("lords") or month_year
            else None
        ),
        "detail": f"{event_label}: {month_year or '—'} · {result.get('verdict') or '—'}",
    }
    if domain == "marriage":
        out["marriage_period"] = pw or month_year
        out["marriage_month_year"] = month_year
        out["marriage_year"] = year
        out["marriage_month"] = month
    return out


def expand_to_kaal_pipeline(result: dict, domain: str) -> dict:
    """Ensure step_audit has Kaal Pipeline step0–step8 for admin display."""
    if not isinstance(result, dict):
        return result
    domain = str(domain or result.get("domain") or "").strip().lower()
    if not domain:
        return result

    bucket = str(result.get("bucket") or "").strip().lower()
    skip_bcp_shell = domain == "career" and bucket == "promotion"

    step_audit = result.get("step_audit")
    if not isinstance(step_audit, dict):
        step_audit = {}
    else:
        step_audit = dict(step_audit)

    # Marriage / career may already ship rich step0–step8(+); only fill gaps.
    if not step_audit.get("step0"):
        step_audit["step0"] = build_kaal_step0(result, domain)
    if domain == "marriage":
        # Vivah BCP step0a — marriage engine only.
        if not step_audit.get("step0a"):
            step_audit["step0a"] = build_kaal_step0a(result, domain, step_audit)
        if not step_audit.get("step7") or not str((step_audit.get("step7") or {}).get("detail") or "").strip():
            merged7 = build_kaal_step7(result, domain, step_audit)
            if isinstance(step_audit.get("step7"), dict):
                merged7 = {**step_audit["step7"], **{k: v for k, v in merged7.items() if v is not None}}
            step_audit["step7"] = merged7
    else:
        # Generic timing: no KP row, no BCP shell, no duplicate transit verify.
        step_audit = prune_generic_kaal_steps(step_audit, domain)

    # Career owns step8 (next AD / window merge). Vivah month-year shell is marriage-only.
    if domain != "career":
        s8 = build_kaal_step8(result, domain, step_audit)
        if isinstance(step_audit.get("step8"), dict):
            prev = step_audit["step8"]
            s8 = {**prev, **s8}
        if domain != "marriage":
            s8 = _strip_marriage_step8_fields(s8)
        step_audit["step8"] = s8
    else:
        s8 = step_audit.get("step8") if isinstance(step_audit.get("step8"), dict) else {}
        if s8:
            s8 = _strip_marriage_step8_fields(s8)
            step_audit["step8"] = s8

    if skip_bcp_shell:
        try:
            from event_timing.career.career_timing import (
                career_step_order_for_bucket,
                finalize_promotion_admin_step_audit,
            )

            step_audit = finalize_promotion_admin_step_audit(
                step_audit,
                bucket=bucket,
                tense=str(result.get("tense") or "general"),
            )
            result["step_order"] = list(career_step_order_for_bucket(bucket))
        except Exception:
            step_audit.pop("step0a", None)
            step_audit.pop("step1", None)
            step_audit.pop("step4", None)

    result["step_audit"] = step_audit
    result["step_order"] = list(
        result.get("step_order") or kaal_step_order_for_domain(domain)
    )
    result["pipeline_format"] = "kaal_v1"
    # Promote primary_window for trace/outcome box when missing.
    if not result.get("primary_window"):
        if domain == "career":
            tw = result.get("timing_window") if isinstance(result.get("timing_window"), dict) else {}
            nxt = tw.get("next_career") if isinstance(tw.get("next_career"), dict) else {}
            if nxt.get("promotion_timeline"):
                result["primary_window"] = str(nxt["promotion_timeline"])[:200]
            elif nxt.get("start") and nxt.get("end"):
                result["primary_window"] = f"{nxt['start']}→{nxt['end']}"
            elif isinstance(s8, dict) and s8.get("promotion_timeline"):
                result["primary_window"] = str(s8["promotion_timeline"])[:200]
            elif isinstance(s8, dict) and s8.get("detail"):
                result["primary_window"] = str(s8["detail"])[:160]
        else:
            pw = s8.get("primary_window") or s8.get("event_month_year")
            if pw:
                result["primary_window"] = pw
    return result

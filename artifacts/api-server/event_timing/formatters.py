"""Format timing engine output for LLM narrator LOCKED blocks."""
from __future__ import annotations

from typing import Any


def format_travel_block(v: dict) -> str:
    if not isinstance(v, dict) or not v:
        return ""
    lines = [
        "════════════════ TRAVEL TIMING ENGINE (LOCKED) ════════════════",
        f"Verdict: {v.get('verdict', '?')} | Band: {v.get('band', '?')}",
        f"Foreign promised: {v.get('foreign_promised', '?')}",
        f"Recommendation: {v.get('recommendation_tier', '?')}",
    ]
    cw = v.get("current_window") or {}
    if cw:
        lines.append(
            f"Current window: {cw.get('start_iso', '?')} → {cw.get('end_iso', '?')} "
            f"({cw.get('severity', '')})"
        )
    nxt = v.get("next_3_windows") or []
    if nxt:
        lines.append("Next windows:")
        for w in nxt[:3]:
            if isinstance(w, dict):
                lines.append(
                    f"  • {w.get('md', '?')}/{w.get('ad', '?')} "
                    f"{w.get('start_iso', '?')}→{w.get('end_iso', '?')} "
                    f"score={w.get('score', '?')}"
                )
    factors = v.get("factors") or []
    if factors:
        lines.append("Top factors:")
        for f in factors[:6]:
            lines.append(f"  • {f}")
    guards = v.get("llm_directives") or []
    if guards:
        lines.append("NARRATOR GUARDS:")
        for g in guards[:5]:
            lines.append(f"  • {g}")
    lines.append("⛔ NO visa guarantee | NO country naming | probability window only")
    lines.append("══════════════════════════════════════════════════════════════")
    return "\n".join(lines)


def format_engine_window_block(v: dict, domain_title: str, label: str = "") -> str:
    """Generic LOCKED block for finance/health/children window engines."""
    if not isinstance(v, dict) or not v:
        return ""
    title = domain_title.replace("_", " ").strip()
    lines = [
        f"════════════════ {title} TIMING ENGINE (LOCKED) ════════════════",
        f"Focus: {label or title}",
        f"Verdict: {v.get('verdict', '?')} | Band: {v.get('band', '?')}",
    ]
    if v.get("recommendation_tier"):
        lines.append(f"Recommendation: {v.get('recommendation_tier')}")
    cw = v.get("current_window") or {}
    if cw:
        lines.append(
            f"Current window: {cw.get('start_iso', '?')} → {cw.get('end_iso', '?')} "
            f"({cw.get('severity', cw.get('md', ''))})"
        )
    nxt = v.get("next_3_windows") or []
    if nxt:
        lines.append("Next windows:")
        for w in nxt[:3]:
            if isinstance(w, dict):
                lines.append(
                    f"  • {w.get('md', '?')}/{w.get('ad', '?')} "
                    f"{w.get('start_iso', '?')}→{w.get('end_iso', '?')} "
                    f"score={w.get('score', '?')}"
                )
    factors = v.get("factors") or []
    if factors:
        lines.append("Top factors:")
        for f in factors[:6]:
            lines.append(f"  • {f}")
    guards = v.get("llm_directives") or v.get("brand_safety_warnings") or []
    if guards:
        lines.append("NARRATOR GUARDS:")
        for g in guards[:5]:
            lines.append(f"  • {g}")
    lines.append("⛔ Probability window only — no guaranteed outcome")
    lines.append("══════════════════════════════════════════════════════════════")
    return "\n".join(lines)


def format_spec_directive_block(domain: str, spec: dict, bucket: str = "") -> str:
    """Emit step checklist when full engine not yet wired."""
    if not spec:
        return ""
    lines = [
        f"=== TIMING SPEC ({domain.upper()}) — ENGINE {spec.get('status', '?').upper()} ===",
        f"Focus: {spec.get('label', domain)}",
    ]
    if bucket:
        lines.append(f"Bucket: {bucket}")
    lines.append(f"Houses: {', '.join(str(h) for h in spec.get('houses', []))}")
    lines.append(f"Dasha targets: {', '.join(spec.get('dasha_targets', []))}")
    lines.append("Pipeline:")
    for step in spec.get("pipeline_steps", [])[:8]:
        lines.append(f"  • {step}")
    lines.append(f"User wants: {spec.get('user_wants', '')}")
    for g in (spec.get("guards") or [])[:4]:
        lines.append(f"  GUARD: {g}")
    if spec.get("status") != "ready":
        lines.append(
            "NOTE: Full deterministic window pending — cite dasha/transit from chart "
            "using spec above; do NOT invent exact dates."
        )
    return "\n".join(lines)


def format_pipeline_audit(ctx: dict) -> str:
    """Compact audit trail for admin/debug."""
    if not isinstance(ctx, dict):
        return ""
    d = ctx.get("demand") or {}
    lines = [
        "TIMING_ROUTE:",
        f"  domain={d.get('domain')} bucket={d.get('bucket')} "
        f"timing={d.get('is_timing')} engine={ctx.get('engine_id')} "
        f"status={ctx.get('engine_status')}",
    ]
    for f in (ctx.get("factors") or [])[:5]:
        lines.append(f"  factor: {f}")
    return "\n".join(lines)

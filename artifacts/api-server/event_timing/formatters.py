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
    answer = v.get("answer_window") if isinstance(v.get("answer_window"), dict) else {}
    if answer and answer.get("start_iso") != (cw or {}).get("start_iso"):
        lines.append(
            f"PRIMARY answer window (rank #1): {answer.get('md', '?')}/{answer.get('ad', '?')}/"
            f"{answer.get('pd', '?')} {answer.get('start_iso', '?')}→{answer.get('end_iso', '?')} "
            f"score={answer.get('score', '?')}"
        )
    periods = v.get("timing_periods") if isinstance(v.get("timing_periods"), list) else []
    if periods:
        lines.append("Ranked timing periods (default = #1 only):")
        for p in periods[:3]:
            if isinstance(p, dict):
                lines.append(
                    f"  #{p.get('rank', '?')} {p.get('lords', '?')} "
                    f"{p.get('start_iso', '?')}→{p.get('end_iso', '?')} "
                    f"score={p.get('score', '?')}"
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


def format_engine_window_block(
    v: dict,
    domain_title: str,
    label: str = "",
    question: str = "",
) -> str:
    """Generic LOCKED block for finance/health/children window engines."""
    if not isinstance(v, dict) or not v:
        return ""
    from event_timing._shared.timing_window_pick import (
        extract_ranked_timing_windows,
        locked_window_instruction,
        narrate_window_line,
    )

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
    ranked = extract_ranked_timing_windows(v)
    if ranked:
        lines.append("Ranked dasha windows (use pick rule below):")
        for i, w in enumerate(ranked[:3]):
            lines.append(f"  {narrate_window_line(w, i + 1)}")
    else:
        nxt = v.get("next_3_windows") or []
        if nxt:
            lines.append("Next windows:")
            for i, w in enumerate(nxt[:3]):
                if isinstance(w, dict):
                    lines.append(
                        f"  • #{i + 1} {w.get('md', '?')}/{w.get('ad', '?')} "
                        f"{w.get('start_iso', '?')}→{w.get('end_iso', '?')} "
                        f"score={w.get('score', '?')}"
                    )
    lock = locked_window_instruction(v, question)
    if lock:
        lines.append(lock)
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


def format_baby_timing_for_prompt(v: dict, question: str = "") -> str:
    """LOCKED narrator block — D7 delay tone first, then dasha windows."""
    if not isinstance(v, dict) or not v:
        return ""
    block = format_engine_window_block(
        v,
        "CHILDREN / BABY",
        "conception & childbirth timing",
        question,
    )
    extra: list[str] = []
    d7 = v.get("d7_picture") if isinstance(v.get("d7_picture"), dict) else {}
    if d7.get("available"):
        fl = d7.get("first_lord") if isinstance(d7.get("first_lord"), dict) else {}
        f5 = d7.get("fifth_lord") if isinstance(d7.get("fifth_lord"), dict) else {}
        flags = d7.get("flags") if isinstance(d7.get("flags"), dict) else {}
        extra.append("D7 SAPTAMSHA (progeny — check delay/late BEFORE dasha):")
        extra.append(
            f"  D7 lagna {d7.get('d7_lagna') or '?'} · "
            f"1L {fl.get('planet') or '?'}@{fl.get('house_in_d7') or '?'}H "
            f"({fl.get('dignity') or '?'})"
        )
        extra.append(
            f"  D7 5L {f5.get('planet') or '?'}@{f5.get('house_in_d7') or '?'}H "
            f"({f5.get('dignity') or '?'}) "
            f"well_placed={f5.get('well_placed')} dusthana={f5.get('in_dusthana')}"
        )
        if flags.get("d7_5l_in_dusthana"):
            extra.append("  D7 delay tone: 5L in dusthana — late/delay framing required")
        elif flags.get("d7_5l_well_placed"):
            extra.append("  D7 tone: 5L well placed — progeny support after dasha scan")
        if d7.get("note"):
            extra.append(f"  {d7['note']}")
    verdict = str(v.get("verdict") or "").upper()
    if verdict in ("DELAYED", "OBSTRUCTED"):
        extra.append(
            f"DELAY/DENIAL FRAME: verdict={verdict} — pehle D7 + yogas batao, "
            "phir next favourable dasha window (no exact delivery date)."
        )
    elif v.get("child_promised"):
        extra.append("CHILD_PROMISED tone supported — still cite ranked dasha window only.")
    ncw = v.get("next_child_window") if isinstance(v.get("next_child_window"), dict) else {}
    if ncw:
        extra.append(
            f"Next child-active dasha: {ncw.get('md')}/{ncw.get('ad')}/{ncw.get('pd')} "
            f"{ncw.get('start_iso', '?')}→{ncw.get('end_iso', '?')} "
            f"({ncw.get('priority', '')})"
        )
    if not extra:
        # Always append gender ban even when no D7 extras.
        extra = []
    extra.append(
        "⛔ NO GENDER PREDICTION: Never say ladka/ladki/beta/beti/boy/girl likelihood "
        "or 'sambhavna zyada'. Chart cannot confirm sex. If user asked gender, "
        "say uncertain only — then give timing window."
    )
    lines = block.split("\n")
    insert_at = len(lines) - 2 if len(lines) > 2 else len(lines)
    for i, line in enumerate(extra):
        lines.insert(insert_at + i, line)
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

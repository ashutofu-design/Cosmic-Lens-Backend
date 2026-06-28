"""Universal timing fallback — last resort when no dedicated engine matches."""
from __future__ import annotations

from typing import Any, Optional

from event_timing._shared.dasha_kp_sync import attach_dasha_kp_sync
from event_timing._shared.generic_timing_engine import compute_generic_timing_window
from event_timing.universal.topic_atlas import (
    build_dynamic_config,
    classify_universal_bucket,
)


def compute_universal_window(
    kundli: dict,
    intel: Optional[dict] = None,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    bucket: str | None = None,
) -> dict:
    b = bucket or classify_universal_bucket(question)
    cfg, meta = build_dynamic_config(question)
    raw = compute_generic_timing_window(
        kundli, cfg, intel, kp, birth, question, b,
    )
    if isinstance(raw, dict):
        raw["domain"] = "universal"
        raw["bucket"] = b
        raw["fallback_mode"] = True
        raw["resolved_topics"] = meta.get("topic_ids") or []
        raw["resolved_topic_labels"] = meta.get("topic_labels") or []
        raw["dynamic_houses"] = [h for h, _, _ in meta.get("concern_houses") or []]
        raw["dynamic_karakas"] = [n for n, _, _ in meta.get("karakas") or []]
        raw["bucket_note"] = (
            "Universal fallback (no dedicated engine) — dynamic houses: "
            + ", ".join(f"{h}H" for h in raw["dynamic_houses"])
            + " | karakas: "
            + ", ".join(raw["dynamic_karakas"][:4])
        )
        raw = attach_dasha_kp_sync(raw, kundli, kp)
        factors = list(raw.get("factors") or [])
        factors.insert(0, f"FALLBACK topics={raw['resolved_topics']}")
        raw["factors"] = factors
    return raw


def format_universal_timing_for_prompt(v: dict, question: str = "") -> str:
    if not isinstance(v, dict) or not v:
        return ""
    bucket = v.get("bucket") or "general_life_event"
    lines = [
        "════════════════ UNIVERSAL TIMING ENGINE (LOCKED) ════════════════",
        "Mode: fallback — no dedicated domain engine matched.",
        f"Verdict: {v.get('verdict', '?')} | Band: {v.get('band', '?')} | Bucket: {bucket}",
    ]
    topics = v.get("resolved_topic_labels") or v.get("resolved_topics") or []
    if topics:
        lines.append(f"Resolved topics: {', '.join(str(t) for t in topics[:3])}")
    note = v.get("bucket_note")
    if note:
        lines.append(f"Focus: {note}")

    run = v.get("dasha_running_now") or {}
    if run:
        lines.append(
            f"Dasha running: {run.get('lords', '?')} "
            f"({run.get('start_iso', '?')} → {run.get('end_iso', '?')})"
        )

    sync = v.get("kp_dasha_sync") or {}
    if sync.get("active_now"):
        hits = ", ".join(
            f"{x['house']}H CSL {x['csl']}={x.get('matches', [])}"
            for x in sync["active_now"]
        )
        lines.append(f"KP ↔ dasha ACTIVE: {hits}")

    cw = v.get("current_window") or {}
    if cw:
        state = "ACTIVE" if cw.get("is_active_now") else "UPCOMING"
        lines.append(
            f"Scored window ({state}): {cw.get('start_iso', '?')} → {cw.get('end_iso', '?')} "
            f"({cw.get('md', '?')}/{cw.get('ad', '?')})"
        )
    for i, w in enumerate(v.get("next_3_windows") or [], 1):
        if isinstance(w, dict):
            lines.append(
                f"  Window {i}: {w.get('start_iso', '?')}→{w.get('end_iso', '?')} "
                f"{w.get('md', '?')}/{w.get('ad', '?')} score={w.get('score', '?')}"
            )
    for f in (v.get("factors") or [])[:7]:
        lines.append(f"  • {f}")
    for g in (v.get("brand_safety_warnings") or v.get("brand_safety") or [])[:4]:
        lines.append(f"  GUARD: {g}")
    lines.append("⛔ Fallback window = readiness/probability — dedicated engine preferred when exists")
    lines.append("══════════════════════════════════════════════════════════════")
    return "\n".join(lines)

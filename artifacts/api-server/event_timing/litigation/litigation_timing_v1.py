"""Litigation timing engine v1 — bail/verdict/case-end windows (anti-fear)."""
from __future__ import annotations

import re
from typing import Any, Optional

from event_timing._shared.generic_timing_engine import DomainTimingConfig, compute_generic_timing_window

_LIT_CFG = DomainTimingConfig(
    domain="litigation",
    engine_version="litigation_timing_v1.0",
    concern_houses=[
        (6, 16.0, "6L (dispute/litigation axis)"),
        (8, 12.0, "8L (crisis/legal shock)"),
        (10, 8.0, "10L (judge/government/authority)"),
        (11, 6.0, "11L (gains/desired relief)"),
        (12, 10.0, "12L (loss/expense/confinement tone)"),
    ],
    leak_houses=[
        (6, 6.0, "6H affliction (prolonged dispute)"),
    ],
    occupant_bumps=[
        (6, 10.0, "occupies 6H (dispute active)"),
        (8, 8.0, "occupies 8H (crisis axis)"),
    ],
    aspect_target_houses=[
        (6, 8.0, "aspects 6H (legal battle)"),
    ],
    karakas=[
        ("Mars", 10.0, "conflict/court fight karaka"),
        ("Saturn", 10.0, "delay/judgment karaka"),
        ("Rahu", 8.0, "complexity/FIR karaka"),
        ("Mercury", 6.0, "arguments/documents karaka"),
    ],
    kp_cusps=[6, 8, 10, 11, 12],
    promote_tags=("6L", "Mercury", "relief", "acquittal"),
    obstruct_tags=("8L", "12L", "12H", "Saturn delay", "Rahu"),
    double_transit_houses=[6, 8, 10],
    promised_label="LEGAL_WINDOW_EASING",
    favourable_label="LEGAL_WINDOW_MODERATE",
    caution_label="LEGAL_DELAY",
    defer_label="LEGAL_PROLONGED",
    brand_safety=[
        "STRICT: No jail/phansi/guaranteed win/guaranteed loss language.",
        "Calm practical tone — qualified lawyer essential.",
        "Verdict/bail timing = probabilistic window, not certainty.",
    ],
    llm_directives=["NO_JAIL_CERTAINTY", "NO_WIN_LOSS_GUARANTEE", "LAWYER_FIRST"],
)

_BUCKET_RX = [
    ("fir_police", r"(?ix)\b(fir|complaint|police|arrest|giraftar|warrant|summons|raid|investigation|inquiry)\b"),
    ("bail_theme", r"(?ix)\b(bail|anticipatory|zamanat|parole|custody|remand)\b"),
    ("settlement", r"(?ix)\b(compromise|settlement|samjhauta|mediation|lok\s+adalat|arbitration|withdraw)\b"),
    ("case_outcome", r"(?ix)\b(verdict|faisla|judgment|judgement|jeet|haar|acquit|dosh[\s-]?mukt|partition\s+decree)\b"),
    ("court_delay", r"(?ix)\b(delay|late|adjourn|pending|latka|speed|tezi)\b"),
    ("acquittal_relief", r"(?ix)\b(acquit|relief|discharge|chhut|quash|mukti|closure|terminate)\b"),
]


def classify_litigation_timing_bucket(question: str) -> str:
    q = question or ""
    for name, rx in _BUCKET_RX:
        if re.search(rx, q):
            return name
    return "general_litigation"


def compute_litigation_window(
    kundli: dict,
    intel: Optional[dict] = None,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    bucket: str | None = None,
) -> dict:
    b = bucket or classify_litigation_timing_bucket(question)
    return compute_generic_timing_window(
        kundli, _LIT_CFG, intel, kp, birth, question, b,
    )


def format_litigation_timing_for_prompt(v: dict, question: str = "") -> str:
    if not isinstance(v, dict) or not v:
        return ""
    lines = [
        "════════════════ LITIGATION TIMING ENGINE (LOCKED) ════════════════",
        f"Verdict: {v.get('verdict', '?')} | Band: {v.get('band', '?')} | Bucket: {v.get('bucket', '?')}",
    ]
    cw = v.get("current_window") or {}
    if cw:
        lines.append(
            f"Current window: {cw.get('start_iso', '?')} → {cw.get('end_iso', '?')} "
            f"({cw.get('md', '?')}/{cw.get('ad', '?')})"
        )
    for i, w in enumerate(v.get("next_3_windows") or [], 1):
        if isinstance(w, dict):
            lines.append(
                f"  Window {i}: {w.get('start_iso', '?')}→{w.get('end_iso', '?')} "
                f"{w.get('md', '?')}/{w.get('ad', '?')} score={w.get('score', '?')}"
            )
    for f in (v.get("factors") or [])[:6]:
        lines.append(f"  • {f}")
    for g in (v.get("brand_safety_warnings") or [])[:6]:
        lines.append(f"  GUARD: {g}")
    lines.append("⛔ Process window only — lawyer consult mandatory; no fear language")
    lines.append("══════════════════════════════════════════════════════════════")
    return "\n".join(lines)

"""Education timing engine v1 — exam/admission/result windows."""
from __future__ import annotations

import re
from typing import Any, Optional

from event_timing._shared.generic_timing_engine import DomainTimingConfig, compute_generic_timing_window

_EDU_CFG = DomainTimingConfig(
    domain="education",
    engine_version="education_timing_v1.0",
    concern_houses=[
        (4, 14.0, "4L (learning foundation)"),
        (5, 16.0, "5L (intellect/exam intelligence)"),
        (9, 14.0, "9L (higher studies/luck in exams)"),
    ],
    leak_houses=[
        (8, 6.0, "8L (exam shock/setback)"),
        (12, 8.0, "12L (loss of focus/distraction)"),
    ],
    occupant_bumps=[
        (5, 12.0, "occupies 5H (study intelligence)"),
        (9, 10.0, "occupies 9H (higher education)"),
    ],
    aspect_target_houses=[
        (5, 8.0, "aspects 5H (exam activation)"),
        (9, 6.0, "aspects 9H (higher-ed activation)"),
    ],
    karakas=[
        ("Mercury", 12.0, "intellect/exam karaka"),
        ("Jupiter", 10.0, "wisdom/guru karaka"),
        ("Moon", 6.0, "memory/concentration karaka"),
    ],
    kp_cusps=[4, 5, 9],
    promote_tags=("5L", "9L", "4L", "Mercury", "Jupiter", "occupies 5H"),
    obstruct_tags=("8L", "12L", "12H"),
    double_transit_houses=[5, 9],
    promised_label="EXAM_WINDOW_FAVOURABLE",
    favourable_label="EXAM_WINDOW_MODERATE",
    caution_label="EXAM_DELAY",
    defer_label="EXAM_LOW_PROBABILITY",
    brand_safety=[
        "Exact marks/rank/college name guarantee mat karo.",
        "UPSC/SSC/bank PO competitive exams → career timing engine if job-selection angle.",
        "Effort + syllabus coverage hamesha emphasise karo.",
    ],
    llm_directives=["NO_EXACT_MARKS", "NO_RANK_GUARANTEE", "NO_COLLEGE_NAME"],
)

_BUCKET_RX = [
    ("admission", r"(?ix)\b(admission|college|university|seat)\b"),
    ("degree_completion", r"(?ix)\b(degree|graduation|complete|pass\s+out)\b"),
    ("exam_success", r"(?ix)\b(exam|result|paper|prelims|mains)\b"),
    ("higher_studies", r"(?ix)\b(masters|phd|higher\s+stud|post\s+grad)\b"),
]


def classify_education_timing_bucket(question: str) -> str:
    q = question or ""
    for name, rx in _BUCKET_RX:
        if re.search(rx, q):
            return name
    return "exam_success"


def compute_education_window(
    kundli: dict,
    intel: Optional[dict] = None,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    bucket: str | None = None,
) -> dict:
    b = bucket or classify_education_timing_bucket(question)
    return compute_generic_timing_window(
        kundli, _EDU_CFG, intel, kp, birth, question, b,
    )


def format_education_timing_for_prompt(v: dict, question: str = "") -> str:
    if not isinstance(v, dict) or not v:
        return ""
    lines = [
        "════════════════ EDUCATION TIMING ENGINE (LOCKED) ════════════════",
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
    for g in (v.get("brand_safety_warnings") or [])[:5]:
        lines.append(f"  GUARD: {g}")
    lines.append("⛔ Window = probability — no exact marks/rank/college guarantee")
    lines.append("══════════════════════════════════════════════════════════════")
    return "\n".join(lines)

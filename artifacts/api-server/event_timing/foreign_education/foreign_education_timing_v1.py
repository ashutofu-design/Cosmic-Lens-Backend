"""Foreign travel + higher education timing v1 — 5H/9H/12H + Rahu/Guru."""
from __future__ import annotations

import re
from typing import Any, Optional

from event_timing._shared.generic_timing_engine import DomainTimingConfig, compute_generic_timing_window

_FOREIGN_EDU_CFG = DomainTimingConfig(
    domain="foreign_education",
    engine_version="foreign_education_timing_v1.0",
    concern_houses=[
        (5, 16.0, "5H (intellect/competitive exam/admission)"),
        (6, 10.0, "6H (competition/rivalry — exam selection)"),
        (9, 18.0, "9H (higher studies/abroad/dharma)"),
        (12, 16.0, "12H (foreign lands/visa/settlement)"),
    ],
    leak_houses=[
        (8, 8.0, "8H (sudden setback/rejection)"),
        (4, 6.0, "4H (homeland pull — settlement delay)"),
    ],
    occupant_bumps=[
        (5, 10.0, "occupies 5H (exam/admission intelligence)"),
        (9, 12.0, "occupies 9H (higher ed / abroad axis)"),
        (12, 12.0, "occupies 12H (foreign shift)"),
    ],
    aspect_target_houses=[
        (5, 8.0, "aspects 5H (exam/admission activation)"),
        (9, 8.0, "aspects 9H (abroad/higher-ed activation)"),
        (12, 8.0, "aspects 12H (visa/settlement activation)"),
    ],
    karakas=[
        ("Rahu", 14.0, "foreign/abroad karaka (Rahu)"),
        ("Jupiter", 12.0, "Guru — higher studies + visa luck karaka"),
        ("Mercury", 8.0, "competitive exam / intellect karaka"),
    ],
    kp_cusps=[5, 6, 9, 12],
    promote_tags=("5L", "6L", "9L", "12L", "Rahu", "Jupiter", "Guru", "occupies 9H", "occupies 12H", "occupies 5H"),
    obstruct_tags=("8L", "8H", "4L", "4H"),
    double_transit_houses=[5, 9, 12],
    promised_label="FOREIGN_EDU_WINDOW_OPEN",
    favourable_label="FOREIGN_EDU_WINDOW_MODERATE",
    caution_label="FOREIGN_EDU_DELAY",
    defer_label="FOREIGN_EDU_LOW_PROBABILITY",
    brand_safety=[
        "Visa/PR/green-card approval guarantee mat karo — probability window only.",
        "Exact college/country/university name mat do.",
        "Competitive exam: effort + syllabus mandatory; rank/marks guarantee nahi.",
        "Settlement = chart window; legal immigration rules alag verify karein.",
    ],
    llm_directives=[
        "NO_GUARANTEED_VISA",
        "NO_DESTINATION_NAMING",
        "NO_EXACT_RANK_OR_MARKS",
        "FOREIGN_EDU_DISCLAIMER",
    ],
)

_BUCKET_RX = [
    ("pr_residency", re.compile(
        r"(?ix)\b(pr\b|green\s+card|permanent\s+residen|priority\s+date|"
        r"crs\s+score|h1b|rfe|citizenship|oath|immigration\s+status|"
        r"decision\s+made|in\s+progress)\b",
    )),
    ("visa", re.compile(
        r"(?ix)\b(visa|passport|embassy|biometrics?|medical\s+test|immigration\s+center|"
        r"spousal\s+visa|student\s+visa|work\s+visa|business\s+visa|investor\s+visa|"
        r"tourist\s+visa|sponsor|appointment)\b",
    )),
    ("settlement", re.compile(
        r"(?ix)\b(permanent\s+foreign\s+settlement|foreign\s+settlement|\bsettlement\b|"
        r"settle\s+(?:abroad|foreign|permanently)|bas\s+(?:jaunga|jaungi|paunga|paungi)|"
        r"videsh\s+(?:basna|me\s+rahena|shift|settle)|abroad\s+shift|"
        r"work[\s-]?permit|foreign\s+citizen|foreign\s+land|language\s+skill|"
        r"network|rent|aashiyan|assets.*foreign|wapas\s+aana|hamesha.*videsh)\b",
    )),
    ("exam_selection", re.compile(
        r"(?ix)\b(competitive\s+exam|exam\s+result|exam\s+anxiety|"
        r"result\s+(?:kab|aayega|aayegi)|selection\s+(?:kab|hoga|hogi|milega|milegi|list)|"
        r"clear\s+(?:kab|hoga)|pass\s+(?:kab|hoga)|cut[\s-]?off|rank|attempt|"
        r"coaching|taiyari|preparation|ielts|gmat|neet|iit|jee|dasha[\s-]?period)\b",
    )),
    ("admission", re.compile(
        r"(?ix)\b(admission|college|university|degree|higher\s+stud|"
        r"post[\s-]?grad|masters|phd|graduation|scholarship|counseling|counselling|"
        r"shortlist|merit|semester|padhai|professor|research|gap\s+year|"
        r"concentration|stream|subject|course|college\s+change|muhurat|mahurat)\b",
    )),
]


def classify_foreign_education_bucket(question: str) -> str:
    q = question or ""
    for name, rx in _BUCKET_RX:
        if rx.search(q):
            return name
    if re.search(r"(?ix)\b(foreign|abroad|videsh|overseas)\b", q):
        return "settlement"
    return "admission"


def compute_foreign_education_window(
    kundli: dict,
    intel: Optional[dict] = None,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    bucket: str | None = None,
) -> dict:
    b = bucket or classify_foreign_education_bucket(question)
    return compute_generic_timing_window(
        kundli, _FOREIGN_EDU_CFG, intel, kp, birth, question, b,
    )


def format_foreign_education_timing_for_prompt(v: dict, question: str = "") -> str:
    if not isinstance(v, dict) or not v:
        return ""
    lines = [
        "════════════════ FOREIGN EDU / TRAVEL TIMING (LOCKED) ════════════════",
        "Axis: 5H + 9H + 12H | Karakas: Rahu + Guru (Jupiter)",
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
    lines.append("⛔ Window = probability — no visa/college/country/rank guarantee")
    lines.append("══════════════════════════════════════════════════════════════════")
    return "\n".join(lines)

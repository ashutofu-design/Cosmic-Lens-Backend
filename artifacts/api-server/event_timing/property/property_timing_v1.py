"""Property timing engine v1 — ghar buy/registry/possession windows."""
from __future__ import annotations

import re
from typing import Any, Optional

from event_timing._shared.generic_timing_engine import DomainTimingConfig, compute_generic_timing_window

_PROPERTY_CFG = DomainTimingConfig(
    domain="property",
    engine_version="property_timing_v1.0",
    concern_houses=[
        (4, 18.0, "4L (home/property axis)"),
        (11, 14.0, "11L (gain/fulfilment of property)"),
        (2, 10.0, "2L (wealth for assets)"),
    ],
    leak_houses=[
        (8, 8.0, "8L (sudden obstacle in property)"),
        (12, 10.0, "12L (expense/legal drain on property)"),
    ],
    occupant_bumps=[
        (4, 12.0, "occupies 4H (home axis)"),
        (11, 10.0, "occupies 11H (gain house)"),
    ],
    aspect_target_houses=[
        (4, 8.0, "aspects 4H (property activation)"),
    ],
    karakas=[
        ("Mars", 10.0, "land/construction karaka"),
        ("Venus", 8.0, "comfort/home karaka"),
        ("Moon", 6.0, "dwelling/family karaka"),
        ("Saturn", 6.0, "delay/discipline in property"),
    ],
    kp_cusps=[4, 11, 2],
    promote_tags=("4L", "11L", "2L", "occupies 4H", "occupies 11H", "Mars", "Venus"),
    obstruct_tags=("8L", "12L", "12H", "Saturn delay"),
    double_transit_houses=[4, 11],
    promised_label="PROPERTY_WINDOW_OPEN",
    favourable_label="PROPERTY_WINDOW_MODERATE",
    caution_label="PROPERTY_DELAY",
    defer_label="PROPERTY_LOW_PROBABILITY",
    brand_safety=[
        "Exact registry date / exact price / exact address kabhi guarantee mat karo.",
        "Legal title, RERA, loan approval — practical verification mandatory.",
        "Seller/builder identity predict mat karo — sirf window + readiness.",
    ],
    llm_directives=[
        "NO_EXACT_PRICE",
        "NO_LOCATION_GUARANTEE",
        "NO_LEGAL_OUTCOME_CERTAINTY",
    ],
)

_BUCKET_RX = [
    ("registry", r"(?ix)\b(registry|griha[\s-]?pravesh|registration)\b"),
    ("possession", r"(?ix)\b(possession|handover|builder\s+possession)\b"),
    ("construction", r"(?ix)\b(construction|build|ban[\s-]?ega|ready)\b"),
    ("buy", r"(?ix)\b(buy|purchase|kharid|lena|ghar\s+len)\b"),
    ("sell", r"(?ix)\b(sell|bech|sale)\b"),
]


def classify_property_timing_bucket(question: str) -> str:
    q = question or ""
    for name, rx in _BUCKET_RX:
        if re.search(rx, q):
            return name
    return "buy"


def compute_property_window(
    kundli: dict,
    intel: Optional[dict] = None,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    bucket: str | None = None,
) -> dict:
    b = bucket or classify_property_timing_bucket(question)
    return compute_generic_timing_window(
        kundli, _PROPERTY_CFG, intel, kp, birth, question, b,
    )


def format_property_timing_for_prompt(v: dict, question: str = "") -> str:
    if not isinstance(v, dict) or not v:
        return ""
    lines = [
        "════════════════ PROPERTY TIMING ENGINE (LOCKED) ════════════════",
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
    dt = v.get("double_transit") or {}
    if dt.get("verdict"):
        lines.append(f"  Double-transit: {dt.get('verdict')} active={dt.get('active')}")
    for g in (v.get("brand_safety_warnings") or [])[:5]:
        lines.append(f"  GUARD: {g}")
    lines.append("⛔ Probability window only — no exact date/price/address guarantee")
    lines.append("══════════════════════════════════════════════════════════════")
    return "\n".join(lines)

"""Vehicle timing engine v1 — car/bike purchase windows (4H, Venus, Mars, 11H)."""
from __future__ import annotations

import re
from typing import Any, Optional

from event_timing._shared.generic_timing_engine import DomainTimingConfig, compute_generic_timing_window

_VEHICLE_CFG = DomainTimingConfig(
    domain="vehicle",
    engine_version="vehicle_timing_v1.0",
    concern_houses=[
        (4, 16.0, "4H (vehicle/comfort asset axis)"),
        (11, 14.0, "11H (gain/fulfilment of vehicle)"),
        (3, 8.0, "3H (commute/short travel)"),
    ],
    leak_houses=[
        (8, 8.0, "8H (sudden vehicle expense/repair)"),
        (12, 8.0, "12H (loan/EMI drain on vehicle)"),
    ],
    occupant_bumps=[
        (4, 10.0, "occupies 4H (vehicle comfort axis)"),
        (11, 8.0, "occupies 11H (fulfilment)"),
    ],
    aspect_target_houses=[
        (4, 8.0, "aspects 4H (vehicle activation)"),
        (11, 6.0, "aspects 11H (purchase fulfilment)"),
    ],
    karakas=[
        ("Venus", 12.0, "luxury/vehicle karaka (Shukra)"),
        ("Mars", 9.0, "machinery/vehicle energy (Mangal)"),
        ("Moon", 6.0, "comfort preference"),
        ("Mercury", 5.0, "commute/trade vehicle"),
    ],
    kp_cusps=[4, 11, 3],
    promote_tags=("4L", "11L", "Venus", "Mars", "occupies 4H", "occupies 11H"),
    obstruct_tags=("8L", "12L", "12H", "Saturn delay"),
    double_transit_houses=[4, 11],
    promised_label="VEHICLE_WINDOW_OPEN",
    favourable_label="VEHICLE_WINDOW_MODERATE",
    caution_label="VEHICLE_PURCHASE_DELAY",
    defer_label="VEHICLE_LOW_PROBABILITY",
    brand_safety=[
        "Exact delivery date / model / colour kabhi guarantee mat karo.",
        "Loan approval, insurance, RTO — practical checks mandatory.",
        "No accident or safety outcome prediction — timing probability only.",
    ],
    llm_directives=[
        "NO_EXACT_MODEL",
        "NO_PRICE_GUARANTEE",
        "NO_SAFETY_CERTAINTY",
    ],
)

_BUCKET_RX = [
    ("maintenance", re.compile(r"(?ix)\b(kharab|maintenance|repair|kharcha\s+rukega)\b")),
    ("upgrade", re.compile(r"(?ix)\b(upgrade|badal|change|exchange|nayi\s+gaadi\s+le)\b")),
    ("sell", re.compile(r"(?ix)\b(sell|bech|bechega|bechegi|bikega|bikegi|sale)\b")),
    ("buy", re.compile(
        r"(?ix)\b(buy|purchase|kharid|khareed|lena|gaadi|gadi|car|bike|scooter|vehicle)\b",
    )),
]


def classify_vehicle_timing_bucket(question: str) -> str:
    q = question or ""
    for name, rx in _BUCKET_RX:
        if rx.search(q):
            return name
    return "buy"


def compute_vehicle_window(
    kundli: dict,
    intel: Optional[dict] = None,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    bucket: str | None = None,
) -> dict:
    b = bucket or classify_vehicle_timing_bucket(question)
    out = compute_generic_timing_window(
        kundli, _VEHICLE_CFG, intel, kp, birth, question, b,
    )
    try:
        from event_timing.vehicle.vehicle_practicality import apply_vehicle_practicality

        out = apply_vehicle_practicality(out, kundli, birth, question)
    except Exception as exc:
        if isinstance(out, dict):
            factors = list(out.get("factors") or [])
            factors.append(f"vehicle_practicality skipped: {exc}")
            out["factors"] = factors
    return out


def format_vehicle_timing_for_prompt(v: dict, question: str = "") -> str:
    if not isinstance(v, dict) or not v:
        return ""
    lines = [
        "════════════════ VEHICLE TIMING ENGINE (LOCKED) v1 ════════════════",
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
    prac = v.get("practicality") if isinstance(v.get("practicality"), dict) else {}
    if prac:
        lines.append(
            f"▸ PRACTICAL: age {prac.get('user_age', '?')} · min {prac.get('min_purchase_age', '?')} · "
            f"afford {prac.get('affordability', '?')} · earliest {prac.get('earliest_practical_iso', '?')}"
        )
    if v.get("strategy"):
        lines.append(f"▸ DIRECTIVE: {v['strategy']}")
    lines.append("RULE: 4H + Venus/Mars + 11H dasha AND age/income practicality — no pakka 6-month promise to minors.")
    lines.append("══════════════════════════════════════════════════════════════")
    return "\n".join(lines)

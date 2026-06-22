"""Love timing engine v1 — reconciliation/commitment/meeting windows."""
from __future__ import annotations

import re
from typing import Any, Optional

from event_timing._shared.generic_timing_engine import DomainTimingConfig, compute_generic_timing_window

_LOVE_CFG = DomainTimingConfig(
    domain="love",
    engine_version="love_timing_v1.0",
    concern_houses=[
        (5, 16.0, "5L (romance/attraction)"),
        (7, 14.0, "7L (partnership/commitment)"),
        (11, 12.0, "11L (fulfilment/desire)"),
    ],
    leak_houses=[
        (8, 8.0, "8L (breakup shock/separation tone)"),
        (12, 8.0, "12L (hidden/loss in relationship)"),
    ],
    occupant_bumps=[
        (5, 12.0, "occupies 5H (romance active)"),
        (7, 10.0, "occupies 7H (partnership axis)"),
    ],
    aspect_target_houses=[
        (5, 8.0, "aspects 5H (romance trigger)"),
        (7, 8.0, "aspects 7H (relationship trigger)"),
    ],
    karakas=[
        ("Venus", 14.0, "love/attraction karaka"),
        ("Moon", 8.0, "emotion/bond karaka"),
        ("Mars", 6.0, "passion/pursuit karaka"),
    ],
    kp_cusps=[5, 7, 11],
    promote_tags=("5L", "7L", "11L", "Venus", "Moon", "occupies 5H", "occupies 7H"),
    obstruct_tags=("8L", "12L", "12H", "separation"),
    double_transit_houses=[5, 7],
    promised_label="LOVE_WINDOW_SUPPORTIVE",
    favourable_label="LOVE_WINDOW_MODERATE",
    caution_label="LOVE_WINDOW_SENSITIVE",
    defer_label="LOVE_WINDOW_LOW",
    brand_safety=[
        "Rejection/betrayal/third-party identity ki certainty mat do.",
        "Breakup ki absolute prediction band — healing + strategy pair karo.",
        "One-sided cases mein self-worth preserve karo.",
        "Love-marriage kab → marriage engine use hota hai.",
    ],
    llm_directives=["LOVE_TONE_RULES", "NO_REJECTION_CERTAINTY", "NO_THIRD_PARTY_ID"],
)

LOVE_TONE_RULES: tuple = (
    "Never encourage breakup or separation; offer perspective only.",
    "Do not label a partner with toxic-trait diagnoses.",
    "Never promise love outcome as certainty; use probability window language.",
    "No third-party identification — cosmic pattern level only.",
)

_BUCKET_RX = [
    ("reconciliation", r"(?ix)\b(patchup|patch\s*up|reconcile|wapas|return)\b"),
    ("commitment_fear", r"(?ix)\b(commitment|propose|shaadi\s+se\s+darr)\b"),
    ("one_sided", r"(?ix)\b(one[\s-]?sided|crush|unrequited)\b"),
    ("timing", r"(?ix)\b(milega|milegi|hoga|hogi|kab)\b"),
]


def classify_love_timing_bucket(question: str) -> str:
    q = question or ""
    for name, rx in _BUCKET_RX:
        if re.search(rx, q):
            return name
    return "timing"


def compute_love_window(
    kundli: dict,
    intel: Optional[dict] = None,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    bucket: str | None = None,
) -> dict:
    b = bucket or classify_love_timing_bucket(question)
    result = compute_generic_timing_window(
        kundli, _LOVE_CFG, intel, kp, birth, question, b,
    )
    result["love_tone_rules"] = list(LOVE_TONE_RULES)
    return result


def format_love_timing_for_prompt(v: dict, question: str = "") -> str:
    if not isinstance(v, dict) or not v:
        return ""
    lines = [
        "════════════════ LOVE TIMING ENGINE (LOCKED) ════════════════",
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
    for f in (v.get("factors") or [])[:5]:
        lines.append(f"  • {f}")
    for g in (v.get("brand_safety_warnings") or [])[:5]:
        lines.append(f"  GUARD: {g}")
    for t in (v.get("love_tone_rules") or [])[:4]:
        lines.append(f"  TONE: {t}")
    lines.append("⛔ Probability window — no rejection/betrayal certainty")
    lines.append("══════════════════════════════════════════════════════════════")
    return "\n".join(lines)

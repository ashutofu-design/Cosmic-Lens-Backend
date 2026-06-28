"""Friends, network & circle timing v1 — 11H, Mercury (Budh) + Rahu."""
from __future__ import annotations

import re
from typing import Any, Optional

from event_timing._shared.dasha_kp_sync import attach_dasha_kp_sync
from event_timing._shared.generic_timing_engine import (
    DomainTimingConfig,
    compute_generic_timing_window,
)

_NETWORK_CFG = DomainTimingConfig(
    domain="network",
    engine_version="network_timing_v1.0",
    concern_houses=[
        (11, 20.0, "11L (friends / gains / social circle / network)"),
        (3, 10.0, "3H (Mercury peers / communication among friends)"),
    ],
    leak_houses=[
        (6, 12.0, "6L (enemies / rivalry / misunderstanding drag)"),
        (12, 8.0, "12L (loss of friends / isolation)"),
        (8, 6.0, "8L (sudden betrayal / break in circle)"),
    ],
    occupant_bumps=[
        (11, 14.0, "occupies 11H (strong friend-network axis)"),
        (3, 10.0, "occupies 3H (peer communication / local circle)"),
    ],
    aspect_target_houses=[
        (11, 12.0, "aspects 11H (network expansion / support)"),
        (3, 8.0, "aspects 3H (friend communication ease)"),
        (6, 6.0, "aspects 6H (enemy pressure — watch for conflict buckets)"),
    ],
    karakas=[
        ("Mercury", 16.0, "friends / peers / communication karaka (Budh)"),
        ("Rahu", 14.0, "influential / unconventional / mass-network karaka"),
        ("Jupiter", 10.0, "well-wishers / elder support karaka"),
        ("Venus", 8.0, "social harmony / group bonding karaka"),
    ],
    kp_cusps=[3, 11],
    promote_tags=("11L", "3L", "Mercury", "Rahu", "Jupiter", "11H", "3H"),
    obstruct_tags=("6L", "Saturn", "Mars", "6H", "12L"),
    double_transit_houses=[11],
    promised_label="NETWORK_WINDOW_STRONG",
    favourable_label="NETWORK_WINDOW_MODERATE",
    caution_label="NETWORK_DELAY",
    defer_label="NETWORK_LOW_READINESS",
    brand_safety=[
        "Influential network window = social readiness — kisi specific VIP ka naam mat do.",
        "Friend misunderstanding healing = communication ease window — doosri side ka intent guarantee nahi.",
        "Enmity peace window = tension-easing period — court/legal dispute alag litigation track hai.",
        "Rahu network = unconventional connections — verify trust practically.",
        "11H gains from circle ≠ guaranteed favor from powerful people.",
    ],
    llm_directives=[
        "NO_VIP_NAME",
        "NO_FRIEND_RECONCILE_GUARANTEE",
        "NO_ENMITY_END_CERTAINTY",
        "TRUST_PRACTICAL_CHECK",
    ],
)

# Order — friend conflict before general enmity; enmity before network build.
_BUCKET_RX = [
    (
        "friend_conflict",
        r"(?ix)\b("
        r"dost\w*|dosti|friend|friends|saheli|sahel|yaar|buddy|"
        r"circle|social\s+circle|friend\s+circle|peer|peers|"
        r"dosto\s+se|friends\s+se|sahel\w*\s+se"
        r")\b.{0,60}\b("
        r"dhokha|dhoke|misunderstanding|galatfehmi|galat\s+fahmi|"
        r"conflict|jhagda|ladai|break|doori|trust\s+issue|bewafai|"
        r"betrayal|misunderstood|galat\s+samjh"
        r")\b|"
        r"\b("
        r"dhokha|misunderstanding|galatfehmi|betrayal|bewafai"
        r")\b.{0,60}\b("
        r"dost\w*|dosti|friend|friends|saheli|circle|yaar"
        r")\b",
    ),
    (
        "enmity_peace",
        r"(?ix)\b("
        r"dushmani|dushman|shatru|enemy|enmity|rivalry|"
        r"bina\s+karan|without\s+reason|unnecessary\s+hatred|"
        r"nafrat|vair|vendetta|bad\s+blood|"
        r"shant|shaant|peace|sulah|reconcile|patch\s+up|theek\s+hoga|khatam\s+hogi"
        r")\b",
    ),
    (
        "influential_network",
        r"(?ix)\b("
        r"network|circle|connections|contacts|"
        r"influential|bade\s+log|powerful\s+people|vip|"
        r"well[\s-]?wisher|support\s+system|social\s+support|"
        r"help\s+karenge|madad\s+karenge|favour|favor|"
        r"11th\s+house|11h|budh|mercury|"
        r"referral|recommendation|mentor\s+network|"
        r"social\s+capital|circle\s+badega|network\s+bane"
        r")\b",
    ),
]


def classify_network_timing_bucket(question: str) -> str:
    q = question or ""
    for name, rx in _BUCKET_RX:
        if re.search(rx, q):
            return name
    return "general_network"


def compute_network_window(
    kundli: dict,
    intel: Optional[dict] = None,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    bucket: str | None = None,
) -> dict:
    b = bucket or classify_network_timing_bucket(question)
    raw = compute_generic_timing_window(
        kundli, _NETWORK_CFG, intel, kp, birth, question, b,
    )
    if isinstance(raw, dict):
        raw["domain"] = "network"
        raw["bucket"] = b
        notes = {
            "influential_network": (
                "Influential circle window — 11H/11L + Mercury/Rahu "
                "support-from-powerful-people convergence."
            ),
            "friend_conflict": (
                "Friend misunderstanding healing — 6L pressure easing + "
                "Mercury/11H communication repair."
            ),
            "enmity_peace": (
                "Enmity cooling window — 6H tension down + 11H social harmony rebuild."
            ),
            "general_network": (
                "General friends/network timing — 11H + Mercury/Rahu combined activation."
            ),
        }
        raw["bucket_note"] = notes.get(b, notes["general_network"])
        raw = attach_dasha_kp_sync(raw, kundli, kp)
    return raw


def format_network_timing_for_prompt(v: dict, question: str = "") -> str:
    if not isinstance(v, dict) or not v:
        return ""
    bucket = v.get("bucket") or "general_network"
    lines = [
        "════════════════ FRIENDS & NETWORK TIMING ENGINE (LOCKED) ════════════════",
        f"Verdict: {v.get('verdict', '?')} | Band: {v.get('band', '?')} | Bucket: {bucket}",
    ]
    note = v.get("bucket_note")
    if note:
        lines.append(f"Focus: {note}")

    run = v.get("dasha_running_now") or {}
    if run:
        tag = "ACTIVE NOW" if run.get("is_running_now") else "RUNNING"
        lines.append(
            f"Dasha running {tag}: {run.get('lords', '?')} "
            f"({run.get('start_iso', '?')} → {run.get('end_iso', '?')})"
        )

    sync = v.get("kp_dasha_sync") or {}
    if sync.get("active_now"):
        hits = ", ".join(
            f"{x['house']}H CSL {x['csl']}={x.get('matches', [])}"
            for x in sync["active_now"]
        )
        lines.append(f"KP ↔ dasha ACTIVE: {hits}")
    for up in (sync.get("upcoming") or [])[:2]:
        nw = up.get("next_window") or {}
        if nw:
            lines.append(
                f"KP ↔ dasha NEXT: {up.get('house')}H CSL {up.get('csl')} "
                f"as {nw.get('roles')} {nw.get('start_iso')}→{nw.get('end_iso')}"
                + (" (running now)" if nw.get("is_running_now") else "")
            )

    cw = v.get("current_window") or {}
    if cw:
        state = "ACTIVE" if cw.get("is_active_now") else "UPCOMING"
        lines.append(
            f"Scored window ({state}): {cw.get('start_iso', '?')} → {cw.get('end_iso', '?')} "
            f"({cw.get('md', '?')}/{cw.get('ad', '?')})"
            + (f" KP hits={cw.get('kp_csl_hits')}" if cw.get("kp_csl_hits") else "")
        )
    elif v.get("best_upcoming_window"):
        bw = v["best_upcoming_window"]
        lines.append(
            f"Best upcoming scored window: {bw.get('start_iso')}→{bw.get('end_iso')} "
            f"{bw.get('md')}/{bw.get('ad')}"
        )
    kp = v.get("kp_layer") or {}
    cusps = kp.get("cusps") or {}
    if cusps:
        lines.append(
            "KP cusps: "
            + ", ".join(f"{h}H={lord}" for h, lord in sorted(cusps.items()))
        )
    for i, w in enumerate(v.get("next_3_windows") or [], 1):
        if isinstance(w, dict):
            st = "ACTIVE" if w.get("is_active_now") else "UPCOMING"
            kp_hit = f" KP={w.get('kp_csl_hits')}" if w.get("kp_csl_hits") else ""
            lines.append(
                f"  Window {i} ({st}): {w.get('start_iso', '?')}→{w.get('end_iso', '?')} "
                f"{w.get('md', '?')}/{w.get('ad', '?')} score={w.get('score', '?')}{kp_hit}"
            )
    for f in (v.get("factors") or [])[:6]:
        lines.append(f"  • {f}")
    for g in (v.get("brand_safety_warnings") or v.get("brand_safety") or [])[:5]:
        lines.append(f"  GUARD: {g}")
    lines.append("⛔ Window = readiness/probability — no VIP naam / guaranteed reconciliation")
    lines.append("══════════════════════════════════════════════════════════════")
    return "\n".join(lines)

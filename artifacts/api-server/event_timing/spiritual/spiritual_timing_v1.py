"""Spiritual growth & occult timing v1 — 8H / 9H / 12H, Ketu + Guru."""
from __future__ import annotations

import re
from typing import Any, Optional

from event_timing._shared.dasha_kp_sync import attach_dasha_kp_sync
from event_timing._shared.generic_timing_engine import (
    DomainTimingConfig,
    compute_generic_timing_window,
)

_SPIRITUAL_CFG = DomainTimingConfig(
    domain="spiritual",
    engine_version="spiritual_timing_v1.0",
    concern_houses=[
        (8, 16.0, "8L (occult/mystery/secret knowledge)"),
        (9, 18.0, "9L (dharma/guru/bhagya)"),
        (12, 16.0, "12L (moksha/meditation/isolation)"),
    ],
    leak_houses=[
        (6, 8.0, "6L (worldly obstacles/distraction)"),
        (3, 5.0, "3L (restless mind/noise)"),
    ],
    occupant_bumps=[
        (8, 12.0, "occupies 8H (occult/secret-knowledge axis)"),
        (9, 14.0, "occupies 9H (guru/dharma activation)"),
        (12, 14.0, "occupies 12H (moksha/meditation axis)"),
    ],
    aspect_target_houses=[
        (9, 10.0, "aspects 9H (guru grace)"),
        (12, 8.0, "aspects 12H (inner peace)"),
        (8, 8.0, "aspects 8H (occult study window)"),
    ],
    karakas=[
        ("Ketu", 14.0, "moksha/detachment karaka"),
        ("Jupiter", 14.0, "guru/dharma karaka"),
        ("Saturn", 8.0, "discipline/sadhana karaka"),
        ("Moon", 6.0, "mind/peace karaka"),
    ],
    kp_cusps=[8, 9, 12],
    promote_tags=("9L", "12L", "8L", "Ketu", "Jupiter", "9H", "12H", "8H"),
    obstruct_tags=("6L", "Rahu", "3L", "6H"),
    double_transit_houses=[9, 12],
    promised_label="SPIRITUAL_WINDOW_STRONG",
    favourable_label="SPIRITUAL_WINDOW_MODERATE",
    caution_label="SPIRITUAL_DELAY",
    defer_label="SPIRITUAL_LOW_READINESS",
    brand_safety=[
        "Guru/deeksha window = inner readiness period — kisi specific guru ka naam mat do.",
        "Occult/jyotish/tarot seekhne ka window ≠ mastery guarantee — guru-shishya parampara + ethics.",
        "Teerthyatra timing = favorable dharma-travel window — health/fitness practical check karo.",
        "Inner peace / restlessness — clinical anxiety ya depression ho to doctor + spiritual dono.",
        "Tantra/black-magic ya guaranteed moksha claims bilkul mat karo.",
    ],
    llm_directives=[
        "NO_GURU_NAME_GUARANTEE",
        "NO_MOKSHA_CERTAINTY",
        "OCCULT_ETHICS_ONLY",
        "DOCTOR_IF_CLINICAL_MENTAL",
    ],
)

# Order matters — pilgrimage before guru (teerth + guru both present).
_BUCKET_RX = [
    (
        "pilgrimage",
        r"(?ix)\b("
        r"teerth|tirth|pilgrim|yatra|char\s+dham|dham\s+yatra|"
        r"religious\s+travel|religious\s+tourism|pavitra\s+sthal|"
        r"mandir|temple|dharmik|kailash|mansarovar|vaishno|amarnath|kedarnath|"
        r"jagannath|kashi|rameswaram|shakti\s+peeth|bodh\s+gaya|kumbh|"
        r"kuldevi|kuldevta|mecca|vatican"
        r")\b",
    ),
    (
        "occult_learning",
        r"(?ix)\b("
        r"astrology|astro\s*logy|jyotish|tarot|occult|palmistry|"
        r"numerology|reiki|secret\s+knowledge|hidden\s+knowledge|"
        r"lal\s+kitab|nadi|prediction|astrologer|intuition|purnanumaan|"
        r"mentor|teacher|institute|commercial\s+client|accuracy|"
        r"8th\s+house|vedic\s+astro|seekh|interpretation"
        r")\b",
    ),
    (
        "guru_deeksha",
        r"(?ix)\b("
        r"guru|guruji|deeksha|diksha|initiation|awakening|awaken|"
        r"kundalini|satguru|spiritual\s+master|sahi\s+guru|"
        r"spiritual\s+guide|dharma\s+guru|mantra\s+siddhi|siddhi|"
        r"purva\s+punya|punya|sanyas|vairagya|atmakaraka|amatyakaraka|"
        r"life\s+purpose|soul\s+mission|third\s+eye|ajna|chakra|aura|"
        r"rishi|saint|siddh|nishtha|janeu|guru\s+mantra"
        r")\b",
    ),
    (
        "inner_peace",
        r"(?ix)\b("
        r"meditation|dhyan|dhyana|inner\s+peace|manasik\s+shanti|"
        r"mental\s+restlessness|restlessness|bechaini|overthinking|"
        r"sukoon|shanti|peace\s+of\s+mind|anxiety|insomnia|nind|"
        r"trauma|emotional\s+trauma|gussa|anger|vipassana|silent\s+retreat|"
        r"saade\s+sati|dhaiya|pranayam|santushti|contentment|"
        r"atma-bal|willpower|self-confidence|enlighten|distraction"
        r")\b",
    ),
]


def classify_spiritual_timing_bucket(question: str) -> str:
    q = question or ""
    for name, rx in _BUCKET_RX:
        if re.search(rx, q):
            return name
    return "general_spiritual"


def compute_spiritual_window(
    kundli: dict,
    intel: Optional[dict] = None,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    bucket: str | None = None,
) -> dict:
    b = bucket or classify_spiritual_timing_bucket(question)
    raw = compute_generic_timing_window(
        kundli, _SPIRITUAL_CFG, intel, kp, birth, question, b,
    )
    if isinstance(raw, dict):
        raw["domain"] = "spiritual"
        raw["bucket"] = b
        notes = {
            "guru_deeksha": "Guru/deeksha readiness — 9H/9L + Jupiter/Ketu dasha convergence.",
            "occult_learning": "Secret-knowledge study window — 8H/8L + Ketu/Mercury supportive AD.",
            "pilgrimage": "Dharma-yatra window — 9H/12H + Jupiter transit support.",
            "inner_peace": "Meditation/shanti window — 12H/12L + Moon/Ketu calm phases.",
            "general_spiritual": "General spiritual growth — 8H/9H/12H combined activation.",
        }
        raw["bucket_note"] = notes.get(b, notes["general_spiritual"])
        raw = attach_dasha_kp_sync(raw, kundli, kp)
    return raw


def format_spiritual_timing_for_prompt(v: dict, question: str = "") -> str:
    if not isinstance(v, dict) or not v:
        return ""
    bucket = v.get("bucket") or "general_spiritual"
    lines = [
        "════════════════ SPIRITUAL TIMING ENGINE (LOCKED) ════════════════",
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
    lines.append("⛔ Window = readiness/probability — no guru naam / moksha guarantee")
    lines.append("══════════════════════════════════════════════════════════════")
    return "\n".join(lines)

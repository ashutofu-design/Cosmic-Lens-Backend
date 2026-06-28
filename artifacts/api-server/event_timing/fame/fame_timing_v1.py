"""Social image, fame & recognition timing v1 — 1H / 5H / 10H, Sun + Rahu + Moon-10th."""
from __future__ import annotations

import re
from typing import Any, Optional

from event_timing._shared.dasha_kp_sync import attach_dasha_kp_sync
from event_timing._shared.generic_timing_engine import (
    DomainTimingConfig,
    _house_lord,
    _lagna_si,
    _planet_house,
    compute_generic_timing_window,
)

_FAME_CFG = DomainTimingConfig(
    domain="fame",
    engine_version="fame_timing_v1.0",
    concern_houses=[
        (1, 18.0, "1L (self-image / public face / personality)"),
        (5, 16.0, "5L (creativity / entertainment / celebrity axis)"),
        (10, 18.0, "10L (status / karma / authority in world)"),
        (11, 12.0, "11H (gains / network reach / followers)"),
    ],
    leak_houses=[
        (6, 10.0, "6L (enemies / scandal / defamation drag)"),
        (8, 8.0, "8L (sudden fall / controversy)"),
        (12, 6.0, "12L (loss of face / isolation)"),
    ],
    occupant_bumps=[
        (1, 14.0, "occupies 1H (self-image / fame on face)"),
        (5, 12.0, "occupies 5H (creative fame / spotlight)"),
        (10, 14.0, "occupies 10H (public status / authority)"),
        (11, 10.0, "occupies 11H (mass reach / social gains)"),
    ],
    aspect_target_houses=[
        (1, 10.0, "aspects 1H (image boost)"),
        (5, 10.0, "aspects 5H (creative visibility)"),
        (10, 12.0, "aspects 10H (career fame / leadership)"),
        (11, 8.0, "aspects 11H (network / viral reach)"),
    ],
    karakas=[
        ("Sun", 16.0, "authority / name / recognition karaka"),
        ("Rahu", 14.0, "mass fame / viral / social-media karaka"),
        ("Jupiter", 12.0, "honor / award / dignity karaka"),
        ("Venus", 10.0, "entertainment / popularity karaka"),
        ("Moon", 8.0, "public mood / mass appeal karaka"),
    ],
    kp_cusps=[1, 5, 10, 11],
    promote_tags=("1L", "5L", "10L", "Sun", "Rahu", "Jupiter", "Venus", "1H", "5H", "10H", "11H"),
    obstruct_tags=("6L", "8L", "Saturn", "6H", "8H"),
    double_transit_houses=[1, 10],
    promised_label="FAME_WINDOW_STRONG",
    favourable_label="FAME_WINDOW_MODERATE",
    caution_label="FAME_DELAY",
    defer_label="FAME_LOW_READINESS",
    brand_safety=[
        "Fame / viral window = readiness period — guaranteed celebrity ya million followers mat bolo.",
        "Award timing = honor window — selection committee / merit practical factor reh sakta hai.",
        "Reputation recovery = image-healing window — legal defamation case alag litigation track hai.",
        "Politics entry = public-leadership readiness — ticket/party/election ground reality alag hai.",
        "Social media virality Rahu-mass axis — ethics / content quality user responsibility.",
    ],
    llm_directives=[
        "NO_VIRAL_GUARANTEE",
        "NO_AWARD_CERTAINTY",
        "NO_POLITICAL_WIN_GUARANTEE",
        "REPUTATION_RECOVERY_HUMBLE",
    ],
)

# Order matters — reputation before social (defamation + fame both present).
_BUCKET_RX = [
    (
        "reputation_recovery",
        r"(?ix)\b("
        r"reputation|bad\s+name|bad\s+naam|galat\s+soch\w*|galat\s+faimi|"
        r"defamation|malign|character\s+assassination|bad\s+press|"
        r"khoyi\s+hui\s+reputation|naam\s+kharab|izzat\s+wapas|"
        r"image\s+theek|image\s+recover|nafrat\s+khatam|"
        r"rumou?r|bad\s+image|scandal\s+clear|controversy\s+end"
        r")\b",
    ),
    (
        "politics_leadership",
        r"(?ix)\b("
        r"politic|political|neta|minister|mp\b|mla\b|cm\b|pm\b|"
        r"election|loksabha|vidhan\s+sabha|party\s+ticket|"
        r"public\s+office|rajneeti|rajya\s+sabha|mayor|"
        r"leadership\s+position|leadership\s+role|power\s+position|"
        r"government\s+post|cabinet|parliament|assembly\s+seat|"
        r"chief\s+minister|prime\s+minister|rally|campaign\s+win"
        r")\b",
    ),
    (
        "awards",
        r"(?ix)\b("
        r"award|recognition|honou?r|honor|padma|bharat\s+ratna|"
        r"national\s+award|international\s+award|nobel|oscar|grammy|"
        r"filmfare|pulitzer|medal|trophy|prize|samman|puraskar|"
        r"felicitation|lifetime\s+achievement|pad\s+shri|pad\s+bhushan"
        r")\b",
    ),
    (
        "social_fame",
        r"(?ix)\b("
        r"fame|famous|celebrity|viral|social\s+media|instagram|youtube|"
        r"influencer|followers|subscribers|content\s+viral|name\s+chalega|"
        r"naam\s+chalega|recognition|public\s+image|publicity|"
        r"limelight|spotlight|star\s+bana|popular|popularity|"
        r"brand\s+face|face\s+of|media\s+attention|trending|"
        r"1st\s+house|5th\s+house|10th\s+house|surya|rahu|"
        r"celebrity\s+yoga|mass\s+fame|public\s+figure"
        r")\b",
    ),
]


def classify_fame_timing_bucket(question: str) -> str:
    q = question or ""
    for name, rx in _BUCKET_RX:
        if re.search(rx, q):
            return name
    return "general_fame"


def _attach_moon_tenth_axis(raw: dict, kundli: dict) -> dict:
    """10th house counted from Moon — public-status sub-axis."""
    factors = list(raw.get("factors") or [])
    planets = kundli.get("planets") if isinstance(kundli, dict) else []
    moon_h = _planet_house(planets if isinstance(planets, list) else [], "Moon")
    lagna = _lagna_si(kundli if isinstance(kundli, dict) else {})
    if moon_h and lagna is not None:
        tenth_from_moon = ((moon_h - 1 + 9) % 12) + 1
        lord = _house_lord(lagna, tenth_from_moon)
        raw["moon_tenth_house"] = tenth_from_moon
        raw["moon_tenth_lord"] = lord
        factors.append(
            f"STEP1b 10th-from-Moon={tenth_from_moon}H lord {lord} (Chandra-karma public axis)"
        )
        raw["factors"] = factors
    return raw


def compute_fame_window(
    kundli: dict,
    intel: Optional[dict] = None,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    bucket: str | None = None,
) -> dict:
    b = bucket or classify_fame_timing_bucket(question)
    raw = compute_generic_timing_window(
        kundli, _FAME_CFG, intel, kp, birth, question, b,
    )
    if isinstance(raw, dict):
        raw["domain"] = "fame"
        raw["bucket"] = b
        notes = {
            "social_fame": "Name/fame & social reach — 1H/5H/10H + Sun/Rahu mass-visibility convergence.",
            "awards": "Honor/award window — 10H/Jupiter dignity + 5H creative merit axis.",
            "reputation_recovery": "Image-healing window — 6L/8L pressure easing + 1H/10H rebuild.",
            "politics_leadership": "Public leadership entry — 10H/Sun/Rahu authority + 11H network.",
            "general_fame": "General fame & recognition — 1H/5H/10H combined activation.",
        }
        raw["bucket_note"] = notes.get(b, notes["general_fame"])
        raw = _attach_moon_tenth_axis(raw, kundli)
        raw = attach_dasha_kp_sync(raw, kundli, kp)
    return raw


def format_fame_timing_for_prompt(v: dict, question: str = "") -> str:
    if not isinstance(v, dict) or not v:
        return ""
    bucket = v.get("bucket") or "general_fame"
    lines = [
        "════════════════ FAME & RECOGNITION TIMING ENGINE (LOCKED) ════════════════",
        f"Verdict: {v.get('verdict', '?')} | Band: {v.get('band', '?')} | Bucket: {bucket}",
    ]
    note = v.get("bucket_note")
    if note:
        lines.append(f"Focus: {note}")

    m10 = v.get("moon_tenth_house")
    m10l = v.get("moon_tenth_lord")
    if m10 and m10l:
        lines.append(f"10th-from-Moon: {m10}H lord {m10l}")

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
    lines.append("⛔ Window = readiness/probability — no viral/award/election guarantee")
    lines.append("══════════════════════════════════════════════════════════════")
    return "\n".join(lines)

"""Love timing v1 — dasha-first (current AD/PD → next scan) + KP via dual-track."""
from __future__ import annotations

from typing import Any, Optional

from event_timing._shared.generic_timing_engine import (
    DomainTimingConfig,
    MIN_AD_PD_ACTIVATION,
    compute_generic_timing_window,
)
from event_timing.love.love_timing_engine_v1 import (
    LOVE_TONE_RULES,
    classify_love_timing_bucket,
)

_LOVE_CFG = DomainTimingConfig(
    domain="love",
    engine_version="love_timing_v2.0",
    concern_houses=[
        (5, 18.0, "5H romance"),
        (7, 18.0, "7H partnership"),
        (11, 12.0, "11H fulfilment in love"),
    ],
    leak_houses=[
        (6, 6.0, "6H conflict"),
        (8, 8.0, "8H sudden breaks"),
        (12, 8.0, "12H hidden/loss"),
    ],
    occupant_bumps=[
        (5, 10.0, "occupies 5H"),
        (7, 10.0, "occupies 7H"),
        (11, 8.0, "occupies 11H"),
    ],
    aspect_target_houses=[
        (5, 8.0, "aspects 5H"),
        (7, 8.0, "aspects 7H"),
        (11, 6.0, "aspects 11H"),
    ],
    karakas=[
        ("Venus", 16.0, "Venus love karaka"),
        ("Moon", 12.0, "Moon emotions"),
        ("Mars", 10.0, "Mars passion"),
    ],
    kp_cusps=[5, 7, 11],
    promote_tags=(
        "5L", "5H", "7L", "7H", "11L", "11H",
        "Venus", "Moon", "Mars", "romance", "partnership", "fulfilment",
        "occupies 5H", "occupies 7H", "occupies 11H",
        "aspects 5H", "aspects 7H", "aspects 11H",
        "conjunct", "karaka",
    ),
    obstruct_tags=("6L", "8L", "12L", "6H", "8H", "12H", "conflict", "hidden"),
    double_transit_houses=[5, 7, 11],
    promised_label="LOVE_WINDOW_SUPPORTIVE",
    favourable_label="LOVE_WINDOW_MODERATE",
    caution_label="LOVE_WINDOW_SENSITIVE",
    defer_label="LOVE_WINDOW_DEFERRED",
    brand_safety=list(LOVE_TONE_RULES) + [
        "Never guarantee exact date — probability window only.",
        "No third-party naming; pattern level only.",
    ],
    llm_directives=[
        "DASHA_FIRST: pehle current AD/PD check — agar 5/7/11 + Venus/Moon weak → abhi shuru nahi.",
        "NEXT_SCAN: current weak ho to chronology se pehla strong AD/PD window batao.",
        f"MANDATORY: activation score < {MIN_AD_PD_ACTIVATION} wala period kabhi answer mat do — next PD/AD scan.",
        "THREE_WINDOWS: engine 3 ranked love periods deta hai — default answer sirf rank #1.",
        "FOLLOW_UP: user 'dusra/2nd/agla' puche → rank #2; 'teesra/3rd' → rank #3.",
        "SIGNIFICATOR: rank-wise sabse powerful graha (5L/7L/11L + 5H/7H/11H occupant + aspect + conjunct lord) ke AD/PD mein love.",
        "LINKAGE: 5H mein baitha, 5H ko aspect, ya 5L ke sath conjunct — sab score rank mein aate hain.",
    ],
)


def compute_love_window(
    kundli: dict,
    intel: Optional[dict] = None,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    bucket: str | None = None,
) -> dict:
    b = bucket or classify_love_timing_bucket(question)
    out = compute_generic_timing_window(
        kundli, _LOVE_CFG, intel, kp, birth, question, b,
    )
    out["engine"] = "love_timing_engine_v1"
    out["love_tone_rules"] = list(LOVE_TONE_RULES)
    out["transits"] = out.get("double_transit") or {}
    ts = str(out.get("timing_source") or "")
    cw = out.get("current_window") if isinstance(out.get("current_window"), dict) else {}
    if ts == "current_dasha_active" and cw:
        out["strategy"] = (
            f"CURRENT love window — abhi chal rahi AD/PD {cw.get('ad')}/{cw.get('pd')} "
            f"({cw.get('start_iso')}→{cw.get('end_iso')}) 5/7/11 axis active."
        )
    elif ts == "next_dasha_scan" and cw:
        out["strategy"] = (
            f"Current dasha mein love trigger weak — pehla strong window "
            f"{cw.get('start_iso')}→{cw.get('end_iso')} AD/PD {cw.get('ad')}/{cw.get('pd')}."
        )
    elif ts == "no_qualified_window":
        out["strategy"] = (
            f"Koi bhi AD/PD window activation >= {MIN_AD_PD_ACTIVATION} nahi mili — "
            "sub-threshold dasha period mat cite karo; defer / weak signal bolo."
        )
    else:
        out["strategy"] = out.get("strategy") or "Chart scan — probability window only."
    return out


def format_love_timing_for_prompt(v: dict, question: str = "") -> str:
    if not isinstance(v, dict) or not v:
        return ""
    lines = [
        "=== LOVE TIMING ENGINE (LOCKED) v2 — dasha-first · 5H/7H/11H · Venus/Moon ===",
        f"Bucket: {v.get('bucket')} · Verdict: {v.get('verdict')} · Band: {v.get('band')}",
        f"Timing source: {v.get('timing_source') or '—'}",
    ]
    ranked = v.get("top_planets") or []
    if ranked:
        tops = [str(r.get("name")) for r in ranked[:3] if isinstance(r, dict) and r.get("name")]
        if tops:
            lines.append(f"▸ D1 significators: {', '.join(tops)}")
    house_lords = v.get("domain_house_lords") or []
    sig_rank = v.get("significator_rank") if isinstance(v.get("significator_rank"), list) else []
    if sig_rank:
        lines.append("▸ LOVE SIGNIFICATORS (score rank — lord / occupant / aspect / conjunct):")
        for e in sig_rank[:10]:
            if not isinstance(e, dict) or not e.get("planet"):
                continue
            lines.append(
                f"  {e.get('planet')} score={e.get('score')} · {e.get('link') or e.get('tag')}"
            )
    elif house_lords:
        hl_bits = [
            f"{hl.get('tag')}={hl.get('planet')} score={hl.get('score')}"
            for hl in house_lords[:5]
            if isinstance(hl, dict) and hl.get("planet")
        ]
        if hl_bits:
            lines.append(f"▸ Domain house lords: {' · '.join(hl_bits)}")
    sig = v.get("primary_significator") if isinstance(v.get("primary_significator"), dict) else {}
    if sig.get("name"):
        roles = ", ".join(sig.get("roles") or []) or sig.get("house_tag") or "karaka"
        lines.append(
            f"▸ TOP love significator: {sig.get('name')} score={sig.get('score')} "
            f"({roles}) — {sig.get('link') or 'love via AD/PD'}"
        )
    periods = v.get("timing_periods") if isinstance(v.get("timing_periods"), list) else []
    if periods:
        lines.append("▸ THREE RANKED LOVE PERIODS (engine locked):")
        for p in periods[:3]:
            if not isinstance(p, dict):
                continue
            rank = p.get("rank") or "?"
            lords = p.get("lords") or "/".join(
                x for x in (p.get("md"), p.get("ad"), p.get("pd")) if x
            )
            via = f" · love_via={p.get('love_via')}" if p.get("love_via") else ""
            lines.append(
                f"  #{rank} {p.get('start_iso')}→{p.get('end_iso')} "
                f"MD/AD/PD={lords} act={p.get('activation_score')}{via}"
            )
        lines.append(
            ">>> DEFAULT ANSWER: cite rank #1 ONLY. "
            "User 'dusra/2nd/agla window' → rank #2; 'teesra/3rd' → rank #3."
        )
    cw = v.get("current_window") or {}
    if v.get("timing_source") == "no_qualified_window":
        lines.append(
            f">>> NO QUALIFIED WINDOW — activation < {MIN_AD_PD_ACTIVATION}. "
            "Do NOT cite MD/AD/PD dates. Defer timing; no hallucinated periods."
        )
    elif not periods and cw.get("start_iso") and cw.get("end_iso"):
        active = "ACTIVE NOW" if cw.get("is_active_now") or v.get("timing_source") == "current_dasha_active" else "UPCOMING"
        lords = cw.get("lords") or "/".join(
            x for x in (cw.get("md"), cw.get("ad"), cw.get("pd")) if x
        )
        lines.append(
            f"▸ PRIMARY window ({active}): {cw.get('start_iso')} → {cw.get('end_iso')} "
            f"MD/AD/PD={lords or '?'}"
        )
        lines.append(
            f">>> NARRATE rank #1 — MD/AD/PD {lords or '?'} "
            f"({cw.get('start_iso')}→{cw.get('end_iso')})."
        )
    nxt = v.get("next_child_window")
    if isinstance(nxt, dict) and nxt.get("start_iso") and not periods:
        lines.append(
            f"▸ NEXT scan window: {nxt.get('start_iso')} → {nxt.get('end_iso')} "
            f"AD/PD={nxt.get('ad', '?')}/{nxt.get('pd', '?')}"
        )
    sync = v.get("kp_dasha_sync") if isinstance(v.get("kp_dasha_sync"), dict) else {}
    active_kp = sync.get("active_now") or []
    if active_kp:
        lines.append(
            "▸ KP CSL active in current dasha: "
            + ", ".join(f"{x.get('house')}H={x.get('csl')}" for x in active_kp[:3])
        )
    elif sync.get("upcoming"):
        up = sync["upcoming"][0]
        nw = up.get("next_window") or {}
        if nw.get("start_iso"):
            lines.append(
                f"▸ KP CSL {up.get('csl')} next active {nw.get('start_iso')}→{nw.get('end_iso')}"
            )
    dt = v.get("double_transit") or {}
    if dt.get("active") and dt.get("verdict"):
        lines.append(f"▸ Double transit: {dt.get('verdict')}")
    dual = v.get("dual_track") if isinstance(v.get("dual_track"), dict) else {}
    if dual.get("winner") and dual.get("winner") != "NONE":
        lines.append(
            f"▸ Vedic+KP match: {dual.get('winner')} "
            f"(converged={dual.get('converged')})"
        )
    if v.get("strategy"):
        lines.append(f"▸ DIRECTIVE: {v['strategy']}")
    for f in (v.get("factors") or [])[:5]:
        if isinstance(f, str) and f.startswith("STEP5"):
            lines.append(f"  • {f}")
    for g in (v.get("brand_safety_warnings") or v.get("love_tone_rules") or [])[:3]:
        lines.append(f"  GUARD: {g}")
    lines.append(
        "RULE: current AD/PD weak → mat bolo 'abhi window chal raha'; "
        "NEXT scan window cite karo. Kabhi bhi pakka date guarantee nahi."
    )
    return "\n".join(lines)


# Backward compat
assess_love_timing = compute_love_window

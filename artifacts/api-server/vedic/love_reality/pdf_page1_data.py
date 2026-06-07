"""
Build Love Reality Pro page-1 dashboard payload (mirrors React love-reality-report).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def _chapter_body(pro: dict, key: str) -> str:
    for ch in pro.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        if (ch.get("key") or "").strip().lower() == key:
            return (ch.get("chapter_body") or ch.get("full_read") or "").strip()
    return ""


def _short(text: str, max_len: int = 220) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rsplit(" ", 1)[0] + "…"


def build_love_reality_page1_data(
    ctx: dict[str, Any],
    bundle: dict[str, Any],
    pro: dict[str, Any],
    p1: dict[str, Any],
    p2: dict[str, Any],
    *,
    report_id: str | None = None,
) -> dict[str, Any]:
    """Dashboard dict for premium PDF page 1."""
    dash = ctx.get("page1_dashboard") or {}
    scores = dash.get("scores") or []

    def pick(label: str) -> dict | None:
        ll = label.lower()
        for row in scores:
            if ll in str(row.get("label") or "").lower():
                return row
        return None

    def num(row: dict | None) -> int:
        try:
            return int(str((row or {}).get("value") or "0"))
        except (TypeError, ValueError):
            return 0

    dims = {d.get("key"): int(d.get("score") or 0) for d in (ctx.get("page4_dimensions") or [])}
    love = num(pick("Love")) or int(dash.get("love_score") or 0)
    breakup = num(pick("Breakup"))
    loyalty = num(pick("Loyalty"))
    reunion = num(pick("Return"))

    lc = bundle.get("love_compatibility") or {}
    bu = bundle.get("breakup_chances") or {}
    ly = bundle.get("loyalty_check") or {}
    wr = bundle.get("will_return") or {}
    fo = bundle.get("future_outcome") or {}

    summary = (
        dash.get("summary_index")
        or lc.get("emotional_summary")
        or lc.get("insight")
        or "Your charts show a complex bond with strong pull and recurring friction windows."
    )

    love_narr = _chapter_body(pro, "love_connection")
    loyalty_narr = _chapter_body(pro, "loyalty")
    breakup_narr = _chapter_body(pro, "breakup")
    future_narr = _chapter_body(pro, "future_outcome")

    snapshot = _short(love_narr or summary, 280)
    ai_bit = _short(pro.get("verdict") or bundle.get("narrative_bridge") or "", 160)
    narrative = snapshot
    if ai_bit and ai_bit not in snapshot:
        narrative = f"{snapshot} {ai_bit}".strip()

    moon = ctx.get("page5_moon") or {}
    insights: list[str] = []
    for r in (lc.get("reasons") or [])[:2]:
        insights.append(str(r).strip())
    if moon.get("shashtashtak"):
        insights.append("Moon rhythm mismatch — emotional pacing differs between partners.")
    else:
        insights.append("Moon signs support smoother emotional rhythm when stress is named early.")
    for r in (bu.get("reasons") or [])[:1]:
        insights.append(str(r).strip())
    if len(insights) < 4:
        insights.append("Repair within 24–48 hours after conflict — silence erodes loyalty scores.")
    insights = [i for i in insights if i][:4]

    remedies = ctx.get("page12_remedies") or {}
    rem_bullets = remedies.get("bullets") if isinstance(remedies, dict) else []
    checklist = ctx.get("page13_checklist") or {}
    chk_bullets = checklist.get("bullets") if isinstance(checklist, dict) else []
    recommendations = [str(x).strip() for x in (rem_bullets or chk_bullets or []) if str(x).strip()][:3]
    if not recommendations:
        recommendations = [
            "Repair within 24 hours after any argument",
            "Weekly 20-minute phone-free check-in",
            "Track dasha dates — avoid ultimatums in down windows",
        ]

    practical = [str(p).strip() for p in (pro.get("practical") or []) if str(p).strip()]
    if practical:
        recommendations = (practical + recommendations)[:3]

    strengths = [
        {"label": "Emotional magnetism", "value": min(100, love + 8)},
        {"label": "Shared growth intent", "value": min(100, loyalty)},
        {"label": "Karmic pull", "value": dims.get("karmic") or 62},
        {"label": "Attraction axis", "value": dims.get("attraction") or min(100, love)},
    ]
    challenges = [
        {"label": "Communication gaps", "value": min(100, breakup)},
        {"label": "Trust under stress", "value": min(100, max(0, 100 - loyalty))},
        {"label": "Timing misalignment", "value": min(100, 68 if reunion < 50 else 42)},
        {"label": "Conflict escalation", "value": min(100, max(breakup, 100 - loyalty) // 2 + 20)},
    ]

    def analysis(title: str, score: int, body: str, fallback: str) -> dict[str, Any]:
        return {
            "title": title,
            "score": score,
            "explanation": _short(body or fallback, 140),
        }

    return {
        "report_id": report_id or f"LR-{uuid.uuid4().hex[:8].upper()}",
        "generated_at": datetime.now(timezone.utc).strftime("%d %B %Y · %H:%M UTC"),
        "p1_name": p1.get("name") or "Partner A",
        "p2_name": p2.get("name") or "Partner B",
        "cosmic_score": int(dash.get("love_score") or love),
        "relationship_summary": _short(summary, 320),
        "metrics": [
            {
                "label": "Love Compatibility",
                "value": love,
                "interpretation": (pick("Love") or {}).get("band") or "Emotional resonance across charts",
            },
            {
                "label": "Breakup Risk",
                "value": breakup,
                "interpretation": (pick("Breakup") or {}).get("band") or "Stress-trigger separation probability",
            },
            {
                "label": "Loyalty & Trust",
                "value": loyalty,
                "interpretation": (pick("Loyalty") or {}).get("band") or "Commitment under pressure",
            },
            {
                "label": "Reunion Chance",
                "value": reunion,
                "interpretation": (pick("Return") or {}).get("band") or "Return window if separated",
            },
        ],
        "insights_narrative": _short(narrative, 360),
        "key_insights": insights,
        "analysis": [
            analysis(
                "Emotional Compatibility",
                dims.get("emotional") or max(0, min(100, int(love * 0.9))),
                love_narr,
                "Feelings run deep but peak at different speeds — name needs early.",
            ),
            analysis(
                "Communication",
                dims.get("communication") or max(20, 100 - breakup),
                breakup_narr,
                "Direct vs indirect styles clash under stress — use calm voice for sensitive topics.",
            ),
            analysis(
                "Trust & Loyalty",
                loyalty,
                loyalty_narr,
                "Trust holds with consistency; hidden resentment erodes loyalty faster than open conflict.",
            ),
            analysis(
                "Long-Term Potential",
                dims.get("stability") or max(0, min(100, (love + loyalty) // 2)),
                future_narr,
                "Workable with shared rituals — without repair habits, cycles repeat every 6–8 months.",
            ),
        ],
        "strengths": strengths,
        "challenges": challenges,
        "verdict": _short(
            (pro.get("verdict") or ctx.get("page14_closing") or "").strip()
            or f"Love {love}/100 · Breakup risk {breakup}/100 — use this as a timing map, not doom.",
            280,
        ),
        "recommendations": recommendations,
    }

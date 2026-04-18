"""
PRO AstroVastu deterministic response builder.

Takes the engine output (multi-room scan) and produces a comprehensive
bilingual report for the mobile UI.

Sections returned:
  - meta              : powered_by, generated_at, kundli summary
  - overall           : score 0-100, grade A-D, one-line verdict
  - mahadasha_alert   : active dasha lord + per-room conflict/favour list
  - rooms             : full per-room breakdown (verdict, severity, remedies)
  - priority_actions  : top 5 most urgent items, sorted by severity × dasha
  - classical_summary : deduped citation list from all rooms
  - footer            : "Powered by Advanced Cosmic Intelligence"

Deterministic (no LLM, no random). Same inputs always produce same output.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from astrovastu_response import build_basic_response


_IST = timezone(timedelta(hours=5, minutes=30))


def _grade(score: int) -> str:
    if score >= 85: return "A"
    if score >= 70: return "B"
    if score >= 50: return "C"
    return "D"


def _overall_summary(score: int) -> Dict[str, str]:
    if score >= 85:
        return {"en": "Excellent — your home strongly supports your kundli energies.",
                "hi": "Bahut shubh — ghar aapki kundli ko poori taakat se support karta hai."}
    if score >= 70:
        return {"en": "Good — most placements align well; small refinements suggested.",
                "hi": "Achha — adhiktar sthaan theek hain; thodi sudhar zaroori."}
    if score >= 50:
        return {"en": "Mixed — several placements need attention to unlock potential.",
                "hi": "Mishrit — kayi sthaan dhyan maangte hain."}
    return {"en": "Needs work — multiple critical placements require remediation.",
            "hi": "Sudhar zaroori — kayi sthaan turant theek karne padenge."}


def build_pro_response(scan_result: Dict[str, Any], plan: str = "pro") -> Dict[str, Any]:
    """
    Convert engine scan_result → user-facing PRO report.
    """
    rooms        = scan_result.get("rooms", [])
    overall      = scan_result.get("overall_score", 0)
    counts       = scan_result.get("verdict_counts", {})
    md_alert     = scan_result.get("mahadasha_alert")
    kctx         = scan_result.get("kundli_context", {})
    priority     = scan_result.get("priority_rooms", [])

    # ── Build per-room remedies via existing BASIC builder ────────────────
    room_reports: List[Dict[str, Any]] = []
    for r in rooms:
        # Re-use BASIC builder to get bilingual remedies + classical refs
        # (we already have engine outputs; pass them through)
        kundli_ctx_for_basic = {
            "lagna":         kctx.get("lagna"),
            "moon_sign":     kctx.get("moon_sign"),
            "mahadasha":     kctx.get("mahadasha"),
            "sade_sati":     {"active": kctx.get("sade_sati", False)},
            "atmakaraka":    kctx.get("atmakaraka"),
            "ishta_devata":  kctx.get("ishta_devata"),
            "weak_planets":  kctx.get("weak_planets", []),
        }
        # Re-construct dicts that build_basic_response expects.
        # PRO engine stores tie_breaker payload split across keys — flatten it
        # into the shape that build_basic_response consumes.
        tb_dict = {
            "verdict":              r["verdict"],   # may have been downgraded by mahadasha layer
            "generic_verdict":      r.get("generic_verdict", r["verdict"]),
            "applied_tie_breakers": r.get("tie_breaker", {}).get("applied", []),
            "reasons":              r.get("tie_breaker", {}).get("reasons", []),
            "classical_refs":       r.get("classical_refs", []),
            "personalization_reason": r.get("personalization_reason", {"en": "", "hi": ""}),
        }

        sev_dict = {
            "severity":  r["severity"],
            "multiplier": r["multiplier"],
            "reasons":   r.get("personalization", {}).get("reasons", []),
        }
        try:
            basic = build_basic_response(
                room_type=r["room_type"],
                direction=r.get("direction_long") or r["direction"],   # base builder expects long form
                kundli_context=kundli_ctx_for_basic,
                tie_breaker_result=tb_dict,
                severity_result=sev_dict,
                generic_room_rule=r.get("generic_rule", {}),
            )
        except Exception as exc:
            import traceback; traceback.print_exc()
            basic = {"remedies": [], "classical_refs": [],
                     "verdict_label": {"en": r["verdict"], "hi": r["verdict"]},
                     "personalization_reason": {"en": "", "hi": ""}}

        room_reports.append({
            "room_type":      r["room_type"],
            "direction":      r["direction"],
            "verdict":        r["verdict"],
            "verdict_label":  basic.get("verdict_label",
                                        {"en": r["verdict"], "hi": r["verdict"]}),
            "severity":       r["severity"],
            "severity_label": r.get("severity_label", r["severity"]),
            "score":          r["score"],
            "zone":           r["zone"],
            "mahadasha_layer": r["mahadasha_layer"],
            "remedies":       basic.get("remedies", []),
            "classical_refs": basic.get("classical_refs", []),
            "reasons":        basic.get("reasons", []),
        })

    # ── Priority actions list (deduped by room+direction) ─────────────────
    priority_actions: List[Dict[str, Any]] = []
    seen = set()
    for p in priority:
        key = (p["room_type"], p["direction"])
        if key in seen: continue
        seen.add(key)
        # Top 1-2 remedies for each priority room
        match = next((rr for rr in room_reports
                      if rr["room_type"] == p["room_type"]
                      and rr["direction"] == p["direction"]), None)
        top_remedies = (match["remedies"][:2] if match else [])
        priority_actions.append({
            "room_type":   p["room_type"],
            "direction":   p["direction"],
            "verdict":     p["verdict"],
            "severity":    p["severity"],
            "why":         (p.get("mahadasha_layer", {}).get("reason_en")
                            or (p.get("personalization", {}).get("reasons") or [None])[0]
                            or "Generic Vastu placement requires attention."),
            "remedies":    top_remedies,
        })

    # ── Deduplicated classical citations across all rooms ─────────────────
    seen_refs = set()
    classical_summary: List[Dict[str, str]] = []
    for rr in room_reports:
        for ref in rr.get("classical_refs", []):
            key = (ref.get("type", ""), ref.get("source", ""))
            if key in seen_refs: continue
            seen_refs.add(key)
            classical_summary.append(ref)

    return {
        "meta": {
            "powered_by":   "Advanced Cosmic Intelligence",
            "generated_at": datetime.now(_IST).isoformat(timespec="seconds"),
            "tier":         "pro",
            "rooms_count":  scan_result.get("rooms_count", len(rooms)),
        },
        "overall": {
            "score":   overall,
            "grade":   _grade(overall),
            "summary": _overall_summary(overall),
            "counts":  {
                "ideal":              counts.get("Ideal", 0),
                "acceptable":         counts.get("Acceptable", 0),
                "adjustment_needed":  counts.get("Adjustment Needed", 0),
                "avoid":              counts.get("Avoid", 0),
            },
        },
        "kundli_summary": {
            "lagna":        kctx.get("lagna"),
            "moon_sign":    kctx.get("moon_sign"),
            "mahadasha":    kctx.get("mahadasha"),
            "sade_sati":    bool(kctx.get("sade_sati")),
            "atmakaraka":   kctx.get("atmakaraka"),
            "ishta_devata": kctx.get("ishta_devata"),
        },
        "mahadasha_alert":   md_alert,
        "rooms":             room_reports,
        "priority_actions":  priority_actions,
        "classical_summary": classical_summary,
        "footer":            "Powered by Advanced Cosmic Intelligence",
    }

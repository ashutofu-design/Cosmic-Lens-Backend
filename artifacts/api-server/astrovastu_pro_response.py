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
from adjacency_rules    import evaluate_adjacencies
from topography_rules   import evaluate_topography
from dimension_rules    import evaluate_room_dimensions
from remedies_db        import merge_remedies


_IST = timezone(timedelta(hours=5, minutes=30))


# Score impact per classical finding — capped per-module then re-capped overall.
# Per-module cap prevents one module (e.g. many "Ideal" dimension ratios across
# 12 rooms) from saturating the budget and drowning out adjacency/topography.
_SEVERITY_DELTA  = {"critical": -5, "major": -3, "moderate": -1, "minor": 0}
_VERDICT_BONUS   = {"Ideal": 1, "Acceptable": 0, "Adjustment Needed": 0, "Avoid": 0}
_PER_MODULE_CAP  = 6   # |cap| per module (adjacency, topography, dimensions)
_CLASSICAL_CAP   = 15  # |total| cap across all classical modules


def _classical_score_impact(findings: List[Dict[str, Any]],
                            cap: int = _PER_MODULE_CAP) -> int:
    delta = 0
    for f in findings or []:
        sev      = (f.get("severity") or "").lower()
        verdict  = f.get("verdict") or ""
        delta += _SEVERITY_DELTA.get(sev, 0)
        delta += _VERDICT_BONUS.get(verdict, 0)
    return max(-cap, min(cap, delta))


def _grade(score: int) -> str:
    if score >= 85: return "A"
    if score >= 70: return "B"
    if score >= 50: return "C"
    return "D"


def _overall_summary(score: int) -> Dict[str, str]:
    try:
        from astrovastu_report_i18n import overall_summary_hi_dev
        hi_dev = overall_summary_hi_dev(score)
    except Exception:
        hi_dev = ""
    if score >= 85:
        return {
            "en": "Excellent — your home strongly supports your kundli energies.",
            "hn": "Bahut shubh — ghar aapki kundli ko poori taakat se support karta hai.",
            "hi": hi_dev or "अत्यंत शुभ — घर आपकी कुंडली की ऊर्जाओं को पूरी तरह सहारा देता है।",
            "hi_dev": hi_dev or "अत्यंत शुभ — घर आपकी कुंडली की ऊर्जाओं को पूरी तरह सहारा देता है।",
        }
    if score >= 70:
        return {
            "en": "Good — most placements align well; small refinements suggested.",
            "hn": "Achha — adhiktar sthaan theek hain; thodi sudhar zaroori.",
            "hi": hi_dev or "अच्छा — अधिकांश स्थान अनुकूल; थोड़ी सूक्ष्म सुधार पर्याप्त।",
            "hi_dev": hi_dev,
        }
    if score >= 50:
        return {
            "en": "Mixed — several placements need attention to unlock potential.",
            "hn": "Mishrit — kayi sthaan dhyan maangte hain.",
            "hi": hi_dev or "मिश्रित — कई स्थानों पर ध्यान देने से संभावनाएँ खुलेंगी।",
            "hi_dev": hi_dev,
        }
    return {
        "en": "Needs work — multiple critical placements require remediation.",
        "hn": "Sudhar zaroori — kayi sthaan turant theek karne padenge.",
        "hi": hi_dev or "सुधार आवश्यक — कई महत्वपूर्ण स्थानों पर तत्काल उपाय ज़रूरी।",
        "hi_dev": hi_dev,
    }


def build_pro_response(
    scan_result: Dict[str, Any],
    plan: str = "pro",
    extras: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Convert engine scan_result → user-facing PRO report.

    Optional `extras` dict (passed from flask route) may contain:
      - room_adjacencies:  [{a, b, relation}]   — for adjacency_rules
      - plot_topography:   {slope_low, slope_high, water_inlet, water_outlet}
      - floor_plan:        original list with optional length_ft/width_ft per room
    """
    extras = extras or {}
    rooms        = scan_result.get("rooms", [])
    single_room  = len(rooms) == 1
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

        # Kundli/vision remedies first; classical DB only tops up multi-room scans.
        _chart_on = bool(kctx.get("chart_vastu_active"))
        _max_db = (
            0
            if single_room and _chart_on
            else (1 if single_room else 2)
        )
        merged_remedies = merge_remedies(
            existing      = basic.get("remedies", []),
            room_type     = r["room_type"],
            verdict       = r["verdict"],
            business_type = None,
            max_total     = 3,
            max_db_classical=_max_db,
        )
        for rem in merged_remedies:
            if rem.get("source") not in ("classical_db", "vision"):
                rem.setdefault("source", "kundli_engine")
        for rem in merged_remedies:
            if not rem.get("hinglish"):
                rem["hinglish"] = rem.get("hindi") or rem.get("english") or ""

        pl = r.get("placement") or {}
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
            "remedies":       merged_remedies,
            "classical_refs": basic.get("classical_refs", []),
            "reasons":        basic.get("reasons", []),
            "placement":      pl,
            "ideal_directions_short": pl.get("ideal_directions_short", ""),
            "placement_status":     pl.get("placement_status", ""),
            "action":               pl.get("action", ""),
            "action_label_en":      pl.get("action_label_en", ""),
            "action_label_hn":      pl.get("action_label_hn", pl.get("action_label_hi", "")),
            "action_label_hi":      pl.get("action_label_hi", pl.get("action_label_hi_dev", "")),
            "action_label_hi_dev":  pl.get("action_label_hi_dev", pl.get("action_label_hi", "")),
            "summary_en":           pl.get("summary_en", ""),
            "summary_hn":           pl.get("summary_hn", ""),
            "summary_hi":           pl.get("summary_hi", pl.get("summary_hi_dev", "")),
            "summary_hi_dev":       pl.get("summary_hi_dev", pl.get("summary_hi", "")),
            "astro_personalized":   r.get("astro_personalized", pl.get("astro_personalized", False)),
            "astro_note_en":        r.get("astro_note_en", pl.get("astro_note_en", "")),
            "astro_note_hn":        pl.get("astro_note_hn", pl.get("astro_note_hi", "")),
            "astro_note_hi":        r.get("astro_note_hi", pl.get("astro_note_hi_dev", "")),
            "astro_note_hi_dev":    r.get("astro_note_hi_dev", pl.get("astro_note_hi", "")),
            "classical_ideal_short": pl.get("classical_ideal_short", ""),
            "chart_note_en":        (
                (r.get("chart_stress_layer") or {}).get("chart_note_en")
                or r.get("astro_note_en", pl.get("astro_note_en", ""))
            ),
            "chart_note_hi":        (
                (r.get("chart_stress_layer") or {}).get("chart_note_hi")
                or r.get("astro_note_hi", pl.get("astro_note_hi", ""))
            ),
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
        pl = (match or {}).get("placement") or p.get("placement") or {}
        priority_actions.append({
            "room_type":   p["room_type"],
            "direction":   p["direction"],
            "verdict":     p["verdict"],
            "severity":    p["severity"],
            "ideal_directions_short": pl.get("ideal_directions_short", ""),
            "action_label_en": pl.get("action_label_en", ""),
            "action_label_hn": pl.get("action_label_hn", pl.get("action_label_hi", "")),
            "action_label_hi": pl.get("action_label_hi", pl.get("action_label_hi_dev", "")),
            "action_label_hi_dev": pl.get("action_label_hi_dev", ""),
            "placement_status": pl.get("placement_status", ""),
            "why":         pl.get("summary_en")
                            or p.get("mahadasha_layer", {}).get("reason_en")
                            or (p.get("personalization", {}).get("reasons") or [None])[0]
                            or "Placement needs attention per your chart.",
            "why_hn":      pl.get("summary_hn", pl.get("summary_hi", "")),
            "why_hi":      pl.get("summary_hi", pl.get("summary_hi_dev", "")),
            "why_hi_dev":  pl.get("summary_hi_dev", pl.get("summary_hi", "")),
            "remedies":    top_remedies,
        })

    # ── Classical rule modules: adjacency / topography / dimension ───────
    adjacency_findings  = evaluate_adjacencies(extras.get("room_adjacencies") or [])
    topography_findings = evaluate_topography(extras.get("plot_topography") or {})
    dimension_findings: List[Dict[str, Any]] = []
    for fp_room in (extras.get("floor_plan") or []):
        if not isinstance(fp_room, dict):
            continue
        d = evaluate_room_dimensions(fp_room)
        if d:
            dimension_findings.append(d)

    # Score impact from classical modules (each capped, then summed & re-capped)
    classical_impact = (
        _classical_score_impact(adjacency_findings)
        + _classical_score_impact(topography_findings)
        + _classical_score_impact(
            [df.get("ratio") or {} for df in dimension_findings]
            + [df.get("aaya")  or {} for df in dimension_findings]
        )
    )
    classical_impact = max(-_CLASSICAL_CAP, min(_CLASSICAL_CAP, classical_impact))
    if classical_impact != 0:
        overall = max(30, min(100, overall + classical_impact))

    # ── Executive bullets for premium PDF (template Part A) ───────────────
    executive_fixes: List[Dict[str, str]] = []
    for pa in priority_actions[:3]:
        executive_fixes.append({
            "en": (
                f"{(pa.get('room_type') or '').replace('_', ' ').title()} "
                f"(now {pa.get('direction', '')}) → ideal {pa.get('ideal_directions_short', '')} "
                f"— {pa.get('action_label_en', '')}"
            ),
            "hi": (
                f"{(pa.get('room_type') or '').replace('_', ' ').title()} "
                f"({pa.get('direction', '')}) → ideal {pa.get('ideal_directions_short', '')} "
                f"— {pa.get('action_label_hi', '')}"
            ),
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

    report = {
        "meta": {
            "powered_by":   "Cosmic Intelligence",
            "generated_at": datetime.now(_IST).isoformat(timespec="seconds"),
            "tier":         "pro",
            "rooms_count":  scan_result.get("rooms_count", len(rooms)),
            "astrovastu_mode": "chart_personalized",
            "method_en": (
                "Classical Vastu room rules adjusted for your Lagna, active Mahadasha, "
                "weak planets, and Ishta Devata."
            ),
            "method_hi": (
                "Shastriya Vastu + aapki Lagna, chal rahi Mahadasha, kamzor grahon "
                "aur Ishta Devata ke hisaab se room-wise ideal disha."
            ),
            "chart_vastu_active": bool(
                (scan_result.get("kundli_context") or {}).get("chart_vastu_active")
            ),
            "chart_stress_count": len(
                (scan_result.get("kundli_context") or {}).get("chart_stress_hits") or []
            ),
            "upload_filename": (extras or {}).get("upload_filename") or "",
            "scan_source": (extras or {}).get("scan_source") or (
                "single_room" if len(rooms) == 1 else "multi_room"
            ),
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
        "executive_fixes":   executive_fixes,
        "classical_summary": classical_summary,
        "adjacency_findings":  adjacency_findings,
        "topography_findings": topography_findings,
        "dimension_findings":  dimension_findings,
        "classical_score_impact": classical_impact,
        "footer":            "Powered by Advanced Cosmic Intelligence",
    }

    report_lang = (extras.get("report_lang") or "en").strip().lower()
    if report_lang == "hinglish":
        report_lang = "hn"
    try:
        from astrovastu_report_i18n import apply_report_language
        report = apply_report_language(report, report_lang)
    except Exception:
        pass
    return report

"""
Business Vastu Response Builder — Phase 4
==========================================
Bilingual (English + Hindi) deterministic report formatter for the
Business Vastu deep-scan engine. Mirrors `astrovastu_pro_response` shape
so the mobile UI can reuse most rendering primitives.

Sections returned:
  - overall            : score, grade, bilingual headline
  - business_summary   : type-specific intro (Shop / Office / Factory)
  - mahadasha_alert    : owner's active dasha vs floor plan
  - stakeholder        : partner-synergy block (always present)
  - muhurat            : optional muhurat-chart alignment
  - rooms              : full per-room report
  - priority_actions   : top 5 fixes (critical-rooms first)
  - classical_summary  : deduped scriptural references
  - footer             : "Powered by Advanced Cosmic Intelligence"
"""

from typing import Any, Dict, List


def _grade(score: int) -> str:
    if score >= 85: return "A"
    if score >= 70: return "B"
    if score >= 55: return "C"
    return "D"


def _overall_summary(score: int, business_type: str) -> Dict[str, str]:
    btype_en = business_type.title()
    btype_hi = {"shop": "Dukaan", "office": "Office",
                "factory": "Karkhana"}.get(business_type, "Vyapar")
    if score >= 85:
        return {"en": f"Excellent — your {btype_en} layout is in strong harmony with classical Vastu and the active planetary cycle.",
                "hi": f"Utkrisht — aapka {btype_hi} Vastu shastra aur grah-kal se purna anukul hai."}
    if score >= 70:
        return {"en": f"Good — your {btype_en} is largely well-aligned. A few targeted fixes will lift it further.",
                "hi": f"Achha — aapka {btype_hi} prayah anukul hai. Kuch sudhar se aur uchcha jayega."}
    if score >= 55:
        return {"en": f"Fair — several rooms need adjustment. Prioritise critical placements (entrance, owner seat, cash counter).",
                "hi": f"Madhyam — kai kamron mein sudhar zaroori. Mukhya sthaan (dwar, swami, golak) pehle theek karein."}
    return {"en": f"Action needed — multiple critical placements conflict with both Vastu and the planetary cycle. Plan a phased remediation.",
            "hi": f"Sudhar avashyak — kai mukhya sthaan Vastu aur grah-kal se virodhi. Charan-bandh upaay yojana banayein."}


def _business_intro(business_type: str) -> Dict[str, str]:
    intros = {
        "shop": {
            "en": "Shop Vastu emphasises customer flow, money retention, and owner authority. Critical zones: entrance (NE/N/E), owner seat (SW), cash counter (N/NE).",
            "hi": "Dukaan Vastu mein grahak ka aana, dhan ka thaharna, aur swami ka adhikar mukhya hai. Mukhya sthaan: dwar (NE/N/E), swami sthaan (SW), golak (N/NE).",
        },
        "office": {
            "en": "Office Vastu balances productivity (S/SE), wealth-attraction (N/NE), and leadership clarity (SW). Reception drives first impression; conference rooms shape decisions.",
            "hi": "Office Vastu mein utpadan-shakti (S/SE), Lakshmi-akarshan (N/NE), aur netritva-spashtata (SW) ka santulan zaroori hai.",
        },
        "factory": {
            "en": "Factory Vastu manages heavy energies — fire (machinery: SE), heavy machine (SW), storage (NW/W), boiler (SE only). Mis-placed heavy zones drain finances rapidly.",
            "hi": "Karkhana Vastu mein bhari urja ka sahi sthaan zaroori — agni (machinery: SE), bhari yantra (SW), bhandar (NW/W). Galat sthaan dhan ka khand kar deta hai.",
        },
    }
    return intros.get(business_type, {"en": "Business Vastu deep-scan.",
                                       "hi": "Vyapar Vastu vishleshan."})


def _room_card(r: Dict[str, Any]) -> Dict[str, Any]:
    """One room rendered for the mobile UI list."""
    md = r.get("mahadasha_layer", {}) or {}
    biz = r.get("business_layer", {}) or {}
    zone = r.get("zone", {}) or {}
    return {
        "room_type":      r["room_type"],
        "direction":      r["direction"],
        "direction_long": r.get("direction_long", r["direction"]),
        "verdict":        r["verdict"],
        "severity":       r.get("severity", "minor"),
        "severity_label": r.get("severity_label", r.get("severity", "minor")),
        "score":          r.get("score", 50),
        "is_critical":    r.get("is_critical", False),
        "zone":           zone,
        "mahadasha":      {
            "applies":   md.get("applies", False),
            "kind":      md.get("kind"),
            "reason_en": md.get("reason_en"),
            "reason_hi": md.get("reason_hi"),
        },
        "business_rule":  {
            "applies":   biz.get("applies", False),
            "kind":      biz.get("kind"),
            "reason_en": biz.get("reason_en"),
            "reason_hi": biz.get("reason_hi"),
        },
        "generic_rule": r.get("generic_rule", {}),
        "tie_breaker":  r.get("tie_breaker", {}),
        "classical_refs": r.get("classical_refs", []),
    }


def _priority_action(r: Dict[str, Any]) -> Dict[str, Any]:
    md = r.get("mahadasha_layer", {}) or {}
    biz = r.get("business_layer", {}) or {}

    why_en_parts = []
    why_hi_parts = []
    if r.get("is_critical"):
        why_en_parts.append("Critical business zone")
        why_hi_parts.append("Mukhya vyapar sthaan")
    if biz.get("applies") and biz.get("kind") == "avoid":
        why_en_parts.append(biz.get("reason_en") or "")
        why_hi_parts.append(biz.get("reason_hi") or "")
    if md.get("applies") and md.get("kind") == "conflict":
        why_en_parts.append(md.get("reason_en") or "")
        why_hi_parts.append(md.get("reason_hi") or "")

    return {
        "room_type":      r["room_type"],
        "direction":      r["direction"],
        "verdict":        r["verdict"],
        "severity_label": r.get("severity_label", r.get("severity", "minor")),
        "is_critical":    r.get("is_critical", False),
        "why_en":         " · ".join([p for p in why_en_parts if p]) or "Adjust per generic rule.",
        "why_hi":         " · ".join([p for p in why_hi_parts if p]) or "Saadharan niyam ke anusaar sudhar.",
    }


def build_business_response(scan: Dict[str, Any], plan: str = "free") -> Dict[str, Any]:
    """Top-level formatter — input is the dict from analyze_business()."""
    if scan.get("error"):
        return {"error": scan["error"], "rooms": []}

    btype  = scan.get("business_type", "shop")
    rooms  = scan.get("rooms", []) or []
    score  = scan.get("overall_score", 0)
    counts = scan.get("verdict_counts", {})

    # Normalise counts to mobile-friendly snake_case (mirrors PRO shape)
    counts_norm = {
        "ideal":             counts.get("Ideal", 0),
        "acceptable":        counts.get("Acceptable", 0),
        "adjustment_needed": counts.get("Adjustment Needed", 0),
        "avoid":             counts.get("Avoid", 0),
    }

    return {
        "kind":   "business_vastu",
        "plan":   plan,
        "meta":   {
            "powered_by":   "Advanced Cosmic Intelligence",
            "tier":         f"business_{btype}",
            "rooms_count":  len(rooms),
        },
        "overall": {
            "score":   score,
            "grade":   _grade(score),
            "summary": _overall_summary(score, btype),
            "counts":  counts_norm,
        },
        "business_summary": {
            "type":    btype,
            "intro":   _business_intro(btype),
        },
        "mahadasha_alert":  scan.get("mahadasha_alert"),
        "stakeholder":      scan.get("stakeholder", {}),
        "muhurat":          scan.get("muhurat"),
        "rooms":            [_room_card(r) for r in rooms],
        "priority_actions": [_priority_action(r) for r in scan.get("priority_rooms", [])],
        "classical_summary": _dedupe_refs(rooms),
        "owner_context":    scan.get("owner_context", {}),
        "footer":  {
            "en": "Powered by Advanced Cosmic Intelligence — based on Brihat Samhita, Mayamatam, and personalised Jyotish.",
            "hi": "Advanced Cosmic Intelligence dvara — Brihat Samhita, Mayamatam, aur vyaktigat Jyotish par adharit.",
        },
    }


def _dedupe_refs(rooms: List[Dict[str, Any]]) -> List[str]:
    seen, out = set(), []
    for r in rooms:
        for ref in r.get("classical_refs", []) or []:
            if isinstance(ref, str) and ref not in seen:
                seen.add(ref)
                out.append(ref)
    return out[:8]

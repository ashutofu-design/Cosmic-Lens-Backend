"""
Business Vastu Engine — Phase 4
================================
Deterministic (NO LLM) deep-scan engine for commercial premises:
shops, offices, and factories. Combines:

  1. Premises Vastu  — per-room verdicts using the proven AstroVastu PRO
     `analyze_room` (mahadasha-aware, Vastu Purusha grid, classical refs).
  2. Owner kundli    — drives the mahadasha layer for the primary
     decision-maker, just like residential PRO.
  3. Partner kundlis — up to 3 stakeholders (optional). Cross-stakeholder
     synergy (common dasha conflicts/strengths) shapes priority.
  4. Muhurat chart   — optional business-start / registration chart. We
     surface a high-level alignment note (current dasha vs muhurat dasha).
  5. Business-type rules — entrance / owner-seat / cash-counter / vault
     etc. have type-specific ideal directions. A "critical room" placed
     wrong is escalated to MAJOR severity even if generic Vastu is mild.

Branding: deterministic — never reveal AI/LLM.
"""

from typing import Any, Dict, List, Optional

from astrovastu_pro_engine import (
    ZONE_LORD,
    VERDICT_SCORE,
    SEV_WEIGHT,
    _norm_direction,
    _to_long_direction,
    _escalate_severity,
    analyze_room,
    mahadasha_direction_check,
)
from astrovastu_engine import build_kundli_context
from astrovastu_rules import get_planet_direction


# ─────────────────────────────────────────────────────────────────────
# Business-type critical-room placement rules
# ─────────────────────────────────────────────────────────────────────
# Each entry: ideal directions (Acceptable+) and forbidden (Avoid).
# A critical room mis-placed → severity escalated to "major" or "critical".
# Sources: Brihat Samhita ch. 53-56, Mayamatam ch. 9-10, Manasara ch. 9.
BUSINESS_CRITICAL: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    "shop": {
        "entrance":      {"ideal": ["N", "NE", "E"],   "avoid": ["SW", "S"]},
        "owner_seat":    {"ideal": ["SW", "S", "W"],    "avoid": ["NE", "N"]},
        "cash_counter":  {"ideal": ["N", "NE"],         "avoid": ["S", "SE", "SW"]},
        "vault":         {"ideal": ["N", "NE"],         "avoid": ["S", "SW"]},
        "stock_storage": {"ideal": ["SW", "W", "S"],    "avoid": ["NE"]},
        "display":       {"ideal": ["E", "N", "NE"],    "avoid": ["SW"]},
    },
    "office": {
        "entrance":       {"ideal": ["N", "NE", "E"],  "avoid": ["SW", "S"]},
        "owner_cabin":    {"ideal": ["SW", "S", "W"],  "avoid": ["NE", "N"]},
        "owner_seat":     {"ideal": ["SW", "S", "W"],  "avoid": ["NE", "N"]},
        "reception":      {"ideal": ["NE", "N", "E"],  "avoid": ["SW", "S"]},
        "conference":     {"ideal": ["NW", "W", "N"],  "avoid": ["SE", "S"]},
        "accounts":       {"ideal": ["N", "NE"],        "avoid": ["S", "SE", "SW"]},
        "vault":          {"ideal": ["N", "NE"],        "avoid": ["S", "SW"]},
        "server_room":    {"ideal": ["SE", "S"],        "avoid": ["NE", "N"]},
        "pantry":         {"ideal": ["SE"],             "avoid": ["NE", "N"]},
        "toilet":         {"ideal": ["NW", "W"],        "avoid": ["NE", "C"]},
    },
    "factory": {
        "entrance":      {"ideal": ["N", "NE", "E"],   "avoid": ["SW", "S"]},
        "owner_cabin":   {"ideal": ["SW", "S", "W"],   "avoid": ["NE", "N"]},
        "owner_seat":    {"ideal": ["SW", "S", "W"],   "avoid": ["NE", "N"]},
        "machinery":     {"ideal": ["SE", "S"],         "avoid": ["NE", "N"]},
        "raw_storage":   {"ideal": ["NW", "W"],         "avoid": ["NE", "SE"]},
        "finished_goods":{"ideal": ["NW", "W"],         "avoid": ["NE", "SE"]},
        "boiler":        {"ideal": ["SE"],              "avoid": ["NE", "N", "NW"]},
        "heavy_machine": {"ideal": ["SW", "S", "W"],    "avoid": ["NE", "N", "E"]},
        "labour_quarter":{"ideal": ["NW", "W"],         "avoid": ["NE"]},
    },
}


def _is_critical(business_type: str, room_type: str) -> bool:
    rules = BUSINESS_CRITICAL.get(business_type, {})
    return room_type.lower() in rules


# Rooms whose IDEAL directions are exclusive — ANY direction outside the
# ideal list is treated as Avoid (per classical strict prescription).
# Examples: vault must be N/NE only; boiler must be SE only.
STRICT_ONLY_ROOMS: Dict[str, set] = {
    "shop":    {"vault", "cash_counter"},
    "office":  {"vault", "accounts", "server_room"},
    "factory": {"boiler", "heavy_machine", "machinery"},
}


def business_specific_check(business_type: str, room_type: str, direction: str) -> Dict[str, Any]:
    """
    Return whether this critical room is well-placed for the business type.
    Non-critical rooms return {applies: False}.

    For STRICT_ONLY rooms (vault, boiler, etc.) any direction outside the
    ideal list is treated as Avoid — these placements are exclusive per
    classical Vastu (Brihat Samhita ch. 53; Mayamatam ch. 9).
    """
    rules = BUSINESS_CRITICAL.get(business_type, {})
    spec  = rules.get(room_type.lower())
    if not spec:
        return {"applies": False}

    d = _norm_direction(direction)
    ideal_dirs = spec.get("ideal", [])
    avoid_dirs = spec.get("avoid", [])
    is_strict  = room_type.lower() in STRICT_ONLY_ROOMS.get(business_type, set())

    if d in ideal_dirs:
        return {
            "applies":   True,
            "kind":      "ideal",
            "severity_delta": -1,
            "reason_en": f"{room_type.replace('_', ' ').title()} in {d} is ideal for a {business_type}.",
            "reason_hi": f"{business_type} ke liye {room_type.replace('_', ' ')} {d} mein utkrisht hai.",
        }
    if d in avoid_dirs:
        return {
            "applies":   True,
            "kind":      "avoid",
            "severity_delta": +2,                # critical room in avoid dir → escalate hard
            "reason_en": f"{room_type.replace('_', ' ').title()} in {d} is highly inauspicious for a {business_type} — relocate or apply remedy.",
            "reason_hi": f"{business_type} ke liye {room_type.replace('_', ' ')} {d} mein bahut ashubh hai — sthaan badle ya upaay kare.",
        }
    if is_strict:
        # Strict-only room placed outside the ideal list → treat as Avoid.
        ideal_str = "/".join(ideal_dirs) if ideal_dirs else "ideal direction"
        return {
            "applies":   True,
            "kind":      "avoid",
            "severity_delta": +2,
            "reason_en": (f"{room_type.replace('_', ' ').title()} must be placed in "
                          f"{ideal_str} only — {d} is not classically permitted for a {business_type}."),
            "reason_hi": (f"{business_type} ke liye {room_type.replace('_', ' ')} keval "
                          f"{ideal_str} mein hi sahi hai — {d} shastra-anukul nahi."),
        }
    return {"applies": True, "kind": "neutral", "severity_delta": 0}


# ─────────────────────────────────────────────────────────────────────
# Stakeholder synergy (owner + up to 3 partners)
# ─────────────────────────────────────────────────────────────────────
def _partner_synergy(owner_ctx: Dict[str, Any],
                     partner_ctxs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Cross-stakeholder dasha-direction synergy. Returns shared favourable
    directions (where ALL stakeholders' active dashas agree) and shared
    conflict directions (where ALL stakeholders' active dashas conflict).
    These weights are surfaced in priority_actions to favour decisions
    aligned with the entire ownership group.
    """
    if not partner_ctxs:
        return {
            "partner_count": 0,
            "common_favour": [],
            "common_conflict": [],
            "summary_en": "Single owner — no partner synergy applied.",
            "summary_hi": "Akele swami — bhagidaar ka koi prabhav nahi.",
        }

    all_ctxs = [owner_ctx] + partner_ctxs
    # For each stakeholder collect their active dasha lord's natural direction.
    # We require EVERY stakeholder to have a resolved dasha — otherwise we
    # cannot honestly claim a "common" pattern.
    dirs: List[str] = []
    unresolved = 0
    for ctx in all_ctxs:
        lord = ctx.get("current_mahadasha")
        d = get_planet_direction(str(lord).strip().capitalize()) if lord else None
        if d:
            dirs.append(_norm_direction(d))
        else:
            unresolved += 1

    n = len(partner_ctxs)
    if unresolved > 0:
        return {
            "partner_count":  n,
            "owner_lord":     owner_ctx.get("current_mahadasha"),
            "partner_lords":  [c.get("current_mahadasha") for c in partner_ctxs],
            "common_favour":  [],
            "common_conflict":[],
            "insufficient_data": True,
            "summary_en": (f"{n} partner(s) added; "
                           f"{unresolved} stakeholder(s) lack resolvable Mahadasha — "
                           "decisions need per-partner weighing."),
            "summary_hi": (f"{n} bhagidaar; "
                           f"{unresolved} ki Mahadasha spasht nahi — "
                           "har bhagidaar par alag vichar zaroori."),
        }

    OPPOSITE = {"N":"S","S":"N","E":"W","W":"E","NE":"SW","SW":"NE","NW":"SE","SE":"NW"}

    common_favour: List[str] = []
    common_conflict: List[str] = []
    # A direction is a "common favour" if every stakeholder's lord shares it.
    if len(set(dirs)) == 1:
        common_favour = [dirs[0]]
        common_conflict = [OPPOSITE.get(dirs[0])] if OPPOSITE.get(dirs[0]) else []
    else:
        # Multiple lords across partners — flag any direction that is
        # the OPPOSITE of every lord (universally bad for the team).
        opposites_of_all = set(OPPOSITE.get(d) for d in dirs if OPPOSITE.get(d))
        if len(opposites_of_all) == 1:
            common_conflict = list(opposites_of_all)

    return {
        "partner_count":  n,
        "owner_lord":     owner_ctx.get("current_mahadasha"),
        "partner_lords":  [c.get("current_mahadasha") for c in partner_ctxs],
        "common_favour":  common_favour,
        "common_conflict":common_conflict,
        "insufficient_data": False,
        "summary_en": (
            f"{n} partner(s) added. "
            + (f"Group favours direction(s): {', '.join(common_favour)}. " if common_favour else "")
            + (f"Group conflicts: {', '.join(common_conflict)}. " if common_conflict else "")
            + ("No common dasha pattern — decisions need per-partner weighing."
               if not (common_favour or common_conflict) else "")
        ),
        "summary_hi": (
            f"{n} bhagidaar jude. "
            + (f"Samuh ko shubh disha: {', '.join(common_favour)}. " if common_favour else "")
            + (f"Samuh ke liye virodhi: {', '.join(common_conflict)}. " if common_conflict else "")
        ),
    }


# ─────────────────────────────────────────────────────────────────────
# Muhurat alignment (optional — date-only acceptable in v1)
# ─────────────────────────────────────────────────────────────────────
def _muhurat_alignment(muhurat_ctx: Optional[Dict[str, Any]],
                       owner_ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Compares the muhurat-chart dasha lord to the owner's active dasha lord.
    If they match → ALIGNED (the business is "in flow" with its starting
    energy). If opposite → STRESSED (current cycle pulls against the
    foundation — explains lulls / friction).

    `muhurat_ctx` should have shape similar to build_kundli_context(): a
    dict with at least "current_mahadasha".
    """
    if not muhurat_ctx:
        return None

    md_owner   = (owner_ctx.get("current_mahadasha")    or "").strip().capitalize()
    md_muhurat = (muhurat_ctx.get("current_mahadasha")  or "").strip().capitalize()
    if not md_owner or not md_muhurat:
        return {
            "applies":  False,
            "summary_en": "Muhurat chart provided but dasha could not be resolved.",
            "summary_hi": "Muhurat chart diya gaya parantu dasha nahi mil saki.",
        }

    if md_owner == md_muhurat:
        return {
            "applies":   True,
            "alignment": "aligned",
            "owner_md":  md_owner, "muhurat_md": md_muhurat,
            "summary_en": (f"Excellent alignment — owner's current Mahadasha ({md_owner}) "
                           "matches the business muhurat. Expect natural momentum."),
            "summary_hi": (f"Utkrisht milaan — swami ki chal Mahadasha ({md_owner}) "
                           "muhurat se mil rahi hai. Sahej pragati ki sambhavna."),
        }

    OPPOSITE_PLANETS = {"Sun":"Saturn","Saturn":"Sun","Mars":"Venus","Venus":"Mars",
                        "Moon":"Mercury","Mercury":"Moon","Jupiter":"Rahu","Rahu":"Jupiter",
                        "Ketu":"Mars"}
    if OPPOSITE_PLANETS.get(md_owner) == md_muhurat:
        return {
            "applies":   True,
            "alignment": "stressed",
            "owner_md":  md_owner, "muhurat_md": md_muhurat,
            "summary_en": (f"Current Mahadasha ({md_owner}) opposes the muhurat "
                           f"foundation ({md_muhurat}). Expect friction; review big "
                           "decisions and consider strengthening remedies."),
            "summary_hi": (f"Chal rahi Mahadasha ({md_owner}) muhurat ki neev "
                           f"({md_muhurat}) ke virodhi hai. Vighna sambhav, mahatvapurn "
                           "nirnay savdhani se le aur upaay kare."),
        }

    return {
        "applies":   True,
        "alignment": "neutral",
        "owner_md":  md_owner, "muhurat_md": md_muhurat,
        "summary_en": (f"Current Mahadasha ({md_owner}) and muhurat foundation "
                       f"({md_muhurat}) are neutral — neither boost nor friction."),
        "summary_hi": (f"Chal rahi Mahadasha ({md_owner}) aur muhurat neev "
                       f"({md_muhurat}) tatasthya hai."),
    }


# ─────────────────────────────────────────────────────────────────────
# Per-room analysis with business overlay
# ─────────────────────────────────────────────────────────────────────
def analyze_business_room(room: Dict[str, Any], owner_ctx: Dict[str, Any],
                           business_type: str) -> Dict[str, Any]:
    """
    Wraps the proven PRO `analyze_room` then layers business-specific
    critical-room rules on top. Critical rooms in 'avoid' direction are
    forced to verdict=Avoid with major+ severity.
    """
    base = analyze_room(room, owner_ctx)
    biz_layer = business_specific_check(business_type, base["room_type"], base["direction"])
    base["business_layer"] = biz_layer
    base["is_critical"]    = _is_critical(business_type, base["room_type"])

    if biz_layer.get("applies"):
        # Apply severity delta and verdict overrides
        if biz_layer["kind"] == "avoid":
            base["verdict"]  = "Avoid"
            base["severity"] = _escalate_severity(base.get("severity", "minor"),
                                                   biz_layer.get("severity_delta", 0))
            base["score"]    = VERDICT_SCORE["Avoid"]
        elif biz_layer["kind"] == "ideal" and base["verdict"] == "Adjustment Needed":
            # ideal placement upgrades a minor adjustment
            base["verdict"]  = "Acceptable"
            base["severity"] = _escalate_severity(base.get("severity", "minor"),
                                                   biz_layer.get("severity_delta", 0))
            base["score"]    = VERDICT_SCORE["Acceptable"]

    return base


# ─────────────────────────────────────────────────────────────────────
# Top-level entry
# ─────────────────────────────────────────────────────────────────────
def analyze_business(floor_plan: List[Dict[str, Any]],
                     business_type: str,
                     owner_kundli: Dict[str, Any],
                     partner_kundlis: Optional[List[Dict[str, Any]]] = None,
                     muhurat_kundli: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Returns a structured Business Vastu deep-scan result.

    Required:
      - floor_plan     : list of {room_type, direction}
      - business_type  : "shop" | "office" | "factory"
      - owner_kundli   : raw kundli dict (chart_data shape) — required

    Optional (engine still works without them — but richer with):
      - partner_kundlis: list of up to 3 partner chart_data dicts
      - muhurat_kundli : business-start chart_data (from registration date)
    """
    if not floor_plan or not isinstance(floor_plan, list):
        return {"error": "empty_floor_plan", "rooms": []}
    if business_type not in BUSINESS_CRITICAL:
        return {"error": "invalid_business_type", "rooms": []}

    owner_ctx    = build_kundli_context(owner_kundli or {})
    partner_ctxs = [build_kundli_context(k or {}) for k in (partner_kundlis or [])][:3]
    muhurat_ctx  = build_kundli_context(muhurat_kundli) if muhurat_kundli else None

    rooms = [analyze_business_room(r, owner_ctx, business_type)
             for r in floor_plan if isinstance(r, dict)]

    # ── Aggregate metrics ──
    overall_score = round(sum(r["score"] for r in rooms) / len(rooms)) if rooms else 0

    counts = {"Ideal": 0, "Acceptable": 0, "Adjustment Needed": 0, "Avoid": 0}
    for r in rooms:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    # Critical-room failures come first, then severity sort
    def _biz_priority(r: Dict[str, Any]) -> tuple:
        crit_w   = 2 if r.get("is_critical") and r.get("verdict") == "Avoid" else 0
        sev_w    = SEV_WEIGHT.get(r.get("severity", "minor"), 1)
        verdict_w= {"Avoid": 4, "Adjustment Needed": 3, "Acceptable": 2, "Ideal": 1}.get(
            r.get("verdict", "Acceptable"), 2)
        md_w     = 1 if r.get("mahadasha_layer", {}).get("kind") == "conflict" else 0
        return (-(crit_w * 10 + sev_w + verdict_w + md_w), r.get("room_type", ""))

    priority = sorted(rooms, key=_biz_priority)[:5]

    # ── Mahadasha-wide alert (owner-driven, same as PRO) ──
    md_alert = None
    md_lord = owner_ctx.get("current_mahadasha")
    if md_lord:
        md_dir_raw = get_planet_direction(str(md_lord).strip().capitalize())
        if md_dir_raw:
            md_dir_norm = _norm_direction(md_dir_raw)
            conflicts   = [r for r in rooms if r["mahadasha_layer"].get("kind") == "conflict"]
            favourables = [r for r in rooms if r["mahadasha_layer"].get("kind") == "favourable"]
            md_alert = {
                "active_lord":      md_lord,
                "lord_direction":   md_dir_norm,
                "conflict_rooms":   [r["room_type"] for r in conflicts],
                "favourable_rooms": [r["room_type"] for r in favourables],
                "summary_en": (f"Owner's active Mahadasha: {md_lord} (rules {md_dir_norm}). "
                               f"{len(conflicts)} room(s) conflict, "
                               f"{len(favourables)} room(s) favoured."),
                "summary_hi": (f"Swami ki chal Mahadasha: {md_lord} ({md_dir_norm} ka swami). "
                               f"{len(conflicts)} kamre virodhi, "
                               f"{len(favourables)} kamre shubh."),
            }

    synergy  = _partner_synergy(owner_ctx, partner_ctxs)
    muhurat  = _muhurat_alignment(muhurat_ctx, owner_ctx)

    return {
        "business_type":   business_type,
        "rooms":           rooms,
        "rooms_count":     len(rooms),
        "overall_score":   overall_score,
        "verdict_counts":  counts,
        "priority_rooms":  priority,
        "mahadasha_alert": md_alert,
        "stakeholder":     synergy,
        "muhurat":         muhurat,
        "owner_context":   {
            "lagna":      owner_ctx.get("lagna"),
            "moon_sign":  owner_ctx.get("moon_sign"),
            "mahadasha":  owner_ctx.get("current_mahadasha"),
            "atmakaraka": owner_ctx.get("atmakaraka"),
        },
    }

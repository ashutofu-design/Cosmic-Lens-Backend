"""Remedy Engine v1.0 — hybrid 3-tier remedy selector.

The PUBLIC API for ALL topical engines (health, marriage, career, ...)
to get a UNIFIED remedy block. Replaces per-engine ad-hoc remedy tables.

Design (May 6 2026, per user mandate):
- TIER 1 PRACTICAL FIRST (real-world action with KPI) —  always shown
- TIER 2 AYURVEDIC SECOND (body-mind, vaidya disclaimer)
- TIER 3 VEDIC LAST (mantra/donation/gemstone with caveats)
- Cost transparency on every paid item
- Anti-superstition guard: vedic NEVER stands alone, ALWAYS paired
- Conflict checker: dangerous gemstone-pairs / overload warned
- Substitution engine: vegetarian / no-fast / no-temple / allergy swaps
- 21/40-day connected stack builder, not disconnected list
- KPI per remedy so user can self-verify in measurable weeks
- UCML personalization hooks (user_facts dict)
- Severity-aware tier-note (urgent_consult → DOCTOR FIRST badge)

Public API:
    get_remedies(topic, planets, areas, severity, user_facts=None,
                   duration_days=21) -> dict
    render_for_locked_facts(result) -> str (formatted block ready for
                                              locked_facts injection)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from .catalog import CATALOG, SYSTEM_PRACTICES
from .conflict_check import check_conflicts
from .substitutions import apply_substitutions
from .stack_builder import build_stack


_VALID_TOPICS = ("health", "marriage", "career", "money", "business")

# tier_note keyed by topic+severity. Health has explicit medical-safety
# tone; marriage/career use action-orientation tone.
_TIER_NOTES: Dict[str, Dict[str, str]] = {
    "health": {
        "monitor":         "Routine check-up enough — keep these as preventive habits.",
        "preventive":      "Add these on TOP of regular check-ups; do not wait for symptoms.",
        "consult":         "Start these alongside a doctor visit — remedies are SUPPORT, not substitute.",
        "urgent_consult":  "First a qualified doctor visit, THEN add these. NEVER delay medical care for remedies.",
    },
    "marriage": {
        "watchful":        "Window is open — practical reach + values-clarity matter most.",
        "supportive":      "Engine signals favourable — push 4 introductions/month + value-filter.",
        "celebratory":     "Strong window — focus on FINAL filtering; don't rush in haste.",
        "consult":         "Pre-marital counsellor 1-2 sessions = highest ROI in this band.",
    },
    "career": {
        "watchful":        "Build runway + skill — Saturn rewards depth not speed.",
        "supportive":      "Push applications/networking — Sun/Mercury active windows compound.",
        "celebratory":     "Take the offer/promotion — but read contract carefully (Mercury-due-diligence).",
    },
    "money": {
        "watchful":        "Tighten the leak first — savings rate + debt-clearance > new investments.",
        "supportive":      "Window favourable — auto-debit SIP + emergency fund are highest-ROI moves.",
        "celebratory":     "Strong dhan-yog — but lock-in via long-corpus (NPS/index/SGB), avoid hot tips.",
        "consult":         "SEBI-registered advisor 1 hr = highest ROI in this band; skip free WhatsApp tips.",
    },
    "business": {
        "watchful":        "Cashflow + 18-mo runway first — don't scale a leaky bucket.",
        "supportive":      "Push customer convos + hiring carefully + brand basics — Sun/Mercury compound.",
        "celebratory":     "Strong window — but founder-fitness + clean books matter MORE now, not less.",
        "consult":         "Cofounder/legal/CA advisor 2 sessions = highest ROI; verbal deals = top killer.",
    },
}

# Universal disclaimer per topic
_DISCLAIMERS: Dict[str, str] = {
    "health":   ("Remedies SUPPLEMENT action, never substitute it. "
                  "Qualified doctor consultation is the primary path. "
                  "Gemstones (paid) require a 3-day trial first. "
                  "Ayurvedic herbs need a vaidya for prakriti-specific dose."),
    "marriage": ("Remedies open opportunity — they don't force outcome. "
                  "Practical action (introductions, value-clarity, communication) "
                  "is the primary lever. Pre-marital counselling > any gemstone."),
    "career":   ("Remedies amplify effort — they don't replace it. "
                  "Skill, applications, and networking remain the primary drivers. "
                  "Avoid get-rich-quick schemes (Rahu's classic trap)."),
    "money":    ("Remedies SUPPORT financial discipline, never replace it. "
                  "Auto-debit + emergency fund + low-cost index investing are the primary levers. "
                  "Skip 'guaranteed return' schemes and paid 'guaranteed remedy' fees > ₹5,000 — "
                  "both are predatory. SEBI-registered advisor > WhatsApp tips."),
    "business": ("Remedies SUPPORT founder discipline, never replace it. "
                  "Cashflow, customer conversations, founder fitness, and clean books remain "
                  "the primary drivers. Verbal-only deals + over-fundraising + vanity-metric "
                  "obsession are the top killers — engine warns; user decides."),
}


def _normalize_severity(topic: str, severity: Optional[str]) -> str:
    """Coerce severity to a known value per topic; default to safest."""
    valid = list(_TIER_NOTES.get(topic, {}).keys())
    if severity in valid:
        return severity
    # Safe defaults — never the most permissive
    return {
        "health":   "consult",
        "marriage": "watchful",
        "career":   "watchful",
        "money":    "watchful",
        "business": "watchful",
    }.get(topic, "watchful")


def get_remedies(topic: str,
                   planets: Optional[List[Dict[str, Any]]] = None,
                   areas: Optional[List[str]] = None,
                   severity: Optional[str] = None,
                   user_facts: Optional[Dict[str, Any]] = None,
                   duration_days: int = 21) -> Dict[str, Any]:
    """Build the unified remedy block for a topical engine.

    Args:
        topic: "health" | "marriage" | "career"
        planets: list of {name, score} — top-N risk/effect planets from
                 the topical engine. Engine picks top-3 unique planets
                 with catalog entries.
        areas: list of system / life-area tags — drives daily-practices
                 layer. Health uses affected_systems; marriage/career
                 use harmony/communication/leadership/skill_depth/etc.
        severity: topic-specific tier (urgent_consult / watchful / ...)
        user_facts: UCML facts dict — drives substitutions
        duration_days: 21 (standard) or 40 (mandala)

    Returns: dict (see schema in module docstring).
    """
    if topic not in _VALID_TOPICS:
        return {
            "topic": topic, "available": False,
            "reason": f"unknown topic; supported: {_VALID_TOPICS}",
        }

    planets    = planets or []
    areas      = areas or []
    norm_sev   = _normalize_severity(topic, severity)
    catalog_t  = CATALOG.get(topic, {}) or {}

    # ── Pick top-3 unique catalog-supported planet remedies ──────────
    selected: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for p in planets:
        if not isinstance(p, dict):
            continue
        name = p.get("name") or p.get("planet")
        if not name or name in seen:
            continue
        entry = catalog_t.get(name)
        if not entry:
            continue
        # Anti-superstition HARD GUARD (architect-fix May 6 2026):
        # never let a planet through with missing practical OR ayurvedic
        # tier — vedic-only would defeat the engine's core promise that
        # the user gets real-world action FIRST. Defensive against future
        # catalog edits that might omit a tier.
        prac = entry.get("practical") or {}
        ayur = entry.get("ayurvedic") or {}
        ved  = entry.get("vedic")     or {}
        if not prac.get("action") or not (ayur.get("practice") or ayur.get("herb")):
            continue
        if not ved.get("mantra"):
            continue
        seen.add(name)
        selected.append({
            "planet":     name,
            "score":      p.get("score"),
            "for_areas":  entry.get("for_areas"),
            "practical":  dict(prac),
            "ayurvedic":  dict(ayur),
            "vedic":      dict(ved),
        })
        if len(selected) >= 3:
            break

    # ── Apply user-facts substitutions ───────────────────────────────
    selected, swaps = apply_substitutions(selected, user_facts)

    # ── System / area practices (top-3 unique, catalog-supported) ────
    system_practices: List[Dict[str, str]] = []
    seen_a: Set[str] = set()
    for a in areas:
        if not a or a in seen_a:
            continue
        sp = SYSTEM_PRACTICES.get(a)
        if not sp:
            continue
        seen_a.add(a)
        system_practices.append({"system": a, "practice": sp["practice"]})
        if len(system_practices) >= 3:
            break

    # ── Conflict check ──────────────────────────────────────────────
    conflicts = check_conflicts(selected, severity=norm_sev, topic=topic)

    # ── Stack builder (21/40-day connected daily routine) ───────────
    stack = build_stack(selected, system_practices,
                          duration_days=duration_days, topic=topic)

    # ── Tier note + disclaimer ──────────────────────────────────────
    tier_note  = _TIER_NOTES.get(topic, {}).get(norm_sev, "")
    disclaimer = _DISCLAIMERS.get(topic,
                    "Remedies SUPPORT effort — they don't replace it.")

    # ── Doctor handoff hint (health-only) ───────────────────────────
    referral_hint = None
    if topic == "health" and norm_sev in ("consult", "urgent_consult"):
        # Map common system tags → specialist suggestion
        spec_map = {
            "heart":         "cardiologist",
            "blood":         "hematologist or general physician (CBC + lipid)",
            "liver":         "hepatologist or gastroenterologist",
            "kidneys":       "nephrologist or urologist",
            "joints":        "rheumatologist or orthopedic",
            "skin":          "dermatologist",
            "nervous":       "neurologist",
            "anxiety":       "psychiatrist + therapist (combo proven best)",
            "auto-immune":   "rheumatologist + immunologist",
            "digestion":     "gastroenterologist",
            "reproductive":  "gynecologist (women) / urologist or endocrinologist (men)",
            "eyes":          "ophthalmologist",
        }
        suggestions: List[str] = []
        for a in areas:
            if a in spec_map and spec_map[a] not in suggestions:
                suggestions.append(spec_map[a])
            if len(suggestions) >= 2:
                break
        if suggestions:
            referral_hint = (
                "Suggested specialist type: " + " / ".join(suggestions)
                + ". Ask your primary care doctor for a referral."
            )

    return {
        "topic":                  topic,
        "available":              bool(selected or system_practices),
        "severity":               norm_sev,
        # Back-compat alias for legacy consumers that read `tier`
        # (architect-fix May 6 2026). Kept for ≥1 transition cycle.
        "tier":                   norm_sev,
        "planet_remedies":        selected,
        "system_practices":       system_practices,
        "stack":                  stack,
        "conflicts":              conflicts,
        "substitutions_applied":  swaps,
        "tier_note":              tier_note,
        "universal_disclaimer":   disclaimer,
        "doctor_referral_hint":   referral_hint,
        "follow_up_prompt":       (f"After {stack['duration_days']} days, "
                                     "rate (1-5) which remedies actually helped "
                                     "so the engine can refine future advice."),
        "engine_version":         "v1.0.0",
    }


def render_for_locked_facts(result: Dict[str, Any]) -> str:
    """Format the engine result as a single text block ready for
    `locked_facts.py` injection.

    Output convention:
        ▸ <TOPIC> REMEDIES (engine-only, Rule M — quote verbatim, NEVER
                              invent mantras/gems):
           ◦ <Planet> — <area>:
             practical : ...
             ayurvedic : ...
             vedic     : ...
             KPI       : ...
           ◦ Daily practices: ...
           ⚠ <conflicts/disclaimer>
           ⚐ TIER NOTE: ...
           📅 <stack summary>
           🩺 <referral hint, if health>
    Empty result returns "".
    """
    if not result or not result.get("available"):
        return ""

    topic = (result.get("topic") or "").upper()
    lines = [
        "",
        f"▸ {topic} REMEDIES (engine-only, Rule M — quote verbatim, NEVER invent mantras/gems):",
    ]

    for r in result.get("planet_remedies", [])[:3]:
        planet = r.get("planet")
        prac   = r.get("practical")  or {}
        ayur   = r.get("ayurvedic") or {}
        ved    = r.get("vedic")     or {}
        lines.append(f"   ◦ {planet}  — {r.get('for_areas','')}")
        if prac.get("action"):
            lines.append(f"     1️⃣ practical : {prac['action']}")
            if prac.get("kpi"):
                lines.append(f"        KPI       : {prac['kpi']}")
            if prac.get("time_to_result"):
                lines.append(f"        result-in : {prac['time_to_result']}")
            # Practical cost (lab tests, books, courses, counsellor) —
            # architect-fix May 6 2026 cost-transparency: render every
            # paid practical step so the user sees real total upfront.
            _pc = prac.get("cost_inr")
            if isinstance(_pc, (int, float)) and _pc > 0:
                lines.append(f"        ₹ cost    : ~₹{int(_pc):,} (practical)")
        if ayur.get("practice") or ayur.get("herb"):
            ayur_line = ayur.get("practice", "")
            if ayur.get("herb"):
                ayur_line = (ayur_line + " | herb: " + ayur["herb"]).strip(" |")
            lines.append(f"     2️⃣ ayurvedic : {ayur_line}")
            if ayur.get("vaidya_caveat") and ayur["vaidya_caveat"] != "—":
                lines.append(f"        ⚠ vaidya  : {ayur['vaidya_caveat']}")
        if ved.get("mantra"):
            lines.append(
                f"     3️⃣ vedic     : {ved.get('day','')} — "
                f"\"{ved['mantra']}\" × {ved.get('count','108')}"
            )
            if ved.get("free_alt"):
                lines.append(f"        free      : {ved['free_alt']}")
            if ved.get("donation"):
                lines.append(f"        daan      : {ved['donation']}")
            if ved.get("gemstone"):
                lines.append(f"        paid      : {ved['gemstone']}")
                if ved.get("gem_caveat"):
                    lines.append(f"        ⚠ gem    : {ved['gem_caveat']}")
                if ved.get("cost_inr_paid"):
                    lines.append(f"        ₹ cost    : {ved['cost_inr_paid']}")

    sps = result.get("system_practices") or []
    if sps:
        lines.append("   ◦ Daily practices (areas):")
        for sp in sps[:3]:
            lines.append(f"     · {sp.get('system')}: {sp.get('practice')}")

    # Stack summary (compact)
    stack = result.get("stack") or {}
    if stack and (stack.get("morning") or stack.get("evening")):
        lines.append(f"   📅 {stack.get('duration_days', 21)}-day stack: "
                       f"{len(stack.get('morning', []))} morning + "
                       f"{len(stack.get('day', []))} day + "
                       f"{len(stack.get('evening', []))} evening + "
                       f"{len(stack.get('weekly', []))} weekly items")

    # Conflicts
    for c in (result.get("conflicts") or []):
        lines.append(f"   ⚠ {c.get('kind')} ({c.get('severity')}): {c.get('message')}")

    # Disclaimer + tier note
    if result.get("universal_disclaimer"):
        lines.append(f"   ⚠ {result['universal_disclaimer']}")
    if result.get("tier_note"):
        lines.append(f"   ⚐ TIER NOTE: {result['tier_note']}")

    # Doctor referral (health only)
    if result.get("doctor_referral_hint"):
        lines.append(f"   🩺 {result['doctor_referral_hint']}")

    # Follow-up prompt
    if result.get("follow_up_prompt"):
        lines.append(f"   🔁 {result['follow_up_prompt']}")

    return "\n".join(lines)

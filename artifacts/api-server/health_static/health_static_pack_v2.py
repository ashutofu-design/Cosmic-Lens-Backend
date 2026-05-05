"""Health Static Pack v2 — Enhanced ADD-ONLY enrichment over health_facts.py.

╔══════════════════════════════════════════════════════════════════════╗
║  ADD-ONLY: ZERO breaking changes to existing health_facts engine.    ║
║  Wraps compute_health_facts() and ENRICHES the pack with:            ║
║                                                                      ║
║    1. House occupants  (6/8/12 — direct disease karakas)             ║
║    2. Body parts vulnerable  (sign-based BPHS mapping)               ║
║    3. D9 health specifics  (Navamsa lagna + 6L state)                ║
║    4. Moon nakshatra  (mental temperament signal)                    ║
║    5. Primary/Secondary/Tertiary concerns  (laser focus for LLM)     ║
║    6. Engine-derived insights  (33 rule-based truths)                ║
║                                                                      ║
║  REMOVED from v2 output (per user dictate H2.7.15):                  ║
║    • KP CSL block      → moved to TIMING pack (future)               ║
║    • KP-Vedic resolver → moved to TIMING pack                        ║
║    • KP nudges in dim  → preserved in `vedic_raw` field already      ║
║    • Ashtakavarga      → moved to TIMING pack                        ║
║                                                                      ║
║  KILLSWITCH: env HEALTH_STATIC_V2=0 → returns base pack untouched.   ║
║  Caller can opt-out instantly without code change.                   ║
║                                                                      ║
║  ARCHITECTURE: Engine=Truth.  All insights are RULE-BASED            ║
║  (deterministic IF/THEN). Same chart → same insights forever.        ║
║  ZERO LLM calls in this module.                                      ║
╚══════════════════════════════════════════════════════════════════════╝

Public API:
  compute_health_static_pack_v2(kundli) -> dict
"""
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional

from health_static.health_facts import compute_health_facts  # noqa: E402

# ── Sign → body-part mapping (BPHS classical, simplified) ──────────
_SIGN_BODY_PARTS: Dict[str, str] = {
    "Aries":       "head, brain, sinus",
    "Taurus":      "throat, neck, thyroid",
    "Gemini":      "arms, shoulders, lungs, nervous system",
    "Cancer":      "chest, stomach, breast, digestive lining",
    "Leo":         "heart, spine, upper back",
    "Virgo":       "intestines, abdomen, digestive process",
    "Libra":       "kidneys, lower back, lumbar",
    "Scorpio":     "reproductive, urinary, colon",
    "Sagittarius": "hips, thighs, liver",
    "Capricorn":   "knees, joints, bones, skin",
    "Aquarius":    "ankles, calves, circulation",
    "Pisces":      "feet, lymphatic, immune system",
}

_SIGN_ELEMENT: Dict[str, str] = {
    "Aries": "fire", "Leo": "fire", "Sagittarius": "fire",
    "Taurus": "earth", "Virgo": "earth", "Capricorn": "earth",
    "Gemini": "air", "Libra": "air", "Aquarius": "air",
    "Cancer": "water", "Scorpio": "water", "Pisces": "water",
}

# Nakshatras grouped by mental-health temperament (BPHS + classical)
_NAK_RESTLESS = {"Ardra", "Swati", "Shatabhisha", "Punarvasu"}
_NAK_CALMING  = {"Pushya", "Rohini", "Hasta", "Anuradha", "Revati"}
_NAK_INTENSE  = {"Mula", "Jyeshtha", "Vishakha", "Magha", "Bharani"}
_NAK_SATURN_RULED = {"Pushya", "Anuradha", "Uttara Bhadrapada"}

# Sign-name → 0-11 index (for h-house lookup from ascendant)
_SIGN_INDEX: Dict[str, int] = {
    "Aries": 0, "Taurus": 1, "Gemini": 2, "Cancer": 3,
    "Leo": 4, "Virgo": 5, "Libra": 6, "Scorpio": 7,
    "Sagittarius": 8, "Capricorn": 9, "Aquarius": 10, "Pisces": 11,
}
_INDEX_SIGN: Dict[int, str] = {v: k for k, v in _SIGN_INDEX.items()}


# ── Helper: which sign falls on house N? ───────────────────────────
def _house_sign(asc_sign: str, house_num: int) -> Optional[str]:
    """Whole-sign system: house N's sign = (asc_index + N - 1) mod 12."""
    asc_idx = _SIGN_INDEX.get(asc_sign)
    if asc_idx is None or not isinstance(house_num, int):
        return None
    return _INDEX_SIGN.get((asc_idx + house_num - 1) % 12)


# ── 1. KP / AV stripper ────────────────────────────────────────────
def _strip_kp_and_av_from_pack(pack: Dict[str, Any]) -> Dict[str, Any]:
    """Remove KP CSL block + KP-related conflict markers. Vedic raw_score
    preserved (it's pre-nudge already). Per user decision H2.7.15:
    static = pure Vedic, KP/AV reserved for TIMING pack.

    Architect-fix R2: instead of POPPING `conflict_flag`, we RESET it to
    False — preserves downstream consumers that read this field. Add
    explicit `kp_was_stripped=True` marker for transparency.
    """
    pack.pop("kp_csl", None)
    pack["kp_was_stripped"] = True  # explicit signal for downstream
    dims = pack.get("dimensions") or {}
    for d in dims.values():
        if isinstance(d, dict):
            # Reset (NOT pop) — preserves field shape for any consumer.
            d["conflict_flag"] = False
            # Reset confidence to NORMAL (was set LOW only by KP resolver).
            if d.get("confidence") == "LOW":
                d["confidence"] = "NORMAL"
            # Remove KP conflict suffix from reason text.
            r = d.get("reason", "")
            if "[KP-VEDIC CONFLICT" in r:
                d["reason"] = r.split(" [KP-VEDIC CONFLICT")[0]
    # Update engine_version tag to mark v2.
    pack["engine_version"] = pack.get("engine_version", "") + "_v2_no_kp"
    return pack


# ── 2. House occupants (6/8/12) ────────────────────────────────────
def _compute_occupants(kundli: Dict[str, Any]) -> Dict[str, List[str]]:
    """Planets occupying disease/chronic/loss houses."""
    out: Dict[str, List[str]] = {"6th": [], "8th": [], "12th": []}
    planets = kundli.get("planets") or []
    for p in planets:
        h = p.get("house")
        n = p.get("name")
        if not n:
            continue
        if h == 6:
            out["6th"].append(n)
        elif h == 8:
            out["8th"].append(n)
        elif h == 12:
            out["12th"].append(n)
    return out


# ── 3. Body parts vulnerable ───────────────────────────────────────
def _compute_body_parts(kundli: Dict[str, Any]) -> List[str]:
    """Map signs falling on 6/8/12 + 6/8 lord placements to body zones."""
    asc = kundli.get("ascendant", "")
    out: List[str] = []
    for hn, label in ((6, "6th"), (8, "8th"), (12, "12th")):
        sg = _house_sign(asc, hn)
        if sg and sg in _SIGN_BODY_PARTS:
            out.append(f"{_SIGN_BODY_PARTS[sg]} ({label} in {sg})")
    return out


# ── 4. D9 health specifics ─────────────────────────────────────────
def _compute_d9_health(kundli: Dict[str, Any]) -> Dict[str, Any]:
    """Navamsa lagna + 6L of D9 + lagna-lord state in D9."""
    dc = kundli.get("divisionalCharts") or {}
    d9 = dc.get("D9") or dc.get("d9") or {}
    if not isinstance(d9, dict) or not d9.get("planets"):
        return {"available": False}
    d9_lagna = d9.get("ascendant", "")
    d9_planets = d9.get("planets", [])
    # 6th house sign in D9
    d9_6th_sign = _house_sign(d9_lagna, 6)
    # Find planets in D9 6th house
    d9_6th_occupants = [
        p.get("name") for p in d9_planets
        if p.get("house") == 6 and p.get("name")
    ]
    # Lagna lord of D9 (sign-lord of D9 ascendant) — simple placement check
    sign_lord = {
        "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
        "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
        "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
        "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
    }
    lagna_lord_name = sign_lord.get(d9_lagna)
    lagna_lord_p = next(
        (p for p in d9_planets if p.get("name") == lagna_lord_name),
        None,
    )
    lagna_lord_house = (lagna_lord_p or {}).get("house")
    lagna_lord_in_dusthana = lagna_lord_house in (6, 8, 12)
    return {
        "available": True,
        "lagna_sign": d9_lagna,
        "lagna_lord": lagna_lord_name,
        "lagna_lord_house": lagna_lord_house,
        "lagna_lord_in_dusthana": lagna_lord_in_dusthana,
        "6th_sign": d9_6th_sign,
        "6th_occupants": d9_6th_occupants,
    }


# ── 5. Moon nakshatra enrichment ───────────────────────────────────
def _add_moon_nakshatra(kundli: Dict[str, Any]) -> Dict[str, Any]:
    """Moon nakshatra + temperament tag (top-level field; pre-computed)."""
    nak = kundli.get("nakshatra") or ""
    pada = kundli.get("nakshatraPada")
    if not nak:
        return {"available": False}
    if nak in _NAK_RESTLESS:
        temperament = "anxiety-prone / restless mind"
    elif nak in _NAK_CALMING:
        temperament = "calming / mentally resilient"
    elif nak in _NAK_INTENSE:
        temperament = "intense transformation periods possible"
    elif nak in _NAK_SATURN_RULED:
        temperament = "patient but heavy mental tendency"
    else:
        temperament = "balanced baseline"
    return {
        "available": True,
        "name": nak,
        "pada": pada,
        "ruler": kundli.get("nakshatraRuler"),
        "temperament": temperament,
    }


# ── 6. Primary/Secondary/Tertiary concerns ─────────────────────────
def _rank_concerns(dimensions: Dict[str, dict]) -> Dict[str, Optional[str]]:
    """Sort dimensions by 'most concerning' = highest severity + worst verdict.

    Worst verdict semantics:
      STANDARD dim (vitality/dr/mental): RED > YELLOW > GREEN  (weak = worse)
      INVERTED dim (chronic_risk/accident): RED > YELLOW > GREEN  (high risk = worse)

    Severity HIGH > MODERATE > LOW.  Concerns ranked by combined badness.
    Returns top 3.
    """
    _verdict_badness = {"RED": 3, "YELLOW": 2, "GREEN": 1}
    _severity_weight = {"HIGH": 3, "MODERATE": 2, "LOW": 1}
    scored: List[tuple] = []
    for name, d in dimensions.items():
        if not isinstance(d, dict):
            continue
        v_score = _verdict_badness.get(d.get("verdict", "GREEN"), 1)
        s_score = _severity_weight.get(d.get("severity", "LOW"), 1)
        # Only RED/YELLOW count as concerns; GREEN is "not a concern".
        if v_score == 1:
            continue
        scored.append((v_score * 10 + s_score, name))
    scored.sort(reverse=True)
    return {
        "primary":   scored[0][1] if len(scored) >= 1 else None,
        "secondary": scored[1][1] if len(scored) >= 2 else None,
        "tertiary":  scored[2][1] if len(scored) >= 3 else None,
    }


# ── 7. Insight derivation — 33 RULES across 5 buckets ──────────────
def _derive_insights(pack: Dict[str, Any]) -> List[str]:
    """Pure rule-based insight derivation. ZERO LLM. Deterministic.

    33 rules, 5 buckets:
      Bucket 1 (10) — Dimension combinations
      Bucket 2 (8)  — Driver/planet signatures
      Bucket 3 (6)  — Body-part / 6th-house sign
      Bucket 4 (4)  — Moon nakshatra temperament
      Bucket 5 (5)  — Cross-signal multi-condition
    """
    insights: List[str] = []
    # Architect-fix R1: explicit defaults + type-coercion guard schema drift.
    _empty: Dict[str, Any] = {}
    def _as_dict(v: Any) -> Dict[str, Any]:
        return v if isinstance(v, dict) else _empty
    dims = _as_dict(pack.get("dimensions"))
    karakas = _as_dict(pack.get("karakas"))
    house_lords = _as_dict(pack.get("house_lords"))
    yogas = pack.get("yogas") if isinstance(pack.get("yogas"), list) else []
    occupants = _as_dict(pack.get("house_occupants"))
    moon_nak = _as_dict(pack.get("moon_nakshatra"))

    vt = (dims.get("vitality") or _empty) if isinstance(dims, dict) else _empty
    dr = (dims.get("disease_resistance") or _empty) if isinstance(dims, dict) else _empty
    cr = (dims.get("chronic_risk") or _empty) if isinstance(dims, dict) else _empty
    mh = (dims.get("mental_health") or _empty) if isinstance(dims, dict) else _empty
    ar = (dims.get("accident_risk") or _empty) if isinstance(dims, dict) else _empty

    sat = (karakas.get("Saturn") or _empty) if isinstance(karakas, dict) else _empty
    rahu = (karakas.get("Rahu") or _empty) if isinstance(karakas, dict) else _empty
    mars = (karakas.get("Mars") or _empty) if isinstance(karakas, dict) else _empty
    sun = (karakas.get("Sun") or _empty) if isinstance(karakas, dict) else _empty
    moon = (karakas.get("Moon") or _empty) if isinstance(karakas, dict) else _empty

    h1 = (house_lords.get("h1") or _empty) if isinstance(house_lords, dict) else _empty
    h6 = (house_lords.get("h6") or _empty) if isinstance(house_lords, dict) else _empty
    h8 = (house_lords.get("h8") or _empty) if isinstance(house_lords, dict) else _empty

    # ── Bucket 1: Dimension insights (10 rules) ──────────────────
    # R1: vit weak + chronic high
    if vt.get("verdict") == "RED" and cr.get("verdict") == "RED":
        insights.append("Constitution weak + chronic susceptibility "
                        "elevated — preventive lifestyle priority")
    # R2: vit GREEN + Arishta yoga
    if vt.get("verdict") == "GREEN" and "Arishta" in yogas:
        insights.append("Natural strength achi hai but Arishta yoga "
                        "noted — periodic checkup advisable")
    # R3: mental weak + Moon afflicted
    moon_dignity = moon.get("dignity", "")
    if mh.get("verdict") in ("RED", "YELLOW") and moon_dignity in (
            "debilitated", "combust", "weak"):
        insights.append("Mental peace zone needs attention + Moon "
                        "afflicted — meditation aur sleep priority")
    # R4: recovery strong + Vipreet
    if dr.get("verdict") == "GREEN" and "Vipreet-Recovery" in yogas:
        insights.append("Bounce-back power above average — bimari aaye "
                        "to recovery fast hoga")
    # R5: accident high + mars-ketu signature
    mars_h = mars.get("house")
    ketu_h = (karakas.get("Ketu") or {}).get("house")
    if (ar.get("verdict") == "RED" and mars_h
            and mars_h == ketu_h):
        insights.append("Accident risk zone elevated — daily physical "
                        "activities me extra mindfulness")
    # R6: balanced baseline (all YELLOW)
    yellows = sum(1 for d in (vt, dr, cr, mh, ar)
                  if d.get("verdict") == "YELLOW")
    if yellows >= 4:
        insights.append("Overall balanced baseline — koi extreme "
                        "signature nahi, general care sufficient")
    # R7: all GREEN constitution
    greens = sum(1 for d in (vt, dr, cr, mh, ar)
                 if d.get("verdict") == "GREEN")
    if greens == 5:
        insights.append("Robust overall constitution — chart me strong "
                        "supportive base across body+mind")
    # R8: mental + chronic both RED
    if mh.get("verdict") == "RED" and cr.get("verdict") == "RED":
        insights.append("Stress chronic risk ko amplify kar raha — "
                        "mind-body link active, dono pe kaam zaroori")
    # R9: dr + cr both RED — double caution
    if dr.get("verdict") == "RED" and cr.get("verdict") == "RED":
        insights.append("Recovery slow + chronic high = double caution — "
                        "proactive medical insurance advisable")
    # R10: body + mind both green
    if (vt.get("verdict") == "GREEN" and dr.get("verdict") == "GREEN"
            and mh.get("verdict") == "GREEN"):
        insights.append("Body aur mind dono supportive — natural baseline "
                        "achi hai, lifestyle se further strengthen ho sakta")

    # ── Bucket 2: Driver/planet signatures (8 rules) ─────────────
    # R11: Saturn in 1/6/8
    sat_h = sat.get("house")
    if sat_h in (1, 6, 8):
        insights.append(f"Saturn {sat_h}th me — chronic stress signature, "
                        "energy slow-burn type")
    # R12: Mars in 6 = fighter
    if mars_h == 6:
        insights.append("Mars 6th me — fighter immunity (Vipreet positive), "
                        "infections se actively recover karte")
    # R13: Rahu in 6/8/12
    rahu_h = rahu.get("house")
    if rahu_h in (6, 8, 12):
        insights.append(f"Rahu {rahu_h}th me — mystery/recurring ailments "
                        "tendency, diagnose karna mushkil ho sakta")
    # R14: Saturn aspecting Moon (7th aspect approximation: 7 houses apart)
    moon_h = moon.get("house")
    if sat_h and moon_h:
        diff = abs(sat_h - moon_h)
        if diff in (6, 7) or (sat_h == moon_h):  # 7th aspect or conjunction
            # Architect-fix R3 (HIGH brand-safety): replaced "depression watch"
            # which violates _DISEASE_BLOCKLIST in health_facts.py.
            insights.append("Saturn aur Moon ka contact — emotional "
                            "heaviness ki tendency, mental peace zone "
                            "pe extra dhyan")
    # R15: Mars-Saturn conjunction
    if mars_h and sat_h and mars_h == sat_h:
        insights.append("Mars-Saturn ek saath — injury/inflammation risk, "
                        "physical stress se safety zaroori")
    # R16: Lagna lord in 8 or 12
    if h1.get("lord_house") in (8, 12):
        insights.append("Lagna lord 8th/12th me — body energy scattered "
                        "feels, regular grounding routine helpful")
    # R17: 6th lord in 8 or 12 (Vipreet Rajyoga style)
    if h6.get("lord_house") in (8, 12):
        insights.append("6th lord 8/12 me — disease channel weakened "
                        "(positive), enemies of body apne aap kam hote")
    # R18: Sun debilitated/combust
    sun_dig = sun.get("dignity", "")
    if sun_dig in ("debilitated", "combust"):
        insights.append("Sun weak — vitality drain tendency, morning "
                        "sunlight aur Vit-D check helpful")

    # ── Bucket 3: Body-part / 6th-house sign (6 rules) ───────────
    asc = pack.get("ascendant", "")
    sixth_sign = _house_sign(asc, 6)
    sixth_elem = _SIGN_ELEMENT.get(sixth_sign or "", "")
    # R19: 6th in fire sign
    if sixth_elem == "fire":
        insights.append(f"6th house {sixth_sign} (fire) — inflammation, "
                        "fever, acid-related issues ki tendency")
    # R20: 6th in earth sign
    if sixth_elem == "earth":
        insights.append(f"6th house {sixth_sign} (earth) — digestive, "
                        "joint, slow-metabolism issues ki tendency")
    # R21: 6th in air sign
    if sixth_elem == "air":
        insights.append(f"6th house {sixth_sign} (air) — nervous system, "
                        "respiratory, circulation issues ki tendency")
    # R22: 6th in water sign
    if sixth_elem == "water":
        insights.append(f"6th house {sixth_sign} (water) — fluid balance, "
                        "immune, lymphatic issues ki tendency")
    # R23: Mars in 1st = head/BP
    if "Mars" in (occupants.get("6th") or []) or mars_h == 1:
        if mars_h == 1:
            insights.append("Mars lagna me — head pressure, blood-related "
                            "(BP) caution advisable")
    # R24: Saturn in 1st = bone/joint/skin
    if sat_h == 1:
        insights.append("Saturn lagna me — bone/joint/skin chronic "
                        "tendency, structural health pe focus")

    # ── Bucket 4: Moon nakshatra temperament (4 rules) ───────────
    nak_name = moon_nak.get("name", "")
    # R25: Restless nakshatra
    if nak_name in _NAK_RESTLESS:
        insights.append(f"Moon {nak_name} nakshatra me — anxiety-prone "
                        "temperament, grounding practices (yoga/walks) helpful")
    # R26: Calming nakshatra
    if nak_name in _NAK_CALMING:
        insights.append(f"Moon {nak_name} nakshatra me — naturally calming "
                        "mind, mental resilience baseline strong")
    # R27: Intense transformation nakshatra
    if nak_name in _NAK_INTENSE:
        insights.append(f"Moon {nak_name} nakshatra me — intense periods "
                        "of mental transformation possible, journaling helps")
    # R28: Saturn-ruled nakshatra
    if nak_name in _NAK_SATURN_RULED:
        insights.append(f"Moon {nak_name} nakshatra (Saturn-ruled) — "
                        "patient temperament but mental heaviness possible")

    # ── Bucket 5: Cross-signal multi-condition (5 rules) ─────────
    # R29: Deep-seated vulnerability
    if (vt.get("verdict") == "RED" and h8.get("lord_house") == 1
            and sat_h in (1, 7)):
        insights.append("Vitality weak + 8L lagna me + Saturn aspect = "
                        "deep-seated constitutional vulnerability, "
                        "long-term lifestyle discipline crucial")
    # R30: Inherited stress pattern
    if (mh.get("verdict") in ("RED", "YELLOW")
            and sat_h and moon_h and sat_h == moon_h):
        insights.append("Mental zone + Moon-Saturn yog = inherited "
                        "stress pattern possible, family awareness helpful")
    # R31: Double red — softened (architect-fix R4: removed "insurance" overclaim)
    if dr.get("verdict") == "RED" and ar.get("verdict") == "RED":
        insights.append("Recovery + accident dono caution zone = extra "
                        "physical mindfulness aur safety routine helpful")
    # R32: Stress-mind-body chain
    if (cr.get("verdict") == "RED" and mh.get("verdict") == "RED"
            and pack.get("body_parts_vulnerable")):
        insights.append("Stress-mind-body chain active — chronic + mental "
                        "+ specific body zone weak = holistic approach needed")
    # R33: Natural recovery baseline (architect-fix R4: softened prognosis-style claim)
    if (dr.get("verdict") == "GREEN" and vt.get("verdict") == "GREEN"
            and "Vipreet-Recovery" in yogas):
        insights.append("Natural recovery baseline strong — body bounce-back "
                        "power achi hai, challenges me resilience high")

    # ── FALLBACK: agar 0 rules fired (rare balanced edge case) ──
    if not insights:
        insights.append("Chart balanced baseline — koi extreme signature "
                        "nahi mila, general lifestyle care sufficient")

    # CAP at top 6 insights to avoid overload
    return insights[:6]


# ── Public API ──────────────────────────────────────────────────────
def compute_health_static_pack_v2(kundli: Dict[str, Any]) -> Dict[str, Any]:
    """Returns enriched health static pack v2.

    Pipeline:
      1. Call existing compute_health_facts() (5 dims + yogas + KP + meta)
      2. Strip KP/AV from output (per H2.7.15 user decision)
      3. Add 6 new enrichment fields
      4. Derive 33-rule insights
      5. Return slim, focused pack ready for LLM grounding

    Killswitch: env HEALTH_STATIC_V2=0 → returns base pack untouched.
    """
    if os.environ.get("HEALTH_STATIC_V2", "1") == "0":
        return compute_health_facts(kundli)

    # Step 1: get base pack from existing engine.
    base = compute_health_facts(kundli)
    if not isinstance(base, dict) or "error" in base:
        return base

    # Step 2: strip KP + AV (none in current pack but defensive).
    base = _strip_kp_and_av_from_pack(base)

    # Step 3: enrichment fields.
    base["house_occupants"] = _compute_occupants(kundli)
    base["body_parts_vulnerable"] = _compute_body_parts(kundli)
    base["d9_health"] = _compute_d9_health(kundli)
    base["moon_nakshatra"] = _add_moon_nakshatra(kundli)
    base["primary_concerns"] = _rank_concerns(base.get("dimensions", {}))

    # Step 4: rule-based insights (uses enriched fields → must come AFTER).
    base["insights"] = _derive_insights(base)

    # Step 5: tag final version.
    base["engine_version"] = (
        "health_static_pack_v2_11fields_33rules_no_kp_no_av"
    )
    base["pack_scope"] = "static_non_timing"

    return base

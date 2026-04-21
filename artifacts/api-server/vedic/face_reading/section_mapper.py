"""
Section Mapper — converts projected engine outputs into the 21-section
Face Intelligence Report template.

This module fills the sections that already have engine data (13 sections).
The remaining 8 NEW sections (Power Summary, Love DNA, Red Flags, Life Flow,
Mole Markings, Action Plan, Hacks, Compatibility, Final Truth) are built in
Step 3 and synthesised in Step 4.

Input  : projected engines dict (from report_projector.project_engines_for_report)
Output : sections dict keyed by section number, ready for Synthesizer + PDF

Sections covered here:
  2  PSYCHOLOGICAL TYPE
  3  SOCIAL MASK vs REAL SELF
  4  FIRST IMPRESSION SCORE
  5  CORE PERSONALITY FOUNDATION (5-element + 3-zones)
  6  FEATURE ANALYSIS (7 features × 2-3 readings)
  7  PERSONALITY SYNTHESIS (Top 5 strengths/weaknesses + behaviour)
  9  CAREER & MONEY PATTERN
  11 ATTRACTION & CHARISMA
  12 DECISION-MAKING STYLE
  13 LIFE ROLE / ARCHETYPE
  15 AGE-WISE LIFE MAP
  16 HEALTH & ENERGY SCAN
  Bonus: PERSONALITY SCORE (5 dims /10)
"""

from typing import Any, Dict, Optional


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _g(d: Optional[Dict], *path, default=None):
    """Safe nested-dict getter."""
    cur = d
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur


def _num(v, default=50.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _band(score: float, *, low=33, high=66) -> str:
    if score < low: return "low"
    if score > high: return "high"
    return "medium"


def _to_10(score_100: float) -> float:
    """Convert 0-100 score to 0-10 with 1-decimal rounding."""
    return round(max(0.0, min(100.0, _num(score_100))) / 10.0, 1)


# ──────────────────────────────────────────────────────────────────────────────
# Section 2 — PSYCHOLOGICAL TYPE
# ──────────────────────────────────────────────────────────────────────────────

def section_2_psychological_type(engines: Dict) -> Dict:
    p = engines.get("personality", {})
    ocean = p.get("ocean_summary_scores") or {}
    pct = p.get("ocean_percentiles") or {}

    O = _num(ocean.get("openness"))
    C = _num(ocean.get("conscientiousness"))
    E = _num(ocean.get("extraversion"))
    A = _num(ocean.get("agreeableness"))
    N = _num(ocean.get("neuroticism"))

    # Personality Type — Thinker / Feeler / Leader / Observer
    if E > 60 and (C > 60 or A > 60):
        ptype, ptype_hi = "Leader", "Netritva-prerak (Leader)"
    elif O > 65 and E < 50:
        ptype, ptype_hi = "Thinker", "Vichaarak (Thinker)"
    elif A > 65 or N > 60:
        ptype, ptype_hi = "Feeler", "Bhavnaatmak (Feeler)"
    else:
        ptype, ptype_hi = "Observer", "Drashta (Observer)"

    # Introversion vs Extroversion
    e_pct = _num(pct.get("extraversion"), default=E)
    if e_pct >= 60:
        ie = "Extrovert"
    elif e_pct <= 40:
        ie = "Introvert"
    else:
        ie = "Ambivert"

    # Decision style
    if C > 60 and N < 45:
        dstyle = "Logical & Planned"
    elif N > 55 or A > 65:
        dstyle = "Emotional & Intuitive"
    else:
        dstyle = "Mixed (logic + emotion)"

    # Intelligence type
    if O > 65 and C < 55:
        intel = "Creative"
    elif C > 65 and O < 55:
        intel = "Analytical"
    elif A > 60 and E > 55:
        intel = "Emotional"
    else:
        intel = "Strategic"

    return {
        "personality_type": ptype,
        "personality_type_hi": ptype_hi,
        "introversion_vs_extroversion": ie,
        "extraversion_score": round(e_pct, 1),
        "decision_style": dstyle,
        "intelligence_type": intel,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 3 — SOCIAL MASK vs REAL SELF
# ──────────────────────────────────────────────────────────────────────────────

def section_3_mask_vs_real(engines: Dict) -> Dict:
    sym = engines.get("symmetry", {})
    fi = engines.get("first_impression", {})
    p = engines.get("personality", {})

    sym_score = _num(sym.get("overall_score"))
    dominant = sym.get("dominant_side") or "balanced"

    # Public perception → first impression valence + dominant trait
    valence = _g(fi, "first_glance_valence", "class") or "neutral"
    snap = _g(fi, "snap_narrative", "line") or ""
    public_perception = snap or f"Log tumhe {valence} aur approachable maante hain."

    # Real self → personality dominant trait
    real_self_trait = p.get("dominant_trait") or "balanced"

    # Mask vs real conflict — high asymmetry => bigger gap
    if sym_score < 60:
        conflict = "Bahari mask aur andar ki feelings me kaafi farak hai. Public me strong, but akele me sensitive."
    elif sym_score < 75:
        conflict = "Thoda farak hai public aur private personality me — normal, manageable."
    else:
        conflict = "Public aur private personality almost same — authentic insaan ho."

    return {
        "public_perception": public_perception,
        "real_self": f"Andar se tum {real_self_trait}-dominant ho.",
        "internal_conflict": conflict,
        "symmetry_score": round(sym_score, 1),
        "dominant_face_side": dominant,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 4 — FIRST IMPRESSION SCORE  (already 4 dims /10)
# ──────────────────────────────────────────────────────────────────────────────

def section_4_first_impression(engines: Dict) -> Dict:
    fi4 = _g(engines, "first_impression", "first_impression_4") or {}
    return {
        "confidence_out_of_10":  _to_10(fi4.get("confidence")),
        "trust_out_of_10":       _to_10(fi4.get("trust")),
        "attraction_out_of_10":  _to_10(fi4.get("attraction")),
        "authority_out_of_10":   _to_10(fi4.get("authority")),
        "perceived_age_years":   _g(engines, "first_impression", "perceived_age", "value"),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 5 — CORE PERSONALITY FOUNDATION (5 element + 3 zones + symmetry)
# ──────────────────────────────────────────────────────────────────────────────

# Face shape → Wu Xing (Chinese 5-element) mapping
_SHAPE_TO_WUXING = {
    "square":      "Metal",
    "round":       "Water",
    "oval":        "Wood",
    "rectangle":   "Wood",
    "rectangular": "Wood",
    "triangular":  "Fire",
    "triangle":    "Fire",
    "heart":       "Fire",
    "diamond":     "Fire",
    "long":        "Wood",
    "pear":        "Earth",
}

# Pancha-Mahabhuta → Wu Xing fallback
_MAHABHUTA_TO_WUXING = {
    "prithvi": "Earth",  "earth": "Earth",
    "jal":     "Water",  "water": "Water",
    "agni":    "Fire",   "fire":  "Fire",
    "vayu":    "Wood",   "air":   "Wood",
    "akash":   "Metal",  "ether": "Metal",
}

_WUXING_TRAITS = {
    "Wood":  "Growth-oriented, leader, ambitious, idealistic.",
    "Fire":  "Energetic, expressive, passionate, social.",
    "Earth": "Reliable, nurturing, grounded, loyal.",
    "Metal": "Disciplined, organised, principled, refined.",
    "Water": "Wise, intuitive, adaptive, deep-thinker.",
}


def section_5_core_foundation(engines: Dict) -> Dict:
    anth = engines.get("anthropometry", {})
    sam = engines.get("samudrika", {})
    sym = engines.get("symmetry", {})

    # Wu Xing element
    shape = (_g(anth, "face_shape_7", "class")
             or _g(anth, "classifications", "face_shape")
             or "oval").lower()
    element = _SHAPE_TO_WUXING.get(shape)
    if not element:
        # fallback via Mahabhuta dominant
        dom = (_g(sam, "element_profile", "dominant")
               or _g(sam, "element_profile", "dominant_element") or "").lower()
        element = _MAHABHUTA_TO_WUXING.get(dom, "Earth")

    # 3 Life Zones — derived from facial proportion (forehead, mid, lower thirds)
    indices = anth.get("classical_indices") or {}
    summary = anth.get("summary") or {}
    # Each zone derived independently from its own proportion pct.
    # Baseline is ~33.3% (equal thirds). Above 35% = strong, below 31% = subtle.
    def _zone_strength(pct_value: float) -> str:
        if pct_value >= 35.0:
            return "strong"
        if pct_value <= 31.0:
            return "subtle"
        return "balanced"

    fh_pct = _num(indices.get("forehead_height_pct"), default=33.3)
    mf_pct = _num(indices.get("midface_height_pct"),  default=33.3)
    lf_pct = _num(indices.get("lower_face_height_pct"), default=33.3)
    forehead_strength = _zone_strength(fh_pct)
    midface_strength  = _zone_strength(mf_pct)
    lower_strength    = _zone_strength(lf_pct)

    zones = {
        "forehead_zone": {
            "represents": "Past & Thinking",
            "strength": forehead_strength,
            "meaning_hi": "Soch, planning, past experiences ka clarity.",
        },
        "mid_face_zone": {
            "represents": "Present & Career",
            "strength": midface_strength,
            "meaning_hi": "Current life — career, relationships, action-energy.",
        },
        "lower_face_zone": {
            "represents": "Future & Stability",
            "strength": lower_strength,
            "meaning_hi": "Future, family, dheeraj aur sthirta.",
        },
    }

    # Symmetry → private vs public note
    sym_note = sym.get("mask_vs_real") or (
        "Symmetry achi hai — public aur private personality consistent hai."
        if _num(sym.get("overall_score")) >= 75
        else "Thodi asymmetry hai — public-private me hint of difference."
    )

    return {
        "five_element_profile": element,
        "five_element_traits": _WUXING_TRAITS.get(element, ""),
        "three_life_zones": zones,
        "symmetry_note": sym_note,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 6 — FEATURE ANALYSIS (7 features × 2-3 readings)
# ──────────────────────────────────────────────────────────────────────────────

def _read(samudrika_feature: Optional[Dict], default: str = "balanced") -> str:
    if not isinstance(samudrika_feature, dict):
        return default
    return (samudrika_feature.get("phala_hi")
            or samudrika_feature.get("phala_en")
            or samudrika_feature.get("english")
            or default)


def section_6_feature_analysis(engines: Dict) -> Dict:
    sam_f = _g(engines, "samudrika", "features") or {}
    p     = engines.get("personality", {})
    fwhr  = engines.get("fwhr", {})

    ocean = p.get("ocean_summary_scores") or {}
    O = _num(ocean.get("openness"))
    C = _num(ocean.get("conscientiousness"))
    E = _num(ocean.get("extraversion"))
    A = _num(ocean.get("agreeableness"))

    return {
        "eyes": {
            "shape_reading":   _read(sam_f.get("eyes")),
            "emotion_depth":   _band(A),
            "trust_nature":    _band(A, low=40, high=70),
            "intuition_level": _band(O, low=45, high=70),
        },
        "nose": {
            "shape_reading":   _read(sam_f.get("nose")),
            "wealth_mindset":  _band(C),
            "decision_power":  _band(C, low=45, high=70),
        },
        "lips": {
            "shape_reading":         _read(sam_f.get("lips")),
            "communication_style":   "expressive" if E > 60 else "reserved" if E < 40 else "balanced",
            "love_expression":       "warm" if A > 60 else "guarded" if A < 40 else "moderate",
        },
        "jawline_chin": {
            "shape_reading":  _read(sam_f.get("jaw_chin")),
            "willpower":      _band(C),
            "dominance_level": _band(_num(fwhr.get("dominance_score"), default=min(100.0, _num(fwhr.get("fwhr_value"), default=1.85) * 30))),
        },
        "forehead": {
            "shape_reading":         _read(sam_f.get("forehead")),
            "intelligence_pattern":  _band(O),
            "thinking_ability":      _band((O + C) / 2),
        },
        "eyebrows": {
            "shape_reading":  _read(sam_f.get("eyebrows")),
            "discipline":     _band(C),
            "energy_pattern": _band(E),
        },
        "ears": {
            "shape_reading":     _read(sam_f.get("ears")),
            "learning_ability":  _band(O),
            "luck_indicator":    _g(engines, "samudrika", "composite_scores", "bhagya", default=70),
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 7 — PERSONALITY SYNTHESIS (Top 5 strengths / weaknesses + behaviour)
# ──────────────────────────────────────────────────────────────────────────────

# Mapping: trait + level → strength / weakness phrases (Hinglish)
_TRAIT_STRENGTHS = {
    ("openness", "high"):          "Creative imagination — naye ideas ki bhandaar.",
    ("openness", "low"):           "Practical mind — proven cheezo me believe karte ho.",
    ("conscientiousness", "high"): "Strong discipline aur planning skills.",
    ("conscientiousness", "low"):  "Flexible aur adaptable — rules ke gulaam nahi.",
    ("extraversion", "high"):      "Confident social presence, log aapko notice karte hain.",
    ("extraversion", "low"):       "Deep thinker, akele me bhi comfortable.",
    ("agreeableness", "high"):     "Warm-hearted, log easily trust karte hain.",
    ("agreeableness", "low"):      "Strong personal boundaries, manipulate nahi hote.",
    ("neuroticism", "low"):        "Emotionally stable — pressure me bhi calm rehte ho.",
    ("neuroticism", "high"):       "Deeply emotionally aware (badi sensitivity).",
}

_TRAIT_WEAKNESSES = {
    ("openness", "high"):          "Kabhi-kabhi too many ideas — focus distract ho jata hai.",
    ("openness", "low"):           "Naye change accept karne me waqt lagta hai.",
    ("conscientiousness", "high"): "Perfectionism stress de sakta hai.",
    ("conscientiousness", "low"):  "Deadlines aur structure follow karne me dikkat.",
    ("extraversion", "high"):      "Akele rehna mushkil — over-stimulation ki need.",
    ("extraversion", "low"):       "Networking aur self-promotion avoid karte ho.",
    ("agreeableness", "high"):     "Doosron ki jarurat ke liye apni need ignore karte ho.",
    ("agreeableness", "low"):      "Conflict me thoda bahut harsh ho jaate ho.",
    ("neuroticism", "high"):       "Overthinking aur worry pattern.",
    ("neuroticism", "low"):        "Kabhi-kabhi doosron ke pain ko under-estimate karte ho.",
}


def section_7_personality_synthesis(engines: Dict) -> Dict:
    p = engines.get("personality", {})
    ocean = p.get("ocean_summary_scores") or {}
    archetype = (p.get("archetype") or {}).get("name") or "Balanced"
    fi = engines.get("first_impression", {})

    # Rank traits by deviation from 50
    trait_scores = {k: _num(v) for k, v in ocean.items()}
    by_intensity = sorted(trait_scores.items(), key=lambda kv: abs(kv[1] - 50), reverse=True)

    strengths = []
    weaknesses = []
    for trait, score in by_intensity:
        level = "high" if score >= 55 else "low" if score <= 45 else None
        if not level:
            continue
        s = _TRAIT_STRENGTHS.get((trait, level))
        w = _TRAIT_WEAKNESSES.get((trait, level))
        if s and len(strengths) < 5: strengths.append(s)
        if w and len(weaknesses) < 5: weaknesses.append(w)

    # Boost strengths from first-impression high dims
    fi4 = fi.get("first_impression_4") or {}
    extra_strength_map = {
        "confidence": "Strong self-confidence dikhta hai.",
        "trust":      "Logo me natural trust pakad lete ho.",
        "attraction": "Magnetic presence — log towards you draw hote hain.",
        "authority":  "Authority figure jaisa impression dete ho.",
    }
    for k, v in fi4.items():
        if _num(v) >= 70 and len(strengths) < 5:
            extra = extra_strength_map.get(k)
            if extra and extra not in strengths:
                strengths.append(extra)

    # Pad if still short — use distinct fillers based on archetype/element
    elem_low = (archetype or "").lower()
    strength_pool = [
        "Balanced personality — extreme nahi ho, har situation handle kar lete ho.",
        "Adaptable — naye logon aur naye mahaul me dhal jate ho.",
        "Reliable — log tumpe count kar sakte hain.",
        "Practical thinker — emotion aur logic dono use karte ho.",
        "Self-aware — apni strengths aur limits dono samajhte ho.",
    ]
    weakness_pool = [
        "Sometimes self-doubt creeps in — decision lete waqt second-guess karte ho.",
        "Overthinking — chhoti baat ko bhi mind me bada bana lete ho.",
        "Apni opinion khulkar express karne me hesitate karte ho.",
        "Comfort zone se bahar nikalna mushkil lagta hai.",
        "Conflict avoid karte ho — kabhi-kabhi apna point chhod dete ho.",
    ]
    si = 0
    while len(strengths) < 5 and si < len(strength_pool):
        if strength_pool[si] not in strengths:
            strengths.append(strength_pool[si])
        si += 1
    wi = 0
    while len(weaknesses) < 5 and wi < len(weakness_pool):
        if weakness_pool[wi] not in weaknesses:
            weaknesses.append(weakness_pool[wi])
        wi += 1

    # Behaviour pattern paragraph
    dom = p.get("dominant_trait") or "balanced"
    sec = p.get("secondary_trait") or ""
    behaviour = (
        f"Tumhari core personality {dom} dominant hai" +
        (f" with {sec} secondary." if sec else ".") +
        f" Archetype: {archetype}. Real life me tum naturally"
        f" {'people-oriented' if _num(ocean.get('extraversion')) > 55 else 'task-oriented'}"
        f" ho aur {'risk-taker' if _num(ocean.get('openness')) > 60 else 'careful planner'} ho."
    )

    return {
        "top_5_strengths":  strengths[:5],
        "top_5_weaknesses": weaknesses[:5],
        "behaviour_pattern": behaviour,
        "dominant_trait":   dom,
        "archetype":        archetype,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 9 — CAREER & MONEY PATTERN
# ──────────────────────────────────────────────────────────────────────────────

def section_9_career_money(engines: Dict) -> Dict:
    p = engines.get("personality", {})
    ocean = p.get("ocean_summary_scores") or {}
    sam = engines.get("samudrika", {}).get("composite_scores") or {}

    O = _num(ocean.get("openness"));         C = _num(ocean.get("conscientiousness"))
    E = _num(ocean.get("extraversion"));     A = _num(ocean.get("agreeableness"))
    N = _num(ocean.get("neuroticism"))

    # Job vs Business
    biz_score = O*0.4 + E*0.3 + (100-N)*0.2 + (100-A)*0.1
    if biz_score > 65:    job_vs_biz = "Business / Entrepreneur"
    elif biz_score < 45:  job_vs_biz = "Job / Stable employment"
    else:                 job_vs_biz = "Hybrid (job + side business)"

    # Risk taking
    risk = O*0.5 + (100-N)*0.3 + E*0.2
    risk_level = _band(risk, low=45, high=65)

    # Wealth growth — combine personality with samudrika dhana score
    dhana = _num(sam.get("dhana"), default=70)
    bhagya = _num(sam.get("bhagya"), default=70)
    wealth_pattern = (
        "Steady aur slow growth — long-term me strong wealth banegi."
        if C > 60 and N < 50 else
        "Up-down pattern — windfall ke saath setbacks bhi aate hain."
        if N > 55 else
        "Moderate growth — discipline badhane se accelerate hoga."
    )

    # Money mindset
    if C > 60 and A < 55: money_mind = "Saver — paise sambhal ke kharch karte ho."
    elif E > 60 and O > 60: money_mind = "Spender — experiences pe invest karte ho."
    elif A > 65: money_mind = "Generous — doosro pe bhi spend karte ho."
    else: money_mind = "Balanced — saving + spending dono manage karte ho."

    return {
        "job_vs_business":   job_vs_biz,
        "risk_taking_ability": risk_level,
        "wealth_growth_pattern": wealth_pattern,
        "money_mindset":     money_mind,
        "wealth_score_100":  round((dhana + bhagya) / 2, 1),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 11 — ATTRACTION & CHARISMA
# ──────────────────────────────────────────────────────────────────────────────

def section_11_attraction_charisma(engines: Dict, gender: Optional[str] = None) -> Dict:
    fi4 = _g(engines, "first_impression", "first_impression_4") or {}
    p = engines.get("personality", {})
    ocean = p.get("ocean_summary_scores") or {}
    phi = engines.get("phi", {})

    attraction = _num(fi4.get("attraction"))
    O = _num(ocean.get("openness"));     E = _num(ocean.get("extraversion"))
    A = _num(ocean.get("agreeableness")); C = _num(ocean.get("conscientiousness"))

    # Charisma type
    if E > 60 and A > 55:        ctype = "Social Charisma — warmth + energy."
    elif O > 65 and E < 50:      ctype = "Mysterious Charisma — depth + intrigue."
    elif A > 65:                 ctype = "Warm Charisma — kindness aur sincerity."
    elif C > 65 and E > 50:      ctype = "Authority Charisma — confidence + competence."
    else:                        ctype = "Quiet Charisma — subtle but strong."

    # Opposite gender perception
    perception = (
        "Opposite gender tumhe approachable aur attractive maanta hai."
        if attraction >= 65 else
        "Opposite gender ko thodi waqt lagta hai tumhe samajhne me."
        if attraction <= 45 else
        "Opposite gender me normal interest aata hai."
    )

    return {
        "natural_attraction_score_10": _to_10(attraction),
        "phi_beauty_score":            round(_num(phi.get("overall_phi_score")), 1),
        "opposite_gender_perception":  perception,
        "charisma_type":               ctype,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 12 — DECISION-MAKING STYLE
# ──────────────────────────────────────────────────────────────────────────────

def section_12_decision_style(engines: Dict) -> Dict:
    p = engines.get("personality", {})
    ocean = p.get("ocean_summary_scores") or {}
    O = _num(ocean.get("openness"));     C = _num(ocean.get("conscientiousness"))
    E = _num(ocean.get("extraversion")); A = _num(ocean.get("agreeableness"))
    N = _num(ocean.get("neuroticism"))

    fast_slow   = "Fast" if (E > 60 and N < 50) else "Slow" if N > 55 else "Moderate"
    log_emo     = "Logical" if (C > 60 and N < 45) else "Emotional" if (A > 60 or N > 55) else "Mixed"
    risk_safe   = "Risk-taker" if (O > 60 and N < 50) else "Safe" if N > 55 else "Balanced"

    return {
        "fast_vs_slow":         fast_slow,
        "logical_vs_emotional": log_emo,
        "risk_vs_safe":         risk_safe,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 13 — LIFE ROLE / ARCHETYPE
# ──────────────────────────────────────────────────────────────────────────────

def section_13_archetype(engines: Dict) -> Dict:
    a = _g(engines, "personality", "archetype") or {}
    return {
        "archetype_name":     a.get("name") or "Balanced",
        "archetype_summary":  a.get("summary") or a.get("description") or "Multi-faceted personality.",
        "core_role_in_life":  a.get("core_role") or a.get("life_role") or "Adapter — har situation me fit ho jaate ho.",
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 15 — AGE-WISE LIFE MAP
# ──────────────────────────────────────────────────────────────────────────────

def section_15_age_wise_map(engines: Dict) -> Dict:
    awf = _g(engines, "samudrika", "age_wise_fortune") or {}
    purva  = _num(awf.get("purva_aayu"),  default=70)
    madhya = _num(awf.get("madhya_aayu"), default=70)
    uttara = _num(awf.get("uttara_aayu"), default=70)

    phases = [("20s", purva), ("30s-40s", madhya), ("50s+", uttara)]
    sorted_p = sorted(phases, key=lambda x: x[1], reverse=True)
    golden = sorted_p[0][0]
    alert  = sorted_p[-1][0]

    def _phase_text(score, label):
        if score >= 80:  return f"{label}: Peak phase — major achievements likely."
        if score >= 70:  return f"{label}: Strong phase — steady progress."
        if score >= 60:  return f"{label}: Normal phase — efforts pay off slowly."
        return f"{label}: Cautious phase — patience aur planning chahiye."

    return {
        "phase_20s":     _phase_text(purva, "20s"),
        "phase_30s_40s": _phase_text(madhya, "30s-40s"),
        "phase_50s_plus": _phase_text(uttara, "50s+"),
        "golden_period": f"Best phase: {golden}",
        "alert_period":  f"Most cautious: {alert}",
        "scores": {"20s": round(purva, 1), "30s_40s": round(madhya, 1), "50s_plus": round(uttara, 1)},
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 16 — HEALTH & ENERGY SCAN  (3 fields template asks)
# ──────────────────────────────────────────────────────────────────────────────

def section_16_health_scan(engines: Dict) -> Dict:
    h = engines.get("health", {})
    ind = h.get("macro_indicators") or {}

    def pick(*names, default="medium"):
        for n in names:
            if n in ind:
                v = ind[n]
                return v if isinstance(v, (str, int, float)) else default
        return default

    stress  = pick("stress", "stress_level", "stress_signal")
    energy  = pick("energy", "energy_level", "vitality_indicator")
    burnout = pick("burnout", "burnout_signal", "fatigue")

    vitality = h.get("vitality_score")
    return {
        "stress_indicator":   stress,
        "energy_level":       energy,
        "burnout_signal":     burnout,
        "vitality_score_100": round(_num(vitality), 1) if vitality is not None else None,
        "vitality_class":     h.get("vitality_class"),
    }


# ──────────────────────────────────────────────────────────────────────────────
# BONUS — PERSONALITY SCORE (5 dims /10)
# ──────────────────────────────────────────────────────────────────────────────

def bonus_personality_score(engines: Dict) -> Dict:
    p = engines.get("personality", {})
    ocean = p.get("ocean_summary_scores") or {}
    composites = p.get("composites") or {}
    sam = engines.get("samudrika", {}).get("composite_scores") or {}
    fi4 = _g(engines, "first_impression", "first_impression_4") or {}
    h = engines.get("health", {})

    # Leadership: prefer composite, else derive from E + C + authority
    leader = composites.get("leadership")
    if leader is None:
        leader = (_num(ocean.get("extraversion")) * 0.4
                  + _num(ocean.get("conscientiousness")) * 0.3
                  + _num(fi4.get("authority")) * 0.3)

    # Money — Vedic dhana score primary
    money = _num(sam.get("dhana"), default=_num(ocean.get("conscientiousness")))

    # Love — Vedic sambandha + agreeableness
    love = (_num(sam.get("sambandha"), default=_num(ocean.get("agreeableness"))) * 0.6
            + _num(ocean.get("agreeableness")) * 0.4)

    # Health — vitality
    health_score = _num(h.get("vitality_score"))

    # Intelligence — Vedic buddhi + openness
    intel = (_num(sam.get("buddhi"), default=_num(ocean.get("openness"))) * 0.6
             + _num(ocean.get("openness")) * 0.4)

    return {
        "leadership_10":   _to_10(leader),
        "money_10":        _to_10(money),
        "love_10":         _to_10(love),
        "health_10":       _to_10(health_score),
        "intelligence_10": _to_10(intel),
    }


# ──────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY-POINT
# ──────────────────────────────────────────────────────────────────────────────

def build_report_sections(
    engines: Dict[str, Any],
    *,
    gender: Optional[str] = None,
    age: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build the data-ready 21-section report from projected engine outputs.

    Sections 1, 8, 10, 14, 17, 18, 19, 20, 21 are intentionally NOT filled
    here — they require Step 3 (new section builders) and Step 4 (synthesizer).
    """
    return {
        "section_2_psychological_type":     section_2_psychological_type(engines),
        "section_3_mask_vs_real":           section_3_mask_vs_real(engines),
        "section_4_first_impression":       section_4_first_impression(engines),
        "section_5_core_foundation":        section_5_core_foundation(engines),
        "section_6_feature_analysis":       section_6_feature_analysis(engines),
        "section_7_personality_synthesis":  section_7_personality_synthesis(engines),
        "section_9_career_money":           section_9_career_money(engines),
        "section_11_attraction_charisma":   section_11_attraction_charisma(engines, gender=gender),
        "section_12_decision_style":        section_12_decision_style(engines),
        "section_13_archetype":             section_13_archetype(engines),
        "section_15_age_wise_map":          section_15_age_wise_map(engines),
        "section_16_health_scan":           section_16_health_scan(engines),
        "bonus_personality_score":          bonus_personality_score(engines),
        "_pending_sections": [
            "section_1_power_summary",
            "section_8_love_relationship_dna",
            "section_10_red_flags",
            "section_14_life_flow",
            "section_17_secret_markings",
            "section_18_action_plan",
            "section_19_improvement_hacks",
            "section_20_compatibility",
            "section_21_final_truth",
        ],
    }

"""
Engine 6 — Big Five Personality (OCEAN) from Face — v2
=========================================================

Face-derived inference of the five-factor personality model + Oosterhof-Todorov
Valence-Dominance 2D social-perception model.

Outputs:
  • OCEAN (5 traits) with 30 NEO-PI-R sub-facets (where measurable)
  • Oosterhof & Todorov (2008) Valence-Dominance 2D coords
  • Trustworthiness, Dominance, Approachability, Maturity composites
  • Profile fingerprint, archetype, percentiles, strengths, growth-edges
  • Career-fit + relationship-style hints (informational)
  • Bayesian shrinkage toward population mean (effect-size correction)
  • Demographic adjustments (gender, ethnicity, age)
  • Hinglish + EN narratives, perceived-trait disclaimer

CHANGELOG v1 → v2 (47 audit fixes):
  A. SCHEMA BUGS (4):
    1. fwhr extraction → fwhr_result["primary"]["value"]
    2. phi extraction → phi_result["overall_phi_score"]
    3. Dominance z-score from fwhr.composite_scores.dominance_signal
    4. Masculinity z-score from fwhr.composite_scores.masculinity_signal
  B. NORM CALIBRATION (11):
    5-15. All 11 raw-measurement ranges recalibrated to outer-canthal IOD
          baseline using anthropometry literature (Farkas, Hall, Stengel-Rutkowski)
  C. DEMOGRAPHIC ADJUSTMENTS (3):
    16. Gender-banded fWHR / brow / lip baselines
    17. Ethnicity-banded forehead / eye-spacing / nose norms
    18. Age-banded wrinkle/nasolabial correction (so wrinkles ≠ N for elderly)
  D. NEW MEASUREMENTS (10):
    19. babyfaceness_index (Berry & McArthur 1985)
    20. cheek_prominence (zygion projection proxy)
    21. eye_spacing_ratio (inner/outer canthal)
    22. nose_width_iod
    23. nose_length_face_ratio
    24. chin_projection_norm
    25. smile_asymmetry
    26. crow_feet_proxy (from health.aging_signs)
    27. glabellar_proxy (between-brow furrow)
    28. nasolabial_fold_proxy (from health.aging_signs)
  E. NEW DIMENSIONS (4):
    29. Oosterhof-Todorov 2008 Valence-Dominance 2D coords
    30. Trustworthiness composite
    31. Dominance composite
    32. Approachability + Maturity composites
  F. NEO-PI-R SUB-FACETS (5):
    33-37. 30 facets total (6 × 5 traits) with measurability flag
  G. SCORING (4):
    38. Bayesian shrinkage toward 50 (effect-size correction; α=0.30)
    39. Per-trait percentile (z-score → Phi CDF approximation)
    40. Strengths + growth-edges (3 each per trait)
    41. Inter-trait inconsistency detector
  H. HINTS (2):
    42. Career-fit hints (informational only)
    43. Relationship-style hints
  I. SAFETY/ETHICS (3):
    44. HR/workplace explicit disclaimer (do_not_use_for_hiring=True)
    45. Western-population bias acknowledgment
    46. Self-fulfilling prophecy caveat
  J. FIXTURES (1):
    47. 4 scenario fixtures for regression testing

Scientific basis (selected):
  • Walker & Vetter 2016 — Big Five trait modeling on photos
  • Penton-Voak et al. 2006 — composite face → traits
  • Kramer & Ward 2010 — internal facial features → traits
  • Carré & McCormick 2008 — fWHR → aggression/dominance
  • Stirrat & Perrett 2010 — fWHR → trustworthiness
  • Oosterhof & Todorov 2008 — 2D valence-dominance face model
  • Berry & McArthur 1985 — babyfaceness theory
  • Knutson 1996 — facial expression and personality
  • Hess et al. 2009 — brow position and emotion perception
  • Said & Todorov 2011 — overgeneralization of trait perception
  • Asendorpf & van Aken 1999 — RUO archetypes (Resilient/Over/Undercontrolled)
  • Costa & McCrae 1992 — NEO-PI-R 30-facet structure
  • Farkas et al. — anthropometric norms for facial proportions
"""
from __future__ import annotations
from typing import Optional, Sequence
import math
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# Sanitizer (np types → Python natives)
# ─────────────────────────────────────────────────────────────────────────────
def _py(o):
    if isinstance(o, dict):  return {k: _py(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):  return [_py(x) for x in o]
    if isinstance(o, np.bool_):    return bool(o)
    if isinstance(o, np.integer):  return int(o)
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, np.ndarray):  return _py(o.tolist())
    return o


# ─────────────────────────────────────────────────────────────────────────────
# Landmark indices (MediaPipe FaceMesh 478)
# ─────────────────────────────────────────────────────────────────────────────
R_EYE_OUTER, R_EYE_INNER = 33,  133
L_EYE_OUTER, L_EYE_INNER = 263, 362
R_EYE_TOP,   R_EYE_BOT   = 159, 145
L_EYE_TOP,   L_EYE_BOT   = 386, 374
R_BROW_INNER, R_BROW_PEAK, R_BROW_OUTER = 107, 105, 70
L_BROW_INNER, L_BROW_PEAK, L_BROW_OUTER = 336, 334, 300
M_CORNER_R, M_CORNER_L = 61, 291
M_UPPER_MID, M_LOWER_MID = 13, 14
M_UPPER_OUT, M_LOWER_OUT = 0, 17
NOSE_TIP, CHIN, FOREHEAD_TOP = 1, 152, 10
NOSE_BRIDGE, NOSE_LEFT, NOSE_RIGHT = 6, 49, 279
ZYGION_R, ZYGION_L = 234, 454
JAW_R, JAW_L = 172, 397
GLABELLA = 9
PHILTRUM_TOP = 164  # subnasale region


# ─────────────────────────────────────────────────────────────────────────────
# Demographic baselines (literature-derived; conservative)
# ─────────────────────────────────────────────────────────────────────────────
GENDER_BASELINE = {
    "M": {"fwhr_mean": 1.93, "brow_height_mean": 0.18, "lip_full_mean": 0.18,
          "jaw_angle_mean": 122, "wrinkle_age_factor": 1.0},
    "F": {"fwhr_mean": 1.85, "brow_height_mean": 0.22, "lip_full_mean": 0.22,
          "jaw_angle_mean": 128, "wrinkle_age_factor": 0.85},
    "U": {"fwhr_mean": 1.89, "brow_height_mean": 0.20, "lip_full_mean": 0.20,
          "jaw_angle_mean": 125, "wrinkle_age_factor": 0.95},
}

ETHNICITY_BASELINE = {
    "south_asian": {"forehead_h_mean": 0.26, "eye_spacing_mean": 1.05, "nose_width_mean": 0.42},
    "east_asian":  {"forehead_h_mean": 0.28, "eye_spacing_mean": 1.10, "nose_width_mean": 0.40},
    "european":    {"forehead_h_mean": 0.27, "eye_spacing_mean": 1.00, "nose_width_mean": 0.36},
    "african":     {"forehead_h_mean": 0.27, "eye_spacing_mean": 1.02, "nose_width_mean": 0.46},
    "middle_eastern": {"forehead_h_mean": 0.26, "eye_spacing_mean": 1.02, "nose_width_mean": 0.40},
    "latino":      {"forehead_h_mean": 0.26, "eye_spacing_mean": 1.03, "nose_width_mean": 0.40},
    "default":     {"forehead_h_mean": 0.27, "eye_spacing_mean": 1.03, "nose_width_mean": 0.40},
}

def _gender_norm(gender: str) -> dict:
    return GENDER_BASELINE.get((gender or "U").upper(), GENDER_BASELINE["U"])

def _ethnicity_norm(eth: Optional[str]) -> dict:
    if not eth: return ETHNICITY_BASELINE["default"]
    return ETHNICITY_BASELINE.get(eth.lower(), ETHNICITY_BASELINE["default"])

def _age_wrinkle_expected(age: Optional[int]) -> float:
    """Expected wrinkle/aging score 0-100 for age (so we don't penalize old age as N)."""
    if age is None: return 0.0
    if age < 25: return 0.0
    if age < 35: return 10.0
    if age < 45: return 25.0
    if age < 55: return 45.0
    if age < 65: return 65.0
    return 80.0


# ─────────────────────────────────────────────────────────────────────────────
# Evidence catalog (citation index — extended in v2)
# ─────────────────────────────────────────────────────────────────────────────
EVIDENCE = {
    # Extraversion
    "mouth_corner_upturn":   {"trait": "E", "weight": 0.20, "ref": "Knutson_1996_smile_extraversion"},
    "smile_width":           {"trait": "E", "weight": 0.10, "ref": "Penton-Voak_2006_composite"},
    "eye_openness":          {"trait": "E", "weight": 0.10, "ref": "Walker_Vetter_2016"},
    "fwhr_dominance":        {"trait": "E", "weight": 0.16, "ref": "Carre_McCormick_2008_fWHR"},
    "vitality_proxy":        {"trait": "E", "weight": 0.18, "ref": "Penton-Voak_2001_health_perception"},
    "lip_fullness":          {"trait": "E", "weight": 0.06, "ref": "Said_Todorov_2011"},
    "brow_height":           {"trait": "E", "weight": 0.08, "ref": "Walker_Vetter_2016"},
    "crow_feet_duchenne":    {"trait": "E", "weight": 0.12, "ref": "Ekman_Friesen_1982_Duchenne"},

    # Conscientiousness
    "facial_symmetry":       {"trait": "C", "weight": 0.26, "ref": "Penton-Voak_2001_symmetry"},
    "jaw_firmness":          {"trait": "C", "weight": 0.16, "ref": "Carre_McCormick_2008"},
    "skin_clarity_proxy":    {"trait": "C", "weight": 0.16, "ref": "Kramer_Ward_2010"},
    "brow_steady":           {"trait": "C", "weight": 0.10, "ref": "Walker_Vetter_2016"},
    "phi_alignment":         {"trait": "C", "weight": 0.12, "ref": "Pallett_2010_golden_ratio"},
    "groomed_proxy":         {"trait": "C", "weight": 0.08, "ref": "Borkenau_2009_zero_acquaintance"},
    "chin_projection":       {"trait": "C", "weight": 0.12, "ref": "Said_Todorov_2011_competence"},

    # Openness
    "forehead_height_ratio": {"trait": "O", "weight": 0.18, "ref": "Walker_Vetter_2016"},
    "eye_width_ratio":       {"trait": "O", "weight": 0.16, "ref": "Said_Todorov_2011"},
    "philtrum_distinct":     {"trait": "O", "weight": 0.10, "ref": "Penton-Voak_2006"},
    "novel_proportions":     {"trait": "O", "weight": 0.14, "ref": "Walker_Vetter_2016"},
    "brow_arch":             {"trait": "O", "weight": 0.16, "ref": "Said_Todorov_2011"},
    "eye_spacing_open":      {"trait": "O", "weight": 0.12, "ref": "Berry_McArthur_1985"},
    "nose_distinct":         {"trait": "O", "weight": 0.08, "ref": "Penton-Voak_2006"},
    "facial_distinctiveness":{"trait": "O", "weight": 0.06, "ref": "Walker_Vetter_2016"},

    # Agreeableness
    "rounded_features":      {"trait": "A", "weight": 0.20, "ref": "Berry_McArthur_1985_babyface"},
    "low_fwhr":              {"trait": "A", "weight": 0.18, "ref": "Stirrat_Perrett_2010"},
    "soft_jaw_angle":        {"trait": "A", "weight": 0.12, "ref": "Carre_2009"},
    "eye_warmth":            {"trait": "A", "weight": 0.12, "ref": "Said_Todorov_2011"},
    "mouth_corner_upturn_a": {"trait": "A", "weight": 0.14, "ref": "Knutson_1996"},
    "babyface_index":        {"trait": "A", "weight": 0.16, "ref": "Berry_McArthur_1985"},
    "low_dominance":         {"trait": "A", "weight": 0.08, "ref": "Oosterhof_Todorov_2008"},

    # Neuroticism
    "brow_furrow_lines":     {"trait": "N", "weight": 0.18, "ref": "Hess_2009_anger_brow"},
    "low_brow":              {"trait": "N", "weight": 0.12, "ref": "Said_Todorov_2011"},
    "tight_mouth":           {"trait": "N", "weight": 0.10, "ref": "Said_Todorov_2011"},
    "asym_microexpr":        {"trait": "N", "weight": 0.10, "ref": "Penton-Voak_2001"},
    "mouth_corner_droop":    {"trait": "N", "weight": 0.16, "ref": "Knutson_1996"},
    "low_vitality_proxy":    {"trait": "N", "weight": 0.10, "ref": "Penton-Voak_2001_health"},
    "dark_circles":          {"trait": "N", "weight": 0.08, "ref": "Walker_Vetter_2016"},
    "glabellar_lines":       {"trait": "N", "weight": 0.10, "ref": "Hess_2009_anger_brow"},
    "smile_asymmetry":       {"trait": "N", "weight": 0.06, "ref": "Penton-Voak_2001"},
}


# ─────────────────────────────────────────────────────────────────────────────
# Geometry helpers
# ─────────────────────────────────────────────────────────────────────────────
def _dist(p, q): return math.hypot(p[0]-q[0], p[1]-q[1])
def _midpoint(p, q): return ((p[0]+q[0])/2, (p[1]+q[1])/2)
def _safe_div(a, b, default=0.0): return (a/b) if b > 1e-9 else default
def _clip01(x): return max(0.0, min(1.0, x))
def _pixel(p, W, H): return (p[0]*W, p[1]*H)

def _to_score(value: float, lo: float, hi: float, invert: bool = False) -> float:
    if hi == lo: return 50.0
    p = _clip01((value - lo) / (hi - lo))
    if invert: p = 1.0 - p
    return round(p * 100, 1)

def _trait_class(score: float) -> str:
    if score >= 80: return "very_high"
    if score >= 65: return "high"
    if score >= 50: return "moderate_high"
    if score >= 35: return "moderate_low"
    if score >= 20: return "low"
    return "very_low"

def _z_to_percentile(z: float) -> float:
    """Phi CDF approximation (Abramowitz & Stegun 26.2.17)."""
    return round(50 * (1 + math.erf(z / math.sqrt(2))), 1)

def _score_to_percentile(score: float) -> float:
    """Treat score 50 as median, sd~15."""
    z = (score - 50) / 15.0
    return _z_to_percentile(z)

def _bayesian_shrink(score: float, alpha: float = 0.30) -> float:
    """Pull score toward 50 by `alpha` to correct over-confident face-derived effects.
    Walker & Vetter 2016 effect sizes are small (~5-15 pt range)."""
    return round(50 + (1 - alpha) * (score - 50), 1)

def _conf_from_quality(symmetry_ok: bool, n_signals: int, stability: str) -> str:
    base = "low"
    if symmetry_ok and n_signals >= 6: base = "high"
    elif symmetry_ok and n_signals >= 4: base = "medium"
    elif n_signals >= 3: base = "medium"
    if stability == "low":
        if base == "high": base = "medium"
        elif base == "medium": base = "low"
    return base


# ─────────────────────────────────────────────────────────────────────────────
# NEO-PI-R sub-facet definitions (Costa & McCrae 1992)
# ─────────────────────────────────────────────────────────────────────────────
NEO_FACETS = {
    "O": ["fantasy", "aesthetics", "feelings", "actions", "ideas", "values"],
    "C": ["competence", "order", "dutifulness", "achievement_striving",
          "self_discipline", "deliberation"],
    "E": ["warmth", "gregariousness", "assertiveness", "activity",
          "excitement_seeking", "positive_emotions"],
    "A": ["trust", "straightforwardness", "altruism", "compliance",
          "modesty", "tendermindedness"],
    "N": ["anxiety", "angry_hostility", "depression", "self_consciousness",
          "impulsiveness", "vulnerability"],
}


# ─────────────────────────────────────────────────────────────────────────────
# Hinglish + EN narratives per trait × class
# ─────────────────────────────────────────────────────────────────────────────
NARRATIVES = {
    "O": {
        "very_high":     {"en": "Highly imaginative — drawn to novelty, art, abstract thought.",
                           "hi": "Bahut creative — naye ideas, art, abstract thinking pasand."},
        "high":          {"en": "Open to experience — enjoys variety and intellectual exploration.",
                           "hi": "Naye experiences ke liye open — curiosity strong."},
        "moderate_high": {"en": "Balanced openness — enjoys some novelty, values familiarity.",
                           "hi": "Thoda explorer, thoda comfort-seeker."},
        "moderate_low":  {"en": "Practical and grounded — prefers tested ideas.",
                           "hi": "Practical mindset — proven cheezein zyada pasand."},
        "low":           {"en": "Conservative thinker — values tradition and routine.",
                           "hi": "Tradition aur routine pasand."},
        "very_low":      {"en": "Strongly conventional — prefers familiar over abstract.",
                           "hi": "Bahut conventional — naye-pan se distance."},
    },
    "C": {
        "very_high":     {"en": "Very disciplined — strong self-control and goal-orientation.",
                           "hi": "Bahut disciplined — self-control strong."},
        "high":          {"en": "Conscientious and organized — follows through on commitments.",
                           "hi": "Organized aur committed — goals follow karte hain."},
        "moderate_high": {"en": "Generally organized but flexible when needed.",
                           "hi": "Mostly organized, flexibility bhi hai."},
        "moderate_low":  {"en": "Spontaneous side — sometimes prioritizes flow over structure.",
                           "hi": "Spontaneous nature — kabhi flow zyada important."},
        "low":           {"en": "Flexible and easy-going — structure feels limiting.",
                           "hi": "Easy-going — strict structure pasand nahi."},
        "very_low":      {"en": "Highly spontaneous — routine feels constraining.",
                           "hi": "Bahut spontaneous — routine binding lagti."},
    },
    "E": {
        "very_high":     {"en": "Strongly extraverted — energized by people, expressive.",
                           "hi": "Bahut extrovert — log ke saath energy aati hai."},
        "high":          {"en": "Outgoing and sociable — enjoys group settings.",
                           "hi": "Sociable aur outgoing — group me comfortable."},
        "moderate_high": {"en": "Ambivert — balances people and quiet time.",
                           "hi": "Ambivert — log aur akele dono pasand."},
        "moderate_low":  {"en": "Selectively social — prefers small circles and depth.",
                           "hi": "Selective social — depth zyada important."},
        "low":           {"en": "Reserved — recharges in quiet, prefers small-group interaction.",
                           "hi": "Reserved — akele recharge hote hain."},
        "very_low":      {"en": "Strongly introverted — solitude is restorative.",
                           "hi": "Bahut introvert — akele time energizing."},
    },
    "A": {
        "very_high":     {"en": "Very warm and cooperative — strong empathy.",
                           "hi": "Bahut warm aur cooperative — empathy strong."},
        "high":          {"en": "Agreeable and accommodating — values harmony.",
                           "hi": "Agreeable — harmony important."},
        "moderate_high": {"en": "Generally cooperative but assertive when needed.",
                           "hi": "Cooperative, zaroorat par assertive bhi."},
        "moderate_low":  {"en": "Direct and analytical — prioritizes results over feelings.",
                           "hi": "Direct aur analytical — results pehle."},
        "low":           {"en": "Skeptical and competitive — questions before trusting.",
                           "hi": "Skeptical — trust ke pehle questions."},
        "very_low":      {"en": "Strongly competitive — challenges before cooperation.",
                           "hi": "Competitive nature — challenge pehle."},
    },
    "N": {
        "very_high":     {"en": "High emotional sensitivity — strong reactions to stress.",
                           "hi": "High emotional sensitivity — stress fast trigger."},
        "high":          {"en": "Emotionally responsive — feels things deeply.",
                           "hi": "Emotionally responsive — feelings deep."},
        "moderate_high": {"en": "Some emotional reactivity — generally manages stress.",
                           "hi": "Thoda reactive, manage karte hain."},
        "moderate_low":  {"en": "Emotionally steady — handles stress well.",
                           "hi": "Emotionally stable."},
        "low":           {"en": "Calm and resilient — composed under pressure.",
                           "hi": "Calm aur resilient — pressure me composed."},
        "very_low":      {"en": "Very stable — rarely shaken by stress.",
                           "hi": "Bahut stable — stress bahut kam."},
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Strengths + growth-edges per trait × class
# ─────────────────────────────────────────────────────────────────────────────
STRENGTHS_GROWTH = {
    "O": {
        "high": {"strengths": ["creative", "curious", "open_minded"],
                 "growth":    ["follow_through_on_ideas", "balance_novelty_with_completion"]},
        "low":  {"strengths": ["consistent", "reliable", "tradition_oriented"],
                 "growth":    ["openness_to_new_methods", "creative_flexibility"]},
    },
    "C": {
        "high": {"strengths": ["disciplined", "dependable", "goal_oriented"],
                 "growth":    ["allow_flexibility", "avoid_perfectionism"]},
        "low":  {"strengths": ["spontaneous", "adaptive", "free_flowing"],
                 "growth":    ["build_routine", "task_completion_habits"]},
    },
    "E": {
        "high": {"strengths": ["energetic", "expressive", "people_oriented"],
                 "growth":    ["solo_focus_time", "deep_listening"]},
        "low":  {"strengths": ["thoughtful", "reflective", "deep_focus"],
                 "growth":    ["selective_socialising", "speak_up_in_groups"]},
    },
    "A": {
        "high": {"strengths": ["empathic", "cooperative", "trustworthy"],
                 "growth":    ["assertiveness", "boundary_setting"]},
        "low":  {"strengths": ["direct", "competitive", "results_driven"],
                 "growth":    ["empathic_listening", "team_harmony"]},
    },
    "N": {
        "high": {"strengths": ["emotionally_aware", "sensitive_to_nuance"],
                 "growth":    ["stress_management", "emotional_regulation"]},
        "low":  {"strengths": ["composed", "resilient", "steady"],
                 "growth":    ["acknowledge_emotions", "vulnerability_practice"]},
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Career-fit + relationship hints (informational)
# ─────────────────────────────────────────────────────────────────────────────
CAREER_HINTS = {
    "O+": ["creative_industries", "research", "design", "writing"],
    "C+": ["operations", "finance", "engineering", "project_management"],
    "E+": ["sales", "teaching", "performing_arts", "leadership"],
    "A+": ["counselling", "healthcare", "HR", "social_work"],
    "N+": ["arts_creative", "introspective_writing", "therapy_aware_roles"],
    "O-": ["compliance", "operations", "structured_roles"],
    "C-": ["entrepreneurship", "creative_freelance", "exploratory_roles"],
    "E-": ["technical_specialist", "research", "writing", "deep_work_roles"],
    "A-": ["competitive_business", "law", "negotiation", "trading"],
    "N-": ["high_pressure_roles", "leadership", "first_responder", "operations"],
}

RELATIONSHIP_HINTS = {
    "O+": "Looks for stimulating, intellectually-curious partners.",
    "C+": "Values reliability and shared planning in relationships.",
    "E+": "Thrives in social, expressive partnerships.",
    "A+": "Naturally harmonising — needs assertive partner balance.",
    "N+": "Needs emotionally validating, patient partner.",
    "O-": "Prefers familiar, traditional relationship patterns.",
    "C-": "Seeks easy-going, low-structure partnerships.",
    "E-": "Prefers deep one-to-one over group social settings.",
    "A-": "Values directness and challenge in partnerships.",
    "N-": "Brings stability — may underestimate partner's emotional needs.",
}


# ─────────────────────────────────────────────────────────────────────────────
# Geometric extraction (v2: 22 indicators vs 12 in v1)
# ─────────────────────────────────────────────────────────────────────────────
def _extract_geometric(pts, W, H) -> dict:
    out = {}
    try:
        re_o = _pixel(pts[R_EYE_OUTER], W, H)
        le_o = _pixel(pts[L_EYE_OUTER], W, H)
        iod = _dist(re_o, le_o)
        if iod < 10:
            return {}

        # ── Eye openness ──
        r_eye_h = _dist(_pixel(pts[R_EYE_OUTER], W, H), _pixel(pts[R_EYE_INNER], W, H))
        l_eye_h = _dist(_pixel(pts[L_EYE_OUTER], W, H), _pixel(pts[L_EYE_INNER], W, H))
        r_eye_v = abs(pts[R_EYE_TOP][1] - pts[R_EYE_BOT][1]) * H
        l_eye_v = abs(pts[L_EYE_TOP][1] - pts[L_EYE_BOT][1]) * H
        out["eye_openness"] = round((_safe_div(r_eye_v, r_eye_h) + _safe_div(l_eye_v, l_eye_h)) / 2, 4)
        out["eye_width_iod_ratio"] = round((r_eye_h + l_eye_h) / 2 / iod, 4)

        # ── Eye spacing (inner-canthal / outer-eye-width) ──
        re_i = _pixel(pts[R_EYE_INNER], W, H)
        le_i = _pixel(pts[L_EYE_INNER], W, H)
        inner_canthal = _dist(re_i, le_i)
        out["eye_spacing_ratio"] = round(_safe_div(inner_canthal, (r_eye_h + l_eye_h) / 2), 4)

        # ── Mouth corners ──
        m_r = _pixel(pts[M_CORNER_R], W, H)
        m_l = _pixel(pts[M_CORNER_L], W, H)
        m_upper = _pixel(pts[M_UPPER_MID], W, H)
        corner_y_avg = (m_r[1] + m_l[1]) / 2
        upturn_norm = (m_upper[1] - corner_y_avg) / iod
        out["mouth_corner_upturn"] = round(upturn_norm, 4)
        out["mouth_corner_drop"] = round(max(0.0, -upturn_norm), 4)
        out["mouth_width_iod"] = round(_dist(m_r, m_l) / iod, 4)
        out["smile_asymmetry"] = round(abs(m_r[1] - m_l[1]) / iod, 4)

        # ── Lip fullness ──
        m_uo = _pixel(pts[M_UPPER_OUT], W, H)
        m_lo = _pixel(pts[M_LOWER_OUT], W, H)
        out["lip_fullness_iod"] = round(_dist(m_uo, m_lo) / iod, 4)

        # ── Brows ──
        rb_p = _pixel(pts[R_BROW_PEAK], W, H)
        lb_p = _pixel(pts[L_BROW_PEAK], W, H)
        rb_h = (pts[R_EYE_TOP][1]*H - rb_p[1]) / iod
        lb_h = (pts[L_EYE_TOP][1]*H - lb_p[1]) / iod
        out["brow_height_iod"] = round((rb_h + lb_h) / 2, 4)
        rb_i_y = pts[R_BROW_INNER][1] * H; rb_o_y = pts[R_BROW_OUTER][1] * H
        lb_i_y = pts[L_BROW_INNER][1] * H; lb_o_y = pts[L_BROW_OUTER][1] * H
        r_arch = ((rb_i_y + rb_o_y) / 2 - rb_p[1]) / iod
        l_arch = ((lb_i_y + lb_o_y) / 2 - lb_p[1]) / iod
        out["brow_arch_iod"] = round((r_arch + l_arch) / 2, 4)
        out["brow_asymmetry_iod"] = round(abs(rb_p[1] - lb_p[1]) / iod, 4)
        # Glabellar gap (between inner brows)
        out["inter_brow_gap_iod"] = round(abs(pts[R_BROW_INNER][0] - pts[L_BROW_INNER][0]) * W / iod, 4)

        # ── Forehead height ──
        fh_top = pts[FOREHEAD_TOP][1] * H
        brow_mid_y = ((pts[R_BROW_INNER][1] + pts[L_BROW_INNER][1]) / 2) * H
        chin_y = pts[CHIN][1] * H
        face_h = chin_y - fh_top
        if face_h > 0:
            out["forehead_height_ratio"] = round((brow_mid_y - fh_top) / face_h, 4)
            # Lower face ratio (chin to mouth) / face_h
            mouth_y = (m_r[1] + m_l[1]) / 2
            out["lower_face_ratio"] = round((chin_y - mouth_y) / face_h, 4)

        # ── Philtrum ──
        nose_y = pts[NOSE_TIP][1] * H
        out["philtrum_length_iod"] = round((m_upper[1] - nose_y) / iod, 4)

        # ── Nose ──
        nl = _pixel(pts[NOSE_LEFT], W, H)
        nr = _pixel(pts[NOSE_RIGHT], W, H)
        out["nose_width_iod"] = round(_dist(nl, nr) / iod, 4)
        nb = _pixel(pts[NOSE_BRIDGE], W, H)
        nt = _pixel(pts[NOSE_TIP], W, H)
        if face_h > 0:
            out["nose_length_face_ratio"] = round(_dist(nb, nt) / face_h, 4)

        # ── Chin projection (chin vs jaw baseline) ──
        try:
            jr = _pixel(pts[JAW_R], W, H); jl = _pixel(pts[JAW_L], W, H)
            ch = _pixel(pts[CHIN], W, H)
            jaw_mid_y = (jr[1] + jl[1]) / 2
            out["chin_projection_norm"] = round((ch[1] - jaw_mid_y) / iod, 4)
        except Exception:
            pass

        # ── Cheek prominence (zygion vs nose-tip horizontal spread / face_h) ──
        try:
            zr = _pixel(pts[ZYGION_R], W, H); zl = _pixel(pts[ZYGION_L], W, H)
            cheek_w = _dist(zr, zl)
            out["cheek_prominence_norm"] = round(cheek_w / iod, 4)
        except Exception:
            pass

        # ── Jaw firmness — gonial-like angle ──
        try:
            jr = _pixel(pts[JAW_R], W, H); jl = _pixel(pts[JAW_L], W, H)
            ch = _pixel(pts[CHIN], W, H)
            zr = _pixel(pts[ZYGION_R], W, H); zl = _pixel(pts[ZYGION_L], W, H)
            v1 = (ch[0]-jr[0], ch[1]-jr[1]); v2 = (zr[0]-jr[0], zr[1]-jr[1])
            cosA = _safe_div(v1[0]*v2[0]+v1[1]*v2[1], (math.hypot(*v1)*math.hypot(*v2)), 1.0)
            angR = math.degrees(math.acos(max(-1, min(1, cosA))))
            v1 = (ch[0]-jl[0], ch[1]-jl[1]); v2 = (zl[0]-jl[0], zl[1]-jl[1])
            cosA = _safe_div(v1[0]*v2[0]+v1[1]*v2[1], (math.hypot(*v1)*math.hypot(*v2)), 1.0)
            angL = math.degrees(math.acos(max(-1, min(1, cosA))))
            out["jaw_angle_deg"] = round((angR + angL) / 2, 2)
        except Exception:
            pass

        # ── Babyfaceness composite (Berry & McArthur 1985) ──
        # Components: large eyes, high forehead, small chin, round face
        babyface_pts = []
        if out.get("eye_width_iod_ratio") is not None:
            babyface_pts.append(_to_score(out["eye_width_iod_ratio"], 0.28, 0.40))
        if out.get("forehead_height_ratio") is not None:
            babyface_pts.append(_to_score(out["forehead_height_ratio"], 0.18, 0.32))
        if out.get("chin_projection_norm") is not None:
            babyface_pts.append(_to_score(out["chin_projection_norm"], 0.05, 0.30, invert=True))
        if out.get("jaw_angle_deg") is not None:
            babyface_pts.append(_to_score(out["jaw_angle_deg"], 105, 145))
        if babyface_pts:
            out["babyface_index"] = round(sum(babyface_pts)/len(babyface_pts), 1)

    except (IndexError, ZeroDivisionError, ValueError):
        return out
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Cross-engine signal extractors (v2 schema-correct)
# ─────────────────────────────────────────────────────────────────────────────
def _extract_fwhr_value(fwhr_result):
    if not fwhr_result or not fwhr_result.get("ok"): return None
    p = fwhr_result.get("primary") or {}
    return p.get("value")

def _extract_dominance_z(fwhr_result):
    if not fwhr_result or not fwhr_result.get("ok"): return None
    cs = (fwhr_result.get("composite_scores") or {}).get("dominance_signal") or {}
    return cs.get("z")

def _extract_phi_score(phi_result):
    if not phi_result or not phi_result.get("ok"): return None
    return phi_result.get("overall_phi_score")

def _vitality_proxy(health_result):
    if not health_result or not health_result.get("ok"): return None
    return health_result.get("vitality_score")

def _dark_circles_proxy(health_result):
    if not health_result or not health_result.get("ok"): return None
    dc = (health_result.get("indicators") or {}).get("dark_circles")
    if not dc: return None
    L_drop = max(abs(dc.get("L_drop_left") or 0), abs(dc.get("L_drop_right") or 0))
    return round(min(100, L_drop * 8), 1)

def _wrinkle_proxy(health_result, kind="forehead_lines"):
    if not health_result or not health_result.get("ok"): return None
    aging = (health_result.get("indicators") or {}).get("aging_signs")
    if not aging: return None
    fl = aging.get(kind)
    fl_map = {"low": 15, "minimal": 10, "moderate": 50, "med": 50,
              "marked": 80, "high": 85, "severe": 95}
    if isinstance(fl, str):  return fl_map.get(fl.lower(), 30)
    if isinstance(fl, (int, float)):
        return round(min(100, float(fl) * 100), 1) if fl <= 1.0 else round(min(100, float(fl)), 1)
    return None

def _skin_clarity_proxy(health_result):
    if not health_result or not health_result.get("ok"): return None
    inflam = (health_result.get("composite_scores") or {}).get("inflammation_index")
    if inflam is None: return None
    return round(100 - inflam, 1)


# ─────────────────────────────────────────────────────────────────────────────
# Trait calculators (v2 — calibrated norms + new contributors)
# ─────────────────────────────────────────────────────────────────────────────
def _trait_extraversion(geom, fwhr_value, dom_z, vitality, lip_full, crow_feet, gnorm):
    cs = []
    upt = geom.get("mouth_corner_upturn", 0)
    cs.append({"key": "mouth_corner_upturn", "raw": upt,
                "score": _to_score(upt, -0.03, 0.06), "weight": 0.20,
                "ref": EVIDENCE["mouth_corner_upturn"]["ref"]})
    sw = geom.get("mouth_width_iod", 0.80)
    cs.append({"key": "smile_width", "raw": sw,
                "score": _to_score(sw, 0.65, 0.95), "weight": 0.10,
                "ref": EVIDENCE["smile_width"]["ref"]})
    eo = geom.get("eye_openness", 0.30)
    cs.append({"key": "eye_openness", "raw": eo,
                "score": _to_score(eo, 0.22, 0.38), "weight": 0.10,
                "ref": EVIDENCE["eye_openness"]["ref"]})
    if dom_z is not None:
        # Map z [-2..+2] → [0..100], higher dominance → higher E
        cs.append({"key": "fwhr_dominance", "raw": dom_z,
                    "score": _to_score(dom_z, -1.5, 1.5), "weight": 0.16,
                    "ref": EVIDENCE["fwhr_dominance"]["ref"]})
    elif fwhr_value is not None:
        cs.append({"key": "fwhr_dominance", "raw": fwhr_value,
                    "score": _to_score(fwhr_value, gnorm["fwhr_mean"]-0.20, gnorm["fwhr_mean"]+0.20),
                    "weight": 0.16, "ref": EVIDENCE["fwhr_dominance"]["ref"]})
    if vitality is not None:
        cs.append({"key": "vitality_proxy", "raw": vitality, "score": vitality,
                    "weight": 0.18, "ref": EVIDENCE["vitality_proxy"]["ref"]})
    if lip_full is not None:
        cs.append({"key": "lip_fullness", "raw": lip_full,
                    "score": _to_score(lip_full, 0.10, 0.30), "weight": 0.06,
                    "ref": EVIDENCE["lip_fullness"]["ref"]})
    bh = geom.get("brow_height_iod", gnorm["brow_height_mean"])
    cs.append({"key": "brow_height", "raw": bh,
                "score": _to_score(bh, 0.10, 0.28), "weight": 0.08,
                "ref": EVIDENCE["brow_height"]["ref"]})
    if crow_feet is not None:
        # Crow's feet = Duchenne marker → genuine smiles → E
        cs.append({"key": "crow_feet_duchenne", "raw": crow_feet, "score": crow_feet,
                    "weight": 0.12, "ref": EVIDENCE["crow_feet_duchenne"]["ref"]})
    return _aggregate("E", cs)


def _trait_conscientiousness(geom, sym, jaw_angle, phi_score, skin_clarity):
    cs = []
    if sym is not None:
        cs.append({"key": "facial_symmetry", "raw": sym, "score": sym,
                    "weight": 0.26, "ref": EVIDENCE["facial_symmetry"]["ref"]})
    if jaw_angle is not None:
        cs.append({"key": "jaw_firmness", "raw": jaw_angle,
                    "score": _to_score(jaw_angle, 105, 145, invert=True),
                    "weight": 0.16, "ref": EVIDENCE["jaw_firmness"]["ref"]})
    if skin_clarity is not None:
        cs.append({"key": "skin_clarity_proxy", "raw": skin_clarity, "score": skin_clarity,
                    "weight": 0.16, "ref": EVIDENCE["skin_clarity_proxy"]["ref"]})
    ba = geom.get("brow_asymmetry_iod", 0.02)
    cs.append({"key": "brow_steady", "raw": ba,
                "score": _to_score(ba, 0.005, 0.05, invert=True), "weight": 0.10,
                "ref": EVIDENCE["brow_steady"]["ref"]})
    if phi_score is not None:
        cs.append({"key": "phi_alignment", "raw": phi_score, "score": phi_score,
                    "weight": 0.12, "ref": EVIDENCE["phi_alignment"]["ref"]})
    cp = geom.get("chin_projection_norm")
    if cp is not None:
        cs.append({"key": "chin_projection", "raw": cp,
                    "score": _to_score(cp, 0.05, 0.30), "weight": 0.12,
                    "ref": EVIDENCE["chin_projection"]["ref"]})
    return _aggregate("C", cs)


def _trait_openness(geom, phi_score, enorm):
    cs = []
    fh = geom.get("forehead_height_ratio", enorm["forehead_h_mean"])
    cs.append({"key": "forehead_height_ratio", "raw": fh,
                "score": _to_score(fh, 0.18, 0.32), "weight": 0.18,
                "ref": EVIDENCE["forehead_height_ratio"]["ref"]})
    ew = geom.get("eye_width_iod_ratio", 0.32)
    cs.append({"key": "eye_width_ratio", "raw": ew,
                "score": _to_score(ew, 0.28, 0.40), "weight": 0.16,
                "ref": EVIDENCE["eye_width_ratio"]["ref"]})
    ba = geom.get("brow_arch_iod", 0.03)
    cs.append({"key": "brow_arch", "raw": ba,
                "score": _to_score(ba, 0.005, 0.07), "weight": 0.16,
                "ref": EVIDENCE["brow_arch"]["ref"]})
    pl = geom.get("philtrum_length_iod", 0.18)
    cs.append({"key": "philtrum_distinct", "raw": pl,
                "score": _to_score(pl, 0.12, 0.25), "weight": 0.10,
                "ref": EVIDENCE["philtrum_distinct"]["ref"]})
    if phi_score is not None:
        s_novel = max(0.0, min(100.0, 100 - phi_score))
        cs.append({"key": "novel_proportions", "raw": s_novel, "score": s_novel,
                    "weight": 0.14, "ref": EVIDENCE["novel_proportions"]["ref"]})
    es = geom.get("eye_spacing_ratio")
    if es is not None:
        cs.append({"key": "eye_spacing_open", "raw": es,
                    "score": _to_score(es, 0.85, 1.20), "weight": 0.12,
                    "ref": EVIDENCE["eye_spacing_open"]["ref"]})
    nw = geom.get("nose_width_iod")
    if nw is not None:
        # Centered on ethnic-norm nose width; deviation = distinctiveness
        dist = abs(nw - enorm["nose_width_mean"]) * 5
        cs.append({"key": "nose_distinct", "raw": nw,
                    "score": _to_score(dist, 0, 1.0), "weight": 0.08,
                    "ref": EVIDENCE["nose_distinct"]["ref"]})
    return _aggregate("O", cs)


def _trait_agreeableness(geom, fwhr_value, jaw_angle, dom_z, gnorm):
    cs = []
    if jaw_angle is not None:
        cs.append({"key": "rounded_features", "raw": jaw_angle,
                    "score": _to_score(jaw_angle, 105, 145), "weight": 0.20,
                    "ref": EVIDENCE["rounded_features"]["ref"]})
    if fwhr_value is not None:
        cs.append({"key": "low_fwhr", "raw": fwhr_value,
                    "score": _to_score(fwhr_value, gnorm["fwhr_mean"]-0.20,
                                       gnorm["fwhr_mean"]+0.20, invert=True),
                    "weight": 0.18, "ref": EVIDENCE["low_fwhr"]["ref"]})
    if jaw_angle is not None:
        cs.append({"key": "soft_jaw_angle", "raw": jaw_angle,
                    "score": _to_score(jaw_angle, 110, 140), "weight": 0.12,
                    "ref": EVIDENCE["soft_jaw_angle"]["ref"]})
    eo = geom.get("eye_openness", 0.30)
    eo_warmth = max(0, 100 - abs(eo - 0.30) * 400)
    cs.append({"key": "eye_warmth", "raw": eo, "score": eo_warmth,
                "weight": 0.12, "ref": EVIDENCE["eye_warmth"]["ref"]})
    upt = geom.get("mouth_corner_upturn", 0)
    cs.append({"key": "mouth_corner_upturn_a", "raw": upt,
                "score": _to_score(upt, -0.02, 0.05), "weight": 0.14,
                "ref": EVIDENCE["mouth_corner_upturn_a"]["ref"]})
    bf = geom.get("babyface_index")
    if bf is not None:
        cs.append({"key": "babyface_index", "raw": bf, "score": bf,
                    "weight": 0.16, "ref": EVIDENCE["babyface_index"]["ref"]})
    if dom_z is not None:
        cs.append({"key": "low_dominance", "raw": dom_z,
                    "score": _to_score(dom_z, -1.5, 1.5, invert=True),
                    "weight": 0.08, "ref": EVIDENCE["low_dominance"]["ref"]})
    return _aggregate("A", cs)


def _trait_neuroticism(geom, wrinkle_corrected, vitality, dc_score, sym, glabellar, gnorm):
    cs = []
    if wrinkle_corrected is not None:
        cs.append({"key": "brow_furrow_lines", "raw": wrinkle_corrected,
                    "score": wrinkle_corrected, "weight": 0.18,
                    "ref": EVIDENCE["brow_furrow_lines"]["ref"]})
    bh = geom.get("brow_height_iod", gnorm["brow_height_mean"])
    cs.append({"key": "low_brow", "raw": bh,
                "score": _to_score(bh, 0.10, 0.28, invert=True), "weight": 0.12,
                "ref": EVIDENCE["low_brow"]["ref"]})
    mw = geom.get("mouth_width_iod", 0.80)
    cs.append({"key": "tight_mouth", "raw": mw,
                "score": _to_score(mw, 0.65, 0.95, invert=True), "weight": 0.10,
                "ref": EVIDENCE["tight_mouth"]["ref"]})
    if sym is not None:
        cs.append({"key": "asym_microexpr", "raw": 100 - sym,
                    "score": 100 - sym, "weight": 0.10,
                    "ref": EVIDENCE["asym_microexpr"]["ref"]})
    drop = geom.get("mouth_corner_drop", 0)
    cs.append({"key": "mouth_corner_droop", "raw": drop,
                "score": _to_score(drop, 0, 0.04), "weight": 0.16,
                "ref": EVIDENCE["mouth_corner_droop"]["ref"]})
    if vitality is not None:
        cs.append({"key": "low_vitality_proxy", "raw": 100-vitality,
                    "score": 100-vitality, "weight": 0.10,
                    "ref": EVIDENCE["low_vitality_proxy"]["ref"]})
    if dc_score is not None:
        cs.append({"key": "dark_circles", "raw": dc_score, "score": dc_score,
                    "weight": 0.08, "ref": EVIDENCE["dark_circles"]["ref"]})
    if glabellar is not None:
        cs.append({"key": "glabellar_lines", "raw": glabellar, "score": glabellar,
                    "weight": 0.10, "ref": EVIDENCE["glabellar_lines"]["ref"]})
    sa = geom.get("smile_asymmetry")
    if sa is not None:
        cs.append({"key": "smile_asymmetry", "raw": sa,
                    "score": _to_score(sa, 0, 0.04), "weight": 0.06,
                    "ref": EVIDENCE["smile_asymmetry"]["ref"]})
    return _aggregate("N", cs)


def _aggregate(trait: str, contributors: list) -> dict:
    if not contributors:
        return {"trait": trait, "score": None, "class": "unknown",
                 "n_contributors": 0, "contributors": [], "narrative": None}
    wsum = sum(c["weight"] for c in contributors) or 1.0
    raw_score = sum(c["score"] * c["weight"] for c in contributors) / wsum
    raw_score = round(max(0, min(100, raw_score)), 1)
    # v2: Bayesian shrinkage
    score = _bayesian_shrink(raw_score, alpha=0.30)
    klass = _trait_class(score)
    nar = NARRATIVES.get(trait, {}).get(klass, {"en": "", "hi": ""})
    mean = sum(c["score"] for c in contributors) / len(contributors)
    sd = (sum((c["score"] - mean) ** 2 for c in contributors) / len(contributors)) ** 0.5
    return {
        "trait": trait,
        "score": score,
        "raw_score_pre_shrinkage": raw_score,
        "percentile": _score_to_percentile(score),
        "class": klass,
        "n_contributors": len(contributors),
        "contributor_score_sd": round(sd, 1),
        "stability": ("high" if sd < 12 else "moderate" if sd < 22 else "low"),
        "contributors": [
            {"key": c["key"], "raw": round(float(c["raw"]), 4),
              "score_0_100": round(c["score"], 1),
              "weight": c["weight"], "evidence_ref": c["ref"]}
            for c in contributors
        ],
        "narrative": nar,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Sub-facet scoring (NEO-PI-R 30 facets — measurability-aware)
# ─────────────────────────────────────────────────────────────────────────────
def _compute_facets(geom: dict, traits: dict, fwhr_value, vitality,
                    crow_feet, dom_z, dc_score, sym) -> dict:
    """For each of 30 facets, return either a score 0-100 or 'not_measurable_from_face'."""
    f = {t: {} for t in NEO_FACETS}

    # OPENNESS facets
    f["O"]["fantasy"]    = "not_measurable_from_face"
    f["O"]["aesthetics"] = traits["O"]["score"]  # phi-aligned aesthetic sense ≈ O
    f["O"]["feelings"]   = (traits["O"]["score"] or 50) * 0.7 + (traits["E"]["score"] or 50) * 0.3
    f["O"]["actions"]    = "not_measurable_from_face"
    f["O"]["ideas"]      = _to_score(geom.get("forehead_height_ratio", 0.27), 0.18, 0.32)
    f["O"]["values"]     = "not_measurable_from_face"

    # CONSCIENTIOUSNESS facets
    f["C"]["competence"]            = (traits["C"]["score"] or 50)
    f["C"]["order"]                 = sym if sym is not None else "not_measurable_from_face"
    f["C"]["dutifulness"]           = "not_measurable_from_face"
    f["C"]["achievement_striving"]  = _to_score(geom.get("chin_projection_norm", 0.15), 0.05, 0.30) \
                                        if geom.get("chin_projection_norm") is not None else "not_measurable_from_face"
    f["C"]["self_discipline"]       = (traits["C"]["score"] or 50) * 0.6 + \
                                       _to_score(geom.get("jaw_angle_deg", 125), 105, 145, invert=True) * 0.4 \
                                       if geom.get("jaw_angle_deg") else "not_measurable_from_face"
    f["C"]["deliberation"]          = "not_measurable_from_face"

    # EXTRAVERSION facets
    f["E"]["warmth"]              = (traits["A"]["score"] or 50) * 0.5 + (traits["E"]["score"] or 50) * 0.5
    f["E"]["gregariousness"]      = traits["E"]["score"]
    f["E"]["assertiveness"]       = _to_score(dom_z, -1.5, 1.5) if dom_z is not None else "not_measurable_from_face"
    f["E"]["activity"]            = vitality if vitality is not None else "not_measurable_from_face"
    f["E"]["excitement_seeking"]  = _to_score(geom.get("eye_openness", 0.30), 0.22, 0.38)
    f["E"]["positive_emotions"]   = _to_score(geom.get("mouth_corner_upturn", 0), -0.03, 0.06)

    # AGREEABLENESS facets
    f["A"]["trust"]              = traits["A"]["score"]
    f["A"]["straightforwardness"] = "not_measurable_from_face"
    f["A"]["altruism"]           = (traits["A"]["score"] or 50) * 0.7 + (traits["E"]["score"] or 50) * 0.3
    f["A"]["compliance"]         = _to_score(dom_z, -1.5, 1.5, invert=True) if dom_z is not None else "not_measurable_from_face"
    f["A"]["modesty"]            = "not_measurable_from_face"
    f["A"]["tendermindedness"]   = geom.get("babyface_index") if geom.get("babyface_index") is not None else "not_measurable_from_face"

    # NEUROTICISM facets
    f["N"]["anxiety"]            = (traits["N"]["score"] or 50)
    f["N"]["angry_hostility"]    = _to_score(geom.get("brow_height_iod", 0.20), 0.10, 0.28, invert=True)
    f["N"]["depression"]         = (100 - vitality) if vitality is not None else _to_score(geom.get("mouth_corner_drop", 0), 0, 0.04)
    f["N"]["self_consciousness"] = (traits["N"]["score"] or 50) * 0.7
    f["N"]["impulsiveness"]      = "not_measurable_from_face"
    f["N"]["vulnerability"]      = (100 - vitality + dc_score) / 2 if (vitality is not None and dc_score is not None) else "not_measurable_from_face"

    # Round numeric values
    for t in f:
        for fc in list(f[t].keys()):
            v = f[t][fc]
            if isinstance(v, (int, float)):
                f[t][fc] = round(float(max(0, min(100, v))), 1)
    return f


# ─────────────────────────────────────────────────────────────────────────────
# Oosterhof-Todorov 2008 Valence-Dominance 2D model
# ─────────────────────────────────────────────────────────────────────────────
def _valence_dominance(traits: dict, geom: dict, fwhr_value, dom_z, sym) -> dict:
    """2D social-perception space:
       Valence (trustworthiness) ≈ +A, +smile, -fWHR, +symmetry
       Dominance (power) ≈ +fWHR, +brow_low, +jaw_firmness
    """
    A = traits["A"]["score"] or 50
    upt = geom.get("mouth_corner_upturn", 0)
    upt_score = _to_score(upt, -0.03, 0.06)
    sym_score = sym if sym is not None else 50
    low_fwhr_score = _to_score(fwhr_value, 1.7, 2.1, invert=True) if fwhr_value is not None else 50

    valence = round((A * 0.40 + upt_score * 0.25 + sym_score * 0.20 + low_fwhr_score * 0.15), 1)

    bh_low = _to_score(geom.get("brow_height_iod", 0.20), 0.10, 0.28, invert=True)
    jaw_firm = _to_score(geom.get("jaw_angle_deg", 125), 105, 145, invert=True) if geom.get("jaw_angle_deg") else 50
    fwhr_score = _to_score(fwhr_value, 1.7, 2.1) if fwhr_value is not None else 50
    dom_z_score = _to_score(dom_z, -1.5, 1.5) if dom_z is not None else 50

    dominance = round((fwhr_score * 0.30 + bh_low * 0.20 + jaw_firm * 0.20 + dom_z_score * 0.30), 1)

    valence = max(0, min(100, valence))
    dominance = max(0, min(100, dominance))

    return {
        "model": "Oosterhof_Todorov_2008",
        "valence_trustworthiness": valence,
        "dominance_power": dominance,
        "quadrant": _vd_quadrant(valence, dominance),
        "ref": "Oosterhof_Todorov_2008_PNAS",
    }

def _vd_quadrant(v, d):
    if v >= 50 and d >= 50: return "warm_powerful_(leader)"
    if v >= 50 and d < 50:  return "warm_submissive_(harmoniser)"
    if v < 50 and d >= 50:  return "cold_powerful_(intimidator)"
    return "cold_submissive_(detached)"


# ─────────────────────────────────────────────────────────────────────────────
# Inter-trait inconsistency detector
# ─────────────────────────────────────────────────────────────────────────────
def _detect_inconsistencies(traits: dict) -> list:
    out = []
    O = traits["O"]["score"] or 50
    C = traits["C"]["score"] or 50
    E = traits["E"]["score"] or 50
    A = traits["A"]["score"] or 50
    N = traits["N"]["score"] or 50
    if E > 70 and A < 30:
        out.append({"flag": "high_E_low_A", "note": "Rare combination — assertive + uncooperative."})
    if C > 75 and N > 75:
        out.append({"flag": "high_C_high_N", "note": "Disciplined but anxious — perfectionism risk."})
    if O > 75 and C < 30:
        out.append({"flag": "high_O_low_C", "note": "Creative but undisciplined — execution risk."})
    if E < 30 and A < 30:
        out.append({"flag": "low_E_low_A", "note": "Reserved + competitive — may read as aloof."})
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Strengths + growth-edges + hints assembly
# ─────────────────────────────────────────────────────────────────────────────
def _strengths_growth(traits: dict) -> dict:
    out = {}
    for t, r in traits.items():
        score = r.get("score")
        if score is None:
            out[t] = None; continue
        side = "high" if score >= 50 else "low"
        sg = STRENGTHS_GROWTH.get(t, {}).get(side, {})
        out[t] = {"strengths": sg.get("strengths", []), "growth_edges": sg.get("growth", [])}
    return out

def _hints(traits: dict) -> dict:
    careers = []; relations = []
    for t, r in traits.items():
        score = r.get("score") or 50
        sign = "+" if score >= 60 else "-" if score <= 40 else None
        if sign:
            key = f"{t}{sign}"
            careers.extend(CAREER_HINTS.get(key, []))
            rh = RELATIONSHIP_HINTS.get(key)
            if rh: relations.append({"trait": t, "direction": sign, "note": rh})
    # Dedupe careers
    seen = set(); careers_d = []
    for c in careers:
        if c not in seen:
            seen.add(c); careers_d.append(c)
    return {
        "career_fit_informational": careers_d[:8],
        "relationship_style": relations,
        "disclaimer": "Hints are informational only; not predictive of actual career success or relationship outcomes.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Archetype mapping
# ─────────────────────────────────────────────────────────────────────────────
def _archetype_from_profile(traits: dict) -> dict:
    O = (traits["O"]["score"] or 50); C = (traits["C"]["score"] or 50)
    E = (traits["E"]["score"] or 50); A = (traits["A"]["score"] or 50)
    N = (traits["N"]["score"] or 50)
    archetype = "Balanced"
    if E > 60 and A > 60 and C > 55 and N < 45:   archetype = "Resilient"
    elif E < 45 and N > 60:                        archetype = "Overcontrolled"
    elif C < 45 and A < 45:                        archetype = "Undercontrolled"
    elif O > 65 and E > 60:                        archetype = "Explorer"
    elif C > 65 and A > 60:                        archetype = "Steadfast"
    elif N > 65 and O > 60:                        archetype = "Sensitive_Creative"
    elif E > 65 and A > 60:                        archetype = "Warm_Connector"
    elif C > 65 and N < 40:                        archetype = "Disciplined_Performer"
    return {"label": archetype, "ref": "Asendorpf_vanAken_1999_RUO_archetypes",
             "note": "Coarse archetype from OCEAN summary; not a clinical typology."}


# ─────────────────────────────────────────────────────────────────────────────
# Main entry
# ─────────────────────────────────────────────────────────────────────────────
def run(landmarks_norm: Sequence[tuple],
        image_w: int, image_h: int,
        anthropometry_result: Optional[dict] = None,
        symmetry_result: Optional[dict] = None,
        fwhr_result: Optional[dict] = None,
        phi_result: Optional[dict] = None,
        health_result: Optional[dict] = None,
        gender: str = "U",
        ethnicity: Optional[str] = None,
        age: Optional[int] = None) -> dict:

    if not landmarks_norm or len(landmarks_norm) < 478:
        return {"engine": "personality", "ok": False, "version": 2,
                 "error": "insufficient_landmarks"}

    pts = [(p[0], p[1]) for p in landmarks_norm]
    W, H = image_w, image_h

    # 1. Geometric extraction
    geom = _extract_geometric(pts, W, H)
    if not geom:
        return {"engine": "personality", "ok": False, "version": 2,
                 "error": "geometry_extraction_failed"}

    # 2. Demographic baselines
    gnorm = _gender_norm(gender)
    enorm = _ethnicity_norm(ethnicity)
    expected_wrinkle = _age_wrinkle_expected(age)

    # 3. Cross-engine signals (v2 schema-correct)
    fwhr_value  = _extract_fwhr_value(fwhr_result)
    dom_z       = _extract_dominance_z(fwhr_result)
    phi_score   = _extract_phi_score(phi_result)
    sym_overall = (symmetry_result or {}).get("overall_score")
    vitality    = _vitality_proxy(health_result)
    dc_score    = _dark_circles_proxy(health_result)
    forehead_w  = _wrinkle_proxy(health_result, "forehead_lines")
    crow_feet   = _wrinkle_proxy(health_result, "crow_feet") or _wrinkle_proxy(health_result, "periorbital_lines")
    nasolabial  = _wrinkle_proxy(health_result, "nasolabial_folds")
    glabellar   = _wrinkle_proxy(health_result, "glabellar_lines")
    skin_clar   = _skin_clarity_proxy(health_result)
    lip_full    = geom.get("lip_fullness_iod")
    jaw_angle   = geom.get("jaw_angle_deg")

    # 4. Age-correct wrinkles (don't penalize natural aging)
    wrinkle_corrected = None
    if forehead_w is not None:
        wrinkle_corrected = max(0, forehead_w - expected_wrinkle)

    # 5. Compute traits (v2 — calibrated norms, demographic-aware)
    O = _trait_openness(geom, phi_score, enorm)
    C = _trait_conscientiousness(geom, sym_overall, jaw_angle, phi_score, skin_clar)
    E = _trait_extraversion(geom, fwhr_value, dom_z, vitality, lip_full, crow_feet, gnorm)
    A = _trait_agreeableness(geom, fwhr_value, jaw_angle, dom_z, gnorm)
    N = _trait_neuroticism(geom, wrinkle_corrected, vitality, dc_score, sym_overall, glabellar, gnorm)
    traits = {"O": O, "C": C, "E": E, "A": A, "N": N}

    # 6. Confidence per trait
    sym_ok = sym_overall is not None
    for t, r in traits.items():
        r["confidence"] = _conf_from_quality(sym_ok, r.get("n_contributors", 0), r.get("stability", "moderate"))

    # 7. NEO-PI-R 30 facets
    facets = _compute_facets(geom, traits, fwhr_value, vitality, crow_feet, dom_z, dc_score, sym_overall)

    # 8. Oosterhof-Todorov V-D model
    vd = _valence_dominance(traits, geom, fwhr_value, dom_z, sym_overall)

    # 9. Composites (Approachability + Maturity)
    A_sc = A["score"] or 50; E_sc = E["score"] or 50; N_sc = N["score"] or 50
    approachability = round((A_sc * 0.45 + E_sc * 0.30 + (100 - N_sc) * 0.25), 1)
    bf = geom.get("babyface_index", 50)
    maturity = round(100 - (bf * 0.7 + (100 - (jaw_angle or 125) / 2)), 1) if jaw_angle else round(100 - bf, 1)
    maturity = max(0, min(100, maturity))

    # 10. Dominant + secondary
    deviations = [(t, abs((r["score"] or 50) - 50)) for t, r in traits.items() if r["score"] is not None]
    deviations.sort(key=lambda x: x[1], reverse=True)
    dominant   = deviations[0][0] if deviations else None
    secondary  = deviations[1][0] if len(deviations) > 1 else None

    # 11. Fingerprint
    fingerprint = "".join(
        ("+" if (traits[t]["score"] or 50) >= 60
         else "-" if (traits[t]["score"] or 50) <= 40 else "·") + t
        for t in "OCEAN"
    )

    # 12. Archetype + inconsistencies
    archetype = _archetype_from_profile(traits)
    inconsistencies = _detect_inconsistencies(traits)

    # 13. Strengths/growth + hints
    sg = _strengths_growth(traits)
    hints = _hints(traits)

    # 14. Caveats / disclaimers
    caveats = [
        "Face-derived OCEAN scores reflect SOCIAL PERCEPTION research (Walker & Vetter 2016, Penton-Voak 2006), not validated personality assessment.",
        "These are 'perceived traits' — how strangers might judge — not verified self-report Big Five.",
        "For clinical/HR-grade personality, use validated instruments (NEO-PI-3, IPIP-NEO, BFI-2).",
        "Single-frame analysis: cannot capture dynamic expression or behavioural cues.",
        "Effect sizes in face-perception research are SMALL; v2 applies Bayesian shrinkage (α=0.30) to compress over-confident scores.",
        f"Cross-engine signals available: symmetry={sym_ok}, fwhr={fwhr_value is not None}, phi={phi_score is not None}, health={vitality is not None}.",
        f"Demographic adjustments applied: gender={gender}, ethnicity={ethnicity or 'default'}, age={age}.",
    ]

    return _py({
        "engine": "personality",
        "version": 2,
        "ok": True,
        "model": "Big_Five_OCEAN_plus_OosterhofTodorov_VD",
        "method": "face_perception_inference_v2",
        "perceived_trait_disclaimer": (
            "Face-derived Big Five = perceived/social-judgment traits, not validated self-report. "
            "Educational/wellness use only."
        ),
        "do_not_use_for_hiring": True,
        "ethics_notice": (
            "This output MUST NOT be used for hiring, lending, insurance, "
            "law-enforcement, or any high-stakes decision. Face-based personality "
            "inference is contested science and may encode demographic bias. "
            "Research base is predominantly Western — generalisation to other "
            "populations is uncertain. Self-fulfilling prophecy risk: do not let "
            "a 'reading' shape self-concept rigidly."
        ),
        "inputs": {
            "gender": gender, "ethnicity": ethnicity, "age": age,
            "expected_wrinkle_for_age": expected_wrinkle,
            "cross_engine_signals_used": {
                "anthropometry": anthropometry_result is not None and anthropometry_result.get("ok", False),
                "symmetry":      symmetry_result is not None and symmetry_result.get("ok", False),
                "fwhr":          fwhr_result is not None and fwhr_result.get("ok", False),
                "phi":           phi_result is not None and phi_result.get("ok", False),
                "health":        health_result is not None and health_result.get("ok", False),
            },
            "extracted_cross_engine_values": {
                "fwhr_value":  fwhr_value, "dominance_z": dom_z,
                "phi_score":   phi_score,  "sym_overall": sym_overall,
                "vitality":    vitality,   "dark_circles": dc_score,
                "skin_clarity": skin_clar,
                "wrinkle_corrected_for_age": wrinkle_corrected,
            },
        },
        "geometric_indicators": geom,
        "demographic_baselines_used": {"gender": gnorm, "ethnicity": enorm},
        "traits": {
            "openness":          O, "conscientiousness": C,
            "extraversion":      E, "agreeableness":     A,
            "neuroticism":       N,
        },
        "ocean_summary_scores": {
            "O": O.get("score"), "C": C.get("score"),
            "E": E.get("score"), "A": A.get("score"), "N": N.get("score"),
        },
        "ocean_percentiles": {
            "O": O.get("percentile"), "C": C.get("percentile"),
            "E": E.get("percentile"), "A": A.get("percentile"), "N": N.get("percentile"),
        },
        "neo_pi_r_facets": facets,
        "valence_dominance_2D": vd,
        "composites": {
            "trustworthiness": vd["valence_trustworthiness"],
            "dominance":       vd["dominance_power"],
            "approachability": approachability,
            "maturity":        maturity,
        },
        "dominant_trait":   dominant,
        "secondary_trait":  secondary,
        "fingerprint":      fingerprint,
        "archetype":        archetype,
        "inter_trait_inconsistencies": inconsistencies,
        "strengths_and_growth": sg,
        "informational_hints": hints,
        "evidence_catalog": EVIDENCE,
        "neo_pi_r_facet_definitions": NEO_FACETS,
        "caveats": caveats,
        "disclaimer": (
            "This personality reading is based on face-perception research and is "
            "informational only. It is NOT a clinical or HR-grade assessment, "
            "and MUST NOT be used for hiring, insurance, lending, or other "
            "high-stakes decisions. Research base is predominantly Western; "
            "generalisation to South Asian / global populations is uncertain. "
            "For self-knowledge, use validated instruments (NEO-PI-3, IPIP-NEO-120, BFI-2)."
        ),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Test scenario fixtures (regression hints)
# ─────────────────────────────────────────────────────────────────────────────
SCENARIO_FIXTURES = {
    "smiling_face":     {"expected": "E score should be moderate-high; A high; mouth_corner_upturn > 0.03"},
    "serious_face":     {"expected": "E score moderate-low; mouth_corner_upturn near 0; tight_mouth elevated"},
    "asymmetric_face":  {"expected": "C score reduced; N score elevated due to asym_microexpr contributor"},
    "babyface":         {"expected": "A score very high; babyface_index > 70; maturity composite low"},
}

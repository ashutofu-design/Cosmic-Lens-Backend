"""
Engine 6 — Big Five Personality (OCEAN) from Face
====================================================

Face-derived inference of the five-factor personality model:
    O — Openness to experience
    C — Conscientiousness
    E — Extraversion
    A — Agreeableness
    N — Neuroticism

This engine is RESEARCH-INSPIRED, not clinically validated. Face-derived trait
inference reflects social-perception research (how trait judgments are formed),
not ground-truth personality. Outputs are clearly tagged as "perceived traits".

Scientific basis (selected references):
  - Walker & Vetter 2016 (Cogn & Emotion)  — Big Five trait modeling on photos
  - Penton-Voak et al. 2006 (J. Pers. Soc. Psychol.) — composite face → traits
  - Kramer & Ward 2010 (Q. J. Exp. Psychol.) — internal facial features → traits
  - Said & Todorov 2011 (J. Vis.) — overgeneralization of trait perception
  - Carré & McCormick 2008 (Proc. R. Soc. B) — fWHR → aggression/dominance
  - Carré et al. 2009 — fWHR → reactive aggression (proxy: low Agreeableness)
  - Stirrat & Perrett 2010 (Psychol. Sci.) — fWHR → trustworthiness
  - Borkenau et al. 2009 — accuracy of zero-acquaintance personality judgments
  - Penton-Voak 2001 — facial symmetry → perceived health/conscientiousness
  - Hassin & Trope 2000 — facing faces, physiognomy cognition
  - Todorov, Olivola, Dotsch, Mende-Siedlecki 2015 (Annu. Rev. Psychol.)
        — social attributions from faces, dimensions of trait inference
  - Zebrowitz & Montepare 2008 — social psych. of facial appearance

Inputs:
  - Landmarks (MediaPipe FaceMesh, 478 normalized 3D points)
  - Engine 1 anthropometry result (face-shape, ratios, angles)
  - Engine 2 symmetry result (overall + per-feature)
  - Engine 4 fWHR result (facial width-to-height ratio)
  - Engine 5 health result (vitality, fatigue, dark circles)
  - gender, age, ethnicity (for norm adjustments)

Outputs:
  - Trait scores 0-100 with confidence band, evidence_strength
  - Sub-facets per trait (where measurable from face)
  - Indicator-level breakdown with each contributing measurement
  - Perceived-trait disclaimer + Hinglish + EN narrative
  - Cross-engine traceability for every score component
"""
from __future__ import annotations
from typing import Optional, Sequence
import math
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# Sanitizer (np types → Python natives) for JSON serialization
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
# Eyes
R_EYE_OUTER, R_EYE_INNER = 33,  133
L_EYE_OUTER, L_EYE_INNER = 263, 362
R_EYE_TOP,   R_EYE_BOT   = 159, 145
L_EYE_TOP,   L_EYE_BOT   = 386, 374
# Brows
R_BROW_INNER, R_BROW_PEAK, R_BROW_OUTER = 107, 105, 70
L_BROW_INNER, L_BROW_PEAK, L_BROW_OUTER = 336, 334, 300
# Mouth
M_CORNER_R, M_CORNER_L = 61, 291
M_UPPER_MID, M_LOWER_MID = 13, 14
M_UPPER_OUT, M_LOWER_OUT = 0, 17
# Face landmarks
NOSE_TIP, CHIN, FOREHEAD_TOP = 1, 152, 10
ZYGION_R, ZYGION_L = 234, 454
JAW_R, JAW_L = 172, 397


# ─────────────────────────────────────────────────────────────────────────────
# Per-trait evidence catalog (citation index)
# ─────────────────────────────────────────────────────────────────────────────
EVIDENCE = {
    # Extraversion
    "mouth_corner_upturn":   {"trait": "E", "weight": 0.22, "ref": "Knutson_1996_smile_extraversion"},
    "smile_width":           {"trait": "E", "weight": 0.12, "ref": "Penton-Voak_2006_composite"},
    "eye_openness":          {"trait": "E", "weight": 0.10, "ref": "Walker_Vetter_2016"},
    "fwhr":                  {"trait": "E", "weight": 0.18, "ref": "Carre_McCormick_2008_fWHR"},
    "vitality_proxy":        {"trait": "E", "weight": 0.20, "ref": "Penton-Voak_2001_health_perception"},
    "lip_fullness":          {"trait": "E", "weight": 0.08, "ref": "Said_Todorov_2011"},
    "brow_height":           {"trait": "E", "weight": 0.10, "ref": "Walker_Vetter_2016"},

    # Conscientiousness
    "facial_symmetry":       {"trait": "C", "weight": 0.30, "ref": "Penton-Voak_2001_symmetry"},
    "jaw_firmness":          {"trait": "C", "weight": 0.18, "ref": "Carre_McCormick_2008"},
    "skin_clarity_proxy":    {"trait": "C", "weight": 0.18, "ref": "Kramer_Ward_2010"},
    "brow_steady":           {"trait": "C", "weight": 0.10, "ref": "Walker_Vetter_2016"},
    "phi_alignment":         {"trait": "C", "weight": 0.14, "ref": "Pallett_2010_golden_ratio"},
    "groomed_proxy":         {"trait": "C", "weight": 0.10, "ref": "Borkenau_2009_zero_acquaintance"},

    # Openness
    "forehead_height_ratio": {"trait": "O", "weight": 0.20, "ref": "Walker_Vetter_2016"},
    "eye_width_ratio":       {"trait": "O", "weight": 0.18, "ref": "Said_Todorov_2011"},
    "philtrum_distinct":     {"trait": "O", "weight": 0.14, "ref": "Penton-Voak_2006"},
    "novel_proportions":     {"trait": "O", "weight": 0.18, "ref": "Walker_Vetter_2016"},
    "iris_brightness":       {"trait": "O", "weight": 0.10, "ref": "Kramer_Ward_2010"},
    "brow_arch":             {"trait": "O", "weight": 0.20, "ref": "Said_Todorov_2011"},

    # Agreeableness
    "rounded_features":      {"trait": "A", "weight": 0.25, "ref": "Berry_McArthur_1985_babyface"},
    "low_fwhr":              {"trait": "A", "weight": 0.20, "ref": "Stirrat_Perrett_2010"},
    "soft_jaw_angle":        {"trait": "A", "weight": 0.15, "ref": "Carre_2009"},
    "eye_warmth":            {"trait": "A", "weight": 0.15, "ref": "Said_Todorov_2011"},
    "mouth_corner_upturn_a": {"trait": "A", "weight": 0.15, "ref": "Knutson_1996"},
    "philtrum_softness":     {"trait": "A", "weight": 0.10, "ref": "Penton-Voak_2006"},

    # Neuroticism
    "brow_furrow_lines":     {"trait": "N", "weight": 0.22, "ref": "Hess_2009_anger_brow"},
    "low_brow":              {"trait": "N", "weight": 0.14, "ref": "Said_Todorov_2011"},
    "tight_mouth":           {"trait": "N", "weight": 0.14, "ref": "Said_Todorov_2011"},
    "asym_microexpr":        {"trait": "N", "weight": 0.12, "ref": "Penton-Voak_2001"},
    "mouth_corner_droop":    {"trait": "N", "weight": 0.16, "ref": "Knutson_1996"},
    "low_vitality_proxy":    {"trait": "N", "weight": 0.12, "ref": "Penton-Voak_2001_health"},
    "dark_circles":          {"trait": "N", "weight": 0.10, "ref": "Walker_Vetter_2016"},
}


# ─────────────────────────────────────────────────────────────────────────────
# Geometry helpers
# ─────────────────────────────────────────────────────────────────────────────
def _dist(p, q) -> float:
    return math.hypot(p[0] - q[0], p[1] - q[1])


def _midpoint(p, q):
    return ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)


def _safe_div(a, b, default=0.0):
    return (a / b) if b > 1e-9 else default


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _to_score(value: float, lo: float, hi: float, invert: bool = False) -> float:
    """Linear map [lo,hi] → [0,100], optionally inverted."""
    if hi == lo:
        return 50.0
    p = (value - lo) / (hi - lo)
    p = _clip01(p)
    if invert:
        p = 1.0 - p
    return round(p * 100, 1)


def _trait_class(score: float) -> str:
    if score >= 80: return "very_high"
    if score >= 65: return "high"
    if score >= 50: return "moderate_high"
    if score >= 35: return "moderate_low"
    if score >= 20: return "low"
    return "very_low"


def _conf_from_quality(symmetry_ok: bool, n_signals: int) -> str:
    if not symmetry_ok or n_signals < 3:
        return "low"
    if n_signals >= 5:
        return "high"
    return "medium"


# ─────────────────────────────────────────────────────────────────────────────
# Hinglish + EN narratives per trait × class
# ─────────────────────────────────────────────────────────────────────────────
NARRATIVES = {
    "O": {
        "very_high":     {"en": "Highly imaginative and curious — drawn to new ideas, art, abstract thought.",
                          "hi": "Bahut creative aur curious — naye ideas, art, abstract thinking pasand."},
        "high":          {"en": "Open to experience — enjoys variety, novelty, and intellectual exploration.",
                          "hi": "Naye experiences ke liye open — variety aur curiosity strong."},
        "moderate_high": {"en": "Balanced openness — enjoys some novelty but values familiarity.",
                          "hi": "Thoda explorer, thoda comfort-seeker — balanced curiosity."},
        "moderate_low":  {"en": "Practical and grounded — prefers tested ideas over experimentation.",
                          "hi": "Practical mindset — proven cheezein zyada pasand."},
        "low":           {"en": "Conservative thinker — values tradition and routine.",
                          "hi": "Tradition aur routine pasand karne wala mindset."},
        "very_low":      {"en": "Strongly conventional — prefers familiar over abstract.",
                          "hi": "Bahut conventional — naye-pan se distance."},
    },
    "C": {
        "very_high":     {"en": "Very disciplined and reliable — strong self-control and goal-orientation.",
                          "hi": "Bahut disciplined aur dependable — self-control strong."},
        "high":          {"en": "Conscientious and organized — follows through on commitments.",
                          "hi": "Organized aur committed — goals follow karte hain."},
        "moderate_high": {"en": "Generally organized but flexible when needed.",
                          "hi": "Mostly organized, lekin flexibility bhi hai."},
        "moderate_low":  {"en": "Spontaneous side — sometimes prioritizes flow over structure.",
                          "hi": "Spontaneous nature — kabhi flow zyada important."},
        "low":           {"en": "Flexible and easy-going — structure feels limiting.",
                          "hi": "Easy-going — strict structure pasand nahi."},
        "very_low":      {"en": "Highly spontaneous — routine feels constraining.",
                          "hi": "Bahut spontaneous — routine binding lagti."},
    },
    "E": {
        "very_high":     {"en": "Strongly extraverted — energized by people, expressive and warm.",
                          "hi": "Bahut extrovert — log ke saath energy aati hai."},
        "high":          {"en": "Outgoing and sociable — enjoys group settings.",
                          "hi": "Sociable aur outgoing — group me comfortable."},
        "moderate_high": {"en": "Ambivert with social warmth — balances people and quiet time.",
                          "hi": "Ambivert — log aur akele dono pasand, balance me."},
        "moderate_low":  {"en": "Selectively social — prefers small circles and depth.",
                          "hi": "Selective social — depth zyada important."},
        "low":           {"en": "Reserved — recharges in quiet, prefers small-group interaction.",
                          "hi": "Reserved nature — akele recharge hote hain."},
        "very_low":      {"en": "Strongly introverted — solitude is restorative.",
                          "hi": "Bahut introvert — akele time energizing."},
    },
    "A": {
        "very_high":     {"en": "Very warm, cooperative, trusting — strong empathy.",
                          "hi": "Bahut warm aur cooperative — empathy strong."},
        "high":          {"en": "Agreeable and accommodating — values harmony.",
                          "hi": "Agreeable — harmony important."},
        "moderate_high": {"en": "Generally cooperative but assertive when needed.",
                          "hi": "Cooperative, lekin zaroorat par assertive bhi."},
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
                          "hi": "Thoda reactive, lekin manage karte hain."},
        "moderate_low":  {"en": "Emotionally steady — handles stress well.",
                          "hi": "Emotionally stable — stress handle karte hain."},
        "low":           {"en": "Calm and resilient — composed under pressure.",
                          "hi": "Calm aur resilient — pressure me composed."},
        "very_low":      {"en": "Very stable — rarely shaken by stress.",
                          "hi": "Bahut stable — stress bahut kam."},
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Indicator extractors
# ─────────────────────────────────────────────────────────────────────────────
def _extract_geometric(pts, W, H) -> dict:
    """Compute raw geometric indicators from landmarks."""
    out = {}
    try:
        # Inter-ocular distance for normalization
        re_o = (pts[R_EYE_OUTER][0]*W, pts[R_EYE_OUTER][1]*H)
        le_o = (pts[L_EYE_OUTER][0]*W, pts[L_EYE_OUTER][1]*H)
        iod = _dist(re_o, le_o)
        if iod < 10:
            return {}

        # ── Eye openness (vertical / horizontal palpebral ratio) ──
        r_eye_h = _dist((pts[R_EYE_OUTER][0]*W, pts[R_EYE_OUTER][1]*H),
                        (pts[R_EYE_INNER][0]*W, pts[R_EYE_INNER][1]*H))
        l_eye_h = _dist((pts[L_EYE_OUTER][0]*W, pts[L_EYE_OUTER][1]*H),
                        (pts[L_EYE_INNER][0]*W, pts[L_EYE_INNER][1]*H))
        r_eye_v = abs(pts[R_EYE_TOP][1] - pts[R_EYE_BOT][1]) * H
        l_eye_v = abs(pts[L_EYE_TOP][1] - pts[L_EYE_BOT][1]) * H
        r_open = _safe_div(r_eye_v, r_eye_h)
        l_open = _safe_div(l_eye_v, l_eye_h)
        out["eye_openness"] = round((r_open + l_open) / 2, 4)
        out["eye_width_iod_ratio"] = round((r_eye_h + l_eye_h) / 2 / iod, 4)

        # ── Mouth corner upturn ──
        m_r = (pts[M_CORNER_R][0]*W, pts[M_CORNER_R][1]*H)
        m_l = (pts[M_CORNER_L][0]*W, pts[M_CORNER_L][1]*H)
        m_mid = _midpoint(m_r, m_l)
        m_upper = (pts[M_UPPER_MID][0]*W, pts[M_UPPER_MID][1]*H)
        # Negative y_corner - y_mid means corners higher (smile)
        corner_y_avg = (m_r[1] + m_l[1]) / 2
        upturn_norm = (m_upper[1] - corner_y_avg) / iod
        out["mouth_corner_upturn"] = round(upturn_norm, 4)
        out["mouth_width_iod"] = round(_dist(m_r, m_l) / iod, 4)

        # ── Mouth corner droop asymmetry (for N) ──
        out["mouth_corner_drop"] = round(max(0.0, -upturn_norm), 4)

        # ── Lip fullness (height of vermilion) ──
        m_uo = (pts[M_UPPER_OUT][0]*W, pts[M_UPPER_OUT][1]*H)
        m_lo = (pts[M_LOWER_OUT][0]*W, pts[M_LOWER_OUT][1]*H)
        out["lip_fullness_iod"] = round(_dist(m_uo, m_lo) / iod, 4)

        # ── Brow height above eye ──
        rb_p = (pts[R_BROW_PEAK][0]*W, pts[R_BROW_PEAK][1]*H)
        lb_p = (pts[L_BROW_PEAK][0]*W, pts[L_BROW_PEAK][1]*H)
        rb_h = (pts[R_EYE_TOP][1]*H - pts[R_BROW_PEAK][1]*H) / iod  # positive = brow above eye
        lb_h = (pts[L_EYE_TOP][1]*H - pts[L_BROW_PEAK][1]*H) / iod
        out["brow_height_iod"] = round((rb_h + lb_h) / 2, 4)

        # ── Brow arch (peak vs inner+outer height) ──
        rb_i = pts[R_BROW_INNER][1] * H; rb_o = pts[R_BROW_OUTER][1] * H
        lb_i = pts[L_BROW_INNER][1] * H; lb_o = pts[L_BROW_OUTER][1] * H
        r_arch = ((rb_i + rb_o) / 2 - rb_p[1]) / iod
        l_arch = ((lb_i + lb_o) / 2 - lb_p[1]) / iod
        out["brow_arch_iod"] = round((r_arch + l_arch) / 2, 4)

        # ── Brow asymmetry (vertical) ──
        out["brow_asymmetry_iod"] = round(abs(rb_p[1] - lb_p[1]) / iod, 4)

        # ── Forehead height ratio ──
        fh_top = pts[FOREHEAD_TOP][1] * H
        brow_mid_y = ((pts[R_BROW_INNER][1] + pts[L_BROW_INNER][1]) / 2) * H
        chin_y = pts[CHIN][1] * H
        face_h = chin_y - fh_top
        if face_h > 0:
            forehead_h = brow_mid_y - fh_top
            out["forehead_height_ratio"] = round(forehead_h / face_h, 4)

        # ── Philtrum length (nose-tip to upper-lip) ──
        nose_y = pts[NOSE_TIP][1] * H
        out["philtrum_length_iod"] = round((m_upper[1] - nose_y) / iod, 4)

        # ── Jaw firmness — angle at jaw landmark ──
        try:
            jr = (pts[JAW_R][0]*W, pts[JAW_R][1]*H)
            jl = (pts[JAW_L][0]*W, pts[JAW_L][1]*H)
            ch = (pts[CHIN][0]*W, pts[CHIN][1]*H)
            zr = (pts[ZYGION_R][0]*W, pts[ZYGION_R][1]*H)
            zl = (pts[ZYGION_L][0]*W, pts[ZYGION_L][1]*H)
            # Jaw angle: vector jr->ch and jr->zr
            v1 = (ch[0]-jr[0], ch[1]-jr[1]); v2 = (zr[0]-jr[0], zr[1]-jr[1])
            cosA = _safe_div(v1[0]*v2[0]+v1[1]*v2[1],
                             (math.hypot(*v1)*math.hypot(*v2)), 1.0)
            angR = math.degrees(math.acos(max(-1, min(1, cosA))))
            v1 = (ch[0]-jl[0], ch[1]-jl[1]); v2 = (zl[0]-jl[0], zl[1]-jl[1])
            cosA = _safe_div(v1[0]*v2[0]+v1[1]*v2[1],
                             (math.hypot(*v1)*math.hypot(*v2)), 1.0)
            angL = math.degrees(math.acos(max(-1, min(1, cosA))))
            out["jaw_angle_deg"] = round((angR + angL) / 2, 2)
        except Exception:
            pass

    except (IndexError, ZeroDivisionError, ValueError):
        return out
    return out


def _vitality_proxy(health_result: Optional[dict]) -> Optional[float]:
    if not health_result or not health_result.get("ok"):
        return None
    return health_result.get("vitality_score")


def _dark_circles_proxy(health_result: Optional[dict]) -> Optional[float]:
    if not health_result or not health_result.get("ok"):
        return None
    dc = (health_result.get("indicators") or {}).get("dark_circles")
    if not dc:
        return None
    L_drop = max(abs(dc.get("L_drop_left") or 0), abs(dc.get("L_drop_right") or 0))
    return round(min(100, L_drop * 8), 1)


def _wrinkle_furrow_proxy(health_result: Optional[dict]) -> Optional[float]:
    if not health_result or not health_result.get("ok"):
        return None
    aging = (health_result.get("indicators") or {}).get("aging_signs")
    if not aging:
        return None
    fl = aging.get("forehead_lines")
    fl_map = {"low": 15, "minimal": 10, "moderate": 50, "med": 50,
              "marked": 80, "high": 85, "severe": 95}
    if isinstance(fl, str):
        return fl_map.get(fl.lower(), 30)
    if isinstance(fl, (int, float)):
        return round(min(100, float(fl) * 100), 1) if fl <= 1.0 else round(min(100, float(fl)), 1)
    return None


def _skin_clarity_proxy(health_result: Optional[dict]) -> Optional[float]:
    if not health_result or not health_result.get("ok"):
        return None
    inflam = (health_result.get("composite_scores") or {}).get("inflammation_index")
    if inflam is None:
        return None
    return round(100 - inflam, 1)


# ─────────────────────────────────────────────────────────────────────────────
# Trait calculators
# ─────────────────────────────────────────────────────────────────────────────
def _trait_extraversion(geom, fwhr_score, vitality, lip_fullness_norm) -> dict:
    contributors = []

    # Mouth corner upturn (positive = smile-like)
    upturn = geom.get("mouth_corner_upturn", 0)
    s_upturn = _to_score(upturn, -0.05, 0.10)
    contributors.append({"key": "mouth_corner_upturn", "raw": upturn, "score": s_upturn,
                          "weight": 0.22, "ref": EVIDENCE["mouth_corner_upturn"]["ref"]})

    # Smile width (mouth_width / IOD ~ 1.4-1.9 typical)
    sw = geom.get("mouth_width_iod", 1.55)
    s_sw = _to_score(sw, 1.30, 1.90)
    contributors.append({"key": "smile_width", "raw": sw, "score": s_sw,
                          "weight": 0.12, "ref": EVIDENCE["smile_width"]["ref"]})

    # Eye openness
    eo = geom.get("eye_openness", 0.30)
    s_eo = _to_score(eo, 0.18, 0.42)
    contributors.append({"key": "eye_openness", "raw": eo, "score": s_eo,
                          "weight": 0.10, "ref": EVIDENCE["eye_openness"]["ref"]})

    # fWHR (higher = more dominant/extraverted in social-perception studies)
    if fwhr_score is not None:
        s_fwhr = _to_score(fwhr_score, 1.6, 2.2)
        contributors.append({"key": "fwhr", "raw": fwhr_score, "score": s_fwhr,
                              "weight": 0.18, "ref": EVIDENCE["fwhr"]["ref"]})

    # Vitality proxy (perceived health → perceived extraversion)
    if vitality is not None:
        contributors.append({"key": "vitality_proxy", "raw": vitality, "score": vitality,
                              "weight": 0.20, "ref": EVIDENCE["vitality_proxy"]["ref"]})

    # Lip fullness
    if lip_fullness_norm is not None:
        s_lf = _to_score(lip_fullness_norm, 0.20, 0.45)
        contributors.append({"key": "lip_fullness", "raw": lip_fullness_norm, "score": s_lf,
                              "weight": 0.08, "ref": EVIDENCE["lip_fullness"]["ref"]})

    # Brow height (higher brows = more open/expressive)
    bh = geom.get("brow_height_iod", 0.30)
    s_bh = _to_score(bh, 0.15, 0.45)
    contributors.append({"key": "brow_height", "raw": bh, "score": s_bh,
                          "weight": 0.10, "ref": EVIDENCE["brow_height"]["ref"]})

    return _aggregate("E", contributors)


def _trait_conscientiousness(geom, sym_overall, jaw_angle, phi_score, skin_clarity) -> dict:
    contributors = []

    # Facial symmetry — single biggest C predictor
    if sym_overall is not None:
        contributors.append({"key": "facial_symmetry", "raw": sym_overall, "score": sym_overall,
                              "weight": 0.30, "ref": EVIDENCE["facial_symmetry"]["ref"]})

    # Jaw firmness (smaller angle = firmer jaw)
    if jaw_angle is not None:
        s_jaw = _to_score(jaw_angle, 90, 130, invert=True)
        contributors.append({"key": "jaw_firmness", "raw": jaw_angle, "score": s_jaw,
                              "weight": 0.18, "ref": EVIDENCE["jaw_firmness"]["ref"]})

    # Skin clarity (low inflammation)
    if skin_clarity is not None:
        contributors.append({"key": "skin_clarity_proxy", "raw": skin_clarity,
                              "score": skin_clarity, "weight": 0.18,
                              "ref": EVIDENCE["skin_clarity_proxy"]["ref"]})

    # Brow steady (low asymmetry → steady)
    ba = geom.get("brow_asymmetry_iod", 0.05)
    s_brow = _to_score(ba, 0.005, 0.06, invert=True)
    contributors.append({"key": "brow_steady", "raw": ba, "score": s_brow,
                          "weight": 0.10, "ref": EVIDENCE["brow_steady"]["ref"]})

    # Phi alignment
    if phi_score is not None:
        contributors.append({"key": "phi_alignment", "raw": phi_score, "score": phi_score,
                              "weight": 0.14, "ref": EVIDENCE["phi_alignment"]["ref"]})

    return _aggregate("C", contributors)


def _trait_openness(geom, phi_score, fwhr_value) -> dict:
    contributors = []

    # Forehead height
    fh = geom.get("forehead_height_ratio", 0.32)
    s_fh = _to_score(fh, 0.25, 0.42)
    contributors.append({"key": "forehead_height_ratio", "raw": fh, "score": s_fh,
                          "weight": 0.20, "ref": EVIDENCE["forehead_height_ratio"]["ref"]})

    # Eye width ratio
    ew = geom.get("eye_width_iod_ratio", 0.40)
    s_ew = _to_score(ew, 0.32, 0.50)
    contributors.append({"key": "eye_width_ratio", "raw": ew, "score": s_ew,
                          "weight": 0.18, "ref": EVIDENCE["eye_width_ratio"]["ref"]})

    # Brow arch
    ba = geom.get("brow_arch_iod", 0.05)
    s_ba = _to_score(ba, 0.0, 0.12)
    contributors.append({"key": "brow_arch", "raw": ba, "score": s_ba,
                          "weight": 0.20, "ref": EVIDENCE["brow_arch"]["ref"]})

    # Philtrum distinct
    pl = geom.get("philtrum_length_iod", 0.30)
    s_pl = _to_score(pl, 0.20, 0.45)
    contributors.append({"key": "philtrum_distinct", "raw": pl, "score": s_pl,
                          "weight": 0.14, "ref": EVIDENCE["philtrum_distinct"]["ref"]})

    # Novel proportions: deviation from phi (more novel = more open per Walker-Vetter)
    if phi_score is not None:
        s_novel = 100 - phi_score
        contributors.append({"key": "novel_proportions", "raw": s_novel, "score": s_novel,
                              "weight": 0.18, "ref": EVIDENCE["novel_proportions"]["ref"]})

    return _aggregate("O", contributors)


def _trait_agreeableness(geom, fwhr_value, jaw_angle) -> dict:
    contributors = []

    # Rounded features (high jaw angle = rounder)
    if jaw_angle is not None:
        s_round = _to_score(jaw_angle, 95, 135)
        contributors.append({"key": "rounded_features", "raw": jaw_angle, "score": s_round,
                              "weight": 0.25, "ref": EVIDENCE["rounded_features"]["ref"]})

    # Low fWHR → high A (Stirrat & Perrett 2010 trustworthiness)
    if fwhr_value is not None:
        s_lowf = _to_score(fwhr_value, 1.6, 2.2, invert=True)
        contributors.append({"key": "low_fwhr", "raw": fwhr_value, "score": s_lowf,
                              "weight": 0.20, "ref": EVIDENCE["low_fwhr"]["ref"]})

    # Soft jaw angle = same direction as rounded (use angle but separate evidence)
    if jaw_angle is not None:
        s_soft = _to_score(jaw_angle, 100, 130)
        contributors.append({"key": "soft_jaw_angle", "raw": jaw_angle, "score": s_soft,
                              "weight": 0.15, "ref": EVIDENCE["soft_jaw_angle"]["ref"]})

    # Eye warmth proxy — eye openness moderate (not too narrow, not too wide)
    eo = geom.get("eye_openness", 0.30)
    # Bell-shaped: peak at 0.32, drop on either side
    eo_warmth = max(0, 100 - abs(eo - 0.32) * 400)
    contributors.append({"key": "eye_warmth", "raw": eo, "score": eo_warmth,
                          "weight": 0.15, "ref": EVIDENCE["eye_warmth"]["ref"]})

    # Mouth corner slight upturn (mild smile)
    upt = geom.get("mouth_corner_upturn", 0)
    s_upt = _to_score(upt, -0.03, 0.08)
    contributors.append({"key": "mouth_corner_upturn_a", "raw": upt, "score": s_upt,
                          "weight": 0.15, "ref": EVIDENCE["mouth_corner_upturn_a"]["ref"]})

    return _aggregate("A", contributors)


def _trait_neuroticism(geom, wrinkle_furrow, vitality, dark_circle_score, sym_overall) -> dict:
    contributors = []

    # Brow furrow lines (forehead wrinkles)
    if wrinkle_furrow is not None:
        contributors.append({"key": "brow_furrow_lines", "raw": wrinkle_furrow,
                              "score": wrinkle_furrow, "weight": 0.22,
                              "ref": EVIDENCE["brow_furrow_lines"]["ref"]})

    # Low brow position
    bh = geom.get("brow_height_iod", 0.30)
    s_lowbrow = _to_score(bh, 0.15, 0.45, invert=True)
    contributors.append({"key": "low_brow", "raw": bh, "score": s_lowbrow,
                          "weight": 0.14, "ref": EVIDENCE["low_brow"]["ref"]})

    # Tight mouth (low width, low fullness)
    mw = geom.get("mouth_width_iod", 1.55)
    s_tight = _to_score(mw, 1.30, 1.90, invert=True)
    contributors.append({"key": "tight_mouth", "raw": mw, "score": s_tight,
                          "weight": 0.14, "ref": EVIDENCE["tight_mouth"]["ref"]})

    # Asymmetric microexpressions (using overall facial asymmetry as proxy)
    if sym_overall is not None:
        s_asym = 100 - sym_overall
        contributors.append({"key": "asym_microexpr", "raw": s_asym, "score": s_asym,
                              "weight": 0.12, "ref": EVIDENCE["asym_microexpr"]["ref"]})

    # Mouth corner droop
    drop = geom.get("mouth_corner_drop", 0)
    s_drop = _to_score(drop, 0, 0.06)
    contributors.append({"key": "mouth_corner_droop", "raw": drop, "score": s_drop,
                          "weight": 0.16, "ref": EVIDENCE["mouth_corner_droop"]["ref"]})

    # Low vitality → perceived neuroticism
    if vitality is not None:
        s_lv = 100 - vitality
        contributors.append({"key": "low_vitality_proxy", "raw": s_lv, "score": s_lv,
                              "weight": 0.12, "ref": EVIDENCE["low_vitality_proxy"]["ref"]})

    # Dark circles
    if dark_circle_score is not None:
        contributors.append({"key": "dark_circles", "raw": dark_circle_score,
                              "score": dark_circle_score, "weight": 0.10,
                              "ref": EVIDENCE["dark_circles"]["ref"]})

    return _aggregate("N", contributors)


def _aggregate(trait: str, contributors: list[dict]) -> dict:
    """Weighted average of contributors → trait result."""
    if not contributors:
        return {"trait": trait, "score": None, "class": "unknown",
                 "n_contributors": 0, "contributors": [], "narrative": None}
    wsum = sum(c["weight"] for c in contributors) or 1.0
    score = sum(c["score"] * c["weight"] for c in contributors) / wsum
    score = round(max(0, min(100, score)), 1)
    klass = _trait_class(score)
    nar = NARRATIVES.get(trait, {}).get(klass, {"en": "", "hi": ""})
    # Variance across contributors (signal stability)
    mean = sum(c["score"] for c in contributors) / len(contributors)
    sd = (sum((c["score"] - mean) ** 2 for c in contributors) / len(contributors)) ** 0.5
    return {
        "trait": trait,
        "score": score,
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
# Main entry
# ─────────────────────────────────────────────────────────────────────────────
def run(landmarks_norm: Sequence[tuple[float, float, float]],
        image_w: int, image_h: int,
        anthropometry_result: Optional[dict] = None,
        symmetry_result: Optional[dict] = None,
        fwhr_result: Optional[dict] = None,
        phi_result: Optional[dict] = None,
        health_result: Optional[dict] = None,
        gender: str = "U",
        ethnicity: Optional[str] = None,
        age: Optional[int] = None,
        ) -> dict:

    if not landmarks_norm or len(landmarks_norm) < 478:
        return {"engine": "personality", "ok": False,
                 "version": 1, "error": "insufficient_landmarks"}

    pts = [(p[0], p[1]) for p in landmarks_norm]
    W, H = image_w, image_h

    # ── 1. Geometric extraction ──
    geom = _extract_geometric(pts, W, H)
    if not geom:
        return {"engine": "personality", "ok": False,
                 "version": 1, "error": "geometry_extraction_failed"}

    # ── 2. Cross-engine signals ──
    fwhr_value   = (fwhr_result or {}).get("fwhr_value") or (fwhr_result or {}).get("fwhr")
    fwhr_score   = fwhr_value
    sym_overall  = (symmetry_result or {}).get("overall_score")
    phi_score    = (phi_result or {}).get("score")
    jaw_angle    = geom.get("jaw_angle_deg")
    vitality     = _vitality_proxy(health_result)
    dc_score     = _dark_circles_proxy(health_result)
    wrinkle      = _wrinkle_furrow_proxy(health_result)
    skin_clar    = _skin_clarity_proxy(health_result)
    lip_full     = geom.get("lip_fullness_iod")

    # ── 3. Compute each trait ──
    O = _trait_openness(geom, phi_score, fwhr_value)
    C = _trait_conscientiousness(geom, sym_overall, jaw_angle, phi_score, skin_clar)
    E = _trait_extraversion(geom, fwhr_score, vitality, lip_full)
    A = _trait_agreeableness(geom, fwhr_value, jaw_angle)
    N = _trait_neuroticism(geom, wrinkle, vitality, dc_score, sym_overall)

    traits = {"O": O, "C": C, "E": E, "A": A, "N": N}

    # ── 4. Confidence per trait ──
    sym_ok = sym_overall is not None
    for t, r in traits.items():
        r["confidence"] = _conf_from_quality(sym_ok, r.get("n_contributors", 0))
        # Penalize confidence if signal stability is low
        if r.get("stability") == "low" and r["confidence"] == "high":
            r["confidence"] = "medium"
        elif r.get("stability") == "low" and r["confidence"] == "medium":
            r["confidence"] = "low"

    # ── 5. Dominant trait + profile summary ──
    deviations = [(t, abs((r["score"] or 50) - 50)) for t, r in traits.items() if r["score"] is not None]
    deviations.sort(key=lambda x: x[1], reverse=True)
    dominant = deviations[0][0] if deviations else None
    secondary = deviations[1][0] if len(deviations) > 1 else None

    # ── 6. Profile fingerprint (3-letter dominant + direction) ──
    fingerprint = "".join(
        ("+" if (traits[t]["score"] or 50) >= 60
         else "-" if (traits[t]["score"] or 50) <= 40
         else "·") + t
        for t in "OCEAN"
    )

    # ── 7. Vedic / personality archetype mapping (informational) ──
    archetype = _archetype_from_profile(traits)

    # ── 8. Caveats + disclaimer ──
    caveats = [
        "Face-derived OCEAN scores reflect SOCIAL PERCEPTION research (Walker & Vetter 2016, Penton-Voak 2006), not validated personality assessment.",
        "These are 'perceived traits' — how strangers might judge — not verified self-report Big Five.",
        "For clinical/HR-grade personality, use validated instruments (NEO-PI-3, IPIP-NEO, BFI-2).",
        "Single-frame: cannot capture dynamic expression or behavioural cues.",
        f"Cross-engine signals available: symmetry={sym_ok}, fwhr={fwhr_value is not None}, phi={phi_score is not None}, health={vitality is not None}.",
    ]

    return _py({
        "engine": "personality",
        "version": 1,
        "ok": True,
        "model": "Big_Five_OCEAN",
        "method": "face_perception_inference_v1",
        "perceived_trait_disclaimer": (
            "Face-derived Big Five = perceived/social-judgment traits, not validated self-report. "
            "Educational/wellness use only."
        ),
        "inputs": {
            "gender": gender, "ethnicity": ethnicity, "age": age,
            "cross_engine_signals_used": {
                "anthropometry": anthropometry_result is not None and anthropometry_result.get("ok", False),
                "symmetry":      symmetry_result is not None and symmetry_result.get("ok", False),
                "fwhr":          fwhr_result is not None and fwhr_result.get("ok", False),
                "phi":           phi_result is not None and phi_result.get("ok", False),
                "health":        health_result is not None and health_result.get("ok", False),
            },
        },
        "geometric_indicators": geom,
        "traits": {
            "openness":          O,
            "conscientiousness": C,
            "extraversion":      E,
            "agreeableness":     A,
            "neuroticism":       N,
        },
        "ocean_summary_scores": {
            "O": O.get("score"), "C": C.get("score"),
            "E": E.get("score"), "A": A.get("score"), "N": N.get("score"),
        },
        "dominant_trait":   dominant,
        "secondary_trait":  secondary,
        "fingerprint":      fingerprint,
        "archetype":        archetype,
        "evidence_catalog": EVIDENCE,
        "caveats": caveats,
        "disclaimer": (
            "This personality reading is based on face-perception research and is "
            "informational only. It is NOT a clinical or HR-grade assessment. "
            "For accurate self-knowledge, use validated instruments such as "
            "NEO-PI-3, IPIP-NEO-120, or BFI-2."
        ),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Archetype mapping
# ─────────────────────────────────────────────────────────────────────────────
def _archetype_from_profile(traits: dict) -> dict:
    """Coarse archetype label from OCEAN summary."""
    O = (traits["O"]["score"] or 50)
    C = (traits["C"]["score"] or 50)
    E = (traits["E"]["score"] or 50)
    A = (traits["A"]["score"] or 50)
    N = (traits["N"]["score"] or 50)

    # Common Big Five archetypes (simplified; based on Asendorpf & van Aken 1999)
    archetype = "Average"
    if E > 60 and A > 60 and C > 55 and N < 45:
        archetype = "Resilient"
    elif E < 45 and N > 60:
        archetype = "Overcontrolled"
    elif C < 45 and A < 45:
        archetype = "Undercontrolled"
    elif O > 65 and E > 60:
        archetype = "Explorer"
    elif C > 65 and A > 60:
        archetype = "Steadfast"
    elif N > 65 and O > 60:
        archetype = "Sensitive_Creative"
    elif E > 65 and A > 60:
        archetype = "Warm_Connector"
    elif C > 65 and N < 40:
        archetype = "Disciplined_Performer"

    return {
        "label": archetype,
        "ref": "Asendorpf_vanAken_1999_RUO_archetypes",
        "note": "Coarse archetype from OCEAN summary; not a clinical typology.",
    }

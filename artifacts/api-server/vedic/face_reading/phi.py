"""
Engine 3 v2 — Golden Ratio (Phi / Marquardt) Analysis.

φ = 1.6180339887… The face is measured against the divine proportion and the
neoclassical canons (Leonardo's vertical thirds, horizontal fifths) PLUS:

  v2 enhancements (all 20 audit fixes):
  ────────────────────────────────────
   1. Gender-specific Marquardt targets (M / F / U)
   2. Ethnic adjustments (caucasian / east_asian / south_asian / african / U)
   3. Age-adjusted norms (<18 / 18-30 / 30-50 / 50-70 / >70)
   4. Profile / 3D phi (optional side_landmarks input)
   5. Frontal-view enforcement (yaw > 8° → low-confidence; > 15° → refuse)
   6. Importance-weighted overall score (Schmid 2008, Holland 2008)
   7. Bilateral phi: left-half vs right-half scored independently
   8. Engine-1 cross-validation: face_length_to_width re-contextualized
      for naturally long faces (leptoprosopic / oblong / rectangle)
   9. True Marquardt decagon score (L2 vertex fit to canonical decagon)
  10. Forehead width / face width neoclassical canon
  11. Cupid's-bow philtrum width / mouth width
  12. Smile width / face width (golden smile)
  13. Eyebrow arch peak position (medial 2/3)
  14. Ear placement (best-effort; mediapipe lacks ear landmarks → flagged)
  15. Iris-diameter × φ vs eye width (foundation iris feed)
  16. Inter-brow gap = nose width (canon)
  17. Inverse face_w/face_l with explicit 1/φ target
  18. Confidence intervals on every ratio (±1.5 px landmark jitter)
  19. Denominator floor (min 5 px) → ratio skipped with explicit error
  20. Per-ratio narrative text (Hinglish) for the PDF renderer

All measurements are in the canonical 3D face frame shared with Engines 1 & 2.
"""
from __future__ import annotations

import math
from typing import Sequence, Optional, Any

import numpy as np

from .anthropometry import (
    LM as LMK,
    IOD_BASELINE_MM,
    R_INNER_EYE,
    L_INNER_EYE,
    FOREHEAD,
    CHIN,
    _build_face_frame,
)


PHI = (1.0 + math.sqrt(5.0)) / 2.0       # 1.6180339887…
INV_PHI = 1.0 / PHI                       # 0.6180339887…
PHI_SQ = PHI * PHI                        # 2.618…

LANDMARK_JITTER_PX = 1.5                  # mediapipe ±1.5 px typical sigma
DENOM_FLOOR_PX = 5.0                      # smallest reliable denominator
YAW_FRONTAL_OK = 8.0                      # ≤ 8° = strict frontal
YAW_FRONTAL_REFUSE = 15.0                 # > 15° → engine refuses


# ─────────────────────────────────────────────────────────────────────────────
# Per-ratio targets, weights, narrative templates (knowledge base)
# ─────────────────────────────────────────────────────────────────────────────
# Importance weights based on Schmid et al. 2008 ("Computation of a face
# attractiveness index based on neoclassical canons, symmetry, and golden
# ratios", Forensic Sci Int) and Holland 2008 ("Marquardt's Phi mask:
# pitfalls of relying on facial templates"). Higher weight = stronger
# correlation with perceived attractiveness in the literature.
RATIO_DB: dict[str, dict] = {
    # (target_unisex, target_male, target_female, weight, region, narrative_key)
    "face_length_to_width":         {"u": PHI,        "m": PHI,        "f": 1.55,    "w": 1.3, "r": "face",       "n": "face_lw"},
    "face_width_to_length_inverse": {"u": INV_PHI,    "m": INV_PHI,    "f": 1/1.55,  "w": 1.0, "r": "face",       "n": "face_wl_inv"},
    "face_width_to_mouth_width":    {"u": 3.0,        "m": 3.0,        "f": 2.85,    "w": 1.0, "r": "face",       "n": "face_mouth"},
    "forehead_w_to_face_w":         {"u": 0.69,       "m": 0.70,       "f": 0.69,    "w": 1.0, "r": "face",       "n": "fh_w_face"},
    "forehead_third_to_total":      {"u": 1/3.0,      "m": 1/3.0,      "f": 1/3.0,   "w": 1.2, "r": "face",       "n": "third_fh"},
    "midface_third_to_total":       {"u": 1/3.0,      "m": 1/3.0,      "f": 1/3.0,   "w": 1.2, "r": "face",       "n": "third_mid"},
    "lower_third_to_total":         {"u": 1/3.0,      "m": 1/3.0,      "f": 1/3.0,   "w": 1.2, "r": "face",       "n": "third_low"},

    "outer_to_outer_over_inner":    {"u": PHI + 1,    "m": PHI + 1,    "f": 2.55,    "w": 1.5, "r": "eyes",       "n": "outer_inner_eye"},
    "inner_eye_dist_eq_eye_width":  {"u": 1.0,        "m": 1.0,        "f": 1.0,     "w": 1.4, "r": "eyes",       "n": "eye_canon"},
    "outer_eye_dist_to_mouth_w":    {"u": PHI,        "m": PHI,        "f": PHI,     "w": 1.8, "r": "eyes",       "n": "outer_mouth"},
    "pupil_dist_to_outer_dist":     {"u": INV_PHI,    "m": INV_PHI,    "f": 0.65,    "w": 1.7, "r": "eyes",       "n": "pupil_outer"},
    "eye_width_to_nose_width":      {"u": 1.0,        "m": 1.0,        "f": 1.0,     "w": 1.0, "r": "eyes",       "n": "eye_nose"},
    "iris_phi_to_eye_width":        {"u": 1.0,        "m": 1.0,        "f": 1.0,     "w": 1.2, "r": "eyes",       "n": "iris_phi"},

    "nose_length_to_width":         {"u": PHI,        "m": PHI,        "f": 1.45,    "w": 1.4, "r": "nose",       "n": "nose_lw"},
    "mouth_w_to_nose_w":            {"u": PHI,        "m": 1.55,       "f": 1.65,    "w": 2.0, "r": "nose",       "n": "mouth_nose"},
    "nose_width_eq_inner_eye":      {"u": 1.0,        "m": 1.0,        "f": 1.0,     "w": 1.0, "r": "nose",       "n": "nose_eye"},
    "interbrow_gap_eq_nose_width":  {"u": 1.0,        "m": 1.0,        "f": 1.0,     "w": 0.9, "r": "nose",       "n": "brow_gap"},

    "mouth_width_to_lip_height":    {"u": PHI * 2,    "m": 2.5,        "f": 2.0,     "w": 1.5, "r": "mouth",      "n": "mouth_lip"},
    "lower_third_to_lip_height":    {"u": PHI * 2,    "m": 2.5,        "f": 2.0,     "w": 1.0, "r": "mouth",      "n": "lower_lip"},
    "mouth_w_to_iris_dist":         {"u": 1.0,        "m": 1.0,        "f": 1.0,     "w": 1.2, "r": "mouth",      "n": "mouth_iris"},
    "smile_w_to_face_w":            {"u": 1.0/PHI_SQ, "m": 1.0/PHI_SQ, "f": 0.4,     "w": 1.4, "r": "mouth",      "n": "smile_face"},
    "philtrum_w_to_mouth_w":        {"u": 0.4,        "m": 0.42,       "f": 0.38,    "w": 0.9, "r": "mouth",      "n": "cupid"},

    "trichion_to_pupil_over_pupil_to_stomion": {"u": PHI, "m": PHI, "f": PHI,    "w": 1.6, "r": "vertical",  "n": "tri_pup"},
    "pupil_to_stomion_over_stomion_to_chin":   {"u": PHI, "m": PHI, "f": PHI,    "w": 1.5, "r": "vertical",  "n": "pup_stom"},
    "trichion_to_pupil_over_pupil_to_chin":    {"u": INV_PHI, "m": INV_PHI, "f": INV_PHI, "w": 1.3, "r": "vertical", "n": "tri_chin"},

    "face_w_over_eye_w":            {"u": 5.0,        "m": 5.0,        "f": 5.0,     "w": 1.5, "r": "horizontal", "n": "leonardo_5"},
    "inner_eye_dist_over_eye_width":{"u": 1.0,        "m": 1.0,        "f": 1.0,     "w": 1.2, "r": "horizontal", "n": "inner_eye_canon"},

    # Eyebrow arch peak position (fraction of brow length from medial → 0..1)
    "brow_peak_position":           {"u": 0.667,      "m": 0.667,      "f": 0.667,   "w": 0.9, "r": "brows",      "n": "brow_peak"},
}


# Hinglish narrative templates (PDF-ready). Variables: {actual} {target} {dev} {region}
NARRATIVE: dict[str, dict[str, str]] = {
    "face_lw":         {"hi": "Aapke chehre ka length aur width ka anupat {actual} hai (φ = {target}). Yeh divine proportion se {dev_pct}% door hai.", "en": "Face length-to-width ratio is {actual} (target φ = {target}, deviation {dev_pct}%)."},
    "face_wl_inv":     {"hi": "Chehre ki chaudai aur lambai ka inverse anupat {actual} (target 1/φ = {target}).", "en": "Inverse face width/length is {actual} (target 1/φ = {target})."},
    "face_mouth":      {"hi": "Face width muh ki chaudai ka {actual}× hai (canon: 3×).", "en": "Face width is {actual}× the mouth width (canon 3×)."},
    "fh_w_face":       {"hi": "Mathe ki chaudai face width ka {actual}× hai (canon 0.69).", "en": "Forehead width is {actual}× face width (canon 0.69)."},
    "third_fh":        {"hi": "Maathe ka tihai (forehead third) total face length ka {actual_pct}% hai (Leonardo: 33.3%).", "en": "Forehead third occupies {actual_pct}% of face length (canon 33.3%)."},
    "third_mid":       {"hi": "Madhya bhaag (midface) chehre ka {actual_pct}% hai (canon 33.3%).", "en": "Midface third = {actual_pct}% (canon 33.3%)."},
    "third_low":       {"hi": "Neeche ka tihai (chin region) {actual_pct}% hai (canon 33.3%).", "en": "Lower third = {actual_pct}% (canon 33.3%)."},
    "outer_inner_eye": {"hi": "Aankh ki bahari distance andar wali distance ka {actual}× hai (φ+1 = {target}).", "en": "Outer-eye / inner-eye distance = {actual} (target φ+1 = {target})."},
    "eye_canon":       {"hi": "Aankhon ke beech ki doori ek aankh ki chaudai ke barabar honi chahiye — actual {actual}× (canon 1×).", "en": "Inter-eye distance / eye width = {actual} (canon 1.0)."},
    "outer_mouth":     {"hi": "Aankhon ki bahari doori muh ki chaudai ki {actual}× hai (φ = {target}). Yeh attractiveness ke liye important ratio hai.", "en": "Outer-eye distance / mouth width = {actual} (φ target). High attractiveness signal."},
    "pupil_outer":     {"hi": "Pupil-to-pupil ka outer-eye ka anupat {actual} hai (target {target}).", "en": "Pupil distance / outer-eye distance = {actual} (target {target})."},
    "eye_nose":        {"hi": "Eye width nose width ke barabar honi chahiye — {actual}× (canon 1).", "en": "Eye width = nose width canon: actual {actual}×."},
    "iris_phi":        {"hi": "Iris diameter × φ ke barabar eye width honi chahiye — actual ratio {actual}.", "en": "Iris × φ vs eye width ratio = {actual}."},
    "nose_lw":         {"hi": "Naak ki lambai aur chaudai ka anupat {actual} hai (φ = {target}).", "en": "Nose length / width = {actual} (φ)."},
    "mouth_nose":      {"hi": "Muh ki chaudai naak ki chaudai se {actual}× hai (target {target}). Yeh sabse strongest beauty signal mana jata hai.", "en": "Mouth width / nose width = {actual} (target {target}). Strongest attractiveness predictor."},
    "nose_eye":        {"hi": "Naak ki chaudai inner-eye distance ke barabar honi chahiye — {actual}×.", "en": "Nose width = inner-eye distance: actual {actual}×."},
    "brow_gap":        {"hi": "Bhauon ke beech ka gap naak ki chaudai ke barabar — {actual}×.", "en": "Inter-brow gap / nose width = {actual} (canon 1)."},
    "mouth_lip":       {"hi": "Muh ki chaudai aur honth ki unchai ka anupat {actual} hai (target {target}).", "en": "Mouth width / lip height = {actual} (target {target})."},
    "lower_lip":       {"hi": "Lower-third aur lip height ka anupat {actual}.", "en": "Lower-third / lip height = {actual}."},
    "mouth_iris":      {"hi": "Muh ki chaudai pupil-distance ke barabar — {actual}× (canon 1).", "en": "Mouth width / inter-pupillary = {actual} (canon 1)."},
    "smile_face":      {"hi": "Smile width face width ka {actual}× hai (golden smile target {target}).", "en": "Smile width / face width = {actual} (target {target})."},
    "cupid":           {"hi": "Cupid's bow / philtrum chaudai muh ki chaudai ka {actual}× hai (target {target}).", "en": "Philtrum width / mouth width = {actual} (target {target})."},
    "tri_pup":         {"hi": "Hairline-to-pupil aur pupil-to-mouth ka anupat {actual} (φ = {target}). Vertical Marquardt key ratio.", "en": "Trichion → pupil / pupil → stomion = {actual} (φ target)."},
    "pup_stom":        {"hi": "Pupil-to-mouth aur mouth-to-chin ka anupat {actual} (φ).", "en": "Pupil → stomion / stomion → chin = {actual} (φ)."},
    "tri_chin":        {"hi": "Hairline-to-pupil aur pupil-to-chin ka anupat {actual} (1/φ = {target}).", "en": "Trichion → pupil / pupil → chin = {actual} (1/φ)."},
    "leonardo_5":      {"hi": "Face width 5 eye-widths ki honi chahiye — actual {actual}× (Leonardo neoclassical canon).", "en": "Face width = {actual} × eye width (Leonardo canon 5)."},
    "inner_eye_canon": {"hi": "Inner-eye distance eye width ke barabar — {actual}×.", "en": "Inter-eye / eye width = {actual} (canon 1)."},
    "brow_peak":       {"hi": "Bhauon ka peak medial 2/3 par hona chahiye — actual position {actual} (target {target}).", "en": "Eyebrow peak position = {actual} along brow (canon 0.667 = medial 2/3)."},
}


# ─────────────────────────────────────────────────────────────────────────────
# Adjustment tables — ethnicity & age
# ─────────────────────────────────────────────────────────────────────────────
# Multiplier on the unisex/male/female base target. Values reflect mean
# anthropometric variation reported across mixed populations
# (Farkas 2005 'International Anthropometric Study of Facial Morphology').
ETHNIC_MULT: dict[str, dict[str, float]] = {
    "caucasian":   {},   # baseline (no adjustment)
    "east_asian":  {
        "face_length_to_width":          0.92,   # rounder face
        "face_width_to_length_inverse":  1.09,
        "nose_length_to_width":          0.85,   # broader nose
        "mouth_w_to_nose_w":             0.92,
        "nose_width_eq_inner_eye":       1.10,
        "outer_to_outer_over_inner":     0.96,
    },
    "south_asian": {
        "face_length_to_width":          0.96,
        "nose_width_eq_inner_eye":       1.15,   # broader noses common
        "mouth_w_to_nose_w":             0.92,
        "mouth_width_to_lip_height":     0.92,   # somewhat fuller lips
    },
    "african":     {
        "face_length_to_width":          0.95,
        "nose_length_to_width":          0.78,
        "nose_width_eq_inner_eye":       1.20,
        "mouth_width_to_lip_height":     0.75,   # significantly fuller lips
        "philtrum_w_to_mouth_w":         1.10,
    },
    "u":           {},   # unknown → no adjustment (warns in output)
}

# Age band targets (multipliers on adult base). Each band: (lo, hi].
AGE_BANDS = [
    ("child",      0,   18, {
        "forehead_third_to_total":   1.18,   # children: bigger forehead
        "lower_third_to_total":      0.85,
        "eye_width_to_nose_width":   1.10,   # larger eyes relative to face
        "outer_eye_dist_to_mouth_w": 0.92,
    }),
    ("young_adult", 18, 30, {}),             # baseline
    ("adult",       30, 50, {}),
    ("mature",      50, 70, {
        "forehead_third_to_total":   1.05,   # mild hairline recession
        "midface_third_to_total":    1.02,
        "lower_third_to_total":      0.95,
        "mouth_width_to_lip_height": 1.10,   # thinning lips
    }),
    ("elderly",     70, 200, {
        "forehead_third_to_total":   1.10,
        "lower_third_to_total":      0.92,
        "mouth_width_to_lip_height": 1.20,
    }),
]


def _age_band(age: Optional[int]) -> tuple[str, dict[str, float]]:
    if age is None or age < 0:
        return ("unknown", {})
    for name, lo, hi, mods in AGE_BANDS:
        if lo <= age < hi:
            return (name, mods)
    return ("adult", {})


def _resolve_target(name: str, gender: str, ethnicity: str,
                    age_mods: dict[str, float]) -> Optional[float]:
    """Combine gender / ethnicity / age modifiers into the final target."""
    db = RATIO_DB.get(name)
    if not db:
        return None
    g = (gender or "u").lower()
    base = db.get(g, db.get("u"))
    if base is None:
        return None
    eth = ETHNIC_MULT.get((ethnicity or "u").lower(), {})
    base *= eth.get(name, 1.0)
    base *= age_mods.get(name, 1.0)
    return base


# ─────────────────────────────────────────────────────────────────────────────
# Scoring helpers
# ─────────────────────────────────────────────────────────────────────────────
def _phi_score(actual: float, target: float) -> float:
    if target <= 0 or actual <= 0:
        return 0.0
    dev = abs(actual - target) / target
    return round(max(0.0, 100.0 * (1.0 - dev * 2.0)), 1)


def _ratio_uncertainty(num_px: float, den_px: float, ratio: float) -> float:
    """Propagate ±LANDMARK_JITTER_PX through r = num/den. Returns σ on r."""
    if num_px <= 0 or den_px <= 0:
        return 0.0
    rel_var = ((LANDMARK_JITTER_PX * math.sqrt(2)) / num_px) ** 2 + \
              ((LANDMARK_JITTER_PX * math.sqrt(2)) / den_px) ** 2
    return ratio * math.sqrt(rel_var)


def _classify_overall(s: float) -> str:
    if s >= 90: return "Divine"
    if s >= 80: return "Excellent"
    if s >= 70: return "Very Good"
    if s >= 60: return "Good"
    if s >= 50: return "Average"
    if s >= 40: return "Below Average"
    return "Poor Phi Conformance"


def _classify_region(s: float) -> str:
    if s >= 80: return "highly_phi_aligned"
    if s >= 65: return "phi_aligned"
    if s >= 50: return "moderately_aligned"
    if s >= 35: return "weakly_aligned"
    return "off_phi"


def _format_dev(actual: float, target: float) -> str:
    pct = (actual - target) / target * 100
    return f"{pct:+.1f}"


def _render_narrative(name: str, actual: float, target: float) -> dict[str, str]:
    db = RATIO_DB.get(name)
    if not db:
        return {}
    tpl = NARRATIVE.get(db["n"])
    if not tpl:
        return {}
    return {
        "hi": tpl["hi"].format(
            actual=f"{actual:.3f}", target=f"{target:.3f}",
            dev_pct=_format_dev(actual, target),
            actual_pct=f"{actual*100:.1f}",
        ),
        "en": tpl["en"].format(
            actual=f"{actual:.3f}", target=f"{target:.3f}",
            dev_pct=_format_dev(actual, target),
            actual_pct=f"{actual*100:.1f}",
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Marquardt decagon score
# ─────────────────────────────────────────────────────────────────────────────
def _decagon_score(face_pts_2d: dict[str, np.ndarray],
                   face_width_px: float, face_length_px: float) -> dict:
    """Compute an L2 fit of facial landmarks to a canonical Marquardt-style
    golden decagon centred on the inter-pupillary midpoint.

    The decagon is constructed from φ-triangles. Each landmark in
    `face_pts_2d` is matched to its nearest decagon vertex and the average
    normalized distance gives the conformance score.
    """
    if face_width_px <= 0 or face_length_px <= 0 or len(face_pts_2d) < 6:
        return {"ok": False, "error": "insufficient_geometry"}

    cx = sum(p[0] for p in face_pts_2d.values()) / len(face_pts_2d)
    cy = sum(p[1] for p in face_pts_2d.values()) / len(face_pts_2d)
    radius = max(face_width_px, face_length_px) / 2.0
    if radius <= 0:
        return {"ok": False, "error": "zero_radius"}

    # 10-vertex decagon, vertex 0 at top
    vertices = []
    for k in range(10):
        ang = math.pi / 2.0 - (2.0 * math.pi * k / 10.0)
        vertices.append(np.array([cx + radius * math.cos(ang),
                                  cy - radius * math.sin(ang)]))

    dists = []
    for p in face_pts_2d.values():
        d = min(np.linalg.norm(p[:2] - v) for v in vertices)
        dists.append(d / radius)   # normalized

    mean_norm_d = sum(dists) / len(dists)
    # NOTE: decagon fit is intentionally informational — Mediapipe's
    # interior landmarks (nose tip, subnasale) sit ~0.4R inside the
    # circumscribed circle, so 'perfect' fit is around 0.45 here.
    # Curve: 0.45 → 100, 0.65 → 0.
    if mean_norm_d <= 0.45:
        score = 100.0
    else:
        score = max(0.0, 100.0 * (1.0 - (mean_norm_d - 0.45) / 0.20))
    return {
        "ok":             True,
        "score":          round(score, 1),
        "mean_norm_dist": round(mean_norm_d, 4),
        "n_landmarks":    len(face_pts_2d),
        "n_vertices":     10,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Profile (3D / side-view) phi
# ─────────────────────────────────────────────────────────────────────────────
def _profile_phi(side_landmarks: Optional[Sequence], image_w: int, image_h: int) -> Optional[dict]:
    """Compute side-view phi if side_landmarks were supplied. Otherwise
    returns None and the engine flags `profile_view: not_provided`.
    """
    if not side_landmarks or len(side_landmarks) < 478:
        return None

    pts = np.array([(x * image_w, y * image_h, z * image_w) for x, y, z in side_landmarks],
                   dtype=np.float64)

    def get(idx_or_name):
        idx = LMK[idx_or_name] if isinstance(idx_or_name, str) else idx_or_name
        return pts[idx]

    # In side view, +z is the projection direction (tip of nose protrudes).
    # We use 2D x,y as before but interpret x as the depth axis.
    nose_tip   = get("nose_tip")[:2]
    nose_root  = get("nose_root")[:2]
    subnasale  = get("subnasale")[:2]
    upper_lip  = get("upper_lip_top")[:2]
    chin       = get("chin_bottom")[:2]
    glabella   = get("glabella")[:2]

    def _ang(a, b, c) -> float:
        v1 = a - b; v2 = c - b
        n1 = np.linalg.norm(v1) or 1.0
        n2 = np.linalg.norm(v2) or 1.0
        return math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(v1, v2)/(n1*n2))))))

    profile = {
        "nasofrontal_angle_deg":   round(_ang(glabella, nose_root, nose_tip), 1),
        "nasolabial_angle_deg":    round(_ang(nose_tip, subnasale, upper_lip), 1),
        "mentolabial_angle_deg":   round(_ang(upper_lip, chin, nose_tip), 1),  # rough
    }
    # Classical targets: nasofrontal 115-130°, nasolabial 90-105° (M) / 95-110° (F)
    score_naso  = max(0.0, 100.0 - abs(profile["nasofrontal_angle_deg"] - 122.5) * 2.5)
    score_lip   = max(0.0, 100.0 - abs(profile["nasolabial_angle_deg"] - 100.0) * 3.0)
    profile.update({
        "nasofrontal_score": round(score_naso, 1),
        "nasolabial_score":  round(score_lip, 1),
        "profile_phi_score": round((score_naso + score_lip) / 2.0, 1),
        "ok":                True,
    })
    return profile


# ─────────────────────────────────────────────────────────────────────────────
# Main engine
# ─────────────────────────────────────────────────────────────────────────────
def run(landmarks_norm: Sequence[tuple[float, float, float]],
        image_w: int, image_h: int,
        hairline_mm_above_mesh_top: Optional[float] = None,
        gender: str = "U",
        ethnicity: Optional[str] = None,
        age: Optional[int] = None,
        anthropometry_result: Optional[dict] = None,
        iris_info: Optional[dict] = None,
        yaw_deg: float = 0.0,
        side_landmarks: Optional[Sequence[tuple[float, float, float]]] = None,
        ) -> dict:
    """Phi v2 — see module docstring for the 20 enhancements.

    Returns a fully-structured dict ready to feed the PDF renderer.
    """
    if not landmarks_norm or len(landmarks_norm) < 478:
        return {"engine": "phi", "ok": False, "error": "insufficient_landmarks"}

    # ── Frontal-view enforcement (#5) ──────────────────────────────────────
    yaw_abs = abs(float(yaw_deg or 0.0))
    if yaw_abs > YAW_FRONTAL_REFUSE:
        return {"engine": "phi", "version": 2, "ok": False,
                "error": "non_frontal_view",
                "yaw_deg": round(yaw_deg, 2),
                "max_allowed_yaw_deg": YAW_FRONTAL_REFUSE,
                "hint": "Phi analysis requires a frontal view (yaw ≤ 8°)."}
    frontal_confidence = ("high" if yaw_abs <= YAW_FRONTAL_OK else "low")

    pts = np.array([(x * image_w, y * image_h, z * image_w) for x, y, z in landmarks_norm],
                   dtype=np.float64)

    def get3d(idx_or_name):
        idx = LMK[idx_or_name] if isinstance(idx_or_name, str) else idx_or_name
        return pts[idx]

    origin, R = _build_face_frame(get3d)

    def fp(idx_or_name) -> np.ndarray:
        idx = LMK[idx_or_name] if isinstance(idx_or_name, str) else idx_or_name
        return R @ (pts[idx] - origin)

    iod_px = abs(fp(L_INNER_EYE)[0] - fp(R_INNER_EYE)[0])
    if iod_px <= 0:
        return {"engine": "phi", "version": 2, "ok": False, "error": "invalid_iod"}
    px_per_mm = iod_px / IOD_BASELINE_MM

    # ── Anchor coordinates (canonical x=horizontal, y=vertical/up) ────────
    # Vertical
    mesh_top_y      = fp(FOREHEAD)[1]
    glabella_y      = fp("glabella")[1]
    subnasale_y     = fp("subnasale")[1]
    stomion_y       = fp(13)[1]
    menton_y        = fp(CHIN)[1]
    pupil_y_avg     = (fp(468)[1] + fp(473)[1]) / 2.0
    brow_y_avg      = (fp(107)[1] + fp(336)[1]) / 2.0
    upper_lip_top_y = fp(0)[1]
    lower_lip_bot_y = fp(17)[1]

    # Horizontal
    r_zygion_x   = fp(234)[0]
    l_zygion_x   = fp(454)[0]
    r_eye_out_x  = fp(33)[0]
    l_eye_out_x  = fp(263)[0]
    r_eye_in_x   = fp(133)[0]
    l_eye_in_x   = fp(362)[0]
    r_alar_x     = fp(98)[0]
    l_alar_x     = fp(327)[0]
    r_mouth_x    = fp(61)[0]
    l_mouth_x    = fp(291)[0]
    r_temple_x   = fp(127)[0]   # frontotemporale
    l_temple_x   = fp(356)[0]
    r_brow_in_x  = fp(107)[0]   # medial brow heads
    l_brow_in_x  = fp(336)[0]
    # Cupid's bow vermilion peaks
    r_cupid_x    = fp(37)[0]
    l_cupid_x    = fp(267)[0]

    face_width_px         = abs(l_zygion_x - r_zygion_x)
    forehead_width_px     = abs(l_temple_x - r_temple_x)
    eye_outer_to_outer_px = abs(l_eye_out_x - r_eye_out_x)
    inner_eye_dist_px     = abs(l_eye_in_x  - r_eye_in_x)
    nose_width_px         = abs(l_alar_x    - r_alar_x)
    mouth_width_px        = abs(l_mouth_x   - r_mouth_x)
    interbrow_gap_px      = abs(l_brow_in_x - r_brow_in_x)
    cupid_width_px        = abs(l_cupid_x   - r_cupid_x)
    r_eye_width_px        = abs(r_eye_in_x  - r_eye_out_x)
    l_eye_width_px        = abs(l_eye_out_x - l_eye_in_x)
    avg_eye_width_px      = (r_eye_width_px + l_eye_width_px) / 2.0
    pupil_distance_px     = abs(fp(468)[0] - fp(473)[0])

    # Trichion (#9 from v1, retained)
    trichion_used = "mediapipe_mesh_top"
    if hairline_mm_above_mesh_top and hairline_mm_above_mesh_top > 0:
        offset_mm = min(float(hairline_mm_above_mesh_top), 60.0)
        trichion_y = mesh_top_y + offset_mm * px_per_mm
        trichion_used = "foundation_hairline_estimator"
        if offset_mm < float(hairline_mm_above_mesh_top):
            trichion_used += "_capped60mm"
    else:
        trichion_y = mesh_top_y

    face_length_px       = abs(menton_y - trichion_y)
    forehead_third_px    = abs(brow_y_avg - trichion_y)
    midface_third_px     = abs(subnasale_y - brow_y_avg)
    lower_third_px       = abs(menton_y - subnasale_y)
    nose_length_px       = abs(subnasale_y - glabella_y)
    pupil_to_stomion_px  = abs(stomion_y - pupil_y_avg)
    stomion_to_chin_px   = abs(menton_y - stomion_y)
    pupil_to_chin_px     = abs(menton_y - pupil_y_avg)
    trichion_to_pupil_px = abs(pupil_y_avg - trichion_y)
    lip_height_px        = abs(lower_lip_bot_y - upper_lip_top_y)

    # Iris size feed (#15)
    iris_dia_px = None
    if iris_info and isinstance(iris_info, dict):
        rr = iris_info.get("right_radius_px") or 0
        lr = iris_info.get("left_radius_px") or 0
        if rr and lr:
            iris_dia_px = (rr + lr)    # diameter = 2 × avg radius

    # Eyebrow peak position (#13). Right brow = 70 (outer), 105 (peak), 107 (inner).
    # Position 0 = inner, 1 = outer.
    def _brow_peak_pos(inner_idx: int, peak_idx: int, outer_idx: int) -> float:
        ix = fp(inner_idx)[0]; ox = fp(outer_idx)[0]; px_ = fp(peak_idx)[0]
        span = abs(ox - ix)
        if span < DENOM_FLOOR_PX: return 0.0
        return abs(px_ - ix) / span
    brow_pos_r = _brow_peak_pos(107, 105, 70)
    brow_pos_l = _brow_peak_pos(336, 334, 300)
    brow_pos_avg = (brow_pos_r + brow_pos_l) / 2.0

    # Age & ethnicity resolution
    g_norm = (gender or "U").upper()
    if g_norm not in ("M", "F", "U"): g_norm = "U"
    eth_norm = (ethnicity or "U").lower()
    if eth_norm not in ("caucasian", "east_asian", "south_asian", "african", "u"):
        eth_norm = "u"
    age_band, age_mods = _age_band(age)

    # ── Build ratios ───────────────────────────────────────────────────────
    ratios: list[dict] = []
    skipped: list[dict] = []

    def add(name: str, num_px: float, den_px: float):
        db = RATIO_DB.get(name)
        if not db:
            return
        target = _resolve_target(name, g_norm, eth_norm, age_mods)
        if target is None or target <= 0:
            return
        if num_px <= 0:
            skipped.append({"name": name, "reason": "non_positive_numerator"})
            return
        if den_px < DENOM_FLOOR_PX:        # #19
            skipped.append({"name": name, "reason": "denominator_below_floor",
                            "denominator_px": round(float(den_px), 2)})
            return
        actual = num_px / den_px
        score = _phi_score(actual, target)
        sigma_r = _ratio_uncertainty(num_px, den_px, actual)        # #18
        score_lo = _phi_score(actual + sigma_r, target)
        score_hi = _phi_score(actual - sigma_r, target)
        ratios.append({
            "name":          name,
            "region":        db["r"],
            "actual":        round(actual, 4),
            "target":        round(target, 4),
            "deviation_pct": round((actual - target) / target * 100, 2),
            "score":         score,
            "weight":        db["w"],
            "ci_low":        round(min(score_lo, score_hi), 1),
            "ci_high":       round(max(score_lo, score_hi), 1),
            "ratio_sigma":   round(sigma_r, 4),
            "numerator_mm":   round(num_px / px_per_mm, 1),
            "denominator_mm": round(den_px / px_per_mm, 1),
            "narrative":     _render_narrative(name, actual, target),
        })

    # FACE
    add("face_length_to_width",         face_length_px,        face_width_px)
    add("face_width_to_length_inverse", face_width_px,         face_length_px)
    add("face_width_to_mouth_width",    face_width_px,         mouth_width_px)
    add("forehead_w_to_face_w",         forehead_width_px,     face_width_px)
    add("forehead_third_to_total",      forehead_third_px,     face_length_px)
    add("midface_third_to_total",       midface_third_px,      face_length_px)
    add("lower_third_to_total",         lower_third_px,        face_length_px)

    # EYES
    add("outer_to_outer_over_inner",    eye_outer_to_outer_px, inner_eye_dist_px)
    add("inner_eye_dist_eq_eye_width",  inner_eye_dist_px,     avg_eye_width_px)
    add("outer_eye_dist_to_mouth_w",    eye_outer_to_outer_px, mouth_width_px)
    add("pupil_dist_to_outer_dist",     pupil_distance_px,     eye_outer_to_outer_px)
    add("eye_width_to_nose_width",      avg_eye_width_px,      nose_width_px)
    if iris_dia_px and iris_dia_px > 0:
        # iris × φ should equal eye width  ⇒ ratio of (iris × φ) to eye_width = 1
        add("iris_phi_to_eye_width",    iris_dia_px * PHI,     avg_eye_width_px)
    else:
        skipped.append({"name": "iris_phi_to_eye_width", "reason": "iris_data_unavailable"})

    # NOSE
    add("nose_length_to_width",         nose_length_px,        nose_width_px)
    add("mouth_w_to_nose_w",            mouth_width_px,        nose_width_px)
    add("nose_width_eq_inner_eye",      nose_width_px,         inner_eye_dist_px)
    add("interbrow_gap_eq_nose_width",  interbrow_gap_px,      nose_width_px)

    # MOUTH
    add("mouth_width_to_lip_height",    mouth_width_px,        lip_height_px)
    add("lower_third_to_lip_height",    lower_third_px,        lip_height_px)
    add("mouth_w_to_iris_dist",         mouth_width_px,        pupil_distance_px)
    add("smile_w_to_face_w",            mouth_width_px,        face_width_px)
    if cupid_width_px > 0:
        add("philtrum_w_to_mouth_w",    cupid_width_px,        mouth_width_px)

    # VERTICAL
    add("trichion_to_pupil_over_pupil_to_stomion", trichion_to_pupil_px, pupil_to_stomion_px)
    add("pupil_to_stomion_over_stomion_to_chin",   pupil_to_stomion_px,  stomion_to_chin_px)
    add("trichion_to_pupil_over_pupil_to_chin",    trichion_to_pupil_px, pupil_to_chin_px)

    # HORIZONTAL fifths (Leonardo)
    add("face_w_over_eye_w",            face_width_px,         avg_eye_width_px)
    add("inner_eye_dist_over_eye_width", inner_eye_dist_px,    avg_eye_width_px)

    # BROW peak (#13) — ratio name is "brow_peak_position", numerator is the
    # actual position (already a 0..1 fraction); we encode it via a dummy
    # denominator of 1 unit so the standard add() math holds.
    if brow_pos_avg > 0:
        # bypass add() since this is a fraction, not a px ratio
        db = RATIO_DB["brow_peak_position"]
        target = _resolve_target("brow_peak_position", g_norm, eth_norm, age_mods)
        score = _phi_score(brow_pos_avg, target)
        ratios.append({
            "name": "brow_peak_position",
            "region": db["r"],
            "actual": round(brow_pos_avg, 4),
            "target": round(target, 4),
            "deviation_pct": round((brow_pos_avg - target) / target * 100, 2),
            "score": score,
            "weight": db["w"],
            "ci_low": score, "ci_high": score, "ratio_sigma": 0.0,
            "numerator_mm": None, "denominator_mm": None,
            "left_position": round(brow_pos_l, 3),
            "right_position": round(brow_pos_r, 3),
            "narrative": _render_narrative("brow_peak_position", brow_pos_avg, target),
        })

    # ── Engine-1 cross-validation (#8) ─────────────────────────────────────
    engine1_context = {}
    if anthropometry_result and isinstance(anthropometry_result, dict):
        fs7 = anthropometry_result.get("face_shape_7") or {}
        face_shape = fs7.get("shape") if isinstance(fs7, dict) else None
        cls = anthropometry_result.get("classifications") or {}
        facial_idx = cls.get("face_shape_length_class")
        cidx = (anthropometry_result.get("classical_indices") or {})
        martin_class = cidx.get("facial_index_class") if isinstance(cidx, dict) else None
        engine1_context = {
            "face_shape":          face_shape,
            "length_class":        facial_idx,
            "facial_index_class":  martin_class,
        }
        leptoprosopic = (martin_class in ("leptoprosopic", "hyperleptoprosopic")
                         or facial_idx in ("long", "very_long"))
        long_shape = face_shape in ("oblong", "rectangle")
        if leptoprosopic or long_shape:
            for r in ratios:
                if r["name"] == "face_length_to_width" and r["deviation_pct"] > 5:
                    r["contextual_note"] = (
                        f"Naturally elongated face ({face_shape or facial_idx}); "
                        "high length/width ratio is phenotype-typical, not a defect."
                    )
                    r["score"] = round(min(100.0, r["score"] + 25.0), 1)   # mercy bump
                    r["weight"] *= 0.5

    # ── Region scores (weighted) ───────────────────────────────────────────
    region_scores: dict[str, dict] = {}
    for region in ("face", "eyes", "nose", "mouth", "vertical", "horizontal", "brows"):
        rs = [r for r in ratios if r["region"] == region]
        if not rs: continue
        wsum = sum(r["weight"] for r in rs) or 1.0
        score = sum(r["score"] * r["weight"] for r in rs) / wsum
        region_scores[region] = {
            "score":         round(score, 1),
            "rating":        _classify_region(score),
            "n_ratios":      len(rs),
            "weight_total":  round(wsum, 2),
        }

    # Vertical thirds detail
    if face_length_px > 0:
        thirds = {
            "forehead_third_pct": round(forehead_third_px / face_length_px * 100, 1),
            "midface_third_pct":  round(midface_third_px  / face_length_px * 100, 1),
            "lower_third_pct":    round(lower_third_px    / face_length_px * 100, 1),
        }
        eq_dev = sum(abs(v - 33.33) for v in thirds.values()) / 3.0
        thirds["equality_score"] = round(max(0.0, 100.0 - eq_dev * 4.0), 1)
        dom = max(forehead_third_px, midface_third_px, lower_third_px)
        thirds["dominant_third"] = ("forehead" if dom == forehead_third_px else
                                    "midface"  if dom == midface_third_px else
                                    "lower_face")
    else:
        thirds = {"error": "invalid_face_length"}

    # Horizontal fifths detail
    if face_width_px > 0 and avg_eye_width_px > 0:
        fifths_px = [
            abs(r_eye_out_x - r_zygion_x), r_eye_width_px, inner_eye_dist_px,
            l_eye_width_px, abs(l_zygion_x - l_eye_out_x),
        ]
        fifths_pct = [round(p / face_width_px * 100, 1) for p in fifths_px]
        eq_dev = sum(abs(p - 20.0) for p in fifths_pct) / 5.0
        fifths = {
            "fifth_widths_pct": fifths_pct,
            "ideal_pct":        20.0,
            "equality_score":   round(max(0.0, 100.0 - eq_dev * 4.0), 1),
            "labels":           ["right_periphery", "right_eye", "inter_ocular",
                                 "left_eye", "left_periphery"],
        }
    else:
        fifths = {"error": "invalid_face_or_eye_width"}

    # ── Bilateral phi (#7) ─────────────────────────────────────────────────
    midline_x = (r_eye_in_x + l_eye_in_x) / 2.0
    def _half_score(side: str) -> dict:
        # restrict ratios that touch only one side; reuse the symmetric ratios
        # but apply per-side widths
        eye_w   = r_eye_width_px if side == "right" else l_eye_width_px
        zyg_x   = r_zygion_x     if side == "right" else l_zygion_x
        out_x   = r_eye_out_x    if side == "right" else l_eye_out_x
        in_x    = r_eye_in_x     if side == "right" else l_eye_in_x
        mouth_x = r_mouth_x      if side == "right" else l_mouth_x
        alar_x  = r_alar_x       if side == "right" else l_alar_x
        half_face_w = abs(zyg_x - midline_x)
        half_mouth  = abs(mouth_x - midline_x)
        half_nose   = abs(alar_x - midline_x)
        scores = []
        if half_mouth > DENOM_FLOOR_PX and half_nose > DENOM_FLOOR_PX:
            scores.append(_phi_score(half_mouth/half_nose, PHI))
        if eye_w > DENOM_FLOOR_PX and half_nose > DENOM_FLOOR_PX:
            scores.append(_phi_score(eye_w/half_nose, 1.0))
        if half_face_w > DENOM_FLOOR_PX and half_mouth > DENOM_FLOOR_PX:
            scores.append(_phi_score(half_face_w/half_mouth, 1.5))
        if not scores:
            return {"score": 0.0, "n_ratios": 0}
        return {"score": round(sum(scores)/len(scores), 1), "n_ratios": len(scores)}
    bilateral = {
        "left":   _half_score("left"),
        "right":  _half_score("right"),
    }
    bilateral["difference"] = round(abs(bilateral["left"]["score"] -
                                        bilateral["right"]["score"]), 1)
    bilateral["dominant_side"] = ("left" if bilateral["left"]["score"] >
                                  bilateral["right"]["score"] else "right")

    # ── Marquardt decagon (#9) ─────────────────────────────────────────────
    deca_pts = {
        "trichion":   np.array([midline_x, trichion_y]),
        "menton":     np.array([midline_x, menton_y]),
        "r_zygion":   np.array([r_zygion_x, fp(234)[1]]),
        "l_zygion":   np.array([l_zygion_x, fp(454)[1]]),
        "r_eye_out":  np.array([r_eye_out_x, fp(33)[1]]),
        "l_eye_out":  np.array([l_eye_out_x, fp(263)[1]]),
        "r_mouth":    np.array([r_mouth_x, fp(61)[1]]),
        "l_mouth":    np.array([l_mouth_x, fp(291)[1]]),
        "nose_tip":   fp("nose_tip")[:2],
        "subnasale":  np.array([midline_x, subnasale_y]),
    }
    decagon = _decagon_score(deca_pts, face_width_px, face_length_px)

    # ── Profile phi (#4) ───────────────────────────────────────────────────
    profile = _profile_phi(side_landmarks, image_w, image_h)

    # ── Weighted overall score (#6) ────────────────────────────────────────
    if ratios:
        wsum = sum(r["weight"] for r in ratios) or 1.0
        ratio_total = sum(r["score"] * r["weight"] for r in ratios) / wsum
    else:
        ratio_total = 0.0
    # Weighted combination: 22 ratios (60%), thirds (15%), fifths (15%),
    # decagon (10%) — decagon kept low-weight since it is a coarse estimate.
    overall_components = [(ratio_total, 0.60)]
    if isinstance(thirds, dict) and "equality_score" in thirds:
        overall_components.append((thirds["equality_score"], 0.15))
    if isinstance(fifths, dict) and "equality_score" in fifths:
        overall_components.append((fifths["equality_score"], 0.15))
    if decagon.get("ok"):
        overall_components.append((decagon["score"], 0.10))
    w_sum = sum(w for _, w in overall_components) or 1.0
    overall = sum(s * w for s, w in overall_components) / w_sum

    # Confidence shaving for non-frontal faces
    if frontal_confidence == "low":
        overall *= 0.85

    # Top / bottom features (only weighted ratios, not bilateral noise)
    sorted_r = sorted(ratios, key=lambda r: r["score"], reverse=True)
    top_3 = [{"name": r["name"], "region": r["region"], "score": r["score"],
              "actual": r["actual"], "target": r["target"]} for r in sorted_r[:3]]
    bot_3 = [{"name": r["name"], "region": r["region"], "score": r["score"],
              "actual": r["actual"], "target": r["target"],
              "deviation_pct": r["deviation_pct"]} for r in sorted_r[-3:][::-1]]

    return {
        "engine":             "phi",
        "version":            2,
        "ok":                 True,
        "phi_constant":       round(PHI, 6),
        "frame":              "canonical_3d_pose_corrected",
        "iod_baseline_mm":    IOD_BASELINE_MM,
        "px_per_mm":          round(px_per_mm, 3),
        "trichion_source":    trichion_used,
        "yaw_deg":            round(yaw_deg, 2),
        "frontal_view_confidence": frontal_confidence,
        "inputs": {
            "gender":         g_norm,
            "ethnicity":      eth_norm,
            "age":            age,
            "age_band":       age_band,
            "ear_landmarks":  "unmeasured_mediapipe_lacks_ear",
        },
        "ratios":             ratios,
        "skipped_ratios":     skipped,
        "region_scores":      region_scores,
        "vertical_thirds":    thirds,
        "horizontal_fifths":  fifths,
        "bilateral_phi":      bilateral,
        "marquardt_decagon":  decagon,
        "profile_phi":        profile or {"ok": False, "reason": "no_side_landmarks_provided"},
        "engine1_cross_validation": engine1_context or None,
        "overall_phi_score":  round(overall, 1),
        "classification":     _classify_overall(overall),
        "top_3_phi_aligned":  top_3,
        "top_3_off_phi":      bot_3,
        "interpretation":     _interpret(overall, region_scores, thirds, fifths,
                                         bilateral, decagon, frontal_confidence,
                                         g_norm, eth_norm, age_band),
    }


def _interpret(overall, regions, thirds, fifths, bilateral, decagon,
               frontal_conf, gender, eth, age_band) -> dict:
    out: list[str] = []
    out.append(f"Overall phi conformance: {overall:.1f}/100 ({_classify_overall(overall)}).")
    out.append(f"Inputs: gender={gender}, ethnicity={eth}, age_band={age_band}.")
    if frontal_conf == "low":
        out.append("⚠ Pose was non-strictly frontal (yaw > 8°); score has been "
                   "discounted by 15%. Re-shoot a true frontal for best accuracy.")
    if regions:
        best_r  = max(regions, key=lambda k: regions[k]["score"])
        worst_r = min(regions, key=lambda k: regions[k]["score"])
        out.append(f"Most phi-aligned region: {best_r} "
                   f"({regions[best_r]['score']:.0f}/100). "
                   f"Least: {worst_r} ({regions[worst_r]['score']:.0f}/100).")
    if isinstance(thirds, dict) and "equality_score" in thirds:
        out.append(f"Vertical thirds: forehead {thirds['forehead_third_pct']}%, "
                   f"midface {thirds['midface_third_pct']}%, "
                   f"lower {thirds['lower_third_pct']}% — "
                   f"{thirds.get('dominant_third','?')}-dominant "
                   f"(equality {thirds['equality_score']:.0f}/100).")
    if isinstance(fifths, dict) and "equality_score" in fifths:
        out.append(f"Horizontal fifths equality: {fifths['equality_score']:.0f}/100.")
    if bilateral and bilateral.get("left", {}).get("n_ratios"):
        out.append(f"Bilateral phi — L: {bilateral['left']['score']:.0f}/100, "
                   f"R: {bilateral['right']['score']:.0f}/100, "
                   f"dominant {bilateral['dominant_side']} "
                   f"(Δ {bilateral['difference']:.0f}).")
    if decagon.get("ok"):
        out.append(f"Marquardt decagon fit: {decagon['score']:.0f}/100 "
                   f"(mean normalized vertex distance {decagon['mean_norm_dist']}).")
    return {"summary": " ".join(out), "highlights": out}

"""
Engine 1: Anthropometry  (v2 — pose-corrected 3D, full Farkas suite)

Research-grade facial anthropometry computed in a canonical 3D face frame
(pose-corrected, identical frame to Engine 2 Symmetry).

Output blocks:
  • measurements_px / measurements_mm  — 22 raw distances
  • depth_projections_mm               — 5 protrusion measurements (z-axis)
  • angles_deg                         — 7 angular measurements
  • ratios                             — 13 dimensionless ratios
  • classical_indices                  — Facial, Nasal, Mandibular, Mouth, Orbital
  • percentiles                        — vs Farkas adult norms (Z → percentile)
  • classifications                    — 9 categorical labels
  • face_shape_7                       — definitive 7-shape verdict
  • summary                            — composite face-shape & key flags

Scale anchor: inter-ocular distance (IOD) baseline = 32mm.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np

# ── Mediapipe Face Mesh landmark indices ────────────────────────────────────
LM = {
    "forehead_top":      10,
    "glabella":          9,
    "nose_root":         168,
    "nose_tip":          1,
    "subnasale":         2,
    "upper_lip_top":     0,
    "lower_lip_bottom":  17,
    "chin_bottom":       152,

    "right_cheek":       234,
    "left_cheek":        454,
    "right_jaw":         172,
    "left_jaw":          397,
    "right_temple":      127,
    "left_temple":       356,

    "r_eye_outer":       33,
    "r_eye_inner":       133,
    "l_eye_inner":       362,
    "l_eye_outer":       263,
    "r_eye_top":         159,
    "r_eye_bottom":      145,
    "l_eye_top":         386,
    "l_eye_bottom":      374,

    "r_brow_inner":      107,
    "r_brow_peak":       105,
    "r_brow_outer":      70,
    "l_brow_inner":      336,
    "l_brow_peak":       334,
    "l_brow_outer":      300,

    "r_alar":            98,
    "l_alar":            327,
    "nose_bridge_mid":   197,

    "r_mouth_corner":    61,
    "l_mouth_corner":    291,
    "philtrum_top":      164,
    "upper_lip_inner":   13,
    "lower_lip_inner":   14,
}

IOD_BASELINE_MM = 32.0

# Frame anchors (must match Engine 2 for cross-engine consistency)
R_INNER_EYE = 133
L_INNER_EYE = 362
FOREHEAD    = 10
CHIN        = 152

# ── Farkas adult norms (pooled mixed-population means; mm) ──────────────────
# References: Farkas 1994 (Anthropometry of the Head and Face), 2nd ed.;
# normative ranges aggregated across published populations.
#
# IMPORTANT: Mediapipe Face Mesh does NOT include the trichion (hairline) — its
# topmost landmark (#10) sits inside the visible forehead, not at the hair
# line. So `forehead_height` here = glabella → visible mesh-top ≈ 30-35mm
# (NOT the classical Farkas trichion-nasion measurement of ~62mm). The norm
# below reflects what Mediapipe actually captures.
# Same applies to `forehead_width`: landmarks 127/356 are frontotemporale,
# not the upper-forehead width — so the norm below is widened accordingly.
FARKAS_NORMS_MM = {
    "face_height_total":   (148.0, 9.0),
    "face_width_zygion":   (130.0, 7.0),
    "forehead_height":     (32.0, 6.0),    # glabella → visible forehead top
    "midface_height":      (62.0, 5.0),
    "lower_face_height":   (62.0, 5.0),
    "jaw_width":           (97.0, 6.0),
    "forehead_width":      (128.0, 8.0),   # frontotemporale-to-frontotemporale
    "nose_length":         (50.0, 4.0),
    "nose_width_alar":     (33.0, 3.0),
    "mouth_width":         (52.0, 4.0),
    "upper_lip_thickness": (8.0, 2.0),
    "lower_lip_thickness": (10.0, 2.0),
}


# ── Geometry helpers ────────────────────────────────────────────────────────
def _build_face_frame(get3d):
    """Orthonormal canonical face frame (same construction as Engine 2)."""
    r_eye    = get3d(R_INNER_EYE)
    l_eye    = get3d(L_INNER_EYE)
    chin     = get3d(CHIN)
    forehead = get3d(FOREHEAD)

    origin = (r_eye + l_eye) / 2.0
    x_axis = l_eye - r_eye
    x_axis /= (np.linalg.norm(x_axis) or 1.0)
    y_tent = forehead - chin
    y_axis = y_tent - np.dot(y_tent, x_axis) * x_axis
    y_axis /= (np.linalg.norm(y_axis) or 1.0)
    z_axis = np.cross(x_axis, y_axis)
    z_axis /= (np.linalg.norm(z_axis) or 1.0)
    R = np.vstack([x_axis, y_axis, z_axis])
    return origin, R


def _angle_between(v1: np.ndarray, v2: np.ndarray) -> float:
    """Angle between two vectors in degrees (0–180)."""
    n1 = np.linalg.norm(v1) or 1.0
    n2 = np.linalg.norm(v2) or 1.0
    cos_t = float(np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0))
    return math.degrees(math.acos(cos_t))


def _signed_tilt_deg(v: np.ndarray, axis_idx: int = 0) -> float:
    """Signed tilt of vector v relative to chosen axis (in 2D x/y plane).
    Positive = counter-clockwise from axis. axis_idx 0=x, 1=y.
    """
    if axis_idx == 0:
        return math.degrees(math.atan2(-v[1], v[0]))   # y inverted (face frame +y is up)
    return math.degrees(math.atan2(v[0], -v[1]))


def _percentile_from_z(z: float) -> float:
    """Convert Z-score → percentile (0–100) via standard normal CDF."""
    return round(0.5 * (1.0 + math.erf(z / math.sqrt(2.0))) * 100.0, 1)


def _classify(value: float, bands: list[tuple[float, str]]) -> str:
    for upper, label in bands:
        if value <= upper:
            return label
    return bands[-1][1]


# ── Classical anthropometric index classifiers ──────────────────────────────
def _facial_index_class(idx: float) -> str:
    """Martin-Saller facial index classification."""
    if idx < 80:    return "hypereuryprosopic"
    if idx < 85:    return "euryprosopic"
    if idx < 90:    return "mesoprosopic"
    if idx < 95:    return "leptoprosopic"
    return "hyperleptoprosopic"


def _nasal_index_class(idx: float) -> str:
    """Topinard nasal index classification."""
    if idx < 70:    return "leptorrhine"
    if idx < 85:    return "mesorrhine"
    return "platyrrhine"


# ── 7-Shape Classifier ──────────────────────────────────────────────────────
def _classify_face_shape_7(forehead_w, cheek_w, jaw_w, face_h) -> tuple[str, str]:
    """Return (shape, reasoning). One of:
       oval | round | square | rectangle | oblong | heart | diamond | triangle
    """
    L_W = face_h / cheek_w if cheek_w else 0.0       # length-to-width
    f_c = forehead_w / cheek_w if cheek_w else 0.0
    j_c = jaw_w / cheek_w if cheek_w else 0.0
    f_j = forehead_w / jaw_w if jaw_w else 0.0

    # Long faces first
    if L_W >= 1.50:
        if 0.85 <= j_c <= 1.05 and 0.85 <= f_c <= 1.05:
            return "rectangle", "Long face with parallel sides (forehead ≈ cheek ≈ jaw)."
        return "oblong", "Long face length (>1.5×) with tapered or curved sides."

    # Heart: forehead is widest, jaw narrows
    if f_c >= 0.95 and j_c <= 0.85 and f_j >= 1.10:
        return "heart", "Forehead wider than cheekbones with a narrowing jaw."

    # Triangle (pear): jaw is widest
    if j_c >= 0.95 and f_c <= 0.88 and f_j <= 0.90:
        return "triangle", "Jaw is the widest section, forehead narrows."

    # Diamond: cheekbones widest with both forehead AND jaw narrower
    if f_c <= 0.85 and j_c <= 0.80 and L_W >= 1.20:
        return "diamond", "Cheekbones project widest; forehead and jaw both narrow."

    # Round vs Square vs Oval (cheekbones widest or all similar)
    if L_W <= 1.10:
        if 0.88 <= j_c <= 1.02:
            return "square", "Equal length and width with strong jawline."
        return "round", "Length ≈ width with softer jaw."

    if 1.10 < L_W < 1.45:
        # The classic balanced face
        if j_c <= 0.85 and f_c >= 0.85:
            return "oval", "Length 1.1–1.45× width with cheekbones widest and tapering jaw."
        if 0.85 < j_c <= 1.00:
            return "square", "Slightly oblong with strong jawline relative to cheekbones."
        return "oval", "Balanced proportions with cheekbones as widest section."

    return "oval", "Default — proportions fall within balanced oval range."


# ═══════════════════════════════════════════════════════════════════════════
# Main engine
# ═══════════════════════════════════════════════════════════════════════════
def run(landmarks_norm: list[tuple[float, float, float]],
        image_width: int,
        image_height: int) -> dict:
    if not landmarks_norm or len(landmarks_norm) < 468:
        return {"engine": "anthropometry", "ok": False, "error": "insufficient_landmarks"}

    W, H = float(image_width), float(image_height)

    def get3d(idx: int) -> np.ndarray:
        lm = landmarks_norm[idx]
        return np.array([lm[0] * W, lm[1] * H, lm[2] * W], dtype=np.float64)

    # ── 1. Canonical 3D face frame ─────────────────────────────────────────
    origin, R = _build_face_frame(get3d)

    def f(name: str) -> np.ndarray:
        """Return a named landmark in canonical face-frame 3D coordinates."""
        return R @ (get3d(LM[name]) - origin)

    # IOD measured in canonical frame
    iod_px = float(np.linalg.norm(f("l_eye_inner") - f("r_eye_inner")))
    if iod_px < 5:
        return {"engine": "anthropometry", "ok": False, "error": "iod_too_small"}
    px_per_mm = iod_px / IOD_BASELINE_MM

    # 2D distance helper (in canonical x-y plane, ignoring depth)
    def d2(a: str, b: str) -> float:
        pa, pb = f(a), f(b)
        return float(math.hypot(pa[0] - pb[0], pa[1] - pb[1]))

    # ── 2. Raw measurements (now pose-corrected) ───────────────────────────
    M = {
        "face_height_total":     d2("forehead_top",   "chin_bottom"),
        "forehead_height":       d2("forehead_top",   "glabella"),
        "midface_height":        d2("glabella",       "subnasale"),
        "lower_face_height":     d2("subnasale",      "chin_bottom"),
        "nose_length":           d2("nose_root",      "subnasale"),
        "nose_tip_to_chin":      d2("nose_tip",       "chin_bottom"),
        "upper_lip_to_chin":     d2("upper_lip_top",  "chin_bottom"),
        "lip_to_chin":           d2("lower_lip_bottom", "chin_bottom"),
        "upper_lip_thickness":   d2("upper_lip_top",  "upper_lip_inner"),
        "lower_lip_thickness":   d2("lower_lip_inner", "lower_lip_bottom"),

        "face_width_zygion":     d2("right_cheek",    "left_cheek"),
        "jaw_width":             d2("right_jaw",      "left_jaw"),
        "forehead_width":        d2("right_temple",   "left_temple"),
        "iod_inner":             iod_px,
        "outer_eye_span":        d2("r_eye_outer",    "l_eye_outer"),
        "right_eye_width":       d2("r_eye_outer",    "r_eye_inner"),
        "left_eye_width":        d2("l_eye_inner",    "l_eye_outer"),
        "right_eye_height":      d2("r_eye_top",      "r_eye_bottom"),
        "left_eye_height":       d2("l_eye_top",      "l_eye_bottom"),
        "nose_width_alar":       d2("r_alar",         "l_alar"),
        "mouth_width":           d2("r_mouth_corner", "l_mouth_corner"),
        "brow_distance_inner":   d2("r_brow_inner",   "l_brow_inner"),
    }

    measurements_px = {k: round(v, 1) for k, v in M.items()}
    measurements_mm = {k: round(v / px_per_mm, 1) for k, v in M.items()}

    # ── 3. Depth (z-axis) projections in mm ────────────────────────────────
    # In canonical frame, +z = toward camera. Reference plane = inner-eye plane (z=0).
    def z_mm(name: str) -> float:
        return round(f(name)[2] / px_per_mm, 1)

    # forehead slope angle: vector glabella → forehead_top in (y,z) plane.
    # Face frame: +y points up (chin → forehead), +z points toward camera.
    # angle = 0  → forehead is vertical (rises straight up from glabella)
    # angle > 0 → forehead protrudes forward (top is forward of glabella)
    # angle < 0 → forehead recedes (top is behind glabella)
    fh_top = f("forehead_top")
    glab   = f("glabella")
    dz = fh_top[2] - glab[2]
    dy = fh_top[1] - glab[1]   # positive (forehead is above glabella in face frame)
    forehead_slope_deg = math.degrees(math.atan2(dz, dy or 1e-9))

    depth_projections_mm = {
        "nose_tip_projection":   z_mm("nose_tip"),     # how far nose tip sits forward of eye plane
        "chin_projection":       z_mm("chin_bottom"),  # forward (+) or recessed (-)
        "brow_ridge_projection": round(((f("r_brow_inner")[2] + f("l_brow_inner")[2]) / 2) / px_per_mm, 1),
        "cheekbone_projection":  round(((f("right_cheek")[2]  + f("left_cheek")[2])  / 2) / px_per_mm, 1),
        "subnasale_projection":  z_mm("subnasale"),
    }

    # ── 4. Angular measurements (degrees) ──────────────────────────────────
    # 4.1 Jaw angle (gonial) — averaged left & right
    def jaw_angle_side(jaw_name: str, temple_name: str) -> float:
        gonion = f(jaw_name)
        v_ramus = f(temple_name) - gonion        # toward temple/ear
        v_body  = f("chin_bottom") - gonion      # toward menton
        return _angle_between(v_ramus, v_body)
    jaw_angle = (jaw_angle_side("right_jaw", "right_temple") +
                 jaw_angle_side("left_jaw",  "left_temple"))  / 2.0

    # 4.2 Chin pointedness — angle at chin_bottom formed by jaw curves
    chin = f("chin_bottom")
    v_rj = f("right_jaw") - chin
    v_lj = f("left_jaw")  - chin
    chin_angle = _angle_between(v_rj, v_lj)

    # 4.3 Canthal tilt — angle of inner→outer eye corner relative to horizontal.
    # Face frame: +y points UP (chin → forehead). For both eyes we want
    # POSITIVE = outer corner higher than inner ("almond" / "cat" eye).
    def canthal_tilt_side(inner: str, outer: str) -> float:
        v = f(outer) - f(inner)
        # |v[0]| is the horizontal span (works for both sides regardless of
        # x-direction). v[1] is signed vertical: positive = outer higher.
        return math.degrees(math.atan2(v[1], abs(v[0]) or 1e-9))
    canthal_tilt = (canthal_tilt_side("r_eye_inner", "r_eye_outer") +
                    canthal_tilt_side("l_eye_inner", "l_eye_outer")) / 2.0

    # 4.4 Nose tip projection angle — in y-z (sagittal) plane, subnasale → nose_tip
    v_nose = f("nose_tip") - f("subnasale")
    # Angle between this vector and the +z (forward) axis, in y-z plane
    nose_tip_angle = math.degrees(math.atan2(-v_nose[1], v_nose[2] or 1e-9))
    # 90° = pointing straight forward; >90° = upturned; <90° = drooping

    # 4.5 Forehead slope (already computed above)

    # 4.6 Lip commissure tilt — angle from upper_lip_top to mouth corners.
    # Positive = corners higher than philtrum top (upturned/smiling at rest).
    # Negative = corners lower than philtrum top (downturned/frowning at rest).
    def commissure_tilt_side(corner: str) -> float:
        v = f(corner) - f("upper_lip_top")
        return math.degrees(math.atan2(v[1], abs(v[0]) or 1e-9))
    lip_commissure_tilt = (commissure_tilt_side("r_mouth_corner") +
                           commissure_tilt_side("l_mouth_corner")) / 2.0

    # 4.7 Brow arch angle — three-point angle at brow_peak
    def brow_arch_side(inner: str, peak: str, outer: str) -> float:
        p = f(peak)
        return _angle_between(f(inner) - p, f(outer) - p)
    brow_arch_angle = (brow_arch_side("r_brow_inner", "r_brow_peak", "r_brow_outer") +
                       brow_arch_side("l_brow_inner", "l_brow_peak", "l_brow_outer")) / 2.0

    angles_deg = {
        "jaw_angle_gonial":      round(jaw_angle, 1),
        "chin_pointedness":      round(chin_angle, 1),
        "canthal_tilt":          round(canthal_tilt, 1),
        "nose_tip_projection":   round(nose_tip_angle, 1),
        "forehead_slope":        round(forehead_slope_deg, 1),
        "lip_commissure_tilt":   round(lip_commissure_tilt, 1),
        "brow_arch_angle":       round(brow_arch_angle, 1),
    }

    # ── 5. Ratios ──────────────────────────────────────────────────────────
    def _r(num, den, places=3):
        return round(num / den, places) if den else 0.0

    ratios = {
        "face_length_to_width":       _r(M["face_height_total"], M["face_width_zygion"]),
        "jaw_to_face_width":          _r(M["jaw_width"],         M["face_width_zygion"]),
        "forehead_to_face_width":     _r(M["forehead_width"],    M["face_width_zygion"]),
        "third_upper":                _r(M["forehead_height"],   M["face_height_total"]),
        "third_middle":               _r(M["midface_height"],    M["face_height_total"]),
        "third_lower":                _r(M["lower_face_height"], M["face_height_total"]),
        "eye_spacing_to_eye_width":   _r(M["iod_inner"],         (M["right_eye_width"] + M["left_eye_width"]) / 2),
        "eye_span_to_face_width":     _r(M["outer_eye_span"],    M["face_width_zygion"]),
        "eye_aspect_ratio_avg":       _r((M["right_eye_height"] + M["left_eye_height"]) / 2,
                                         (M["right_eye_width"]  + M["left_eye_width"])  / 2),
        "nose_length_to_face":        _r(M["nose_length"],       M["face_height_total"]),
        "nose_width_to_mouth_width":  _r(M["nose_width_alar"],   M["mouth_width"]),
        "mouth_to_face_width":        _r(M["mouth_width"],       M["face_width_zygion"]),
        "lip_ratio_upper_to_lower":   _r(M["upper_lip_thickness"], M["lower_lip_thickness"]),
    }

    # ── 6. Classical anthropometric indices (×100 per convention) ──────────
    facial_idx = round(measurements_mm["face_height_total"] / measurements_mm["face_width_zygion"] * 100, 1) \
                 if measurements_mm["face_width_zygion"] else 0
    nasal_idx = round(measurements_mm["nose_width_alar"] / measurements_mm["nose_length"] * 100, 1) \
                if measurements_mm["nose_length"] else 0
    mandibular_idx = round(measurements_mm["jaw_width"] / measurements_mm["face_width_zygion"] * 100, 1) \
                     if measurements_mm["face_width_zygion"] else 0
    mouth_idx = round(measurements_mm["mouth_width"] / measurements_mm["face_width_zygion"] * 100, 1) \
                if measurements_mm["face_width_zygion"] else 0
    avg_eye_h = (measurements_mm["right_eye_height"] + measurements_mm["left_eye_height"]) / 2
    avg_eye_w = (measurements_mm["right_eye_width"]  + measurements_mm["left_eye_width"])  / 2
    orbital_idx = round(avg_eye_h / avg_eye_w * 100, 1) if avg_eye_w else 0

    classical_indices = {
        "facial_index":            facial_idx,
        "facial_index_class":      _facial_index_class(facial_idx),
        "nasal_index":             nasal_idx,
        "nasal_index_class":       _nasal_index_class(nasal_idx),
        "mandibular_index":        mandibular_idx,
        "mouth_index":             mouth_idx,
        "orbital_index":           orbital_idx,
    }

    # ── 7. Population percentiles vs Farkas norms ──────────────────────────
    percentiles = {}
    for key, (mean, sd) in FARKAS_NORMS_MM.items():
        if key not in measurements_mm:
            continue
        val = measurements_mm[key]
        z = (val - mean) / sd if sd else 0
        pct = _percentile_from_z(z)
        if pct >= 85:    band = "above_average"
        elif pct >= 60:  band = "high_typical"
        elif pct >= 40:  band = "typical"
        elif pct >= 15:  band = "low_typical"
        else:            band = "below_average"
        percentiles[key] = {
            "value_mm": val,
            "norm_mm": mean,
            "sd_mm": sd,
            "z_score": round(z, 2),
            "percentile": pct,
            "band": band,
        }

    # ── 8. Categorical classifications ─────────────────────────────────────
    classifications = {
        "face_shape_length_class": _classify(ratios["face_length_to_width"], [
            (1.10, "round_short"), (1.30, "oval"), (1.45, "long_oval"), (99.0, "long"),
        ]),
        "face_shape_jaw_class": _classify(ratios["jaw_to_face_width"], [
            (0.72, "tapered_heart"), (0.82, "oval"), (0.92, "square"), (99.0, "wide_jaw"),
        ]),
        "forehead_class": _classify(ratios["forehead_to_face_width"], [
            (0.78, "narrow"), (0.92, "balanced"), (99.0, "broad"),
        ]),
        "eye_spacing_class": _classify(ratios["eye_spacing_to_eye_width"], [
            (0.95, "close_set"), (1.10, "balanced"), (99.0, "wide_set"),
        ]),
        "eye_openness_class": _classify(ratios["eye_aspect_ratio_avg"], [
            (0.28, "narrow_hooded"), (0.38, "almond"), (99.0, "round_open"),
        ]),
        "lip_class": _classify(ratios["lip_ratio_upper_to_lower"], [
            (0.55, "fuller_lower"), (0.85, "balanced"), (1.20, "fuller_upper"), (99.0, "very_full_upper"),
        ]),
        "mouth_size_class": _classify(ratios["mouth_to_face_width"], [
            (0.36, "small_mouth"), (0.46, "medium_mouth"), (99.0, "wide_mouth"),
        ]),
        "nose_breadth_class": _classify(ratios["nose_width_to_mouth_width"], [
            (0.62, "narrow_nose"), (0.78, "balanced_nose"), (99.0, "wide_nose"),
        ]),
        "dominant_third": max(
            ("upper",  ratios["third_upper"]),
            ("middle", ratios["third_middle"]),
            ("lower",  ratios["third_lower"]),
            key=lambda kv: kv[1],
        )[0],
        # Angular classifications
        "jaw_angle_class": _classify(angles_deg["jaw_angle_gonial"], [
            (105, "sharp_strong"), (120, "defined"), (135, "rounded"), (180, "very_rounded"),
        ]),
        "canthal_tilt_class": _classify(angles_deg["canthal_tilt"], [
            (-2, "downturned"), (3, "neutral"), (8, "upturned_almond"), (90, "strongly_upturned"),
        ]),
        "lip_commissure_class": _classify(angles_deg["lip_commissure_tilt"], [
            (-3, "downturned_resting"), (3, "neutral_resting"), (90, "upturned_smiling_resting"),
        ]),
        "forehead_slope_class": _classify(angles_deg["forehead_slope"], [
            (-5, "receding"), (5, "vertical"), (90, "protruding"),
        ]),
        "brow_arch_class": _classify(angles_deg["brow_arch_angle"], [
            (155, "highly_arched"), (170, "softly_arched"), (180, "straight"),
        ]),
    }

    # ── 9. 7-Shape definitive face-shape verdict ───────────────────────────
    shape, reasoning = _classify_face_shape_7(
        measurements_mm["forehead_width"],
        measurements_mm["face_width_zygion"],
        measurements_mm["jaw_width"],
        measurements_mm["face_height_total"],
    )
    face_shape_7 = {
        "shape": shape,
        "reasoning": reasoning,
        "inputs_mm": {
            "forehead_width":   measurements_mm["forehead_width"],
            "cheekbone_width":  measurements_mm["face_width_zygion"],
            "jaw_width":        measurements_mm["jaw_width"],
            "face_height":      measurements_mm["face_height_total"],
        },
    }

    # ── 10. Summary ────────────────────────────────────────────────────────
    summary = {
        "face_shape_7":             shape,
        "face_shape_compound":      _compose_face_shape(classifications),
        "facial_index_class":       classical_indices["facial_index_class"],
        "nasal_index_class":        classical_indices["nasal_index_class"],
        "iod_mm_baseline":          IOD_BASELINE_MM,
        "measurements_count":       len(measurements_px),
        "depth_projections_count":  len(depth_projections_mm),
        "angles_count":             len(angles_deg),
        "ratios_count":             len(ratios),
        "indices_count":            5,
        "percentiles_count":        len(percentiles),
        "classifications_count":    len(classifications),
    }

    return {
        "engine": "anthropometry",
        "ok": True,
        "version": 2,
        "scale": {
            "iod_pixels": round(iod_px, 2),
            "iod_baseline_mm": IOD_BASELINE_MM,
            "px_per_mm": round(px_per_mm, 4),
            "frame": "canonical_3d_pose_corrected",
        },
        "measurements_px":      measurements_px,
        "measurements_mm":      measurements_mm,
        "depth_projections_mm": depth_projections_mm,
        "angles_deg":           angles_deg,
        "ratios":               ratios,
        "classical_indices":    classical_indices,
        "percentiles":          percentiles,
        "classifications":      classifications,
        "face_shape_7":         face_shape_7,
        "summary":              summary,
    }


def _compose_face_shape(c: dict) -> str:
    length = c.get("face_shape_length_class", "")
    jaw = c.get("face_shape_jaw_class", "")
    if length == "round_short" and jaw in ("oval", "wide_jaw"):  return "round"
    if length == "long" and jaw == "tapered_heart":              return "oblong_heart"
    if length == "long" and jaw == "square":                     return "rectangle"
    if length in ("long", "long_oval") and jaw == "oval":        return "long_oval"
    if length == "oval" and jaw == "tapered_heart":              return "heart"
    if length == "oval" and jaw == "square":                     return "square_oval"
    if length == "oval" and jaw == "wide_jaw":                   return "diamond_wide"
    if length == "oval" and jaw == "oval":                       return "oval"
    return f"{length}_{jaw}"

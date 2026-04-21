"""
Engine 1: Anthropometry

Farkas-inspired facial anthropometry — 20+ raw measurements and ~12 derived
ratios computed from Mediapipe Face Mesh landmarks (478-point refined model).

Outputs are normalized by inter-ocular distance (IOD) — the gold-standard
anchor in facial anthropometry, since IOD is one of the most stable adult
measurements (~31–33 mm in 95% of adults). This makes results image-size
independent and comparable across photos.

This engine reports raw geometry only. Classical interpretation
(Samudrika-style "long nose = leadership") is handled by Vedic engines.
Symmetry, golden ratio, and fWHR are separate dedicated engines (2, 3, 4).
"""
from __future__ import annotations

import math
from typing import Sequence

# ── Mediapipe Face Mesh landmark indices (canonical 478-point model) ────────
# Documented in mediapipe.solutions.face_mesh.FACEMESH_TESSELATION graph and
# https://github.com/google/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png
LM = {
    # Vertical (face height)
    "forehead_top":      10,
    "glabella":          9,    # between brows (nose bridge top)
    "nose_root":         168,  # nasion
    "nose_tip":          1,
    "subnasale":         2,    # base of nose / top of philtrum
    "upper_lip_top":     0,    # vermilion border, upper lip
    "lower_lip_bottom":  17,   # vermilion border, lower lip
    "chin_bottom":       152,  # menton

    # Horizontal (widths)
    "right_cheek":       234,  # zygion right
    "left_cheek":        454,  # zygion left
    "right_jaw":         172,  # gonion right
    "left_jaw":          397,  # gonion left
    "right_temple":      127,  # frontotemporale right
    "left_temple":       356,  # frontotemporale left

    # Eyes
    "r_eye_outer":       33,
    "r_eye_inner":       133,
    "l_eye_inner":       362,
    "l_eye_outer":       263,
    "r_eye_top":         159,
    "r_eye_bottom":      145,
    "l_eye_top":         386,
    "l_eye_bottom":      374,

    # Brows
    "r_brow_inner":      107,
    "r_brow_peak":       105,
    "r_brow_outer":      70,
    "l_brow_inner":      336,
    "l_brow_peak":       334,
    "l_brow_outer":      300,

    # Nose
    "r_alar":            98,   # right nostril wing
    "l_alar":            327,  # left nostril wing
    "nose_bridge_mid":   197,

    # Mouth
    "r_mouth_corner":    61,
    "l_mouth_corner":    291,
    "philtrum_top":      164,
    "upper_lip_inner":   13,
    "lower_lip_inner":   14,
}

# Adult average IOD in mm (used as scale anchor) — published norms:
# Caucasian/Asian adult IOD = 31–33 mm. We use 32 mm as a neutral baseline
# so reported "mm" values are population-anchored estimates, not exact.
IOD_BASELINE_MM = 32.0


# ── Geometry helpers ────────────────────────────────────────────────────────
def _dist(p1: Sequence[float], p2: Sequence[float]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def _midpoint(p1: Sequence[float], p2: Sequence[float]) -> tuple[float, float]:
    return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)


# ── Categorical classifiers (research-based thresholds) ─────────────────────
def _classify(value: float, bands: list[tuple[float, str]]) -> str:
    """bands sorted ascending by upper bound. Last band's bound = +inf."""
    for upper, label in bands:
        if value <= upper:
            return label
    return bands[-1][1]


# ── Main engine ─────────────────────────────────────────────────────────────
def run(landmarks_norm: list[tuple[float, float, float]],
        image_width: int,
        image_height: int) -> dict:
    """Compute anthropometric measurements + ratios + classifications.

    Args:
        landmarks_norm: 478 normalized (x,y,z) tuples from Mediapipe FaceMesh
        image_width, image_height: source image dimensions in pixels

    Returns:
        Engine result dict with keys: engine, measurements_px, measurements_mm,
        ratios, classifications, summary.
    """
    if not landmarks_norm or len(landmarks_norm) < 468:
        return {
            "engine": "anthropometry",
            "ok": False,
            "error": "insufficient_landmarks",
            "landmark_count": len(landmarks_norm) if landmarks_norm else 0,
        }

    # Convert normalized → pixel coords
    P = {name: (landmarks_norm[idx][0] * image_width,
                landmarks_norm[idx][1] * image_height)
         for name, idx in LM.items()}

    # ── 1. Establish scale: inter-ocular distance (inner-corner-to-inner-corner) ─
    iod_px = _dist(P["r_eye_inner"], P["l_eye_inner"])
    if iod_px < 5:  # degenerate
        return {"engine": "anthropometry", "ok": False, "error": "iod_too_small"}

    px_per_mm = iod_px / IOD_BASELINE_MM   # scale factor

    # ── 2. Raw measurements (pixels, then mm via IOD scale) ─────────────────
    M = {
        # Vertical
        "face_height_total":     _dist(P["forehead_top"],   P["chin_bottom"]),
        "forehead_height":       _dist(P["forehead_top"],   P["glabella"]),
        "midface_height":        _dist(P["glabella"],       P["subnasale"]),
        "lower_face_height":     _dist(P["subnasale"],      P["chin_bottom"]),
        "nose_length":           _dist(P["nose_root"],      P["subnasale"]),
        "nose_tip_to_chin":      _dist(P["nose_tip"],       P["chin_bottom"]),
        "upper_lip_to_chin":     _dist(P["upper_lip_top"],  P["chin_bottom"]),
        "lip_to_chin":           _dist(P["lower_lip_bottom"], P["chin_bottom"]),
        "upper_lip_thickness":   _dist(P["upper_lip_top"],  P["upper_lip_inner"]),
        "lower_lip_thickness":   _dist(P["lower_lip_inner"], P["lower_lip_bottom"]),

        # Horizontal
        "face_width_zygion":     _dist(P["right_cheek"],    P["left_cheek"]),
        "jaw_width":             _dist(P["right_jaw"],      P["left_jaw"]),
        "forehead_width":        _dist(P["right_temple"],   P["left_temple"]),
        "iod_inner":             iod_px,
        "outer_eye_span":        _dist(P["r_eye_outer"],    P["l_eye_outer"]),
        "right_eye_width":       _dist(P["r_eye_outer"],    P["r_eye_inner"]),
        "left_eye_width":        _dist(P["l_eye_inner"],    P["l_eye_outer"]),
        "right_eye_height":      _dist(P["r_eye_top"],      P["r_eye_bottom"]),
        "left_eye_height":       _dist(P["l_eye_top"],      P["l_eye_bottom"]),
        "nose_width_alar":       _dist(P["r_alar"],         P["l_alar"]),
        "mouth_width":           _dist(P["r_mouth_corner"], P["l_mouth_corner"]),
        "brow_distance_inner":   _dist(P["r_brow_inner"],   P["l_brow_inner"]),
    }

    measurements_px = {k: round(v, 1) for k, v in M.items()}
    measurements_mm = {k: round(v / px_per_mm, 1) for k, v in M.items()}

    # ── 3. Ratios (dimensionless, the real signal) ──────────────────────────
    # Guard against zero divisions (defensive)
    def _r(num, den, places=3):
        return round(num / den, places) if den else 0.0

    ratios = {
        # Face proportion
        "face_length_to_width":      _r(M["face_height_total"], M["face_width_zygion"]),
        "jaw_to_face_width":         _r(M["jaw_width"],         M["face_width_zygion"]),
        "forehead_to_face_width":    _r(M["forehead_width"],    M["face_width_zygion"]),

        # Rule-of-thirds (vertical)
        "third_upper":               _r(M["forehead_height"],   M["face_height_total"]),
        "third_middle":              _r(M["midface_height"],    M["face_height_total"]),
        "third_lower":               _r(M["lower_face_height"], M["face_height_total"]),

        # Eye proportions
        "eye_spacing_to_eye_width":  _r(M["iod_inner"],         (M["right_eye_width"] + M["left_eye_width"]) / 2),
        "eye_span_to_face_width":    _r(M["outer_eye_span"],    M["face_width_zygion"]),
        "eye_aspect_ratio_avg":      _r((M["right_eye_height"] + M["left_eye_height"]) / 2,
                                        (M["right_eye_width"]  + M["left_eye_width"])  / 2),

        # Nose & mouth
        "nose_length_to_face":       _r(M["nose_length"],       M["face_height_total"]),
        "nose_width_to_mouth_width": _r(M["nose_width_alar"],   M["mouth_width"]),
        "mouth_to_face_width":       _r(M["mouth_width"],       M["face_width_zygion"]),
        "lip_ratio_upper_to_lower":  _r(M["upper_lip_thickness"], M["lower_lip_thickness"]),
    }

    # ── 4. Categorical classifications ─────────────────────────────────────
    classifications = {
        # Face shape (length-to-width)
        "face_shape_length_class": _classify(ratios["face_length_to_width"], [
            (1.10, "round_short"),
            (1.30, "oval"),
            (1.45, "long_oval"),
            (99.0, "long"),
        ]),
        # Face shape vs jaw width (square vs heart vs oval)
        "face_shape_jaw_class": _classify(ratios["jaw_to_face_width"], [
            (0.72, "tapered_heart"),
            (0.82, "oval"),
            (0.92, "square"),
            (99.0, "wide_jaw"),
        ]),
        # Forehead breadth
        "forehead_class": _classify(ratios["forehead_to_face_width"], [
            (0.78, "narrow"),
            (0.92, "balanced"),
            (99.0, "broad"),
        ]),
        # Eye spacing
        "eye_spacing_class": _classify(ratios["eye_spacing_to_eye_width"], [
            (0.95, "close_set"),
            (1.10, "balanced"),
            (99.0, "wide_set"),
        ]),
        # Eye openness (almond vs round vs hooded)
        "eye_openness_class": _classify(ratios["eye_aspect_ratio_avg"], [
            (0.28, "narrow_hooded"),
            (0.38, "almond"),
            (99.0, "round_open"),
        ]),
        # Lip fullness ratio
        "lip_class": _classify(ratios["lip_ratio_upper_to_lower"], [
            (0.55, "fuller_lower"),
            (0.85, "balanced"),
            (1.20, "fuller_upper"),
            (99.0, "very_full_upper"),
        ]),
        # Mouth size relative to face
        "mouth_size_class": _classify(ratios["mouth_to_face_width"], [
            (0.36, "small_mouth"),
            (0.46, "medium_mouth"),
            (99.0, "wide_mouth"),
        ]),
        # Nose breadth relative to mouth (Vedic + Western marker)
        "nose_breadth_class": _classify(ratios["nose_width_to_mouth_width"], [
            (0.62, "narrow_nose"),
            (0.78, "balanced_nose"),
            (99.0, "wide_nose"),
        ]),
        # Vertical thirds balance — flag the dominant third
        "dominant_third": max(
            ("upper",  ratios["third_upper"]),
            ("middle", ratios["third_middle"]),
            ("lower",  ratios["third_lower"]),
            key=lambda kv: kv[1],
        )[0],
    }

    # ── 5. Human-readable summary (for downstream narration) ───────────────
    summary = {
        "face_shape": _compose_face_shape(classifications),
        "iod_mm_estimate": round(IOD_BASELINE_MM, 1),
        "measurements_count": len(measurements_px),
        "ratios_count": len(ratios),
        "classifications_count": len(classifications),
    }

    return {
        "engine": "anthropometry",
        "ok": True,
        "scale": {
            "iod_pixels": round(iod_px, 2),
            "iod_baseline_mm": IOD_BASELINE_MM,
            "px_per_mm": round(px_per_mm, 4),
        },
        "measurements_px": measurements_px,
        "measurements_mm": measurements_mm,
        "ratios": ratios,
        "classifications": classifications,
        "summary": summary,
    }


def _compose_face_shape(c: dict) -> str:
    """Combine length + jaw classifications into a single descriptive shape."""
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

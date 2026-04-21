"""
Engine 3 — Golden Ratio (Phi / Marquardt) Analysis.

Measures the face against the divine proportion φ = 1.618033988…
and the neoclassical canons (Leonardo da Vinci's vertical thirds and
horizontal fifths). Same pose-corrected canonical 3D frame as Engines
1 & 2 for cross-engine consistency.

What it computes
────────────────
  • 22 classical φ ratios (face / eyes / nose / mouth / vertical / horizontal)
  • Vertical-thirds analysis (Leonardo: forehead = midface = lower face)
  • Horizontal-fifths analysis (Leonardo: face width = 5 × eye width)
  • Per-region phi scores (face, eyes, nose, mouth, vertical, horizontal)
  • Overall Marquardt phi score 0–100
  • Aesthetic classification (Divine / Excellent / Very Good / … / Below Avg)
  • Top 3 most phi-aligned features  + top 3 most off-phi features

All measurements derived in the canonical face frame so head pose,
yaw, roll and pitch do NOT affect the ratios.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np


# Reuse the same anchors / scale as Engines 1 & 2 for consistency
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


# ─────────────────────────────────────────────────────────────────────────────
# φ-conformance helpers
# ─────────────────────────────────────────────────────────────────────────────
def _phi_score(actual: float, target: float) -> float:
    """0..100 conformance score (deviation from target normalized).

    Uses |actual − target| / target. 0% deviation → 100. 50% deviation → 0.
    """
    if target <= 0 or actual <= 0:
        return 0.0
    dev = abs(actual - target) / target
    score = max(0.0, 100.0 * (1.0 - dev * 2.0))   # 50% deviation = 0
    return round(score, 1)


def _classify_overall(score: float) -> str:
    if score >= 90: return "Divine"
    if score >= 80: return "Excellent"
    if score >= 70: return "Very Good"
    if score >= 60: return "Good"
    if score >= 50: return "Average"
    if score >= 40: return "Below Average"
    return "Poor Phi Conformance"


def _classify_region(score: float) -> str:
    if score >= 80: return "highly_phi_aligned"
    if score >= 65: return "phi_aligned"
    if score >= 50: return "moderately_aligned"
    if score >= 35: return "weakly_aligned"
    return "off_phi"


# ─────────────────────────────────────────────────────────────────────────────
# Main engine
# ─────────────────────────────────────────────────────────────────────────────
def run(landmarks_norm: Sequence[tuple[float, float, float]],
        image_w: int, image_h: int,
        hairline_mm_above_mesh_top: float | None = None) -> dict:
    """Phi analysis on canonical-frame landmarks.

    Args:
      landmarks_norm: 478 (x,y,z) tuples from Mediapipe (normalized 0..1)
      image_w, image_h: pixel dims (used to denormalize)
      hairline_mm_above_mesh_top: optional offset (mm) from foundation hairline
        estimator. If provided, vertical-thirds use the true hairline; else
        falls back to mesh top (Mediapipe lm 10).

    Returns: dict with `engine: "phi"`, `version: 1`, ratios, region scores,
    overall_phi_score, classification, and `phi_constant`.
    """
    if not landmarks_norm or len(landmarks_norm) < 478:
        return {"engine": "phi", "ok": False, "error": "insufficient_landmarks"}

    pts = np.array([(x * image_w, y * image_h, z * image_w) for x, y, z in landmarks_norm],
                   dtype=np.float64)

    def get3d(idx_or_name):
        idx = LMK[idx_or_name] if isinstance(idx_or_name, str) else idx_or_name
        return pts[idx]

    # ── 1. Canonical face frame (same as Engines 1 & 2) ────────────────────
    origin, R = _build_face_frame(get3d)

    def fp(idx_or_name) -> np.ndarray:
        """Landmark in canonical face-frame 3D coords (units = pixels)."""
        idx = LMK[idx_or_name] if isinstance(idx_or_name, str) else idx_or_name
        return R @ (pts[idx] - origin)

    # IOD scale (canonical-frame x-distance between inner eyes)
    iod_px = abs(fp(L_INNER_EYE)[0] - fp(R_INNER_EYE)[0])
    if iod_px <= 0:
        return {"engine": "phi", "ok": False, "error": "invalid_iod"}
    px_per_mm = iod_px / IOD_BASELINE_MM

    def dx(a, b) -> float:    # horizontal canonical distance (px)
        return abs(fp(a)[0] - fp(b)[0])

    def dy(a, b) -> float:    # vertical canonical distance (px)
        return abs(fp(a)[1] - fp(b)[1])

    def d2d(a, b) -> float:   # planar canonical distance (px) ignoring z
        va, vb = fp(a), fp(b)
        return float(math.hypot(va[0] - vb[0], va[1] - vb[1]))

    # ── 2. Key reference points ────────────────────────────────────────────
    # Vertical anchors
    mesh_top_y      = fp(FOREHEAD)[1]                  # landmark 10
    glabella_y      = fp("glabella")[1]                # 9
    subnasale_y     = fp(2)[1]                          # bottom of nose (subnasale)
    stomion_y       = fp(13)[1]                         # mouth opening (between lips)
    menton_y        = fp(CHIN)[1]                       # 152
    pupil_y_avg     = (fp(468)[1] + fp(473)[1]) / 2.0   # avg pupil y
    brow_y_avg      = (fp(107)[1] + fp(336)[1]) / 2.0   # inner brow tops
    upper_lip_top_y = fp(0)[1]                          # 0 = upper lip top
    lower_lip_bot_y = fp(17)[1]                         # 17 = lower lip bottom

    # Horizontal anchors
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

    face_width_px   = abs(l_zygion_x - r_zygion_x)
    eye_outer_to_outer_px = abs(l_eye_out_x - r_eye_out_x)
    inner_eye_dist_px     = abs(l_eye_in_x  - r_eye_in_x)
    nose_width_px         = abs(l_alar_x    - r_alar_x)
    mouth_width_px        = abs(l_mouth_x   - r_mouth_x)
    r_eye_width_px        = abs(r_eye_in_x  - r_eye_out_x)
    l_eye_width_px        = abs(l_eye_out_x - l_eye_in_x)
    avg_eye_width_px      = (r_eye_width_px + l_eye_width_px) / 2.0
    pupil_distance_px     = abs(fp(468)[0] - fp(473)[0])

    # Trichion (true hairline) — use foundation estimate if provided.
    # NOTE: canonical face-frame +y points UP (chin → forehead), so the
    # hairline (which sits ABOVE the mesh top) has a LARGER y than mesh_top_y.
    # Cap the offset at a sane physiological maximum (60 mm) so a noisy
    # hairline detector that wandered into the background can't blow up the
    # vertical-thirds analysis.
    if hairline_mm_above_mesh_top and hairline_mm_above_mesh_top > 0:
        offset_mm = min(float(hairline_mm_above_mesh_top), 60.0)
        trichion_y = mesh_top_y + offset_mm * px_per_mm
        trichion_used = "foundation_hairline_estimator"
        if offset_mm < float(hairline_mm_above_mesh_top):
            trichion_used += "_capped60mm"
    else:
        trichion_y = mesh_top_y     # fall back to mesh top
        trichion_used = "mediapipe_mesh_top"

    # Length anchors
    face_length_px       = abs(menton_y - trichion_y)
    forehead_third_px    = abs(brow_y_avg - trichion_y)        # trichion → brows
    midface_third_px     = abs(subnasale_y - brow_y_avg)        # brows → subnasale
    lower_third_px       = abs(menton_y - subnasale_y)          # subnasale → chin
    nose_length_px       = abs(subnasale_y - glabella_y)
    pupil_to_stomion_px  = abs(stomion_y - pupil_y_avg)
    stomion_to_chin_px   = abs(menton_y - stomion_y)
    pupil_to_chin_px     = abs(menton_y - pupil_y_avg)
    trichion_to_pupil_px = abs(pupil_y_avg - trichion_y)
    lip_height_px        = abs(lower_lip_bot_y - upper_lip_top_y)

    # ── 3. Phi ratios ──────────────────────────────────────────────────────
    ratios: list[dict] = []

    def add(name: str, region: str, num_px: float, den_px: float,
            target: float, ideal_label: str = "phi"):
        if den_px <= 0 or num_px <= 0:
            return
        actual = num_px / den_px
        score = _phi_score(actual, target)
        ratios.append({
            "name":         name,
            "region":       region,
            "actual":       round(actual, 4),
            "target":       round(target, 4),
            "target_label": ideal_label,
            "deviation_pct": round((actual - target) / target * 100, 2),
            "score":        score,
            "numerator_mm":   round(num_px / px_per_mm, 1),
            "denominator_mm": round(den_px / px_per_mm, 1),
        })

    # FACE region (length / width balance)
    add("face_length_to_width",         "face",  face_length_px,   face_width_px,        PHI)
    add("face_width_to_mouth_width",    "face",  face_width_px,    mouth_width_px,       3.0,  "leonardo_3:1")
    add("cheekbone_to_face_length",     "face",  face_width_px,    face_length_px,       INV_PHI)
    add("forehead_third_to_total",      "face",  forehead_third_px, face_length_px,      1/3.0, "third")
    add("midface_third_to_total",       "face",  midface_third_px,  face_length_px,      1/3.0, "third")
    add("lower_third_to_total",         "face",  lower_third_px,    face_length_px,      1/3.0, "third")

    # EYES region
    add("outer_to_outer_over_inner",    "eyes",  eye_outer_to_outer_px, inner_eye_dist_px, PHI + 1, "phi+1")
    add("inner_eye_dist_eq_eye_width",  "eyes",  inner_eye_dist_px,     avg_eye_width_px,  1.0, "1:1_canon")
    add("outer_eye_dist_to_mouth_w",    "eyes",  eye_outer_to_outer_px, mouth_width_px,    PHI)
    add("pupil_dist_to_outer_dist",     "eyes",  pupil_distance_px,     eye_outer_to_outer_px, INV_PHI)
    add("eye_width_to_nose_width",      "eyes",  avg_eye_width_px,      nose_width_px,     1.0, "1:1_canon")

    # NOSE region
    add("nose_length_to_width",         "nose",  nose_length_px,    nose_width_px,        PHI)
    add("mouth_w_to_nose_w",            "nose",  mouth_width_px,    nose_width_px,        PHI)
    add("nose_width_eq_inner_eye",      "nose",  nose_width_px,     inner_eye_dist_px,    1.0, "1:1_canon")

    # MOUTH region
    add("mouth_width_to_lip_height",    "mouth", mouth_width_px,    lip_height_px,        PHI * 2, "2phi")
    add("lower_third_to_lip_height",    "mouth", lower_third_px,    lip_height_px,        PHI * 2, "2phi")
    add("mouth_w_to_iris_dist",         "mouth", mouth_width_px,    pupil_distance_px,    1.0, "1:1_canon")

    # VERTICAL phi (Marquardt vertical proportions)
    add("trichion_to_pupil_over_pupil_to_stomion", "vertical",
        trichion_to_pupil_px, pupil_to_stomion_px, PHI)
    add("pupil_to_stomion_over_stomion_to_chin",   "vertical",
        pupil_to_stomion_px, stomion_to_chin_px, PHI)
    add("trichion_to_pupil_over_pupil_to_chin",    "vertical",
        trichion_to_pupil_px, pupil_to_chin_px, INV_PHI)

    # HORIZONTAL fifths (Leonardo: face = 5 eye widths)
    add("face_w_over_eye_w",            "horizontal",
        face_width_px, avg_eye_width_px, 5.0, "leonardo_5:1")
    add("inner_eye_dist_over_eye_width", "horizontal",
        inner_eye_dist_px, avg_eye_width_px, 1.0, "1:1_canon")

    # ── 4. Region scores ───────────────────────────────────────────────────
    region_scores: dict[str, dict] = {}
    for region in ("face", "eyes", "nose", "mouth", "vertical", "horizontal"):
        region_ratios = [r for r in ratios if r["region"] == region]
        if not region_ratios:
            continue
        avg = sum(r["score"] for r in region_ratios) / len(region_ratios)
        region_scores[region] = {
            "score":   round(avg, 1),
            "rating":  _classify_region(avg),
            "n_ratios": len(region_ratios),
        }

    # ── 5. Vertical thirds detail ──────────────────────────────────────────
    if face_length_px > 0:
        thirds_pct = {
            "forehead_third_pct": round(forehead_third_px / face_length_px * 100, 1),
            "midface_third_pct":  round(midface_third_px  / face_length_px * 100, 1),
            "lower_third_pct":    round(lower_third_px    / face_length_px * 100, 1),
        }
        # Equal thirds = 33.33% each. Penalize deviation.
        equality_dev = sum(abs(v - 33.33) for v in thirds_pct.values()) / 3.0
        thirds_score = max(0.0, 100.0 - equality_dev * 4.0)   # 25%-pt deviation = 0
        thirds_pct["equality_score"] = round(thirds_score, 1)
        thirds_pct["dominant"] = max(thirds_pct, key=lambda k: thirds_pct[k]
                                     if k.endswith("_pct") else -1)
        # Identify dominant third
        dom_val = max(forehead_third_px, midface_third_px, lower_third_px)
        if dom_val == forehead_third_px:   thirds_pct["dominant_third"] = "forehead"
        elif dom_val == midface_third_px:  thirds_pct["dominant_third"] = "midface"
        else:                               thirds_pct["dominant_third"] = "lower_face"
    else:
        thirds_pct = {"error": "invalid_face_length"}

    # ── 6. Horizontal fifths detail ────────────────────────────────────────
    if face_width_px > 0 and avg_eye_width_px > 0:
        # Five canonical fifths (each 20% of face width, ≈ 1 eye width):
        #   1. R-zygion → R-outer-eye           (peripheral right)
        #   2. R-outer-eye → R-inner-eye        (right eye)
        #   3. R-inner-eye → L-inner-eye        (inter-ocular)
        #   4. L-inner-eye → L-outer-eye        (left eye)
        #   5. L-outer-eye → L-zygion           (peripheral left)
        fifths_px = [
            abs(r_eye_out_x - r_zygion_x),
            r_eye_width_px,
            inner_eye_dist_px,
            l_eye_width_px,
            abs(l_zygion_x - l_eye_out_x),
        ]
        fifths_pct = [round(p / face_width_px * 100, 1) for p in fifths_px]
        ideal = 20.0
        fifths_dev = sum(abs(p - ideal) for p in fifths_pct) / 5.0
        fifths_score = max(0.0, 100.0 - fifths_dev * 4.0)
        fifths = {
            "fifth_widths_pct": fifths_pct,
            "ideal_pct":        ideal,
            "equality_score":   round(fifths_score, 1),
            "labels":           ["right_periphery", "right_eye", "inter_ocular",
                                 "left_eye", "left_periphery"],
        }
    else:
        fifths = {"error": "invalid_face_or_eye_width"}

    # ── 7. Overall Marquardt phi score ─────────────────────────────────────
    if ratios:
        weighted_total = (
            sum(r["score"] for r in ratios) +
            (thirds_pct.get("equality_score", 0.0) if isinstance(thirds_pct, dict) else 0) +
            (fifths.get("equality_score", 0.0) if isinstance(fifths, dict) else 0)
        )
        n_components = len(ratios) + 2
        overall = weighted_total / n_components
    else:
        overall = 0.0

    # ── 8. Top / bottom features ───────────────────────────────────────────
    sorted_ratios = sorted(ratios, key=lambda r: r["score"], reverse=True)
    top_3   = [{"name": r["name"], "region": r["region"], "score": r["score"],
                "actual": r["actual"], "target": r["target"]}
               for r in sorted_ratios[:3]]
    bot_3   = [{"name": r["name"], "region": r["region"], "score": r["score"],
                "actual": r["actual"], "target": r["target"],
                "deviation_pct": r["deviation_pct"]}
               for r in sorted_ratios[-3:][::-1]]

    return {
        "engine":            "phi",
        "version":           1,
        "ok":                True,
        "phi_constant":      round(PHI, 6),
        "frame":             "canonical_3d_pose_corrected",
        "iod_baseline_mm":   IOD_BASELINE_MM,
        "px_per_mm":         round(px_per_mm, 3),
        "trichion_source":   "foundation_hairline_estimator" if hairline_mm_above_mesh_top
                              else "mediapipe_mesh_top",
        "ratios":            ratios,
        "region_scores":     region_scores,
        "vertical_thirds":   thirds_pct,
        "horizontal_fifths": fifths,
        "overall_phi_score": round(overall, 1),
        "classification":    _classify_overall(overall),
        "top_3_phi_aligned": top_3,
        "top_3_off_phi":     bot_3,
        "interpretation":    _interpret(overall, region_scores, thirds_pct, fifths),
    }


def _interpret(overall: float, regions: dict, thirds: dict, fifths: dict) -> dict:
    """Plain-language summary."""
    summary: list[str] = []
    summary.append(f"Overall phi conformance: {overall:.1f}/100 ({_classify_overall(overall)}).")

    if regions:
        best_region = max(regions, key=lambda k: regions[k]["score"])
        worst_region = min(regions, key=lambda k: regions[k]["score"])
        summary.append(
            f"Most phi-aligned region: {best_region} "
            f"({regions[best_region]['score']:.0f}/100). "
            f"Least: {worst_region} ({regions[worst_region]['score']:.0f}/100)."
        )

    if isinstance(thirds, dict) and "equality_score" in thirds:
        summary.append(
            f"Vertical thirds: forehead {thirds['forehead_third_pct']}%, "
            f"midface {thirds['midface_third_pct']}%, "
            f"lower {thirds['lower_third_pct']}% — "
            f"{thirds.get('dominant_third', '?')}-dominant "
            f"(equality score {thirds['equality_score']:.0f}/100)."
        )

    if isinstance(fifths, dict) and "equality_score" in fifths:
        summary.append(
            f"Horizontal fifths equality: {fifths['equality_score']:.0f}/100."
        )

    return {
        "summary":    " ".join(summary),
        "highlights": summary,
    }

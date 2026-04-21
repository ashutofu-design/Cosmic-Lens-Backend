"""
Engine 2: Facial Symmetry  (v2 — pose-corrected, 3D, Vedic-aware)

Quantifies left-right facial symmetry using Mediapipe landmark pairs in
a canonical (pose-corrected) 3D face coordinate frame.

Method:
  1. Build an orthonormal 3D face frame from key landmarks
     (inner eye corners + forehead-chin axis). This automatically removes
     head roll and most yaw, so lateral features (jaw, temples, cheeks)
     are no longer penalised by small head pose.
  2. Transform every landmark into this canonical frame using the full
     (x, y, z) tuple from Mediapipe.
  3. For each landmark pair, mirror the right point's x-coordinate and
     measure the 3D Euclidean distance to the true left point.
  4. Normalize by inter-ocular distance (IOD).
  5. Roll up to per-feature scores → overall weighted score → tier.

Adds versus v1:
  • Pose-corrected 3D measurement (was 2D image-plane only)
  • Per-feature dominant side (was overall only)
  • Top-3 most asymmetric individual landmark pairs (with descriptive labels)
  • Vedic side interpretation (Surya / Chandra / Sushumna naadi mapping)
  • Z-axis (depth) component — detects "one cheekbone projects more"
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np

# ── Landmark pairs: (right_idx, left_idx, group, label) ─────────────────────
PAIRS = [
    # Eyes
    (33,  263, "eyes",   "outer_eye_corner"),
    (133, 362, "eyes",   "inner_eye_corner"),
    (159, 386, "eyes",   "upper_eyelid_mid"),
    (145, 374, "eyes",   "lower_eyelid_mid"),
    (157, 384, "eyes",   "upper_eyelid_medial"),
    (154, 381, "eyes",   "lower_eyelid_medial"),

    # Brows
    (107, 336, "brows",  "brow_inner"),
    (105, 334, "brows",  "brow_peak"),
    (70,  300, "brows",  "brow_outer"),
    (46,  276, "brows",  "brow_tail"),

    # Nose
    (98,  327, "nose",   "alar_wing"),
    (102, 331, "nose",   "nostril_tip"),
    (49,  279, "nose",   "nasal_sidewall"),
    (240, 460, "nose",   "nasal_base"),

    # Mouth
    (61,  291, "mouth",  "mouth_corner"),
    (40,  270, "mouth",  "upper_lip_outer"),
    (84,  314, "mouth",  "lower_lip_outer"),
    (185, 409, "mouth",  "upper_lip_mid"),

    # Cheeks
    (234, 454, "cheeks", "zygion_cheekbone"),
    (50,  280, "cheeks", "cheek_apex"),
    (123, 352, "cheeks", "mid_cheek"),

    # Jaw
    (172, 397, "jaw",    "gonion_jaw_angle"),
    (136, 365, "jaw",    "mid_jaw"),
    (150, 379, "jaw",    "mandible_curve"),

    # Temples / forehead sides
    (127, 356, "temples", "frontotemporale"),
    (54,  284, "temples", "forehead_temple"),
    (21,  251, "temples", "forehead_lateral"),
]

# Anchor landmarks for the canonical face frame
R_INNER_EYE = 133
L_INNER_EYE = 362
FOREHEAD    = 10
CHIN        = 152

# Score floor: displacement (in IOD) at which a feature score reaches 0.
# 0.10 IOD ≈ 3.2 mm. Now realistic (vs 0.15 before) because pose correction
# removes the "false asymmetry" that used to inflate lateral displacement.
SCORE_FLOOR_IOD = 0.10


# ── Geometry helpers ────────────────────────────────────────────────────────
def _build_face_frame(get3d) -> tuple[np.ndarray, np.ndarray]:
    """Build orthonormal canonical face frame.

    Returns:
        origin (3,)  — frame origin (midpoint of inner eye corners)
        R      (3,3) — rows are face-frame basis vectors expressed in image coords.
                       Apply R @ (p - origin) to convert image-coord 3D → face-coord 3D.
    """
    r_eye    = get3d(R_INNER_EYE)
    l_eye    = get3d(L_INNER_EYE)
    chin     = get3d(CHIN)
    forehead = get3d(FOREHEAD)

    origin = (r_eye + l_eye) / 2.0

    # x-axis: lateral, right → left (anatomical left)
    x_axis = l_eye - r_eye
    x_axis /= (np.linalg.norm(x_axis) or 1.0)

    # y-axis: vertical, chin → forehead, orthogonalised against x.
    # Mediapipe image y grows downward, so chin→forehead is "up" in face frame.
    y_tent = forehead - chin
    y_axis = y_tent - np.dot(y_tent, x_axis) * x_axis
    y_axis /= (np.linalg.norm(y_axis) or 1.0)

    # z-axis: out of face plane, toward camera
    z_axis = np.cross(x_axis, y_axis)
    z_axis /= (np.linalg.norm(z_axis) or 1.0)

    R = np.vstack([x_axis, y_axis, z_axis])
    return origin, R


def _classify_tier(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 90: return "exceptional"
    if score >= 80: return "high"
    if score >= 70: return "balanced"
    if score >= 55: return "moderate"
    return "asymmetric"


# ── Vedic interpretation tables ────────────────────────────────────────────
VEDIC_SIDE_MEANING = {
    "right_dominant": {
        "naadi": "Pingala (Surya naadi)",
        "principle": "Surya — solar, masculine, paternal",
        "active_aspects": [
            "Conscious mind & logic",
            "Action, ambition, willpower",
            "Future-orientation",
            "Father / paternal lineage influence",
            "External/material focus",
        ],
        "guidance": (
            "Right-side dominance suggests an active, externally-focused "
            "energy. Engage left-nostril breathing (Chandra Anuloma) and "
            "introspective practices to balance the lunar current."
        ),
    },
    "left_dominant": {
        "naadi": "Ida (Chandra naadi)",
        "principle": "Chandra — lunar, feminine, maternal",
        "active_aspects": [
            "Subconscious mind & intuition",
            "Emotion, receptivity, nurturing",
            "Past-orientation, memory",
            "Mother / maternal lineage influence",
            "Internal/spiritual focus",
        ],
        "guidance": (
            "Left-side dominance suggests an introspective, receptive "
            "energy. Engage right-nostril breathing (Surya Anuloma) and "
            "active pursuits to balance the solar current."
        ),
    },
    "balanced": {
        "naadi": "Sushumna (central naadi)",
        "principle": "Equilibrium — harmony of Surya & Chandra",
        "active_aspects": [
            "Balanced consciousness",
            "Even distribution of action & reflection",
            "Auspicious for meditation & sadhana",
            "Karmic equilibrium reflected outwardly",
        ],
        "guidance": (
            "A near-symmetric face reflects balanced Ida-Pingala flow. "
            "This is considered auspicious in Samudrika Shastra and "
            "favourable for spiritual practice."
        ),
    },
}


# ── Main engine ─────────────────────────────────────────────────────────────
def run(landmarks_norm: list[tuple[float, float, float]],
        image_width: int,
        image_height: int) -> dict:
    """Compute pose-corrected 3D symmetry metrics."""
    if not landmarks_norm or len(landmarks_norm) < 468:
        return {"engine": "symmetry", "ok": False, "error": "insufficient_landmarks"}

    W, H = float(image_width), float(image_height)

    # Mediapipe z is in normalized units roughly on the same scale as x.
    # Convert all coords to "pixel-equivalent" 3D using image_width as the
    # depth scale (Mediapipe convention).
    def get3d(idx: int) -> np.ndarray:
        lm = landmarks_norm[idx]
        return np.array([lm[0] * W, lm[1] * H, lm[2] * W], dtype=np.float64)

    # ── 1. Build canonical face frame ──────────────────────────────────────
    origin, R = _build_face_frame(get3d)

    def to_face(idx: int) -> np.ndarray:
        return R @ (get3d(idx) - origin)

    # IOD in face-frame x (always lies along x-axis by construction)
    r_eye_f = to_face(R_INNER_EYE)
    l_eye_f = to_face(L_INNER_EYE)
    iod_px = float(np.linalg.norm(l_eye_f - r_eye_f))
    if iod_px < 5:
        return {"engine": "symmetry", "ok": False, "error": "iod_too_small"}

    # ── 2. Per-pair displacement (3D, in canonical frame) ──────────────────
    per_pair = []
    for r_idx, l_idx, group, label in PAIRS:
        if r_idx >= len(landmarks_norm) or l_idx >= len(landmarks_norm):
            continue
        rp = to_face(r_idx)
        lp = to_face(l_idx)

        # Mirror right point across the y-z plane (negate x)
        rp_mirrored = rp.copy()
        rp_mirrored[0] = -rp_mirrored[0]

        diff = lp - rp_mirrored
        disp_3d = float(np.linalg.norm(diff))
        disp_lat = float(diff[0])    # lateral mismatch (x): how far off the mirror
        disp_vert = float(diff[1])   # vertical mismatch (y): one side higher
        disp_depth = float(diff[2])  # depth mismatch (z): one side projects more

        # Side balance: which side projects further from midline (in canonical x)
        # |rp.x| vs |lp.x|. Positive = right-side landmark is laterally larger.
        side_balance = abs(rp[0]) - abs(lp[0])

        # Vertical asymmetry sign: positive = left side higher (lower y in face frame
        # means higher in image, since y-axis points toward forehead → +y is "up")
        vert_diff_mm_units = lp[1] - rp[1]   # +ve: left landmark higher than right

        per_pair.append({
            "right_idx": r_idx,
            "left_idx":  l_idx,
            "group":     group,
            "label":     label,
            "displacement_iod":        round(disp_3d / iod_px, 4),
            "displacement_iod_lateral":  round(abs(disp_lat) / iod_px, 4),
            "displacement_iod_vertical": round(abs(disp_vert) / iod_px, 4),
            "displacement_iod_depth":    round(abs(disp_depth) / iod_px, 4),
            "side_balance_iod":        round(side_balance / iod_px, 4),
            "vertical_offset_iod":     round(vert_diff_mm_units / iod_px, 4),
        })

    if not per_pair:
        return {"engine": "symmetry", "ok": False, "error": "no_valid_pairs"}

    # ── 3. Per-feature aggregation ─────────────────────────────────────────
    def _feature_block(group: str) -> dict:
        items = [p for p in per_pair if p["group"] == group]
        if not items:
            return {"pairs": 0, "score": None, "dominant_side": None}

        mean_disp = sum(p["displacement_iod"] for p in items) / len(items)
        mean_lat  = sum(p["displacement_iod_lateral"]  for p in items) / len(items)
        mean_vert = sum(p["displacement_iod_vertical"] for p in items) / len(items)
        mean_dep  = sum(p["displacement_iod_depth"]    for p in items) / len(items)

        score = max(0.0, min(100.0, 100.0 - (mean_disp / SCORE_FLOOR_IOD) * 100.0))

        # Group-level dominant side: average signed side_balance
        avg_balance = sum(p["side_balance_iod"] for p in items) / len(items)
        if abs(avg_balance) < 0.015:
            dom = "balanced"
        elif avg_balance > 0:
            dom = "right_dominant"
        else:
            dom = "left_dominant"

        # Group-level vertical bias: which side sits higher
        avg_vert = sum(p["vertical_offset_iod"] for p in items) / len(items)
        if abs(avg_vert) < 0.010:
            vert_bias = "level"
        elif avg_vert > 0:
            vert_bias = "left_higher"
        else:
            vert_bias = "right_higher"

        return {
            "pairs": len(items),
            "mean_disp_iod":          round(mean_disp, 4),
            "mean_lateral_iod":       round(mean_lat, 4),
            "mean_vertical_iod":      round(mean_vert, 4),
            "mean_depth_iod":         round(mean_dep, 4),
            "score":                  round(score, 1),
            "dominant_side":          dom,
            "side_balance_iod":       round(avg_balance, 4),
            "vertical_bias":          vert_bias,
            "vertical_offset_iod":    round(avg_vert, 4),
        }

    groups = ["eyes", "brows", "nose", "mouth", "cheeks", "jaw", "temples"]
    per_feature = {g: _feature_block(g) for g in groups}

    # ── 4. Overall weighted score ──────────────────────────────────────────
    weights = {
        "eyes":   2.0,
        "mouth":  1.8,
        "nose":   1.5,
        "brows":  1.2,
        "cheeks": 1.0,
        "jaw":    1.0,
        "temples": 0.5,
    }
    weighted_sum = 0.0
    weight_total = 0.0
    for g, w in weights.items():
        s = per_feature[g]["score"]
        if s is not None:
            weighted_sum += s * w
            weight_total += w
    overall_score = round(weighted_sum / weight_total, 1) if weight_total else None
    tier = _classify_tier(overall_score)

    # ── 5. Most / least symmetric features ─────────────────────────────────
    scored = [(g, per_feature[g]["score"]) for g in groups
              if per_feature[g]["score"] is not None]
    scored_sorted = sorted(scored, key=lambda kv: kv[1], reverse=True)
    most_sym  = scored_sorted[0][0]  if scored_sorted else None
    least_sym = scored_sorted[-1][0] if scored_sorted else None

    # ── 6. Top-3 most-asymmetric individual pairs ──────────────────────────
    pairs_sorted = sorted(per_pair, key=lambda p: p["displacement_iod"], reverse=True)
    top3 = []
    for p in pairs_sorted[:3]:
        # Convert IOD-normalized displacement to mm using 32mm IOD baseline
        mm_total = round(p["displacement_iod"]   * 32.0, 2)
        mm_lat   = round(p["displacement_iod_lateral"]  * 32.0, 2)
        mm_vert  = round(p["displacement_iod_vertical"] * 32.0, 2)
        mm_dep   = round(p["displacement_iod_depth"]    * 32.0, 2)
        side_higher = ("left" if p["vertical_offset_iod"] > 0
                       else "right" if p["vertical_offset_iod"] < 0
                       else "level")
        top3.append({
            "feature": p["group"],
            "label":   p["label"],
            "total_mm":    mm_total,
            "lateral_mm":  mm_lat,
            "vertical_mm": mm_vert,
            "depth_mm":    mm_dep,
            "side_higher": side_higher,
        })

    # ── 7. Overall dominant side ───────────────────────────────────────────
    avg_side = sum(p["side_balance_iod"] for p in per_pair) / len(per_pair)
    if abs(avg_side) < 0.015:
        dominant_side = "balanced"
    elif avg_side > 0:
        dominant_side = "right_dominant"
    else:
        dominant_side = "left_dominant"

    vedic = VEDIC_SIDE_MEANING[dominant_side]

    # ── 8. Interpretation ──────────────────────────────────────────────────
    interp = _interpret(overall_score, tier, most_sym, least_sym, dominant_side, top3)

    return {
        "engine": "symmetry",
        "ok": True,
        "version": 2,
        "scale": {
            "iod_pixels": round(iod_px, 2),
            "iod_baseline_mm": 32.0,
            "frame": "canonical_3d_pose_corrected",
        },
        "overall_score": overall_score,
        "tier": tier,
        "per_feature": per_feature,
        "most_symmetric_feature": most_sym,
        "least_symmetric_feature": least_sym,
        "top_asymmetric_pairs": top3,
        "dominant_side": dominant_side,
        "dominant_side_strength_iod": round(avg_side, 4),
        "vedic_interpretation": {
            "dominant_side": dominant_side,
            **vedic,
        },
        "summary": {
            "pairs_evaluated": len(per_pair),
            "feature_groups": len([g for g in groups if per_feature[g]["score"] is not None]),
            "interpretation": interp,
        },
    }


def _interpret(score, tier, most, least, side, top3) -> str:
    if score is None:
        return "Symmetry could not be evaluated."
    parts = [f"Overall pose-corrected symmetry: {score}/100 ({tier})."]
    if most and least and most != least:
        parts.append(f"Most symmetric region: {most}; least: {least}.")
    if side == "right_dominant":
        parts.append("Right side projects slightly more — Pingala (Surya) influence active.")
    elif side == "left_dominant":
        parts.append("Left side projects slightly more — Ida (Chandra) influence active.")
    else:
        parts.append("Both sides project equally — Sushumna (balanced) state.")
    if top3:
        t = top3[0]
        parts.append(
            f"Largest single asymmetry: {t['label']} ({t['feature']}) — "
            f"{t['total_mm']}mm total offset (lateral {t['lateral_mm']}mm, "
            f"vertical {t['vertical_mm']}mm, depth {t['depth_mm']}mm)."
        )
    return " ".join(parts)

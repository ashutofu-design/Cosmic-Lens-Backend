"""
Hairline (trichion) estimation.

Mediapipe Face Mesh stops at landmark #10 (forehead_top), which sits
INSIDE the visible forehead — not at the hairline. Several engines need
the true trichion:

  • Engine 1: forehead_height percentile (vs Farkas trichion-nasion)
  • Engine 14: Mian Xiang forehead palaces
  • Engine 15: Age Map (hairline = ages 15-30 zone)
  • Engine 9: Lalat Rekha (forehead lines)

Method: Walk upward from forehead_top in the original image. At each row,
check whether the pixel still resembles facial-skin color (within a
tolerance of the sampled forehead patch in YCrCb space). Stop when the
row leaves the skin range — that row is the estimated trichion.

Returns: pixel y-coord of estimated hairline + estimated full-forehead
height in mm (using IOD scale).
"""
from __future__ import annotations

import math
from typing import Sequence

import cv2
import numpy as np


def estimate_hairline(rgb_img: np.ndarray,
                      points_px: Sequence[tuple[int, int]],
                      iod_px: float,
                      iod_baseline_mm: float = 32.0) -> dict:
    """Estimate trichion (hairline) Y-coord and total forehead height.

    Args:
        rgb_img:   HxWx3 RGB image
        points_px: full landmark list in pixel coords
        iod_px:    inter-ocular distance in pixels (for mm scaling)
        iod_baseline_mm: scale anchor

    Returns:
        dict with hairline_y_px, total_forehead_height_mm, etc.
    """
    if rgb_img is None or rgb_img.ndim != 3:
        return {"ok": False, "error": "invalid_image"}
    if not points_px or len(points_px) < 200:
        return {"ok": False, "error": "insufficient_landmarks"}

    h, w = rgb_img.shape[:2]
    forehead_top_x, forehead_top_y = points_px[10]
    glabella_x, glabella_y = points_px[9]
    nose_root_x, nose_root_y = points_px[168]

    # ── 1. Sample reference skin colour from the forehead area ─────────────
    # Use a vertical strip just below forehead_top (definitely on skin).
    px_per_mm = iod_px / iod_baseline_mm
    sample_top = forehead_top_y
    sample_bottom = min(h, forehead_top_y + max(8, int(px_per_mm * 5)))
    sample_left = max(0, forehead_top_x - int(px_per_mm * 5))
    sample_right = min(w, forehead_top_x + int(px_per_mm * 5))
    if sample_bottom - sample_top < 4 or sample_right - sample_left < 4:
        return {"ok": False, "error": "sample_window_too_small"}

    skin_patch = rgb_img[sample_top:sample_bottom, sample_left:sample_right]
    ycrcb_patch = cv2.cvtColor(skin_patch, cv2.COLOR_RGB2YCrCb).reshape(-1, 3)

    # Tolerance = 2× std-dev in Cr/Cb channels (color stays similar; Y can vary)
    cr_mean, cb_mean = float(ycrcb_patch[:, 1].mean()), float(ycrcb_patch[:, 2].mean())
    cr_std,  cb_std  = float(ycrcb_patch[:, 1].std()),  float(ycrcb_patch[:, 2].std())
    cr_tol = max(8.0, 2.5 * cr_std)
    cb_tol = max(8.0, 2.5 * cb_std)

    # ── 2. Walk upward row by row from forehead_top ────────────────────────
    # Convert full image to YCrCb once
    ycrcb_full = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2YCrCb)

    # Window width: same as sample
    win_left = sample_left
    win_right = sample_right

    hairline_y = forehead_top_y      # default if we never leave skin
    found = False
    consecutive_non_skin = 0
    REQUIRED_NON_SKIN_ROWS = max(3, int(px_per_mm * 1))   # require ~1 mm of non-skin

    # Maximum upward search distance: half the face height (don't run off image)
    max_distance = min(forehead_top_y, int((nose_root_y - forehead_top_y) * 4))
    for offset in range(1, max_distance):
        y = forehead_top_y - offset
        if y < 0:
            break
        row = ycrcb_full[y, win_left:win_right]
        if row.size == 0:
            break
        cr_diff = np.abs(row[:, 1].astype(np.float32) - cr_mean)
        cb_diff = np.abs(row[:, 2].astype(np.float32) - cb_mean)
        skin_pixels = ((cr_diff < cr_tol) & (cb_diff < cb_tol)).mean()
        if skin_pixels < 0.45:    # <45% of row pixels look like skin
            consecutive_non_skin += 1
            if consecutive_non_skin >= REQUIRED_NON_SKIN_ROWS:
                hairline_y = y + REQUIRED_NON_SKIN_ROWS    # back off to last skin row
                found = True
                break
        else:
            consecutive_non_skin = 0

    # ── 3. Distances ───────────────────────────────────────────────────────
    extra_above_mesh_px = max(0, forehead_top_y - hairline_y)
    # Hairline → glabella (between brows). In image coords, glabella_y > hairline_y.
    trichion_to_glabella_px = max(0, glabella_y - hairline_y)
    # Hairline → nasion (nose root, landmark 168). Farkas trichion-nasion baseline.
    trichion_to_nasion_px   = max(0, nose_root_y - hairline_y) if found \
                              else max(0, nose_root_y - forehead_top_y)

    return {
        "ok": True,
        "found_hairline": found,
        "hairline_y_px":              int(hairline_y),
        "forehead_top_y_px":          int(forehead_top_y),
        "extra_above_mesh_top_px":    int(extra_above_mesh_px),
        "extra_above_mesh_top_mm":    round(extra_above_mesh_px / px_per_mm, 1),
        "trichion_to_glabella_mm":    round(trichion_to_glabella_px / px_per_mm, 1),
        "trichion_to_nasion_mm":      round(trichion_to_nasion_px / px_per_mm, 1),
        "method": "ycrcb_skin_walk",
    }

"""
Skin pixel sampling — extracts color/luminance metrics from key facial regions.

Sampled patches (small windows centered on Mediapipe landmarks):
  • forehead   — center of forehead (best general-skin sample)
  • cheek_r    — right cheek apex
  • cheek_l    — left cheek apex
  • nose_tip   — nose tip (often slightly different — oily/red zone)
  • chin       — chin (sebum / shadow info)

Output per region:
  rgb_mean  — average sRGB tuple
  hsv_mean  — average HSV (H 0–179, S 0–255, V 0–255)
  lab_mean  — average CIE Lab (L 0–100, a/b -128 to 127)
  ita       — Individual Typology Angle (degrees) → standard skin classification
              (very_light / light / intermediate / tan / brown / dark)
  undertone — warm / neutral / cool (from b* channel)

Aggregated:
  composite — averaged metrics across cheeks + forehead (general skin)
  redness   — relative a* value (Pitta marker in Ayurveda + health flag)
  yellowness — relative b* value (Vata/Kapha marker)
"""
from __future__ import annotations

import math
from typing import Sequence

import cv2
import numpy as np

# Landmark indices for each sample region (Mediapipe FaceMesh)
SAMPLE_REGIONS = {
    "forehead":  151,    # mid-forehead between brows
    "cheek_r":   50,     # right cheek apex (already used in symmetry)
    "cheek_l":   280,    # left cheek apex
    "nose_tip":  4,      # nose tip area
    "chin":      199,    # chin pad below lower lip
}

PATCH_HALF_PX = 8        # sample window = 17×17 pixels around each point


# ── ITA classification per Del Bino & Bernerd (2013) ───────────────────────
def _ita_class(ita: float) -> str:
    if ita > 55:    return "very_light"
    if ita > 41:    return "light"
    if ita > 28:    return "intermediate"
    if ita > 10:    return "tan"
    if ita > -30:   return "brown"
    return "dark"


def _undertone_class(b_star: float) -> str:
    """Warm/neutral/cool from CIE Lab b* channel.
    b* > 18 = warm (yellow/golden)
    b* between 12-18 = neutral
    b* < 12 = cool (pink/blue)
    """
    if b_star > 18:  return "warm"
    if b_star > 12:  return "neutral"
    return "cool"


def _sample_patch(rgb_img: np.ndarray, cx: int, cy: int) -> np.ndarray | None:
    h, w = rgb_img.shape[:2]
    x0 = max(0, cx - PATCH_HALF_PX)
    y0 = max(0, cy - PATCH_HALF_PX)
    x1 = min(w, cx + PATCH_HALF_PX + 1)
    y1 = min(h, cy + PATCH_HALF_PX + 1)
    if x1 - x0 < 5 or y1 - y0 < 5:
        return None
    return rgb_img[y0:y1, x0:x1]


def _patch_metrics(rgb_patch: np.ndarray) -> dict:
    """Compute color metrics from a small RGB patch."""
    # Drop extreme outliers (specular highlights / shadows) by trimming
    # via per-channel 10–90 percentiles.
    flat = rgb_patch.reshape(-1, 3).astype(np.float64)
    lo = np.percentile(flat, 10, axis=0)
    hi = np.percentile(flat, 90, axis=0)
    mask = np.all((flat >= lo) & (flat <= hi), axis=1)
    trimmed = flat[mask] if mask.any() else flat
    rgb_mean = tuple(round(float(c), 1) for c in trimmed.mean(axis=0))

    # HSV
    rgb_pix = np.uint8([[list(rgb_mean)]])
    hsv_pix = cv2.cvtColor(rgb_pix, cv2.COLOR_RGB2HSV)[0, 0]
    hsv_mean = tuple(int(c) for c in hsv_pix)

    # Lab (CIE)
    lab_pix = cv2.cvtColor(rgb_pix, cv2.COLOR_RGB2LAB)[0, 0]
    L_raw, a_raw, b_raw = float(lab_pix[0]), float(lab_pix[1]), float(lab_pix[2])
    # OpenCV stores L as 0-255; convert to standard 0-100 scale.
    L_std = L_raw * 100.0 / 255.0
    # OpenCV stores a/b as 0-255 with 128 as 0; convert to -128..127
    a_std = a_raw - 128.0
    b_std = b_raw - 128.0
    lab_mean = (round(L_std, 1), round(a_std, 1), round(b_std, 1))

    # Individual Typology Angle (ITA), standard skin classification
    if b_std == 0:
        ita = 90.0
    else:
        ita = math.degrees(math.atan2(L_std - 50.0, b_std))

    return {
        "rgb_mean":  rgb_mean,
        "hsv_mean":  hsv_mean,
        "lab_mean":  lab_mean,
        "ita":       round(ita, 1),
        "ita_class": _ita_class(ita),
        "undertone": _undertone_class(b_std),
    }


def sample_skin(rgb_img: np.ndarray, points_px: Sequence[tuple[int, int]]) -> dict:
    """Sample skin metrics from each region defined in SAMPLE_REGIONS.

    Args:
        rgb_img: HxWx3 RGB image (numpy array)
        points_px: full landmark list in pixel coords (478 points)

    Returns:
        dict with per-region metrics and an aggregated composite.
    """
    if rgb_img is None or rgb_img.ndim != 3:
        return {"ok": False, "error": "invalid_image"}
    if not points_px or len(points_px) < 200:
        return {"ok": False, "error": "insufficient_landmarks"}

    per_region = {}
    valid_lab = []  # collect (L, a, b) from cheek/forehead for aggregate

    for name, idx in SAMPLE_REGIONS.items():
        if idx >= len(points_px):
            per_region[name] = {"error": "landmark_missing"}
            continue
        cx, cy = points_px[idx]
        patch = _sample_patch(rgb_img, cx, cy)
        if patch is None:
            per_region[name] = {"error": "patch_out_of_bounds"}
            continue
        metrics = _patch_metrics(patch)
        per_region[name] = metrics
        if name in ("forehead", "cheek_r", "cheek_l"):
            valid_lab.append(metrics["lab_mean"])

    # Composite from forehead + cheeks (best representative skin)
    composite = None
    if valid_lab:
        L_avg = sum(v[0] for v in valid_lab) / len(valid_lab)
        a_avg = sum(v[1] for v in valid_lab) / len(valid_lab)
        b_avg = sum(v[2] for v in valid_lab) / len(valid_lab)
        ita_comp = math.degrees(math.atan2(L_avg - 50.0, b_avg)) if b_avg != 0 else 90.0
        composite = {
            "lab_mean":  (round(L_avg, 1), round(a_avg, 1), round(b_avg, 1)),
            "ita":       round(ita_comp, 1),
            "ita_class": _ita_class(ita_comp),
            "undertone": _undertone_class(b_avg),
            "lightness_L":  round(L_avg, 1),
            "redness_a":    round(a_avg, 1),
            "yellowness_b": round(b_avg, 1),
        }

    return {
        "ok": True,
        "per_region": per_region,
        "composite": composite,
        "patch_size_px": PATCH_HALF_PX * 2 + 1,
        "regions_sampled": len(per_region),
    }

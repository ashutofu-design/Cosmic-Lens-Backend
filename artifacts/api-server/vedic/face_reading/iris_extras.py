"""
Iris/pupil extras: mm-scale conversion + pupil dilation estimate.

Mediapipe gives iris perimeter (4 points) but no pupil. We estimate pupil
radius via OpenCV HoughCircles inside a tight ROI around the iris.

Real-world references:
  • Adult iris diameter:  11.7 mm ± 0.5 mm  (highly stable, used as a scale ref)
  • Adult pupil diameter: 2–4 mm bright light, 4–8 mm dim light
  • Adult IPD (inter-pupillary): M 64 mm, F 61.7 mm
"""
from __future__ import annotations

import math

import cv2
import numpy as np

IRIS_DIAMETER_MM = 11.7   # near-constant across adults; better scale reference than IPD


def estimate_pupil(rgb_img: np.ndarray, iris_center_px, iris_radius_px: float) -> dict:
    """Detect pupil radius inside an iris ROI using HoughCircles.

    Returns dict with pupil_radius_px, pupil_radius_mm (using iris=11.7mm), and
    dilation ratio (pupil/iris). Falls back gracefully if Hough fails.
    """
    cx, cy = int(iris_center_px[0]), int(iris_center_px[1])
    R = int(round(iris_radius_px))
    if R < 4:
        return {"ok": False, "error": "iris_too_small"}

    h, w = rgb_img.shape[:2]
    pad = R + 2
    x0, y0 = max(0, cx - pad), max(0, cy - pad)
    x1, y1 = min(w, cx + pad + 1), min(h, cy + pad + 1)
    if x1 - x0 < 8 or y1 - y0 < 8:
        return {"ok": False, "error": "roi_out_of_bounds"}

    roi = rgb_img[y0:y1, x0:x1]
    gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    gray = cv2.medianBlur(gray, 3)

    # Pupil is the darkest small disc inside the iris
    min_r = max(2, int(R * 0.25))
    max_r = max(min_r + 2, int(R * 0.65))

    try:
        circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, dp=1.2,
            minDist=max(8, R), param1=80, param2=14,
            minRadius=min_r, maxRadius=max_r,
        )
    except cv2.error:
        circles = None

    pupil_r = None
    if circles is not None and len(circles[0]) > 0:
        # Pick the circle nearest the iris center
        best = min(circles[0], key=lambda c: (c[0] - (cx - x0)) ** 2 + (c[1] - (cy - y0)) ** 2)
        pupil_r = float(best[2])

    if pupil_r is None:
        # Fallback: darkest patch radius via thresholding
        _, dark = cv2.threshold(gray, max(20, int(gray.mean() * 0.55)), 255, cv2.THRESH_BINARY_INV)
        m = cv2.moments(dark)
        if m["m00"] > 5:
            pupil_r = math.sqrt(m["m00"] / math.pi) * 0.6   # area→radius, conservative
        else:
            return {"ok": False, "error": "pupil_not_found"}

    px_per_mm = (2.0 * iris_radius_px) / IRIS_DIAMETER_MM
    pupil_mm = pupil_r / px_per_mm if px_per_mm > 0 else 0.0
    iris_mm = (2.0 * iris_radius_px) / px_per_mm if px_per_mm > 0 else 0.0
    dilation = pupil_r / iris_radius_px if iris_radius_px > 0 else 0.0

    if dilation < 0.18:    state = "constricted"
    elif dilation < 0.35:  state = "normal_bright"
    elif dilation < 0.55:  state = "normal_dim"
    else:                  state = "dilated"

    return {
        "ok": True,
        "pupil_radius_px":  round(pupil_r, 2),
        "pupil_diameter_mm": round(2 * pupil_mm, 2),
        "iris_diameter_mm":  round(iris_mm, 2),
        "px_per_mm_iris":    round(px_per_mm, 3),
        "dilation_ratio":    round(dilation, 3),
        "dilation_state":    state,
    }


def iris_mm_summary(right_radius_px: float, left_radius_px: float, ipd_px: float) -> dict:
    """Convert iris/IPD pixels to mm using the iris-diameter scale (more
    reliable than IPD-baseline because iris size is near-constant)."""
    avg_iris_radius = (right_radius_px + left_radius_px) / 2.0
    if avg_iris_radius <= 0:
        return {"ok": False, "error": "invalid_iris_radius"}
    px_per_mm = (2.0 * avg_iris_radius) / IRIS_DIAMETER_MM
    return {
        "ok": True,
        "px_per_mm": round(px_per_mm, 3),
        "right_iris_diameter_mm": round((2 * right_radius_px) / px_per_mm, 2),
        "left_iris_diameter_mm":  round((2 * left_radius_px)  / px_per_mm, 2),
        "ipd_mm":                 round(ipd_px / px_per_mm, 2),
        "scale_reference":        f"iris_diameter={IRIS_DIAMETER_MM}mm",
    }

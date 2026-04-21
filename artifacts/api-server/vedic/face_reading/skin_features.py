"""
Advanced skin/facial-feature analyzers.

Modules used by future engines:
  • detect_moles         — Samudrika Shastra (tilak / til positions)
  • estimate_oiliness    — Ayurvedic Prakriti (Pitta vs Vata)
  • detect_wrinkles      — Lalat Rekha (Engine 11)
  • detect_dark_circles  — Health (Engine 5)
  • detect_beard         — anthropometry chin-landmark accuracy guard
  • estimate_eyebrow_density — Mukha Lakshana (Engine 10)
  • sample_hair_color    — Wu Xing element classifier (Engine 16)

All functions accept (rgb_img, points_px) and return dicts. Methods are
classical OpenCV (no ML weights needed) — robust enough for our scoring.
"""
from __future__ import annotations

import math
from typing import Sequence

import cv2
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# 1. Moles / spots (Samudrika tilak detection)
# ─────────────────────────────────────────────────────────────────────────────
def detect_moles(rgb_img: np.ndarray, points_px: Sequence[tuple[int, int]],
                 face_bbox: dict) -> dict:
    """Find dark isolated spots inside the face region (likely moles/freckles)."""
    if not face_bbox:
        return {"ok": False, "error": "no_face_bbox"}

    x, y, bw, bh = face_bbox["x"], face_bbox["y"], face_bbox["w"], face_bbox["h"]
    H, W = rgb_img.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + bw), min(H, y + bh)
    face_roi = rgb_img[y0:y1, x0:x1]
    if face_roi.size == 0:
        return {"ok": False, "error": "empty_roi"}

    gray = cv2.cvtColor(face_roi, cv2.COLOR_RGB2GRAY)
    gray = cv2.medianBlur(gray, 3)

    # Local-mean adaptive: dark spots stand out vs neighbours
    mean = cv2.GaussianBlur(gray, (31, 31), 0)
    diff = cv2.subtract(mean, gray)            # positive where pixel is darker than nbhd
    _, mask = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Mole candidates: small (3–80 px area), roundish (extent > 0.5)
    moles = []
    for c in contours:
        area = cv2.contourArea(c)
        if not (3 <= area <= 80):
            continue
        x_c, y_c, w_c, h_c = cv2.boundingRect(c)
        bbox_area = max(1, w_c * h_c)
        extent = area / bbox_area
        if extent < 0.5:
            continue
        # Aspect ratio close to 1
        if max(w_c, h_c) / max(1, min(w_c, h_c)) > 2.2:
            continue
        cx_face = int(x_c + w_c / 2)
        cy_face = int(y_c + h_c / 2)
        cx_img, cy_img = cx_face + x0, cy_face + y0
        # Normalize position relative to face bbox: (0..1, 0..1)
        nx = round((cx_img - x) / bw, 3)
        ny = round((cy_img - y) / bh, 3)
        zone = _classify_face_zone(nx, ny)
        moles.append({
            "x_px": cx_img, "y_px": cy_img,
            "norm_x": nx, "norm_y": ny,
            "area_px": int(area),
            "zone": zone,
        })
    moles.sort(key=lambda m: -m["area_px"])
    return {
        "ok": True,
        "count": len(moles),
        "moles": moles[:12],            # top 12 only (samudrika rarely uses >12)
        "method": "adaptive_dark_blob",
    }


def _classify_face_zone(nx: float, ny: float) -> str:
    """Coarse 3×3 grid for mole-zone mapping (Samudrika simplified)."""
    col = "left" if nx < 0.40 else ("right" if nx > 0.60 else "center")
    row = "upper" if ny < 0.35 else ("lower" if ny > 0.70 else "middle")
    return f"{row}_{col}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Oiliness / specular highlights (Pitta marker)
# ─────────────────────────────────────────────────────────────────────────────
def estimate_oiliness(rgb_img: np.ndarray, points_px: Sequence[tuple[int, int]]) -> dict:
    """Specular highlight ratio in T-zone (forehead + nose)."""
    if len(points_px) < 200:
        return {"ok": False, "error": "insufficient_landmarks"}

    H, W = rgb_img.shape[:2]
    forehead_pts = [points_px[i] for i in (10, 67, 109, 151, 338, 297, 9)]
    nose_pts = [points_px[i] for i in (168, 6, 197, 195, 5, 4, 1, 19)]
    cheek_pts = [points_px[i] for i in (50, 280, 117, 346, 205, 425)]

    def _patch_specular_ratio(pts):
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        x0, y0 = max(0, min(xs) - 5), max(0, min(ys) - 5)
        x1, y1 = min(W, max(xs) + 5), min(H, max(ys) + 5)
        if x1 - x0 < 6 or y1 - y0 < 6:
            return None
        patch = rgb_img[y0:y1, x0:x1]
        gray = cv2.cvtColor(patch, cv2.COLOR_RGB2GRAY)
        return float((gray > 220).mean()), float(gray.mean())

    t_zone = _patch_specular_ratio(forehead_pts + nose_pts)
    cheeks = _patch_specular_ratio(cheek_pts)
    if t_zone is None or cheeks is None:
        return {"ok": False, "error": "patch_oob"}

    t_spec, t_mean = t_zone
    c_spec, c_mean = cheeks
    score = round(min(1.0, (t_spec * 6.0) + max(0.0, (t_spec - c_spec) * 4.0)), 2)

    if score > 0.6:    cls = "oily"
    elif score > 0.3:  cls = "combination"
    elif score > 0.1:  cls = "normal"
    else:              cls = "dry"

    return {
        "ok": True,
        "tzone_specular_ratio":  round(t_spec, 4),
        "cheek_specular_ratio":  round(c_spec, 4),
        "tzone_brightness":      round(t_mean, 2),
        "cheek_brightness":      round(c_mean, 2),
        "oiliness_score":        score,
        "skin_type":             cls,   # oily / combination / normal / dry
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Wrinkles / forehead lines (Lalat Rekha)
# ─────────────────────────────────────────────────────────────────────────────
def detect_wrinkles(rgb_img: np.ndarray, points_px: Sequence[tuple[int, int]]) -> dict:
    """Edge-density estimate of horizontal forehead lines + crow's feet."""
    if len(points_px) < 200:
        return {"ok": False, "error": "insufficient_landmarks"}
    H, W = rgb_img.shape[:2]

    def _edge_density(pts, expand_x=0, expand_y=0):
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        x0 = max(0, min(xs) - expand_x); y0 = max(0, min(ys) - expand_y)
        x1 = min(W, max(xs) + expand_x); y1 = min(H, max(ys) + expand_y)
        if x1 - x0 < 10 or y1 - y0 < 10:
            return None
        patch = rgb_img[y0:y1, x0:x1]
        gray = cv2.cvtColor(patch, cv2.COLOR_RGB2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(gray, 30, 90)
        return float(edges.mean()) / 255.0   # 0..1

    # Forehead band: above eyebrows, below hairline (use mesh top + brows)
    forehead_top = points_px[10]
    brow_r, brow_l = points_px[107], points_px[336]
    fh_pts = [forehead_top, (brow_r[0], brow_r[1] - 5), (brow_l[0], brow_l[1] - 5)]
    forehead_density = _edge_density(fh_pts, expand_x=15, expand_y=5)

    # Crow's feet: outer corners of eyes
    crow_r = _edge_density([points_px[33], points_px[127], points_px[234]], expand_x=8, expand_y=8)
    crow_l = _edge_density([points_px[263], points_px[356], points_px[454]], expand_x=8, expand_y=8)

    # Nasolabial (smile lines): nose wing → mouth corner
    nlf_r = _edge_density([points_px[129], points_px[61]], expand_x=6, expand_y=4)
    nlf_l = _edge_density([points_px[358], points_px[291]], expand_x=6, expand_y=4)

    def _grade(v):
        if v is None: return "n/a"
        if v > 0.18: return "deep"
        if v > 0.10: return "moderate"
        if v > 0.05: return "fine"
        return "minimal"

    return {
        "ok": True,
        "forehead_edge_density":   round(forehead_density, 4) if forehead_density is not None else None,
        "forehead_lines":          _grade(forehead_density),
        "crow_feet_right":         _grade(crow_r),
        "crow_feet_left":          _grade(crow_l),
        "nasolabial_right":        _grade(nlf_r),
        "nasolabial_left":         _grade(nlf_l),
        "method":                  "canny_edge_density",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. Dark circles (health marker)
# ─────────────────────────────────────────────────────────────────────────────
def detect_dark_circles(rgb_img: np.ndarray, points_px: Sequence[tuple[int, int]]) -> dict:
    if len(points_px) < 200:
        return {"ok": False, "error": "insufficient_landmarks"}
    H, W = rgb_img.shape[:2]
    lab_full = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2LAB)

    def _under_eye_L_vs_cheek(under_idx, cheek_idx):
        ux, uy = points_px[under_idx]
        cx, cy = points_px[cheek_idx]
        size = max(4, abs(uy - cy) // 2)
        u0x, u0y = max(0, ux - size), max(0, uy - 1)
        u1x, u1y = min(W, ux + size), min(H, uy + size)
        c0x, c0y = max(0, cx - size), max(0, cy - size // 2)
        c1x, c1y = min(W, cx + size), min(H, cy + size)
        if u1x - u0x < 4 or u1y - u0y < 4 or c1x - c0x < 4 or c1y - c0y < 4:
            return None
        u_L = float(lab_full[u0y:u1y, u0x:u1x, 0].mean())
        c_L = float(lab_full[c0y:c1y, c0x:c1x, 0].mean())
        # Convert from OpenCV 0-255 to standard 0-100
        return (c_L - u_L) * 100.0 / 255.0

    r_drop = _under_eye_L_vs_cheek(145, 50)    # right under-eye vs right cheek
    l_drop = _under_eye_L_vs_cheek(374, 280)   # left  under-eye vs left  cheek

    def _grade(v):
        if v is None:    return "n/a"
        if v > 8:        return "severe"
        if v > 5:        return "moderate"
        if v > 2:        return "mild"
        return "none"

    return {
        "ok": True,
        "lightness_drop_right_L": round(r_drop, 2) if r_drop is not None else None,
        "lightness_drop_left_L":  round(l_drop, 2) if l_drop is not None else None,
        "right_grade":            _grade(r_drop),
        "left_grade":             _grade(l_drop),
        "method":                 "lab_L_under_eye_vs_cheek",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. Beard / moustache mask
# ─────────────────────────────────────────────────────────────────────────────
def detect_beard(rgb_img: np.ndarray, points_px: Sequence[tuple[int, int]]) -> dict:
    """Dark non-skin pixel ratio in chin + upper-lip ROIs."""
    if len(points_px) < 200:
        return {"ok": False, "error": "insufficient_landmarks"}
    H, W = rgb_img.shape[:2]

    def _dark_ratio(pts, pad_x=4, pad_y=4):
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        x0 = max(0, min(xs) - pad_x); y0 = max(0, min(ys) - pad_y)
        x1 = min(W, max(xs) + pad_x); y1 = min(H, max(ys) + pad_y)
        if x1 - x0 < 6 or y1 - y0 < 6:
            return None, None
        patch = rgb_img[y0:y1, x0:x1]
        hsv = cv2.cvtColor(patch, cv2.COLOR_RGB2HSV)
        # Beard pixels: low V (dark) AND low-medium S (not pure colour)
        mask = (hsv[..., 2] < 90) & (hsv[..., 1] < 110)
        return float(mask.mean()), int(mask.sum())

    chin_pts = [points_px[i] for i in (152, 175, 199, 200, 18, 83, 313)]
    moustache_pts = [points_px[i] for i in (164, 0, 11, 12, 268, 38)]

    chin_r, _ = _dark_ratio(chin_pts, pad_x=6, pad_y=4)
    must_r, _ = _dark_ratio(moustache_pts, pad_x=4, pad_y=2)

    chin_r = chin_r or 0.0
    must_r = must_r or 0.0

    if chin_r > 0.35 and must_r > 0.25:    cls = "full_beard"
    elif chin_r > 0.25:                     cls = "chin_beard_or_stubble"
    elif must_r > 0.25:                     cls = "moustache_only"
    elif chin_r > 0.12 or must_r > 0.10:    cls = "light_stubble"
    else:                                   cls = "clean_shaven"

    return {
        "ok": True,
        "chin_dark_ratio":      round(chin_r, 3),
        "moustache_dark_ratio": round(must_r, 3),
        "facial_hair":          cls,
        "warns_landmark_accuracy": cls in ("full_beard", "chin_beard_or_stubble"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6. Eyebrow density (Mukha Lakshana)
# ─────────────────────────────────────────────────────────────────────────────
def estimate_eyebrow_density(rgb_img: np.ndarray, points_px: Sequence[tuple[int, int]]) -> dict:
    """Dark pixel ratio inside each eyebrow polygon."""
    if len(points_px) < 200:
        return {"ok": False, "error": "insufficient_landmarks"}
    H, W = rgb_img.shape[:2]
    hsv = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2HSV)

    BROW_R = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
    BROW_L = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]

    def _density(idxs):
        pts = np.array([points_px[i] for i in idxs], dtype=np.int32)
        mask = np.zeros((H, W), dtype=np.uint8)
        try:
            cv2.fillConvexPoly(mask, cv2.convexHull(pts), 255)
        except Exception:
            return None, None, None
        roi = hsv[mask == 255]
        if roi.size == 0:
            return None, None, None
        dark = (roi[:, 2] < 100) & (roi[:, 1] < 130)
        return float(dark.mean()), int(mask.sum() // 255), int(dark.sum())

    r_dens, r_area, r_dark = _density(BROW_R)
    l_dens, l_area, l_dark = _density(BROW_L)

    def _grade(v):
        if v is None:   return "n/a"
        if v > 0.55:    return "very_thick"
        if v > 0.35:    return "thick"
        if v > 0.18:    return "medium"
        if v > 0.08:    return "thin"
        return "very_thin_or_groomed"

    return {
        "ok": True,
        "right_density": round(r_dens, 3) if r_dens is not None else None,
        "left_density":  round(l_dens, 3) if l_dens is not None else None,
        "right_grade":   _grade(r_dens),
        "left_grade":    _grade(l_dens),
        "right_area_px": r_area,
        "left_area_px":  l_area,
        "method":        "hsv_dark_ratio_in_brow_polygon",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 7. Hair colour sample (above hairline)
# ─────────────────────────────────────────────────────────────────────────────
def sample_hair_color(rgb_img: np.ndarray, points_px: Sequence[tuple[int, int]],
                      hairline_y_px: int | None) -> dict:
    """Sample a strip above the estimated hairline. Skip if no hairline found."""
    if hairline_y_px is None or hairline_y_px <= 5:
        return {"ok": False, "error": "no_hairline"}

    H, W = rgb_img.shape[:2]
    forehead_top_x = points_px[10][0]
    half_w = max(20, int((points_px[356][0] - points_px[127][0]) * 0.20))

    y0 = max(0, hairline_y_px - 30)
    y1 = max(y0 + 1, hairline_y_px - 4)
    x0 = max(0, forehead_top_x - half_w)
    x1 = min(W, forehead_top_x + half_w)
    if x1 - x0 < 8 or y1 - y0 < 6:
        return {"ok": False, "error": "roi_too_small"}

    patch = rgb_img[y0:y1, x0:x1]
    flat = patch.reshape(-1, 3).astype(np.float32)
    # Drop very bright (background sky / wall) pixels
    brightness = flat.mean(axis=1)
    keep = brightness < 200
    if keep.sum() < 20:
        return {"ok": False, "error": "no_hair_pixels"}
    hair = flat[keep]
    rgb_mean = tuple(round(float(c), 1) for c in hair.mean(axis=0))

    pix = np.uint8([[list(rgb_mean)]])
    hsv = cv2.cvtColor(pix, cv2.COLOR_RGB2HSV)[0, 0]
    L = float(cv2.cvtColor(pix, cv2.COLOR_RGB2LAB)[0, 0, 0]) * 100.0 / 255.0

    if L < 22:                       cls = "black"
    elif L < 38:                     cls = "dark_brown"
    elif L < 55:                     cls = "brown"
    elif L < 70 and hsv[0] < 25:     cls = "light_brown_or_blonde"
    elif L < 85:                     cls = "blonde_or_grey"
    else:                            cls = "white_or_grey"

    return {
        "ok": True,
        "rgb_mean":   rgb_mean,
        "hsv_mean":   tuple(int(v) for v in hsv),
        "lightness_L": round(L, 1),
        "hair_color": cls,
        "sample_size_px": int(keep.sum()),
    }

"""
Mediapipe Face Mesh wrapper.

Extracts 468 face landmarks (or 478 with refined eye/iris) from an image.
Returns normalized + pixel coordinates plus a quality assessment.
This is the FOUNDATION (Step 0) used by all 20 face-reading engines.
"""
from __future__ import annotations

import io
import math
from dataclasses import dataclass, field, asdict
from typing import Optional

import cv2
import numpy as np
from PIL import Image

import mediapipe as mp

# ── Singleton FaceMesh (heavy to construct; reuse across requests) ──────────
_FACE_MESH = None


def _get_face_mesh():
    global _FACE_MESH
    if _FACE_MESH is None:
        _FACE_MESH = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,   # adds iris + lip refinement → 478 points
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    return _FACE_MESH


# ── Result containers ───────────────────────────────────────────────────────
@dataclass
class Quality:
    face_detected: bool = False
    landmark_count: int = 0
    image_width: int = 0
    image_height: int = 0
    face_bbox: dict = field(default_factory=dict)         # {x, y, w, h, area_ratio}
    yaw_deg: float = 0.0       # left-right rotation (0 = facing camera)
    pitch_deg: float = 0.0     # up-down tilt
    roll_deg: float = 0.0      # head tilt sideways
    brightness: float = 0.0    # 0–255 mean luma
    sharpness: float = 0.0     # Laplacian variance (higher = sharper)
    issues: list = field(default_factory=list)
    score: int = 0             # 0–100 overall usability


@dataclass
class LandmarkSet:
    angle: str                         # "front" | "left" | "right"
    points_norm: list = field(default_factory=list)  # [(x,y,z) ...] normalized 0–1
    points_px: list = field(default_factory=list)    # [(x,y) ...] pixel coords
    quality: Quality = field(default_factory=Quality)


# ── Public API ──────────────────────────────────────────────────────────────
def extract_landmarks(image_bytes: bytes, angle: str = "front") -> LandmarkSet:
    """Decode image bytes → run FaceMesh → return landmarks + quality.

    angle: 'front' | 'left' | 'right' — only used for labeling here, but
    quality thresholds differ per angle (profile shots have different yaw).
    """
    result = LandmarkSet(angle=angle)

    # ── 1. Decode image ────────────────────────────────────────────────────
    try:
        pil = Image.open(io.BytesIO(image_bytes))
        if pil.mode != "RGB":
            pil = pil.convert("RGB")
        img_rgb = np.array(pil)
    except Exception as e:
        result.quality.issues.append(f"image_decode_failed: {e}")
        return result

    h, w = img_rgb.shape[:2]
    result.quality.image_width = w
    result.quality.image_height = h

    # ── 2. Quality pre-checks (brightness + sharpness) ─────────────────────
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    result.quality.brightness = float(round(gray.mean(), 2))
    result.quality.sharpness = float(round(cv2.Laplacian(gray, cv2.CV_64F).var(), 2))

    if result.quality.brightness < 50:
        result.quality.issues.append("too_dark")
    elif result.quality.brightness > 230:
        result.quality.issues.append("too_bright")
    if result.quality.sharpness < 30:
        result.quality.issues.append("blurry")

    # ── 3. Run FaceMesh ────────────────────────────────────────────────────
    fm = _get_face_mesh()
    mp_result = fm.process(img_rgb)

    if not mp_result.multi_face_landmarks:
        result.quality.issues.append("no_face_detected")
        result.quality.score = 0
        return result

    landmarks = mp_result.multi_face_landmarks[0].landmark
    result.quality.face_detected = True
    result.quality.landmark_count = len(landmarks)

    # ── 4. Coordinates ─────────────────────────────────────────────────────
    pts_norm = [(round(lm.x, 6), round(lm.y, 6), round(lm.z, 6)) for lm in landmarks]
    pts_px = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
    result.points_norm = pts_norm
    result.points_px = pts_px

    # ── 5. Bounding box ────────────────────────────────────────────────────
    xs = [p[0] for p in pts_px]
    ys = [p[1] for p in pts_px]
    bx, by = min(xs), min(ys)
    bw, bh = max(xs) - bx, max(ys) - by
    result.quality.face_bbox = {
        "x": bx, "y": by, "w": bw, "h": bh,
        "area_ratio": round((bw * bh) / float(w * h), 4),
    }
    if result.quality.face_bbox["area_ratio"] < 0.05:
        result.quality.issues.append("face_too_small")

    # ── 6. Head pose (approx) using key landmark triangulation ─────────────
    # Standard mediapipe canonical face indices:
    # 1 = nose tip, 33 = right eye outer, 263 = left eye outer,
    # 61 = right mouth corner, 291 = left mouth corner, 199 = chin
    try:
        yaw, pitch, roll = _estimate_pose(pts_px, w, h)
        result.quality.yaw_deg = round(yaw, 1)
        result.quality.pitch_deg = round(pitch, 1)
        result.quality.roll_deg = round(roll, 1)

        # Per-angle yaw expectations
        if angle == "front" and abs(yaw) > 18:
            result.quality.issues.append(f"not_frontal (yaw={yaw:.0f}°)")
        elif angle == "left" and yaw > -25:   # face turned to user's left → camera sees right side
            result.quality.issues.append(f"left_profile_too_shallow (yaw={yaw:.0f}°)")
        elif angle == "right" and yaw < 25:
            result.quality.issues.append(f"right_profile_too_shallow (yaw={yaw:.0f}°)")
        if abs(roll) > 20:
            result.quality.issues.append(f"head_tilted (roll={roll:.0f}°)")
    except Exception as e:
        result.quality.issues.append(f"pose_estimation_failed: {e}")

    # ── 7. Final quality score (0–100) ─────────────────────────────────────
    score = 100
    if "blurry" in result.quality.issues: score -= 30
    if "too_dark" in result.quality.issues or "too_bright" in result.quality.issues: score -= 20
    if "face_too_small" in result.quality.issues: score -= 25
    if any(i.startswith("not_frontal") or i.startswith("left_profile_too_shallow")
           or i.startswith("right_profile_too_shallow") for i in result.quality.issues): score -= 25
    if any(i.startswith("head_tilted") for i in result.quality.issues): score -= 10
    result.quality.score = max(0, score)

    return result


def _estimate_pose(pts_px, img_w: int, img_h: int) -> tuple[float, float, float]:
    """Rough head-pose estimation using solvePnP on 6 canonical landmarks.

    Returns (yaw, pitch, roll) in degrees.
    """
    # Mediapipe Face Mesh indices for 6 canonical points
    image_pts = np.array([
        pts_px[1],     # nose tip
        pts_px[152],   # chin
        pts_px[33],    # right eye outer corner
        pts_px[263],   # left eye outer corner
        pts_px[61],    # right mouth corner
        pts_px[291],   # left mouth corner
    ], dtype=np.float64)

    # 3D model points (canonical face, in mm-ish units)
    model_pts = np.array([
        (0.0, 0.0, 0.0),
        (0.0, -63.6, -12.5),
        (-43.3, 32.7, -26.0),
        (43.3, 32.7, -26.0),
        (-28.9, -28.9, -24.1),
        (28.9, -28.9, -24.1),
    ], dtype=np.float64)

    focal = float(img_w)
    center = (img_w / 2.0, img_h / 2.0)
    cam_matrix = np.array([
        [focal, 0, center[0]],
        [0, focal, center[1]],
        [0, 0, 1],
    ], dtype=np.float64)
    dist = np.zeros((4, 1))

    ok, rvec, tvec = cv2.solvePnP(model_pts, image_pts, cam_matrix, dist,
                                   flags=cv2.SOLVEPNP_ITERATIVE)
    if not ok:
        return (0.0, 0.0, 0.0)

    rot_mat, _ = cv2.Rodrigues(rvec)
    sy = math.sqrt(rot_mat[0, 0] ** 2 + rot_mat[1, 0] ** 2)
    if sy > 1e-6:
        pitch = math.degrees(math.atan2(rot_mat[2, 1], rot_mat[2, 2]))
        yaw   = math.degrees(math.atan2(-rot_mat[2, 0], sy))
        roll  = math.degrees(math.atan2(rot_mat[1, 0], rot_mat[0, 0]))
    else:
        pitch = math.degrees(math.atan2(-rot_mat[1, 2], rot_mat[1, 1]))
        yaw   = math.degrees(math.atan2(-rot_mat[2, 0], sy))
        roll  = 0.0
    return yaw, pitch, roll


def landmark_set_to_dict(ls: LandmarkSet, include_points: bool = False) -> dict:
    """Compact dict for API responses. By default omits the heavy points list."""
    d = {
        "angle": ls.angle,
        "quality": asdict(ls.quality),
    }
    if include_points:
        d["points_norm"] = ls.points_norm
        d["points_px"] = ls.points_px
    else:
        d["landmark_count"] = len(ls.points_norm)
    return d

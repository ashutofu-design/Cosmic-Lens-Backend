"""
Mediapipe Face Mesh wrapper  (v2 — full Step-0 foundation).

Extracts up to 478 face landmarks (refined model: iris + lips) from an
image AND performs all downstream foundation analyses needed by the 20
face-reading engines.

Foundation v2 adds:
  • EXIF auto-rotation  (iPhone sideways photos auto-corrected)
  • HEIC / HEIF support (iPhone .heic photos)
  • Multi-face rejection (group photos rejected with clear error)
  • Iris / pupil landmarks exposed (centers + radii + gaze direction)
  • Skin pixel sampling (5 regions → ITA, undertone, redness, yellowness)
  • Hairline (trichion) estimation (skin-walk algorithm above mesh-top)
  • Expression neutrality check (smile / closed eyes / open mouth flags)
  • Glasses / occlusion detection (brightness profile around eyes)
  • Profile (left/right) image processing alongside front

This is the FOUNDATION used by all 20 face-reading engines.
"""
from __future__ import annotations

import io
import math
from dataclasses import dataclass, field, asdict
from typing import Optional

import cv2
import numpy as np
from PIL import Image, ImageOps

import mediapipe as mp

# Register HEIC/HEIF support so PIL can open .heic files (iPhone default)
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    _HEIF_OK = True
except Exception:
    _HEIF_OK = False

# Local helpers
from . import skin as _skin
from . import hairline as _hairline


# ── Singletons (heavy to construct; reuse across requests) ──────────────────
_FACE_MESH = None
_FACE_DETECTOR = None


def _get_face_mesh():
    global _FACE_MESH
    if _FACE_MESH is None:
        _FACE_MESH = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=4,            # detect up to 4 so we can reject multi-face
            refine_landmarks=True,      # adds iris + lip refinement → 478 points
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    return _FACE_MESH


def _get_face_detector():
    """Short-range face detector for fast multi-face counting."""
    global _FACE_DETECTOR
    if _FACE_DETECTOR is None:
        _FACE_DETECTOR = mp.solutions.face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )
    return _FACE_DETECTOR


# ── Result containers ───────────────────────────────────────────────────────
@dataclass
class Quality:
    face_detected: bool = False
    landmark_count: int = 0
    face_count: int = 0
    image_width: int = 0
    image_height: int = 0
    face_bbox: dict = field(default_factory=dict)
    yaw_deg: float = 0.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    brightness: float = 0.0
    sharpness: float = 0.0
    issues: list = field(default_factory=list)
    score: int = 0


@dataclass
class IrisInfo:
    right_center_px: tuple = (0, 0)
    left_center_px:  tuple = (0, 0)
    right_radius_px: float = 0.0
    left_radius_px:  float = 0.0
    inter_pupillary_distance_px: float = 0.0
    gaze_direction:  str = "unknown"     # straight | left | right | up | down
    gaze_offset_norm_x: float = 0.0      # pupil offset from eye center, normalized
    gaze_offset_norm_y: float = 0.0


@dataclass
class ExpressionInfo:
    smile_score: float = 0.0             # 0..1+; >0.15 = smiling
    eyes_open_score: float = 0.0         # 0..1; <0.2 = eyes closed
    mouth_open_score: float = 0.0        # 0..1; >0.15 = mouth open
    is_neutral: bool = True
    flags: list = field(default_factory=list)


@dataclass
class OcclusionInfo:
    glasses_likely: bool = False
    glasses_score: float = 0.0           # 0..1, higher = more likely
    eye_region_brightness_diff: float = 0.0
    notes: list = field(default_factory=list)


@dataclass
class LandmarkSet:
    angle: str
    points_norm: list = field(default_factory=list)
    points_px: list = field(default_factory=list)
    quality: Quality = field(default_factory=Quality)
    iris: Optional[IrisInfo] = None
    expression: Optional[ExpressionInfo] = None
    occlusion: Optional[OcclusionInfo] = None
    skin: Optional[dict] = None
    hairline: Optional[dict] = None


# ── Public API ──────────────────────────────────────────────────────────────
def extract_landmarks(image_bytes: bytes,
                      angle: str = "front",
                      enable_skin: bool = True,
                      enable_hairline: bool = True) -> LandmarkSet:
    """Decode image bytes → run FaceMesh → return landmarks + full v2 metadata.

    angle: 'front' | 'left' | 'right' — yaw thresholds & checks differ.
    """
    result = LandmarkSet(angle=angle)

    # ── 1. Decode image (HEIC + EXIF auto-rotation handled) ────────────────
    try:
        pil = Image.open(io.BytesIO(image_bytes))
        # Apply EXIF orientation so portraits taken sideways come out upright.
        # This MUST happen before any pixel work or face detection will fail.
        pil = ImageOps.exif_transpose(pil)
        if pil.mode != "RGB":
            pil = pil.convert("RGB")
        img_rgb = np.array(pil)
    except Exception as e:
        result.quality.issues.append(f"image_decode_failed: {e}")
        return result

    h, w = img_rgb.shape[:2]
    result.quality.image_width = w
    result.quality.image_height = h

    # ── 2. Brightness + sharpness ──────────────────────────────────────────
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    result.quality.brightness = float(round(gray.mean(), 2))
    result.quality.sharpness = float(round(cv2.Laplacian(gray, cv2.CV_64F).var(), 2))
    if result.quality.brightness < 50:
        result.quality.issues.append("too_dark")
    elif result.quality.brightness > 230:
        result.quality.issues.append("too_bright")
    if result.quality.sharpness < 30:
        result.quality.issues.append("blurry")

    # ── 3. Multi-face rejection (run BEFORE FaceMesh so we get true count) ─
    try:
        det = _get_face_detector().process(img_rgb)
        face_count = len(det.detections) if det.detections else 0
        result.quality.face_count = face_count
        if face_count > 1:
            result.quality.issues.append(f"multiple_faces_detected (count={face_count})")
            # Continue but flag — front photos with >1 face are auto-rejected by score
    except Exception as e:
        result.quality.issues.append(f"face_detector_failed: {e}")

    # ── 4. Run FaceMesh ────────────────────────────────────────────────────
    fm = _get_face_mesh()
    mp_result = fm.process(img_rgb)

    if not mp_result.multi_face_landmarks:
        result.quality.issues.append("no_face_detected")
        result.quality.score = 0
        return result

    landmarks = mp_result.multi_face_landmarks[0].landmark
    result.quality.face_detected = True
    result.quality.landmark_count = len(landmarks)

    # ── 5. Coordinates ─────────────────────────────────────────────────────
    pts_norm = [(round(lm.x, 6), round(lm.y, 6), round(lm.z, 6)) for lm in landmarks]
    pts_px = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
    result.points_norm = pts_norm
    result.points_px = pts_px

    # ── 6. Bounding box ────────────────────────────────────────────────────
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

    # ── 7. Head pose (solvePnP on 6 canonical points) ──────────────────────
    try:
        yaw, pitch, roll = _estimate_pose(pts_px, w, h)
        result.quality.yaw_deg = round(yaw, 1)
        result.quality.pitch_deg = round(pitch, 1)
        result.quality.roll_deg = round(roll, 1)
        if angle == "front" and abs(yaw) > 18:
            result.quality.issues.append(f"not_frontal (yaw={yaw:.0f}°)")
        elif angle == "left" and yaw > -25:
            result.quality.issues.append(f"left_profile_too_shallow (yaw={yaw:.0f}°)")
        elif angle == "right" and yaw < 25:
            result.quality.issues.append(f"right_profile_too_shallow (yaw={yaw:.0f}°)")
        if abs(roll) > 20:
            result.quality.issues.append(f"head_tilted (roll={roll:.0f}°)")
    except Exception as e:
        result.quality.issues.append(f"pose_estimation_failed: {e}")

    # ── 8. Iris / pupil landmarks (refined model: indices 468-477) ─────────
    if len(pts_px) >= 478:
        result.iris = _compute_iris_info(pts_px)

    # ── 9. Expression neutrality ───────────────────────────────────────────
    result.expression = _compute_expression_info(pts_px)
    if not result.expression.is_neutral:
        for f in result.expression.flags:
            result.quality.issues.append(f"non_neutral_expression: {f}")

    # ── 10. Glasses / occlusion ────────────────────────────────────────────
    result.occlusion = _compute_occlusion_info(img_rgb, pts_px)
    if result.occlusion.glasses_likely:
        result.quality.issues.append(
            f"glasses_or_occlusion_detected (score={result.occlusion.glasses_score:.2f})"
        )

    # ── 11. Skin pixel sampling (front only, optional) ─────────────────────
    if enable_skin and angle == "front":
        try:
            result.skin = _skin.sample_skin(img_rgb, pts_px)
        except Exception as e:
            result.skin = {"ok": False, "error": f"skin_sampling_failed: {e}"}

    # ── 12. Hairline (trichion) estimation (front only, optional) ──────────
    if enable_hairline and angle == "front" and len(pts_px) > 168:
        try:
            iod_px = math.hypot(pts_px[133][0] - pts_px[362][0],
                                pts_px[133][1] - pts_px[362][1])
            result.hairline = _hairline.estimate_hairline(img_rgb, pts_px, iod_px)
        except Exception as e:
            result.hairline = {"ok": False, "error": f"hairline_estimation_failed: {e}"}

    # ── 13. Final quality score ────────────────────────────────────────────
    score = 100
    if "blurry" in result.quality.issues: score -= 30
    if "too_dark" in result.quality.issues or "too_bright" in result.quality.issues: score -= 20
    if "face_too_small" in result.quality.issues: score -= 25
    if any(i.startswith("not_frontal") or i.startswith("left_profile_too_shallow")
           or i.startswith("right_profile_too_shallow") for i in result.quality.issues): score -= 25
    if any(i.startswith("head_tilted") for i in result.quality.issues): score -= 10
    if any(i.startswith("multiple_faces_detected") for i in result.quality.issues): score -= 40
    if any(i.startswith("non_neutral_expression") for i in result.quality.issues): score -= 8
    if any(i.startswith("glasses_or_occlusion_detected") for i in result.quality.issues): score -= 10
    result.quality.score = max(0, score)

    return result


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════
def _estimate_pose(pts_px, img_w: int, img_h: int) -> tuple[float, float, float]:
    image_pts = np.array([
        pts_px[1], pts_px[152], pts_px[33], pts_px[263], pts_px[61], pts_px[291],
    ], dtype=np.float64)
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
    cam_matrix = np.array([[focal, 0, center[0]], [0, focal, center[1]], [0, 0, 1]],
                          dtype=np.float64)
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


def _compute_iris_info(pts_px) -> IrisInfo:
    """Iris landmarks (refined model):
      Right iris: 468 (center), 469-472 (perimeter)
      Left  iris: 473 (center), 474-477 (perimeter)
    """
    info = IrisInfo()
    info.right_center_px = pts_px[468]
    info.left_center_px  = pts_px[473]

    # Radius = mean distance from center to perimeter points
    def _radius(center, perim_pts):
        dists = [math.hypot(p[0] - center[0], p[1] - center[1]) for p in perim_pts]
        return sum(dists) / len(dists) if dists else 0.0

    info.right_radius_px = round(_radius(pts_px[468], [pts_px[i] for i in (469, 470, 471, 472)]), 2)
    info.left_radius_px  = round(_radius(pts_px[473], [pts_px[i] for i in (474, 475, 476, 477)]), 2)
    info.inter_pupillary_distance_px = round(
        math.hypot(pts_px[468][0] - pts_px[473][0],
                   pts_px[468][1] - pts_px[473][1]), 2)

    # Gaze: pupil offset relative to eye corner span, averaged across both eyes.
    def _eye_center(outer, inner, top, bottom):
        return ((pts_px[outer][0] + pts_px[inner][0] + pts_px[top][0] + pts_px[bottom][0]) / 4.0,
                (pts_px[outer][1] + pts_px[inner][1] + pts_px[top][1] + pts_px[bottom][1]) / 4.0)

    r_eye_c = _eye_center(33, 133, 159, 145)
    l_eye_c = _eye_center(263, 362, 386, 374)
    r_eye_w = math.hypot(pts_px[33][0] - pts_px[133][0], pts_px[33][1] - pts_px[133][1]) or 1.0
    l_eye_w = math.hypot(pts_px[263][0] - pts_px[362][0], pts_px[263][1] - pts_px[362][1]) or 1.0
    r_eye_h = math.hypot(pts_px[159][0] - pts_px[145][0], pts_px[159][1] - pts_px[145][1]) or 1.0
    l_eye_h = math.hypot(pts_px[386][0] - pts_px[374][0], pts_px[386][1] - pts_px[374][1]) or 1.0

    r_off_x = (pts_px[468][0] - r_eye_c[0]) / r_eye_w
    l_off_x = (pts_px[473][0] - l_eye_c[0]) / l_eye_w
    r_off_y = (pts_px[468][1] - r_eye_c[1]) / r_eye_h
    l_off_y = (pts_px[473][1] - l_eye_c[1]) / l_eye_h
    info.gaze_offset_norm_x = round((r_off_x + l_off_x) / 2.0, 3)
    info.gaze_offset_norm_y = round((r_off_y + l_off_y) / 2.0, 3)

    if abs(info.gaze_offset_norm_x) < 0.10 and abs(info.gaze_offset_norm_y) < 0.10:
        info.gaze_direction = "straight"
    elif abs(info.gaze_offset_norm_x) > abs(info.gaze_offset_norm_y):
        info.gaze_direction = "right" if info.gaze_offset_norm_x > 0 else "left"
    else:
        info.gaze_direction = "down" if info.gaze_offset_norm_y > 0 else "up"
    return info


def _compute_expression_info(pts_px) -> ExpressionInfo:
    """Detect smile / closed eyes / open mouth so user can be asked for retake."""
    info = ExpressionInfo()

    # Eye-aspect ratio (open/closed)
    def _ear(top_idx, bottom_idx, outer_idx, inner_idx):
        v = math.hypot(pts_px[top_idx][0] - pts_px[bottom_idx][0],
                       pts_px[top_idx][1] - pts_px[bottom_idx][1])
        h = math.hypot(pts_px[outer_idx][0] - pts_px[inner_idx][0],
                       pts_px[outer_idx][1] - pts_px[inner_idx][1]) or 1.0
        return v / h

    ear_r = _ear(159, 145, 33,  133)
    ear_l = _ear(386, 374, 263, 362)
    info.eyes_open_score = round((ear_r + ear_l) / 2.0, 3)

    # Mouth open ratio (vertical lip gap / mouth width)
    mouth_open = math.hypot(pts_px[13][0] - pts_px[14][0],
                            pts_px[13][1] - pts_px[14][1])
    mouth_w = math.hypot(pts_px[61][0] - pts_px[291][0],
                         pts_px[61][1] - pts_px[291][1]) or 1.0
    info.mouth_open_score = round(mouth_open / mouth_w, 3)

    # Smile: corners higher than upper-lip top + corners far apart
    upper_lip_y = pts_px[0][1]
    r_corner_y, l_corner_y = pts_px[61][1], pts_px[291][1]
    avg_corner_y = (r_corner_y + l_corner_y) / 2.0
    # Image y grows downward; smiling = corners ABOVE upper lip → smaller y
    rise = (upper_lip_y - avg_corner_y) / mouth_w
    info.smile_score = round(rise, 3)

    if info.eyes_open_score < 0.18:
        info.flags.append("eyes_closed_or_squinting")
    if info.mouth_open_score > 0.15:
        info.flags.append("mouth_open")
    if info.smile_score > 0.06:
        info.flags.append("smiling")

    info.is_neutral = len(info.flags) == 0
    return info


def _compute_occlusion_info(rgb_img: np.ndarray, pts_px) -> OcclusionInfo:
    """Heuristic glasses detection: glasses introduce a darker horizontal band
    across the bridge of the nose (frame top) and bright reflections on lenses.

    We compare the brightness of a strip across the upper eye region to the
    brightness of the cheek region just below.
    """
    info = OcclusionInfo()
    h, w = rgb_img.shape[:2]
    gray = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2GRAY)

    # Eye strip: from forehead-bottom to upper eye lid
    eye_top_y = min(pts_px[107][1], pts_px[336][1])    # brow inner
    eye_bot_y = max(pts_px[145][1], pts_px[374][1])    # lower lid
    eye_left_x = min(pts_px[127][0], pts_px[33][0])
    eye_right_x = max(pts_px[356][0], pts_px[263][0])

    # Cheek strip: just below lower lid, same width
    cheek_top_y = eye_bot_y + max(5, int((eye_bot_y - eye_top_y) * 0.3))
    cheek_bot_y = cheek_top_y + max(8, int((eye_bot_y - eye_top_y) * 0.6))

    if (eye_bot_y - eye_top_y < 5 or eye_right_x - eye_left_x < 10 or
        cheek_bot_y >= h):
        info.notes.append("region_out_of_bounds")
        return info

    eye_strip = gray[eye_top_y:eye_bot_y, eye_left_x:eye_right_x]
    cheek_strip = gray[cheek_top_y:cheek_bot_y, eye_left_x:eye_right_x]

    eye_brightness = float(eye_strip.mean()) if eye_strip.size else 0.0
    cheek_brightness = float(cheek_strip.mean()) if cheek_strip.size else 0.0
    diff = cheek_brightness - eye_brightness    # positive = eyes darker (frames likely)

    info.eye_region_brightness_diff = round(diff, 2)

    # Also count bright spots (specular highlights typical of glasses)
    bright_pixel_ratio = float((eye_strip > 220).mean()) if eye_strip.size else 0.0
    edge_strength = float(cv2.Laplacian(eye_strip, cv2.CV_64F).var()) if eye_strip.size else 0.0

    # Heuristic score 0..1
    score = 0.0
    if diff > 18:                     score += 0.35
    if diff > 30:                     score += 0.20
    if bright_pixel_ratio > 0.02:     score += 0.20
    if edge_strength > 1500:          score += 0.15
    if edge_strength > 3000:          score += 0.15
    info.glasses_score = round(min(score, 1.0), 2)
    info.glasses_likely = info.glasses_score >= 0.5
    if info.glasses_likely:
        info.notes.append("brightness_drop_and_high_edges_in_eye_region")
    return info


# ═══════════════════════════════════════════════════════════════════════════
# Serialization
# ═══════════════════════════════════════════════════════════════════════════
def landmark_set_to_dict(ls: LandmarkSet, include_points: bool = False) -> dict:
    d = {
        "angle": ls.angle,
        "quality": asdict(ls.quality),
    }
    if ls.iris is not None:
        d["iris"] = asdict(ls.iris)
    if ls.expression is not None:
        d["expression"] = asdict(ls.expression)
    if ls.occlusion is not None:
        d["occlusion"] = asdict(ls.occlusion)
    if ls.skin is not None:
        d["skin"] = ls.skin
    if ls.hairline is not None:
        d["hairline"] = ls.hairline
    if include_points:
        d["points_norm"] = ls.points_norm
        d["points_px"] = ls.points_px
    else:
        d["landmark_count"] = len(ls.points_norm)
    return d

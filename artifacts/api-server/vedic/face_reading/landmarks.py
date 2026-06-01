"""
Mediapipe Face Mesh wrapper  (v3 — fully hardened foundation).

Pipeline:
  1. image_io.decode_image  → validate + EXIF + HEIC + downscale + un-mirror
  2. white_balance          → gray-world WB (skin reproducibility)
  3. mediapipe FaceDetection → multi-face count
  4. mediapipe FaceMesh     → 478 landmarks
  5. solvePnP head pose     → yaw/pitch/roll (pitch wrap-corrected)
  6. iris/pupil details      → IPD, gaze, mm scale, pupil dilation
  7. expression checks       → smile/EAR/mouth_open
  8. occlusion/glasses       → brightness + edge heuristic
  9. skin sampling           → 5 regions, ITA, undertone
 10. hairline (trichion)
 11. moles, oiliness, wrinkles, dark circles, beard, brow density, hair color
 12. edge-of-frame, distance, portrait-blur warnings
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Optional

import cv2
import numpy as np

import mediapipe as mp

from . import image_io as _img
from . import white_balance as _wb
from . import skin as _skin
from . import skin_features as _sfx
from . import iris_extras as _iris_extras
from . import hairline as _hairline


# ── Singletons ──────────────────────────────────────────────────────────────
_FACE_MESH = None
_FACE_DETECTOR = None


def _get_face_mesh():
    global _FACE_MESH
    if _FACE_MESH is None:
        _FACE_MESH = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=4,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    return _FACE_MESH


def _get_face_detector():
    global _FACE_DETECTOR
    if _FACE_DETECTOR is None:
        _FACE_DETECTOR = mp.solutions.face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )
    return _FACE_DETECTOR


# IOD reference (mm) — Farkas adult means
IOD_BASELINE_MM = {"M": 32.7, "F": 31.3, "U": 32.0}


# ── Result containers ───────────────────────────────────────────────────────
@dataclass
class Quality:
    face_detected: bool = False
    landmark_count: int = 0
    face_count: int = 0
    image_width: int = 0
    image_height: int = 0
    original_width: int = 0
    original_height: int = 0
    image_format: str = ""
    bytes_in: int = 0
    downscaled: bool = False
    mirror_applied: bool = False
    white_balanced: bool = False
    face_bbox: dict = field(default_factory=dict)
    yaw_deg: float = 0.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    brightness: float = 0.0
    sharpness: float = 0.0          # Laplacian variance on face crop (primary)
    sharpness_global: float = 0.0   # full-frame (debug / portrait-mode check)
    portrait_blur_warning: bool = False
    edge_clipping: list = field(default_factory=list)   # which edges face touches
    distance_estimate: str = "unknown"
    issues: list = field(default_factory=list)
    score: int = 0


@dataclass
class IrisInfo:
    right_center_px: tuple = (0, 0)
    left_center_px:  tuple = (0, 0)
    right_radius_px: float = 0.0
    left_radius_px:  float = 0.0
    inter_pupillary_distance_px: float = 0.0
    gaze_direction:  str = "unknown"
    gaze_offset_norm_x: float = 0.0
    gaze_offset_norm_y: float = 0.0
    mm_scale: dict = field(default_factory=dict)
    pupil_right: dict = field(default_factory=dict)
    pupil_left:  dict = field(default_factory=dict)


@dataclass
class ExpressionInfo:
    smile_score: float = 0.0
    eyes_open_score: float = 0.0
    mouth_open_score: float = 0.0
    is_neutral: bool = True
    flags: list = field(default_factory=list)


@dataclass
class OcclusionInfo:
    glasses_likely: bool = False
    glasses_score: float = 0.0
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
    moles: Optional[dict] = None
    oiliness: Optional[dict] = None
    wrinkles: Optional[dict] = None
    dark_circles: Optional[dict] = None
    beard: Optional[dict] = None
    eyebrow_density: Optional[dict] = None
    hair_color: Optional[dict] = None
    rgb_image: Optional[np.ndarray] = None       # cached for engines (excluded from JSON)


# ── Public API ──────────────────────────────────────────────────────────────
def extract_landmarks(image_bytes: bytes,
                      angle: str = "front",
                      mirror: bool = False,
                      gender: str = "U",
                      enable_skin: bool = True,
                      enable_hairline: bool = True,
                      enable_features: bool = True,
                      apply_white_balance: bool = True) -> LandmarkSet:
    """Full v3 foundation extraction.

    Args:
      image_bytes: raw image payload
      angle:       'front' | 'left' | 'right'
      mirror:      True if input is a mirrored selfie (will be un-flipped)
      gender:      'M' | 'F' | 'U' — adjusts IOD-mm scale baseline
      enable_*:    toggle expensive sub-analyses
    """
    result = LandmarkSet(angle=angle)

    # ── 1. Decode + EXIF + HEIC + downscale + un-mirror ────────────────────
    decoded, err = _img.decode_image(image_bytes, mirror=mirror)
    if decoded is None:
        result.quality.issues.append(err or "decode_failed")
        return result

    rgb = decoded.rgb
    h, w = rgb.shape[:2]
    q = result.quality
    q.image_width = w
    q.image_height = h
    q.original_width = decoded.original_width
    q.original_height = decoded.original_height
    q.image_format = decoded.format
    q.bytes_in = decoded.bytes_in
    q.downscaled = decoded.downscaled
    q.mirror_applied = decoded.mirror_applied
    for n in decoded.notes:
        q.issues.append(f"info:{n}")

    # ── 2. Brightness pre-check (sharpness measured on face crop later) ─────
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    q.brightness = float(round(gray.mean(), 2))
    q.sharpness_global = float(round(cv2.Laplacian(gray, cv2.CV_64F).var(), 2))
    if q.brightness < 45:    q.issues.append("too_dark")
    elif q.brightness > 238: q.issues.append("too_bright")

    # ── 3. Multi-face count (run before mesh) ──────────────────────────────
    try:
        det = _get_face_detector().process(rgb)
        q.face_count = len(det.detections) if det.detections else 0
        if q.face_count > 1:
            q.issues.append(f"multiple_faces_detected (count={q.face_count})")
    except Exception as e:
        q.issues.append(f"face_detector_failed: {e}")

    if q.face_count == 0:
        q.issues.append("no_face_in_image")

    # ── 4. FaceMesh (do this before WB so detection isn't affected) ────────
    fm = _get_face_mesh()
    mp_result = fm.process(rgb)
    if not mp_result.multi_face_landmarks:
        q.issues.append("no_face_detected")
        q.score = 0
        return result

    landmarks = mp_result.multi_face_landmarks[0].landmark
    q.face_detected = True
    q.landmark_count = len(landmarks)
    pts_norm = [(round(lm.x, 6), round(lm.y, 6), round(lm.z, 6)) for lm in landmarks]
    pts_px = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
    result.points_norm = pts_norm
    result.points_px = pts_px

    # ── 5. Bounding box + edge-clipping ────────────────────────────────────
    xs = [p[0] for p in pts_px]; ys = [p[1] for p in pts_px]
    bx, by = min(xs), min(ys)
    bw, bh = max(xs) - bx, max(ys) - by
    q.face_bbox = {
        "x": bx, "y": by, "w": bw, "h": bh,
        "area_ratio": round((bw * bh) / float(w * h), 4),
    }
    if q.face_bbox["area_ratio"] < 0.05:
        q.issues.append("face_too_small")

    # Face-region sharpness (phones often blur background; full-frame Laplacian is misleading)
    try:
        pad = max(2, int(min(bw, bh) * 0.04))
        fy0 = max(0, by - pad)
        fy1 = min(h, by + bh + pad)
        fx0 = max(0, bx - pad)
        fx1 = min(w, bx + bw + pad)
        face_patch = gray[fy0:fy1, fx0:fx1]
        face_var = float(cv2.Laplacian(face_patch, cv2.CV_64F).var()) if face_patch.size else 0.0
        # Scale-normalize so distant-but-sharp faces are not penalized
        norm = face_var * (max(bh, 80) / 200.0)
        q.sharpness = float(round(norm, 2))
        if norm < 28:
            q.issues.append("blurry")
    except Exception:
        q.sharpness = q.sharpness_global
        if q.sharpness_global < 22:
            q.issues.append("blurry")

    edge_thresh = max(2, int(min(w, h) * 0.008))
    if bx <= edge_thresh:           q.edge_clipping.append("left")
    if by <= edge_thresh:           q.edge_clipping.append("top")
    if (w - (bx + bw)) <= edge_thresh: q.edge_clipping.append("right")
    if (h - (by + bh)) <= edge_thresh: q.edge_clipping.append("bottom")
    if q.edge_clipping:
        q.issues.append(f"face_clipped_at: {','.join(q.edge_clipping)}")

    # ── 6. White balance (after detection so geometry untouched) ───────────
    if apply_white_balance:
        balanced, wb_info = _wb.gray_world_balance(rgb, q.face_bbox)
        if wb_info.get("applied"):
            rgb = balanced
            q.white_balanced = True

    # ── 7. Head pose (with pitch wrap fix) ─────────────────────────────────
    try:
        yaw, pitch, roll = _estimate_pose(pts_px, w, h)
        # Wrap pitch into (-90, 90] — solvePnP can flip 180° on upright faces.
        if pitch > 90:    pitch -= 180
        elif pitch < -90: pitch += 180
        q.yaw_deg = round(yaw, 1)
        q.pitch_deg = round(pitch, 1)
        q.roll_deg = round(roll, 1)
        if angle == "front" and abs(yaw) > 28:
            q.issues.append(f"not_frontal (yaw={yaw:.0f}°)")
        elif angle == "left" and yaw > -18:
            q.issues.append(f"left_profile_too_shallow (yaw={yaw:.0f}°)")
        elif angle == "right" and yaw < 18:
            q.issues.append(f"right_profile_too_shallow (yaw={yaw:.0f}°)")
        if abs(roll) > 28:
            q.issues.append(f"head_tilted (roll={roll:.0f}°)")
        if abs(pitch) > 32:
            q.issues.append(f"head_pitched (pitch={pitch:.0f}°)")
    except Exception as e:
        q.issues.append(f"pose_estimation_failed: {e}")

    # ── 8. Distance estimate (IPD vs image width) ──────────────────────────
    if len(pts_px) >= 478:
        ipd_px = math.hypot(pts_px[468][0] - pts_px[473][0],
                            pts_px[468][1] - pts_px[473][1])
        ipd_ratio = ipd_px / float(w)
        if ipd_ratio < 0.05:
            q.distance_estimate = "too_far"
            q.issues.append(f"camera_too_far (ipd_ratio={ipd_ratio:.3f})")
        elif ipd_ratio < 0.10:
            q.distance_estimate = "far"
        elif ipd_ratio < 0.30:
            q.distance_estimate = "arms_length"
        elif ipd_ratio < 0.45:
            q.distance_estimate = "close"
        else:
            q.distance_estimate = "very_close"
            q.issues.append(f"camera_too_close (ipd_ratio={ipd_ratio:.3f}); perspective distortion likely")

    # ── 9. Portrait-mode bokeh check (face sharp, edges blurred) ───────────
    try:
        face_patch = gray[by:by + bh, bx:bx + bw]
        # Outer 12% strip on each side
        strip_w = max(8, int(w * 0.06))
        edge_strip = np.concatenate([gray[:, :strip_w].ravel(),
                                     gray[:, -strip_w:].ravel()])
        face_sharp = float(cv2.Laplacian(face_patch, cv2.CV_64F).var()) if face_patch.size else 0
        edge_sharp = float(cv2.Laplacian(edge_strip.reshape(-1, strip_w), cv2.CV_64F).var()) \
                     if edge_strip.size else 0
        if face_sharp > 80 and edge_sharp < 12:
            q.portrait_blur_warning = True
            q.issues.append("portrait_mode_bokeh_detected")
    except Exception:
        pass

    # ── 10. Iris / pupil ───────────────────────────────────────────────────
    if len(pts_px) >= 478:
        result.iris = _compute_iris_info(pts_px, rgb)

    # ── 11. Expression neutrality ──────────────────────────────────────────
    result.expression = _compute_expression_info(pts_px)
    if not result.expression.is_neutral:
        for f in result.expression.flags:
            q.issues.append(f"non_neutral_expression: {f}")

    # ── 12. Glasses / occlusion ────────────────────────────────────────────
    result.occlusion = _compute_occlusion_info(rgb, pts_px)
    if result.occlusion.glasses_likely:
        q.issues.append(
            f"glasses_or_occlusion_detected (score={result.occlusion.glasses_score:.2f})"
        )

    # IOD scale (gender-aware)
    iod_baseline = IOD_BASELINE_MM.get(gender.upper(), IOD_BASELINE_MM["U"])
    iod_px = math.hypot(pts_px[133][0] - pts_px[362][0],
                        pts_px[133][1] - pts_px[362][1])

    # ── 13. Skin sampling (front only) ─────────────────────────────────────
    if enable_skin and angle == "front":
        try:
            result.skin = _skin.sample_skin(rgb, pts_px)
        except Exception as e:
            result.skin = {"ok": False, "error": f"skin_sampling_failed: {e}"}

    # ── 14. Hairline (front only) ──────────────────────────────────────────
    if enable_hairline and angle == "front" and len(pts_px) > 168 and iod_px > 0:
        try:
            result.hairline = _hairline.estimate_hairline(rgb, pts_px, iod_px,
                                                         iod_baseline_mm=iod_baseline)
        except Exception as e:
            result.hairline = {"ok": False, "error": f"hairline_estimation_failed: {e}"}

    # ── 15. Advanced features (front only) ─────────────────────────────────
    if enable_features and angle == "front":
        try:    result.moles = _sfx.detect_moles(rgb, pts_px, q.face_bbox)
        except Exception as e: result.moles = {"ok": False, "error": str(e)}
        try:    result.oiliness = _sfx.estimate_oiliness(rgb, pts_px)
        except Exception as e: result.oiliness = {"ok": False, "error": str(e)}
        try:    result.wrinkles = _sfx.detect_wrinkles(rgb, pts_px)
        except Exception as e: result.wrinkles = {"ok": False, "error": str(e)}
        try:    result.dark_circles = _sfx.detect_dark_circles(rgb, pts_px)
        except Exception as e: result.dark_circles = {"ok": False, "error": str(e)}
        try:    result.beard = _sfx.detect_beard(rgb, pts_px)
        except Exception as e: result.beard = {"ok": False, "error": str(e)}
        try:    result.eyebrow_density = _sfx.estimate_eyebrow_density(rgb, pts_px)
        except Exception as e: result.eyebrow_density = {"ok": False, "error": str(e)}
        try:
            hl_y = result.hairline.get("hairline_y_px") if result.hairline and result.hairline.get("ok") else None
            result.hair_color = _sfx.sample_hair_color(rgb, pts_px, hl_y)
        except Exception as e: result.hair_color = {"ok": False, "error": str(e)}

        # Beard warning into issues (chin landmarks affected)
        if result.beard and result.beard.get("warns_landmark_accuracy"):
            q.issues.append(f"beard_detected:{result.beard['facial_hair']} (chin landmarks reduced confidence)")

    # ── 16. Cache RGB for downstream engines (in-memory only) ──────────────
    result.rgb_image = rgb

    # ── 16b. Plausibility — reject obvious non-face uploads ───────────────
    _apply_face_plausibility_checks(result)

    # ── 17. Final score ────────────────────────────────────────────────────
    score = 100
    if any(str(i).startswith("not_a_face") for i in q.issues):
        score = 0
    if "no_face_detected" in q.issues or "no_face_in_image" in q.issues:
        score = 0
    if "blurry" in q.issues:
        score -= 18 if angle == "front" else 10
    if "too_dark" in q.issues or "too_bright" in q.issues:
        score -= 15
    if "face_too_small" in q.issues:
        score -= 20
    if any(i.startswith("not_frontal") for i in q.issues):
        score -= 12
    if any(i.startswith("left_profile_too_shallow") or i.startswith("right_profile_too_shallow")
           for i in q.issues):
        score -= 10 if angle in ("left", "right") else 0
    if any(i.startswith("head_tilted") for i in q.issues):
        score -= 6
    if any(i.startswith("head_pitched") for i in q.issues):
        score -= 5
    if any(i.startswith("multiple_faces_detected") for i in q.issues):
        score -= 40
    if any(i.startswith("non_neutral_expression") for i in q.issues):
        score -= 4
    if any(i.startswith("glasses_or_occlusion_detected") for i in q.issues):
        score -= 5
    if any(i.startswith("face_clipped_at") for i in q.issues):
        score -= 8
    if any(i.startswith("camera_too_far") or i.startswith("camera_too_close") for i in q.issues):
        score -= 8
    if any(i.startswith("portrait_mode_bokeh_detected") for i in q.issues):
        score -= 3
    if any(i.startswith("beard_detected") for i in q.issues):
        score -= 3
    q.score = max(0, score)
    # Good landmark lock → floor so accurate selfies are not rejected by stacked soft warnings
    if q.face_detected and q.landmark_count >= 468 and not any(
        str(i).startswith("not_a_face") for i in q.issues
    ):
        floor = 52 if angle == "front" else 42
        q.score = max(q.score, floor)

    return result


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════
def _apply_face_plausibility_checks(result: "LandmarkSet") -> None:
    """Flag uploads that are not a plausible human face (objects, scenery, etc.)."""
    q = result.quality
    if not q.face_detected or not result.points_px:
        return

    bbox = q.face_bbox or {}
    bw = float(bbox.get("w") or 0)
    bh = float(bbox.get("h") or 0)
    area = float(bbox.get("area_ratio") or 0)

    if bw <= 0 or bh <= 0:
        q.issues.append("not_a_face:invalid_geometry")
        return

    aspect = bw / bh
    if aspect < 0.52 or aspect > 1.45:
        q.issues.append("not_a_face:unnatural_face_shape")

    if area < 0.035:
        q.issues.append("not_a_face:subject_too_small")
    elif area > 0.88:
        q.issues.append("not_a_face:invalid_framing")

    if q.face_count == 0:
        q.issues.append("not_a_face:low_detector_confidence")

    try:
        expr = result.expression
        if expr is not None:
            ear = float(getattr(expr, "eyes_open_score", 0) or 0)
            if ear < 0.05:
                q.issues.append("not_a_face:eyes_not_visible")
    except Exception:
        pass

    try:
        iris = result.iris
        if iris is not None:
            ipd = float(getattr(iris, "inter_pupillary_distance_px", 0) or 0)
            if ipd > 0 and bw > 0:
                ipd_ratio = ipd / bw
                if ipd_ratio < 0.12 or ipd_ratio > 0.55:
                    q.issues.append("not_a_face:unnatural_eye_spacing")
    except Exception:
        pass


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


def _compute_iris_info(pts_px, rgb_img: np.ndarray) -> IrisInfo:
    info = IrisInfo()
    info.right_center_px = pts_px[468]
    info.left_center_px  = pts_px[473]

    def _radius(center, perim_pts):
        dists = [math.hypot(p[0] - center[0], p[1] - center[1]) for p in perim_pts]
        return sum(dists) / len(dists) if dists else 0.0

    info.right_radius_px = round(_radius(pts_px[468], [pts_px[i] for i in (469, 470, 471, 472)]), 2)
    info.left_radius_px  = round(_radius(pts_px[473], [pts_px[i] for i in (474, 475, 476, 477)]), 2)
    info.inter_pupillary_distance_px = round(
        math.hypot(pts_px[468][0] - pts_px[473][0],
                   pts_px[468][1] - pts_px[473][1]), 2)

    # Gaze
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

    # mm scale + pupil
    info.mm_scale = _iris_extras.iris_mm_summary(
        info.right_radius_px, info.left_radius_px, info.inter_pupillary_distance_px
    )
    try:
        info.pupil_right = _iris_extras.estimate_pupil(rgb_img, info.right_center_px, info.right_radius_px)
    except Exception as e:
        info.pupil_right = {"ok": False, "error": str(e)}
    try:
        info.pupil_left = _iris_extras.estimate_pupil(rgb_img, info.left_center_px, info.left_radius_px)
    except Exception as e:
        info.pupil_left = {"ok": False, "error": str(e)}
    return info


def _compute_expression_info(pts_px) -> ExpressionInfo:
    info = ExpressionInfo()

    def _ear(top_idx, bottom_idx, outer_idx, inner_idx):
        v = math.hypot(pts_px[top_idx][0] - pts_px[bottom_idx][0],
                       pts_px[top_idx][1] - pts_px[bottom_idx][1])
        h = math.hypot(pts_px[outer_idx][0] - pts_px[inner_idx][0],
                       pts_px[outer_idx][1] - pts_px[inner_idx][1]) or 1.0
        return v / h

    ear_r = _ear(159, 145, 33,  133)
    ear_l = _ear(386, 374, 263, 362)
    info.eyes_open_score = round((ear_r + ear_l) / 2.0, 3)

    mouth_open = math.hypot(pts_px[13][0] - pts_px[14][0],
                            pts_px[13][1] - pts_px[14][1])
    mouth_w = math.hypot(pts_px[61][0] - pts_px[291][0],
                         pts_px[61][1] - pts_px[291][1]) or 1.0
    info.mouth_open_score = round(mouth_open / mouth_w, 3)

    upper_lip_y = pts_px[0][1]
    avg_corner_y = (pts_px[61][1] + pts_px[291][1]) / 2.0
    info.smile_score = round((upper_lip_y - avg_corner_y) / mouth_w, 3)

    if info.eyes_open_score < 0.18:  info.flags.append("eyes_closed_or_squinting")
    if info.mouth_open_score > 0.15: info.flags.append("mouth_open")
    if info.smile_score > 0.10:      info.flags.append("smiling")
    info.is_neutral = len(info.flags) == 0
    return info


def _compute_occlusion_info(rgb_img: np.ndarray, pts_px) -> OcclusionInfo:
    info = OcclusionInfo()
    h, w = rgb_img.shape[:2]
    gray = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2GRAY)

    eye_top_y = min(pts_px[107][1], pts_px[336][1])
    eye_bot_y = max(pts_px[145][1], pts_px[374][1])
    eye_left_x = min(pts_px[127][0], pts_px[33][0])
    eye_right_x = max(pts_px[356][0], pts_px[263][0])
    cheek_top_y = eye_bot_y + max(5, int((eye_bot_y - eye_top_y) * 0.3))
    cheek_bot_y = cheek_top_y + max(8, int((eye_bot_y - eye_top_y) * 0.6))

    if (eye_bot_y - eye_top_y < 5 or eye_right_x - eye_left_x < 10 or cheek_bot_y >= h):
        info.notes.append("region_out_of_bounds")
        return info

    eye_strip = gray[eye_top_y:eye_bot_y, eye_left_x:eye_right_x]
    cheek_strip = gray[cheek_top_y:cheek_bot_y, eye_left_x:eye_right_x]
    eye_brightness = float(eye_strip.mean()) if eye_strip.size else 0.0
    cheek_brightness = float(cheek_strip.mean()) if cheek_strip.size else 0.0
    diff = cheek_brightness - eye_brightness
    info.eye_region_brightness_diff = round(diff, 2)

    bright_pixel_ratio = float((eye_strip > 220).mean()) if eye_strip.size else 0.0
    edge_strength = float(cv2.Laplacian(eye_strip, cv2.CV_64F).var()) if eye_strip.size else 0.0

    score = 0.0
    if diff > 18:                 score += 0.35
    if diff > 30:                 score += 0.20
    if bright_pixel_ratio > 0.02: score += 0.20
    if edge_strength > 1500:      score += 0.15
    if edge_strength > 3000:      score += 0.15
    info.glasses_score = round(min(score, 1.0), 2)
    info.glasses_likely = info.glasses_score >= 0.62
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
    if ls.iris is not None:        d["iris"] = asdict(ls.iris)
    if ls.expression is not None:  d["expression"] = asdict(ls.expression)
    if ls.occlusion is not None:   d["occlusion"] = asdict(ls.occlusion)
    if ls.skin is not None:        d["skin"] = ls.skin
    if ls.hairline is not None:    d["hairline"] = ls.hairline
    if ls.moles is not None:       d["moles"] = ls.moles
    if ls.oiliness is not None:    d["oiliness"] = ls.oiliness
    if ls.wrinkles is not None:    d["wrinkles"] = ls.wrinkles
    if ls.dark_circles is not None: d["dark_circles"] = ls.dark_circles
    if ls.beard is not None:       d["beard"] = ls.beard
    if ls.eyebrow_density is not None: d["eyebrow_density"] = ls.eyebrow_density
    if ls.hair_color is not None:  d["hair_color"] = ls.hair_color
    if include_points:
        d["points_norm"] = ls.points_norm
        d["points_px"] = ls.points_px
    else:
        d["landmark_count"] = len(ls.points_norm)
    return d


def landmark_set_from_dict(d: dict) -> LandmarkSet:
    """Rebuild LandmarkSet from Redis/session JSON (no rgb_image)."""
    ls = LandmarkSet(angle=d.get("angle") or "front")
    ls.points_norm = list(d.get("points_norm") or [])
    ls.points_px = [tuple(p) if isinstance(p, (list, tuple)) else p for p in (d.get("points_px") or [])]

    qd = d.get("quality") or {}
    if isinstance(qd, dict):
        ls.quality = Quality(**{k: v for k, v in qd.items() if k in Quality.__dataclass_fields__})

    if d.get("iris"):
        ls.iris = IrisInfo(**{k: v for k, v in d["iris"].items() if k in IrisInfo.__dataclass_fields__})
    if d.get("expression"):
        ls.expression = ExpressionInfo(
            **{k: v for k, v in d["expression"].items() if k in ExpressionInfo.__dataclass_fields__}
        )
    if d.get("occlusion"):
        ls.occlusion = OcclusionInfo(
            **{k: v for k, v in d["occlusion"].items() if k in OcclusionInfo.__dataclass_fields__}
        )
    for attr in (
        "skin", "hairline", "moles", "oiliness", "wrinkles",
        "dark_circles", "beard", "eyebrow_density", "hair_color",
    ):
        if d.get(attr) is not None:
            setattr(ls, attr, d[attr])
    return ls

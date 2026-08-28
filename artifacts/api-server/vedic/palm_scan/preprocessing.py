"""Deterministic, non-destructive palm image preprocessing."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

import cv2
import numpy as np


@dataclass
class PreprocessArtifacts:
    original_rgb: np.ndarray
    processed_rgb: np.ndarray
    crease_enhanced: np.ndarray
    foreground_mask: np.ndarray
    metadata: dict


def _digest(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def preprocess(
    decoded_rgb: np.ndarray,
    landmarks: list[dict] | None,
    *,
    target_long_edge: int = 1200,
    allow_perspective: bool = True,
) -> PreprocessArtifacts:
    """Return new arrays; ``decoded_rgb`` is never mutated."""
    original = np.ascontiguousarray(decoded_rgb).copy()
    before_hash = _digest(original)
    height, width = original.shape[:2]
    scale = min(1.0, target_long_edge / float(max(height, width)))
    if scale < 1.0:
        normalized = cv2.resize(
            original, (round(width * scale), round(height * scale)),
            interpolation=cv2.INTER_AREA,
        )
        resize_status = "applied"
    else:
        normalized = original.copy()
        resize_status = "not_needed"

    # A monocular landmark quadrilateral permits planar normalization, but not
    # true 3-D pose correction. Keep output dimensions stable and record H.
    homography = np.eye(3, dtype=np.float64)
    perspective_status = "skipped"
    perspective_reason = "insufficient_landmark_geometry"
    if not allow_perspective:
        perspective_reason = "quality_gate_not_permitted"
    if allow_perspective and landmarks and len(landmarks) == 21:
        points = np.array([(p["x"], p["y"]) for p in landmarks], np.float32)
        p5, p17, wrist = points[5], points[17], points[0]
        palm_width = float(np.linalg.norm(p5 - p17))
        if palm_width > 0.08 and all(np.isfinite(points.ravel())):
            lower_left = wrist + (p5 - p17) * 0.42
            lower_right = wrist + (p17 - p5) * 0.42
            source = np.float32([p5, p17, lower_right, lower_left])
            xmin, ymin = source.min(axis=0)
            xmax, ymax = source.max(axis=0)
            destination = np.float32([
                [xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax],
            ])
            source_px = source * np.float32([normalized.shape[1], normalized.shape[0]])
            destination_px = destination * np.float32([normalized.shape[1], normalized.shape[0]])
            candidate = cv2.getPerspectiveTransform(source_px, destination_px)
            if np.isfinite(candidate).all() and abs(np.linalg.det(candidate)) > 1e-8:
                homography = candidate
                perspective_status = "applied"
                perspective_reason = "landmark_planar_homography"
    planar = cv2.warpPerspective(
        normalized, homography, (normalized.shape[1], normalized.shape[0]),
        flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101,
    )

    lab = cv2.cvtColor(planar, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    background = cv2.GaussianBlur(l_channel, (0, 0), 31)
    illumination = cv2.addWeighted(l_channel, 1.0, background, -1.0, 128)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(illumination)
    denoised = cv2.bilateralFilter(clahe, 7, 32, 32)
    sharpness_before = float(cv2.Laplacian(denoised, cv2.CV_64F).var())
    sharpen_applied = 45.0 <= sharpness_before < 180.0
    if sharpen_applied:
        soft = cv2.GaussianBlur(denoised, (0, 0), 1.0)
        final_l = cv2.addWeighted(denoised, 1.25, soft, -0.25, 0)
    else:
        final_l = denoised
    processed = cv2.cvtColor(
        cv2.merge((final_l, a_channel, b_channel)), cv2.COLOR_LAB2RGB
    )
    crease = cv2.morphologyEx(
        final_l, cv2.MORPH_BLACKHAT,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
    )

    foreground = np.zeros(final_l.shape, np.uint8)
    separation_method = "landmark_convex_hull_fallback"
    if landmarks and len(landmarks) == 21:
        normalized_points = np.float32([(p["x"], p["y"]) for p in landmarks])
        point_px = normalized_points * np.float32([processed.shape[1], processed.shape[0]])
        transformed = cv2.perspectiveTransform(point_px[None, :, :], homography)[0]
        landmark_seed = np.zeros_like(foreground)
        palm_width = float(np.linalg.norm(transformed[5] - transformed[17]))
        palm_width_px = max(5, round(palm_width * .08))
        palm_polygon = cv2.convexHull(
            np.int32(transformed[[0, 1, 2, 5, 9, 13, 17]])
        )
        cv2.fillConvexPoly(landmark_seed, palm_polygon, 255)
        finger_width = max(5, round(palm_width * .16))
        joint_radius = max(3, round(palm_width * .10))
        for chain in (
            (1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12),
            (13, 14, 15, 16), (17, 18, 19, 20),
        ):
            chain_points = np.int32(transformed[list(chain)])
            cv2.polylines(
                landmark_seed, [chain_points], False, 255, finger_width
            )
            for point in chain_points:
                cv2.circle(
                    landmark_seed, tuple(point), joint_radius, 255, -1
                )
        probable_hand = cv2.dilate(
            landmark_seed,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (palm_width_px * 2 + 1,) * 2),
        )
        # Use landmark geometry only as GrabCut seeds; the final boundary is
        # selected from image pixels. If color separation is unstable, retain
        # the explicit landmark fallback instead of presenting it as CV output.
        try:
            grabcut_mask = np.full(foreground.shape, cv2.GC_BGD, np.uint8)
            grabcut_mask[probable_hand > 0] = cv2.GC_PR_FGD
            sure_hand = cv2.erode(
                landmark_seed,
                cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE, (palm_width_px + 1,) * 2
                ),
            )
            grabcut_mask[sure_hand > 0] = cv2.GC_FGD
            cv2.grabCut(
                planar, grabcut_mask, None,
                np.zeros((1, 65), np.float64),
                np.zeros((1, 65), np.float64),
                3, cv2.GC_INIT_WITH_MASK,
            )
            pixel_foreground = np.uint8(
                (grabcut_mask == cv2.GC_FGD) | (grabcut_mask == cv2.GC_PR_FGD)
            ) * 255
            pixel_foreground = cv2.morphologyEx(
                pixel_foreground, cv2.MORPH_CLOSE,
                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)),
            )
            area_ratio = np.count_nonzero(pixel_foreground) / pixel_foreground.size
            seed_coverage = (
                np.count_nonzero(cv2.bitwise_and(pixel_foreground, landmark_seed))
                / max(np.count_nonzero(landmark_seed), 1)
            )
            if 0.03 <= area_ratio <= 0.85 and seed_coverage >= 0.72:
                foreground = pixel_foreground
                separation_method = "landmark_seeded_grabcut"
            else:
                foreground = probable_hand
        except cv2.error:
            foreground = probable_hand
    else:
        # Conservative central fallback is metadata-explicit and never treated
        # as a detected hand.
        out_height, out_width = foreground.shape
        foreground[
            out_height // 5:out_height * 4 // 5,
            out_width // 5:out_width * 4 // 5,
        ] = 255
        separation_method = "central_region_unreliable_fallback"

    assert _digest(original) == before_hash
    metadata = {
        "coordinate_space": "processed",
        "original_sha256": before_hash,
        "processed_sha256": _digest(processed),
        "original_preserved": True,
        "stages": {
            "decode_exif_orientation": {"status": "applied_by_image_io"},
            "resolution_normalization": {
                "status": resize_status, "target_long_edge_px": target_long_edge,
                "input_size": [width, height],
                "output_size": [processed.shape[1], processed.shape[0]],
                "scale": round(scale, 8),
            },
            "perspective_normalization": {
                "status": perspective_status, "method": perspective_reason,
                "homography": [[round(float(v), 9) for v in row] for row in homography],
                "limitation": "planar_landmark_proxy_not_3d_rectification",
            },
            "illumination_normalization": {"status": "applied", "method": "gaussian_background_division_proxy"},
            "contrast_enhancement": {"status": "applied", "method": "CLAHE", "clip_limit": 2.0},
            "denoise": {"status": "applied", "method": "bilateral_filter"},
            "crease_enhancement": {"status": "applied", "method": "morphological_blackhat"},
            "sharpening": {
                "status": "applied" if sharpen_applied else "skipped",
                "method": "bounded_unsharp_mask" if sharpen_applied else "none",
                "reason": "moderate_input_sharpness" if sharpen_applied else "not_defensible_for_measured_sharpness",
            },
            "palm_background_separation": {"status": "detected" if landmarks else "unknown", "method": separation_method},
        },
        "artifacts": {
            "original": None, "processed": None, "crease_enhanced": None,
            "foreground_mask": None,
        },
    }
    return PreprocessArtifacts(original, processed, crease, foreground, metadata)

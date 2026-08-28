"""Landmark-supported anatomical segmentation with explicit fallback metadata."""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .detectors import confidence_band


@dataclass
class SegmentationResult:
    sections: dict
    masks: dict[str, np.ndarray]
    quality: float


def _largest_polygon(mask: np.ndarray) -> list[dict]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return []
    contour = max(contours, key=cv2.contourArea)
    epsilon = max(1.0, cv2.arcLength(contour, True) * .006)
    points = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2)
    height, width = mask.shape
    return [
        {"x": round(float(x) / width, 6), "y": round(float(y) / height, 6)}
        for x, y in points
    ]


def _section(mask: np.ndarray, confidence: float, method: str, reference: str) -> dict:
    pixels = int(np.count_nonzero(mask))
    return {
        "status": "detected" if pixels else "not_detected",
        "confidence": round(confidence if pixels else 0.0, 4),
        "confidence_band": confidence_band(confidence if pixels else 0.0),
        "method": method,
        "polygon": _largest_polygon(mask),
        "mask_reference": reference if pixels else None,
        "mask_stats": {
            "area_px": pixels,
            "area_normalized": round(pixels / float(mask.size), 6),
            "bounding_box_normalized": _bbox(mask),
        },
    }


def _bbox(mask: np.ndarray) -> dict | None:
    ys, xs = np.where(mask > 0)
    if not len(xs):
        return None
    height, width = mask.shape
    return {
        "x": round(float(xs.min()) / width, 6),
        "y": round(float(ys.min()) / height, 6),
        "width": round(float(xs.max() - xs.min() + 1) / width, 6),
        "height": round(float(ys.max() - ys.min() + 1) / height, 6),
    }


def segment_hand(
    image_shape: tuple[int, int],
    landmarks: list[dict],
    confidence: float,
    foreground_mask: np.ndarray | None = None,
) -> SegmentationResult:
    height, width = image_shape
    points = np.float32([(p["x"] * width, p["y"] * height) for p in landmarks])
    palm_width = max(8.0, float(np.linalg.norm(points[5] - points[17])))
    line_width = max(5, round(palm_width * .18))
    joint_radius = max(4, round(palm_width * .11))
    masks = {name: np.zeros((height, width), np.uint8) for name in (
        "hand_boundary", "palm_region", "fingers", "thumb", "wrist", "visible_palm"
    )}

    finger_chains = ((5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20))
    for chain in finger_chains:
        chain_points = np.int32(points[list(chain)])
        cv2.polylines(masks["fingers"], [chain_points], False, 255, line_width)
        for point in chain_points:
            cv2.circle(masks["fingers"], tuple(point), joint_radius, 255, -1)
    thumb_points = np.int32(points[[1, 2, 3, 4]])
    cv2.polylines(masks["thumb"], [thumb_points], False, 255, line_width)
    for point in thumb_points:
        cv2.circle(masks["thumb"], tuple(point), joint_radius, 255, -1)

    across = (points[17] - points[5]) * .44
    wrist_left, wrist_right = points[0] - across, points[0] + across
    palm_polygon = np.int32([points[5], points[9], points[13], points[17], wrist_right, wrist_left])
    cv2.fillConvexPoly(masks["palm_region"], cv2.convexHull(palm_polygon), 255)
    wrist_polygon = np.int32([
        wrist_left, wrist_right, wrist_right + (points[0] - points[9]) * .22,
        wrist_left + (points[0] - points[9]) * .22,
    ])
    cv2.fillConvexPoly(masks["wrist"], wrist_polygon, 255)

    masks["hand_boundary"] = cv2.bitwise_or(
        cv2.bitwise_or(masks["palm_region"], masks["fingers"]),
        cv2.bitwise_or(masks["thumb"], masks["wrist"]),
    )
    masks["hand_boundary"] = cv2.morphologyEx(
        masks["hand_boundary"], cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (line_width + 1, line_width + 1)),
    )
    geometry_hand = masks["hand_boundary"].copy()
    union = int(np.count_nonzero(geometry_hand))
    overlap = int(np.count_nonzero(cv2.bitwise_and(
        geometry_hand, foreground_mask
    ))) if foreground_mask is not None else union
    if foreground_mask is not None and foreground_mask.shape == masks["palm_region"].shape:
        for key in ("hand_boundary", "palm_region", "fingers", "thumb", "wrist"):
            refined = cv2.bitwise_and(masks[key], foreground_mask)
            # A failed pixel segmentation must not erase a valid anatomical
            # region; retain the geometry fallback and expose lower agreement.
            if np.count_nonzero(refined) >= np.count_nonzero(masks[key]) * .35:
                masks[key] = refined
        masks["visible_palm"] = masks["palm_region"].copy()
        method = "landmark_anatomical_masks_intersected_with_foreground"
    else:
        masks["visible_palm"] = masks["palm_region"].copy()
        method = "landmark_anatomical_polygon_fallback"

    references = {
        key: f"segmentation/{key}" for key in masks
    }
    sections = {
        key: _section(mask, confidence * (.92 if key == "visible_palm" else .88),
                      method, references[key])
        for key, mask in masks.items()
    }
    quality = float(np.clip(overlap / max(union, 1), 0.0, 1.0))
    return SegmentationResult(sections, masks, quality)

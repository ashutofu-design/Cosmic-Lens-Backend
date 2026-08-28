"""Detector interfaces and conservative pixel/MediaPipe implementations."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math
from typing import Protocol

import cv2
import numpy as np


LANDMARK_NAMES = (
    "wrist", "thumb_cmc", "thumb_mcp", "thumb_ip", "thumb_tip",
    "index_mcp", "index_pip", "index_dip", "index_tip",
    "middle_mcp", "middle_pip", "middle_dip", "middle_tip",
    "ring_mcp", "ring_pip", "ring_dip", "ring_tip",
    "little_mcp", "little_pip", "little_dip", "little_tip",
)


@dataclass(frozen=True)
class HandDetection:
    landmarks: list[dict]
    handedness: str
    confidence: float
    source_handedness_label: str


class HandLandmarkBackend(Protocol):
    def detect(self, rgb: np.ndarray, *, pixels_are_mirrored: bool = False) -> HandDetection | None:
        """Return one best hand detected from image pixels."""


class CreaseDetector(Protocol):
    def detect(self, rgb: np.ndarray, palm_mask: np.ndarray) -> dict:
        """Return generic crease paths that are directly supported by pixels."""


class MarkingDetector(Protocol):
    def detect(self, crease_result: dict) -> dict:
        """Return conservative geometry-supported marking candidates."""


class LineIdentityVerifier(Protocol):
    def verify(self, candidates: list[dict], context: dict) -> dict[str, dict]:
        """Assign named lines to candidate IDs; it must never return paths."""


def palmar_view_handedness(points: list[dict]) -> str | None:
    """Hand side from a palm-up gallery photo (thumb vs little finger in image x).

    When fingers point toward the top of the frame, a right palm has the thumb
    on the right of the image. MediaPipe selfie labels must not be swapped.
    """
    by_id = {int(point["id"]): point for point in points if "id" in point}
    thumb = by_id.get(4) or by_id.get(2)
    pinky = by_id.get(20) or by_id.get(17)
    if not thumb or not pinky:
        return None
    dx = float(thumb["x"]) - float(pinky["x"])
    if abs(dx) < 0.02:
        return None
    return "right" if dx > 0 else "left"


class MediaPipeHandsBackend:
    """MediaPipe Hands adapter.

    Gallery palm photos are unmirrored palmar views. MediaPipe's built-in
    left/right label assumes a mirrored selfie, so palmistry uses thumb vs
    little-finger image position instead of that selfie label.
    """

    def __init__(self, min_detection_confidence: float = 0.55):
        self.min_detection_confidence = min_detection_confidence
        self._hands = None

    def _model(self):
        if self._hands is None:
            import mediapipe as mp

            self._hands = mp.solutions.hands.Hands(
                static_image_mode=True,
                max_num_hands=1,
                model_complexity=1,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=0.5,
            )
        return self._hands

    def detect(self, rgb: np.ndarray, *, pixels_are_mirrored: bool = False) -> HandDetection | None:
        result = self._model().process(rgb)
        if not result.multi_hand_landmarks:
            return None
        scores = [
            float(item.classification[0].score)
            for item in (result.multi_handedness or [])
        ]
        best = int(np.argmax(scores)) if scores else 0
        hand = result.multi_hand_landmarks[best]
        classification = (
            result.multi_handedness[best].classification[0]
            if result.multi_handedness and best < len(result.multi_handedness)
            else None
        )
        source = classification.label.lower() if classification else "unknown"
        confidence = float(classification.score) if classification else 0.0
        points = [
            {
                "id": index,
                "name": LANDMARK_NAMES[index],
                "x": float(np.clip(point.x, 0.0, 1.0)),
                "y": float(np.clip(point.y, 0.0, 1.0)),
                "z_relative": float(point.z),
                "confidence": confidence,
                "status": "detected",
            }
            for index, point in enumerate(hand.landmark)
        ]
        geometric = palmar_view_handedness(points)
        if geometric:
            handedness = geometric
        else:
            handedness = source
        return HandDetection(points, handedness, confidence, source)


class ConservativeCreaseDetector:
    """Fuse two deterministic pixel methods; never assigns semantic line names."""

    def __init__(self, minimum_length_ratio: float = 0.08):
        self.minimum_length_ratio = minimum_length_ratio

    @staticmethod
    def _skeleton(binary: np.ndarray) -> np.ndarray:
        image = binary.copy()
        skeleton = np.zeros_like(image)
        element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        while cv2.countNonZero(image):
            opened = cv2.morphologyEx(image, cv2.MORPH_OPEN, element)
            skeleton = cv2.bitwise_or(skeleton, cv2.subtract(image, opened))
            image = cv2.erode(image, element)
        return skeleton

    @staticmethod
    def _longest_skeleton_path(component: np.ndarray) -> np.ndarray:
        """Trace an ordered approximate graph diameter through an 8-neighbor skeleton."""
        pixels = {
            (int(y), int(x)) for y, x in np.argwhere(component > 0)
        }
        if len(pixels) < 2:
            return np.empty((0, 2), np.int32)

        def neighbors(point):
            y, x = point
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if (dx or dy) and (y + dy, x + dx) in pixels:
                        yield y + dy, x + dx

        def farthest(start):
            queue = deque([start])
            distance = {start: 0.0}
            parent = {}
            best = start
            while queue:
                current = queue.popleft()
                for nxt in neighbors(current):
                    if nxt in distance:
                        continue
                    step = math.sqrt(2.0) if (
                        nxt[0] != current[0] and nxt[1] != current[1]
                    ) else 1.0
                    distance[nxt] = distance[current] + step
                    parent[nxt] = current
                    queue.append(nxt)
                    if distance[nxt] > distance[best]:
                        best = nxt
            return best, parent

        endpoints = [
            point for point in pixels if sum(1 for _ in neighbors(point)) == 1
        ]
        first = endpoints[0] if endpoints else next(iter(pixels))
        start, _ = farthest(first)
        end, parent = farthest(start)
        ordered = [end]
        while ordered[-1] != start and ordered[-1] in parent:
            ordered.append(parent[ordered[-1]])
        ordered.reverse()
        return np.array([(x, y) for y, x in ordered], np.int32)

    def _trace(self, binary: np.ndarray, response: np.ndarray, method: str) -> list[dict]:
        skeleton = self._skeleton(binary)
        count, labels, stats, _ = cv2.connectedComponentsWithStats(skeleton, 8)
        height, width = binary.shape
        minimum = self.minimum_length_ratio * min(width, height)
        paths = []
        for label in range(1, count):
            component = np.uint8(labels == label) * 255
            ordered = self._longest_skeleton_path(component)
            if len(ordered) < 2:
                continue
            deltas = np.diff(ordered.astype(float), axis=0)
            length = float(np.sum(np.linalg.norm(deltas, axis=1)))
            if length < minimum:
                continue
            path = ConservativeCreaseDetector._export_skeleton_path(ordered)
            if len(path) < 2:
                continue
            values = response[path[:, 1], path[:, 0]]
            evidence = float(np.mean(values) / 255.0)
            one = np.uint8(component > 0)
            neighbors = cv2.filter2D(one, cv2.CV_16S, np.ones((3, 3), np.int16)) - one
            branch_y, branch_x = np.where((one > 0) & (neighbors >= 4))
            endpoint_y, endpoint_x = np.where((one > 0) & (neighbors <= 1))
            step = max(1, len(branch_x) // 20)
            paths.append({
                "method": method,
                "path_px": path,
                "arc_length_px": length,
                "evidence": evidence,
                "component_area_px": int(stats[label, cv2.CC_STAT_AREA]),
                "skeleton_pixels": int(np.count_nonzero(component)),
                "branch_points": [
                    {"x": round(float(x) / width, 6), "y": round(float(y) / height, 6)}
                    for x, y in zip(branch_x[::step], branch_y[::step])
                ],
                "endpoint_count": int(len(endpoint_x)),
            })
        return sorted(paths, key=lambda item: item["arc_length_px"], reverse=True)[:20]

    @staticmethod
    def _export_skeleton_path(
        ordered: np.ndarray,
        *,
        max_points: int = 64,
        min_points: int = 4,
    ) -> np.ndarray:
        """Preserve ordered skeleton geometry for API paths — do not collapse to endpoints."""
        if len(ordered) < 2:
            return ordered
        step = max(1, len(ordered) // max_points)
        exported = ordered[::step]
        if not np.array_equal(exported[-1], ordered[-1]):
            exported = np.vstack([exported, ordered[-1:]])
        if len(exported) < min_points and len(ordered) >= min_points:
            step = max(1, len(ordered) // min_points)
            exported = ordered[::step]
            if not np.array_equal(exported[-1], ordered[-1]):
                exported = np.vstack([exported, ordered[-1:]])
        return exported

    @staticmethod
    def _measure(path: np.ndarray, length: float, evidence: float, source: dict) -> dict:
        if len(path) < 2:
            return {}
        vector = path[-1].astype(float) - path[0].astype(float)
        chord = max(float(np.linalg.norm(vector)), 1e-6)
        continuity = float(np.clip(source["skeleton_pixels"] / max(length, 1.0), 0, 1))
        curvature = float(np.clip(length / chord - 1.0, 0, 5))
        direction = math.degrees(math.atan2(float(vector[1]), float(vector[0])))
        return {
            "length_px": round(length, 3),
            "strength_proxy": round(evidence, 4),
            "depth_proxy": {"value": round(evidence, 4), "label": "blackhat_or_edge_response_not_physical_depth"},
            "clarity": round(evidence * continuity, 4),
            "continuity": round(continuity, 4),
            "curvature": round(curvature, 4),
            "direction_degrees": round(direction, 3),
            "break_candidates": [],
            "branch_candidates": source["branch_points"],
            "fork_candidates": source["branch_points"],
            "island_candidates": (
                [{"status": "ambiguous_closed_component"}]
                if source["endpoint_count"] == 0 else []
            ),
            "intersection_candidates": source["branch_points"],
            "parallel_candidates": [],
            "relative_position": "unassigned_within_visible_palm",
        }

    def detect(self, rgb: np.ndarray, palm_mask: np.ndarray) -> dict:
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        enhanced = cv2.createCLAHE(2.0, (8, 8)).apply(gray)
        dark_ridges = cv2.morphologyEx(
            enhanced, cv2.MORPH_BLACKHAT,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
        )
        threshold = max(12, int(np.percentile(dark_ridges[palm_mask > 0], 82))) if np.any(palm_mask) else 255
        blackhat_binary = np.uint8((dark_ridges >= threshold) & (palm_mask > 0)) * 255
        blackhat_binary = cv2.morphologyEx(blackhat_binary, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        adaptive = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 21, 5,
        )
        edges = cv2.Canny(enhanced, 35, 100)
        edge_binary = cv2.bitwise_and(cv2.bitwise_or(adaptive, edges), palm_mask)
        edge_binary = cv2.morphologyEx(edge_binary, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        height, width = gray.shape
        method_paths = {
            "blackhat_adaptive": self._trace(blackhat_binary, dark_ridges, "blackhat_adaptive"),
            "canny_ridge": self._trace(edge_binary, edges, "canny_ridge"),
        }
        found, used_second = [], set()
        for first in method_paths["blackhat_adaptive"]:
            first_center = np.mean(first["path_px"], axis=0)
            match_index, match_distance = None, float("inf")
            for index, second in enumerate(method_paths["canny_ridge"]):
                if index in used_second:
                    continue
                distance = float(np.linalg.norm(first_center - np.mean(second["path_px"], axis=0)))
                if distance < match_distance:
                    match_index, match_distance = index, distance
            agreement = match_index is not None and match_distance <= min(width, height) * .06
            evidence = first["evidence"]
            methods = [first["method"]]
            if agreement:
                second = method_paths["canny_ridge"][match_index]
                used_second.add(match_index)
                evidence = (evidence + second["evidence"]) / 2.0
                methods.append(second["method"])
            confidence = float(np.clip(.30 + evidence * .35 + (.20 if agreement else 0), 0, .88))
            path = first["path_px"]
            measurements = self._measure(path, first["arc_length_px"], evidence, first)
            normalized_path = [
                {"x": round(float(x) / width, 6), "y": round(float(y) / height, 6)}
                for x, y in path
            ]
            endpoints = [
                {"x": round(float(path[0][0]) / width, 6), "y": round(float(path[0][1]) / height, 6)},
                {"x": round(float(path[-1][0]) / width, 6), "y": round(float(path[-1][1]) / height, 6)},
            ]
            found.append({
                "id": f"crease_candidate_{len(found) + 1}",
                "status": "detected",
                "detected": True,
                "semantic_identity": "ambiguous",
                "confidence": round(confidence, 4),
                "confidence_band": confidence_band(confidence),
                "detector_agreement": round(1.0 if agreement else .5, 3),
                "methods": methods,
                "method_evidence": {
                    first["method"]: round(first["evidence"], 4),
                    **({second["method"]: round(second["evidence"], 4)} if agreement else {}),
                },
                "path": normalized_path,
                "path_point_count": len(normalized_path),
                "path_source": "skeleton_trace",
                "start_point": endpoints[0],
                "end_point": endpoints[1],
                "endpoints": endpoints,
                "length": round(first["arc_length_px"], 3),
                "normalized_length": round(first["arc_length_px"] / min(width, height), 6),
                "depth": measurements["depth_proxy"],
                "clarity": measurements["clarity"],
                "continuity": measurements["continuity"],
                "curvature": measurements["curvature"],
                "direction": measurements["direction_degrees"],
                "breaks": measurements["break_candidates"],
                "branches": measurements["branch_candidates"],
                "forks": measurements["fork_candidates"],
                "islands": measurements["island_candidates"],
                "crosses_intersections": measurements["intersection_candidates"],
                "parallel_support_lines": measurements["parallel_candidates"],
                "measurements": measurements,
                "source_layer": "visible_palm",
                "image_region": {
                    "x_min": round(float(np.min(path[:, 0])) / width, 6),
                    "y_min": round(float(np.min(path[:, 1])) / height, 6),
                    "x_max": round(float(np.max(path[:, 0])) / width, 6),
                    "y_max": round(float(np.max(path[:, 1])) / height, 6),
                },
                "raw_crease_evidence": {
                    "primary_method": first["method"],
                    "all_methods": methods,
                    "mean_response": round(evidence, 4),
                    "detector_agreement": round(1.0 if agreement else .5, 3),
                },
                "raw": {"arc_length_px": round(first["arc_length_px"], 3),
                        "mean_response": round(evidence, 4)},
            })
            if len(found) >= 12:
                break
        agreement_score = float(np.mean([item["detector_agreement"] for item in found])) if found else 0.0
        return {
            "candidates": found,
            "methods": {
                name: {"candidate_count": len(paths), "method": name}
                for name, paths in method_paths.items()
            },
            "agreement": round(agreement_score, 4),
            "masks": {
                "blackhat_adaptive": blackhat_binary,
                "canny_ridge": edge_binary,
            },
        }


class ConservativeMarkingDetector:
    """Return only ambiguous observable junction/closed-contour candidates."""

    def detect(self, crease_result: dict) -> dict:
        candidates = []
        for line in crease_result.get("candidates", []):
            measurements = line.get("measurements", {})
            for kind in ("fork", "island", "intersection", "parallel"):
                for point in measurements.get(f"{kind}_candidates", []):
                    candidates.append({
                        "type": "ambiguous", "geometry_hint": kind,
                        "location": "visible_palm_unassigned",
                        "coordinates": [point] if "x" in point and "y" in point else [],
                        "confidence": 0.35,
                        "confidence_band": confidence_band(0.35),
                        "methods": line.get("methods", []),
                    })
        return {
            "status": "ambiguous" if candidates else "not_detected",
            "confidence": max((c["confidence"] for c in candidates), default=0.0),
            "confidence_band": confidence_band(max((c["confidence"] for c in candidates), default=0.0)),
            "reason": "typed_marking_requires_multi_method_geometry_support",
            "supported_types": [
                "star", "cross", "triangle", "square", "trident", "grille",
                "island", "fork", "dot", "vertical_line", "horizontal_line",
            ],
            "candidates": candidates,
        }


def confidence_band(value: float) -> str:
    if value >= 0.90:
        return "very_high"
    if value >= 0.75:
        return "high"
    if value >= 0.55:
        return "moderate"
    if value >= 0.35:
        return "ambiguous"
    return "unreliable"

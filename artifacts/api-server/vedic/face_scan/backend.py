"""Injectable, measurement-only face landmark backend contract."""
from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Protocol

import numpy as np

_BACKEND_LOCK = Lock()


@dataclass(frozen=True)
class FaceCandidate:
    """One detector candidate in strict image-normalized coordinates."""

    landmarks: list[tuple[float, float, float]]
    confidence: float
    bbox: tuple[float, float, float, float]
    pose: dict[str, float] = field(default_factory=dict)
    landmark_confidences: list[float] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)


@dataclass(frozen=True)
class DetectionBatch:
    candidates: list[FaceCandidate]
    face_count: int
    backend: str
    notes: list[str] = field(default_factory=list)


class FaceLandmarkBackend(Protocol):
    def detect(self, image_bytes: bytes, rgb: np.ndarray) -> DetectionBatch:
        """Return all representable candidates, never an implicit primary."""


class LegacyMediaPipeBackend:
    """Conservative adapter over the existing MediaPipe foundation.

    The legacy extractor exposes only its first mesh. When its independent
    detector reports multiple faces, the engine receives a count/candidate
    mismatch and rejects the scan as ambiguous.
    """

    def detect(self, image_bytes: bytes, rgb: np.ndarray) -> DetectionBatch:
        # Lazy import keeps the isolated package usable in tests without
        # MediaPipe and avoids loading unrelated legacy modules unless used.
        from vedic.face_reading.landmarks import _get_face_detector, extract_landmarks

        detector_confidence = 0.0
        detector_bbox = None
        notes = []
        with _BACKEND_LOCK:
            value = extract_landmarks(
                image_bytes,
                angle="front",
                gender="U",
                enable_skin=False,
                enable_hairline=False,
                enable_features=False,
                apply_white_balance=False,
            )
            q = value.quality
            detector_count = int(q.face_count or 0)
            try:
                detector_output = _get_face_detector().process(rgb)
                detections = list(detector_output.detections or [])
                detector_count = len(detections)
                if len(detections) == 1 and detections[0].score:
                    detector_confidence = float(detections[0].score[0])
                    box = detections[0].location_data.relative_bounding_box
                    detector_bbox = (
                        float(box.xmin), float(box.ymin),
                        float(box.width), float(box.height),
                    )
            except Exception:
                notes.append("independent_detection_confidence_unavailable")
        if not value.points_norm:
            return DetectionBatch(
                [], detector_count, "legacy_mediapipe_478", notes=notes
            )
        xs = [float(point[0]) for point in value.points_norm]
        ys = [float(point[1]) for point in value.points_norm]
        bbox = (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
        candidate = FaceCandidate(
            landmarks=[tuple(map(float, point)) for point in value.points_norm],
            confidence=max(0.0, min(1.0, detector_confidence)),
            bbox=bbox,
            pose={
                "yaw_degrees": float(q.yaw_deg),
                "pitch_degrees": float(q.pitch_deg),
                "roll_degrees": float(q.roll_deg),
            },
            evidence={
                "glasses_observed": bool(
                    value.occlusion and value.occlusion.glasses_likely
                ),
                "detector_face_count": detector_count,
                "confidence_source": (
                    "mediapipe_face_detection_score"
                    if detector_confidence > 0
                    else "unavailable"
                ),
                "independent_detection_bbox": detector_bbox,
            },
        )
        return DetectionBatch(
            [candidate], max(1, detector_count), "legacy_mediapipe_478",
            notes=notes,
        )

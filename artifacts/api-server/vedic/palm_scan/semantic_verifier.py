"""Optional OpenCV-DNN semantic line identity verifier.

The verifier emits candidate IDs and confidence only. Geometry always comes
from the existing pixel-derived crease detector.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from .dataset import LINE_CLASSES, PREPROCESSING_VERSION
from .geometric_verifier import GeometricLineVerifier

EXPECTED_NORMALIZATION = {
    "scale": 1.0 / 255.0,
    "mean": [.485, .456, .406],
    "std": [.229, .224, .225],
}


class OpenCVDNNSemanticLineVerifier:
    def __init__(
        self,
        model_path: str | Path | None,
        *,
        metadata_path: str | Path | None = None,
        input_size: tuple[int, int] | None = None,
        probability_threshold: float = .60,
        overlap_threshold: float = .35,
        quality_threshold: float = .55,
        uniqueness_margin: float = .05,
        net_loader: Callable[[str], object] = cv2.dnn.readNetFromONNX,
    ):
        self.model_path = Path(model_path) if model_path else None
        self.input_size = input_size
        self.probability_threshold = probability_threshold
        self.overlap_threshold = overlap_threshold
        self.quality_threshold = quality_threshold
        self.uniqueness_margin = uniqueness_margin
        self.net = None
        self.metadata: dict = {}
        self.load_error: str | None = None
        self.last_evidence: dict = {"status": "model_unavailable"}
        if self.model_path is None or not self.model_path.is_file():
            return
        metadata_file = (
            Path(metadata_path) if metadata_path
            else self.model_path.with_suffix(".metadata.json")
        )
        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            _validate_model_metadata(metadata)
            metadata_input = metadata["input"]
            metadata_size = (
                int(metadata_input["width"]), int(metadata_input["height"])
            )
            if self.input_size is not None and tuple(self.input_size) != metadata_size:
                raise ValueError("constructor input_size conflicts with model metadata")
            self.input_size = metadata_size
            self.metadata = metadata
            self.net = net_loader(str(self.model_path))
            self.last_evidence = {
                "status": "ready",
                "model_version": metadata.get("model_version", "unknown"),
                "dataset_manifest_sha256": metadata.get("dataset_manifest_sha256"),
                "preprocessing_version": metadata.get("preprocessing_version"),
            }
        except Exception as exc:
            self.load_error = type(exc).__name__
            self.net = None
            self.last_evidence = {
                "status": "model_unavailable",
                "error_type": self.load_error,
            }

    def verify(self, candidates: list[dict], context: dict) -> dict[str, dict]:
        if self.net is None:
            self.last_evidence = {**self.last_evidence, "status": "model_unavailable"}
            return {}
        rgb = context.get("processed_rgb")
        palm_mask = context.get("palm_mask")
        quality = context.get("quality", {})
        quality_score = float(quality.get("score", 0.0))
        if (
            not isinstance(rgb, np.ndarray)
            or rgb.ndim != 3
            or rgb.shape[2] != 3
            or not isinstance(palm_mask, np.ndarray)
            or not quality.get("usable")
            or quality_score < self.quality_threshold
            or not candidates
        ):
            self.last_evidence = {
                **self.last_evidence,
                "status": "quality_gate_failed",
                "quality_score": round(quality_score, 4),
            }
            return {}
        probabilities = self._infer(rgb)
        height, width = probabilities.shape[1:]
        resized_palm = cv2.resize(
            np.uint8(palm_mask > 0), (width, height), interpolation=cv2.INTER_NEAREST
        )
        probabilities *= resized_palm[None, :, :]
        thresholds = self.metadata.get("thresholds", {})
        proposals: list[tuple[float, str, str, float, float]] = []
        for class_index, name in enumerate(LINE_CLASSES):
            calibration = self.metadata["calibration_by_class"][name]
            if calibration.get("status") != "evaluated":
                continue
            class_map = probabilities[class_index]
            threshold = float(thresholds.get(name, self.probability_threshold))
            ranked = []
            for candidate in candidates:
                candidate_id = candidate.get("id")
                path = candidate.get("path", [])
                if not isinstance(candidate_id, str) or len(path) < 2:
                    continue
                path_mask = self._path_mask(path, (height, width))
                path_pixels = path_mask > 0
                if not np.any(path_pixels):
                    continue
                mean_probability = float(np.mean(class_map[path_pixels]))
                overlap = float(np.mean(class_map[path_pixels] >= threshold))
                confidence = min(
                    mean_probability,
                    overlap,
                    float(candidate.get("confidence", 0.0)),
                    quality_score,
                )
                ranked.append((confidence, candidate_id, mean_probability, overlap))
            ranked.sort(reverse=True)
            if not ranked:
                continue
            best = ranked[0]
            runner_up = ranked[1][0] if len(ranked) > 1 else 0.0
            if (
                best[2] >= threshold
                and best[3] >= self.overlap_threshold
                and best[0] >= min(threshold, self.overlap_threshold)
                and best[0] - runner_up >= self.uniqueness_margin
            ):
                proposals.append((best[0], name, best[1], best[2], best[3]))
        proposals.sort(reverse=True)
        assignments: dict[str, dict] = {}
        used_candidates: set[str] = set()
        for confidence, name, candidate_id, _, _ in proposals:
            if candidate_id in used_candidates:
                continue
            assignments[name] = {
                "candidate_id": candidate_id,
                "confidence": round(confidence, 6),
            }
            used_candidates.add(candidate_id)
        self.last_evidence = {
            "status": "completed",
            "model_version": self.metadata.get("model_version", "unknown"),
            "dataset_manifest_sha256": self.metadata.get("dataset_manifest_sha256"),
            "preprocessing_version": self.metadata.get("preprocessing_version"),
            "assigned_classes": sorted(assignments),
            "requirements": [
                "candidate_overlap", "class_probability", "quality_gate", "uniqueness",
            ],
        }
        return assignments

    def _infer(self, rgb: np.ndarray) -> np.ndarray:
        if self.input_size is None:
            raise ValueError("semantic model input size is unavailable")
        width, height = self.input_size
        resized = cv2.resize(rgb, (width, height), interpolation=cv2.INTER_AREA)
        normalization = self.metadata["normalization"]
        blob = cv2.dnn.blobFromImage(
            resized, scalefactor=float(normalization["scale"]), size=(width, height),
            mean=(0, 0, 0), swapRB=False, crop=False,
        )
        std = np.asarray(normalization["std"], np.float32).reshape(1, 3, 1, 1)
        mean_scaled = np.asarray(normalization["mean"], np.float32).reshape(1, 3, 1, 1)
        blob = (blob - mean_scaled) / std
        self.net.setInput(blob)
        output = np.asarray(self.net.forward(), np.float32)
        if output.ndim == 4:
            output = output[0]
        if output.shape[0] != len(LINE_CLASSES):
            raise ValueError("semantic model output class count is incompatible")
        if self.metadata.get("output_activation", "logits") == "logits":
            output = 1.0 / (1.0 + np.exp(-np.clip(output, -30, 30)))
        return output

    @staticmethod
    def _path_mask(path: list[dict], shape: tuple[int, int]) -> np.ndarray:
        height, width = shape
        mask = np.zeros((height, width), np.uint8)
        points = np.int32([
            [
                round(float(point["x"]) * (width - 1)),
                round(float(point["y"]) * (height - 1)),
            ]
            for point in path
            if isinstance(point, dict) and "x" in point and "y" in point
        ])
        if len(points) >= 2:
            cv2.polylines(mask, [points], False, 1, max(2, round(min(width, height) * .012)))
        return mask


def _validate_model_metadata(metadata: object) -> None:
    if not isinstance(metadata, dict):
        raise ValueError("semantic model metadata must be an object")
    if metadata.get("trained") is not True:
        raise ValueError("semantic model metadata does not mark model as trained")
    if tuple(metadata.get("class_order", ())) != LINE_CLASSES:
        raise ValueError("semantic model class_order is incompatible")
    if metadata.get("preprocessing_version") != PREPROCESSING_VERSION:
        raise ValueError("semantic model preprocessing_version is incompatible")
    version = metadata.get("model_version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("semantic model model_version must be non-empty")
    digest = metadata.get("dataset_manifest_sha256")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest.lower())
    ):
        raise ValueError("semantic model dataset manifest hash is invalid")
    thresholds = metadata.get("thresholds")
    if not isinstance(thresholds, dict) or set(thresholds) != set(LINE_CLASSES):
        raise ValueError("semantic model thresholds must cover every class")
    for name, value in thresholds.items():
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not np.isfinite(value)
            or not 0 <= float(value) <= 1
        ):
            raise ValueError(f"semantic model threshold for {name} is invalid")
    calibration = metadata.get("calibration_by_class")
    if not isinstance(calibration, dict) or set(calibration) != set(LINE_CLASSES):
        raise ValueError(
            "semantic model calibration_by_class must cover every class"
        )
    for name, record in calibration.items():
        if not isinstance(record, dict) or record.get("status") not in {
            "evaluated", "not_evaluated",
        }:
            raise ValueError(
                f"semantic model calibration status for {name} is invalid"
            )
        if record["status"] == "evaluated":
            threshold = record.get("threshold")
            if (
                not isinstance(threshold, (int, float))
                or isinstance(threshold, bool)
                or not np.isfinite(threshold)
                or not 0 <= float(threshold) <= 1
                or not isinstance(record.get("supervised_examples"), int)
                or isinstance(record.get("supervised_examples"), bool)
                or record["supervised_examples"] <= 0
            ):
                raise ValueError(
                    f"semantic model calibration evidence for {name} is invalid"
                )
            if not np.isclose(float(thresholds[name]), float(threshold)):
                raise ValueError(
                    f"semantic model threshold for {name} disagrees with calibration"
                )
    input_metadata = metadata.get("input")
    if not isinstance(input_metadata, dict):
        raise ValueError("semantic model input metadata is required")
    if (
        not isinstance(input_metadata.get("width"), int)
        or isinstance(input_metadata.get("width"), bool)
        or input_metadata["width"] <= 0
        or not isinstance(input_metadata.get("height"), int)
        or isinstance(input_metadata.get("height"), bool)
        or input_metadata["height"] <= 0
        or input_metadata.get("channels") != 3
        or input_metadata.get("color_order") != "RGB"
    ):
        raise ValueError("semantic model input metadata is incompatible")
    normalization = metadata.get("normalization")
    if not isinstance(normalization, dict):
        raise ValueError("semantic model normalization metadata is required")
    if not np.isclose(normalization.get("scale", np.nan), EXPECTED_NORMALIZATION["scale"]):
        raise ValueError("semantic model normalization scale is incompatible")
    for key in ("mean", "std"):
        values = normalization.get(key)
        expected = EXPECTED_NORMALIZATION[key]
        if (
            not isinstance(values, list)
            or len(values) != 3
            or any(
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not np.isfinite(value)
                for value in values
            )
            or not np.allclose(values, expected)
        ):
            raise ValueError(f"semantic model normalization {key} is incompatible")
    if any(float(value) <= 0 for value in normalization["std"]):
        raise ValueError("semantic model normalization std must be positive")
    if metadata.get("output_activation") not in {"logits", "probabilities"}:
        raise ValueError("semantic model output_activation is incompatible")
    class_weights = metadata.get("class_weights")
    if not isinstance(class_weights, dict) or set(class_weights) != set(LINE_CLASSES):
        raise ValueError("semantic model class_weights must cover every class")
    if any(
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not np.isfinite(value)
        or float(value) < 0
        for value in class_weights.values()
    ):
        raise ValueError("semantic model class_weights are invalid")
    if not isinstance(metadata.get("supervision_policy"), dict):
        raise ValueError("semantic model supervision_policy is required")


class HybridLineVerifier:
    """Prefer ONNX semantic assignments; fall back to geometric regions."""

    def __init__(
        self,
        primary: OpenCVDNNSemanticLineVerifier,
        fallback: GeometricLineVerifier,
    ):
        self.primary = primary
        self.fallback = fallback
        self.last_evidence: dict = {"status": "ready", "method": "hybrid_semantic_geometric"}

    def verify(self, candidates: list[dict], context: dict) -> dict[str, dict]:
        assignments = self.primary.verify(candidates, context)
        primary_evidence = dict(getattr(self.primary, "last_evidence", {}))
        if assignments:
            self.last_evidence = {
                **primary_evidence,
                "method": "opencv_dnn_semantic",
                "used_fallback": False,
            }
            return assignments
        fallback_assignments = self.fallback.verify(candidates, context)
        self.last_evidence = {
            **primary_evidence,
            "method": "hybrid_semantic_geometric",
            "used_fallback": True,
            "fallback": dict(getattr(self.fallback, "last_evidence", {})),
        }
        return fallback_assignments


def default_line_verifier():
    """Production factory: ONNX when PALM_SEMANTIC_ONNX_PATH is set and loads."""
    import os

    fallback = GeometricLineVerifier()
    onnx_path = (os.environ.get("PALM_SEMANTIC_ONNX_PATH") or "").strip()
    if not onnx_path:
        return fallback
    metadata_path = (os.environ.get("PALM_SEMANTIC_ONNX_METADATA_PATH") or "").strip() or None
    semantic = OpenCVDNNSemanticLineVerifier(onnx_path, metadata_path=metadata_path)
    if semantic.net is None:
        return fallback
    return HybridLineVerifier(semantic, fallback)

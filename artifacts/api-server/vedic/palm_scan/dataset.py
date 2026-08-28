"""Versioned palm dataset contract and deterministic annotation tooling.

Images remain external: manifests contain only safe relative paths or metadata
for externally managed HTTP(S) URIs.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

import cv2
import numpy as np

from .ground_truth import ANNOTATION_SCHEMA

DATASET_SCHEMA = "palm_scan_dataset/1.0"
PREPROCESSING_VERSION = "palm_semantic_rgb/1.0"
LINE_CLASSES = (
    "heart_line", "head_line", "life_line", "fate_line",
    "sun_apollo_line", "mercury_line", "mars_support_line",
)
MASK_CLASSES = LINE_CLASSES + ("hand_mask", "palm_mask")
MOUNT_CLASSES = (
    "Jupiter", "Saturn", "Sun/Apollo", "Mercury",
    "Upper Mars", "Lower Mars", "Venus", "Moon/Luna",
)
READABILITY = {"clear", "faint", "occluded", "unknown"}
SPLITS = {"unassigned", "train", "val", "test"}
REVIEW_STATUS = {"draft", "annotated", "in_review", "approved", "rejected"}
HANDEDNESS = {"left", "right", "unknown"}
QUALITY_LABELS = {"good", "acceptable", "poor", "unknown"}
CONSENT_STATUSES = {"granted", "withdrawn", "not_applicable"}
CONSENT_USES = {"annotation", "model_training", "evaluation"}
DEFAULT_FAINT_WEIGHT = 0.35


def create_manifest(dataset_id: str, version: str = "1.0") -> dict:
    if not _nonempty(dataset_id) or not _nonempty(version):
        raise ValueError("dataset_id and version must be non-empty strings")
    return {
        "dataset_schema": DATASET_SCHEMA,
        "annotation_schema": ANNOTATION_SCHEMA,
        "dataset_id": dataset_id,
        "version": version,
        "samples": [],
    }


def save_manifest(manifest: dict, path: str | Path, *, overwrite: bool = False) -> Path:
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("Invalid palm dataset: " + "; ".join(errors))
    destination = Path(path)
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return destination


def load_manifest(path: str | Path) -> dict:
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("Invalid palm dataset: " + "; ".join(errors))
    return manifest


def manifest_hash(manifest: dict) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_manifest(manifest: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]
    _equals(manifest, "dataset_schema", DATASET_SCHEMA, errors)
    _equals(manifest, "annotation_schema", ANNOTATION_SCHEMA, errors)
    for key in ("dataset_id", "version"):
        if not _nonempty(manifest.get(key)):
            errors.append(f"{key} must be a non-empty string")
    samples = manifest.get("samples")
    if not isinstance(samples, list):
        return errors + ["samples must be an array"]
    image_ids: set[str] = set()
    subject_splits: dict[str, set[str]] = defaultdict(set)
    for index, sample in enumerate(samples):
        _validate_sample(sample, f"samples[{index}]", errors)
        if not isinstance(sample, dict):
            continue
        image = sample.get("image")
        image_id = image.get("id") if isinstance(image, dict) else None
        if isinstance(image_id, str):
            if image_id in image_ids:
                errors.append(f"samples[{index}].image.id must be unique")
            image_ids.add(image_id)
        subject = sample.get("subject_id")
        split = sample.get("split")
        if _nonempty(subject) and split in {"train", "val", "test"}:
            subject_splits[subject].add(split)
    for subject, assigned in sorted(subject_splits.items()):
        if len(assigned) > 1:
            errors.append(
                f"subject_id {subject!r} leaks across splits: {sorted(assigned)}"
            )
    return errors


def _validate_sample(sample: Any, where: str, errors: list[str]) -> None:
    if not isinstance(sample, dict):
        errors.append(f"{where} must be an object")
        return
    if not _nonempty(sample.get("subject_id")):
        errors.append(f"{where}.subject_id must be a non-empty string")
    if sample.get("split") not in SPLITS:
        errors.append(f"{where}.split must be one of {sorted(SPLITS)}")
    if sample.get("handedness") not in HANDEDNESS:
        errors.append(f"{where}.handedness must be one of {sorted(HANDEDNESS)}")
    image = sample.get("image")
    if not isinstance(image, dict):
        errors.append(f"{where}.image must be an object")
    else:
        _validate_image(image, f"{where}.image", errors)
    annotations = sample.get("annotations")
    if not isinstance(annotations, dict):
        errors.append(f"{where}.annotations must be an object")
        return
    if annotations.get("coordinate_space") != "normalized_0_1":
        errors.append(f"{where}.annotations.coordinate_space must be normalized_0_1")
    landmarks = annotations.get("landmarks")
    if not isinstance(landmarks, list):
        errors.append(f"{where}.annotations.landmarks must be an array")
    else:
        for index, landmark in enumerate(landmarks):
            location = f"{where}.annotations.landmarks[{index}]"
            if not isinstance(landmark, dict):
                errors.append(f"{location} must be an object")
                continue
            if not isinstance(landmark.get("id"), int) or isinstance(landmark.get("id"), bool):
                errors.append(f"{location}.id must be an integer")
            if not _nonempty(landmark.get("name")):
                errors.append(f"{location}.name must be a non-empty string")
            _point(landmark, location, errors, keys=("normalized_x", "normalized_y"))
            _confidence(landmark.get("confidence"), f"{location}.confidence", errors)
    segmentations = annotations.get("segmentations")
    if not isinstance(segmentations, dict):
        errors.append(f"{where}.annotations.segmentations must be an object")
    else:
        for name in ("hand", "palm"):
            _polygon_record(segmentations.get(name), f"{where}.annotations.segmentations.{name}", errors)
    lines = annotations.get("major_lines")
    if not isinstance(lines, dict) or set(lines) != set(LINE_CLASSES):
        errors.append(f"{where}.annotations.major_lines must contain exactly {list(LINE_CLASSES)}")
    else:
        for name in LINE_CLASSES:
            _line(lines[name], f"{where}.annotations.major_lines.{name}", errors)
    mounts = annotations.get("mounts")
    if not isinstance(mounts, dict) or set(mounts) != set(MOUNT_CLASSES):
        errors.append(f"{where}.annotations.mounts must contain exactly {list(MOUNT_CLASSES)}")
    else:
        for name in MOUNT_CLASSES:
            _polygon_record(mounts[name], f"{where}.annotations.mounts.{name}", errors)
    markings = annotations.get("markings")
    if not isinstance(markings, list):
        errors.append(f"{where}.annotations.markings must be an array")
    else:
        for index, marking in enumerate(markings):
            location = f"{where}.annotations.markings[{index}]"
            if not isinstance(marking, dict) or not _nonempty(marking.get("type")):
                errors.append(f"{location}.type must be a non-empty string")
                continue
            points = marking.get("points")
            if not isinstance(points, list):
                errors.append(f"{location}.points must be an array")
            else:
                for point_index, point in enumerate(points):
                    _point(point, f"{location}.points[{point_index}]", errors)
            _confidence(marking.get("confidence"), f"{location}.confidence", errors)
    quality = sample.get("capture_quality")
    if not isinstance(quality, dict):
        errors.append(f"{where}.capture_quality must be an object")
    else:
        for key in ("overall", "lighting", "focus", "occlusion", "framing"):
            if quality.get(key) not in QUALITY_LABELS:
                errors.append(f"{where}.capture_quality.{key} must be one of {sorted(QUALITY_LABELS)}")
    review = sample.get("review")
    if not isinstance(review, dict):
        errors.append(f"{where}.review must be an object")
    else:
        if review.get("status") not in REVIEW_STATUS:
            errors.append(f"{where}.review.status must be one of {sorted(REVIEW_STATUS)}")
        for key in ("annotator_id", "reviewer_id"):
            value = review.get(key)
            if value is not None and not _nonempty(value):
                errors.append(f"{where}.review.{key} must be null or a non-empty string")
    provenance = sample.get("provenance")
    if not isinstance(provenance, dict):
        errors.append(f"{where}.provenance must be an object")
    else:
        for key in ("created_at", "annotation_tool", "annotation_version"):
            if not _nonempty(provenance.get(key)):
                errors.append(f"{where}.provenance.{key} must be a non-empty string")


def _validate_image(image: dict, where: str, errors: list[str]) -> None:
    if not _safe_identifier(image.get("id")):
        errors.append(
            f"{where}.id must use only letters, numbers, dot, underscore, or hyphen"
        )
    path, uri = image.get("path"), image.get("uri")
    if (path is None) == (uri is None):
        errors.append(f"{where} must define exactly one of path or uri")
    if path is not None and not is_safe_relative_path(path):
        errors.append(f"{where}.path must be a safe relative path")
    if uri is not None:
        if not _nonempty(uri) or urlparse(uri).scheme not in {"https", "http"}:
            errors.append(f"{where}.uri must be an HTTP(S) URI")
    for key in ("width", "height"):
        value = image.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"{where}.{key} must be a positive integer")
    digest = image.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(
        char not in "0123456789abcdef" for char in digest.lower()
    ):
        errors.append(f"{where}.sha256 must be a 64-character hexadecimal string")
    for key in ("license", "source"):
        if not _nonempty(image.get(key)):
            errors.append(f"{where}.{key} must be a non-empty string")
    consent = image.get("consent")
    if not isinstance(consent, dict):
        errors.append(f"{where}.consent must be an object")
    else:
        if consent.get("status") not in CONSENT_STATUSES:
            errors.append(
                f"{where}.consent.status must be one of {sorted(CONSENT_STATUSES)}"
            )
        uses = consent.get("allowed_uses")
        if (
            not isinstance(uses, list)
            or not uses
            or not all(isinstance(item, str) and item in CONSENT_USES for item in uses)
        ):
            errors.append(
                f"{where}.consent.allowed_uses must contain values from "
                f"{sorted(CONSENT_USES)}"
            )
        if not _nonempty(consent.get("record_id")):
            errors.append(f"{where}.consent.record_id must be a non-empty string")
        if not _nonempty(consent.get("recorded_at")):
            errors.append(f"{where}.consent.recorded_at must be a non-empty string")
        if (
            consent.get("status") == "not_applicable"
            and not _nonempty(consent.get("legal_basis"))
        ):
            errors.append(
                f"{where}.consent.legal_basis is required when status is not_applicable"
            )


def _line(line: Any, where: str, errors: list[str]) -> None:
    if not isinstance(line, dict):
        errors.append(f"{where} must be an object")
        return
    readability = line.get("readability")
    if readability not in READABILITY:
        errors.append(f"{where}.readability must be one of {sorted(READABILITY)}")
    _confidence(line.get("confidence"), f"{where}.confidence", errors)
    points = line.get("path", [])
    if not isinstance(points, list):
        errors.append(f"{where}.path must be an array")
    else:
        if (
            readability in {"clear", "faint", "occluded"}
            and len(points) < 2
            and not line.get("mask_path")
            and not line.get("mask_polygon")
        ):
            errors.append(f"{where} requires a path or mask_path when readable")
        for index, point in enumerate(points):
            _point(point, f"{where}.path[{index}]", errors)
    mask_path = line.get("mask_path")
    if mask_path is not None and not is_safe_relative_path(mask_path):
        errors.append(f"{where}.mask_path must be a safe relative path")
    if mask_path is not None:
        digest = line.get("mask_sha256")
        if not _sha256_string(digest):
            errors.append(f"{where}.mask_sha256 is required with mask_path")
    mask_polygon = line.get("mask_polygon")
    if mask_polygon is not None:
        if not isinstance(mask_polygon, list) or len(mask_polygon) < 3:
            errors.append(f"{where}.mask_polygon requires at least three points")
        else:
            for index, point in enumerate(mask_polygon):
                _point(point, f"{where}.mask_polygon[{index}]", errors)


def _polygon_record(value: Any, where: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{where} must be an object")
        return
    polygon = value.get("polygon")
    if not isinstance(polygon, list) or len(polygon) < 3:
        errors.append(f"{where}.polygon requires at least three points")
        return
    for index, point in enumerate(polygon):
        _point(point, f"{where}.polygon[{index}]", errors)
    _confidence(value.get("confidence"), f"{where}.confidence", errors)


def _point(value: Any, where: str, errors: list[str], keys: tuple[str, str] = ("x", "y")) -> None:
    if not isinstance(value, dict):
        errors.append(f"{where} must be an object")
        return
    for key in keys:
        number = value.get(key)
        if (
            not isinstance(number, (int, float))
            or isinstance(number, bool)
            or not math.isfinite(float(number))
            or not 0 <= float(number) <= 1
        ):
            errors.append(f"{where}.{key} must be a finite number within 0..1")


def _confidence(value: Any, where: str, errors: list[str]) -> None:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
        or not 0 <= float(value) <= 1
    ):
        errors.append(f"{where} must be a finite number within 0..1")


def _equals(value: dict, key: str, expected: str, errors: list[str]) -> None:
    if value.get(key) != expected:
        errors.append(f"{key} must equal {expected}")


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _safe_identifier(value: Any) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value) is not None
        and value not in {".", ".."}
    )


def is_safe_relative_path(value: Any) -> bool:
    if not _nonempty(value) or "\x00" in value or "\\" in value or ":" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and path.parts[0] not in {"", "."}


def resolve_asset_path(asset_root: str | Path, relative_path: str) -> Path:
    if not is_safe_relative_path(relative_path):
        raise ValueError(f"unsafe relative asset path: {relative_path!r}")
    root = Path(asset_root).resolve()
    resolved = (root / PurePosixPath(relative_path)).resolve()
    if resolved == root or root not in resolved.parents:
        raise ValueError(f"asset path escapes asset root: {relative_path!r}")
    return resolved


def validate_local_assets(
    manifest: dict,
    asset_root: str | Path,
    *,
    reject_remote: bool = False,
    require_training_consent: bool = False,
) -> list[str]:
    """Validate local image/mask integrity once before export or training."""
    errors = validate_manifest(manifest)
    if errors:
        return errors
    cache: dict[Path, tuple[str, tuple[int, int] | None]] = {}

    def inspect(relative: str, location: str) -> tuple[str, tuple[int, int] | None] | None:
        try:
            path = resolve_asset_path(asset_root, relative)
        except ValueError as exc:
            errors.append(f"{location}: {exc}")
            return None
        if not path.is_file():
            errors.append(f"{location} does not exist: {relative}")
            return None
        if path not in cache:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            decoded = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            dimensions = (
                (int(decoded.shape[1]), int(decoded.shape[0]))
                if decoded is not None and decoded.ndim >= 2 else None
            )
            cache[path] = digest, dimensions
        return cache[path]

    for index, sample in enumerate(manifest["samples"]):
        image = sample["image"]
        location = f"samples[{index}].image"
        consent = image["consent"]
        if require_training_consent and (
            consent["status"] == "withdrawn"
            or "model_training" not in consent["allowed_uses"]
        ):
            errors.append(
                f"{location}.consent does not authorize model_training"
            )
        if "uri" in image:
            if reject_remote:
                errors.append(
                    f"{location}.uri is not supported offline; materialize it as a local path"
                )
            continue
        inspected = inspect(image["path"], f"{location}.path")
        if inspected:
            digest, dimensions = inspected
            if digest.lower() != image["sha256"].lower():
                errors.append(f"{location}.sha256 does not match local asset")
            expected = (image["width"], image["height"])
            if dimensions is None:
                errors.append(f"{location}.path is not a decodable image")
            elif dimensions != expected:
                errors.append(
                    f"{location} dimensions {dimensions} do not match manifest {expected}"
                )
        for name in LINE_CLASSES:
            line = sample["annotations"]["major_lines"][name]
            if not line.get("mask_path"):
                continue
            mask_location = f"samples[{index}].annotations.major_lines.{name}"
            inspected_mask = inspect(line["mask_path"], f"{mask_location}.mask_path")
            if inspected_mask:
                digest, dimensions = inspected_mask
                if digest.lower() != line["mask_sha256"].lower():
                    errors.append(f"{mask_location}.mask_sha256 does not match local asset")
                expected = (image["width"], image["height"])
                if dimensions is None:
                    errors.append(f"{mask_location}.mask_path is not a decodable image")
                elif dimensions != expected:
                    errors.append(
                        f"{mask_location}.mask_path dimensions {dimensions} "
                        f"do not match image {expected}"
                    )
    return errors


def _sha256_string(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value.lower())
    )


def grouped_split(
    manifest: dict,
    *,
    seed: int = 1337,
    train: float = 0.7,
    val: float = 0.15,
    test: float = 0.15,
) -> dict:
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("Invalid palm dataset: " + "; ".join(errors))
    ratios = (train, val, test)
    if any(not isinstance(v, (int, float)) or v < 0 for v in ratios) or not math.isclose(sum(ratios), 1.0):
        raise ValueError("split ratios must be non-negative and sum to 1")
    output = json.loads(json.dumps(manifest))
    grouped: dict[str, list[dict]] = defaultdict(list)
    for sample in output["samples"]:
        grouped[sample["subject_id"]].append(sample)
    subjects = sorted(grouped)
    random.Random(seed).shuffle(subjects)
    total_samples = len(output["samples"])
    targets = {"train": total_samples * train, "val": total_samples * val, "test": total_samples * test}
    counts = Counter()
    for subject in subjects:
        size = len(grouped[subject])
        choices = ("train", "val", "test")
        split = min(
            choices,
            key=lambda name: (
                (counts[name] + size - targets[name]) ** 2 - (counts[name] - targets[name]) ** 2,
                choices.index(name),
            ),
        )
        counts[split] += size
        for sample in grouped[subject]:
            sample["split"] = split
    return output


def rasterize_sample(
    sample: dict,
    size: tuple[int, int] = (256, 256),
    *,
    asset_root: str | Path | None = None,
    include_landmarks: bool = False,
    line_width: int = 3,
    heatmap_sigma: float = 2.5,
) -> tuple[np.ndarray, tuple[str, ...]]:
    wrapper = create_manifest("single-sample")
    wrapper["samples"] = [sample]
    errors = validate_manifest(wrapper)
    if errors:
        raise ValueError("Invalid palm sample: " + "; ".join(errors))
    height, width = size
    if height <= 0 or width <= 0:
        raise ValueError("raster size must be positive")
    annotations = sample["annotations"]
    channels: list[np.ndarray] = []
    for name in LINE_CLASSES:
        mask = np.zeros((height, width), np.uint8)
        line = annotations["major_lines"][name]
        mask_polygon = line.get("mask_polygon", [])
        if len(mask_polygon) >= 3:
            polygon = np.int32([
                [round(point["x"] * (width - 1)), round(point["y"] * (height - 1))]
                for point in mask_polygon
            ])
            cv2.fillPoly(mask, [polygon], 1)
        mask_path = line.get("mask_path")
        if mask_path:
            if asset_root is None:
                raise ValueError(
                    f"{name}.mask_path requires an explicit asset_root"
                )
            resolved = resolve_asset_path(asset_root, mask_path)
            loaded = cv2.imread(str(resolved), cv2.IMREAD_GRAYSCALE)
            if loaded is None:
                raise OSError(f"unable to read line mask: {resolved}")
            loaded = cv2.resize(
                loaded, (width, height), interpolation=cv2.INTER_NEAREST
            )
            mask = np.maximum(mask, np.uint8(loaded > 0))
        points = line.get("path", [])
        if len(points) >= 2:
            pixels = np.int32([
                [round(point["x"] * (width - 1)), round(point["y"] * (height - 1))]
                for point in points
            ])
            cv2.polylines(mask, [pixels], False, 1, max(1, int(line_width)))
        channels.append(mask)
    for name in ("hand", "palm"):
        mask = np.zeros((height, width), np.uint8)
        polygon = np.int32([
            [round(point["x"] * (width - 1)), round(point["y"] * (height - 1))]
            for point in annotations["segmentations"][name]["polygon"]
        ])
        cv2.fillPoly(mask, [polygon], 1)
        channels.append(mask)
    names: tuple[str, ...] = MASK_CLASSES
    if include_landmarks:
        yy, xx = np.mgrid[:height, :width]
        for landmark in annotations["landmarks"]:
            center_x = landmark["normalized_x"] * (width - 1)
            center_y = landmark["normalized_y"] * (height - 1)
            heatmap = np.exp(
                -((xx - center_x) ** 2 + (yy - center_y) ** 2)
                / (2.0 * heatmap_sigma ** 2)
            ).astype(np.float32)
            channels.append(heatmap)
        names += tuple(f"landmark:{item['name']}" for item in annotations["landmarks"])
    return np.stack(channels).astype(np.float32), names


def line_supervision_weights(
    sample: dict, *, faint_weight: float = DEFAULT_FAINT_WEIGHT
) -> np.ndarray:
    """Per-class loss/metric weights; unknown and occluded are ignored."""
    if (
        not isinstance(faint_weight, (int, float))
        or isinstance(faint_weight, bool)
        or not math.isfinite(float(faint_weight))
        or not 0 <= float(faint_weight) <= 1
    ):
        raise ValueError("faint_weight must be a finite number within 0..1")
    mapping = {
        "clear": 1.0,
        "faint": float(faint_weight),
        "unknown": 0.0,
        # Default policy: visible partial occluded annotations are not complete
        # enough to supervise absence outside the traced portion.
        "occluded": 0.0,
    }
    lines = sample.get("annotations", {}).get("major_lines", {})
    return np.asarray([
        mapping.get(lines.get(name, {}).get("readability"), 0.0)
        for name in LINE_CLASSES
    ], dtype=np.float32)


def calibrate_thresholds_numpy(
    probabilities: np.ndarray,
    targets: np.ndarray,
    supervision: np.ndarray,
) -> dict[str, dict]:
    """Calibrate only classes with supervised validation examples."""
    _validate_metric_arrays(probabilities, targets, supervision)
    output: dict[str, dict] = {}
    for index, name in enumerate(LINE_CLASSES):
        selected = supervision[:, index] > 0
        if not np.any(selected):
            output[name] = {"status": "not_evaluated", "threshold": None}
            continue
        truth = targets[selected, index] >= .5
        weights = supervision[selected, index, None, None]
        best_threshold, best_score = .5, -1.0
        for threshold in np.linspace(.20, .80, 25):
            predicted = probabilities[selected, index] >= threshold
            tp = float(np.sum(weights * (predicted & truth)))
            fp = float(np.sum(weights * (predicted & ~truth)))
            fn = float(np.sum(weights * (~predicted & truth)))
            score = 2 * tp / max(2 * tp + fp + fn, 1e-12)
            if score > best_score:
                best_threshold, best_score = float(threshold), score
        output[name] = {
            "status": "evaluated",
            "threshold": best_threshold,
            "supervised_examples": int(np.count_nonzero(selected)),
        }
    return output


def semantic_metrics_numpy(
    probabilities: np.ndarray,
    targets: np.ndarray,
    supervision: np.ndarray,
    thresholds: dict[str, float],
) -> dict[str, dict]:
    """Weighted metrics with explicit null state for unsupervised classes."""
    _validate_metric_arrays(probabilities, targets, supervision)
    output: dict[str, dict] = {}
    for index, name in enumerate(LINE_CLASSES):
        selected = supervision[:, index] > 0
        if not np.any(selected):
            output[name] = {
                "status": "not_evaluated",
                "iou": None, "dice": None, "precision": None, "recall": None,
                "supervised_examples": 0,
            }
            continue
        truth = targets[selected, index] >= .5
        predicted = probabilities[selected, index] >= thresholds[name]
        weights = supervision[selected, index, None, None]
        tp = float(np.sum(weights * (predicted & truth)))
        fp = float(np.sum(weights * (predicted & ~truth)))
        fn = float(np.sum(weights * (~predicted & truth)))
        union = tp + fp + fn
        output[name] = {
            "status": "evaluated",
            "iou": tp / max(union, 1e-12),
            "dice": 2 * tp / max(2 * tp + fp + fn, 1e-12),
            "precision": tp / max(tp + fp, 1e-12),
            "recall": tp / max(tp + fn, 1e-12),
            "supervised_examples": int(np.count_nonzero(selected)),
        }
    return output


def _validate_metric_arrays(
    probabilities: np.ndarray, targets: np.ndarray, supervision: np.ndarray
) -> None:
    if probabilities.shape != targets.shape or probabilities.ndim != 4:
        raise ValueError("probabilities and targets must have matching NCHW shapes")
    if probabilities.shape[1] != len(LINE_CLASSES):
        raise ValueError("metric arrays have incompatible class count")
    if supervision.shape != probabilities.shape[:2]:
        raise ValueError("supervision must have shape [samples, classes]")


def dataset_statistics(manifest: dict) -> dict:
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("Invalid palm dataset: " + "; ".join(errors))
    samples = manifest["samples"]
    readability = {
        name: dict(Counter(
            sample["annotations"]["major_lines"][name]["readability"] for sample in samples
        ))
        for name in LINE_CLASSES
    }
    return {
        "dataset_schema": DATASET_SCHEMA,
        "sample_count": len(samples),
        "subject_count": len({sample["subject_id"] for sample in samples}),
        "split_counts": dict(Counter(sample["split"] for sample in samples)),
        "handedness_counts": dict(Counter(sample["handedness"] for sample in samples)),
        "review_status_counts": dict(Counter(sample["review"]["status"] for sample in samples)),
        "capture_quality_counts": dict(Counter(
            sample["capture_quality"]["overall"] for sample in samples
        )),
        "line_readability": readability,
        "manifest_sha256": manifest_hash(manifest),
        "accuracy_claim": None,
    }

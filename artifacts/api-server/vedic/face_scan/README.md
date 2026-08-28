# Face Scan Phase 1

This package produces deterministic, measurement-only JSON (`schema_version:
1.0`) from one face image. It is isolated from the existing face-reading
routes and does not implement Phase 2.

## Technology

- Existing hardened `vedic.face_reading.image_io` handles magic-byte
  validation, EXIF orientation, mirroring, bounded decoding, and downscaling.
- The default adapter wraps the existing MediaPipe 478-point mesh with all
  legacy skin, hairline, and feature analyses disabled.
- MediaPipe Face Detection supplies an independent detection confidence and
  boundary check. Substantial detector/mesh boundary disagreement fails closed.
- An injectable backend protocol makes face count, candidates, confidence,
  pose, visibility, and observable obstruction evidence testable without
  MediaPipe or real images.
- OpenCV computes capture-quality and conservative pixel texture/line proxies.
  Annotation drawing consumes only coordinates already present in the JSON.

## HTTP contract

- `POST /api/face-scan`: multipart `image`, optional boolean `mirror`.
- Upload limit: 12 MB. Rate limit: 10 requests/minute when Flask-Limiter is
  available.
- `GET /api/face-scan/<scan_id>/annotated`: private, short-lived PNG from a
  bounded 32-item in-process cache; 30 requests/minute.
- There is intentionally no processed-image endpoint because Phase 1 does not
  expose a separately transformed image.

Unusable captures return the complete schema with measurement sections marked
unknown and no annotation reference. Multiple faces require either one face or
a dominant candidate supported by area and confidence evidence. The legacy
adapter fails closed when it reports multiple faces but exposes only one mesh.
Decoded but unusable images return HTTP 422. Issue codes follow the canonical
quality contract (`face_not_detected`, `excessive_blur`, `poor_lighting`,
`face_cropped`, `extreme_angle`, `important_landmarks_hidden`, and
`insufficient_resolution`).

Every exposed landmark, major measurement, region, symmetry result, and
classification carries confidence. Measurements that are not defensible from
the selected monocular 2D landmarks—such as physical chin projection, reliable
skin-mark identity, and eyebrow hair density—remain explicitly `unknown`.
Traditional zones include upper/middle/lower plus landmark-derived forehead,
eyebrow/eye, nose, bilateral cheek, mouth, chin, and left/right face polygons.

## Explicit exclusions

No health or disease claims, diagnosis, personality, first-impression,
Samudrika or mole meanings, ethnicity or gender inference, population
percentiles, attractiveness, narration, reports, or billing are produced.
Traditional zones are coordinate polygons only and have no meanings. Face
shape is a low-stakes geometry label and preserves ambiguity when thresholds
are close.

## Limitations

Coordinates and ratios are image-plane measurements affected by pose,
perspective, lens distortion, expression, crop, lighting, and detector error.
Relative mesh depth is not physical depth. Chin projection is explicitly
unknown from a monocular frontal image. Glasses, mask, and hair obstruction
issues are emitted only when the backend supplies observable evidence.
`face_scan_annotation/1.0` supports boundaries, landmarks, feature regions,
zone polygons, raw measurements with tolerances, and face-shape labels.
Evaluation reports landmark error, bounding-box and polygon IoU, measurement
error, classification correctness, and basic confidence calibration, but makes
no accuracy claim.

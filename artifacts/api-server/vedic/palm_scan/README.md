# Palm Scan Phase 1

This package measures visible properties of a single palm photograph. It does
not provide palmistry meanings, personality claims, health claims, or
predictions.

`POST /api/palm-scan` accepts multipart field `image` (maximum 12 MB) and an
optional explicit `mirror=true|false`. The JSON response follows schema version
`1.0`. Successful scans expose a short-lived PNG at the returned
`annotated_image_reference`. The original decoded pixels, deterministic
processed image, enhancement masks, and segmentation masks are also exposed by
bounded, private artifact URLs. The in-process cache holds at most 32 scans and
is intentionally ephemeral.

## Technology selection

- Pillow and the existing `face_reading.image_io` pipeline provide file magic
  validation, size limits, decode, animated-frame handling, EXIF orientation,
  optional HEIF support, and explicit mirror correction.
- MediaPipe Hands 0.10 supplies anatomical centerline landmarks. It is not a
  palm-line or marking model.
- OpenCV and NumPy provide deterministic planar normalization, illumination
  correction, CLAHE, bilateral denoise, guarded sharpening, landmark-supported
  GrabCut foreground separation, anatomical segmentation, blackhat/adaptive
  and Canny/ridge crease evidence,
  skeletonization, connected components, and measurable geometry.
- No additional model or dependency is hidden behind the API.

## Detection policy

- MediaPipe Hands supplies 21 anatomical landmarks and handedness. MediaPipe's
  mirrored-selfie handedness assumption is corrected after the optional input
  un-mirror operation.
- Geometry is reported as normalized coordinates plus raw pixel measurements.
- The generic CV detector can expose unlabelled crease candidates supported by
  image pixels. Two methods are fused and disagreement remains ambiguous. It
  cannot reliably identify the seven named palm lines; named lines therefore
  remain `unknown`/ambiguous in Phase 1 while retaining a complete measurement
  schema.
- Special markings are not emitted without a validated classifier.
- Mount elevation/development, static-image flexibility, and occlusion
  disambiguation are unsupported by ordinary monocular RGB and remain
  `unknown`.
- Union-line regions require an outer-edge view. A frontal palm image reports
  `outer_edge_not_visible`.
- A failed quality gate stops geometry and crease extraction. Confidence `0.55`
  is the explicit reliable/Phase 2 eligibility threshold.

Detector protocols in `detectors.py` permit fixture and future trained-model
injection without changing the response contract. A replaceable line-identity
verifier may assign only existing crease-candidate IDs; the engine copies their
pixel-derived paths and rejects duplicate or below-threshold assignments. This
prevents an ML or vision verifier from inventing coordinates.

## Ground truth and evaluation

`ground_truth.py` defines `palm_scan_annotation/1.0`, normalized-coordinate
validation/loading, an example annotation factory, and offline comparison for
landmark error, symmetric path error, segmentation IoU, detection
precision/recall/accuracy, and confidence calibration. These are evaluator
implementations only. No benchmark accuracy is claimed.

## Known limitations

- Foreground separation uses landmark-seeded GrabCut and falls back to explicit
  landmark geometry when pixel separation is unstable. It is not a trained
  hand-segmentation network; each section reports its method and confidence.
- Landmark homography is a planar perspective proxy and cannot recover 3-D
  shape, physical depth, mount prominence, or elevation.
- Strength, depth, texture, taper, and tip-shape fields are explicitly labelled
  pixel/geometry proxies. They are not physical measurements.
- A single image cannot establish flexibility or reliably separate occlusion
  from self-occlusion.
- Generic CV is sensitive to skin texture, lighting, compression, scars, and
  background leakage. It is not presented as a trained palm-line model.

# Palm semantic dataset and training pipeline

This tooling extends `palm_scan_annotation/1.0` with the versioned
`palm_scan_dataset/1.0` manifest. Images and raw image bytes are never embedded
in a manifest. A sample references either a safe path relative to the manifest
or an externally managed HTTP(S) URI.

## Sample contract

Every sample contains:

- `subject_id` and `split` (`unassigned`, `train`, `val`, or `test`). One
  subject must never appear in multiple train/validation/test splits.
- `image`: unique `id`, exactly one `path` or `uri`, positive `width` and
  `height`, lowercase-compatible SHA-256, `license`, structured `consent`, and
  `source`. Consent records include status, allowed uses, record ID, and date;
  withdrawn samples or samples without `model_training` scope cannot train.
  IDs are restricted to filename-safe tokens because raster exports use them
  as artifact names.
- normalized `0..1` annotations: landmarks, hand/palm polygons, exactly seven
  major-line records, exactly eight mount polygons, and markings.
- each line has `readability` (`clear`, `faint`, `occluded`, or `unknown`),
  annotation `confidence`, a normalized path when visible, and optionally a
  safe relative `mask_path` with `mask_sha256`.
- `handedness`, capture-quality labels, annotator/reviewer status, and
  provenance (`created_at`, tool, and annotation version).

The exact required fields and ranges are enforced by `dataset.py`. Absolute
paths, backslash paths, traversal (`..`), file URIs, non-finite coordinates,
booleans masquerading as numbers, duplicate image IDs, and subject leakage are
rejected.

## Annotation guidance

- **Clear:** trace the center of the visible crease continuously. Confidence
  describes annotation certainty, not a model score.
- **Faint:** trace only pixels the annotator can support; do not extrapolate
  through invisible regions. Use lower confidence.
- **Occluded:** trace visible portions only. Never bridge jewelry, fingers,
  glare, crops, or other obstruction by assumption. Occluded annotations are
  ignored for training by default because a partial trace cannot supervise
  absence outside its visible portion. No visible-partial loss policy is
  currently implemented.
- **Unknown:** use an empty path when identity or visibility is insufficient.
  Unknown is preferred over a guessed identity.
- Keep paths thin and centered. Masks, when supplied, should cover the visible
  line and not nearby texture. Mount and segmentation polygons should follow
  visible boundaries.
- Markings require a type, normalized supporting points, and confidence.
  Unclear marks should use an explicitly ambiguous project label.
- Do not horizontally flip images during augmentation: doing so changes
  handedness. The trainer uses photometric augmentation only.

## Privacy, consent, and licensing

Collect the minimum metadata needed. Use pseudonymous subject IDs; never put
names, emails, phone numbers, account IDs, or biometric templates in the
manifest. Record informed consent that explicitly covers annotation and model
training, the data source, and a license compatible with the intended use.
Honor withdrawal and retention policies. Do not add scraped, unlicensed, or
unknown-consent images. URI access control and deletion remain the dataset
owner's responsibility.

## Dataset commands

Run from `artifacts/api-server`:

```shell
python -m vedic.palm_scan.dataset_cli init dataset.json --dataset-id palms-v1
python -m vedic.palm_scan.dataset_cli add dataset.json sample.json --output dataset-added.json
python -m vedic.palm_scan.dataset_cli validate dataset-added.json
python -m vedic.palm_scan.dataset_cli validate dataset-added.json --assets --reject-remote
python -m vedic.palm_scan.dataset_cli split dataset-added.json dataset-split.json --seed 1337
python -m vedic.palm_scan.dataset_cli stats dataset-split.json
python -m vedic.palm_scan.dataset_cli rasterize dataset-split.json targets
python -m vedic.palm_scan.dataset_cli rasterize dataset-split.json targets-with-landmarks --landmark-heatmaps
```

Commands refuse destructive overwrites unless `--force` is provided. Prefer
`add --output` to create a new manifest; use `--force` only for an intentional
in-place update. Asset validation resolves all local paths beneath the explicit
`--asset-root` (default: manifest directory), checks existence and containment,
decodes dimensions, and verifies image/mask SHA-256 values. URLs are never
downloaded. Rasterization also requires an asset root whenever `mask_path` is
used and merges masks after binary nearest-neighbor resize.

Raster target order is fixed:

1. `heart_line`
2. `head_line`
3. `life_line`
4. `fate_line`
5. `sun_apollo_line`
6. `mercury_line`
7. `mars_support_line`
8. `hand_mask`
9. `palm_mask`

## Optional training

PyTorch is offline-only and is absent from core requirements:

```shell
pip install -r requirements-palm-training.txt
python -m vedic.palm_scan.training.train_semantic_lines dataset-split.json model-output --seed 1337
```

The small U-Net uses BCE plus Dice loss, deterministic seed controls,
subject-grouped manifest splits, label-safe photometric augmentation, per-class
IoU/Dice/precision/recall, held-out validation threshold calibration,
checkpoints, and ONNX export. Loss and metrics use per-class supervision:
`clear=1`, `faint=0.35` by default (configurable with `--faint-weight`), and
`unknown=occluded=0`. Unsupervised validation classes are excluded from
calibration and reported as `not_evaluated` with null metrics, never zero
accuracy. Training performs one mandatory local asset preflight before epochs
and rejects URI samples unless they have been materialized with a local path.

The ONNX sidecar records class order, input dimensions/color order,
normalization, preprocessing version, manifest hash, class weights,
supervision policy, thresholds/calibration, model version, and validation-only
metrics. Runtime rejects missing or incompatible metadata rather than silently
assuming preprocessing defaults, and cannot assign classes whose validation
calibration status is `not_evaluated`. `onnx` and `onnxscript` remain optional
training/export dependencies only. No model or weights are included, no
untrained model is enabled, and this repository makes no accuracy claim.

Production can explicitly instantiate
`OpenCVDNNSemanticLineVerifier`. It loads ONNX via OpenCV DNN and only emits a
named line when class probability, candidate overlap, scan quality, and
one-to-one uniqueness agree. It returns candidate IDs and confidence only;
line coordinates always remain those of the Phase 1 crease candidate. Missing,
incompatible, untrained, or unloadable models return no assignments.

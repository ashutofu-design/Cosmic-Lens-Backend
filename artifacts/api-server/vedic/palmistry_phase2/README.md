# Palm Analysis Engine Phase 2

Phase 2 is a deterministic, traditional-palmistry interpretation layer. It
accepts only the canonical `PalmScanResult` JSON emitted by Phase 1 schema
`1.0`. It never receives, loads, follows, or analyzes image bytes, image URLs,
or Phase 1 artifact references. Phase 1 and Phase 2 remain independently
replaceable.

## Request and response

`POST /api/palm-reading/interpret` accepts:

```json
{"palm_scan_result": {"schema_version": "1.0", "...": "..."}}
```

The endpoint rejects multipart and raw-image/file/artifact fields. Invalid
schema and valid-but-insufficient scans return HTTP 422 with structured
details. A default conservative Phase 1 result will often be insufficient:
unknown named lines and unknown mount development/elevation are intentionally
not reinterpreted from texture.

### Single-hand and bilateral modes

- `POST /api/palm-reading/interpret` is the quick single-hand route. Its output
  declares partial completeness and that bilateral comparison is unavailable.
- `POST /api/palm-reading/interpret-bilateral` accepts exact left and right
  `PalmScanResult/1.0` objects plus the user's explicit `writing_hand`.
- The dominant hand is labeled current/developed symbolism and the
  non-dominant hand baseline/underlying symbolism. These are traditional
  conventions, not scientific facts.
- Paired differences are emitted only when both measurements are independently
  readable and reliable. Each comparison preserves both raw values,
  confidences, threshold, direction, and evidence path.

Admission requires the complete canonical `PalmScanResult/1.0` boundary,
including every Phase 1 object/array section and all three image-reference
keys. References are type-checked as string/null but never fetched. The
following compatibility gates must all pass:

- `validation.status == accepted_measurements_only`
- `validation.quality_gate == passed`
- `quality.gate == passed` and `quality.usable == true`
- `scan_confidence.phase_2_eligible == true`
- `scan_confidence.phase_2_reason == eligible_measurement_only`
- scan confidence meets the configured reliable threshold

## Architecture

- `schema.py`: exact version and required-section boundary validation,
  including statuses, confidence ranges, ambiguity, union readability,
  markings, and conflicts.
- `rules.py`: versioned independent `Rule` records. Every record declares its
  domain/category, conditions, evidence paths, required confidence, polarity,
  weight, rule confidence, priority, and source tradition.
- `engine.py`: single-feature evaluation, confidence propagation,
  explainability traces, then per-category and per-domain fusion.
- `conflicts.py`: preserves positive, negative, supporting, and contradictory
  evidence, performs versioned cross-domain tension detection, and classifies
  results as strong, moderate, mixed, weak, or insufficient. It does not
  select only the maximum signal.
- `narrator.py`: replaceable structured-narrator protocol and deterministic
  grounded default. Narration runs only after analysis. A future LLM adapter
  must accept and validate only the structured analysis object.
- `api.py`: thin JSON-only Flask Blueprint.

Priority is major line > mount/hand/thumb/finger > minor marking. Scores use
`weight * priority_multiplier * propagated_confidence`; score metadata marks
them `internal_only`. Propagated confidence is the minimum of scan, feature,
and rule confidence, so Phase 2 cannot upgrade source confidence. Strong
classification requires confidence at least `0.75` and two independent feature
families. The reliable feature threshold defaults to `0.55`; both thresholds
are configurable.

Rules cover all seven named lines and all eight mounts, plus palm, finger,
fingertip shape, finger spacing, thumb proportions/angle, readable union-line,
major-line branch/fork/island observations, and supported marking
measurements. A rule fires only for an actually detected/readable, unambiguous
measurement that satisfies confidence and Phase 1 eligibility checks.
Detected named lines also require completed semantic verification, a valid
`source_candidate_id`, and a path identical to the referenced pixel-derived
crease candidate. Major domain conclusions are capped at `weak` when only one
independent feature family supports them.

Every configured personality, love/relationship, marriage, career, money,
recognition, and traditional-vitality subtopic is always present in the output.
Unsupported subtopics remain explicitly `insufficient_data`; no filler is
generated. Category and domain conclusions include confidence, classification,
rule IDs, and a feature → raw measurement → signal → confidence evidence
chain. Signed and normalized scores are internal-only.

The deterministic narrator returns these grounded sections: Overall Palm
Profile, Personality, Emotional & Relationship Nature, Love/Marriage, Career,
Money, Strengths, Challenges, Important Patterns, Traditional Palmistry
Guidance, and Confidence & Limitations. Evidentiary statements are copied only
from structured conclusions/signals. Empty sections remain empty.

## Provenance and limits

Interpretations are encoded as traditional palmistry conventions, not
scientific findings. Rule provenance is explicitly
`traditional_palmistry`; this package makes no empirical validation claim.
It does not diagnose health, estimate lifespan, promise wealth, or make
deterministic future or date claims. Union lines require an explicitly
readable outer-edge scan. Monocular texture is never treated as mount
development or elevation. Results are limited by Phase 1 image quality,
semantic detector support, and confidence calibration.

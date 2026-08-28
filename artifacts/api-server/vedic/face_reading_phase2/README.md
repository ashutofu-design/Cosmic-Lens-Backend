# Face Reading Phase 2

This package accepts `FaceScanResult/1.0` JSON and produces deterministic,
evidence-traced traditional face-reading associations. It never accepts or
reads an image, image URL, upload, or Phase 1 artifact.

## Pipeline

`FaceScanResult` → schema/admission validation → confidence-filtered feature
signals → explicit single/cross-feature rules → landmark-zone mapping →
priority-weighted conflict resolution → domain conclusions → grounded narrator.

The default endpoint is `POST /api/face-reading/interpret`:

```json
{
  "face_scan_result": {},
  "traditional_system": "indian_samudrik_v1"
}
```

`traditional_system` is optional. `GET /api/face-reading/systems` lists the
registered systems.

## Rule-system isolation

- `indian_samudrik_v1` (`indian.samudrik/1.0`)
- `chinese_mian_xiang_v1` (`chinese.mian_xiang/1.0`)

Exactly one system is evaluated per request. Rules carry the selected system
namespace in their IDs, and signals from different systems are never merged.
The rules are cautious cultural associations, not claims of scientific
validity.
The registry rejects namespace mismatches, duplicate IDs, unknown Phase 1
zones, unsafe claim language, and cross-feature rules that do not contain at
least two independent feature families. Categories without rules in the
selected system are explicitly marked `not_supported_by_ruleset`.

## Confidence and evidence

Rule confidence is
`min(scan confidence, every source-feature confidence, rule confidence)`.
Ambiguous, unknown, unsupported, or below-threshold measurements are skipped.
Structural rules have greater priority than supporting features, and verified
marking rules cannot override reliable structural evidence. Strong domain
conclusions require at least two independent feature families.

Every signal preserves:

- source feature and measurement paths
- raw measured value
- condition and threshold
- source, rule, scan, and propagated confidence
- separate container, candidate/item, and effective feature confidence
- priority, weight, domain/category, zone, system, and rule ID

## Safety and limitations

Narration consumes only resolved structured conclusions. It cannot inspect
Phase 1 data directly. Output is for reflective or entertainment use and must
not be used for medical, employment, financial, legal, relationship,
eligibility, or other consequential decisions. The engine does not infer
protected traits, morality, criminality, medical conditions, dates, life
events, or deterministic future outcomes.
All narrator implementations, including injected LLM adapters, are
post-validated against the fired rule IDs and allowed structured statements.

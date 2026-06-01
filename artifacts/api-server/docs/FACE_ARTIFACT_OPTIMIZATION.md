# Face Reading — Artifact-first PDF + token optimization

## Cache hierarchy

| Tier | Key | Bypasses |
|------|-----|----------|
| L1 | `face:session:{id}` + `_report_lang_cache` | Re-analyze |
| L2 | `face:analysis:{id}` | Engine re-run |
| L2b | `face:insights:canonical:{id}` | English Pass A |
| L2c | `face:insights:{id}:{lang}` | Per-lang Pass A / localize |
| L3 | `face:narration:{id}:{lang}` | **assemble_report + all AI** |
| L4 | `face:pdf:{id}:{lang}` + artifact extras | **Render + AI** |

## Target PDF flow

```
GET report.pdf
  → L4 valid?     → stream bytes (ZERO assemble/AI/render)
  → L3 valid?     → render_pdf only
  → else          → skeleton + budgeted Pass A/B → L3 → render → L4
```

## Version invalidation

| Bump | Effect |
|------|--------|
| `FACE_NARRATION_VERSION` | L3 + L2 insights stale |
| `FACE_PDF_RENDER_VERSION` | L4 stale, L3 kept (rerender only) |

## AI modes (`token_budget.py`)

- `full` — canonical EN Pass A + localize + Pass B (4o)
- `mini_only` — Pass A / localize, no 4o
- `localize_only` — EN canonical → mini rewrite for new language
- `template_only` — no OpenAI (caps / emergency / disabled)

## Cross-language

1. First report: Pass A in **English** → `face:insights:canonical:{analysis_id}`
2. Hindi/Hinglish: **localize** mini call only (~1 call vs full rebuild)
3. L3 narration cached per `analysis_id:lang`

## Regeneration rules

| Action | OpenAI | Render |
|--------|--------|--------|
| Re-download PDF | No | No (L4) |
| New language (cached EN) | Localize only | If no L4 |
| Rename cover (`?name=`) | No | Only if L3 exists, no L4 |
| `?rerender=1` | No | Yes (layout bump) |

## Modules

- `pdf_registry.py` — L4 artifact + checksum
- `token_budget.py` — tiers, caps, routing
- `token_analytics.py` — per-report / hotspot costs
- `artifact_pipeline.py` — orchestrates L4→L3→AI→render
- `narration_artifact.py` — canonical + localize
- `report_version.py` — version constants

## Fixes (2025-05)

- L3 render: `hydrate_report_for_render()` restores `engines` + appendix from payload / `face:analysis`
- Celery: `celery_worker_available()` pings workers; no 202 if worker down (sync fallback)
- Dedup L3: DB hit no longer re-runs `extract_landmarks`
- DB persist includes `front_points_norm` for face map on dedup
- Mobile: `X-User-Id` + `user_id` on analyze/PDF for token tiers

## Env

```bash
FACE_NARRATION_VERSION=face-v8-artifact
FACE_PDF_RENDER_VERSION=pdf-12block-v1
FACE_EMERGENCY_GLOBAL_CAP_USD=15
FACE_TIER_STANDARD_DAILY_USD=2
FACE_TIER_PRO_REPORT_USD=0.60
```

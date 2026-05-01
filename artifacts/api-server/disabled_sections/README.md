# Disabled LLM Context Sections

**Disabled on:** 2026-05-01
**Per:** User request

## What's in here

Archive copies of LLM-prompt sections that were **removed from the active prompt**
but kept in the codebase per the project's ADD-ONLY edit policy.

| File | Contains | Original location |
|------|----------|-------------------|
| `sections_10_to_13.py` | `_section_arudha`, `_section_ashtakavarga`, `_section_shadbala`, `_section_argala` | `kundli_full_context.py` L1223-L1541 |

## Why disabled

User wants these 4 sections (Arudha Padas, Ashtakavarga, Shadbala, Argala/Virodhargala)
**not** sent to the LLM in the whole-kundli context block. The function definitions
remain inside `kundli_full_context.py` (untouched) — only the **call sites** inside
`build_full_chart_context()` are gated behind a feature flag.

## How they're disabled (no code deletion)

In `kundli_full_context.py` → `build_full_chart_context()`, a flag wraps the 4
section calls:

```python
_SEND_SECTIONS_10_TO_13 = False
if _SEND_SECTIONS_10_TO_13:
    # ... 4 section append blocks ...
```

## Re-enable

Flip the flag back to `True`:

```python
_SEND_SECTIONS_10_TO_13 = True
```

Then restart the `artifacts/api-server: API Server` workflow.

## Note

The underlying engines (e.g. `ashtakavarga.py`, `argala.py`, `arudha`/jaimini code)
are **still actively used** by topic-specific engines like `marriage_engine.py`
(Phase 2.8.18 focus block uses SAV + Argala internally). Only the **whole-kundli
prompt sections** are disabled — engines still compute internally and inject
their results into topic-specific verdict blocks (e.g. AUTHORITATIVE MARRIAGE
VERDICT). This is intentional: locked numbers reach the LLM via verdict blocks,
not the generic chart dump.

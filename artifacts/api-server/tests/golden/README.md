# M11 — Golden Marriage Test Runner

Auto-tests for the marriage timing pipeline (`/api/ask` + translator_lock).
Validates that 5 baseline profiles continue to produce expected verdicts +
windows after any code change.

## Quick start

```bash
# 1. Make sure api-server workflow is running
# 2. Run all enabled profiles
python3 artifacts/api-server/tests/golden/run_golden_marriage.py

# Run only one profile
python3 artifacts/api-server/tests/golden/run_golden_marriage.py --only P40

# Use a different base URL (e.g. against deployed prod)
python3 artifacts/api-server/tests/golden/run_golden_marriage.py \
    --base https://your-app.replit.app
```

Exit code `0` = all PASS. `1` = at least one FAIL. `2` = setup error.

## Output statuses

| Status   | Meaning |
|----------|---------|
| **PASS** | All expected.* assertions matched |
| **FAIL** | One or more assertions failed (check the `└─ ...` lines) |
| **DRIFT** | HTTP 200 + translator_lock OK, but `verdict` keyword not detected in text — likely a real engine change worth manual review (NOT counted as failure) |
| **SKIP** | `enabled: false` in fixtures |

## What gets validated (per profile)

1. HTTP status code matches
2. `engine_tag == "ans-engine"` (proves translator_lock fired)
3. `translator_lock` field present in response
4. `path_used` in allowlist (e.g. `LLM_POLISHED` or `TEMPLATE`)
5. `severity` in allowlist (e.g. `OK`, `WARN`)
6. `llm_rejected` flag matches expected
7. Response text contains expected window keywords (e.g. "May", "2026")
8. Response text does NOT contain AI-tells (e.g. "I am an AI")
9. Verdict keyword detected in text (DRIFT signal, not a hard fail)

## Adding a new profile

Edit `profiles.json`:

```json
{
  "id": "P5",
  "enabled": true,
  "name": "<short label>",
  "note": "<expected verdict / context>",
  "birth_data": {
    "name": "...", "day": 1, "month": 1, "year": 1990,
    "hour": 12, "minute": 0, "ampm": "PM",
    "lat": 0.0, "lon": 0.0, "tz": 5.5,
    "gender": "M", "place": "..."
  },
  "question": "Meri shaadi kab hogi?",
  "lang": "hn",
  "expected": {
    "http_status": 200,
    "engine_tag": "ans-engine",
    "translator_lock_present": true,
    "path_used_in": ["LLM_POLISHED", "TEMPLATE"],
    "severity_in": ["OK", "WARN"],
    "llm_rejected": false,
    "text_must_contain_any": ["<window keyword>"],
    "text_must_not_contain": ["I am an AI", "as a language model"],
    "verdict": "PROMISED"
  }
}
```

## Current profile status

| ID  | Name | Enabled | Expected verdict | Notes |
|-----|------|---------|------------------|-------|
| P40 | Rajalaxmi | ✅ | PROMISED (May-Jul 2026) | Locked baseline |
| P1  | TBD | ❌ | DENIED | Awaiting birth data |
| P2  | TBD | ❌ | DELAYED | Awaiting birth data |
| P3  | TBD | ❌ | DELAYED | Awaiting birth data |
| P4  | TBD | ❌ | PROMISED | Awaiting birth data |

To enable P1-P4, fill `birth_data` + flip `enabled: true` in `profiles.json`.

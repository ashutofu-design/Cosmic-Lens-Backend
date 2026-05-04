#!/usr/bin/env python3
"""
Golden Marriage Test Runner — M11 (Phase 2.10.5 STEP 7C).

Runs each enabled profile in `profiles.json` against the live `/api/ask`
endpoint and validates the response against `expected.*` assertions.

Usage:
    python3 artifacts/api-server/tests/golden/run_golden_marriage.py
    python3 artifacts/api-server/tests/golden/run_golden_marriage.py --only P40
    python3 artifacts/api-server/tests/golden/run_golden_marriage.py --base http://localhost:80

Exit codes:
    0  — all enabled profiles PASSED
    1  — at least one FAILED
    2  — runner setup error (network, missing fixtures, etc.)

Output: color-coded report. PASS / FAIL / SKIP / DRIFT per profile.
DRIFT = HTTP 200 + translator_lock present, but `verdict` or window
keywords differ from baseline (likely a real engine change worth review).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import urllib.request
import urllib.error

# Make api-server modules importable so we can pre-compute `kundli` from
# `birth_data`. The /api/ask route expects a pre-computed `kundli` field
# (mobile client computes it locally before sending). Without it, the
# route-level gate refuses with "kundli nahi hai".
_API_SERVER_DIR = Path(__file__).resolve().parents[2]
if str(_API_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(_API_SERVER_DIR))

try:
    import io as _io
    import contextlib as _contextlib
    from kundli_engine import calculate_kundli as _calculate_kundli  # type: ignore
except Exception as _e:  # noqa: BLE001
    _calculate_kundli = None
    _kundli_import_err = str(_e)
else:
    _kundli_import_err = ""


def _compute_kundli(birth: dict) -> dict | None:
    """Build kundli from birth dict; suppress engine stdout chatter."""
    if _calculate_kundli is None:
        return None
    try:
        with _contextlib.redirect_stdout(_io.StringIO()):
            return _calculate_kundli(birth)
    except Exception:
        return None

# ─────────────────────────────────────────────────────────────────────────────
# ANSI colors (works on macOS / Linux / Replit terminal)
# ─────────────────────────────────────────────────────────────────────────────
_C_GREEN  = "\033[32m"
_C_RED    = "\033[31m"
_C_YELLOW = "\033[33m"
_C_BLUE   = "\033[34m"
_C_DIM    = "\033[2m"
_C_BOLD   = "\033[1m"
_C_RESET  = "\033[0m"

if not sys.stdout.isatty():  # plain text when piped
    _C_GREEN = _C_RED = _C_YELLOW = _C_BLUE = _C_DIM = _C_BOLD = _C_RESET = ""


def _c(color: str, text: str) -> str:
    return f"{color}{text}{_C_RESET}"


# ─────────────────────────────────────────────────────────────────────────────
# HTTP helpers
# ─────────────────────────────────────────────────────────────────────────────
def _post_ask(base_url: str, payload: dict, timeout: float = 90.0) -> tuple[int, dict | None, str]:
    """Returns (http_status, response_json_or_None, error_message_or_empty)."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url     = f"{base_url.rstrip('/')}/api/ask",
        data    = body,
        method  = "POST",
        headers = {"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            raw    = resp.read().decode("utf-8")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                return status, None, f"non-JSON response: {e}"
            return status, data, ""
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        return e.code, None, f"HTTP {e.code}: {err_body[:200]}"
    except urllib.error.URLError as e:
        return 0, None, f"network error: {e.reason}"
    except TimeoutError:
        return 0, None, "request timed out"


# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────
def _validate_response(resp: dict, expected: dict) -> tuple[bool, list[str]]:
    """Returns (passed, [list_of_failure_messages])."""
    failures: list[str] = []

    # 1. engine_tag
    exp_tag = expected.get("engine_tag")
    if exp_tag is not None:
        actual_tag = resp.get("engine_tag")
        if actual_tag != exp_tag:
            failures.append(f"engine_tag: expected {exp_tag!r}, got {actual_tag!r}")

    # 2. translator_lock present
    if expected.get("translator_lock_present"):
        if not isinstance(resp.get("translator_lock"), dict):
            failures.append("translator_lock: missing or not a dict")

    tlock = resp.get("translator_lock") or {}

    # 3. path_used in allowlist
    allowed_paths = expected.get("path_used_in")
    if allowed_paths:
        actual_path = tlock.get("path_used")
        if actual_path not in allowed_paths:
            failures.append(f"path_used: expected one of {allowed_paths}, got {actual_path!r}")

    # 4. severity in allowlist
    allowed_sev = expected.get("severity_in")
    if allowed_sev:
        actual_sev = tlock.get("severity")
        if actual_sev not in allowed_sev:
            failures.append(f"severity: expected one of {allowed_sev}, got {actual_sev!r}")

    # 5. llm_rejected explicit check
    if "llm_rejected" in expected:
        actual_rej = tlock.get("llm_rejected")
        if actual_rej != expected["llm_rejected"]:
            failures.append(f"llm_rejected: expected {expected['llm_rejected']}, got {actual_rej}")

    # 6. text contains ANY of the keywords (window markers)
    text = (resp.get("text") or "").lower()
    must_any = expected.get("text_must_contain_any") or []
    if must_any:
        hits = [k for k in must_any if k.lower() in text]
        if not hits:
            failures.append(f"text_must_contain_any: none of {must_any} found")

    # 7. text must NOT contain forbidden phrases (AI-tells)
    must_not = expected.get("text_must_not_contain") or []
    for phrase in must_not:
        if phrase.lower() in text:
            failures.append(f"text_must_not_contain: forbidden phrase {phrase!r} present")

    # 8. verdict (DRIFT-class — non-fatal but flagged)
    # Verdict is logged informationally; counted as DRIFT not FAIL when
    # everything else passes but verdict differs.
    return (len(failures) == 0, failures)


def _check_drift(resp: dict, expected: dict) -> str | None:
    """Returns drift message if verdict differs from expected, else None.
    Verdict isn't always exposed in the response envelope — best-effort."""
    exp_verdict = expected.get("verdict")
    if not exp_verdict:
        return None
    text = (resp.get("text") or "").upper()
    # Heuristic: look for verdict keyword in response text. Hinglish-aware
    # patterns (engine output uses "promised window", "yog active",
    # "vilamb", etc. organically — match generously, this is a soft signal).
    verdict_keywords = {
        "PROMISED": ["PROMISED", "PROMISE", "STRONG YOG", "YOG ACTIVE",
                     "SHAADI KA YOG", "WINDOW KHULI", "WINDOW OPEN"],
        "DELAYED":  ["DELAY", "DELAYED", "VILAMB", "DERI"],
        "DENIED":   ["DENIED", "DENY", "NO STRONG", "WEAK YOG", "ANUPLABDH"],
    }
    expected_kws = verdict_keywords.get(exp_verdict.upper(), [exp_verdict.upper()])
    if not any(kw in text for kw in expected_kws):
        return f"verdict={exp_verdict!r} not detected in text (no keywords matched)"
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────
def _run_profile(base_url: str, profile: dict) -> dict:
    """Returns result dict: {id, status, duration_s, failures, drift, response_summary}."""
    pid     = profile["id"]
    birth   = profile["birth_data"]
    kundli  = _compute_kundli(birth)
    if kundli is None:
        return {
            "id": pid, "name": profile.get("name", ""),
            "duration": 0.0, "status": "FAIL",
            "failures": [f"kundli compute failed (import err: {_kundli_import_err or 'see logs'})"],
            "drift": None, "summary": {},
        }
    payload = {
        "question":  profile["question"],
        "kundli":    kundli,
        "birthData": birth,
        "lang":      profile.get("lang", "hn"),
    }
    t0 = time.time()
    status, resp, err = _post_ask(base_url, payload)
    dt = time.time() - t0

    result: dict[str, Any] = {
        "id":        pid,
        "name":      profile.get("name", ""),
        "duration":  dt,
        "status":    "FAIL",
        "failures":  [],
        "drift":     None,
        "summary":   {},
    }

    # HTTP status check first
    exp_status = profile.get("expected", {}).get("http_status", 200)
    if status != exp_status:
        result["failures"].append(f"http_status: expected {exp_status}, got {status} ({err})")
        return result
    if resp is None:
        result["failures"].append(f"empty response body ({err})")
        return result

    # Capture summary for report
    tlock = resp.get("translator_lock") or {}
    result["summary"] = {
        "engine_tag":   resp.get("engine_tag"),
        "source":       resp.get("source"),
        "text_chars":   len(resp.get("text") or ""),
        "path_used":    tlock.get("path_used"),
        "severity":     tlock.get("severity"),
        "llm_rejected": tlock.get("llm_rejected"),
    }

    passed, failures = _validate_response(resp, profile.get("expected", {}))
    drift_msg = _check_drift(resp, profile.get("expected", {}))

    if not passed:
        result["status"]   = "FAIL"
        result["failures"] = failures
    elif drift_msg:
        result["status"] = "DRIFT"
        result["drift"]  = drift_msg
    else:
        result["status"] = "PASS"

    if drift_msg and passed:
        result["drift"] = drift_msg

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Golden marriage test runner")
    parser.add_argument("--base", default=os.environ.get("GOLDEN_BASE_URL", "http://localhost:80"),
                        help="API base URL (default: http://localhost:80)")
    parser.add_argument("--only", default=None, help="Run only the given profile ID (e.g. P40)")
    parser.add_argument("--fixtures", default=None,
                        help="Path to profiles.json (default: alongside this script)")
    args = parser.parse_args()

    fixtures_path = Path(args.fixtures) if args.fixtures else Path(__file__).parent / "profiles.json"
    if not fixtures_path.exists():
        print(_c(_C_RED, f"FATAL: fixtures file not found: {fixtures_path}"))
        return 2

    try:
        fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(_c(_C_RED, f"FATAL: failed to parse fixtures: {e}"))
        return 2

    profiles = fixtures.get("profiles", [])
    if args.only:
        profiles = [p for p in profiles if p.get("id") == args.only]
        if not profiles:
            print(_c(_C_RED, f"FATAL: no profile with id {args.only!r}"))
            return 2

    print(_c(_C_BOLD, f"\n=== M11 Golden Marriage Test ==="))
    print(_c(_C_DIM, f"Base URL : {args.base}"))
    print(_c(_C_DIM, f"Fixtures : {fixtures_path}"))
    print(_c(_C_DIM, f"Profiles : {len(profiles)} loaded "
                     f"({sum(1 for p in profiles if p.get('enabled', True))} enabled)\n"))

    results: list[dict] = []
    for p in profiles:
        if not p.get("enabled", True):
            print(f"  {_c(_C_DIM, '[SKIP]')} {p['id']:<6} {p.get('name','')}  "
                  f"{_c(_C_DIM, '(disabled in fixtures)')}")
            results.append({"id": p["id"], "status": "SKIP"})
            continue

        print(f"  [....] {p['id']:<6} {p.get('name',''):<24}", end="", flush=True)
        r = _run_profile(args.base, p)
        results.append(r)

        # Re-print line with final status
        sys.stdout.write("\r")
        if r["status"] == "PASS":
            tag = _c(_C_GREEN, "[PASS]")
        elif r["status"] == "DRIFT":
            tag = _c(_C_YELLOW, "[DRIFT]")
        elif r["status"] == "FAIL":
            tag = _c(_C_RED, "[FAIL]")
        else:
            tag = _c(_C_DIM, "[----]")

        s = r.get("summary", {})
        meta = (f"engine={s.get('engine_tag','?')} "
                f"path={s.get('path_used','?')} "
                f"sev={s.get('severity','?')} "
                f"chars={s.get('text_chars','?')} "
                f"{r['duration']:.1f}s")
        print(f"  {tag} {p['id']:<6} {p.get('name',''):<24} {_c(_C_DIM, meta)}")

        if r["status"] == "FAIL":
            for f in r["failures"]:
                print(f"         {_c(_C_RED, '└─ '+f)}")
        elif r["status"] == "DRIFT":
            print(f"         {_c(_C_YELLOW, '└─ '+r['drift'])}")

    # ── Summary ─────────────────────────────────────────────────────────────
    n_pass  = sum(1 for r in results if r["status"] == "PASS")
    n_fail  = sum(1 for r in results if r["status"] == "FAIL")
    n_drift = sum(1 for r in results if r["status"] == "DRIFT")
    n_skip  = sum(1 for r in results if r["status"] == "SKIP")
    n_total = len(results)

    print()
    print(_c(_C_BOLD, "─── Summary ───"))
    line = (f"  {_c(_C_GREEN, str(n_pass)+' PASS')}  "
            f"{_c(_C_YELLOW, str(n_drift)+' DRIFT')}  "
            f"{_c(_C_RED, str(n_fail)+' FAIL')}  "
            f"{_c(_C_DIM, str(n_skip)+' SKIP')}  "
            f"({n_total} total)")
    print(line)
    print()

    return 1 if n_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Audit 100 spiritual questions — routing, engine, dasha/KP output."""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from event_timing.timing_router import detect_timing_intent, resolve_timing_domain, run_timing_engine
from scripts.spiritual_100_cases import ALL_CASES

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "ascendantDeg": 255.0,
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7, "longitude": 75.0},
        {"name": "Saturn", "sign": "Virgo", "house": 10, "longitude": 165.0},
        {"name": "Mars", "sign": "Cancer", "house": 8, "longitude": 105.0},
        {"name": "Venus", "sign": "Leo", "house": 9, "longitude": 135.0},
        {"name": "Mercury", "sign": "Aries", "house": 5, "longitude": 15.0},
        {"name": "Jupiter", "sign": "Pisces", "house": 4, "longitude": 345.0},
        {"name": "Rahu", "sign": "Aquarius", "house": 3, "longitude": 315.0},
        {"name": "Ketu", "sign": "Leo", "house": 9, "longitude": 135.0},
        {"name": "Sun", "sign": "Capricorn", "house": 2, "longitude": 285.0},
    ],
    "dashas": [
        {
            "lord": "Jupiter",
            "start": "2024-01-01",
            "end": "2040-12-31",
            "subDashas": [
                {
                    "lord": "Ketu",
                    "start": "2025-01-01",
                    "end": "2027-12-31",
                    "subDashas": [
                        {"lord": "Mercury", "start": "2025-01-01", "end": "2025-07-01"},
                        {"lord": "Moon", "start": "2025-07-01", "end": "2026-01-01"},
                        {"lord": "Mars", "start": "2026-01-01", "end": "2026-07-01"},
                    ],
                },
            ],
        },
    ],
}

KP_SAMPLE = {
    "cusps": [
        {"house": 8, "subLord": "Ketu"},
        {"house": 9, "subLord": "Jupiter"},
        {"house": 12, "subLord": "Moon"},
    ],
}

_STATIC_KYA_RX = re.compile(
    r"(?ix)^kya\b(?!.*\b(kab|kab\s+tak|kis\s+(?:mahine|saal|year|month|date)|dasha\s+me|gochar|transit)\b)"
)

_TIMING_HINT_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+se|when|kis\s+(?:mahine|saal|year|month|date|turning\s+point)|"
    r"kis\s+dasha|dasha\s+me|gochar|transit|trigger|active|shuru\s+hoga|khatam|"
    r"milega|milegi|aayega|aayegi|banega|banegi|lagenge|prapt|approve"
    r")\b"
)


def _expect_kind(q: str) -> str:
    """timing | static | mixed (kya + kab in same Q)."""
    has_kya = bool(re.search(r"(?ix)\bkya\b", q))
    has_when = bool(_TIMING_HINT_RX.search(q))
    if has_kya and not has_when:
        return "static"
    if has_when:
        return "timing"
    return "static"


def _engine_ok(raw: dict) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if not raw.get("verdict") or raw.get("verdict") == "UNKNOWN":
        issues.append("no_verdict")
    cw = raw.get("current_window")
    if not cw:
        issues.append("no_current_window")
    else:
        if not cw.get("md") and not cw.get("ad"):
            issues.append("window_missing_dasha_lords")
        if not cw.get("start_iso") or not cw.get("end_iso"):
            issues.append("window_missing_dates")
    top3 = raw.get("next_3_windows") or []
    if not top3:
        issues.append("no_next_windows")
    kp = raw.get("kp_layer") or {}
    if not kp.get("cusps"):
        issues.append("no_kp_cusps")
    factors = " ".join(raw.get("factors") or [])
    if not any(x in factors for x in ("STEP1", "STEP5", "8L", "9L", "12L", "Ketu", "Jupiter")):
        issues.append("weak_house_factors")
    return (len(issues) == 0, issues)


def main() -> int:
    by_domain: Counter[str] = Counter()
    by_bucket: Counter[str] = Counter()
    by_category: dict[str, Counter[str]] = defaultdict(Counter)
    timing_vs_static = Counter()
    engine_issues: list[str] = []
    misroutes: list[str] = []
    static_as_timing: list[str] = []
    timing_missed: list[str] = []

    rows: list[dict] = []

    for i, (cat, exp_domain, q) in enumerate(ALL_CASES, 1):
        kind = _expect_kind(q)
        timing_vs_static[kind] += 1
        dom, bucket, is_t = resolve_timing_domain(q)
        det = detect_timing_intent(q)
        by_domain[dom] += 1
        by_bucket[bucket] += 1
        by_category[cat][dom] += 1

        eng_status = ""
        eng_verdict = ""
        eng_issues: list[str] = []
        if is_t:
            ctx = run_timing_engine(q, SAMPLE_KUNDLI, {}, KP_SAMPLE, None)
            eng_status = ctx.engine_status
            eng_verdict = str((ctx.raw or {}).get("verdict") or "")
            ok, eng_issues = _engine_ok(ctx.raw or {})

        if kind == "static" and is_t:
            static_as_timing.append(f"#{i} [{dom}] {q[:70]}")
        if kind == "timing" and not is_t:
            timing_missed.append(f"#{i} [{dom}] {q[:70]}")
        if kind == "timing" and is_t and dom != exp_domain:
            misroutes.append(f"#{i} want={exp_domain} got={dom} bucket={bucket} | {q[:65]}")
        if is_t and eng_issues:
            engine_issues.append(f"#{i} [{dom}] {eng_issues} | {q[:55]}")

        rows.append({
            "idx": i,
            "category": cat,
            "question": q,
            "expect_kind": kind,
            "domain": dom,
            "bucket": bucket,
            "is_timing": is_t,
            "detect_timing": det,
            "engine_status": eng_status,
            "verdict": eng_verdict,
            "engine_issues": eng_issues,
        })

    print(f"TOTAL={len(ALL_CASES)}")
    print(f"TIMING_VS_STATIC={dict(timing_vs_static)}")
    print(f"DOMAIN_COUNTS={dict(by_domain)}")
    print(f"BUCKET_COUNTS={dict(by_bucket)}")
    print(f"MISROUTES={len(misroutes)}")
    print(f"STATIC_FLAGGED_TIMING={len(static_as_timing)}")
    print(f"TIMING_MISSED={len(timing_missed)}")
    print(f"ENGINE_ISSUES={len(engine_issues)}")
    print("\n--- BY CATEGORY → DOMAIN ---")
    for cat, cnt in by_category.items():
        print(f"  {cat}: {dict(cnt)}")
    print("\n--- MISROUTES (timing Q, wrong domain) ---")
    for line in misroutes[:40]:
        print(line.encode("ascii", "replace").decode("ascii"))
    print("\n--- TIMING MISSED (kab Q not timing) ---")
    for line in timing_missed[:40]:
        print(line.encode("ascii", "replace").decode("ascii"))
    print("\n--- STATIC AS TIMING (kya-only) ---")
    for line in static_as_timing[:25]:
        print(line.encode("ascii", "replace").decode("ascii"))
    print("\n--- ENGINE ISSUES ---")
    for line in engine_issues[:20]:
        print(line.encode("ascii", "replace").decode("ascii"))

    out_path = os.path.join(os.path.dirname(__file__), "spiritual_100_audit.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"\nJSON={out_path}")

    gap_count = len(misroutes) + len(timing_missed)
    return 1 if gap_count else 0


if __name__ == "__main__":
    raise SystemExit(main())

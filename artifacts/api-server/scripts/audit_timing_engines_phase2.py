#!/usr/bin/env python3
"""Phase 2 timing engine audit — property/education/litigation/love + router wiring."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from event_timing.domain_specs import list_domains_by_status
from event_timing.timing_router import format_timing_block, resolve_timing_domain, run_timing_engine

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
                    "lord": "Venus",
                    "start": "2025-01-01",
                    "end": "2027-12-31",
                    "subDashas": [
                        {"lord": "Mercury", "start": "2025-01-01", "end": "2025-07-01"},
                        {"lord": "Moon", "start": "2025-07-01", "end": "2026-01-01"},
                        {"lord": "Mars", "start": "2026-01-01", "end": "2026-07-01"},
                        {"lord": "Rahu", "start": "2026-07-01", "end": "2027-01-01"},
                    ],
                },
                {
                    "lord": "Sun",
                    "start": "2028-01-01",
                    "end": "2029-06-01",
                    "subDashas": [
                        {"lord": "Jupiter", "start": "2028-01-01", "end": "2028-07-01"},
                    ],
                },
            ],
        },
    ],
}

PHASE2_CASES: list[tuple[str, str, str]] = [
    ("Ghar kab lun?", "property", "PROPERTY TIMING ENGINE"),
    ("Registry kab hogi?", "property", "PROPERTY TIMING ENGINE"),
    ("Possession kab milegi?", "property", "PROPERTY TIMING ENGINE"),
    ("Exam result kab aayega?", "education", "EDUCATION TIMING ENGINE"),
    ("Admission kab hogi?", "education", "EDUCATION TIMING ENGINE"),
    ("Court case kab khatam hoga?", "litigation", "LITIGATION TIMING ENGINE"),
    ("Bail kab milegi?", "litigation", "LITIGATION TIMING ENGINE"),
    ("Patchup kab hoga?", "love", "LOVE TIMING ENGINE"),
    ("Pyaar kab milega?", "love", "LOVE TIMING ENGINE"),
]

WIRED_CASES: list[tuple[str, str, str, dict | None]] = [
    ("Bachcha kab hoga?", "children", "CHILDREN TIMING ENGINE", None),
    (
        "Health recovery kab hogi?",
        "health",
        "HEALTH TIMING ENGINE",
        {"domain": "health", "is_timing": True},
    ),
    (
        "Paisa kab aayega?",
        "finance",
        "FINANCE TIMING ENGINE",
        {"domain": "finance", "is_timing": True},
    ),
]


def main() -> int:
    gaps: list[str] = []
    all_cases = PHASE2_CASES + WIRED_CASES

    for i, item in enumerate(all_cases, 1):
        q, exp_dom, exp_marker = item[:3]
        llm_intent = item[3] if len(item) > 3 else None
        dom, _, is_t = resolve_timing_domain(q, llm_intent)
        if not is_t:
            gaps.append(f"#{i} NOT_TIMING {q!r}")
            continue
        if dom != exp_dom:
            gaps.append(f"#{i} DOMAIN {q!r} want={exp_dom} got={dom}")
            continue

        ctx = run_timing_engine(q, SAMPLE_KUNDLI, {}, {}, None, llm_intent or {"is_timing": True})
        if ctx.engine_status != "ready":
            gaps.append(
                f"#{i} STATUS {q!r} want=ready got={ctx.engine_status} "
                f"factors={ctx.factors[:2]}"
            )
            continue

        block = format_timing_block(ctx)
        if exp_marker not in block:
            gaps.append(f"#{i} BLOCK {q!r} missing marker {exp_marker!r}")
        if not ctx.verdict or ctx.verdict == "UNKNOWN":
            gaps.append(f"#{i} VERDICT {q!r} empty/unknown verdict={ctx.verdict!r}")

    partial = list_domains_by_status("partial")
    if partial:
        gaps.append(f"PARTIAL_ENGINES remain: {partial}")

    print(f"TOTAL={len(all_cases)} GAPS={len(gaps)}")
    print(f"ENGINES_READY={list_domains_by_status('ready')}")
    for g in gaps[:40]:
        print(g.encode("ascii", "replace").decode("ascii"))
    return 1 if gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())

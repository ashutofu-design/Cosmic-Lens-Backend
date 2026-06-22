#!/usr/bin/env python3
"""Phase 3 bulk timing audit — cross-domain routing + engine harness (~12k bank).

Usage:
  python scripts/audit_timing_bulk_phase3.py              # routing only, full bank
  python scripts/audit_timing_bulk_phase3.py --quick      # first 500 cases
  python scripts/audit_timing_bulk_phase3.py --engine     # also run timing engines
  python scripts/audit_timing_bulk_phase3.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from event_timing.domain_specs import list_domains_by_status
from event_timing.timing_router import (
    detect_timing_intent,
    format_timing_block,
    resolve_timing_domain,
    run_timing_engine,
)
from scripts.timing_question_bank import BankCase, bank_stats, generate_timing_bank

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
            ],
        },
    ],
}

ENGINE_MARKERS: dict[str, tuple[str, ...]] = {
    "property": ("PROPERTY TIMING ENGINE",),
    "education": ("EDUCATION TIMING ENGINE",),
    "litigation": ("LITIGATION TIMING ENGINE",),
    "love": ("LOVE TIMING ENGINE",),
    "travel": ("TRAVEL TIMING ENGINE",),
    "finance": ("FINANCE TIMING ENGINE",),
    "health": ("HEALTH TIMING ENGINE",),
    "children": ("CHILDREN TIMING ENGINE",),
    "career": ("CAREER", "verdict", "Verdict"),
    "marriage": ("TIMING SPEC (MARRIAGE)", "marriage uses dedicated"),
}

# Marriage/career use dedicated openai_helper paths; engine audit is lighter
ENGINE_SKIP_VERDICT: set[str] = {"marriage"}


@dataclass
class Gap:
    idx: int
    question: str
    gap_type: str
    detail: str
    expect_domain: str = ""
    got_domain: str = ""


@dataclass
class AuditReport:
    total: int = 0
    gaps: list[Gap] = field(default_factory=list)
    routing_pass: int = 0
    engine_pass: int = 0
    engine_skipped: int = 0
    by_gap_type: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_domain: dict[str, dict[str, int]] = field(default_factory=lambda: defaultdict(dict))


def _safe(s: str) -> str:
    return s.encode("ascii", "replace").decode("ascii")


def audit_case(
    idx: int,
    case: BankCase,
    *,
    run_engine: bool,
) -> list[Gap]:
    gaps: list[Gap] = []
    q = case.question
    intent = case.llm_intent

    got_timing = detect_timing_intent(q, intent)
    got_dom, _, router_timing = resolve_timing_domain(q, intent)

    if router_timing != case.expect_timing:
        gaps.append(Gap(
            idx, q, "TIMING",
            f"want={case.expect_timing} router={router_timing} detect={got_timing}",
            case.expect_domain, got_dom,
        ))

    if case.expect_timing and got_dom != case.expect_domain:
        gaps.append(Gap(
            idx, q, "DOMAIN",
            f"want={case.expect_domain} got={got_dom}",
            case.expect_domain, got_dom,
        ))

    if not case.expect_timing and got_timing and got_dom not in ("general", case.expect_domain):
        if case.expect_domain == "general" and got_dom != "general":
            gaps.append(Gap(
                idx, q, "STATIC_LEAK",
                f"static Q routed to {got_dom}",
                "general", got_dom,
            ))

    if not run_engine or not case.expect_timing:
        return gaps

    ctx = run_timing_engine(q, SAMPLE_KUNDLI, {}, {}, None, intent or {"is_timing": True})
    dom = case.expect_domain

    if ctx.engine_status not in ("ready", "skipped_non_timing"):
        gaps.append(Gap(
            idx, q, "ENGINE_STATUS",
            f"status={ctx.engine_status} factors={ctx.factors[:2]}",
            dom, got_dom,
        ))
        return gaps

    block = format_timing_block(ctx)
    markers = ENGINE_MARKERS.get(dom, ())
    if markers and not any(m in block for m in markers):
        gaps.append(Gap(
            idx, q, "ENGINE_BLOCK",
            f"missing marker in block (len={len(block)})",
            dom, got_dom,
        ))

    if dom not in ENGINE_SKIP_VERDICT:
        if not ctx.verdict or ctx.verdict == "UNKNOWN":
            gaps.append(Gap(
                idx, q, "ENGINE_VERDICT",
                f"verdict={ctx.verdict!r}",
                dom, got_dom,
            ))

    return gaps


def run_audit(
    cases: list[BankCase],
    *,
    run_engine: bool = False,
    limit: Optional[int] = None,
) -> AuditReport:
    report = AuditReport()
    subset = cases[:limit] if limit else cases
    report.total = len(subset)

    for i, case in enumerate(subset, 1):
        case_gaps = audit_case(i, case, run_engine=run_engine)
        if not case_gaps:
            report.routing_pass += 1
            if case.expect_timing and run_engine:
                report.engine_pass += 1
            elif case.expect_timing and not run_engine:
                report.engine_skipped += 1
        for g in case_gaps:
            report.gaps.append(g)
            report.by_gap_type[g.gap_type] += 1
            dom = case.expect_domain
            if dom not in report.by_domain:
                report.by_domain[dom] = {"total": 0, "gaps": 0}
            report.by_domain[dom]["gaps"] = report.by_domain[dom].get("gaps", 0) + 1

        dom = case.expect_domain
        if dom not in report.by_domain:
            report.by_domain[dom] = {"total": 0, "gaps": 0}
        report.by_domain[dom]["total"] = report.by_domain[dom].get("total", 0) + 1

    return report


def print_report(report: AuditReport, *, run_engine: bool) -> None:
    print(f"TOTAL={report.total} GAPS={len(report.gaps)}")
    print(f"ROUTING_PASS={report.routing_pass}")
    if run_engine:
        print(f"ENGINE_PASS={report.engine_pass}")
    else:
        print(f"ENGINE_SKIPPED={report.engine_skipped} (use --engine to run)")
    print(f"GAP_TYPES={dict(report.by_gap_type)}")
    print(f"ENGINES_READY={list_domains_by_status('ready')}")
    for g in report.gaps[:50]:
        print(_safe(f"#{g.idx} [{g.gap_type}] {g.question!r} — {g.detail}"))
    if len(report.gaps) > 50:
        print(f"... and {len(report.gaps) - 50} more gaps")


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3 bulk timing audit")
    parser.add_argument("--quick", action="store_true", help="First 500 cases only")
    parser.add_argument("--limit", type=int, default=0, help="Cap case count")
    parser.add_argument("--engine", action="store_true", help="Run timing engines (slower)")
    parser.add_argument("--json", type=str, default="", help="Write JSON report path")
    args = parser.parse_args()

    bank = generate_timing_bank()
    st = bank_stats(bank)
    limit = 500 if args.quick else (args.limit or None)

    print(f"BANK_TOTAL={st['total']} TIMING={st['timing']} STATIC={st['static']}")
    print(f"BANK_BY_DOMAIN={st['by_domain']}")

    report = run_audit(bank, run_engine=args.engine, limit=limit)
    print_report(report, run_engine=args.engine)

    if args.json:
        payload = {
            "bank_stats": st,
            "total": report.total,
            "gaps": len(report.gaps),
            "gap_types": dict(report.by_gap_type),
            "by_domain": dict(report.by_domain),
            "sample_gaps": [asdict(g) for g in report.gaps[:200]],
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"WROTE {args.json}")

    return 1 if report.gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())

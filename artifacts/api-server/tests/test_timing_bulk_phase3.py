"""Phase 3 bulk timing audit — quick smoke tests."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.timing_question_bank import bank_stats, generate_timing_bank
from scripts.audit_timing_bulk_phase3 import run_audit


def test_bank_size_at_least_10k():
    bank = generate_timing_bank()
    st = bank_stats(bank)
    assert st["total"] >= 10000, f"bank too small: {st['total']}"
    assert st["timing"] >= 8000


def test_bank_covers_all_domains():
    bank = generate_timing_bank()
    st = bank_stats(bank)
    domains = st["by_domain"]
    for dom in (
        "marriage", "career", "travel", "property", "education",
        "litigation", "love", "children", "finance", "health",
    ):
        assert domains.get(dom, 0) >= 50, f"{dom} under-represented: {domains.get(dom)}"


def test_full_bank_routing_zero_gaps():
    bank = generate_timing_bank()
    report = run_audit(bank, run_engine=False)
    assert report.total == len(bank)
    assert len(report.gaps) == 0, f"sample gaps: {report.gaps[:5]}"


def test_engine_sample_zero_gaps():
    bank = generate_timing_bank()
    # Engine on first 60 timing-positive cases only (mixed domains)
    timing_cases = [c for c in bank if c.expect_timing][:60]
    report = run_audit(timing_cases, run_engine=True)
    assert len(report.gaps) == 0, report.gaps[:5]

"""100-question routing audit — foreign education / visa / PR / settlement."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_foreign_education import classify_foreign_education_bucket, is_foreign_education_timing_question
from event_timing.foreign_education_routing_audit import audit_question, classify_engine_family
from event_timing.timing_router import resolve_timing_domain
from tests.foreign_education_100_cases import QUESTIONS


@pytest.mark.parametrize("question,allowed,bucket", QUESTIONS)
def test_foreign_education_100_routing(
    question: str,
    allowed: frozenset[str],
    bucket: str,
) -> None:
    ok, got = audit_question(question, allowed)
    assert ok, f"Q routed to {got!r}, expected one of {sorted(allowed)}: {question[:80]}"
    if "foreign_education_timing" in allowed and classify_engine_family(question) == "foreign_education_timing":
        dom, bkt, is_timing = resolve_timing_domain(question)
        assert dom == "foreign_education"
        assert is_timing
        assert bkt == bucket


def test_foreign_education_100_coverage() -> None:
    assert len(QUESTIONS) == 100


def test_foreign_education_timing_hit_rate() -> None:
    fe_hits = sum(
        1 for q, _a, _b in QUESTIONS
        if classify_engine_family(q) == "foreign_education_timing"
    )
    assert fe_hits >= 72, f"only {fe_hits}/100 hit foreign_education_timing"


if __name__ == "__main__":
    passed = 0
    failed: list[str] = []
    for q, allowed, bucket in QUESTIONS:
        ok, got = audit_question(q, allowed)
        if ok:
            passed += 1
        else:
            failed.append(f"[{got}] {q[:70]}... (bucket={bucket})")
    fe = sum(1 for q, _, _ in QUESTIONS if classify_engine_family(q) == "foreign_education_timing")
    print(f"PASS {passed}/100 | foreign_education_timing={fe}/100")
    for line in failed:
        print("FAIL", line)

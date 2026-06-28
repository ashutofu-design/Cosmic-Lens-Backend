"""Audit 100 real-life property/vehicle questions — engine-family routing."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from event_timing.property.property_timing_v1 import classify_property_timing_bucket
from event_timing.property_routing_audit import classify_engine_family
from event_timing.timing_router import resolve_timing_domain
from event_timing.vehicle.vehicle_timing_v1 import classify_vehicle_timing_bucket
from property_100_cases import QUESTIONS


def _resolve_routing(question: str) -> tuple[str, str, str, bool, str | None]:
    """Return (engine_family, domain, router_bucket, is_timing, sub_bucket)."""
    dom, bucket, is_timing = resolve_timing_domain(question)
    family = classify_engine_family(question)
    sub_bucket: str | None = None
    if dom == "property" and is_timing:
        sub_bucket = classify_property_timing_bucket(question)
    elif dom == "vehicle" and is_timing:
        sub_bucket = classify_vehicle_timing_bucket(question)
    return family, dom, bucket, is_timing, sub_bucket


def test_property_100_engine_routing() -> None:
    passed = 0
    failures: list[dict[str, object]] = []

    for question, acceptable in QUESTIONS:
        family, dom, bucket, is_timing, sub_bucket = _resolve_routing(question)
        if family in acceptable:
            passed += 1
            continue
        failures.append(
            {
                "question": question,
                "got": family,
                "acceptable": sorted(acceptable),
                "domain": dom,
                "bucket": bucket,
                "sub_bucket": sub_bucket,
                "is_timing": is_timing,
            }
        )

    total = len(QUESTIONS)
    if failures:
        lines = [
            f"Property/vehicle routing audit: {passed}/{total} passed, {len(failures)} failed",
            "",
        ]
        for item in failures:
            lines.append(f"FAIL: {item['question'][:90]}")
            lines.append(
                f"  got={item['got']} acceptable={item['acceptable']} "
                f"domain={item['domain']} bucket={item['bucket']} "
                f"sub_bucket={item['sub_bucket']} is_timing={item['is_timing']}"
            )
        pytest.fail("\n".join(lines))

    assert passed == total

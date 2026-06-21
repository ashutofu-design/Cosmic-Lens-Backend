#!/usr/bin/env python3
"""Audit foundation health questions — routing coverage."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_health.classifier import classify_health_archetype, is_health_static_question

QUESTIONS = [
    ("Meri sehat kaisi hai?", "overall_vitality"),
    ("Overall health strong hai?", "overall_vitality"),
    ("Chronic issue ki tendency?", "chronic_tendency"),
    ("Long term bimari risk?", "chronic_tendency"),
    ("Stress anxiety tension?", "mental_stress"),
    ("Neend nahi aati insomnia?", "mental_stress"),
    ("Surgery risk high hai?", "surgery_risk_tone"),
    ("Operation safe hai?", "surgery_risk_tone"),
    ("Future health risk?", "preventive_risk"),
    ("Recovery capacity?", "recovery_capacity"),
    ("Accident risk?", "accident_risk"),
    ("Papa ki health?", "parent_health"),
    ("Addiction nasha?", "addiction_support"),
    ("Fertility conceive?", "reproductive_support"),
    ("Chart se bimari bata", "refuse_diagnosis"),
    ("Kab marunga?", "refuse_death"),
    ("Operation muhurat kab?", "refuse_surgery_muhurat"),
    ("Pet dard sehat?", "general_health"),
]


def main() -> int:
    ok = 0
    for q, expected in QUESTIONS:
        in_scope = is_health_static_question(q)
        arch = classify_health_archetype(q)
        if in_scope and arch == expected:
            ok += 1
            print(f"OK  {arch:22} {q[:50]}")
        else:
            print(f"FAIL expected={expected} got={arch} scope={in_scope}  {q[:50]}")
    total = len(QUESTIONS)
    print(f"\n{ok}/{total} OK")
    return 0 if ok == total else 1


if __name__ == "__main__":
    raise SystemExit(main())

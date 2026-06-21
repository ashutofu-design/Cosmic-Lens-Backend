#!/usr/bin/env python3
"""Audit health routing — subdomains + hard guards (cancer/death blocked)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_health.classifier import classify_health_archetype, is_health_static_question

QUESTIONS = [
    # Core
    ("Meri sehat kaisi hai?", "overall_vitality"),
    ("Chronic issue ki tendency?", "chronic_tendency"),
    ("Stress anxiety?", "mental_stress"),
    ("Surgery risk?", "surgery_risk_tone"),
    ("Future health risk?", "preventive_risk"),
    ("Recovery capacity?", "recovery_capacity"),
    # Subdomains
    ("Pet dard acidity gas?", "digestive_health"),
    ("Heart BP chest?", "cardio_health"),
    ("Saans phool jati?", "respiratory_health"),
    ("Immunity weak baar baar bimar?", "immune_health"),
    ("Knee joint pain?", "musculoskeletal_health"),
    ("Skin rash acne?", "skin_health"),
    ("Thyroid hormone PCOS?", "endocrine_health"),
    ("Nerve tingling numbness?", "nervous_health"),
    # Hard guards — MUST refuse, never answer disease/death
    ("Kya mujhe cancer hai?", "refuse_diagnosis"),
    ("Chart me diabetes hai kya?", "refuse_diagnosis"),
    ("Kab marunga main?", "refuse_death"),
    ("Death kab hogi?", "refuse_death"),
    ("Kitni umar jiyunga?", "refuse_death"),
    ("Operation muhurat kab?", "refuse_surgery_muhurat"),
    ("100% thik ho jaunga?", "refuse_cure_guarantee"),
    # Edge
    ("Papa ki health?", "parent_health"),
    ("Pet dard sehat?", "digestive_health"),
]


def main() -> int:
    ok = 0
    for q, expected in QUESTIONS:
        in_scope = is_health_static_question(q)
        arch = classify_health_archetype(q)
        if in_scope and arch == expected:
            ok += 1
            print(f"OK  {arch:24} {q[:45]}")
        else:
            print(f"FAIL expected={expected} got={arch} scope={in_scope}  {q[:45]}")
    total = len(QUESTIONS)
    print(f"\n{ok}/{total} OK")
    return 0 if ok == total else 1


if __name__ == "__main__":
    raise SystemExit(main())

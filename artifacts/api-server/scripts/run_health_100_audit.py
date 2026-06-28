#!/usr/bin/env python3
"""Run 100-question health routing audit — print breakdown."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.health_routing_audit import classify_health_routing, family_label
from tests.health_100_cases import QUESTIONS

if __name__ == "__main__":
    counts: Counter[str] = Counter()
    gaps: list[str] = []
    for i, (q, cat) in enumerate(QUESTIONS, 1):
        r = classify_health_routing(q)
        lab = family_label(r)
        counts[lab] += 1
        if r.get("family") in ("health_timing_gap", "llm", "health_llm"):
            gaps.append(f"Q{i:03d} [{lab}] ({cat}) {q[:65]}...")
    print(f"TOTAL={len(QUESTIONS)}")
    for k, v in counts.most_common():
        print(f"  {v:3d}  {k}")
    print(f"\nGAPS/LLM={len(gaps)}")
    for g in gaps:
        print(g)

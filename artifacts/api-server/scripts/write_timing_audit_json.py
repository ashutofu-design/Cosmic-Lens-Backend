#!/usr/bin/env python3
"""Write timing audit results to JSON (for CI / manual review)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ask_hard_guards import is_real_timing_engine_block
from event_timing.timing_router import detect_timing_intent, resolve_timing_domain, run_timing_engine

_K = {
    "ascendant": "Leo",
    "planets": [
        {"name": "Sun", "house": 1, "sign": "Leo"},
        {"name": "Moon", "house": 5, "sign": "Sagittarius"},
        {"name": "Mars", "house": 9, "sign": "Aries"},
        {"name": "Mercury", "house": 2, "sign": "Virgo"},
        {"name": "Jupiter", "house": 11, "sign": "Gemini"},
        {"name": "Venus", "house": 3, "sign": "Libra"},
        {"name": "Saturn", "house": 7, "sign": "Aquarius"},
        {"name": "Rahu", "house": 5, "sign": "Sagittarius"},
        {"name": "Ketu", "house": 11, "sign": "Gemini"},
    ],
    "dashas": [
        {
            "lord": "Sun",
            "start": "2020-01-01",
            "end": "2026-01-01",
            "subDashas": [
                {
                    "lord": "Moon",
                    "start": "2024-01-01",
                    "end": "2026-01-01",
                    "subDashas": [{"lord": "Mars", "start": "2025-01-01", "end": "2025-08-01"}],
                },
            ],
        },
    ],
}

CASES = [
    ("Shaadi kab hogi?", "marriage", True),
    ("Promotion kab milega?", "career", True),
    ("Mera content kab viral hoga?", "fame", True),
    ("Guru kab milega?", "spiritual", True),
    ("Bade log help kab karenge?", "network", True),
    ("Videsh kab jaunga?", "travel", True),
    ("Bail kab milegi?", "litigation", True),
    ("Lottery kab lagegi?", "universal", True),
    ("Pyaar kab milega?", "love", True),
    ("College admission kab hoga?", "education", True),
    ("Biwi kaisi hogi?", "general", False),
]

OUT = ROOT / "timing_audit_result.json"


def main() -> int:
    gaps = []
    rows = []
    for q, exp_dom, exp_t in CASES:
        dom, bucket, is_t = resolve_timing_domain(q)
        row = {"q": q, "exp_dom": exp_dom, "got_dom": dom, "bucket": bucket, "is_timing": is_t}
        if is_t != exp_t or (exp_t and dom != exp_dom):
            gaps.append(f"ROUTE {q!r} exp={exp_dom}/{exp_t} got={dom}/{is_t}")
        if is_t and dom != "marriage":
            ctx = run_timing_engine(q, _K, {}, {}, None)
            block = (ctx.raw or {}).get("_prompt_block") or ""
            row["engine"] = ctx.engine_status
            row["verdict"] = ctx.verdict
            row["block_ok"] = is_real_timing_engine_block(block)
            row["dual"] = bool((ctx.raw or {}).get("dual_track"))
            if not row["block_ok"]:
                gaps.append(f"BLOCK {q!r} domain={dom}")
        rows.append(row)

    # LLM mis-hint must not override registry
    dom, _, is_t = resolve_timing_domain(
        "Lottery kab lagegi?", {"domain": "finance", "is_timing": True},
    )
    if dom != "universal":
        gaps.append(f"LLM_OVERRIDE lottery got {dom}")

    OUT.write_text(json.dumps({"gaps": gaps, "rows": rows}, indent=2), encoding="utf-8")
    return 1 if gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())

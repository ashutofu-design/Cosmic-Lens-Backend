#!/usr/bin/env python3
"""Ask-section gap audit — routing, engine block, hard-guard acceptance."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_hard_guards import is_real_timing_engine_block, passthrough_missing_required_engine
from event_timing.timing_router import resolve_timing_domain, run_timing_engine

_K = {
    "ascendant": "Leo",
    "planets": [{"name": "Sun", "house": 1, "sign": "Leo"}, {"name": "Moon", "house": 5, "sign": "Sagittarius"},
               {"name": "Mars", "house": 9, "sign": "Aries"}, {"name": "Mercury", "house": 2, "sign": "Virgo"},
               {"name": "Jupiter", "house": 11, "sign": "Gemini"}, {"name": "Venus", "house": 3, "sign": "Libra"},
               {"name": "Saturn", "house": 7, "sign": "Aquarius"}, {"name": "Rahu", "house": 5, "sign": "Sagittarius"},
               {"name": "Ketu", "house": 11, "sign": "Gemini"}],
    "dashas": [{"lord": "Sun", "start": "2020-01-01", "end": "2026-01-01",
                "subDashas": [{"lord": "Moon", "start": "2024-01-01", "end": "2026-01-01",
                               "subDashas": [{"lord": "Mars", "start": "2025-01-01", "end": "2025-08-01"}]}]}],
}

QUESTIONS = [
    "Shaadi kab hogi?",
    "Promotion kab milega?",
    "Mera content kab viral hoga?",
    "Guru kab milega?",
    "Bade log help kab karenge?",
    "Videsh kab jaunga?",
    "Bail kab milegi?",
    "Lottery kab lagegi?",
    "Biwi kaisi hogi?",
    "College admission kab hoga?",
]


def main() -> int:
    gaps = []
    rows = []
    for q in QUESTIONS:
        dom, bucket, is_t = resolve_timing_domain(q)
        row = {"question": q, "domain": dom, "bucket": bucket, "is_timing": is_t}
        block = ""
        if is_t and dom != "marriage":
            ctx = run_timing_engine(q, _K, {}, {}, None)
            block = (ctx.raw or {}).get("_prompt_block") or ""
            row["engine_status"] = ctx.engine_status
            row["verdict"] = ctx.verdict
            row["block_ok"] = is_real_timing_engine_block(block)
            row["dual_track"] = bool((ctx.raw or {}).get("dual_track"))
            missing = passthrough_missing_required_engine(
                q, None,
                marriage_block="" if dom != "marriage" else "x",
                career_block="" if dom != "career" else "x",
                domain_timing_block=block,
                has_domain_engine=bool(block) and is_real_timing_engine_block(block),
            )
            row["missing_engine"] = missing
            if is_t and dom not in ("marriage", "career") and not row["block_ok"]:
                gaps.append(f"BLOCK_REJECTED {q} domain={dom}")
            if missing and missing not in ("no_domain_engine", None):
                gaps.append(f"MISSING {q} -> {missing}")
        rows.append(row)

    out = Path(__file__).resolve().parents[1] / "audit_ask_gaps_result.json"
    out.write_text(json.dumps({"gaps": gaps, "rows": rows}, indent=2), encoding="utf-8")
    print(f"GAPS={len(gaps)} written {out}")
    for g in gaps:
        print(g)
    for r in rows:
        print(
            f"{r['question'][:40]:40} dom={r['domain']:12} "
            f"t={r['is_timing']} block_ok={r.get('block_ok', '-')}"
        )
    return 1 if gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())

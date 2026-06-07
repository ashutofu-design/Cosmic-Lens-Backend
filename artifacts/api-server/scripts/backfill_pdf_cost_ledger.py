#!/usr/bin/env python3
"""Persist report-cache PDF rows into _pdf_cost_ledger.json (one-time on VPS)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pdf_generation_log import _load, _merge_report_cache_ledger, _save  # noqa: E402


def main() -> int:
    before = _load()
    merged = _merge_report_cache_ledger(before)
    added = [r for r in merged if r.get("source") == "report_cache_ledger"]
    if not added:
        print("OK: no missing rows — cost ledger already covers report cache.")
        return 0
    for row in added:
        row.pop("source", None)
    out = list(before)
    out.extend(added)
    out.sort(
        key=lambda r: r.get("generated_at") or "",
        reverse=True,
    )
    _save(out)
    print(f"OK: appended {len(added)} row(s) from report cache ledger.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

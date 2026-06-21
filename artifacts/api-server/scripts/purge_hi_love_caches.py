#!/usr/bin/env python3
"""Delete all saved Hindi Love Reality pro-report + polish snapshot files."""
from __future__ import annotations

import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import love_reality_polish_snapshot as snap
import love_reality_report_json_cache as jcache


def main() -> int:
    n_json = jcache.purge_all_hi_reports()
    n_snap = snap.purge_all_hi_snapshots()
    print(f"Purged Hindi caches: json={n_json} polish_snap={n_snap}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

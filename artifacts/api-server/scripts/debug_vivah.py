"""Debug vivah scan output for Panchang list."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vedic.panchang.marriage_muhurta import scan_vivah_muhurat

DELHI = {"lat": 28.6139, "lng": 77.2090, "tz_h": 5.5}
start = date.today()
r = scan_vivah_muhurat(start, days=180, **DELHI)

out = {
    "scan_from": r["scan_from"],
    "highly_count": r["highly_favorable_count"],
    "favorable_count": r["favorable_count"],
    "conditional_count": r["conditional_count"],
    "returned_highly": len(r["highly_favorable"]),
    "returned_favorable": len(r["favorable"]),
    "returned_conditional": len(r["conditional"]),
    "may_2026": [
        x["date"]
        for x in r["highly_favorable"] + r["favorable"] + r["conditional"]
        if x["date"].startswith(f"{start.year}-05") or x["date"].startswith("2026-05")
    ][:20],
    "sample": (r["highly_favorable"][:1] or r["favorable"][:1] or [{}])[0],
}
Path(ROOT / "scripts" / "debug_vivah_out.json").write_text(
    json.dumps(out, indent=2, default=str), encoding="utf-8"
)
print("wrote debug_vivah_out.json")

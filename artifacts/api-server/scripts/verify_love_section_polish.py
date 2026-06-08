#!/usr/bin/env python3
"""
Verify Love Reality Pro polish has all LLM sections before/after PDF render.

Usage (on VPS after deploy):
  cd artifacts/api-server
  python scripts/verify_love_section_polish.py              # list recent snapshots
  python scripts/verify_love_section_polish.py --latest     # check newest snapshot
  python scripts/verify_love_section_polish.py --path .cache/love_polish/<hash>.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_API = Path(__file__).resolve().parents[1]
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

_REQUIRED_CHAPTERS = ("breakup", "loyalty")
_MIN_WORDS = {
    "love_connection": 90,
    "breakup": 90,
    "loyalty": 90,
    "red_flags": 70,
}


def _wc(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text or ""))


def _chapter_body(pro: dict, key: str) -> str:
    for ch in pro.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        if str(ch.get("key") or "").lower() == key:
            return str(ch.get("chapter_body") or ch.get("full_read") or "").strip()
    return ""


def audit_pro(pro: dict) -> dict[str, dict]:
    from vedic.love_reality.love_section_polish import _assembly_depth_ok, _ASSEMBLY_VER

    rows: dict[str, dict] = {}
    rows["_assembly"] = {
        "ok": _assembly_depth_ok(pro),
        "version": (pro.get("_meta") or {}).get("assembly"),
        "expected": _ASSEMBLY_VER,
    }
    for key in ("verdict",):
        body = str(pro.get(key) or "")
        rows[key] = {"words": _wc(body), "ok": _wc(body) >= 80, "preview": body[:120]}
    da = pro.get("deep_analysis")
    rows["deep_analysis"] = {
        "ok": isinstance(da, list) and len(da) >= 4,
        "blocks": len(da) if isinstance(da, list) else 0,
    }
    br = str(pro.get("blueprint_reality") or _chapter_body(pro, "love_connection") or "")
    rows["blueprint_reality"] = {
        "words": _wc(br),
        "ok": _wc(br) >= _MIN_WORDS["love_connection"],
        "preview": br[:120] if br else "(EMPTY — Page 5 will be 1 engine line only)",
    }
    for ck in _REQUIRED_CHAPTERS:
        if ck == "love_connection":
            continue
        body = _chapter_body(pro, ck)
        need = _MIN_WORDS[ck]
        rows[ck] = {
            "words": _wc(body),
            "ok": _wc(body) >= need,
            "preview": body[:120] if body else "(EMPTY — PDF will show engine fallback)",
        }
    harm = str(pro.get("harmony") or _chapter_body(pro, "will_return") or "")
    rows["harmony"] = {"words": _wc(harm), "ok": _wc(harm) >= 90, "preview": harm[:120]}
    rf = str(pro.get("red_flags_narrative") or _chapter_body(pro, "red_flags") or "")
    rows["red_flags_narrative"] = {
        "words": _wc(rf),
        "ok": _wc(rf) >= _MIN_WORDS["red_flags"],
        "preview": rf[:120] if rf else "(EMPTY — Page 12 bullets only)",
    }
    dasha = str(pro.get("dasha_narrative") or "")
    rows["dasha_narrative"] = {
        "words": _wc(dasha),
        "ok": _wc(dasha) >= 60,
        "preview": dasha[:120] if dasha else "(EMPTY — Dasha page engine bullets only)",
    }
    road = str(pro.get("roadmap_narrative") or "")
    rows["roadmap_narrative"] = {
        "words": _wc(road),
        "ok": _wc(road) >= 70,
        "preview": road[:120] if road else "(EMPTY — Roadmap table only)",
    }
    return rows


def _print_audit(rows: dict[str, dict], label: str) -> bool:
    print(f"\n=== {label} ===")
    all_ok = True
    for name, row in rows.items():
        ok = row.get("ok", False)
        if not ok:
            all_ok = False
        mark = "OK" if ok else "MISSING"
        extra = ""
        if "words" in row:
            extra = f" ({row['words']} words)"
        if "blocks" in row:
            extra = f" ({row['blocks']} blocks)"
        if row.get("version"):
            extra = f" assembly={row.get('version')} expected={row.get('expected')}"
        print(f"  [{mark}] {name}{extra}")
        prev = row.get("preview")
        if prev and not ok:
            print(f"         -> {prev!r}")
    return all_ok


def _snap_dir() -> Path:
    return _API / ".cache" / "love_polish"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--latest", action="store_true", help="Audit newest snapshot JSON")
    ap.add_argument("--path", help="Explicit polish snapshot path")
    ap.add_argument("--pdf-pages", action="store_true", help="Map chapters to PDF page labels")
    args = ap.parse_args()

    if args.pdf_pages:
        print("PDF mapping (when chapters OK):")
        print("  love_connection  -> Page 5  Partner Blueprint vs Reality")
        print("  breakup          -> Page 8  Core Root Cause (only breakup after v2 fix)")
        print("  loyalty          -> Page 10 Loyalty & Trust")
        print("  red_flags        -> Page 12 Red Flags Matrix body")
        print("  harmony          -> Page 13 Harmony Formula")
        print("  dasha_narrative  -> Page 14 Dasha (prose) + engine bullet lines")
        print("  roadmap_narrative-> Page 15 Roadmap (prose) + engine score table")
        print()

    paths: list[Path] = []
    if args.path:
        paths = [Path(args.path)]
    elif args.latest:
        snaps = sorted(_snap_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not snaps:
            print("No polish snapshots in .cache/love_polish/")
            return 1
        paths = [snaps[0]]
    else:
        snaps = sorted(_snap_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
        if not snaps:
            print("No snapshots. Generate a Pro PDF first, then: --latest")
            return 1
        print("Recent polish snapshots:")
        for p in snaps:
            print(f"  {p.name}  ({p.stat().st_size} bytes)")
        print("\nRun with --latest to audit the newest file.")
        return 0

    ok_all = True
    for p in paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"Read failed {p}: {exc}")
            return 1
        if not isinstance(data, dict):
            print(f"Not a dict: {p}")
            return 1
        ok = _print_audit(audit_pro(data), str(p))
        ok_all = ok_all and ok

    if ok_all:
        print("\nPASS: All LLM sections present — PDF pages 5 & 12 will be full.")
        return 0
    print("\nFAIL: Some sections empty — Page 5 and/or Page 12 will stay thin until fixed.")
    print("Fix: rm .cache/love_polish/*.json, LOVE_REALITY_FORCE_LLM=1, regenerate PDF.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

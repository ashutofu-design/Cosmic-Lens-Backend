#!/usr/bin/env python3
"""
Hindi Love Reality Pro — section-by-section diagnostics (S4, S5, S7, S8, KPI, script).

VS Code / local:
  cd artifacts/api-server
  python scripts/diag_hi_love_sections.py

VPS (after git pull):
  cd /root/Cosmic-Lens-Backend/artifacts/api-server
  python3 scripts/diag_hi_love_sections.py
  python3 scripts/diag_hi_love_sections.py --json path/to/saved_report.json
  python3 scripts/diag_hi_love_sections.py --purge
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

_API = Path(__file__).resolve().parents[1]
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

try:
    from dotenv import load_dotenv

    load_dotenv(_API / ".env")
except Exception:
    pass

_DEVA = re.compile(r"[\u0900-\u097F]")


def _wc(text: str) -> int:
    return len((text or "").split())


def _deva(text: str) -> int:
    return len(_DEVA.findall(text or ""))


def _latest_json(dir_path: Path) -> Path | None:
    if not dir_path.is_dir():
        return None
    files = sorted(dir_path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _load_payload(path: Path | None) -> dict[str, Any] | None:
    if path:
        return json.loads(path.read_text(encoding="utf-8"))
    json_dir = _API / ".cache" / "love_report_json"
    if not json_dir.is_dir():
        return None
    files = sorted(json_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for rep in files:
        try:
            data = json.loads(rep.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        if str(data.get("lang") or "").lower() == "hi":
            print(f"  found Hindi cache: {rep.name}")
            return data
    if files:
        newest = files[0]
        lang = str(json.loads(newest.read_text(encoding="utf-8")).get("lang") or "").lower()
        print(f"  [WARN] no lang=hi cache — newest is {newest.name} lang={lang!r}")
        print("  -> App se Hindi report generate karo, phir script dubara chalao")
    return None


def _with_sections(payload: dict) -> dict:
    p1 = payload.get("page1")
    ctx = payload.get("pdf_context")
    pro = payload.get("pro_premium")
    if not isinstance(p1, dict) or not isinstance(ctx, dict):
        print("  [FAIL] page1/pdf_context missing — cannot rebuild app_sections")
        return {**payload, "content_script": "unknown"}
    try:
        from vedic.love_reality.app_report_sections import build_localized_app_sections

        sections, script, p1_out, ctx_out = build_localized_app_sections(
            p1, ctx, pro if isinstance(pro, dict) else {}, "hi",
        )
        return {
            **payload,
            "page1": p1_out,
            "pdf_context": ctx_out,
            "app_sections": sections,
            "content_script": script,
        }
    except Exception as exc:
        print(f"  [FAIL] build_localized_app_sections: {exc}")
        return {**payload, "content_script": "unknown"}


def _row(name: str, ok: bool, detail: str) -> dict[str, Any]:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}: {detail}")
    return {"name": name, "ok": ok, "detail": detail}


def _check_section4(payload: dict) -> dict[str, Any]:
    from vedic.love_reality.section4_gate import effective_section4_hi_text, section4_hi_load_gate
    from vedic.love_reality.love_section_polish import remedies_action_hi_ready

    pro = payload.get("pro_premium") if isinstance(payload.get("pro_premium"), dict) else {}
    text = effective_section4_hi_text(payload)
    gate_ok, reason = section4_hi_load_gate(payload)
    narr = str(pro.get("remedies_action_narrative") or "").strip()
    canon = str(payload.get("section4_hi_body") or "").strip()
    meta = (pro.get("_meta") or {}).get("section4_remedies") if isinstance(pro.get("_meta"), dict) else {}
    rows = [
        _row("S4 remedies_action_hi_ready", remedies_action_hi_ready(pro), f"narr_wc={_wc(narr)} narr_deva={_deva(narr)}"),
        _row("S4 section4_hi_body", bool(canon), f"wc={_wc(canon)} deva={_deva(canon)}"),
        _row("S4 effective text", _wc(text) >= 70 and _deva(text) >= 24, f"wc={_wc(text)} deva={_deva(text)}"),
        _row("S4 gate", gate_ok, reason or "ok"),
    ]
    if meta:
        print(f"         llm_meta: {meta}")
    if text:
        print(f"         preview: {text[:120]!r}...")
    return {"section": "section4_remedies", "rows": rows, "ok": all(r["ok"] for r in rows)}


def _check_section8(payload: dict) -> dict[str, Any]:
    from vedic.love_reality.section8_gate import effective_section8_hi_text, section8_hi_load_gate
    from vedic.love_reality.love_section_polish import breakup_chapter_hi_ready

    pro = payload.get("pro_premium") if isinstance(payload.get("pro_premium"), dict) else {}
    text = effective_section8_hi_text(payload)
    gate_ok, reason = section8_hi_load_gate(payload)
    meta = (pro.get("_meta") or {}).get("section8_breakup") if isinstance(pro.get("_meta"), dict) else {}
    rows = [
        _row("S8 breakup_chapter_hi_ready", breakup_chapter_hi_ready(pro), ""),
        _row("S8 effective text", _wc(text) >= 80 and _deva(text) >= 24, f"wc={_wc(text)} deva={_deva(text)}"),
        _row("S8 gate", gate_ok, reason or "ok"),
    ]
    if meta:
        print(f"         llm_meta: {meta}")
    dbg = payload.get("section8_debug")
    if dbg:
        print(f"         section8_debug: {dbg}")
    return {"section": "section8_root_cause", "rows": rows, "ok": all(r["ok"] for r in rows)}


def _check_other_llm(payload: dict) -> dict[str, Any]:
    from vedic.love_reality.love_section_polish import (
        blueprint_section_hi_ready,
        deep_analysis_hi_ready,
        moon_sync_narrative_hi_ready,
    )

    pro = payload.get("pro_premium") if isinstance(payload.get("pro_premium"), dict) else {}
    rows = [
        _row("S5 blueprint", blueprint_section_hi_ready(pro), ""),
        _row("S3 deep_analysis", deep_analysis_hi_ready(pro), ""),
        _row("S7 moon_sync", moon_sync_narrative_hi_ready(pro), ""),
    ]
    return {"section": "other_llm", "rows": rows, "ok": all(r["ok"] for r in rows)}


def _check_scorecard(payload: dict) -> dict[str, Any]:
    p1 = payload.get("page1") if isinstance(payload.get("page1"), dict) else {}
    lines: list[str] = []
    for sec in payload.get("app_sections") or []:
        if isinstance(sec, dict) and str(sec.get("id") or "").lower() == "scorecard":
            lines = [str(b).strip() for b in (sec.get("bullets") or []) if str(b).strip()]
            break
    if not lines:
        for row in p1.get("metrics") or []:
            if isinstance(row, dict):
                lines.append(f"{row.get('label')}: {row.get('value')}/100")
    ok = True
    for line in lines:
        label = str(line.split(":")[0] or "").strip()
        if not _deva(label):
            ok = False
            _row("KPI label", False, f"English label: {label!r}")
    if lines and ok:
        _row("KPI scorecard", True, f"{len(lines)} lines, all labels देवनागरी")
    elif not lines:
        _row("KPI scorecard", False, "no scorecard lines")
    return {"section": "scorecard", "ok": ok and bool(lines)}


def _check_script(payload: dict) -> dict[str, Any]:
    script = str(payload.get("content_script") or "unknown").strip().lower()
    ok = script == "hi"
    _row("content_script", ok, script)
    if script == "unknown":
        print("  -> app_sections build failed — check pm2 logs: love_reality_pro_report app_sections build failed")
    elif script == "hi_partial":
        print("  -> kuch sections abhi English — relocalize ya full LLM chahiye")
    return {"section": "content_script", "ok": ok, "script": script}


def _check_deploy() -> bool:
    print("\n=== STEP 0: Code on disk ===")
    api = (_API / "love_reality_api.py").read_text(encoding="utf-8")
    checks = {
        "_hi_script_block_response": "_hi_script_block_response" in api,
        "section4_gate.py": (_API / "vedic" / "love_reality" / "section4_gate.py").is_file(),
        "section8_gate.py": (_API / "vedic" / "love_reality" / "section8_gate.py").is_file(),
        "diag_hi_love_sections.py": (_API / "scripts" / "diag_hi_love_sections.py").is_file(),
    }
    ok = True
    for name, hit in checks.items():
        mark = "OK" if hit else "MISSING"
        if not hit:
            ok = False
        print(f"  [{mark}] {name}")
    return ok


def _purge() -> None:
    print("\n=== Purge Hindi caches ===")
    n_json = n_snap = 0
    try:
        import love_reality_report_json_cache as jcache

        n_json = jcache.purge_all_hi_reports()
    except Exception as exc:
        print(f"  json purge warn: {exc}")
    try:
        import love_reality_polish_snapshot as snap

        fn = getattr(snap, "purge_all_hi_snapshots", None)
        n_snap = int(fn()) if callable(fn) else 0
    except Exception as exc:
        print(f"  snap purge warn: {exc}")
    print(f"  purged json={n_json} snap={n_snap}")
    for pat in ("love_polish", "love_report_json"):
        d = _API / ".cache" / pat
        if not d.is_dir():
            continue
        removed = 0
        for f in d.glob("*.json"):
            try:
                f.unlink()
                removed += 1
            except OSError:
                pass
        print(f"  wiped {d}: {removed} json files")


def main() -> int:
    ap = argparse.ArgumentParser(description="Diagnose all Hindi Love Reality sections")
    ap.add_argument("--json", type=Path, help="Saved report JSON (from cache or API response)")
    ap.add_argument("--purge", action="store_true", help="Purge Hindi server caches")
    ap.add_argument("--no-rebuild", action="store_true", help="Skip _with_app_sections rebuild")
    args = ap.parse_args()

    print("Hindi Love Reality — full section diagnostics")
    print(f"API root: {_API}")

    deploy_ok = _check_deploy()
    if args.purge:
        _purge()

    print("\n=== STEP 1: Load payload ===")
    raw = _load_payload(args.json)
    if not raw:
        print("  [NONE] No Hindi report JSON — app se Hindi report generate karo, phir dubara run karo")
        print("  Or: curl/API se JSON save karke --json path pass karo")
        return 1
    src = args.json or _latest_json(_API / ".cache" / "love_report_json")
    print(f"  source: {src}")

    payload = raw if args.no_rebuild else _with_sections(raw)

    results = [
        _check_section4(payload),
        _check_section8(payload),
        _check_other_llm(payload),
        _check_scorecard(payload),
        _check_script(payload),
    ]

    print("\n=== SUMMARY ===")
    for block in results:
        mark = "PASS" if block.get("ok") else "FAIL"
        print(f"  [{mark}] {block.get('section')}")
    if not deploy_ok:
        print("  Deploy: git pull + pm2 restart cosmic-api")
    if all(b.get("ok") for b in results) and deploy_ok:
        print("All sections PASS — mobile app reload karke Hindi report kholo.")
        return 0
    print("FAILED sections upar dikhe — fix + purge + regenerate.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

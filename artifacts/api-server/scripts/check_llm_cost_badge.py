#!/usr/bin/env python3
"""Verify Love Reality English report LLM cost (INR) badge — run on VPS."""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

_API = Path(__file__).resolve().parents[1]
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))


def step_code() -> bool:
    print("\n=== 1) Code on disk ===")
    api = (_API / "love_reality_api.py").read_text(encoding="utf-8")
    polish = (_API / "vedic" / "love_reality" / "love_section_polish.py").read_text(encoding="utf-8")
    tel = (_API / "vedic" / "compat" / "openai_pdf_telemetry.py").read_text(encoding="utf-8")
    checks = {
        "_attach_llm_cost_inr": "_attach_llm_cost_inr" in api,
        "sum_llm_cost_inr_from_pro_meta": "sum_llm_cost_inr_from_pro_meta" in tel,
        "section acc.record": "acc.record(resp, scope)" in polish,
        "merge section pdf_generation": "merge_pdf_generation_into_meta" in polish,
    }
    ok = True
    for name, hit in checks.items():
        mark = "OK" if hit else "MISSING"
        if not hit:
            ok = False
        print(f"  [{mark}] {name}")
    return ok


def step_aggregate_math() -> bool:
    print("\n=== 2) Cost math (dry run) ===")
    from vedic.compat.openai_pdf_telemetry import sum_llm_cost_inr_from_pro_meta

    meta = {
        "sections": {
            "verdict_page": {"pdf_generation": {"estimated_cost_inr": 4.2}},
            "breakup": {"pdf_generation": {"estimated_cost_inr": 8.1}},
            "remedies_action": {"pdf_generation": {"estimated_cost_inr": 3.7}},
        }
    }
    total = sum_llm_cost_inr_from_pro_meta(meta)
    rounded = int(round(total))
    print(f"  sample sections sum: {total:.2f} INR -> UI shows: {rounded}")
    ok = rounded == 16
    print(f"  [{'PASS' if ok else 'FAIL'}] aggregate helper")
    return ok


def step_api_attach() -> bool:
    print("\n=== 3) API attach llm_cost_inr ===")
    from love_reality_api import _attach_llm_cost_inr

    payload = {
        "pro_premium": {
            "_meta": {
                "sections": {
                    "verdict_page": {"pdf_generation": {"estimated_cost_inr": 5.0}},
                    "blueprint": {"pdf_generation": {"estimated_cost_inr": 7.0}},
                }
            }
        }
    }
    out = _attach_llm_cost_inr(payload)
    cost = out.get("llm_cost_inr")
    ok = cost == 12
    print(f"  llm_cost_inr={cost} (expect 12)")
    print(f"  [{'PASS' if ok else 'FAIL'}] _attach_llm_cost_inr")
    return ok


def step_saved_cache() -> bool:
    print("\n=== 4) Saved English report cache ===")
    cache_dir = _API / ".cache" / "love_report_json"
    if not cache_dir.is_dir():
        print("  [SKIP] no cache dir — app se English report generate karo")
        return True
    files = sorted(cache_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print("  [SKIP] cache empty — pehle phone se English report banao")
        return True
    found_en = False
    ok = True
    for path in files[:5]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"  [BAD] {path.name}: {exc}")
            ok = False
            continue
        lang = str(data.get("lang") or "").lower()
        cost = data.get("llm_cost_inr")
        meta = (data.get("pro_premium") or {}).get("_meta") or {}
        top = (meta.get("pdf_generation") or {}).get("estimated_cost_inr")
        secs = meta.get("sections") or {}
        sec_sum = 0.0
        for row in secs.values():
            if isinstance(row, dict):
                try:
                    sec_sum += float((row.get("pdf_generation") or {}).get("estimated_cost_inr") or 0)
                except (TypeError, ValueError):
                    pass
        if lang != "en":
            continue
        found_en = True
        show = cost if cost else (int(round(sec_sum)) if sec_sum > 0 else int(round(float(top or 0))))
        mark = "PASS" if show and int(show) > 0 else "FAIL"
        if mark == "FAIL":
            ok = False
        print(f"  [{mark}] {path.name} lang=en llm_cost_inr={cost} sec_sum={sec_sum:.2f} top={top}")
        print(f"         -> mobile badge would show: {show if show else '(blank)'}")
    if not found_en:
        print("  [WARN] no lang=en cache — English report generate karo phir dubara chalao")
    return ok


def main() -> int:
    print("LLM cost INR badge — server setup check")
    print(f"API: {_API}")
    results = [step_code(), step_aggregate_math(), step_api_attach(), step_saved_cache()]
    print("\n=== SUMMARY ===")
    if all(results):
        print("Server setup PASS — agar mobile par number nahi dikhe:")
        print("  1) app reload (Expo)")
        print("  2) love-reality-pro-report.tsx mein llmCostInr UI deployed hai?")
        print("  3) English lang select karke NAYA report generate karo")
        return 0
    print("Some checks FAILED — git pull + pm2 restart, phir cache clear + naya report")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

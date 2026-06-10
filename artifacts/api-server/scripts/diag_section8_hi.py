#!/usr/bin/env python3
"""
Section 8 (breakup chapter) — server-side diagnostics for Hindi Love Reality Pro.

Run on VPS (one command per step or all at once):
  cd /root/Cosmic-Lens-Backend/artifacts/api-server
  python3 scripts/diag_section8_hi.py
  python3 scripts/diag_section8_hi.py --live-llm
  python3 scripts/diag_section8_hi.py --live-llm --purge
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

_API = Path(__file__).resolve().parents[1]
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

try:
    from dotenv import load_dotenv

    load_dotenv(_API / ".env")
except Exception:
    pass


def _wc(text: str) -> int:
    return len((text or "").split())


def _breakup_body(pro: dict) -> str:
    for ch in pro.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        if str(ch.get("key") or "").lower() == "breakup":
            return str(ch.get("chapter_body") or ch.get("full_read") or "").strip()
    return ""


def _latest_json(dir_path: Path, pattern: str) -> Path | None:
    files = sorted(dir_path.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _mock_bundle() -> dict:
    return {
        "p1": {"name": "TestYou", "moonSign": "Cancer"},
        "p2": {"name": "TestPartner", "moonSign": "Aries"},
        "breakup_chances": {
            "score": 72,
            "breakup_score": 72,
            "emotional_summary": "Moon square Saturn creates emotional withdrawal under stress.",
            "reasons": [
                "Venus-Mars friction spikes during arguments",
                "Saturn transit pressures commitment timing",
            ],
        },
        "love_compatibility": {"score": 68, "emotional_summary": "Strong pull with pacing mismatch."},
        "hidden_red_flags": {"reasons": ["Mercury signs clash on silence vs talk"]},
        "couple_signals": {
            "synastry_notes": ["7th lord exchange adds karmic weight"],
            "moon_mismatch": "Cardinal vs water pacing",
        },
    }


def step_deploy() -> bool:
    print("\n=== STEP 1: Code deployed? ===")
    api_py = (_API / "love_reality_api.py").read_text(encoding="utf-8")
    polish_py = (_API / "vedic" / "love_reality" / "love_section_polish.py").read_text(encoding="utf-8")
    checks = {
        "_hi_section8_block_response": "_hi_section8_block_response" in api_py,
        "breakup_chapter_word_count": "breakup_chapter_word_count" in api_py,
        "section8_gate.py exists": (_API / "vedic" / "love_reality" / "section8_gate.py").is_file(),
        "ensure_breakup 3 attempts": "LOVE_REALITY_SECTION8_ATTEMPTS" in polish_py,
    }
    ok = True
    for name, hit in checks.items():
        mark = "OK" if hit else "MISSING"
        if not hit:
            ok = False
        print(f"  [{mark}] {name}")
    if not ok:
        print("  -> git pull on VPS + pm2 restart cosmic-api")
    return ok


def step_openai() -> bool:
    print("\n=== STEP 2: OpenAI client ===")
    try:
        from openai_helper import is_available, _get_client

        avail = is_available()
        client = _get_client()
        print(f"  is_available: {avail}")
        print(f"  client: {'OK' if client else 'NONE'}")
        print(f"  OPENAI_API_KEY set: {bool(os.environ.get('OPENAI_API_KEY'))}")
        return bool(avail and client)
    except Exception as exc:
        print(f"  FAIL import: {exc}")
        return False


def step_polish() -> bool:
    print("\n=== STEP 3: LLM polish enabled? ===")
    try:
        from vedic.love_reality.premium_polish import _polish_enabled

        on = _polish_enabled()
        print(f"  polish_enabled: {on}")
        print(f"  LOVE_REALITY_PREMIUM_POLISH: {os.environ.get('LOVE_REALITY_PREMIUM_POLISH')!r}")
        if not on:
            print("  -> Set LOVE_REALITY_PREMIUM_POLISH=1 in .env and pm2 restart")
        return on
    except Exception as exc:
        print(f"  FAIL: {exc}")
        return False


def step_saved_snapshots() -> bool:
    print("\n=== STEP 4: Saved Hindi snapshots / JSON cache ===")
    snap_dir = _API / ".cache" / "love_polish"
    json_dir = _API / ".cache" / "love_report_json"
    snap = _latest_json(snap_dir, "*.json")
    rep = _latest_json(json_dir, "*.json")
    ok = True
    for label, path in (("newest polish snapshot", snap), ("newest report JSON", rep)):
        if not path:
            print(f"  [NONE] {label}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"  [BAD] {label} {path.name}: {exc}")
            ok = False
            continue
        pro = data if label.startswith("newest polish") else data.get("pro_premium") or {}
        if not isinstance(pro, dict):
            pro = data.get("pro_premium") or {}
        body = _breakup_body(pro if "chapters" in pro else data)
        wc = _wc(body)
        mark = "OK" if wc >= 80 else "EMPTY"
        if wc < 80:
            ok = False
        print(f"  [{mark}] {label}: {path.name} breakup_words={wc}")
        if body:
            print(f"         preview: {body[:100]!r}...")
        meta = (pro.get("_meta") or {}).get("section8_breakup") if isinstance(pro, dict) else None
        if meta:
            print(f"         section8_llm_meta: {meta}")
    return ok


def step_gate() -> None:
    print("\n=== STEP 5: Section 8 gate (empty payload) ===")
    from vedic.love_reality.section8_gate import section8_hi_load_gate

    payload = {
        "lang": "hi",
        "pro_premium": {"chapters": []},
        "app_sections": [{"id": "root_cause", "body": ""}],
    }
    ok, reason = section8_hi_load_gate(payload)
    print(f"  gate_ok={ok}")
    print(f"  reason: {reason}")


def step_live_llm(*, purge: bool) -> bool:
    print("\n=== STEP 6: Live breakup LLM (OpenAI call) ===")
    if purge:
        print("  Purging Hindi caches first...")
        try:
            import love_reality_polish_snapshot as snap
            import love_reality_report_json_cache as jcache

            print(f"  purged json={jcache.purge_all_hi_reports()} snap={snap.purge_all_hi_snapshots()}")
        except Exception as exc:
            print(f"  purge warn: {exc}")
        cache_dir = _API / ".cache" / "love_polish"
        for name in glob.glob(str(cache_dir / "chapter_breakup_*.json")):
            try:
                os.remove(name)
                print(f"  removed {os.path.basename(name)}")
            except OSError:
                pass

    from vedic.love_reality.love_section_polish import (
        breakup_chapter_word_count,
        ensure_breakup_section8_llm,
    )

    bundle = _mock_bundle()
    pro: dict = {"chapters": [], "verdict": "Test verdict for prior digest.", "deep_analysis": [
        {"key": "emotional", "title": "Emotional", "explanation": "x" * 50},
        {"key": "communication", "title": "Communication", "explanation": "x" * 50},
        {"key": "trust", "title": "Trust", "explanation": "x" * 50},
        {"key": "long_term", "title": "Long term", "explanation": "x" * 50},
    ]}
    print("  Calling ensure_breakup_section8_llm (force_llm=True)...")
    pro = ensure_breakup_section8_llm(bundle, pro, "hi", force_llm=True)
    wc = breakup_chapter_word_count(pro)
    body = _breakup_body(pro)
    meta = (pro.get("_meta") or {}).get("section8_breakup")
    print(f"  breakup_words: {wc}")
    print(f"  section8_llm_meta: {meta}")
    if body:
        print(f"  preview: {body[:200]!r}...")
    if wc >= 80:
        print("  PASS: OpenAI wrote Section 8 breakup chapter")
        return True
    print("  FAIL: breakup still empty/short — check OpenAI balance, API key, pm2 env")
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Diagnose Hindi Section 8 / breakup LLM on server")
    ap.add_argument("--live-llm", action="store_true", help="Run real OpenAI breakup call (costs tokens)")
    ap.add_argument("--purge", action="store_true", help="With --live-llm, purge Hindi caches first")
    args = ap.parse_args()

    print("Section 8 diagnostics — Cosmic Lens API server")
    print(f"API root: {_API}")

    results = [
        step_deploy(),
        step_openai(),
        step_polish(),
        step_saved_snapshots(),
    ]
    step_gate()
    if args.live_llm:
        results.append(step_live_llm(purge=args.purge))

    print("\n=== SUMMARY ===")
    if all(results):
        print("All automated checks PASS.")
        if not args.live_llm:
            print("Run with --live-llm to test real OpenAI breakup generation.")
        return 0
    print("Some checks FAILED — fix items marked MISSING/FAIL/NONE above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

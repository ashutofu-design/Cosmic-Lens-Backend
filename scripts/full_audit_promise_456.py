#!/usr/bin/env python3
"""Full live ASK AUDIT for relationship promise questions 4–6."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = [
    "Kya meri life me romantic relationship banega?",
    "Kya meri life me long-term relationship ka yog hai?",
    "Kya main committed relationship ke liye bana/bani hoon?",
]
OUTPUT_OFFSET = 4  # full_audit_p4.txt, p5, p6


def main() -> int:
    results = []
    for i, q in enumerate(QUESTIONS, OUTPUT_OFFSET):
        out_path = ROOT / "scripts" / f"full_audit_p{i}.txt"
        print(f"Running Q{i}...", flush=True)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "ask_audit_question.py"), q, "--lang", "hi"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            cwd=str(ROOT),
        )
        text = (proc.stdout or "") + (proc.stderr or "")
        out_path.write_text(text, encoding="utf-8")
        entry = {"question": q, "exit_code": proc.returncode, "output_file": str(out_path)}
        if '"pass":' in text:
            try:
                audit_start = text.index("=== AUDIT ===")
                audit_json = text[audit_start:].split("=== AUDIT ===", 1)[1].strip()
                entry["audit"] = json.loads(audit_json)
            except Exception as exc:
                entry["parse_error"] = str(exc)
        results.append(entry)
        print(f"Q{i} done exit={proc.returncode}", flush=True)

    summary_path = ROOT / "scripts" / "full_audit_promise_456.json"
    summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    passed = sum(1 for r in results if (r.get("audit") or {}).get("pass"))
    print(f"SUMMARY: {passed}/{len(QUESTIONS)} PASS -> {summary_path}")
    return 0 if passed == len(QUESTIONS) else 1


if __name__ == "__main__":
    raise SystemExit(main())

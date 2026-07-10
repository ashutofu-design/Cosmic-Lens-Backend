#!/usr/bin/env python3
"""Batch ASK AUDIT — run multiple questions, save JSON + TXT."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ask_audit_question as audit  # noqa: E402

QUESTIONS = [
    "Kya meri current relationship long-term chalegi?",
    "Kya mera partner sach me mujhse pyaar karta hai?",
    "Kya mera partner loyal aur faithful hai?",
    "Kya hum dono compatible hain?",
    "Relationship me problems kis wajah se aa rahi hain?",
]


def main() -> int:
    admin_token = audit._read_admin_secret()
    demo = audit._demo_login()
    uid = int(demo["id"])
    api_key = str(demo["api_key"])
    kundli, birth = audit._user_kundli(uid, api_key)

    results: list[dict] = []
    lines: list[str] = []

    for i, q in enumerate(QUESTIONS, 1):
        lines.append(f"\n{'=' * 72}\n[{i}/{len(QUESTIONS)}] {q}\n{'=' * 72}")
        ask_out = audit._ask_stream(q, "hi", uid, api_key, kundli, birth)
        admin_row = audit._admin_latest(uid, admin_token, q) if admin_token else None
        report = audit._audit(q, ask_out, admin_row)
        results.append(report)
        lines.append("\n=== ANSWER ===\n" + (report.get("answer_text") or "(empty)"))
        lines.append(
            f"\n=== PATH ===\nsource={report.get('ask_source')} | "
            f"engine={report.get('admin_engine')} | archetype={report.get('admin_archetype')} | "
            f"path={report.get('answer_path')} | pass={report.get('pass')}"
        )
        ev = report.get("evidence_audit") or {}
        lines.append("\n=== EVIDENCE ===")
        for e in ev.get("evidence_sample") or []:
            lines.append(f"  - {e}")
        for w in ev.get("warnings") or []:
            lines.append(f"  WARN: {w}")
        lines.append(f"\nok: {report.get('ok')}")
        lines.append(f"issues: {report.get('issues')}")

    out_json = ROOT / "scripts" / "ask_audit_batch_results.json"
    out_txt = ROOT / "scripts" / "ask_audit_batch_results.txt"
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    out_txt.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_json} and {out_txt}")
    return 0 if all(r.get("pass") for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

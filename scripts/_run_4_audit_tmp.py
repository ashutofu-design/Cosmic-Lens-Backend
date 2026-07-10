#!/usr/bin/env python3
"""Temporary runner for 4 Hindi audit questions."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ask_audit_question as audit  # noqa: E402

QUESTIONS = [
    "Kya mera partner sach me mujhse pyaar karta hai?",
    "Kya mera partner loyal aur faithful hai?",
    "Kya hum dono compatible hain?",
    "Relationship me problems kis wajah se aa rahi hain?",
]

OUT = ROOT / "audit_4_results.json"


def main() -> int:
    admin_token = audit._read_admin_secret()
    demo = audit._demo_login()
    uid = int(demo["id"])
    api_key = str(demo["api_key"])
    kundli, birth = audit._user_kundli(uid, api_key)

    results: list[dict] = []
    for q in QUESTIONS:
        print(f"ASKING: {q}", flush=True)
        ask_out = audit._ask_stream(q, "hi", uid, api_key, kundli, birth)
        admin_row = audit._admin_latest(uid, admin_token, q) if admin_token else None
        report = audit._audit(q, ask_out, admin_row)
        results.append(report)
        print(json.dumps(report, ensure_ascii=False), flush=True)
        print("---END---", flush=True)

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"WROTE {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

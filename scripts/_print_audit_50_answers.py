#!/usr/bin/env python3
"""Print all 50 audit answers to stdout + report file."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "scripts" / "full_audit_promise_50.json"
OUT_PATH = ROOT / "scripts" / "audit_50_answers_print.txt"


def content_ok(r: dict) -> bool:
    src = str(r.get("ask_source") or "")
    text = str(r.get("answer_text") or "").strip()
    issues = r.get("issues") or []
    blocked = any(str(x).startswith(("RUNTIME", "WRONG_ENGINE")) for x in issues)
    return bool(text) and src == "mr_engine_then_llm" and not blocked


def main() -> int:
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    rows = sorted(rows, key=lambda r: int(r.get("q_index") or 0))
    n = len(rows)
    strict = sum(1 for r in rows if r.get("pass"))
    content = sum(1 for r in rows if content_ok(r))
    no_admin = sum(1 for r in rows if any("NO_ADMIN_ENGINE" in str(i) for i in (r.get("issues") or [])))
    bad = [r for r in rows if not content_ok(r)]

    lines: list[str] = []
    lines.append(f"Total: {n}/50")
    lines.append(f"Strict PASS: {strict}/{n}")
    lines.append(f"Content OK (MR engine + answer): {content}/{n}")
    lines.append(f"NO_ADMIN_ENGINE: {no_admin}/{n}")
    lines.append("")
    lines.append("=== WRONG ROUTING / NO ANSWER ===")
    if not bad:
        lines.append("(none)")
    else:
        for r in bad:
            lines.append(
                f"Q{r.get('q_index')}: {r.get('question')} | source={r.get('ask_source')} | issues={r.get('issues')}"
            )
    lines.append("")
    lines.append("=== ALL 50 ANSWERS ===")
    for r in rows:
        qi = r.get("q_index")
        q = r.get("question") or ""
        src = r.get("ask_source") or ""
        ans = (r.get("answer_text") or "").strip()
        ok = "SAHI" if content_ok(r) else "GALAT"
        lines.append("")
        lines.append(f"--- Q{qi} [{ok}] source={src} ---")
        lines.append(f"Q: {q}")
        lines.append(f"A: {ans if ans else '(NO ANSWER)'}")

    text = "\n".join(lines)
    OUT_PATH.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

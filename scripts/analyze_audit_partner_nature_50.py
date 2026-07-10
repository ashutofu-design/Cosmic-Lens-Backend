#!/usr/bin/env python3
"""Analyze full_audit_partner_nature_50.json — content vs routing failures."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "scripts" / "full_audit_partner_nature_50.json"


def content_ok(r: dict) -> bool:
    src = str(r.get("ask_source") or "")
    text = str(r.get("answer_text") or "").strip()
    issues = r.get("issues") or []
    blocked = any(
        str(x).startswith(
            (
                "BLOCKED",
                "ENGINE_REFUSAL",
                "DIRECT_LLM",
                "TIMING_Q_BUT_STATIC",
                "WRONG_ENGINE",
                "RUNTIME",
            )
        )
        for x in issues
    ) or "timing_domain_clarifier" in src or "needs_clarification" in str(r.get("ask_topic") or "")
    return bool(text) and src == "mr_engine_then_llm" and not blocked


def year_leak(text: str) -> bool:
    return bool(re.search(r"\b20(2[4-9]|3\d)\b", text))


def main() -> int:
    if not JSON_PATH.is_file():
        print(f"Missing {JSON_PATH}")
        return 2
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    n = len(rows)
    strict = sum(1 for r in rows if r.get("pass"))
    content = sum(1 for r in rows if content_ok(r))
    no_admin = sum(1 for r in rows if any("NO_ADMIN_ENGINE" in str(i) for i in (r.get("issues") or [])))
    leaks = [(r.get("q_index"), r.get("question")) for r in rows if year_leak(str(r.get("answer_text") or ""))]
    bad = [r for r in rows if not content_ok(r)]

    print(f"Completed: {n}/50")
    print(f"Strict PASS: {strict}/{n}")
    print(f"Content OK (mr_engine + answer): {content}/{n}")
    print(f"NO_ADMIN_ENGINE: {no_admin}/{n}")
    print(f"Year leak (2024+): {len(leaks)}")
    if leaks:
        for qi, q in leaks:
            print(f"  Q{qi}: {q}")

    print("\n=== CONTENT/Routing FAILURES ===")
    if not bad:
        print("(none)")
    else:
        for r in bad:
            print(
                f"Q{r.get('q_index')}: {r.get('question')!r}\n"
                f"  source={r.get('ask_source')} topic={r.get('ask_topic')}\n"
                f"  issues={r.get('issues')}\n"
                f"  answer={str(r.get('answer_text') or '')[:120]}..."
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

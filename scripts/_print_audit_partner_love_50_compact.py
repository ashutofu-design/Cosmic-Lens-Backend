#!/usr/bin/env python3
"""Print partner-love 50 audit results compactly (for chat pasting)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "scripts" / "full_audit_partner_love_50.json"


def content_ok(r: dict) -> bool:
    src = str(r.get("ask_source") or "")
    text = str(r.get("answer_text") or "").strip()
    issues = r.get("issues") or []
    blocked = any(
        str(x).startswith(
            ("BLOCKED", "ENGINE_REFUSAL", "DIRECT_LLM", "TIMING_Q_BUT_STATIC", "WRONG_ENGINE", "RUNTIME")
        )
        for x in issues
    ) or "timing_domain_clarifier" in src or "needs_clarification" in str(r.get("ask_topic") or "")
    return bool(text) and src == "mr_engine_then_llm" and not blocked


def year_leak(text: str) -> bool:
    return bool(re.search(r"\b20(2[4-9]|3\d)\b", text or ""))


def main() -> int:
    if not JSON_PATH.is_file():
        print(f"Missing {JSON_PATH}")
        return 2
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    rows = sorted(rows, key=lambda r: int(r.get("q_index") or 0))

    n = len(rows)
    strict = sum(1 for r in rows if r.get("pass"))
    content = sum(1 for r in rows if content_ok(r))
    no_admin = sum(1 for r in rows if any("NO_ADMIN_ENGINE" in str(i) for i in (r.get("issues") or [])))
    no_answer = sum(1 for r in rows if not (r.get("answer_text") or "").strip())

    leaks = [r for r in rows if year_leak(str(r.get("answer_text") or ""))]
    bad = [r for r in rows if not content_ok(r)]

    print(f"RESULT: {n}/50  strict_pass={strict}  content_ok={content}  NO_ADMIN_ENGINE={no_admin}  no_answer={no_answer}")
    if leaks:
        print("Year leak questions:", [f"Q{r.get('q_index')}:{r.get('question')}" for r in leaks])
    if bad:
        print("\nWRONG/ROUTING FAILS:")
        for r in bad:
            qi = r.get("q_index")
            q = r.get("question")
            src = r.get("ask_source")
            issues = r.get("issues") or []
            a = str(r.get("answer_text") or "").strip()
            a0 = a[:220] + ("..." if len(a) > 220 else "")
            print(f"Q{qi}: {q}\n  source={src}\n  issues={issues}\n  A0={a0}\n")
    else:
        print("\nWRONG/ROUTING FAILS: none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python3
"""Remove duplicate firebase_verify_route — keep Google Sign-In version."""
from __future__ import annotations

import re
import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "flask_app.py"

ROUTE_PATTERN = re.compile(
    r'@app\.route\(["\']/api/auth/firebase-verify["\'],\s*methods=\[[^\]]+\]\)\s*'
    r"def firebase_verify_route\(\):.*?"
    r"(?=\n@app\.route|\ndef _firebase_verify_|\ndef [a-z_]+\(|\nclass |\Z)",
    re.DOTALL,
)


def main() -> int:
    if not TARGET.is_file():
        print(f"ERROR: not found: {TARGET}", file=sys.stderr)
        return 1

    text = TARGET.read_text(encoding="utf-8")
    matches = list(ROUTE_PATTERN.finditer(text))

    if len(matches) <= 1:
        print("OK: no duplicate firebase_verify_route.")
        return 0

    keep_idx = None
    for i, m in enumerate(matches):
        if "sign_in_provider" in m.group(0) and "resolve_email_from_decoded" in m.group(0):
            keep_idx = i
            break

    if keep_idx is None:
        print("ERROR: patched route (with sign_in_provider) not found.", file=sys.stderr)
        return 1

    for i, m in reversed(list(enumerate(matches))):
        if i == keep_idx:
            continue
        text = text[: m.start()] + text[m.end() :]

    TARGET.write_text(text, encoding="utf-8")
    removed = len(matches) - 1
    print(f"OK: removed {removed} duplicate firebase_verify_route(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

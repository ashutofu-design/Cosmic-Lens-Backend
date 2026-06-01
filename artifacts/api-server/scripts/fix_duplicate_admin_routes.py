#!/usr/bin/env python3
"""Keep only the patched Admin routes block; strip all other /api/admin/* routes."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "flask_app.py"
MARKER = "# ── Admin routes ────────────────────────────────────────────────────────────────"


def _health_idx(text: str, start: int) -> int:
    for needle in (
        '@app.route("/api/health", methods=["GET"])',
        '@app.route("/api/healthz", methods=["GET"])',
        '@app.route("/api/healthz"',
    ):
        idx = text.find(needle, start)
        if idx != -1:
            return idx
    return -1


def _strip_admin_routes(text: str) -> str:
    out = text
    while True:
        idx = out.find('@app.route("/api/admin')
        if idx == -1:
            idx = out.find("@app.route('/api/admin")
        if idx == -1:
            break
        rest = out[idx + 1 :]
        nxt = re.search(r"\n@app\.route|\n# ──", rest)
        end = idx + 1 + nxt.start() if nxt else len(out)
        out = out[:idx].rstrip() + "\n\n" + out[end:].lstrip()
    return out


def main() -> int:
    if not TARGET.is_file():
        print("ERROR: flask_app.py not found", file=sys.stderr)
        return 1

    text = TARGET.read_text(encoding="utf-8")
    marker_idx = text.find(MARKER)
    if marker_idx == -1:
        print("ERROR: admin routes marker not found", file=sys.stderr)
        return 1

    health_idx = _health_idx(text, marker_idx)
    if health_idx == -1:
        print("ERROR: health route anchor not found after admin block", file=sys.stderr)
        return 1

    good_block = text[marker_idx:health_idx].strip() + "\n\n"
    before = _strip_admin_routes(text[:marker_idx])
    after = _strip_admin_routes(text[health_idx:])

    new_text = before.rstrip() + "\n\n" + good_block + after.lstrip()
    TARGET.write_text(new_text, encoding="utf-8")

    counts = {
        "admin_dashboard_route": new_text.count("def admin_dashboard_route("),
        "admin_stats": new_text.count("def admin_stats("),
        "admin_users": new_text.count("def admin_users("),
    }
    print("OK: kept single admin block:", counts)

    for name, n in counts.items():
        if n != 1:
            print(f"ERROR: expected 1 {name}, got {n}", file=sys.stderr)
            return 1

    try:
        compile(new_text, str(TARGET), "exec")
    except SyntaxError as e:
        print(f"ERROR: syntax: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

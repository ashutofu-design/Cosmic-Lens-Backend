#!/usr/bin/env python3
"""Ensure require_admin exists and admin routes are present once in flask_app.py."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "flask_app.py"

REQUIRE_ADMIN_BLOCK = '''
# ── Admin auth helper ──────────────────────────────────────────────────────────
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "").strip()


def require_admin():
    """Check admin token from header. Returns None if valid, error response if not."""
    from admin_dashboard import admin_no_auth

    if admin_no_auth():
        return None
    if not ADMIN_SECRET:
        return jsonify({"error": "Admin auth is not configured"}), 503
    token = request.headers.get("X-Admin-Token", "")
    if not token or token != ADMIN_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    return None

'''.lstrip("\n")


def main() -> int:
    if not TARGET.is_file():
        print("ERROR: flask_app.py not found", file=sys.stderr)
        return 1

    text = TARGET.read_text(encoding="utf-8")
    changed = False

    if "def require_admin(" not in text:
        m = re.search(r"(init_db\(app\)\s*\n)", text)
        if not m:
            print("ERROR: init_db(app) not found", file=sys.stderr)
            return 1
        text = text[: m.end()] + "\n" + REQUIRE_ADMIN_BLOCK + text[m.end() :]
        changed = True
        print("OK: added require_admin()")

    # Remove duplicate admin route blocks (keep first)
    marker = '# ── Admin routes ────────────────────────────────────────────────────────────────'
    count = text.count(marker)
    if count > 1:
        first = text.find(marker)
        second = text.find(marker, first + 1)
        health_idx = text.find('@app.route("/api/health', second)
        if health_idx == -1:
            health_idx = text.find('@app.route("/api/healthz', second)
        if health_idx != -1:
            text = text[:second] + text[health_idx:]
            changed = True
            print("OK: removed duplicate admin routes block")

    if changed:
        TARGET.write_text(text, encoding="utf-8")
        print("OK: saved flask_app.py")
    else:
        print("OK: require_admin present, no duplicate admin blocks")

    try:
        compile(text, str(TARGET), "exec")
        print("OK: syntax check passed")
    except SyntaxError as e:
        print(f"ERROR: syntax error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

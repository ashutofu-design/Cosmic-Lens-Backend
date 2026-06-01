#!/usr/bin/env python3
"""Add admin API routes + require_admin() to VPS flask_app.py if missing."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "flask_app.py"
ADMIN_PY = ROOT / "admin_dashboard.py"

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

ADMIN_ROUTES = '''
# ── Admin routes ────────────────────────────────────────────────────────────────


@app.route("/api/admin/dashboard", methods=["GET"])
def admin_dashboard_route():
    """Full local admin dashboard payload (users, payments, reports)."""
    err = require_admin()
    if err:
        return err
    from admin_dashboard import build_dashboard

    return jsonify(build_dashboard(db.session))


@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    """Dashboard stats — total users, PRO users, active today."""
    err = require_admin()
    if err:
        return err

    from datetime import timedelta
    from admin_dashboard import build_dashboard

    dash = build_dashboard(db.session)
    today = datetime.now(_UTC_TZ.utc).replace(tzinfo=None) - timedelta(hours=24)
    pro_users = User.query.filter_by(is_pro=True).count()
    active_today = User.query.filter(User.last_active >= today).count()
    total_kundli = Kundli.query.count()

    return jsonify(
        {
            "total_users": dash["total_users"],
            "pro_users": pro_users,
            "active_today": active_today,
            "total_kundli": total_kundli,
            "payments": dash["payments"],
        }
    )


@app.route("/api/admin/users", methods=["GET"])
def admin_users():
    """List all users with pagination."""
    err = require_admin()
    if err:
        return err

    from admin_dashboard import build_users_list

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    search = request.args.get("search", "").strip()

    return jsonify(build_users_list(db.session, page=page, per_page=per_page, search=search))


@app.route("/api/admin/users/<int:user_id>", methods=["GET"])
def admin_user_detail(user_id):
    """Get full detail of one user."""
    err = require_admin()
    if err:
        return err

    from admin_dashboard import build_user_detail

    detail = build_user_detail(user_id)
    if not detail:
        return jsonify({"error": "User not found"}), 404
    return jsonify(detail)


@app.route("/api/admin/users/<int:user_id>/pro", methods=["POST"])
def admin_toggle_pro(user_id):
    """Toggle PRO status for a user."""
    err = require_admin()
    if err:
        return err

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(force=True, silent=True) or {}
    user.is_pro = data.get("is_pro", not user.is_pro)
    db.session.commit()
    return jsonify({"success": True, "user_id": user_id, "is_pro": user.is_pro})


@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
def admin_delete_user(user_id):
    """Delete a user and their kundli."""
    err = require_admin()
    if err:
        return err

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"success": True})


'''.lstrip("\n")


def main() -> int:
    if not ADMIN_PY.is_file():
        print(f"ERROR: missing {ADMIN_PY.name} — copy it to the api-server folder first.", file=sys.stderr)
        return 1
    if not TARGET.is_file():
        print(f"ERROR: missing {TARGET}", file=sys.stderr)
        return 1

    text = TARGET.read_text(encoding="utf-8")
    changed = False

    if "def require_admin(" not in text:
        m = re.search(r"(init_db\(app\)\s*\n)", text)
        if not m:
            print("ERROR: could not find init_db(app) anchor", file=sys.stderr)
            return 1
        text = text[: m.end()] + "\n" + REQUIRE_ADMIN_BLOCK + text[m.end() :]
        changed = True
        print("OK: inserted require_admin() block")

    if "/api/admin/dashboard" not in text:
        anchor_markers = [
            '@app.route("/api/health", methods=["GET"])',
            '@app.route("/api/healthz"',
            '@app.route("/api/healthz", methods=["GET"])',
        ]
        inserted = False
        for marker in anchor_markers:
            idx = text.find(marker)
            if idx != -1:
                text = text[:idx] + ADMIN_ROUTES + "\n\n" + text[idx:]
                inserted = True
                changed = True
                print(f"OK: inserted admin routes before {marker[:40]}...")
                break
        if not inserted:
            print("ERROR: could not find health route anchor for admin routes", file=sys.stderr)
            return 1

    if not changed:
        print("OK: admin routes already present — no changes.")
        return 0

    TARGET.write_text(text, encoding="utf-8")
    print(f"OK: patched {TARGET.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

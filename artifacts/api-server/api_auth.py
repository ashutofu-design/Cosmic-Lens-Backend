"""Shared API authentication helpers for Flask routes and blueprints."""

from __future__ import annotations

from flask import jsonify, request


def get_authed_user(user_id: int):
    """Validate X-API-Key header for a given user_id. Returns (user, error_response)."""
    from models import User

    api_key = request.headers.get("X-API-Key", "").strip()
    user = User.query.get(user_id)
    if not user:
        return None, (jsonify({"error": "User not found"}), 404)
    if not api_key or user.api_key != api_key:
        return None, (jsonify({"error": "Unauthorized — invalid API key"}), 401)
    return user, None


def require_authed_user():
    """Require X-User-Id + X-API-Key headers. Returns (user, error_response)."""
    uid_hdr = (request.headers.get("X-User-Id") or "").strip()
    if not uid_hdr:
        return None, (
            jsonify(
                {
                    "error": "auth_required",
                    "message": "X-User-Id and X-API-Key required",
                }
            ),
            401,
        )
    try:
        user_id = int(uid_hdr)
    except (TypeError, ValueError):
        return None, (jsonify({"error": "invalid_user_id"}), 400)
    return get_authed_user(user_id)


def _coerce_user_id(raw) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def authed_user_from_request(data: dict | None = None):
    """
    Resolve authenticated user — X-User-Id header is authoritative when present.

    Rejects body/query user_id that disagrees with X-User-Id (IDOR/BOLA guard).
    Legacy clients without X-User-Id may still send user_id in JSON (deprecated).
    """
    payload = data if isinstance(data, dict) else {}
    uid_hdr = (request.headers.get("X-User-Id") or "").strip()
    body_uid = _coerce_user_id(payload.get("user_id"))
    if body_uid is None:
        body_uid = _coerce_user_id(request.args.get("user_id"))

    if uid_hdr:
        try:
            header_uid = int(uid_hdr)
        except (TypeError, ValueError):
            return None, (jsonify({"error": "invalid_user_id"}), 400)
        if body_uid is not None and body_uid != header_uid:
            return None, (
                jsonify(
                    {
                        "error": "forbidden",
                        "message": "user_id does not match X-User-Id",
                    }
                ),
                403,
            )
        return get_authed_user(header_uid)

    if body_uid is None:
        return None, (
            jsonify(
                {
                    "error": "auth_required",
                    "message": "X-User-Id and X-API-Key required",
                }
            ),
            401,
        )
    return get_authed_user(body_uid)


def auth_error_response(require_user) -> tuple | None:
    """Run require_user() and return a Flask error tuple, or None if OK."""
    if not require_user:
        return None
    _user, err = require_user()
    return err


def assert_route_user_id(route_user_id: int):
    """For /api/user/<id>/... — URL id must match authenticated header user."""
    user, err = require_authed_user()
    if err:
        return None, err
    if int(user.id) != int(route_user_id):
        return None, (
            jsonify({"error": "forbidden", "message": "URL user_id mismatch"}),
            403,
        )
    return user, None

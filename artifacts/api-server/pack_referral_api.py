"""Cosmic Pack referral routes — share code + attach + reward on pack buy."""
from __future__ import annotations

from flask import jsonify, request

import pack_referral as pref


def _resolve_user():
    from flask_app import get_authed_user

    uid_hdr = (request.headers.get("X-User-Id") or "").strip()
    if not uid_hdr:
        return None, (jsonify({"error": "auth_required", "message": "X-User-Id required"}), 401)
    try:
        user, err = get_authed_user(int(uid_hdr))
    except (TypeError, ValueError):
        return None, (jsonify({"error": "invalid_user_id"}), 400)
    if err:
        return None, err
    return user, None


def register_pack_referral_routes(app) -> None:
    @app.route("/api/pack-referral/mine", methods=["GET", "OPTIONS"])
    def pack_referral_mine():
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        return jsonify(pref.mine_payload(user))

    @app.route("/api/pack-referral/attach", methods=["POST", "OPTIONS"])
    def pack_referral_attach():
        if request.method == "OPTIONS":
            return "", 204
        user, err = _resolve_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        code = (data.get("referral_code") or data.get("code") or "").strip()
        out = pref.attach_referrer(user, code)
        if not out.get("ok"):
            status = 400
            if out.get("error") == "self_referral_not_allowed":
                status = 400
            return jsonify(out), status
        return jsonify(out)

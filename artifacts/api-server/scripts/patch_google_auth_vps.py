#!/usr/bin/env python3
"""Add/replace Google Sign-In aware firebase-verify route on VPS."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "flask_app.py"

NEW_ROUTE = '''
@app.route("/api/auth/firebase-verify", methods=["POST"])
def firebase_verify_route():
    """Firebase login — Google Sign-In or phone OTP."""
    from firebase_admin_helper import (
        FirebaseAuthError,
        resolve_email_from_decoded,
        resolve_sign_in_provider,
        verify_id_token,
    )
    from subscription_helper import auto_start_trial_on_signup, subscription_status

    data = request.get_json(force=True, silent=True) or {}
    id_token = (data.get("id_token") or "").strip()
    name = (data.get("name") or "").strip()[:200]

    if not id_token:
        return jsonify({"ok": False, "error": "Missing id_token"}), 400

    try:
        decoded = verify_id_token(id_token)
    except FirebaseAuthError as e:
        app.logger.warning("[firebase-verify] %s", e)
        return jsonify({"ok": False, "error": str(e)}), 401

    phone_e164 = (decoded.get("phone_number") or "").strip()
    email = resolve_email_from_decoded(decoded)
    firebase_uid = (decoded.get("uid") or "").strip()
    display_name = (decoded.get("name") or name or "").strip()[:200]
    sign_in_provider = resolve_sign_in_provider(decoded)

    if sign_in_provider == "google.com":
        if not email:
            return jsonify({"ok": False, "error": "Google account has no email. Use a Gmail account with email permission."}), 401
        return _firebase_verify_google_user(
            email=email,
            firebase_uid=firebase_uid,
            name=display_name,
            auto_start_trial_on_signup=auto_start_trial_on_signup,
            subscription_status=subscription_status,
        )

    if phone_e164 and phone_e164.startswith("+"):
        return _firebase_verify_phone_user(
            phone_e164=phone_e164,
            name=display_name,
            auto_start_trial_on_signup=auto_start_trial_on_signup,
            subscription_status=subscription_status,
        )

    if email and "@" in email:
        return _firebase_verify_google_user(
            email=email,
            firebase_uid=firebase_uid,
            name=display_name,
            auto_start_trial_on_signup=auto_start_trial_on_signup,
            subscription_status=subscription_status,
        )

    return jsonify({"ok": False, "error": "Token has no verified phone or email"}), 401


'''.lstrip("\n")

GOOGLE_HELPER = '''
def _firebase_verify_google_user(*, email, firebase_uid, name, auto_start_trial_on_signup, subscription_status):
    from sqlalchemy.exc import IntegrityError

    user = User.query.filter_by(email=email).first()
    if not user and firebase_uid:
        user = User.query.filter_by(google_id=firebase_uid).first()

    is_new = False
    if not user:
        is_new = True
        local_name = name or email.split("@", 1)[0]
        user = User(
            name=local_name,
            email=email,
            google_id=firebase_uid or None,
            api_key=secrets.token_hex(32),
        )
        db.session.add(user)
        try:
            db.session.flush()
        except IntegrityError:
            db.session.rollback()
            user = User.query.filter_by(email=email).first()
            is_new = False
            if not user and firebase_uid:
                user = User.query.filter_by(google_id=firebase_uid).first()
            if not user:
                return jsonify({"ok": False, "error": "User creation race; please retry"}), 500
        if is_new:
            try:
                auto_start_trial_on_signup(user)
            except Exception:
                app.logger.exception("[firebase-verify] auto_start_trial failed")
    else:
        if not user.api_key:
            user.api_key = secrets.token_hex(32)
        if firebase_uid and not user.google_id:
            user.google_id = firebase_uid
        if not user.email:
            user.email = email
        user.last_active = datetime.now(_UTC_TZ.utc).replace(tzinfo=None)
        if name and (not user.name or user.name.startswith("User ")):
            user.name = name

    db.session.commit()
    payload = user.to_dict()
    payload["subscription"] = subscription_status(user)
    payload["is_new_user"] = is_new
    payload["ok"] = True
    return jsonify(payload), (201 if is_new else 200)


'''.lstrip("\n")

REPLACE_PATTERNS = [
    r'@app\.route\(["\']/api/auth/firebase-verify["\'],\s*methods=\[["\']POST["\']\]\)\s*def firebase_verify_route\(\):.*?(?=\ndef _firebase_verify_phone_user)',
    r'@app\.route\(["\']/api/auth/firebase-verify["\'],\s*methods=\(["\']POST["\'],\)\]\)\s*def firebase_verify_route\(\):.*?(?=\ndef _firebase_verify_phone_user)',
]

INSERT_ANCHORS = [
    '@app.route("/api/auth/demo", methods=["POST"])',
    "@app.route('/api/auth/demo', methods=['POST'])",
    '@app.route("/api/auth/signup", methods=["POST"])',
    "def _firebase_verify_phone_user",
]


def main() -> int:
    if not TARGET.is_file():
        print(f"ERROR: not found: {TARGET}", file=sys.stderr)
        return 1

    text = TARGET.read_text(encoding="utf-8")

    if "sign_in_provider == \"google.com\"" in text and "resolve_email_from_decoded" in text:
        print("OK: Google auth patch already applied.")
        return 0

    for pat in REPLACE_PATTERNS:
        if re.search(pat, text, flags=re.DOTALL):
            text = re.sub(pat, NEW_ROUTE.rstrip() + "\n\n", text, count=1, flags=re.DOTALL)
            TARGET.write_text(text, encoding="utf-8")
            print("OK: replaced firebase_verify_route for Google Sign-In.")
            return 0

    block = NEW_ROUTE
    if "def _firebase_verify_google_user" not in text:
        block += GOOGLE_HELPER

    for anchor in INSERT_ANCHORS:
        if anchor in text:
            text = text.replace(anchor, block + anchor, 1)
            TARGET.write_text(text, encoding="utf-8")
            print(f"OK: inserted firebase-verify route before: {anchor[:50]}...")
            return 0

    print("ERROR: could not find insert point in flask_app.py", file=sys.stderr)
    print("Run:  grep -n 'auth/demo\\|auth/signup\\|firebase' flask_app.py | head -20", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

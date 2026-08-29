"""Optional Google Play Integrity verification for sensitive API routes."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

log = logging.getLogger(__name__)


def integrity_required() -> bool:
    """Opt-in only — set PLAY_INTEGRITY_REQUIRED=1 after mobile SDK + Play Console are live."""
    return os.environ.get("PLAY_INTEGRITY_REQUIRED", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _service_account_info() -> dict[str, Any] | None:
    raw = (os.environ.get("PLAY_INTEGRITY_SERVICE_ACCOUNT_JSON") or "").strip()
    if not raw:
        raw = (os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON") or "").strip()
    if not raw:
        path = (os.environ.get("PLAY_INTEGRITY_CREDENTIALS_PATH") or "").strip()
        if path and os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception as exc:
                log.warning("[integrity] credentials file unreadable: %s", exc)
                return None
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.warning("[integrity] invalid service account JSON for Play Integrity")
        return None


def verify_play_integrity_token(token: str) -> bool:
    """Decode token via Play Integrity API. False when misconfigured or invalid."""
    token = (token or "").strip()
    if not token:
        return False
    package = (os.environ.get("PLAY_INTEGRITY_PACKAGE_NAME") or "com.cosmiclens.app").strip()
    creds = _service_account_info()
    if not creds:
        log.error("[integrity] no service account — rejecting token")
        return False
    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account
        import requests

        scopes = ["https://www.googleapis.com/auth/playintegrity"]
        credentials = service_account.Credentials.from_service_account_info(creds, scopes=scopes)
        credentials.refresh(Request())
        url = f"https://playintegrity.googleapis.com/v1/{package}:decodeIntegrityToken"
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {credentials.token}"},
            json={"integrityToken": token},
            timeout=8,
        )
        if resp.status_code != 200:
            log.warning("[integrity] decode failed status=%s", resp.status_code)
            return False
        payload = resp.json()
        verdict = (
            (payload.get("tokenPayloadExternal") or {})
            .get("deviceIntegrity", {})
            .get("deviceRecognitionVerdict")
            or []
        )
        return "MEETS_DEVICE_INTEGRITY" in verdict or "MEETS_BASIC_INTEGRITY" in verdict
    except Exception as exc:
        log.warning("[integrity] verify failed: %s", exc)
        return False


def play_integrity_error_response():
    from flask import jsonify

    return jsonify({"error": "integrity_verification_failed"}), 403


def check_play_integrity_request() -> tuple[bool, tuple | None]:
    """Return (ok, error_response). Skips when PLAY_INTEGRITY_REQUIRED is off."""
    if not integrity_required():
        return True, None
    from flask import request

    token = (request.headers.get("X-Play-Integrity") or "").strip()
    if not verify_play_integrity_token(token):
        return False, play_integrity_error_response()
    return True, None

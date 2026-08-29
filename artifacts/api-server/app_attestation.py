"""Server-side client attestation — Google Play Integrity + Firebase App Check.

Both are verified on the server. A client that fails (or omits) attestation is
rejected before the sensitive handler runs; the client is never asked to make
the trust decision itself.

Enforcement is controlled by environment variables so the backend can be
deployed before the signed Play Store build that carries the tokens:

    PLAY_INTEGRITY_REQUIRED=1   enforce Play Integrity on protected paths
    APP_CHECK_REQUIRED=1        enforce Firebase App Check on protected paths
    ATTESTATION_EXEMPT_PATHS    extra comma-separated path prefixes to skip

Protected paths cover payment, entitlement/credit grants and expensive
AI/compute endpoints.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any

log = logging.getLogger(__name__)

# Sensitive prefixes: money, entitlement and expensive compute.
PROTECTED_PREFIXES: tuple[str, ...] = (
    "/api/payment/",
    "/api/create-order",
    "/api/verify-payment",
    "/api/subscription/",
    "/api/ask",
    "/api/stt",
    "/api/tts",
    "/api/face_reading/analyze",
    "/api/face_reading/extract",
    "/api/face_reading/report",
    "/api/cosmic-intelligence-v3/",
    "/api/couple-report/",
    "/api/numerology-report/",
    "/api/palmistry-report/",
    "/api/face-reading-report/",
    "/api/business-vastu/",
    "/api/birth-time-rectification/",
    "/api/astrovastu/",
    "/api/gemstone/",
    "/api/career/",
)

# Never gate these — health checks, webhooks (server-to-server) and auth
# bootstrap must work without a mobile attestation token.
ALWAYS_EXEMPT_PREFIXES: tuple[str, ...] = (
    "/api/healthz",
    "/api/health",
    "/api/payment/webhook",
    "/api/telegram/",
    "/api/admin/",
    "/api/login",
    "/api/signup",
    "/api/auth/",
)


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def play_integrity_required() -> bool:
    return _truthy("PLAY_INTEGRITY_REQUIRED")


def app_check_required() -> bool:
    return _truthy("APP_CHECK_REQUIRED")


def attestation_enabled() -> bool:
    return play_integrity_required() or app_check_required()


def _exempt_prefixes() -> tuple[str, ...]:
    extra = (os.environ.get("ATTESTATION_EXEMPT_PATHS") or "").strip()
    custom = tuple(p.strip() for p in extra.split(",") if p.strip())
    return ALWAYS_EXEMPT_PREFIXES + custom


def path_is_protected(path: str) -> bool:
    p = (path or "").rstrip("/") or "/"
    for prefix in _exempt_prefixes():
        if p.startswith(prefix.rstrip("/") or "/"):
            return False
    for prefix in PROTECTED_PREFIXES:
        if p.startswith(prefix.rstrip("/") or "/"):
            return True
    return False


# ── Firebase App Check ────────────────────────────────────────────────────────

_JWKS_URL = "https://firebaseappcheck.googleapis.com/v1/jwks"
_JWKS_TTL = 3600
_jwks_lock = threading.Lock()
_jwks_cache: dict[str, Any] = {"fetched_at": 0.0, "keys": None}


def _app_check_project_number() -> str:
    return (
        os.environ.get("FIREBASE_PROJECT_NUMBER")
        or os.environ.get("APP_CHECK_PROJECT_NUMBER")
        or ""
    ).strip()


def _load_jwks() -> Any:
    now = time.time()
    with _jwks_lock:
        if _jwks_cache["keys"] and now - _jwks_cache["fetched_at"] < _JWKS_TTL:
            return _jwks_cache["keys"]
    try:
        import requests

        resp = requests.get(_JWKS_URL, timeout=8)
        if resp.status_code != 200:
            log.warning("[appcheck] JWKS fetch status=%s", resp.status_code)
            return None
        keys = resp.json()
        with _jwks_lock:
            _jwks_cache["keys"] = keys
            _jwks_cache["fetched_at"] = now
        return keys
    except Exception as exc:
        log.warning("[appcheck] JWKS fetch failed: %s", exc)
        return None


def verify_app_check_token(token: str) -> bool:
    """Verify a Firebase App Check JWT against Google's public JWKS."""
    token = (token or "").strip()
    if not token:
        return False
    project_number = _app_check_project_number()
    if not project_number:
        log.error("[appcheck] FIREBASE_PROJECT_NUMBER not set — rejecting token")
        return False
    jwks = _load_jwks()
    if not jwks:
        return False
    try:
        from jwt import PyJWKClient  # type: ignore
        import jwt as pyjwt

        header = pyjwt.get_unverified_header(token)
        if (header.get("alg") or "").upper() != "RS256":
            return False
        signing_key = PyJWKClient(_JWKS_URL).get_signing_key_from_jwt(token)
        pyjwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=[f"projects/{project_number}"],
            issuer=f"https://firebaseappcheck.googleapis.com/{project_number}",
        )
        return True
    except Exception as exc:
        log.warning("[appcheck] token rejected: %s", exc)
        return False


# ── Combined request gate ─────────────────────────────────────────────────────


def _error(reason: str):
    from flask import jsonify

    return jsonify({"error": "attestation_failed", "reason": reason}), 403


def check_attestation_request(path: str | None = None) -> tuple[bool, tuple | None]:
    """(ok, flask_error). Fail closed on protected paths when enforcement is on."""
    if not attestation_enabled():
        return True, None

    from flask import request

    target = path if path is not None else (request.path or "")
    if request.method == "OPTIONS":
        return True, None
    if not path_is_protected(target):
        return True, None

    if play_integrity_required():
        from play_integrity import verify_play_integrity_token

        token = (request.headers.get("X-Play-Integrity") or "").strip()
        if not verify_play_integrity_token(token):
            return False, _error("play_integrity")

    if app_check_required():
        token = (
            request.headers.get("X-Firebase-AppCheck")
            or request.headers.get("X-App-Check")
            or ""
        ).strip()
        if not verify_app_check_token(token):
            return False, _error("app_check")

    return True, None


def install_attestation_guard(app) -> None:
    """Register a before_request gate on the Flask app."""

    @app.before_request
    def _attestation_gate():  # noqa: ANN202
        ok, err = check_attestation_request()
        if not ok:
            return err
        return None

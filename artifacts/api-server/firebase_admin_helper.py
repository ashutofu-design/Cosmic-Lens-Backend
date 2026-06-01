"""
Firebase Admin SDK helper.

Usage:
    from firebase_admin_helper import verify_id_token
    decoded = verify_id_token(id_token)
    phone = decoded.get("phone_number")  # e.g. "+916370082770"
    uid   = decoded.get("uid")

Configuration (env var, REQUIRED):
    FIREBASE_SERVICE_ACCOUNT_JSON  — full JSON content of the service-account
                                     key file downloaded from Firebase console
                                     (Project Settings → Service Accounts →
                                     Generate new private key).
    Optional alternatives for VPS deployment:
      FIREBASE_SERVICE_ACCOUNT_JSON_BASE64 — base64 encoded service-account JSON
      GOOGLE_APPLICATION_CREDENTIALS       — path to service-account JSON file

The init is lazy + singleton-safe: the SDK is initialized on the first call
and reused. If the env var is missing or malformed, a clear ValueError is
raised at the call site (NOT at import time) so the rest of the API keeps
working until the operator wires the secret.
"""

from __future__ import annotations

import json
import logging
import os
import base64
import threading
from typing import Any, Dict

import firebase_admin
from firebase_admin import auth as fb_auth
from firebase_admin import credentials

log = logging.getLogger(__name__)

_INIT_LOCK = threading.Lock()
_INITIALIZED = False


def _load_service_account() -> Dict[str, Any]:
    """Load Firebase service account from JSON env, base64 env, or file path."""
    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise FirebaseAuthError(
                f"FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON: {e}"
            ) from e

    raw_b64 = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON_BASE64", "").strip()
    if raw_b64:
        try:
            decoded = base64.b64decode(raw_b64).decode("utf-8")
            return json.loads(decoded)
        except Exception as e:
            raise FirebaseAuthError(
                f"FIREBASE_SERVICE_ACCOUNT_JSON_BASE64 is invalid: {e}"
            ) from e

    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if cred_path:
        try:
            with open(cred_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise FirebaseAuthError(
                f"GOOGLE_APPLICATION_CREDENTIALS file could not be read: {e}"
            ) from e

    raise FirebaseAuthError(
        "Firebase Admin credentials are not set. Add one of: "
        "FIREBASE_SERVICE_ACCOUNT_JSON, FIREBASE_SERVICE_ACCOUNT_JSON_BASE64, "
        "or GOOGLE_APPLICATION_CREDENTIALS."
    )


class FirebaseAuthError(Exception):
    """Raised when Firebase token verification fails or admin is misconfigured."""


def _ensure_initialized() -> None:
    """Idempotently initialize the Firebase Admin SDK from the service-account env var."""
    global _INITIALIZED
    if _INITIALIZED:
        return
    with _INIT_LOCK:
        if _INITIALIZED:
            return

        sa_dict = _load_service_account()

        try:
            # Reuse default app if already initialized elsewhere (hot reload safe).
            try:
                firebase_admin.get_app()
            except ValueError:
                cred = credentials.Certificate(sa_dict)
                firebase_admin.initialize_app(cred)
            _INITIALIZED = True
            log.info(
                "[firebase] Admin SDK initialized for project=%s",
                sa_dict.get("project_id", "?"),
            )
        except Exception as e:  # pragma: no cover
            raise FirebaseAuthError(f"Failed to initialize Firebase Admin: {e}") from e


def verify_id_token(id_token: str, *, check_revoked: bool = False) -> Dict[str, Any]:
    """
    Verify a Firebase ID token and return its decoded claims.

    Raises FirebaseAuthError on any failure (malformed, expired, revoked,
    mis-signed, or admin not configured). The Flask route layer should map
    that to a 401 response.

    Returned dict includes (subset):
        uid, phone_number, firebase: {sign_in_provider}, iat, exp, iss, aud
    """
    if not id_token or not isinstance(id_token, str):
        raise FirebaseAuthError("Missing ID token")

    _ensure_initialized()

    try:
        decoded = fb_auth.verify_id_token(id_token, check_revoked=check_revoked)
    except fb_auth.RevokedIdTokenError as e:
        raise FirebaseAuthError("Token has been revoked. Please sign in again.") from e
    except fb_auth.ExpiredIdTokenError as e:
        raise FirebaseAuthError("Token has expired. Please sign in again.") from e
    except fb_auth.InvalidIdTokenError as e:
        raise FirebaseAuthError(f"Invalid token: {e}") from e
    except Exception as e:
        raise FirebaseAuthError(f"Token verification failed: {e}") from e

    return decoded


def resolve_sign_in_provider(decoded: Dict[str, Any]) -> str:
    """e.g. google.com, phone, password."""
    firebase_meta = decoded.get("firebase") or {}
    return str(firebase_meta.get("sign_in_provider") or "").strip()


def resolve_email_from_decoded(decoded: Dict[str, Any]) -> str:
    """
    Extract a verified email from a Firebase ID token.
    Google tokens occasionally omit top-level `email`; fall back to identities
    and Admin SDK user lookup.
    """
    email = str(decoded.get("email") or "").strip().lower()
    if email and "@" in email:
        return email

    identities = (decoded.get("firebase") or {}).get("identities") or {}
    if isinstance(identities, dict):
        for key in ("email", "google.com"):
            vals = identities.get(key) or []
            if isinstance(vals, list):
                for v in vals:
                    s = str(v or "").strip().lower()
                    if "@" in s:
                        return s

    uid = str(decoded.get("uid") or "").strip()
    provider = resolve_sign_in_provider(decoded)
    if not uid or provider not in ("google.com", "password", "apple.com"):
        return ""

    _ensure_initialized()
    try:
        record = fb_auth.get_user(uid)
        em = str(record.email or "").strip().lower()
        if em and "@" in em:
            return em
    except Exception as e:
        log.warning("[firebase] get_user(%s) failed: %s", uid, e)

    return ""


def is_configured() -> bool:
    """Lightweight check used by health endpoints / dev guards."""
    return bool(
        os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
        or os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON_BASE64", "").strip()
        or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    )

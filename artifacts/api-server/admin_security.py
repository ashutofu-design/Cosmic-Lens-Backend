"""Admin panel hardening — panel unlock sequence, device allowlist, bound session tokens."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_UNLOCK_SEQUENCE = ("locate", "locate", "locate", "for", "for", "for")
_DEVICE_ID_RX = re.compile(r"^[a-f0-9]{16,64}$")
_STORE_LOCK = threading.Lock()

# In-memory failed-attempt counters (per IP) when limiter unavailable elsewhere.
_FAIL_BUCKETS: dict[str, list[float]] = {}


def _is_production() -> bool:
    try:
        from billing_security import is_production

        return is_production()
    except Exception:
        if os.environ.get("PROD", "").strip().lower() in ("1", "true", "yes", "on"):
            return True
        return os.environ.get("FLASK_ENV", "").strip().lower() == "production"


def admin_security_relaxed() -> bool:
    # Defence in depth: startup_security refuses to boot production with this
    # flag, but a misconfigured PROD detection must still not relax admin auth.
    if _is_production():
        return False
    return os.environ.get("ADMIN_SECURITY_RELAXED", "").strip() == "1"


def admin_allow_all_devices() -> bool:
    """When true, any valid device ID is allowed (no enroll code / cap)."""
    if _is_production():
        return False
    raw = os.environ.get("ADMIN_ALLOW_ALL_DEVICES", "0").strip().lower()
    return raw in ("1", "true", "yes", "on")


def _ensure_device_registered(device_id: str, label: str = "auto") -> None:
    did = _normalize_device_id(device_id)
    if not _valid_device_id(did):
        return
    now = datetime.now(timezone.utc).isoformat()
    with _STORE_LOCK:
        store = _load_store()
        devices = [d for d in (store.get("devices") or []) if isinstance(d, dict)]
        for item in devices:
            if _normalize_device_id(str(item.get("device_id") or "")) == did:
                item["last_seen_at"] = now
                store["devices"] = devices
                _save_store(store)
                return
        devices.append(
            {
                "device_id": did,
                "label": str(label or "auto").strip()[:80],
                "registered_at": now,
                "last_seen_at": now,
            }
        )
        store["devices"] = devices
        _save_store(store)


def admin_security_enabled() -> bool:
    try:
        from admin_dashboard import admin_no_auth

        if admin_no_auth():
            return False
    except Exception:
        pass
    if admin_security_relaxed():
        return False
    secret = _session_secret()
    return bool(secret)


def _session_secret() -> str:
    return os.environ.get("ADMIN_SECRET", "").strip()


def _gate_secret() -> str:
    explicit = os.environ.get("ADMIN_GATE_SECRET", "").strip()
    if explicit:
        return explicit
    return _session_secret()


def _max_devices() -> int:
    try:
        return max(1, min(10, int(os.environ.get("ADMIN_MAX_DEVICES", "2"))))
    except (TypeError, ValueError):
        return 2


def _gate_ttl_sec() -> int:
    try:
        return max(300, min(86_400, int(os.environ.get("ADMIN_GATE_TTL_SEC", "7200"))))
    except (TypeError, ValueError):
        return 7200


def _session_ttl_sec() -> int:
    try:
        return max(3600, min(2_592_000, int(os.environ.get("ADMIN_SESSION_TTL_SEC", "604800"))))
    except (TypeError, ValueError):
        return 604800


def _store_path() -> Path:
    raw = os.environ.get("ADMIN_DEVICE_STORE", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent / "data" / "admin_devices.json"


def _normalize_device_id(device_id: str) -> str:
    return str(device_id or "").strip().lower()


def _valid_device_id(device_id: str) -> bool:
    return bool(_DEVICE_ID_RX.match(_normalize_device_id(device_id)))


def _load_store() -> dict[str, Any]:
    path = _store_path()
    if not path.is_file():
        return {"devices": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"devices": []}
    if not isinstance(data, dict):
        return {"devices": []}
    devices = data.get("devices")
    if not isinstance(devices, list):
        data["devices"] = []
    return data


def _save_store(data: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_allowed_devices() -> list[dict[str, Any]]:
    with _STORE_LOCK:
        store = _load_store()
    out: list[dict[str, Any]] = []
    for item in store.get("devices") or []:
        if isinstance(item, dict) and item.get("device_id"):
            out.append(
                {
                    "device_id": str(item.get("device_id")),
                    "label": str(item.get("label") or ""),
                    "registered_at": str(item.get("registered_at") or ""),
                    "last_seen_at": str(item.get("last_seen_at") or ""),
                }
            )
    return out


def is_device_allowed(device_id: str) -> bool:
    if not admin_security_enabled():
        return True
    did = _normalize_device_id(device_id)
    if not _valid_device_id(did):
        return False
    if admin_allow_all_devices():
        _ensure_device_registered(did)
        return True
    with _STORE_LOCK:
        store = _load_store()
        for item in store.get("devices") or []:
            if isinstance(item, dict) and _normalize_device_id(str(item.get("device_id") or "")) == did:
                return True
    return False


def touch_device(device_id: str) -> None:
    did = _normalize_device_id(device_id)
    if not _valid_device_id(did):
        return
    now = datetime.now(timezone.utc).isoformat()
    with _STORE_LOCK:
        store = _load_store()
        changed = False
        for item in store.get("devices") or []:
            if isinstance(item, dict) and _normalize_device_id(str(item.get("device_id") or "")) == did:
                item["last_seen_at"] = now
                changed = True
                break
        if changed:
            _save_store(store)


def register_device(device_id: str, *, label: str = "", enroll_code: str = "") -> tuple[bool, str]:
    """Register a new admin device when enroll code matches."""
    if not admin_security_enabled():
        return True, "security_off"
    did = _normalize_device_id(device_id)
    if not _valid_device_id(did):
        return False, "invalid_device_id"
    if admin_allow_all_devices():
        _ensure_device_registered(did, label=label or "auto")
        return True, "auto_allowed"
    if is_device_allowed(did):
        touch_device(did)
        return True, "already_allowed"

    expected = os.environ.get("ADMIN_ENROLL_CODE", "").strip()
    if not expected or not hmac.compare_digest(str(enroll_code or ""), expected):
        return False, "enroll_code_required"

    now = datetime.now(timezone.utc).isoformat()
    with _STORE_LOCK:
        store = _load_store()
        devices = [d for d in (store.get("devices") or []) if isinstance(d, dict)]
        if any(_normalize_device_id(str(d.get("device_id") or "")) == did for d in devices):
            store["devices"] = devices
            _save_store(store)
            return True, "already_allowed"
        if len(devices) >= _max_devices():
            return False, "device_limit_reached"
        devices.append(
            {
                "device_id": did,
                "label": str(label or "").strip()[:80],
                "registered_at": now,
                "last_seen_at": now,
            }
        )
        store["devices"] = devices
        _save_store(store)
    return True, "registered"


def revoke_device(device_id: str) -> bool:
    did = _normalize_device_id(device_id)
    with _STORE_LOCK:
        store = _load_store()
        before = store.get("devices") or []
        after = [
            d
            for d in before
            if isinstance(d, dict) and _normalize_device_id(str(d.get("device_id") or "")) != did
        ]
        if len(after) == len(before):
            return False
        store["devices"] = after
        _save_store(store)
    return True


def _sign_payload(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def issue_gate_token(device_id: str) -> tuple[str, int]:
    did = _normalize_device_id(device_id)
    exp = int(time.time()) + _gate_ttl_sec()
    payload = f"{did}:{exp}"
    sig = _sign_payload(payload, _gate_secret())
    return f"{payload}:{sig}", exp


def verify_gate_token(token: str, device_id: str) -> bool:
    if not admin_security_enabled():
        return True
    secret = _gate_secret()
    if not secret:
        return False
    did = _normalize_device_id(device_id)
    parts = str(token or "").strip().split(":")
    if len(parts) != 3:
        return False
    tok_did, exp_s, sig = parts
    if tok_did != did:
        return False
    try:
        exp = int(exp_s)
    except (TypeError, ValueError):
        return False
    if exp < int(time.time()):
        return False
    payload = f"{tok_did}:{exp}"
    expected = _sign_payload(payload, secret)
    return hmac.compare_digest(sig, expected)


def issue_session_token(device_id: str) -> tuple[str, int]:
    did = _normalize_device_id(device_id)
    exp = int(time.time()) + _session_ttl_sec()
    payload = f"{did}:{exp}"
    sig = _sign_payload(payload, _session_secret())
    return f"{payload}:{sig}", exp


def verify_session_token(token: str, device_id: str) -> bool:
    if not admin_security_enabled():
        secret = _session_secret()
        return bool(secret) and hmac.compare_digest(str(token or ""), secret)
    secret = _session_secret()
    if not secret:
        return False
    did = _normalize_device_id(device_id)
    parts = str(token or "").strip().split(":")
    if len(parts) != 3:
        # Legacy shared token — reject under strict mode.
        return False
    tok_did, exp_s, sig = parts
    if tok_did != did:
        return False
    try:
        exp = int(exp_s)
    except (TypeError, ValueError):
        return False
    if exp < int(time.time()):
        return False
    payload = f"{tok_did}:{exp}"
    expected = _sign_payload(payload, secret)
    return hmac.compare_digest(sig, expected)


def validate_unlock_steps(steps: list[Any]) -> bool:
    if len(steps) != len(_UNLOCK_SEQUENCE):
        return False
    for got, want in zip(steps, _UNLOCK_SEQUENCE):
        if str(got or "").strip().lower() != want:
            return False
    return True


def is_ip_blocked(ip: str, *, window_sec: int = 900, max_fails: int = 8) -> bool:
    """Return True if IP exceeded the fail budget (read-only)."""
    key = str(ip or "unknown").strip()[:64]
    now = time.time()
    with _STORE_LOCK:
        bucket = [t for t in _FAIL_BUCKETS.get(key, []) if now - t < window_sec]
        return len(bucket) > max_fails


def record_fail(ip: str, *, window_sec: int = 900, max_fails: int = 8) -> bool:
    """Record a failed attempt; return True if IP should now be blocked."""
    key = str(ip or "unknown").strip()[:64]
    now = time.time()
    with _STORE_LOCK:
        bucket = [t for t in _FAIL_BUCKETS.get(key, []) if now - t < window_sec]
        bucket.append(now)
        _FAIL_BUCKETS[key] = bucket
        return len(bucket) > max_fails


def device_id_redacted(device_id: str) -> str:
    did = _normalize_device_id(device_id)
    if len(did) <= 8:
        return did
    return f"{did[:6]}…{did[-4:]}"

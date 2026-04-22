"""
Image-hash → session_id dedup index (Level 1: in-memory).

Same image upload within TTL returns the existing session_id, skipping
re-extraction and re-running of all 8 engines (~5-10s saved).

Optionally scoped per user_id so two different users uploading the same
photo do NOT share each other's session.

Pure-Python, thread-safe, zero deps.
"""
from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from typing import Optional

_LOCK = threading.RLock()
_STORE: "OrderedDict[str, dict]" = OrderedDict()
_MAX_ENTRIES = 500
_TTL_SECONDS = 30 * 60        # 30 minutes — matches session_cache TTL


def hash_bytes(data: bytes) -> str:
    """SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def _key(image_sha256: str, user_id: Optional[int]) -> str:
    return f"{user_id or 0}:{image_sha256}"


def lookup(image_sha256: str, user_id: Optional[int] = None) -> Optional[str]:
    """Return cached session_id if same image was analyzed within TTL, else None."""
    k = _key(image_sha256, user_id)
    with _LOCK:
        entry = _STORE.get(k)
        if entry is None:
            return None
        if time.time() - entry["ts"] > _TTL_SECONDS:
            _STORE.pop(k, None)
            return None
        _STORE.move_to_end(k)
        return entry["session_id"]


def remember(image_sha256: str, session_id: str, user_id: Optional[int] = None) -> None:
    """Record (image_hash, session_id) so future identical uploads dedupe."""
    k = _key(image_sha256, user_id)
    with _LOCK:
        _STORE[k] = {"session_id": session_id, "ts": time.time()}
        _STORE.move_to_end(k)
        _evict_locked()


def forget(image_sha256: str, user_id: Optional[int] = None) -> None:
    with _LOCK:
        _STORE.pop(_key(image_sha256, user_id), None)


def stats() -> dict:
    with _LOCK:
        return {"entries": len(_STORE), "max": _MAX_ENTRIES, "ttl_sec": _TTL_SECONDS}


def _evict_locked() -> None:
    now = time.time()
    expired = [k for k, v in _STORE.items() if now - v["ts"] > _TTL_SECONDS]
    for k in expired:
        _STORE.pop(k, None)
    while len(_STORE) > _MAX_ENTRIES:
        _STORE.popitem(last=False)

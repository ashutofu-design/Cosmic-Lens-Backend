"""
In-memory session cache for face-reading runs.

Engines 3–20 will need to re-use the foundation extraction many times.
We cache the LandmarkSet + raw RGB image (downscaled) keyed by session_id
with a TTL so the user's selfie is processed once per session.

Note: in-process only (single worker). For multi-worker deployments,
swap the dict for Redis with the same get/put interface.
"""
from __future__ import annotations

import threading
import time
import uuid
from collections import OrderedDict

_LOCK = threading.RLock()
_STORE: "OrderedDict[str, dict]" = OrderedDict()
_MAX_ENTRIES = 200
_TTL_SECONDS = 30 * 60        # 30 minutes


def new_session_id() -> str:
    return uuid.uuid4().hex


def put(session_id: str, payload: dict) -> None:
    with _LOCK:
        _STORE[session_id] = {"payload": payload, "ts": time.time()}
        _STORE.move_to_end(session_id)
        _evict_locked()


def get(session_id: str) -> dict | None:
    with _LOCK:
        entry = _STORE.get(session_id)
        if entry is None:
            return None
        if time.time() - entry["ts"] > _TTL_SECONDS:
            _STORE.pop(session_id, None)
            return None
        _STORE.move_to_end(session_id)
        return entry["payload"]


def drop(session_id: str) -> None:
    with _LOCK:
        _STORE.pop(session_id, None)


def stats() -> dict:
    with _LOCK:
        return {
            "entries": len(_STORE),
            "max":     _MAX_ENTRIES,
            "ttl_sec": _TTL_SECONDS,
        }


def _evict_locked() -> None:
    # TTL eviction
    now = time.time()
    expired = [k for k, v in _STORE.items() if now - v["ts"] > _TTL_SECONDS]
    for k in expired:
        _STORE.pop(k, None)
    # LRU eviction
    while len(_STORE) > _MAX_ENTRIES:
        _STORE.popitem(last=False)

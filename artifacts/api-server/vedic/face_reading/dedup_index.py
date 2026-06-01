"""
Image-hash → session_id dedup — Redis primary, in-memory fallback, DB via flask.

Level 1: Redis face:dedup:{user_id}:{sha256}  (90d TTL)
Level 2: in-memory OrderedDict (when Redis down)
Level 3: FaceReadingLog in PostgreSQL (flask_app analyze)
"""
from __future__ import annotations

import hashlib
import logging
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, Optional

from . import face_cache as _fc
from . import redis_manager as _rm

log = logging.getLogger(__name__)

_LOCK = threading.RLock()
_MEMORY: "OrderedDict[str, dict]" = OrderedDict()
_MEMORY_MAX = 500
_TTL_SECONDS = int(__import__("os").environ.get("FACE_DEDUP_TTL", str(90 * 24 * 3600)))


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _mem_key(image_sha256: str, user_id: Optional[int]) -> str:
    return f"{user_id or 0}:{image_sha256}"


def lookup(image_sha256: str, user_id: Optional[int] = None) -> Optional[str]:
    """Return cached session_id if known."""
    hit = _fc.get_dedup(image_sha256, user_id)
    if hit and hit.get("session_id"):
        log.debug("[dedup] Redis HIT sha=%s…", image_sha256[:8])
        return hit["session_id"]
    k = _mem_key(image_sha256, user_id)
    with _LOCK:
        entry = _MEMORY.get(k)
        if entry is None:
            return None
        if time.time() - entry["ts"] > _TTL_SECONDS:
            _MEMORY.pop(k, None)
            return None
        return entry.get("session_id")


def lookup_record(image_sha256: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Return {session_id, analysis_id?} from Redis dedup."""
    hit = _fc.get_dedup(image_sha256, user_id)
    if hit:
        return hit
    sid = lookup(image_sha256, user_id)
    if sid:
        return {"session_id": sid, "analysis_id": None}
    return None


def remember(
    image_sha256: str,
    session_id: str,
    user_id: Optional[int] = None,
    analysis_id: Optional[str] = None,
) -> None:
    _fc.put_dedup(image_sha256, session_id, user_id, analysis_id)
    k = _mem_key(image_sha256, user_id)
    with _LOCK:
        _MEMORY[k] = {
            "session_id": session_id,
            "analysis_id": analysis_id,
            "ts": time.time(),
        }
        _MEMORY.move_to_end(k)
        while len(_MEMORY) > _MEMORY_MAX:
            _MEMORY.popitem(last=False)
    log.debug(
        "[dedup] remember sha=%s… session=%s analysis=%s",
        image_sha256[:8],
        session_id[:8],
        (analysis_id or "")[:8],
    )


def forget(image_sha256: str, user_id: Optional[int] = None) -> None:
    uid = user_id if user_id is not None else 0
    prefix = (__import__("os").environ.get("FACE_REDIS_PREFIX") or "face")
    _rm.delete(f"{prefix}:dedup:{uid}:{image_sha256}")
    with _LOCK:
        _MEMORY.pop(_mem_key(image_sha256, user_id), None)


def stats() -> dict:
    return {
        "backend": "redis" if _rm.is_available() else "memory_fallback",
        "memory_entries": len(_MEMORY),
        "ttl_sec": _TTL_SECONDS,
    }

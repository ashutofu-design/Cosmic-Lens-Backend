"""
Session cache for face-reading runs — Redis-backed with in-memory fallback.

Stores landmark dicts (points included) + metadata in Redis.
Front JPEG bytes live in a separate key with shorter TTL (extract temp).

Public API unchanged: put, get, drop, stats, new_session_id
Extended: put_session, get_session, delete_session, update_session, set_ttl
"""
from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import OrderedDict
from typing import Any, Dict, Optional

from . import redis_codec as _codec
from . import redis_manager as _rm

log = logging.getLogger(__name__)

_LOCK = threading.RLock()
_MEMORY: "OrderedDict[str, dict]" = OrderedDict()
_MEMORY_MAX = int(__import__("os").environ.get("FACE_MEMORY_CACHE_MAX", "200"))

TTL_SESSION = int(__import__("os").environ.get("FACE_SESSION_TTL", str(24 * 3600)))
TTL_EXTRACT_IMG = int(__import__("os").environ.get("FACE_EXTRACT_IMG_TTL", str(2 * 3600)))

_PREFIX = (__import__("os").environ.get("FACE_REDIS_PREFIX") or "face").strip().rstrip(":")


def _session_key(session_id: str) -> str:
    return f"{_PREFIX}:session:{session_id}"


def _img_key(session_id: str) -> str:
    return f"{_PREFIX}:session:{session_id}:img:front"


def new_session_id() -> str:
    return uuid.uuid4().hex


def _encode_payload(payload: dict) -> dict:
    """Convert LandmarkSet objects → JSON-safe dicts; strip rgb_image."""
    from .landmarks import LandmarkSet, landmark_set_to_dict

    out = dict(payload)
    ls_map = out.get("landmark_sets")
    if isinstance(ls_map, dict):
        encoded = {}
        for angle, ls in ls_map.items():
            if isinstance(ls, LandmarkSet):
                encoded[angle] = landmark_set_to_dict(ls, include_points=True)
            elif isinstance(ls, dict):
                encoded[angle] = ls
        out["landmark_sets"] = encoded
    # Never persist numpy / large blobs inside main session JSON
    rp = out.get("report_payload")
    if isinstance(rp, dict):
        rp = dict(rp)
        rp.pop("front_image_bytes", None)
        out["report_payload"] = rp
    return out


def _decode_payload(data: dict) -> dict:
    """Restore LandmarkSet objects from cached dicts."""
    from .landmarks import landmark_set_from_dict

    out = dict(data)
    ls_map = out.get("landmark_sets")
    if isinstance(ls_map, dict):
        decoded = {}
        for angle, d in ls_map.items():
            if isinstance(d, dict) and "quality" in d:
                decoded[angle] = landmark_set_from_dict(d)
            else:
                decoded[angle] = d
        out["landmark_sets"] = decoded
    return out


def _memory_put(session_id: str, payload: dict) -> None:
    with _LOCK:
        _MEMORY[session_id] = {"payload": payload, "ts": time.time()}
        _MEMORY.move_to_end(session_id)
        while len(_MEMORY) > _MEMORY_MAX:
            _MEMORY.popitem(last=False)


def _memory_get(session_id: str) -> Optional[dict]:
    with _LOCK:
        entry = _MEMORY.get(session_id)
        if not entry:
            return None
        if time.time() - entry["ts"] > TTL_SESSION:
            _MEMORY.pop(session_id, None)
            return None
        _MEMORY.move_to_end(session_id)
        return entry["payload"]


def put_session(session_id: str, payload: dict, ttl_seconds: Optional[int] = None) -> None:
    put(session_id, payload, ttl_seconds=ttl_seconds)


def put(session_id: str, payload: dict, ttl_seconds: Optional[int] = None) -> None:
    ttl = ttl_seconds if ttl_seconds is not None else TTL_SESSION
    encoded = _encode_payload(payload)
    front_bytes = payload.get("front_image_bytes")
    if isinstance(front_bytes, bytes) and len(front_bytes) > 0:
        encoded.pop("front_image_bytes", None)
        if _rm.is_available():
            _rm.set_raw(_img_key(session_id), front_bytes, TTL_EXTRACT_IMG)
    raw = _codec.dumps(encoded)
    if _rm.set_raw(_session_key(session_id), raw, ttl):
        log.debug(
            "[session_cache] Redis PUT %s ~%dB ttl=%ds",
            session_id[:8],
            len(raw),
            ttl,
        )
        return
    decoded = _decode_payload(encoded)
    if isinstance(front_bytes, bytes):
        decoded["front_image_bytes"] = front_bytes
    _memory_put(session_id, decoded)
    log.debug("[session_cache] memory PUT %s (redis down)", session_id[:8])


def get_session(session_id: str) -> Optional[dict]:
    return get(session_id)


def get(session_id: str) -> Optional[dict]:
    raw = _rm.get_raw(_session_key(session_id))
    if raw is not None:
        data = _codec.loads(raw)
        if not isinstance(data, dict):
            return None
        payload = _decode_payload(data)
        img = _rm.get_raw(_img_key(session_id))
        if img:
            payload["front_image_bytes"] = img
        elif "report_payload" in payload:
            rp = payload.get("report_payload") or {}
            if isinstance(rp, dict) and rp.get("front_image_bytes"):
                payload["front_image_bytes"] = rp.get("front_image_bytes")
        log.debug("[session_cache] Redis HIT %s", session_id[:8])
        return payload
    payload = _memory_get(session_id)
    if payload:
        log.debug("[session_cache] memory HIT %s", session_id[:8])
    else:
        log.debug("[session_cache] MISS %s", session_id[:8])
    return payload


def update_session(session_id: str, patch: dict) -> Optional[dict]:
    """Merge patch into existing session; returns merged payload or None."""
    current = get(session_id)
    if current is None:
        return None
    merged = {**current, **patch}
    if "report_payload" in patch and isinstance(current.get("report_payload"), dict):
        rp = dict(current["report_payload"])
        rp.update(patch.get("report_payload") or {})
        merged["report_payload"] = rp
    put(session_id, merged)
    return merged


def delete_session(session_id: str) -> None:
    drop(session_id)


def drop(session_id: str) -> None:
    _rm.delete(_session_key(session_id))
    _rm.delete(_img_key(session_id))
    with _LOCK:
        _MEMORY.pop(session_id, None)


def set_ttl(session_id: str, ttl_seconds: int) -> bool:
    ok = _rm.expire(_session_key(session_id), ttl_seconds)
    _rm.expire(_img_key(session_id), min(ttl_seconds, TTL_EXTRACT_IMG))
    return ok


def stats() -> dict:
    from .face_cache import cache_stats

    mem_count = len(_MEMORY)
    return {
        "backend": "redis" if _rm.is_available() else "memory_fallback",
        "memory_entries": mem_count,
        "memory_max": _MEMORY_MAX,
        "ttl_session_sec": TTL_SESSION,
        "ttl_extract_img_sec": TTL_EXTRACT_IMG,
        "redis": cache_stats(),
    }

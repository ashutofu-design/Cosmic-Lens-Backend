"""
Singleton Redis connection for Face Reading caches.

Fails open: if Redis is unavailable, callers use in-memory fallback layers.
Never raises from public helpers — logs and returns None / False instead.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any, Optional

log = logging.getLogger(__name__)

_CLIENT = None
_CLIENT_LOCK = threading.Lock()
_LAST_ERROR: Optional[str] = None
_STATS = {"hits": 0, "misses": 0, "errors": 0, "latency_ms_total": 0.0, "ops": 0}


def _redis_enabled() -> bool:
    if (os.environ.get("FACE_REDIS_ENABLED") or "1").strip().lower() in (
        "0", "false", "no", "off",
    ):
        return False
    return bool((os.environ.get("REDIS_URL") or os.environ.get("FACE_REDIS_URL") or "").strip())


def _build_url() -> str:
    return (
        os.environ.get("REDIS_URL")
        or os.environ.get("FACE_REDIS_URL")
        or "redis://localhost:6379/0"
    ).strip()


def is_available() -> bool:
    """True when a live Redis client is connected."""
    return get_client() is not None


def get_client():
    """Return shared redis.Redis or None (singleton, lazy connect)."""
    global _CLIENT, _LAST_ERROR
    if not _redis_enabled():
        return None
    if _CLIENT is not None:
        return _CLIENT
    with _CLIENT_LOCK:
        if _CLIENT is not None:
            return _CLIENT
        try:
            import redis
            url = _build_url()
            _CLIENT = redis.Redis.from_url(
                url,
                decode_responses=False,
                socket_connect_timeout=float(
                    os.environ.get("REDIS_CONNECT_TIMEOUT", "3")
                ),
                socket_timeout=float(os.environ.get("REDIS_SOCKET_TIMEOUT", "5")),
                health_check_interval=30,
                retry_on_timeout=True,
            )
            _CLIENT.ping()
            log.info("[redis] connected url=%s", url.split("@")[-1])
            _LAST_ERROR = None
            return _CLIENT
        except Exception as exc:
            _LAST_ERROR = str(exc)
            _CLIENT = None
            log.warning("[redis] unavailable, using memory fallback: %s", exc)
            return None


def reconnect() -> bool:
    """Force reconnect (e.g. after connection drop)."""
    global _CLIENT
    with _CLIENT_LOCK:
        _CLIENT = None
    return get_client() is not None


def last_error() -> Optional[str]:
    return _LAST_ERROR


def _record_op(hit: bool, latency_ms: float, error: bool = False) -> None:
    if error:
        _STATS["errors"] += 1
    elif hit:
        _STATS["hits"] += 1
    else:
        _STATS["misses"] += 1
    _STATS["ops"] += 1
    _STATS["latency_ms_total"] += latency_ms


def get_raw(key: str) -> Optional[bytes]:
    """GET bytes value."""
    client = get_client()
    if client is None:
        return None
    t0 = time.perf_counter()
    try:
        val = client.get(key)
        ms = (time.perf_counter() - t0) * 1000.0
        _record_op(val is not None, ms)
        if ms > 50:
            log.debug("[redis] slow GET %s %.1fms", key[:48], ms)
        return val
    except Exception as exc:
        _record_op(False, 0, error=True)
        log.warning("[redis] GET failed %s: %s", key[:48], exc)
        reconnect()
        return None


def set_raw(key: str, value: bytes, ttl_seconds: Optional[int] = None) -> bool:
    client = get_client()
    if client is None:
        return False
    t0 = time.perf_counter()
    try:
        if ttl_seconds and ttl_seconds > 0:
            client.setex(key, int(ttl_seconds), value)
        else:
            client.set(key, value)
        ms = (time.perf_counter() - t0) * 1000.0
        _record_op(True, ms)
        return True
    except Exception as exc:
        _record_op(False, 0, error=True)
        log.warning("[redis] SET failed %s: %s", key[:48], exc)
        reconnect()
        return False


def delete(key: str) -> bool:
    client = get_client()
    if client is None:
        return False
    try:
        client.delete(key)
        return True
    except Exception:
        reconnect()
        return False


def expire(key: str, ttl_seconds: int) -> bool:
    client = get_client()
    if client is None:
        return False
    try:
        client.expire(key, int(ttl_seconds))
        return True
    except Exception:
        reconnect()
        return False


def incr(key: str, ttl_seconds: Optional[int] = None) -> Optional[int]:
    """INCR with optional TTL on first write."""
    client = get_client()
    if client is None:
        return None
    try:
        pipe = client.pipeline()
        pipe.incr(key)
        if ttl_seconds:
            pipe.expire(key, int(ttl_seconds), nx=True)
        results = pipe.execute()
        return int(results[0])
    except Exception:
        reconnect()
        return None


def publish(channel: str, message: bytes) -> bool:
    """PUBLISH bytes to a Redis channel (progress events)."""
    client = get_client()
    if client is None:
        return False
    try:
        client.publish(channel, message)
        return True
    except Exception as exc:
        log.warning("[redis] PUBLISH failed %s: %s", channel[:48], exc)
        reconnect()
        return False


def set_nx_raw(key: str, value: bytes, ttl_seconds: int) -> bool:
    """SET if not exists — used for PDF generation locks."""
    client = get_client()
    if client is None:
        return False
    try:
        return bool(client.set(key, value, nx=True, ex=int(ttl_seconds)))
    except Exception:
        reconnect()
        return False


def stats() -> dict:
    avg_ms = (
        _STATS["latency_ms_total"] / _STATS["ops"]
        if _STATS["ops"] else 0.0
    )
    return {
        "available": is_available(),
        "last_error": _LAST_ERROR,
        "hits": _STATS["hits"],
        "misses": _STATS["misses"],
        "errors": _STATS["errors"],
        "ops": _STATS["ops"],
        "avg_latency_ms": round(avg_ms, 2),
        "url_host": _build_url().split("@")[-1] if _redis_enabled() else None,
    }

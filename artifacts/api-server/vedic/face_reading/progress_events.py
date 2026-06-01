"""
Face PDF job progress — Redis state + pub/sub for SSE/WebSocket clients.

Keys:
  face:progress:{job_id}     — latest event JSON (TTL = FACE_PDF_JOB_TTL)
Channel:
  face:progress:ch:{job_id}  — pub/sub fan-out
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Any, Dict, Iterator, Optional

from . import redis_codec as _codec
from . import redis_manager as _rm

log = logging.getLogger(__name__)

_PREFIX = (os.environ.get("FACE_REDIS_PREFIX") or "face").strip().rstrip(":")
_TTL = int(os.environ.get("FACE_PDF_JOB_TTL", str(3600)))


def job_id(session_id: str, lang: str) -> str:
    return f"{session_id}:{lang}"


def _progress_key(jid: str) -> str:
    return f"{_PREFIX}:progress:{jid}"


def _channel(jid: str) -> str:
    return f"{_PREFIX}:progress:ch:{jid}"


def emit(
    jid: str,
    stage: str,
    percent: int,
    *,
    status: str = "processing",
    message: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Persist + publish one progress event."""
    evt = {
        "job_id": jid,
        "event_id": uuid.uuid4().hex[:12],
        "status": status,
        "stage": stage,
        "percent": max(0, min(100, int(percent))),
        "message": message,
        "ts": time.time(),
        **(extra or {}),
    }
    raw = _codec.dumps(evt)
    _rm.set_raw(_progress_key(jid), raw, _TTL)
    _rm.publish(_channel(jid), raw)
    log.debug(
        "[progress] %s %s %d%% %s",
        jid[:16],
        stage,
        evt["percent"],
        status,
    )
    return evt


def get_latest(jid: str) -> Optional[Dict[str, Any]]:
    raw = _rm.get_raw(_progress_key(jid))
    if not raw:
        return None
    data = _codec.loads(raw)
    return data if isinstance(data, dict) else None


def subscribe(jid: str, timeout_seconds: float = 120.0) -> Iterator[Dict[str, Any]]:
    """Blocking iterator for SSE/WebSocket — yields decoded events."""
    client = _rm.get_client()
    if client is None:
        latest = get_latest(jid)
        if latest:
            yield latest
        return

    import redis

    pubsub = client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(_channel(jid))
    deadline = time.time() + timeout_seconds
    try:
        latest = get_latest(jid)
        if latest:
            yield latest
            if latest.get("status") in ("ready", "failed"):
                return

        while time.time() < deadline:
            msg = pubsub.get_message(timeout=1.0)
            if not msg or msg.get("type") != "message":
                continue
            data = msg.get("data")
            if isinstance(data, bytes):
                evt = _codec.loads(data)
            else:
                continue
            if isinstance(evt, dict):
                yield evt
                if evt.get("status") in ("ready", "failed"):
                    break
    finally:
        try:
            pubsub.unsubscribe(_channel(jid))
            pubsub.close()
        except Exception:
            pass

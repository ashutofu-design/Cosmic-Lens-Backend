"""
Face Reading Redis cache layers (analysis, narration, PDF meta, tokens, rate limits).

Keys (prefix FACE_REDIS_PREFIX or default 'face'):
  face:session:{session_id}           — session metadata + report_payload (no image bytes)
  face:session:{session_id}:img:front — front JPEG bytes, TTL extract
  face:dedup:{user_id}:{sha256}       — session_id + analysis_id
  face:analysis:{analysis_id}         — immutable analyze snapshot
  face:narration:{analysis_id}:{lang} — assembled report sans images
  face:pdf:{analysis_id}:{lang}         — PDF file path metadata
  face:job:pdf:{session_id}:{lang}    — in-flight PDF job state
  face:ratelimit:{endpoint}:{ip}      — rate limit counters
  face:token:daily:{yyyy-mm-dd}       — global daily spend USD
  face:token:user:{uid}:{date}        — per-user daily spend
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Any, Dict, Optional

from . import redis_codec as _codec
from . import redis_manager as _rm

log = logging.getLogger(__name__)

_PREFIX = (os.environ.get("FACE_REDIS_PREFIX") or "face").strip().rstrip(":")

TTL_SESSION = int(os.environ.get("FACE_SESSION_TTL", str(24 * 3600)))
TTL_EXTRACT_IMG = int(os.environ.get("FACE_EXTRACT_IMG_TTL", str(2 * 3600)))
TTL_ANALYSIS = int(os.environ.get("FACE_ANALYSIS_TTL", str(24 * 3600)))
TTL_NARRATION = int(os.environ.get("FACE_NARRATION_TTL", str(30 * 24 * 3600)))
TTL_PDF_META = int(os.environ.get("FACE_PDF_META_TTL", str(30 * 24 * 3600)))
TTL_DEDUP = int(os.environ.get("FACE_DEDUP_TTL", str(90 * 24 * 3600)))
TTL_JOB = int(os.environ.get("FACE_PDF_JOB_TTL", str(3600)))


def _k(*parts: str) -> str:
    return f"{_PREFIX}:" + ":".join(str(p) for p in parts if p is not None and str(p) != "")


def new_analysis_id() -> str:
    return uuid.uuid4().hex


# ── Analysis snapshot ───────────────────────────────────────────────────────
def put_analysis(analysis_id: str, snapshot: Dict[str, Any]) -> bool:
    snap = dict(snapshot)
    snap["analysis_id"] = analysis_id
    snap.setdefault("cached_at", time.time())
    raw = _codec.dumps(snap)
    ok = _rm.set_raw(_k("analysis", analysis_id), raw, TTL_ANALYSIS)
    if ok:
        log.info(
            "[face_cache] analysis stored id=%s size=%dB",
            analysis_id[:8],
            len(raw),
        )
    return ok


def get_analysis(analysis_id: str) -> Optional[Dict[str, Any]]:
    raw = _rm.get_raw(_k("analysis", analysis_id))
    if raw is None:
        log.debug("[face_cache] analysis MISS id=%s", analysis_id[:8])
        return None
    log.debug("[face_cache] analysis HIT id=%s", analysis_id[:8])
    return _codec.loads(raw)


# ── Per-language narration / assembled report (L3) ───────────────────────────
def put_narration(
    analysis_id: str,
    lang: str,
    report: Dict[str, Any],
    *,
    narration_version: Optional[str] = None,
    render_version: Optional[str] = None,
) -> bool:
    from .report_version import NARRATION_VERSION, PDF_RENDER_VERSION

    slim = _slim_report_for_cache(report)
    payload = {
        "lang": lang,
        "report": slim,
        "cached_at": time.time(),
        "narration_version": narration_version or NARRATION_VERSION,
        "render_version": render_version or PDF_RENDER_VERSION,
    }
    raw = _codec.dumps(payload)
    ok = _rm.set_raw(_k("narration", analysis_id, lang), raw, TTL_NARRATION)
    if ok:
        delete_pdf_artifact(analysis_id, lang)
    return ok


def get_narration(analysis_id: str, lang: str) -> Optional[Dict[str, Any]]:
    """Legacy getter — no version check."""
    data = _get_narration_payload(analysis_id, lang)
    if isinstance(data, dict):
        return data.get("report")
    return None


def get_narration_versioned(analysis_id: str, lang: str) -> Optional[Dict[str, Any]]:
    """L3 hit only when narration_version matches."""
    from .report_version import narration_cache_valid

    data = _get_narration_payload(analysis_id, lang)
    if not isinstance(data, dict):
        return None
    if not narration_cache_valid(data.get("narration_version")):
        log.debug(
            "[face_cache] narration STALE %s/%s ver=%s",
            analysis_id[:8],
            lang,
            data.get("narration_version"),
        )
        return None
    log.debug("[face_cache] narration HIT %s/%s", analysis_id[:8], lang)
    return data.get("report")


def _get_narration_payload(analysis_id: str, lang: str) -> Optional[Dict[str, Any]]:
    raw = _rm.get_raw(_k("narration", analysis_id, lang))
    if raw is None:
        return None
    data = _codec.loads(raw)
    return data if isinstance(data, dict) else None


# ── Canonical insights (L2b) — English Pass A, all languages derive ────────
def put_canonical_insights(analysis_id: str, pass_a: Dict[str, Any], version: str) -> bool:
    raw = _codec.dumps(
        {"pass_a": pass_a, "version": version, "cached_at": time.time()}
    )
    return _rm.set_raw(_k("insights", "canonical", analysis_id), raw, TTL_NARRATION)


def get_canonical_insights(analysis_id: str) -> Optional[Dict[str, Any]]:
    from .report_version import insights_cache_valid

    raw = _rm.get_raw(_k("insights", "canonical", analysis_id))
    if not raw:
        return None
    data = _codec.loads(raw)
    if not isinstance(data, dict) or not insights_cache_valid(data.get("version")):
        return None
    return data.get("pass_a")


def put_insights_lang(analysis_id: str, lang: str, pass_a: Dict[str, Any], version: str) -> bool:
    raw = _codec.dumps({"pass_a": pass_a, "version": version, "cached_at": time.time()})
    return _rm.set_raw(_k("insights", analysis_id, lang), raw, TTL_NARRATION)


def get_insights_lang(analysis_id: str, lang: str) -> Optional[Dict[str, Any]]:
    from .report_version import insights_cache_valid

    raw = _rm.get_raw(_k("insights", analysis_id, lang))
    if not raw:
        return None
    data = _codec.loads(raw)
    if not isinstance(data, dict) or not insights_cache_valid(data.get("version")):
        return None
    return data.get("pass_a")


# ── PDF artifact extras (checksum, render version) ─────────────────────────
def put_pdf_artifact_extras(analysis_id: str, lang: str, extras: Dict[str, Any]) -> bool:
    return _rm.set_raw(
        _k("pdf", "artifact", analysis_id, lang),
        _codec.dumps(extras),
        TTL_PDF_META,
    )


def get_pdf_artifact_extras(analysis_id: str, lang: str) -> Optional[Dict[str, Any]]:
    raw = _rm.get_raw(_k("pdf", "artifact", analysis_id, lang))
    return _codec.loads(raw) if raw else None


def delete_pdf_artifact(analysis_id: str, lang: str) -> None:
    _rm.delete(_k("pdf", analysis_id, lang))
    _rm.delete(_k("pdf", "artifact", analysis_id, lang))


def _slim_report_for_cache(report: Dict[str, Any]) -> Dict[str, Any]:
    """Drop bytes and engine blobs from cached report."""
    out = dict(report)
    out.pop("front_image_bytes", None)
    out.pop("engines", None)
    return out


# ── PDF metadata (points to report_cache disk file) ─────────────────────────
def put_pdf_meta(
    analysis_id: str,
    lang: str,
    *,
    ledger_id: str,
    path: str,
    filename: str,
    size_bytes: int,
) -> bool:
    meta = {
        "ledger_id": ledger_id,
        "path": path,
        "filename": filename,
        "size_bytes": size_bytes,
        "cached_at": time.time(),
    }
    raw = _codec.dumps(meta)
    return _rm.set_raw(_k("pdf", analysis_id, lang), raw, TTL_PDF_META)


def get_pdf_meta(analysis_id: str, lang: str) -> Optional[Dict[str, Any]]:
    raw = _rm.get_raw(_k("pdf", analysis_id, lang))
    if raw is None:
        return None
    log.debug("[face_cache] pdf meta HIT %s/%s", analysis_id[:8], lang)
    return _codec.loads(raw)


# ── PDF job state (async-ready) ─────────────────────────────────────────────
def set_pdf_job(session_id: str, lang: str, status: str, **extra: Any) -> bool:
    payload = {"status": status, "updated_at": time.time(), **extra}
    raw = _codec.dumps(payload)
    return _rm.set_raw(_k("job", "pdf", session_id, lang), raw, TTL_JOB)


def get_pdf_job(session_id: str, lang: str) -> Optional[Dict[str, Any]]:
    raw = _rm.get_raw(_k("job", "pdf", session_id, lang))
    return _codec.loads(raw) if raw else None


def pdf_lock_key(analysis_id: str, lang: str) -> str:
    return _k("lock", "pdf", analysis_id, lang)


def try_acquire_pdf_lock(
    analysis_id: str,
    lang: str,
    owner: str,
    ttl_seconds: Optional[int] = None,
) -> bool:
    """One active PDF build per analysis_id + lang."""
    ttl = ttl_seconds or TTL_JOB
    return _rm.set_nx_raw(
        pdf_lock_key(analysis_id, lang),
        _codec.dumps({"owner": owner, "ts": time.time()}),
        ttl,
    )


def release_pdf_lock(analysis_id: str, lang: str) -> None:
    _rm.delete(pdf_lock_key(analysis_id, lang))


def celery_task_id(session_id: str, lang: str) -> str:
    """Stable Celery task id for deduplicated enqueue."""
    return f"face-pdf-{session_id}-{lang}"


# ── Dedup (Redis layer — used by dedup_index.py) ────────────────────────────
def put_dedup(
    image_sha256: str,
    session_id: str,
    user_id: Optional[int] = None,
    analysis_id: Optional[str] = None,
) -> bool:
    uid = user_id if user_id is not None else 0
    payload = {
        "session_id": session_id,
        "analysis_id": analysis_id,
        "ts": time.time(),
    }
    raw = _codec.dumps(payload)
    return _rm.set_raw(_k("dedup", str(uid), image_sha256), raw, TTL_DEDUP)


def get_dedup(image_sha256: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    uid = user_id if user_id is not None else 0
    raw = _rm.get_raw(_k("dedup", str(uid), image_sha256))
    return _codec.loads(raw) if raw else None


# ── Token budget (USD floats as strings) ────────────────────────────────────
def _today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def record_token_spend(usd: float, user_id: Optional[int] = None) -> None:
    if usd <= 0:
        return
    day = _today()
    ttl = 48 * 3600
    key_d = _k("token", "daily", day)
    cur = _rm.get_raw(key_d)
    total = float(_codec.loads(cur) or 0) + usd
    _rm.set_raw(key_d, _codec.dumps(round(total, 6)), ttl)
    if user_id:
        key_u = _k("token", "user", str(user_id), day)
        cur_u = _rm.get_raw(key_u)
        total_u = float(_codec.loads(cur_u) or 0) + usd
        _rm.set_raw(key_u, _codec.dumps(round(total_u, 6)), ttl)


def get_daily_spend(user_id: Optional[int] = None) -> float:
    day = _today()
    if user_id:
        raw = _rm.get_raw(_k("token", "user", str(user_id), day))
        if raw:
            return float(_codec.loads(raw) or 0)
    raw = _rm.get_raw(_k("token", "daily", day))
    return float(_codec.loads(raw) or 0) if raw else 0.0


def is_daily_token_capped(user_id: Optional[int] = None) -> bool:
    cap = float(os.environ.get("OPENAI_DAILY_CAP_USD", "15"))
    user_cap = float(os.environ.get("FACE_USER_DAILY_CAP_USD", "2"))
    if get_daily_spend() >= cap:
        return True
    if user_id and get_daily_spend(user_id) >= user_cap:
        return True
    return False


# ── Rate limit (Redis INCR per window) ────────────────────────────────────
def check_rate_limit(bucket: str, limit: int, window_seconds: int = 60) -> bool:
    """
    Return True if request is ALLOWED, False if rate limited.
    Falls open (allow) when Redis unavailable.
    """
    key = _k("ratelimit", bucket)
    n = _rm.incr(key, ttl_seconds=window_seconds)
    if n is None:
        return True
    return n <= limit


def cache_stats() -> Dict[str, Any]:
    return {
        "redis": _rm.stats(),
        "ttl": {
            "session": TTL_SESSION,
            "extract_img": TTL_EXTRACT_IMG,
            "analysis": TTL_ANALYSIS,
            "narration": TTL_NARRATION,
            "pdf_meta": TTL_PDF_META,
            "dedup": TTL_DEDUP,
        },
        "prefix": _PREFIX,
    }

"""Cosmic Intelligence V3 — live timed sessions with FIFO queue + user handoff.

Statuses (migrate-compatible):
  queued | pending(legacy→queued) → awaiting_user → accepted → ended | rejected

Flow:
  1. User request always creates a durable `queued` session (even if admin offline
     or another consultation is live). Waitlist size is unlimited — any number of
     users may join the FIFO queue while one session is in progress.
  2. Admin Accept moves queue-head to `awaiting_user` (timer NOT started) + push user.
  3. User Accept starts the timer (`accepted`). Only one live session at a time.
  4. If user does not accept within AWAITING_USER_SECONDS → requeue to end of FIFO.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

_BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".cache", "cosmic_intelligence_v3_sessions")
)
_UPLOADS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".cache", "v3_uploads")
)
_SETTINGS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".cache", "cosmic_intelligence_v3_settings.json")
)
_lock = threading.Lock()
log = logging.getLogger("cosmic_v3_sessions")

PACKS: dict[str, dict[str, Any]] = {
    "15": {"minutes": 15, "price_inr": 399, "label": "15 min"},
    "30": {"minutes": 30, "price_inr": 699, "label": "30 min"},
    "45": {"minutes": 45, "price_inr": 999, "label": "45 min"},
    "60": {"minutes": 60, "price_inr": 1299, "label": "60 min"},
}

MAX_EXTEND_SECONDS = 180
DEFAULT_EXTEND_SECONDS = 120
RESUME_MIN_SECONDS = 300  # 5 min
AWAITING_USER_SECONDS = 120  # 2 min — then requeue to end
# None = unlimited waitlist. Do not set a cap — any number of users may queue
# while one consultation is live (or while admin is offline).
QUEUE_MAX_SIZE: int | None = None

# Treat legacy "pending" as queued for FIFO / filters.
_QUEUE_STATUSES = frozenset({"queued", "pending"})
_BUSY_STATUSES = frozenset({"awaiting_user", "accepted"})

_USER_DETAILS_MARKER = "Below are my details"


def _session_has_user_details_intro(rec: dict[str, Any]) -> bool:
    for m in rec.get("messages") or []:
        if not isinstance(m, dict):
            continue
        if str(m.get("kind") or "") == "user_birth_intro":
            return True
        text = str(m.get("text") or "")
        if m.get("sender") == "user" and _USER_DETAILS_MARKER.lower() in text.lower():
            return True
    return False


def _build_v3_user_details_intro(
    user_id: int,
    *,
    fallback_name: str = "",
    cosmo_id: str = "",
) -> str:
    """Build the auto first message for admin live chat (name / gender / DOB / time / place)."""
    name = (fallback_name or "").strip()
    gender = ""
    dob = ""
    tob = ""
    place = ""
    try:
        from admin_dashboard import _parse_birth_data
        from models import Kundli, Profile, User

        uid = int(user_id)
        profiles = (
            Profile.query.filter_by(user_id=uid)
            .filter(Profile.deleted_at.is_(None))
            .order_by(Profile.is_primary.desc(), Profile.id.asc())
            .all()
        )
        profile = next((p for p in profiles if p.is_primary), None) or (
            profiles[0] if profiles else None
        )
        if profile is not None:
            birth = _parse_birth_data(getattr(profile, "birth_data", None))
            name = (profile.name or name or "").strip()
            gender = (profile.gender or birth.get("gender") or "").strip()
            dob = str(birth.get("dob") or "").strip()
            tob = str(birth.get("tob") or "").strip()
            place = str(birth.get("place") or "").strip()

        if not dob or not tob or not place or not name:
            legacy = Kundli.query.filter_by(user_id=uid).first()
            if legacy is not None:
                if not name:
                    name = (legacy.name or "").strip()
                if not dob:
                    dob = (legacy.dob or "").strip()
                if not tob:
                    tob = (legacy.tob or "").strip()
                if not place:
                    place = (legacy.pob or "").strip()

        if not name:
            user = User.query.get(uid)
            if user is not None:
                name = (getattr(user, "name", None) or "").strip()
    except Exception:
        log.exception("[v3] failed building user details intro for user_id=%s", user_id)

    lines = [
        "Hi Cosmo,",
        "Below are my details",
        "",
    ]
    cid = (cosmo_id or "").strip()
    if cid:
        lines.append(f"Cosmo ID: {cid}")
    lines.extend(
        [
            f"Name: {name or '—'}",
            f"Gender: {gender or '—'}",
            f"DOB: {dob or '—'}",
            f"Time: {tob or '—'}",
            f"Place: {place or '—'}",
        ]
    )
    return "\n".join(lines)


def _ensure_v3_user_details_intro(
    rec: dict[str, Any],
    *,
    now: datetime | None = None,
) -> bool:
    """Append birth-details intro as a user message once. Returns True if added."""
    if _session_has_user_details_intro(rec):
        return False
    uid = int(rec.get("user_id") or 0)
    if uid <= 0:
        return False
    text = _build_v3_user_details_intro(
        uid,
        fallback_name=str(rec.get("user_name") or ""),
        cosmo_id=str(rec.get("cosmo_user_id") or ""),
    )
    if not text.strip():
        return False
    if not isinstance(rec.get("messages"), list):
        rec["messages"] = []
    rec["messages"].append(
        {
            "id": str(uuid.uuid4()),
            "sender": "user",
            "kind": "user_birth_intro",
            "text": text,
            "image_url": "",
            "ts": _iso(now) if now else _iso(),
        }
    )
    rec["messages"] = rec["messages"][-500:]
    return True


def get_v3_chat_settings() -> dict[str, Any]:
    """Return the admin-controlled V3 request availability."""
    try:
        with open(_SETTINGS_PATH, encoding="utf-8") as fh:
            raw = json.load(fh)
        enabled = bool(raw.get("enabled")) if isinstance(raw, dict) else False
        updated_at = raw.get("updated_at") if isinstance(raw, dict) else None
    except (OSError, ValueError, TypeError):
        enabled = False
        updated_at = None
    return {"enabled": enabled, "updated_at": updated_at}


_blocked_attempts: dict[int, list[float]] = {}
_BLOCKED_WINDOW_SECONDS = 15 * 60


def record_blocked_v3_attempt(user_id: int) -> int:
    """Record a connect attempt while chat is closed; return attempt # in window."""
    import time as _time

    now = _time.time()
    with _lock:
        hits = [t for t in _blocked_attempts.get(int(user_id), []) if now - t < _BLOCKED_WINDOW_SECONDS]
        hits.append(now)
        _blocked_attempts[int(user_id)] = hits
        return len(hits)


def set_v3_chat_enabled(enabled: bool) -> dict[str, Any]:
    _ensure_dir()
    settings = {"enabled": bool(enabled), "updated_at": _iso()}
    tmp = f"{_SETTINGS_PATH}.tmp"
    with _lock:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(settings, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, _SETTINGS_PATH)
    return settings


def _ensure_dir() -> None:
    try:
        os.makedirs(_BASE, exist_ok=True)
        os.makedirs(_UPLOADS, exist_ok=True)
    except Exception:
        pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _now()).isoformat()


def _parse_iso(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        s = str(raw).strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _normalize_status(status: str | None) -> str:
    s = (status or "").strip().lower()
    if s == "pending":
        return "queued"
    return s


def _is_queued(rec: dict[str, Any]) -> bool:
    return _normalize_status(rec.get("status")) == "queued"


def _queue_sort_key(rec: dict[str, Any]) -> str:
    return str(rec.get("queued_at") or rec.get("created_at") or "")


def _save(record: dict) -> str:
    _ensure_dir()
    sid = record.get("session_id") or str(uuid.uuid4())
    record["session_id"] = sid
    path = os.path.join(_BASE, f"{sid}.json")
    with _lock:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=2)
    try:
        print(
            f"[v3_live] saved id={sid} status={record.get('status')} "
            f"user={record.get('user_id')} pack={record.get('pack_id')}",
            flush=True,
        )
    except Exception:
        pass
    return sid


def _load(session_id: str) -> dict[str, Any] | None:
    _ensure_dir()
    path = os.path.join(_BASE, f"{(session_id or '').strip()}.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            rec = json.load(fh)
        return rec if isinstance(rec, dict) else None
    except Exception:
        return None


def _iter_all_records() -> list[dict[str, Any]]:
    _ensure_dir()
    out: list[dict[str, Any]] = []
    try:
        names = [n for n in os.listdir(_BASE) if n.endswith(".json")]
    except OSError:
        return out
    for name in names:
        try:
            with open(os.path.join(_BASE, name), encoding="utf-8") as fh:
                rec = json.load(fh)
            if isinstance(rec, dict):
                out.append(rec)
        except Exception:
            continue
    return out


def _remaining_seconds(rec: dict[str, Any]) -> int | None:
    exp = _parse_iso(rec.get("expires_at"))
    if not exp:
        return None
    return max(0, int((exp - _now()).total_seconds()))


def _awaiting_user_remaining(rec: dict[str, Any]) -> int | None:
    if _normalize_status(rec.get("status")) != "awaiting_user":
        return None
    exp = _parse_iso(rec.get("awaiting_user_expires_at"))
    if not exp:
        return None
    return max(0, int((exp - _now()).total_seconds()))


def _requeue_awaiting_user(rec: dict[str, Any], *, reason: str = "user_accept_timeout") -> dict[str, Any]:
    """Move awaiting_user back to end of FIFO queue (no timer started)."""
    now = _iso()
    rec["status"] = "queued"
    rec["queued_at"] = now
    rec["updated_at"] = now
    rec["awaiting_user_at"] = None
    rec["awaiting_user_expires_at"] = None
    rec["accepted_at"] = None
    rec["accepted_by"] = None
    rec["started_at"] = None
    rec["expires_at"] = None
    rec["requeue_count"] = int(rec.get("requeue_count") or 0) + 1
    rec["last_requeue_reason"] = reason
    msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
    msgs.append(
        {
            "id": str(uuid.uuid4()),
            "sender": "system",
            "text": "User did not accept in time — returned to waiting queue.",
            "image_url": "",
            "ts": now,
        }
    )
    rec["messages"] = msgs[-500:]
    _save(rec)
    try:
        alert_admin_for_queue_head_if_idle()
    except Exception:
        pass
    return rec


def _maybe_expire(rec: dict[str, Any]) -> dict[str, Any]:
    """Expire live timer OR awaiting_user handoff timeout."""
    status = _normalize_status(rec.get("status"))

    if status == "awaiting_user":
        rem = _awaiting_user_remaining(rec)
        if rem is not None and rem <= 0:
            return _requeue_awaiting_user(rec, reason="user_accept_timeout")
        return rec

    if status != "accepted":
        # Migrate legacy pending → queued in memory (persist on next write).
        if (rec.get("status") or "") == "pending":
            rec["status"] = "queued"
            if not rec.get("queued_at"):
                rec["queued_at"] = rec.get("created_at") or _iso()
        return rec

    rem = _remaining_seconds(rec)
    if rem is not None and rem <= 0:
        ended = end_v3_session(str(rec.get("session_id") or ""), reason="timer_expired")
        return ended or rec
    return rec


def queue_position_for(session_id: str) -> int | None:
    """1-based FIFO position among queued sessions, or None if not queued."""
    sid = (session_id or "").strip()
    if not sid:
        return None
    queued = []
    for rec in _iter_all_records():
        rec = _maybe_expire(dict(rec))
        if _is_queued(rec):
            queued.append(rec)
    queued.sort(key=_queue_sort_key)
    for i, rec in enumerate(queued, start=1):
        if str(rec.get("session_id") or "") == sid:
            return i
    return None


def has_active_or_awaiting_v3_session() -> bool:
    """True when a live chat or awaiting-user handoff is already in progress."""
    for rec in _iter_all_records():
        rec = _maybe_expire(dict(rec))
        if _normalize_status(rec.get("status")) in _BUSY_STATUSES:
            return True
    return False


def get_queue_head() -> dict[str, Any] | None:
    """Oldest queued session (after applying timeouts)."""
    queued: list[dict[str, Any]] = []
    for rec in _iter_all_records():
        rec = _maybe_expire(dict(rec))
        if _is_queued(rec):
            queued.append(rec)
    if not queued:
        return None
    queued.sort(key=_queue_sort_key)
    return queued[0]


def _public_session(rec: dict[str, Any]) -> dict[str, Any]:
    rec = _maybe_expire(dict(rec))
    status = _normalize_status(rec.get("status"))
    used = int(rec.get("extend_seconds_used") or 0)
    pos = queue_position_for(str(rec.get("session_id") or "")) if status == "queued" else None
    awaiting_rem = _awaiting_user_remaining(rec)
    return {
        "session_id": rec.get("session_id"),
        "created_at": rec.get("created_at"),
        "queued_at": rec.get("queued_at") or rec.get("created_at"),
        "updated_at": rec.get("updated_at"),
        "status": status,
        "minutes": rec.get("minutes"),
        "price_inr": rec.get("price_inr"),
        "label": rec.get("label"),
        "pack_id": rec.get("pack_id"),
        "accepted_at": rec.get("accepted_at"),
        "awaiting_user_at": rec.get("awaiting_user_at"),
        "awaiting_user_expires_at": rec.get("awaiting_user_expires_at"),
        "awaiting_user_remaining_seconds": awaiting_rem,
        "started_at": rec.get("started_at"),
        "expires_at": rec.get("expires_at"),
        "remaining_seconds": _remaining_seconds(rec),
        "extend_seconds_used": used,
        "extend_seconds_left": max(0, MAX_EXTEND_SECONDS - used),
        "max_extend_seconds": MAX_EXTEND_SECONDS,
        "ended_at": rec.get("ended_at"),
        "user_id": rec.get("user_id"),
        "cosmo_user_id": rec.get("cosmo_user_id") or "",
        "user_name": rec.get("user_name") or "",
        "user_email": rec.get("user_email") or "",
        "preferred_language": rec.get("preferred_language") or "",
        "message_count": len(rec.get("messages") or []),
        "queue_position": pos,
        "is_queue_head": pos == 1,
        "requeue_count": int(rec.get("requeue_count") or 0),
        "engine_busy": has_active_or_awaiting_v3_session(),
    }


def create_v3_session_request(
    *,
    user_id: int,
    pack_id: str,
    user_email: str = "",
    user_phone: str = "",
    user_name: str = "",
    cosmo_user_id: str = "",
    preferred_language: str = "",
) -> dict[str, Any]:
    """Enqueue a V3 request. Always succeeds into `queued` (unlimited waitlist).

    - One open request per user (reuse existing queued/awaiting/live).
    - No global queue size limit (`QUEUE_MAX_SIZE is None`).
    - Safe while another session is live or chat is offline.
    """
    pack = PACKS.get((pack_id or "").strip())
    if not pack:
        raise ValueError("invalid_pack")

    # One open request per user — return existing queued/awaiting/live instead of duplicate.
    existing = find_active_v3_session_for_user(int(user_id), as_record=True)
    if existing:
        out = dict(existing)
        out["_reused"] = True
        return out

    lang = (preferred_language or "").strip().lower()
    if lang in ("english", "en"):
        lang = "en"
    elif lang in ("hindi", "hi"):
        lang = "hi"
    elif lang in ("hinglish", "hn", "hi-en", "hi_en"):
        lang = "hn"
    elif lang not in ("en", "hi", "hn"):
        lang = ""
    now = _iso()
    record: dict[str, Any] = {
        "session_id": str(uuid.uuid4()),
        "created_at": now,
        "queued_at": now,
        "updated_at": now,
        "user_id": user_id,
        "cosmo_user_id": cosmo_user_id or "",
        "user_email": (user_email or "")[:200],
        "user_phone": (user_phone or "")[:40],
        "user_name": (user_name or "")[:120],
        "preferred_language": lang,
        "pack_id": pack_id,
        "minutes": pack["minutes"],
        "price_inr": pack["price_inr"],
        "label": pack["label"],
        "status": "queued",
        "payment": "waived_preview",
        "accepted_at": None,
        "accepted_by": None,
        "awaiting_user_at": None,
        "awaiting_user_expires_at": None,
        "started_at": None,
        "expires_at": None,
        "extend_seconds_used": 0,
        "requeue_count": 0,
        "messages": [],
    }
    _save(record)
    record["_reused"] = False
    return record


def get_v3_session(session_id: str) -> dict[str, Any] | None:
    rec = _load(session_id)
    if not rec:
        return None
    return _maybe_expire(rec)


def admin_ready_v3_session(session_id: str, *, admin_note: str = "") -> dict[str, Any]:
    """Admin Accept → notify user; timer does NOT start yet.

    Returns {ok, session|error, ...}.
    """
    rec = _load(session_id)
    if not rec:
        return {"ok": False, "error": "not_found"}
    rec = _maybe_expire(rec)
    status = _normalize_status(rec.get("status"))

    if status == "awaiting_user":
        return {"ok": True, "session": rec, "already": True}
    if status == "accepted" and rec.get("expires_at"):
        return {"ok": True, "session": _maybe_expire(rec), "already_live": True}
    if status != "queued":
        return {"ok": False, "error": "not_queued", "status": status}

    # One handoff / live chat at a time.
    if has_active_or_awaiting_v3_session():
        return {"ok": False, "error": "engine_busy", "status": status}

    head = get_queue_head()
    if not head or str(head.get("session_id")) != str(rec.get("session_id")):
        return {
            "ok": False,
            "error": "not_queue_head",
            "queue_position": queue_position_for(str(rec.get("session_id") or "")),
        }

    now = _now()
    rec["status"] = "awaiting_user"
    rec["accepted_at"] = _iso(now)  # admin selected
    rec["accepted_by"] = "admin"
    rec["awaiting_user_at"] = _iso(now)
    rec["awaiting_user_expires_at"] = _iso(now + timedelta(seconds=AWAITING_USER_SECONDS))
    rec["started_at"] = None
    rec["expires_at"] = None
    rec["updated_at"] = _iso(now)
    if admin_note:
        rec["admin_note"] = str(admin_note)[:200]
    if not isinstance(rec.get("messages"), list):
        rec["messages"] = []
    rec["messages"].append(
        {
            "id": str(uuid.uuid4()),
            "sender": "system",
            "text": (
                "Cosmic Intelligence Engine is ready. "
                "Accept within 2 minutes to start your live session."
            ),
            "image_url": "",
            "ts": _iso(now),
        }
    )
    _save(rec)
    return {"ok": True, "session": rec}


# Back-compat alias used by admin routes / Telegram — now means "ready for user".
def accept_v3_session(session_id: str, *, admin_note: str = "") -> dict[str, Any] | None:
    result = admin_ready_v3_session(session_id, admin_note=admin_note)
    if not result.get("ok"):
        return None
    return result.get("session")


def user_accept_v3_session(session_id: str, *, user_id: int) -> dict[str, Any]:
    """User confirms → start timer and open live chat."""
    rec = get_v3_session(session_id)
    if not rec:
        return {"ok": False, "error": "not_found"}
    if int(rec.get("user_id") or 0) != int(user_id):
        return {"ok": False, "error": "forbidden"}

    status = _normalize_status(rec.get("status"))
    if status == "accepted" and rec.get("expires_at"):
        # Backfill intro for sessions that went live before this feature.
        if _ensure_v3_user_details_intro(rec):
            _save(rec)
        return {"ok": True, "session": rec, "already_live": True}
    if status != "awaiting_user":
        return {"ok": False, "error": "not_awaiting_user", "status": status}

    rem = _awaiting_user_remaining(rec)
    if rem is not None and rem <= 0:
        rec = _requeue_awaiting_user(rec, reason="user_accept_timeout")
        return {
            "ok": False,
            "error": "accept_expired",
            "status": "queued",
            "session": _public_session(rec),
        }

    now = _now()
    minutes = int(rec.get("minutes") or 15)
    expires = now + timedelta(minutes=minutes)
    rec["status"] = "accepted"
    rec["started_at"] = _iso(now)
    rec["expires_at"] = _iso(expires)
    rec["awaiting_user_expires_at"] = None
    rec["updated_at"] = _iso(now)
    rec["extend_seconds_used"] = int(rec.get("extend_seconds_used") or 0)
    if not isinstance(rec.get("messages"), list):
        rec["messages"] = []
    rec["messages"].append(
        {
            "id": str(uuid.uuid4()),
            "sender": "system",
            "text": f"Live session started · {rec.get('label') or minutes} min. Timer is running.",
            "image_url": "",
            "ts": _iso(now),
        }
    )
    # Auto first user message for admin: birth profile details.
    _ensure_v3_user_details_intro(rec, now=now)
    _save(rec)
    return {"ok": True, "session": rec}


def reject_v3_session(session_id: str) -> dict[str, Any] | None:
    rec = _load(session_id)
    if not rec:
        return None
    now = _iso()
    rec["status"] = "rejected"
    rec["updated_at"] = now
    rec["awaiting_user_expires_at"] = None
    _save(rec)
    try:
        alert_admin_for_queue_head_if_idle()
    except Exception:
        pass
    return rec


def cancel_v3_waitlist(session_id: str, *, user_id: int) -> dict[str, Any]:
    """User permanently leaves a queued/awaiting handoff."""
    rec = get_v3_session(session_id)
    if not rec:
        return {"ok": False, "error": "not_found"}
    if int(rec.get("user_id") or 0) != int(user_id):
        return {"ok": False, "error": "forbidden"}

    status = _normalize_status(rec.get("status"))
    if status in ("ended", "rejected"):
        return {"ok": True, "cancelled": True, "already": True, "session": rec}
    if status not in ("queued", "awaiting_user"):
        return {"ok": False, "error": "not_waiting", "status": status}

    now = _iso()
    rec["status"] = "rejected"
    rec["rejected_reason"] = "cancelled_by_user"
    rec["cancelled_at"] = now
    rec["updated_at"] = now
    rec["awaiting_user_expires_at"] = None
    rec["started_at"] = None
    rec["expires_at"] = None
    messages = rec.get("messages") if isinstance(rec.get("messages"), list) else []
    messages.append(
        {
            "id": str(uuid.uuid4()),
            "sender": "system",
            "text": "User left the waiting list.",
            "image_url": "",
            "ts": now,
        }
    )
    rec["messages"] = messages[-500:]
    _save(rec)
    try:
        alert_admin_for_queue_head_if_idle()
    except Exception:
        pass
    return {"ok": True, "cancelled": True, "session": rec}


def end_v3_session(session_id: str, *, reason: str = "manual") -> dict[str, Any] | None:
    rec = _load(session_id)
    if not rec:
        return None
    now = _iso()
    rec["status"] = "ended"
    rec["ended_at"] = now
    rec["ended_reason"] = reason
    rec["updated_at"] = now
    rec["awaiting_user_expires_at"] = None
    messages = rec.get("messages") if isinstance(rec.get("messages"), list) else []
    messages.append(
        {
            "id": str(uuid.uuid4()),
            "sender": "system",
            "text": (
                "Time up — live session ended."
                if reason == "timer_expired"
                else "Live session ended."
            ),
            "image_url": "",
            "ts": now,
        }
    )
    rec["messages"] = messages[-500:]
    _save(rec)
    # Free slot → alert admin about next FIFO head (deduped).
    try:
        alert_admin_for_queue_head_if_idle()
    except Exception:
        pass
    return rec


_alert_head_guard = False


def alert_admin_for_queue_head_if_idle() -> dict[str, Any]:
    """After end/timeout/requeue: if engine free, notify admin about current queue head.

    Dedupes by (session_id + queued_at) so repeated polls do not spam.
    Does not create a new session.
    """
    global _alert_head_guard
    if _alert_head_guard:
        return {"ok": True, "alerted": False, "reason": "reentrant"}
    _alert_head_guard = True
    try:
        if has_active_or_awaiting_v3_session():
            return {"ok": True, "alerted": False, "reason": "engine_busy"}
        head = get_queue_head()
        if not head:
            return {"ok": True, "alerted": False, "reason": "empty_queue"}

        sid = str(head.get("session_id") or "")
        q_at = str(head.get("queued_at") or head.get("created_at") or "")
        token = f"{sid}:{q_at}"
        if str(head.get("queue_head_alert_token") or "") == token:
            return {"ok": True, "alerted": False, "reason": "already_alerted", "session_id": sid}

        head["queue_head_alert_token"] = token
        head["queue_head_alerted_at"] = _iso()
        head["updated_at"] = head["queue_head_alerted_at"]
        _save(head)

        try:
            from order_founder_alert import notify_founder_v3_live_chat_request

            notify_founder_v3_live_chat_request(head)
        except Exception:
            pass
        try:
            from admin_push import notify_admin_push_v3_request

            notify_admin_push_v3_request(head)
        except Exception:
            pass
        return {"ok": True, "alerted": True, "session_id": sid}
    finally:
        _alert_head_guard = False


def leave_or_end_v3_session(session_id: str) -> dict[str, Any]:
    """User taps End — permanently end; this session cannot be resumed."""
    rec = get_v3_session(session_id)
    if not rec:
        return {"ok": False, "error": "not_found"}
    status = _normalize_status(rec.get("status"))
    if status != "accepted":
        return {"ok": True, "ended": True, "status": status}

    rem = _remaining_seconds(rec) or 0
    end_v3_session(session_id, reason="ended_by_user")
    return {
        "ok": True,
        "ended": True,
        "resumable": False,
        "remaining_seconds": rem,
    }


def find_active_v3_session_for_user(
    user_id: int, *, as_record: bool = False
) -> dict[str, Any] | None:
    """Most recent queued / awaiting_user / accepted (resumable) session for user."""
    best: dict[str, Any] | None = None
    for rec in _iter_all_records():
        try:
            if int(rec.get("user_id") or 0) != int(user_id):
                continue
            rec = _maybe_expire(dict(rec))
            status = _normalize_status(rec.get("status"))
            if status == "accepted":
                rem = _remaining_seconds(rec) or 0
                if rem < RESUME_MIN_SECONDS:
                    end_v3_session(str(rec.get("session_id")), reason="below_resume_threshold")
                    continue
            elif status not in ("queued", "awaiting_user"):
                continue
            if best is None or str(rec.get("created_at") or "") > str(best.get("created_at") or ""):
                best = rec
        except Exception:
            continue
    if not best:
        return None
    return best if as_record else _public_session(best)


def _v3_tx_row(rec: dict[str, Any]) -> dict[str, Any] | None:
    """Build one purchase-history style row from a V3 session record."""
    try:
        status = _normalize_status(rec.get("status"))
        amount = int(rec.get("price_inr") or 0)
        if amount <= 0:
            pack = PACKS.get(str(rec.get("pack_id") or ""))
            amount = int((pack or {}).get("price_inr") or 0)
        label = str(rec.get("label") or "").strip() or "Live session"
        minutes = int(rec.get("minutes") or 0)
        paid_at = (
            rec.get("accepted_at")
            or rec.get("started_at")
            or rec.get("queued_at")
            or rec.get("created_at")
        )
        display_status = "paid" if status in ("accepted", "ended") else status
        return {
            "id": f"v3-{rec.get('session_id')}",
            "kind": "v3_live",
            "title": f"Cosmic Intelligence V3 · {label}",
            "subtitle": f"{minutes} min live" if minutes else "Live consultation",
            "amount_inr": amount,
            "order_id": str(rec.get("session_id") or "")[:12],
            "status": display_status,
            "paid_at": paid_at,
            "payment": rec.get("payment") or "",
            "user_id": int(rec.get("user_id") or 0),
            "_raw_status": status,
        }
    except Exception:
        return None


def list_v3_transactions_for_user(user_id: int) -> list[dict[str, Any]]:
    """Purchase-history rows for this user's V3 live bookings (coin / money ledger).

    Includes queued / live / ended sessions with pack price. Skips rejected/cancelled.
    """
    uid = int(user_id)
    rows: list[dict[str, Any]] = []
    keep = frozenset({"queued", "pending", "awaiting_user", "accepted", "ended"})
    for rec in _iter_all_records():
        try:
            if int(rec.get("user_id") or 0) != uid:
                continue
            status = _normalize_status(rec.get("status"))
            if status not in keep:
                continue
            row = _v3_tx_row(rec)
            if not row:
                continue
            row.pop("user_id", None)
            row.pop("_raw_status", None)
            rows.append(row)
        except Exception:
            continue
    return rows


def list_v3_transactions_admin(
    *,
    user_id: int | None = None,
    status_mode: str = "paid",
) -> list[dict[str, Any]]:
    """Admin transaction rows for V3 live across users.

    status_mode:
      - paid  → accepted / ended
      - failed → rejected / cancelled
      - all   → queued / pending / awaiting_user / accepted / ended / rejected / cancelled
    """
    mode = (status_mode or "paid").strip().lower()
    if mode == "failed":
        keep = frozenset({"rejected", "cancelled"})
    elif mode == "all":
        keep = frozenset(
            {
                "queued",
                "pending",
                "awaiting_user",
                "accepted",
                "ended",
                "rejected",
                "cancelled",
            }
        )
    else:
        keep = frozenset({"accepted", "ended"})

    rows: list[dict[str, Any]] = []
    for rec in _iter_all_records():
        try:
            uid = int(rec.get("user_id") or 0)
            if user_id is not None and uid != int(user_id):
                continue
            status = _normalize_status(rec.get("status"))
            if status not in keep:
                continue
            row = _v3_tx_row(rec)
            if not row:
                continue
            row.pop("_raw_status", None)
            rows.append(row)
        except Exception:
            continue
    return rows


def list_v3_chat_history_for_user(user_id: int, *, limit: int = 40) -> list[dict[str, Any]]:
    """Past V3 live chats the user can re-read in My Reports (Last talked).

    Includes ended / accepted sessions, plus any session that already has
    chat messages (so history still shows even if status is odd).
    """
    uid = int(user_id)
    rows: list[dict[str, Any]] = []
    for rec in _iter_all_records():
        try:
            if int(rec.get("user_id") or 0) != uid:
                continue
            status = _normalize_status(rec.get("status"))
            msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
            talk = [
                m
                for m in msgs
                if isinstance(m, dict)
                and str(m.get("sender") or "").lower() in ("user", "admin")
                and (str(m.get("text") or "").strip() or str(m.get("image_url") or "").strip())
            ]
            # Always show finished / live chats; also any session with real talk.
            if status not in ("ended", "accepted") and not talk:
                # Still show if they at least started and have system/chat trail.
                if status in ("rejected", "queued", "pending", "awaiting_user") and not msgs:
                    continue
                if status in ("queued", "pending") and not talk:
                    continue
            last = talk[-1] if talk else None
            if not last and msgs:
                # Fall back to last message of any kind for preview.
                for m in reversed(msgs):
                    if isinstance(m, dict) and (
                        str(m.get("text") or "").strip() or str(m.get("image_url") or "").strip()
                    ):
                        last = m
                        break
            preview = ""
            if last:
                preview = str(last.get("text") or "").strip()
                if not preview and last.get("image_url"):
                    preview = "📷 Photo"
                sender = str(last.get("sender") or "").lower()
                if sender == "admin" and preview:
                    preview = f"Guide: {preview}"
                elif sender == "user" and preview:
                    preview = f"You: {preview}"
            if not preview:
                preview = "Tap to open chat"
            label = str(rec.get("label") or "").strip() or "Live session"
            minutes = int(rec.get("minutes") or 0)
            when = (
                rec.get("ended_at")
                or rec.get("started_at")
                or rec.get("accepted_at")
                or rec.get("updated_at")
                or rec.get("created_at")
            )
            rows.append(
                {
                    "session_id": rec.get("session_id"),
                    "label": label,
                    "minutes": minutes,
                    "status": status,
                    "created_at": rec.get("created_at"),
                    "ended_at": rec.get("ended_at"),
                    "started_at": rec.get("started_at"),
                    "talked_at": when,
                    "message_count": len(talk) if talk else len(msgs),
                    "preview": (preview[:160] + ("…" if len(preview) > 160 else "")),
                }
            )
        except Exception:
            continue
    rows.sort(key=lambda r: str(r.get("talked_at") or ""), reverse=True)
    return rows[: max(1, min(100, int(limit or 40)))]


def extend_v3_session(
    session_id: str, *, seconds: int = DEFAULT_EXTEND_SECONDS
) -> dict[str, Any]:
    """Admin extends live timer. Hard cap: MAX_EXTEND_SECONDS total."""
    rec = get_v3_session(session_id)
    if not rec:
        return {"ok": False, "error": "not_found"}
    if _normalize_status(rec.get("status")) != "accepted":
        return {"ok": False, "error": "not_live", "status": rec.get("status")}

    try:
        req = int(seconds)
    except (TypeError, ValueError):
        req = DEFAULT_EXTEND_SECONDS
    req = max(60, min(180, req))

    used = int(rec.get("extend_seconds_used") or 0)
    left = max(0, MAX_EXTEND_SECONDS - used)
    if left <= 0:
        return {
            "ok": False,
            "error": "extend_cap_reached",
            "extend_seconds_used": used,
            "extend_seconds_left": 0,
            "max_extend_seconds": MAX_EXTEND_SECONDS,
        }

    grant = min(req, left)
    exp = _parse_iso(rec.get("expires_at")) or _now()
    new_exp = exp + timedelta(seconds=grant)
    rec["expires_at"] = _iso(new_exp)
    rec["extend_seconds_used"] = used + grant
    rec["updated_at"] = _iso()
    mins = grant // 60
    rec.setdefault("messages", []).append(
        {
            "id": str(uuid.uuid4()),
            "sender": "system",
            "text": f"Cosmic Intelligence V3 extended the timer by +{mins} min.",
            "image_url": "",
            "ts": _iso(),
        }
    )
    _save(rec)
    return {
        "ok": True,
        "granted_seconds": grant,
        "session": _public_session(rec),
    }


def append_v3_message(
    session_id: str,
    *,
    sender: str,
    text: str = "",
    image_url: str = "",
) -> dict[str, Any]:
    rec = get_v3_session(session_id)
    if not rec:
        return {"ok": False, "error": "not_found"}
    if _normalize_status(rec.get("status")) != "accepted":
        return {"ok": False, "error": "not_live", "status": rec.get("status")}

    sender = (sender or "").strip().lower()
    if sender not in ("user", "admin"):
        return {"ok": False, "error": "invalid_sender"}

    body = (text or "").strip()[:4000]
    img = (image_url or "").strip()[:500_000]
    if not body and not img:
        return {"ok": False, "error": "empty_message"}

    msg = {
        "id": str(uuid.uuid4()),
        "sender": sender,
        "text": body,
        "image_url": img,
        "ts": _iso(),
    }
    msgs = rec.get("messages")
    if not isinstance(msgs, list):
        msgs = []
    msgs.append(msg)
    rec["messages"] = msgs[-500:]
    rec["updated_at"] = msg["ts"]
    if sender == "admin":
        rec["admin_typing_at"] = None
    _save(rec)
    return {"ok": True, "message": msg, "session": _public_session(rec)}


_ADMIN_TYPING_TTL_SECONDS = 5


def set_v3_admin_typing(session_id: str, *, typing: bool = True) -> dict[str, Any]:
    rec = get_v3_session(session_id)
    if not rec:
        return {"ok": False, "error": "not_found"}
    if _normalize_status(rec.get("status")) != "accepted":
        return {"ok": False, "error": "not_live", "status": rec.get("status")}
    if typing:
        rec["admin_typing_at"] = _iso()
    else:
        rec["admin_typing_at"] = None
    rec["updated_at"] = _iso()
    _save(rec)
    return {"ok": True, "admin_typing": bool(typing)}


def is_v3_admin_typing(rec: dict[str, Any] | None) -> bool:
    if not rec:
        return False
    ts = _parse_iso(rec.get("admin_typing_at"))
    if not ts:
        return False
    age = (_now() - ts).total_seconds()
    return 0 <= age <= _ADMIN_TYPING_TTL_SECONDS


def get_v3_messages(
    session_id: str, *, after_ts: str | None = None
) -> dict[str, Any]:
    rec = get_v3_session(session_id)
    if not rec:
        return {"ok": False, "error": "not_found"}
    # Live chat: ensure birth-details intro exists (idempotent) so admin always sees it.
    if _normalize_status(rec.get("status")) == "accepted":
        if _ensure_v3_user_details_intro(rec):
            _save(rec)
            rec = get_v3_session(session_id) or rec
    msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
    if after_ts:
        after = _parse_iso(after_ts)
        if after:
            filtered = []
            for m in msgs:
                mt = _parse_iso(m.get("ts") if isinstance(m, dict) else None)
                if mt and mt > after:
                    filtered.append(m)
            msgs = filtered
    return {
        "ok": True,
        "messages": msgs,
        "admin_typing": is_v3_admin_typing(rec),
        "session": _public_session(rec),
    }


def save_v3_image_data_url(data_url: str) -> str | None:
    raw = (data_url or "").strip()
    if not raw.startswith("data:image"):
        return None
    try:
        header, b64 = raw.split(",", 1)
        mime = header.split(":", 1)[1].split(";", 1)[0] or "image/jpeg"
        ext = "png" if "png" in mime else ("webp" if "webp" in mime else "jpg")
        data = base64.b64decode(b64)
        if len(data) > 6 * 1024 * 1024:
            return None
        _ensure_dir()
        name = f"{uuid.uuid4().hex}.{ext}"
        path = os.path.join(_UPLOADS, name)
        with open(path, "wb") as fh:
            fh.write(data)
        return f"/api/cosmic-intelligence-v3/media/{name}"
    except Exception:
        return None


def read_v3_media(filename: str) -> tuple[bytes, str] | None:
    name = os.path.basename((filename or "").strip())
    if not name or not re.match(r"^[a-f0-9]{32}\.(jpg|jpeg|png|webp)$", name, re.I):
        return None
    path = os.path.join(_UPLOADS, name)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "rb") as fh:
            data = fh.read()
        ext = name.rsplit(".", 1)[-1].lower()
        mime = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
        }.get(ext, "application/octet-stream")
        return data, mime
    except Exception:
        return None


def list_v3_sessions(
    *, page: int = 1, per_page: int = 50, status: str | None = None
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    status_filter = (status or "").strip().lower() or None
    # Legacy clients filter status=pending → include queued too.
    for rec in _iter_all_records():
        try:
            rec = _maybe_expire(dict(rec))
            norm = _normalize_status(rec.get("status"))
            if status_filter:
                if status_filter in ("pending", "queued"):
                    if norm != "queued":
                        continue
                elif norm != status_filter:
                    continue
            rows.append(_public_session(rec))
        except Exception:
            continue

    # FIFO: queued first by queued_at ASC, then awaiting_user, then accepted, then rest.
    def _sort_key(r: dict[str, Any]) -> tuple:
        st = _normalize_status(r.get("status"))
        rank = {"awaiting_user": 0, "accepted": 1, "queued": 2}.get(st, 9)
        if st == "queued":
            return (rank, str(r.get("queued_at") or r.get("created_at") or ""))
        return (rank, str(r.get("created_at") or ""), )

    rows.sort(key=_sort_key)
    # For non-queued, show newest first within rank buckets after awaiting/accepted.
    queued = [r for r in rows if _normalize_status(r.get("status")) == "queued"]
    awaiting = [r for r in rows if _normalize_status(r.get("status")) == "awaiting_user"]
    accepted = [r for r in rows if _normalize_status(r.get("status")) == "accepted"]
    rest = [
        r for r in rows
        if _normalize_status(r.get("status")) not in ("queued", "awaiting_user", "accepted")
    ]
    rest.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    rows = awaiting + accepted + queued + rest

    # Back-compat: old admin bundle shows Accept/Reject only for "pending".
    # New admin UI treats pending == queued, so this is safe for both.
    for r in rows:
        if r.get("status") == "queued":
            r["status"] = "pending"

    total = len(rows)
    page = max(1, int(page or 1))
    per_page = max(1, min(100, int(per_page or 50)))
    pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    head = get_queue_head()
    return {
        "sessions": rows[start : start + per_page],
        "total": total,
        "page": page,
        "pages": pages,
        "per_page": per_page,
        "queue_head_id": (head or {}).get("session_id"),
        "engine_busy": has_active_or_awaiting_v3_session(),
        "queued_count": len(queued),
    }


def session_public_view(session_id: str) -> dict[str, Any] | None:
    rec = get_v3_session(session_id)
    if not rec:
        return None
    return _public_session(rec)


def notify_user_v3_ready(rec: dict[str, Any]) -> dict[str, Any]:
    """Push the user that admin is ready — they must Accept to start timer."""
    try:
        uid = int(rec.get("user_id") or 0)
        if not uid:
            return {"sent": 0, "error": "no_user"}
        label = str(rec.get("label") or "Live")

        def _send() -> dict[str, Any]:
            from notification_helper import send_to_user

            return send_to_user(
                uid,
                title="Cosmic Intelligence is ready 🔔",
                body=(
                    f"Your {label} consultation is ready. "
                    "Open Ask and tap Accept within 2 minutes to start."
                ),
                data={
                    "kind": "v3_ready",
                    "screen": "/(tabs)/ask",
                    "session_id": str(rec.get("session_id") or ""),
                },
            )

        # send_to_user does a DB lookup (User.query) which needs a Flask app
        # context. Telegram Accept runs in a plain thread WITHOUT one — the
        # push used to fail silently there. Wrap in app context when missing.
        try:
            from flask import has_app_context

            if has_app_context():
                result = _send()
            else:
                from flask_app import app as _flask_app

                with _flask_app.app_context():
                    result = _send()
        except Exception as exc:
            result = {"sent": 0, "error": str(exc)[:160]}
        try:
            log.info("[v3] ready push user=%s result=%s", uid, result)
        except Exception:
            pass
        return result
    except Exception as exc:
        return {"sent": 0, "error": str(exc)[:160]}

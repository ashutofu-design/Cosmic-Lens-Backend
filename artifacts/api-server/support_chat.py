"""Persistent Help & Support chat — file-backed threads (not V3 consultations).

One open thread per user. Messages: text + images. Admin inbox + user app poll.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

log = logging.getLogger("support_chat")

_BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".cache", "support_threads")
)
_UPLOADS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".cache", "support_uploads")
)
_tid_locks_guard = threading.Lock()
_tid_locks: dict[str, threading.RLock] = {}
_ADMIN_TYPING_TTL_SECONDS = 5
_IDLE_CLOSE_SECONDS = int(os.environ.get("SUPPORT_IDLE_CLOSE_SECONDS") or str(30 * 60))
_idle_closer_started = False


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso() -> str:
    return _now().isoformat().replace("+00:00", "Z")


def _parse_iso(val: Any) -> datetime | None:
    if not val or not isinstance(val, str):
        return None
    try:
        s = val.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _ensure_dir() -> None:
    os.makedirs(_BASE, exist_ok=True)
    os.makedirs(_UPLOADS, exist_ok=True)


def _safe_tid(thread_id: str) -> str:
    tid = (thread_id or "").strip()
    if not tid or tid in (".", "..") or "/" in tid or "\\" in tid:
        return ""
    return tid


def _proc_lock_for(tid: str) -> threading.RLock:
    with _tid_locks_guard:
        lock = _tid_locks.get(tid)
        if lock is None:
            lock = threading.RLock()
            _tid_locks[tid] = lock
        return lock


class SupportLockTimeout(RuntimeError):
    """Cross-worker lock not acquired — do not write unlocked."""


@contextmanager
def _thread_lock(thread_id: str) -> Iterator[None]:
    """In-process RLock + mkdir lock so gunicorn workers cannot clobber a bot append."""
    tid = _safe_tid(thread_id)
    if not tid:
        yield
        return
    _ensure_dir()
    lock_dir = os.path.join(_BASE, f".{tid}.lockdir")
    deadline = time.time() + 8.0
    with _proc_lock_for(tid):
        owned = False
        while True:
            try:
                os.mkdir(lock_dir)
                owned = True
                break
            except FileExistsError:
                try:
                    age = time.time() - os.path.getmtime(lock_dir)
                except OSError:
                    age = 999.0
                if age > 20.0:
                    try:
                        os.rmdir(lock_dir)
                        continue
                    except OSError:
                        pass
                if time.time() >= deadline:
                    log.warning("[support] lock timeout tid=%s — refusing unlocked write", tid)
                    raise SupportLockTimeout(tid)
                time.sleep(0.01)
        try:
            yield
        finally:
            if owned:
                try:
                    os.rmdir(lock_dir)
                except OSError:
                    pass


def _save(record: dict[str, Any]) -> str:
    """Atomic replace so readers never see a truncated JSON file (which 404s the app)."""
    _ensure_dir()
    tid = _safe_tid(str(record.get("thread_id") or "")) or str(uuid.uuid4())
    record["thread_id"] = tid
    path = os.path.join(_BASE, f"{tid}.json")
    tmp = os.path.join(_BASE, f".{tid}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            if os.path.isfile(tmp):
                os.remove(tmp)
        except OSError:
            pass
        raise
    return tid


def _load(thread_id: str) -> dict[str, Any] | None:
    _ensure_dir()
    tid = _safe_tid(thread_id)
    if not tid:
        return None
    path = os.path.join(_BASE, f"{tid}.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            rec = json.load(fh)
        return rec if isinstance(rec, dict) else None
    except Exception:
        return None


def _iter_all() -> list[dict[str, Any]]:
    _ensure_dir()
    out: list[dict[str, Any]] = []
    try:
        names = [
            n
            for n in os.listdir(_BASE)
            if n.endswith(".json") and not n.startswith(".")
        ]
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


def _last_message(rec: dict[str, Any]) -> dict[str, Any] | None:
    msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
    for m in reversed(msgs):
        if isinstance(m, dict) and m.get("sender") in ("user", "admin", "bot"):
            return m
    return None


def _public_thread(rec: dict[str, Any]) -> dict[str, Any]:
    msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
    last = _last_message(rec)
    preview = ""
    if last:
        preview = str(last.get("text") or "").strip()
        if not preview and last.get("image_url"):
            preview = "[Image]"
    unread_admin = int(rec.get("unread_admin") or 0)
    unread_user = int(rec.get("unread_user") or 0)
    return {
        "thread_id": rec.get("thread_id"),
        "created_at": rec.get("created_at"),
        "updated_at": rec.get("updated_at"),
        "status": rec.get("status") or "open",
        "user_id": rec.get("user_id"),
        "cosmo_user_id": rec.get("cosmo_user_id") or "",
        "user_name": rec.get("user_name") or "",
        "user_email": rec.get("user_email") or "",
        "message_count": len(msgs),
        "last_message_preview": preview[:160],
        "last_message_at": (last or {}).get("ts") or rec.get("updated_at"),
        "last_sender": (last or {}).get("sender") or "",
        "unread_admin": unread_admin,
        "unread_user": unread_user,
        "admin_typing": is_admin_typing(rec),
        "escalated": bool(rec.get("escalated")),
        "ai_handled": bool(rec.get("ai_handled")),
        "agent_state": str(rec.get("agent_state") or ""),
        "has_admin": any(
            isinstance(m, dict) and str(m.get("sender") or "") == "admin" for m in msgs
        ),
    }


def get_thread(thread_id: str) -> dict[str, Any] | None:
    return _load(thread_id)


def find_open_thread_for_user(user_id: int) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    for rec in _iter_all():
        try:
            if int(rec.get("user_id") or 0) != int(user_id):
                continue
            st = str(rec.get("status") or "open")
            if st == "closed":
                continue
            if best is None or str(rec.get("updated_at") or "") > str(
                best.get("updated_at") or ""
            ):
                best = rec
        except Exception:
            continue
    return best


def get_or_create_thread(
    *,
    user_id: int,
    user_name: str = "",
    user_email: str = "",
    user_phone: str = "",
    cosmo_user_id: str = "",
) -> dict[str, Any]:
    close_idle_threads()
    existing = find_open_thread_for_user(int(user_id))
    if existing:
        tid = str(existing.get("thread_id") or "")
        with _thread_lock(tid):
            rec = _load(tid) or existing
            changed = False
            for k, v in (
                ("user_name", user_name),
                ("user_email", user_email),
                ("user_phone", user_phone),
                ("cosmo_user_id", cosmo_user_id),
            ):
                if v and str(rec.get(k) or "") != str(v):
                    rec[k] = v
                    changed = True
            if changed:
                rec["updated_at"] = _iso()
                _save(rec)
            return rec

    now = _iso()
    rec: dict[str, Any] = {
        "thread_id": str(uuid.uuid4()),
        "created_at": now,
        "updated_at": now,
        "status": "open",
        "user_id": int(user_id),
        "user_name": (user_name or "").strip(),
        "user_email": (user_email or "").strip(),
        "user_phone": (user_phone or "").strip(),
        "cosmo_user_id": (cosmo_user_id or "").strip(),
        "unread_admin": 0,
        "unread_user": 0,
        "admin_typing_at": None,
        "messages": [
            {
                "id": str(uuid.uuid4()),
                "sender": "system",
                "text": "Cosmic Help is here. You’ll get short answers about the app. For payments, refunds, or missing PDFs, our team will join this chat.",
                "image_url": "",
                "ts": now,
            }
        ],
    }
    _save(rec)
    return rec


def append_message(
    thread_id: str,
    *,
    sender: str,
    text: str = "",
    image_url: str = "",
    user_id: int | None = None,
) -> dict[str, Any]:
    try:
        with _thread_lock(thread_id):
            rec = _load(thread_id)
            if not rec:
                return {"ok": False, "error": "not_found"}
            if user_id is not None and int(rec.get("user_id") or 0) != int(user_id):
                return {"ok": False, "error": "forbidden"}

            sender = (sender or "").strip().lower()
            if sender not in ("user", "admin", "bot"):
                return {"ok": False, "error": "invalid_sender"}

            if str(rec.get("status") or "open") == "closed":
                return {"ok": False, "error": "not_found"}

            body = (text or "").strip()[:4000]
            img = (image_url or "").strip()[:500_000]
            if not body and not img:
                return {"ok": False, "error": "empty_message"}

            now = _iso()
            msg = {
                "id": str(uuid.uuid4()),
                "sender": sender,
                "text": body,
                "image_url": img,
                "ts": now,
            }
            msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
            msgs.append(msg)
            rec["messages"] = msgs[-1000:]
            rec["updated_at"] = now
            if sender == "user":
                rec["admin_typing_at"] = None
                if rec.get("escalated"):
                    rec["status"] = "waiting_admin"
                    rec["unread_admin"] = int(rec.get("unread_admin") or 0) + 1
                else:
                    rec["status"] = "open"
            elif sender == "bot":
                rec["status"] = "waiting_user"
                rec["unread_user"] = int(rec.get("unread_user") or 0) + 1
                rec["unread_admin"] = 0
                rec["admin_typing_at"] = None
                rec["ai_handled"] = True
            else:
                rec["status"] = "waiting_user"
                rec["unread_user"] = int(rec.get("unread_user") or 0) + 1
                rec["admin_typing_at"] = None
                rec["unread_admin"] = 0
            _save(rec)
            return {"ok": True, "message": msg, "thread": _public_thread(rec)}
    except SupportLockTimeout:
        return {"ok": False, "error": "busy"}


def mark_escalated(thread_id: str) -> dict[str, Any]:
    try:
        with _thread_lock(thread_id):
            rec = _load(thread_id)
            if not rec:
                return {"ok": False, "error": "not_found"}
            rec["escalated"] = True
            rec["status"] = "waiting_admin"
            rec["agent_state"] = "waiting_for_human"
            rec["unread_admin"] = max(1, int(rec.get("unread_admin") or 0))
            rec["updated_at"] = _iso()
            _save(rec)
            return {"ok": True, "thread": _public_thread(rec)}
    except SupportLockTimeout:
        return {"ok": False, "error": "busy"}


def clear_escalation(thread_id: str) -> dict[str, Any]:
    """Allow AI how-to again after a product question is answered."""
    try:
        with _thread_lock(thread_id):
            rec = _load(thread_id)
            if not rec:
                return {"ok": False, "error": "not_found"}
            rec["escalated"] = False
            rec["status"] = "waiting_user"
            rec["agent_state"] = "answered"
            rec["ai_handled"] = True
            rec["updated_at"] = _iso()
            _save(rec)
            return {"ok": True, "thread": _public_thread(rec)}
    except SupportLockTimeout:
        return {"ok": False, "error": "busy"}


def set_agent_state(thread_id: str, state: str) -> dict[str, Any]:
    try:
        with _thread_lock(thread_id):
            rec = _load(thread_id)
            if not rec:
                return {"ok": False, "error": "not_found"}
            rec["agent_state"] = (state or "").strip()
            rec["updated_at"] = _iso()
            if state == "processing":
                rec["status"] = "open"
            elif state == "waiting_for_human":
                rec["escalated"] = True
                rec["status"] = "waiting_admin"
            elif state == "answered":
                rec["status"] = "waiting_user"
                rec["ai_handled"] = True
                rec["escalated"] = False
            elif state == "failed":
                rec["status"] = "waiting_admin"
            _save(rec)
            return {"ok": True, "thread": _public_thread(rec)}
    except SupportLockTimeout:
        return {"ok": False, "error": "busy"}


def get_messages(
    thread_id: str,
    *,
    after_ts: str | None = None,
    mark_read_for: str | None = None,
) -> dict[str, Any]:
    try:
        with _thread_lock(thread_id):
            rec = _load(thread_id)
            if not rec:
                return {"ok": False, "error": "not_found"}
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
            dirty = False
            if mark_read_for == "admin" and int(rec.get("unread_admin") or 0) != 0:
                rec["unread_admin"] = 0
                dirty = True
            elif mark_read_for == "user" and int(rec.get("unread_user") or 0) != 0:
                rec["unread_user"] = 0
                dirty = True
            if dirty:
                _save(rec)
            return {
                "ok": True,
                "messages": msgs,
                "admin_typing": is_admin_typing(rec),
                "agent_state": str(rec.get("agent_state") or ""),
                "agent_typing": str(rec.get("agent_state") or "") == "processing",
                "thread": _public_thread(rec),
            }
    except SupportLockTimeout:
        # Read-only fallback — never write unlocked
        rec = _load(thread_id)
        if not rec:
            return {"ok": False, "error": "busy"}
        msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
        return {
            "ok": True,
            "messages": msgs,
            "admin_typing": is_admin_typing(rec),
            "agent_state": str(rec.get("agent_state") or ""),
            "agent_typing": str(rec.get("agent_state") or "") == "processing",
            "thread": _public_thread(rec),
        }


def set_admin_typing(thread_id: str, *, typing: bool = True) -> dict[str, Any]:
    with _thread_lock(thread_id):
        rec = _load(thread_id)
        if not rec:
            return {"ok": False, "error": "not_found"}
        if typing:
            rec["admin_typing_at"] = _iso()
        else:
            rec["admin_typing_at"] = None
        rec["updated_at"] = _iso()
        _save(rec)
        return {"ok": True, "admin_typing": bool(typing)}


def is_admin_typing(rec: dict[str, Any] | None) -> bool:
    if not rec:
        return False
    ts = _parse_iso(rec.get("admin_typing_at"))
    if not ts:
        return False
    age = (_now() - ts).total_seconds()
    return 0 <= age <= _ADMIN_TYPING_TTL_SECONDS


def close_thread(thread_id: str) -> dict[str, Any]:
    """Permanently wipe the ticket: chat JSON + uploaded photos. Nothing remains."""
    with _thread_lock(thread_id):
        rec = _load(thread_id)
        if not rec:
            return {"ok": False, "error": "not_found"}
        tid = str(rec.get("thread_id") or thread_id).strip()
        _purge_thread_files(rec, tid)
        return {"ok": True, "deleted": True, "thread_id": tid}


def _last_chat_at(rec: dict[str, Any]) -> datetime | None:
    last = _last_message(rec)
    return (
        _parse_iso((last or {}).get("ts") if last else None)
        or _parse_iso(rec.get("updated_at"))
        or _parse_iso(rec.get("created_at"))
    )


def close_idle_threads(*, idle_seconds: int | None = None) -> int:
    """Hard-delete idle AI how-to chats only — never purge escalated / human tickets."""
    limit = int(idle_seconds if idle_seconds is not None else _IDLE_CLOSE_SECONDS)
    if limit < 60:
        limit = 60
    now = _now()
    closed = 0
    for rec in list(_iter_all()):
        # Keep tickets waiting for / with human support
        if rec.get("escalated") or str(rec.get("status") or "") in (
            "waiting_admin",
            "admin_joined",
            "human",
        ):
            continue
        msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
        if any(isinstance(m, dict) and m.get("sender") == "admin" for m in msgs):
            continue
        ts = _last_chat_at(rec)
        if not ts:
            continue
        if (now - ts).total_seconds() < limit:
            continue
        tid = str(rec.get("thread_id") or "").strip()
        if not tid:
            continue
        result = close_thread(tid)
        if result.get("ok"):
            closed += 1
    return closed


def start_idle_closer() -> None:
    global _idle_closer_started
    if _idle_closer_started:
        return
    _idle_closer_started = True

    def _loop() -> None:
        while True:
            try:
                threading.Event().wait(60)
                close_idle_threads()
            except Exception as exc:
                log.warning("[support] idle closer failed: %s", exc)

    threading.Thread(target=_loop, daemon=True, name="support-idle-close").start()


_MEDIA_NAME_RE = re.compile(r"^[a-f0-9]{32}\.(jpg|jpeg|png|webp)$", re.I)


def _upload_name_from_url(url: str) -> str | None:
    raw = (url or "").strip()
    if not raw or raw.startswith("data:"):
        return None
    name = os.path.basename(raw.split("?", 1)[0])
    if not name or not _MEDIA_NAME_RE.match(name):
        return None
    return name


def _purge_thread_files(rec: dict[str, Any], thread_id: str) -> None:
    msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
    for m in msgs:
        if not isinstance(m, dict):
            continue
        name = _upload_name_from_url(str(m.get("image_url") or ""))
        if not name:
            continue
        try:
            path = os.path.join(_UPLOADS, name)
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            pass
    tid = (thread_id or "").strip()
    if not tid or tid in (".", "..") or "/" in tid or "\\" in tid:
        return
    json_path = os.path.join(_BASE, f"{tid}.json")
    try:
        if os.path.isfile(json_path):
            os.remove(json_path)
    except OSError:
        pass
    for extra in (f".{tid}.lockdir", f".{tid}.lock"):
        extra_path = os.path.join(_BASE, extra)
        try:
            if os.path.isdir(extra_path):
                os.rmdir(extra_path)
            elif os.path.isfile(extra_path):
                os.remove(extra_path)
        except OSError:
            pass


def _purge_closed_threads() -> None:
    """Remove leftover closed tickets (old close kept JSON; close now means wipe)."""
    for rec in list(_iter_all()):
        if str(rec.get("status") or "open") != "closed":
            continue
        tid = str(rec.get("thread_id") or "").strip()
        if tid:
            _purge_thread_files(rec, tid)


def reopen_thread(thread_id: str) -> dict[str, Any]:
    with _thread_lock(thread_id):
        rec = _load(thread_id)
        if not rec:
            return {"ok": False, "error": "not_found"}
        now = _iso()
        rec["status"] = "open"
        rec["updated_at"] = now
        msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
        msgs.append(
            {
                "id": str(uuid.uuid4()),
                "sender": "system",
                "text": "Support reopened this chat.",
                "image_url": "",
                "ts": now,
            }
        )
        rec["messages"] = msgs[-1000:]
        _save(rec)
        return {"ok": True, "thread": _public_thread(rec)}


def list_threads(
    *, status: str | None = None, page: int = 1, per_page: int = 50
) -> dict[str, Any]:
    close_idle_threads()
    _purge_closed_threads()
    rows = [_public_thread(r) for r in _iter_all()]
    # AI-only how-to chats stay in the app — admin sees tickets that need a human.
    rows = [
        r
        for r in rows
        if r.get("escalated")
        or r.get("has_admin")
        or int(r.get("unread_admin") or 0) > 0
    ]
    status_filter = (status or "").strip().lower() or None
    if status_filter == "open":
        rows = [r for r in rows if r.get("status") != "closed"]
    elif status_filter:
        rows = [r for r in rows if str(r.get("status") or "") == status_filter]

    open_rows = [r for r in rows if r.get("status") != "closed"]
    closed_rows = [r for r in rows if r.get("status") == "closed"]
    open_rows.sort(
        key=lambda r: (
            int(r.get("unread_admin") or 0),
            str(r.get("updated_at") or ""),
        ),
        reverse=True,
    )
    closed_rows.sort(key=lambda r: str(r.get("updated_at") or ""), reverse=True)
    rows = open_rows + closed_rows

    total = len(rows)
    page = max(1, int(page or 1))
    per_page = max(1, min(100, int(per_page or 50)))
    pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    waiting = sum(
        1
        for r in open_rows
        if int(r.get("unread_admin") or 0) > 0 or r.get("escalated")
    )
    return {
        "threads": rows[start : start + per_page],
        "total": total,
        "page": page,
        "pages": pages,
        "per_page": per_page,
        "waiting_admin_count": waiting,
    }


def user_owns_support_media(user_id: int, filename: str) -> bool:
    """True if this user's thread references the upload (auth for media GET)."""
    name = os.path.basename((filename or "").strip())
    if not name or not _MEDIA_NAME_RE.match(name):
        return False
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return False
    needle = f"/api/support/media/{name}"
    for rec in _iter_all():
        if int(rec.get("user_id") or 0) != uid:
            continue
        msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
        for m in msgs:
            if not isinstance(m, dict):
                continue
            url = str(m.get("image_url") or "")
            if name in url or needle in url:
                return True
    return False


def save_support_image_data_url(data_url: str) -> str | None:
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
        return f"/api/support/media/{name}"
    except Exception:
        return None


def read_support_media(filename: str) -> tuple[bytes, str] | None:
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


def notify_user_support_reply(rec: dict[str, Any]) -> dict[str, Any]:
    try:
        from notification_helper import send_to_user

        uid = int(rec.get("user_id") or 0)
        if not uid:
            return {"sent": 0, "error": "no_user"}

        def _send() -> dict[str, Any]:
            return send_to_user(
                uid,
                title="Support replied",
                body="You have a new reply in Help & Support.",
                data={
                    "kind": "support_reply",
                    "screen": "/help-support",
                    "thread_id": str(rec.get("thread_id") or ""),
                },
            )

        try:
            from flask import has_app_context

            if has_app_context():
                return _send()
            from flask_app import app as _flask_app

            with _flask_app.app_context():
                return _send()
        except Exception as exc:
            return {"sent": 0, "error": str(exc)[:160]}
    except Exception as exc:
        return {"sent": 0, "error": str(exc)[:160]}


def notify_admin_new_support_message(rec: dict[str, Any], message: dict[str, Any]) -> None:
    """Fire-and-forget admin push + Telegram — only after human escalation."""
    if not rec or not rec.get("escalated"):
        log.info("[support] skip admin/telegram — AI chat, not escalated")
        return

    def _run() -> None:
        try:
            from admin_push import notify_admin_push_support_message

            notify_admin_push_support_message(rec, message)
        except Exception as exc:
            log.warning("[support] admin push failed: %s", exc)
        try:
            from order_founder_alert import notify_founder_support_message

            notify_founder_support_message(rec, message)
        except Exception as exc:
            log.warning("[support] telegram alert failed: %s", exc)

    threading.Thread(target=_run, daemon=True).start()

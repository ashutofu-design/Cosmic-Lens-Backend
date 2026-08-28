"""Web Push notifications to the admin's phone (Chrome) for V3 live chat requests.

Works even when the admin website is closed: pushes go through FCM to the
browser's service worker, which shows a notification with Accept / Reject
action buttons. Re-pushes every ~20s while the request stays pending so the
phone keeps ringing until the admin acts.

Requires: pip install pywebpush  (pulls py-vapid + cryptography)
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from typing import Any

log = logging.getLogger("admin_push")

_BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".cache", "admin_push_subscriptions")
)
_VAPID_PEM = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".cache", "admin_push_vapid.pem")
)
_lock = threading.Lock()

# Keep re-ringing the phone while the request is pending.
REPUSH_INTERVAL_SECONDS = 20
REPUSH_MAX_ATTEMPTS = 9  # ~3 minutes of ringing


def _ensure_dir() -> None:
    try:
        os.makedirs(_BASE, exist_ok=True)
    except Exception:
        pass


def _vapid():
    """Load (or create on first use) the VAPID signing key."""
    from py_vapid import Vapid02

    _ensure_dir()
    if os.path.isfile(_VAPID_PEM):
        return Vapid02.from_file(_VAPID_PEM)
    v = Vapid02()
    v.generate_keys()
    v.save_key(_VAPID_PEM)
    return v


def get_vapid_public_key() -> str:
    """URL-safe base64 public key for PushManager.subscribe()."""
    import base64

    from cryptography.hazmat.primitives import serialization

    v = _vapid()
    raw = v.public_key.public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def save_subscription(subscription: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(subscription, dict) or not subscription.get("endpoint"):
        return {"ok": False, "error": "invalid_subscription"}
    _ensure_dir()
    # One file per endpoint (dedupe by endpoint hash) so re-subscribes overwrite.
    import hashlib

    key = hashlib.sha256(str(subscription["endpoint"]).encode()).hexdigest()[:32]
    path = os.path.join(_BASE, f"{key}.json")
    with _lock:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(subscription, fh)
    return {"ok": True, "id": key}


def _list_subscriptions() -> list[tuple[str, dict[str, Any]]]:
    _ensure_dir()
    out: list[tuple[str, dict[str, Any]]] = []
    try:
        names = [n for n in os.listdir(_BASE) if n.endswith(".json")]
    except OSError:
        return out
    for name in names:
        try:
            with open(os.path.join(_BASE, name), encoding="utf-8") as fh:
                sub = json.load(fh)
            if isinstance(sub, dict) and sub.get("endpoint"):
                out.append((name, sub))
        except Exception:
            continue
    return out


def _push_to_all(payload: dict[str, Any]) -> int:
    """Send one push to every saved subscription. Returns delivered count."""
    from pywebpush import WebPushException, webpush

    subs = _list_subscriptions()
    if not subs:
        return 0
    data = json.dumps(payload, ensure_ascii=False)
    sent = 0
    for name, sub in subs:
        try:
            webpush(
                subscription_info=sub,
                data=data,
                vapid_private_key=_VAPID_PEM,
                vapid_claims={"sub": "mailto:admin@coosmic.icu"},
                ttl=120,
            )
            sent += 1
        except WebPushException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (404, 410):
                # Subscription expired — clean up.
                try:
                    os.remove(os.path.join(_BASE, name))
                except OSError:
                    pass
            else:
                log.warning("[admin_push] push failed: %s", exc)
        except Exception as exc:
            log.warning("[admin_push] push error: %s", exc)
    return sent


def _admin_token() -> str:
    return (os.environ.get("ADMIN_SECRET") or "").strip()


def send_test_push() -> int:
    return _push_to_all(
        {
            "kind": "test",
            "title": "Cosmic Admin — test push",
            "body": "Push notifications kaam kar rahe hain. ✅",
            "tag": f"test-{uuid.uuid4().hex[:6]}",
        }
    )


def _v3_payload(record: dict[str, Any], attempt: int) -> dict[str, Any]:
    name = str(record.get("user_name") or record.get("user_email") or "User")
    label = str(record.get("label") or f"{record.get('minutes') or '—'} min")
    price = record.get("price_inr")
    lang_raw = str(record.get("preferred_language") or "").strip().lower()
    lang_label = {"hi": "हिंदी", "en": "English", "hn": "Hinglish"}.get(lang_raw, "")
    body = f"{name} · {label}" + (f" · ₹{price}" if price else "")
    if lang_label:
        body += f" · {lang_label}"
    if attempt > 0:
        body += f"  (waiting {attempt * REPUSH_INTERVAL_SECONDS}s)"
    return {
        "kind": "v3_request",
        "title": "⚡ New V3 live chat — Accept?",
        "body": body,
        "session_id": str(record.get("session_id") or ""),
        "tag": f"v3-{str(record.get('session_id') or '')[:12]}",
        "admin_token": _admin_token(),
    }


def notify_admin_push_v3_blocked(info: dict[str, Any]) -> None:
    """One push per blocked connect attempt while V3 chat is closed."""
    if not info:
        return

    def _run() -> None:
        try:
            name = str(info.get("user_name") or info.get("user_email") or "User")
            label = str(info.get("label") or "").strip()
            price = info.get("price_inr")
            attempt = int(info.get("attempt") or 1)
            body = name
            if label:
                body += f" · {label}" + (f" · ₹{price}" if price else "")
            body += f" · attempt {attempt}"
            sent = _push_to_all(
                {
                    "kind": "v3_blocked",
                    "title": "🔴 User trying to connect — V3 chat is CLOSED",
                    "body": body,
                    "session_id": str(info.get("session_id") or ""),
                    "tag": f"v3-blocked-{info.get('user_id') or 'x'}",
                    "admin_token": _admin_token(),
                }
            )
            print(f"[admin_push] v3 blocked push sent={sent} user={info.get('user_id')}", flush=True)
        except Exception as exc:
            log.warning("[admin_push] v3 blocked notify error: %s", exc)

    threading.Thread(target=_run, daemon=True).start()


def notify_admin_push_v3_request(record: dict[str, Any]) -> None:
    """Fire-and-forget: push now, then keep re-pushing while still pending."""
    if not record or not record.get("session_id"):
        return

    session_id = str(record["session_id"])

    def _run() -> None:
        try:
            sent = _push_to_all(_v3_payload(record, 0))
            print(f"[admin_push] v3 push sent={sent} session={session_id[:8]}", flush=True)
            if sent == 0:
                return
            from cosmic_intelligence_v3_sessions import get_v3_session

            for attempt in range(1, REPUSH_MAX_ATTEMPTS + 1):
                time.sleep(REPUSH_INTERVAL_SECONDS)
                rec = get_v3_session(session_id)
                st = str((rec or {}).get("status") or "")
                if not rec or st not in ("pending", "queued"):
                    return
                _push_to_all(_v3_payload(rec, attempt))
        except Exception as exc:
            log.warning("[admin_push] v3 notify error: %s", exc)

    threading.Thread(target=_run, daemon=True).start()


def notify_admin_push_support_message(
    thread: dict[str, Any], message: dict[str, Any]
) -> None:
    """One-shot push when a user sends a Help & Support message."""
    if not thread or not thread.get("escalated"):
        return

    def _run() -> None:
        try:
            uid = thread.get("user_id")
            cosmo = str(thread.get("cosmo_user_id") or "").strip()
            name = str(
                thread.get("user_name")
                or thread.get("user_email")
                or cosmo
                or (f"User #{uid}" if uid else "")
                or "User"
            )
            preview = str(message.get("text") or "").strip()
            if not preview and message.get("image_url"):
                preview = "[Image]"
            body = f"{name}: {preview[:120]}" if preview else f"{name} sent a support message"
            sent = _push_to_all(
                {
                    "kind": "support_message",
                    "title": "💬 New Help & Support message",
                    "body": body,
                    "thread_id": str(thread.get("thread_id") or ""),
                    "tag": f"support-{str(thread.get('thread_id') or '')[:12]}",
                    "admin_token": _admin_token(),
                }
            )
            print(
                f"[admin_push] support push sent={sent} thread={str(thread.get('thread_id') or '')[:8]}",
                flush=True,
            )
        except Exception as exc:
            log.warning("[admin_push] support notify error: %s", exc)

    threading.Thread(target=_run, daemon=True).start()


def notify_admin_push_lifemap_order(
    record: dict[str, Any], *, kind_label: str = "LifeMap"
) -> None:
    """One-shot browser push when a LifeMap / Pro report order is placed."""
    if not record:
        return

    def _run() -> None:
        try:
            oid = str(record.get("order_id") or "")
            urgent = bool(record.get("urgent"))
            cosmo = str(record.get("cosmo_user_id") or "").strip()
            snap = (
                record.get("engine_snapshot")
                if isinstance(record.get("engine_snapshot"), dict)
                else {}
            )
            p1 = record.get("p1") if isinstance(record.get("p1"), dict) else {}
            p2 = record.get("p2") if isinstance(record.get("p2"), dict) else {}
            person = record.get("person") if isinstance(record.get("person"), dict) else {}
            p1n = str(snap.get("p1_name") or p1.get("name") or "").strip()
            p2n = str(snap.get("p2_name") or p2.get("name") or "").strip()
            subject = (
                str(record.get("subject_name") or "").strip()
                or (f"{p1n} & {p2n}" if p1n and p2n else (p1n or p2n))
                or str(person.get("name") or "").strip()
                or "New booking"
            )
            eta = "Priority · 12h" if urgent else "Standard · 4–6 days"
            who = cosmo or "User"
            deliverable = str(record.get("deliverable") or "").strip().lower()
            plan = str(record.get("plan") or "").strip().lower()
            is_video = deliverable == "video" or plan == "vip" or str(
                record.get("contact_method") or ""
            ).strip().lower() == "whatsapp"
            if is_video:
                wa = str(record.get("contact_value") or "").strip()
                wa_bit = f" · WA +91{wa}" if wa else " · WA number missing"
                pub = str(record.get("public_order_id") or "").strip()
                oid_bit = f" · {pub}" if pub else ""
                body = (
                    f"{who} ne {kind_label} Personalized Video request kiya "
                    f"(WhatsApp · no PDF){wa_bit}{oid_bit} · {subject} · {eta}"
                )
                title = f"🎥 Video · {kind_label}"
            else:
                pub = str(record.get("public_order_id") or "").strip()
                oid_bit = f" · {pub}" if pub else ""
                body = (
                    f"{who} ne {kind_label} PDF request kiya{oid_bit} · {subject} · {eta}"
                )
                title = f"📄 PDF request · {kind_label}"
            if urgent:
                title = f"⚡ PRIORITY · {title}"
            sent = _push_to_all(
                {
                    "kind": "lifemap_order",
                    "title": title,
                    "body": body[:220],
                    "order_id": oid,
                    "public_order_id": str(record.get("public_order_id") or ""),
                    "tab": "lifemap",
                    "tag": f"lifemap-{oid[:12] or 'new'}",
                    "admin_token": _admin_token(),
                }
            )
            print(
                f"[admin_push] lifemap push sent={sent} kind={kind_label} order={oid[:8]}",
                flush=True,
            )
        except Exception as exc:
            log.warning("[admin_push] lifemap notify error: %s", exc)

    threading.Thread(target=_run, daemon=True).start()

"""
Cosmic Lens — Push Notification Helper (Expo Push API).

No Firebase Cloud Messaging credentials required — Expo handles delivery to
both Android (via FCM under the hood) and iOS (via APNs). We just hit
https://exp.host/api/v2/push/send with the user's ExpoPushToken.

Public API:
    send_push(tokens, title, body, data=None) -> dict
    send_to_user(user_id, title, body, data=None) -> dict
    broadcast(title, body, data=None, plan=None) -> dict
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable

import requests

log = logging.getLogger("notify")

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
_TIMEOUT = 8


def _is_expo_token(t: str | None) -> bool:
    if not t:
        return False
    return t.startswith("ExponentPushToken[") or t.startswith("ExpoPushToken[")


def send_push(
    tokens: str | Iterable[str],
    title: str,
    body: str,
    data: dict | None = None,
    sound: str | None = "default",
    priority: str = "high",
) -> dict:
    """
    Send to one or many Expo push tokens. Returns Expo response dict.
    Skips invalid tokens silently.
    """
    if isinstance(tokens, str):
        tokens = [tokens]

    valid = [t for t in tokens if _is_expo_token(t)]
    if not valid:
        return {"sent": 0, "skipped": "no valid tokens"}

    messages = [{
        "to":       t,
        "title":    title,
        "body":     body,
        "sound":    sound,
        "priority": priority,
        "data":     data or {},
        "channelId": "default",
    } for t in valid]

    try:
        resp = requests.post(
            EXPO_PUSH_URL,
            json=messages,
            headers={
                "Accept":           "application/json",
                "Accept-Encoding":  "gzip, deflate",
                "Content-Type":     "application/json",
            },
            timeout=_TIMEOUT,
        )
        return {
            "sent":     len(valid),
            "status":   resp.status_code,
            "response": resp.json() if resp.ok else resp.text[:300],
        }
    except Exception as exc:
        log.warning("[NOTIFY] Expo push failed: %s", exc)
        return {"sent": 0, "error": str(exc)}


def send_to_user(user_id: int, title: str, body: str, data: dict | None = None) -> dict:
    """Look up the user's saved push token and send."""
    from models import User  # local import to avoid circular
    user = User.query.get(int(user_id))
    if not user:
        return {"sent": 0, "error": "user not found"}
    if not user.push_enabled:
        return {"sent": 0, "skipped": "push disabled by user"}
    if not _is_expo_token(user.expo_push_token):
        return {"sent": 0, "skipped": "no token registered"}
    return send_push(user.expo_push_token, title, body, data)


def broadcast(
    title: str,
    body: str,
    data: dict | None = None,
    plan: str | None = None,
) -> dict:
    """
    Broadcast to all opted-in users. Optionally filter by plan
    ('pro', 'elite', etc.).
    """
    from models import User
    q = User.query.filter(
        User.push_enabled.is_(True),
        User.expo_push_token.isnot(None),
    )
    if plan:
        q = q.filter(User.plan == plan)
    tokens = [u.expo_push_token for u in q.all() if _is_expo_token(u.expo_push_token)]
    if not tokens:
        return {"sent": 0, "skipped": "no recipients"}

    # Expo accepts up to 100 messages per request — chunk
    sent_total = 0
    last_resp = None
    for i in range(0, len(tokens), 100):
        chunk = tokens[i:i + 100]
        r = send_push(chunk, title, body, data)
        sent_total += r.get("sent", 0)
        last_resp = r
    return {"sent": sent_total, "recipients": len(tokens), "last": last_resp}

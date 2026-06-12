"""Instant founder alerts when a Love Reality Pro manual PDF order is placed."""
from __future__ import annotations

import logging
import os
import threading
from typing import Any

import requests

log = logging.getLogger("order_alert")

_TIMEOUT = 10


def _lang_label(code: str) -> str:
    return {"en": "English", "hn": "Hinglish", "hi": "हिन्दी"}.get(
        (code or "en").lower(), code or "en"
    )


def _format_person_details(person: dict[str, Any], fallback_name: str) -> list[str]:
    """Name, DOB, birth time, place from Love Reality p1/p2 payload."""
    if not isinstance(person, dict):
        person = {}
    name = str(person.get("name") or fallback_name or "—").strip()
    lines = [f"• Name: {name}"]

    dob = ""
    try:
        y, m, d = int(person.get("year", 0)), int(person.get("month", 0)), int(person.get("day", 0))
        if y and m and d:
            dob = f"{d:02d}/{m:02d}/{y}"
    except (TypeError, ValueError):
        pass
    if dob:
        lines.append(f"• DOB: {dob}")

    tob = ""
    try:
        h, mn = int(person.get("hour", 0)), int(person.get("minute", 0))
        ampm = str(person.get("ampm") or "").upper().strip()
        if h or mn or ampm:
            tob = f"{h:02d}:{mn:02d}" + (f" {ampm}" if ampm else "")
    except (TypeError, ValueError):
        pass
    if tob:
        lines.append(f"• Time: {tob.strip()}")

    place = str(person.get("place") or person.get("pob") or "").strip()
    if place:
        lines.append(f"• Place: {place}")

    gender = str(person.get("gender") or "").strip()
    if gender:
        lines.append(f"• Gender: {gender}")

    return lines


def format_love_reality_order_alert(record: dict[str, Any]) -> str:
    snap = record.get("engine_snapshot") if isinstance(record.get("engine_snapshot"), dict) else {}
    p1 = record.get("p1") if isinstance(record.get("p1"), dict) else {}
    p2 = record.get("p2") if isinstance(record.get("p2"), dict) else {}
    p1_name = snap.get("p1_name") or p1.get("name") or "Person 1"
    p2_name = snap.get("p2_name") or p2.get("name") or "Person 2"
    urgent = bool(record.get("urgent"))
    method = str(record.get("contact_method") or "whatsapp")
    contact = str(record.get("contact_value") or "—")
    oid = str(record.get("order_id") or "")[:8]
    lang = _lang_label(str(record.get("lang") or "en"))

    lines = [
        "🛍️ New Love Reality Pro order",
        "",
        f"👤 Person 1 — {p1_name}",
        *_format_person_details(p1, str(p1_name)),
        "",
        f"👤 Person 2 — {p2_name}",
        *_format_person_details(p2, str(p2_name)),
        "",
        f"🌐 Report language: {lang}",
        f"{'⚡ Priority — 12 hours' if urgent else '📦 Standard — 24–48 hours'}",
        f"📲 Deliver on {method.title()}: {contact}",
        f"🆔 Order #{oid}",
    ]
    user_id = int(record.get("user_id") or 0)
    if user_id:
        lines.append(f"👥 App user ID: {user_id}")
    return "\n".join(lines)


def _send_telegram(text: str) -> bool:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = (os.environ.get("TELEGRAM_FOUNDER_CHAT_ID") or "").strip()
    if not token or not chat_id:
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
            timeout=_TIMEOUT,
        )
        if resp.ok:
            return True
        log.warning("[order_alert] Telegram failed: %s", resp.text[:200])
    except Exception as exc:
        log.warning("[order_alert] Telegram error: %s", exc)
    return False


def _send_msg91_sms(text: str) -> bool:
    auth_key = (os.environ.get("MSG91_AUTH_KEY") or "").strip()
    phone = (os.environ.get("FOUNDER_ALERT_PHONE") or "").strip()
    sender = (os.environ.get("MSG91_SENDER_ID") or "COSMIC").strip()[:6]
    if not auth_key or not phone:
        return False
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) == 10:
        digits = "91" + digits
    elif digits.startswith("91") and len(digits) == 12:
        pass
    else:
        log.warning("[order_alert] Invalid FOUNDER_ALERT_PHONE")
        return False
    sms_body = text.split("\n")[0]
    if len(sms_body) > 140:
        sms_body = sms_body[:137] + "..."
    try:
        resp = requests.get(
            "https://control.msg91.com/api/sendhttp.php",
            params={
                "authkey": auth_key,
                "mobiles": digits,
                "message": sms_body,
                "sender": sender,
                "route": "4",
                "country": "91",
            },
            timeout=_TIMEOUT,
        )
        return resp.ok
    except Exception as exc:
        log.warning("[order_alert] MSG91 error: %s", exc)
    return False


def _dispatch_alerts(record: dict[str, Any]) -> None:
    text = format_love_reality_order_alert(record)
    sent = _send_telegram(text)
    if not sent:
        _send_msg91_sms(text)
    try:
        print(f"[order_alert] founder notify telegram={sent} order={record.get('order_id')}", flush=True)
    except Exception:
        pass


def notify_founder_love_reality_order(record: dict[str, Any]) -> None:
    """Non-blocking alert — safe to call from request thread."""
    if not record:
        return
    has_telegram = bool(
        (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
        and (os.environ.get("TELEGRAM_FOUNDER_CHAT_ID") or "").strip()
    )
    has_sms = bool(
        (os.environ.get("MSG91_AUTH_KEY") or "").strip()
        and (os.environ.get("FOUNDER_ALERT_PHONE") or "").strip()
    )
    if not has_telegram and not has_sms:
        try:
            print(
                "[order_alert] skipped — set TELEGRAM_BOT_TOKEN + TELEGRAM_FOUNDER_CHAT_ID "
                "or MSG91_AUTH_KEY + FOUNDER_ALERT_PHONE in .env",
                flush=True,
            )
        except Exception:
            pass
        return
    threading.Thread(target=_dispatch_alerts, args=(record,), daemon=True).start()

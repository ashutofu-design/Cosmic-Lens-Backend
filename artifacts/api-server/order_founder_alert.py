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
        "📁 Deliver in My Reports (in-app)",
        f"🆔 Order #{oid}",
    ]
    user_id = int(record.get("user_id") or 0)
    cosmo_id = (str(record.get("cosmo_user_id") or "").strip().upper())
    if not cosmo_id and user_id:
        try:
            from cosmo_user_id import cosmo_display_id_for_user_id

            cosmo_id = cosmo_display_id_for_user_id(user_id)
        except Exception:
            cosmo_id = ""
    if cosmo_id:
        lines.append(f"👥 {cosmo_id}")
    lines.extend([
        "",
        "📝 Deliver (paste in Telegram):",
        f"MYREPORT {oid}",
        "",
        "(MY MILAN / MYMILAN bhi chalega — same command)",
        "(one-time — after deliver this order id expires; new report = new order)",
        "",
        "<paste full report in same message (80+ chars), or>",
        "<report part 1 — long? send part 2+ then reply DONE>",
    ])
    return "\n".join(lines)


def format_milan_order_alert(record: dict[str, Any]) -> str:
    snap = record.get("engine_snapshot") if isinstance(record.get("engine_snapshot"), dict) else {}
    p1 = record.get("p1") if isinstance(record.get("p1"), dict) else {}
    p2 = record.get("p2") if isinstance(record.get("p2"), dict) else {}
    p1_name = snap.get("p1_name") or p1.get("name") or "Person 1"
    p2_name = snap.get("p2_name") or p2.get("name") or "Person 2"
    urgent = bool(record.get("urgent"))
    oid = str(record.get("order_id") or "")[:8]
    lang = _lang_label(str(record.get("lang") or "en"))
    couple_score = snap.get("couple_score")
    couple_band = snap.get("couple_band") or "—"

    lines = [
        "💍 New Marriage Compatibility Pro order",
        "",
        f"👤 Person 1 — {p1_name}",
        *_format_person_details(p1, str(p1_name)),
        "",
        f"👤 Person 2 — {p2_name}",
        *_format_person_details(p2, str(p2_name)),
        "",
        f"📊 Couple score: {couple_score}/100 ({couple_band})" if couple_score is not None else f"📊 Couple band: {couple_band}",
        f"🌐 Report language: {lang}",
        f"{'⚡ Priority — 12 hours' if urgent else '📦 Standard — 24–48 hours'}",
        "📁 Deliver in My Reports (in-app)",
        f"🆔 Order #{oid}",
    ]
    user_id = int(record.get("user_id") or 0)
    cosmo_id = (str(record.get("cosmo_user_id") or "").strip().upper())
    if not cosmo_id and user_id:
        try:
            from cosmo_user_id import cosmo_display_id_for_user_id

            cosmo_id = cosmo_display_id_for_user_id(user_id)
        except Exception:
            cosmo_id = ""
    if cosmo_id:
        lines.append(f"👥 {cosmo_id}")
    lines.extend([
        "",
        "📝 Deliver (paste in Telegram):",
        f"MYREPORT {oid}",
        "",
        "(MY MILAN / MYMILAN bhi chalega — same command)",
        "(one-time — after deliver this order id expires; new report = new order)",
        "",
        "<paste full report in same message (80+ chars), or>",
        "<report part 1 — long? send part 2+ then reply DONE>",
    ])
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


def notify_founder_milan_order(record: dict[str, Any]) -> None:
    """Non-blocking alert for Marriage Compatibility Pro orders."""
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
        return

    def _run() -> None:
        text = format_milan_order_alert(record)
        sent = _send_telegram(text)
        if not sent:
            _send_msg91_sms(text)
        try:
            print(f"[order_alert] milan notify telegram={sent} order={record.get('order_id')}", flush=True)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()


def format_astrovastu_room_order_alert(record: dict[str, Any]) -> str:
    oid = str(record.get("order_id") or "")[:8]
    room = str(record.get("room_type") or "—")
    direction = str(record.get("direction") or "—")
    amount = record.get("amount_inr")
    cosmo = str(record.get("cosmo_user_id") or record.get("user_id") or "—")
    lines = [
        "🏠 New AstroVastu room upload (paid)",
        "",
        f"• Order: {oid}",
        f"• User: {cosmo}",
        f"• Room: {room}",
        f"• Direction: {direction}",
        f"• Amount: ₹{amount}" if amount else "• Amount: —",
        "",
        "Admin panel → AstroVastu room orders → review photo & upload report.",
    ]
    return "\n".join(lines)


def notify_founder_astrovastu_room_order(record: dict[str, Any]) -> None:
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
        return

    def _run() -> None:
        text = format_astrovastu_room_order_alert(record)
        sent = _send_telegram(text)
        if not sent:
            _send_msg91_sms(text)
        try:
            print(f"[order_alert] astrovastu room notify telegram={sent} order={record.get('order_id')}", flush=True)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()


def format_business_vastu_order_alert(record: dict[str, Any]) -> str:
    oid = str(record.get("order_id") or "")[:8]
    btype = str(record.get("business_type") or "—")
    prop = str(record.get("property_name") or "—")
    photos = record.get("room_photos") if isinstance(record.get("room_photos"), list) else []
    has_pdf = bool(
        isinstance(record.get("floor_plan_upload"), dict)
        and (
            record["floor_plan_upload"].get("data_url")
            or record["floor_plan_upload"].get("base64")
        )
    )
    cosmo = str(record.get("cosmo_user_id") or record.get("user_id") or "—")
    lines = [
        "🏪 New Business Vastu upload",
        "",
        f"• Order: {oid}",
        f"• User: {cosmo}",
        f"• Type: {btype}",
        f"• Premise: {prop}",
        f"• Room photos: {len(photos)}",
        f"• Full shop PDF: {'yes' if has_pdf else 'no'}",
        "",
        "Admin panel → Business Vastu orders → review photos & upload report.",
    ]
    return "\n".join(lines)


def notify_founder_business_vastu_order(record: dict[str, Any]) -> None:
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
        return

    def _run() -> None:
        text = format_business_vastu_order_alert(record)
        sent = _send_telegram(text)
        if not sent:
            _send_msg91_sms(text)
        try:
            print(
                f"[order_alert] business vastu notify telegram={sent} "
                f"order={record.get('order_id')}",
                flush=True,
            )
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()

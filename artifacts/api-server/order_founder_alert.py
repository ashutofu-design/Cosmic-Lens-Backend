"""Instant founder alerts when a Love Reality Pro manual PDF order is placed."""
from __future__ import annotations

import logging
import os
import threading
from typing import Any

import requests

log = logging.getLogger("order_alert")

_TIMEOUT = 10

# V3 live chat "continuous ring" — Telegram reminder pings until Accept/Reject.
V3_REMIND_INTERVAL_SECONDS = 12
V3_REMIND_MAX_SECONDS = 300  # 5 min tak har 12s pe ping


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
        f"{'⚡ Priority — 12 hours' if urgent else '📦 Standard — within 24 hours'}",
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
        "✅ Pehle Accept Order dabao (Telegram / Admin).",
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
        f"{'⚡ Priority — 12 hours' if urgent else '📦 Standard — within 24 hours'}",
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
        "✅ Pehle Accept Order dabao (Telegram / Admin).",
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


def _send_telegram_message_id(
    text: str, reply_markup: dict[str, Any] | None = None
) -> int | None:
    """Like _send_telegram but returns the sent message_id (for later delete)."""
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = (os.environ.get("TELEGRAM_FOUNDER_CHAT_ID") or "").strip()
    if not token or not chat_id:
        return None
    try:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json=payload,
            timeout=_TIMEOUT,
        )
        if resp.ok:
            return int((resp.json().get("result") or {}).get("message_id") or 0) or None
        log.warning("[order_alert] Telegram failed: %s", resp.text[:200])
    except Exception as exc:
        log.warning("[order_alert] Telegram error: %s", exc)
    return None


def _delete_telegram_message(message_id: int) -> None:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = (os.environ.get("TELEGRAM_FOUNDER_CHAT_ID") or "").strip()
    if not token or not chat_id or not message_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/deleteMessage",
            json={"chat_id": chat_id, "message_id": int(message_id)},
            timeout=_TIMEOUT,
        )
    except Exception:
        pass


def _send_telegram(text: str, reply_markup: dict[str, Any] | None = None) -> bool:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = (os.environ.get("TELEGRAM_FOUNDER_CHAT_ID") or "").strip()
    if not token or not chat_id:
        return False
    try:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json=payload,
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


# LifeMap Accept Order reminders (spaced — not V3-style rapid ring).
LIFEMAP_REMIND_INTERVAL_SECONDS = 5 * 60
LIFEMAP_REMIND_MAX_SECONDS = 30 * 60

_LIFEMAP_KIND_CODE = {
    "love_reality_pro": "lr",
    "milan_pro": "ml",
    "numerology_pro": "nm",
    "astrovastu_pro": "av",
    "business_vastu_pro": "bz",
}


def lifemap_accept_buttons(kind: str, order_id: str) -> dict[str, Any]:
    code = _LIFEMAP_KIND_CODE.get(kind) or kind
    oid = str(order_id or "").strip()
    # Telegram callback_data max 64 bytes — lma:lr:<uuid> ≈ 42 chars.
    return {
        "inline_keyboard": [
            [{"text": "✅ Accept Order", "callback_data": f"lma:{code}:{oid}"}]
        ]
    }


def _dispatch_lifemap_alerts(
    *,
    text: str,
    record: dict[str, Any],
    kind: str,
    kind_label: str,
) -> None:
    oid = str(record.get("order_id") or "").strip()
    buttons = lifemap_accept_buttons(kind, oid) if oid else None
    sent = _send_telegram(text, reply_markup=buttons)
    if not sent:
        _send_msg91_sms(text)
    try:
        from admin_push import notify_admin_push_lifemap_order

        notify_admin_push_lifemap_order(record, kind_label=kind_label)
    except Exception:
        pass
    try:
        print(
            f"[order_alert] {kind} notify telegram={sent} order={oid}",
            flush=True,
        )
    except Exception:
        pass

    if not sent or not oid or not buttons:
        return

    # Spaced reminders until Accept Order (Telegram or admin panel).
    import time as _time

    last_reminder_id: int | None = None
    waited = 0
    while waited < LIFEMAP_REMIND_MAX_SECONDS:
        _time.sleep(LIFEMAP_REMIND_INTERVAL_SECONDS)
        waited += LIFEMAP_REMIND_INTERVAL_SECONDS
        try:
            from lifemap_admin_deliver import is_lifemap_order_accepted

            if is_lifemap_order_accepted(kind, oid):
                if last_reminder_id:
                    _delete_telegram_message(last_reminder_id)
                break
        except Exception:
            break
        mins = waited // 60
        new_id = _send_telegram_message_id(
            f"🔔 LifeMap order still waiting — Accept Order dabao\n"
            f"{kind_label} · #{oid[:8]} · {mins} min\n"
            f"Admin: https://admin.coosmic.icu → LifeMap",
            reply_markup=buttons,
        )
        if last_reminder_id:
            _delete_telegram_message(last_reminder_id)
        if new_id:
            last_reminder_id = new_id


def _dispatch_alerts(record: dict[str, Any]) -> None:
    text = format_love_reality_order_alert(record)
    _dispatch_lifemap_alerts(
        text=text,
        record=record,
        kind="love_reality_pro",
        kind_label="Love Reality Pro",
    )


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
    # Always attempt web push; Telegram/SMS optional.
    if not has_telegram and not has_sms:
        try:
            from admin_push import notify_admin_push_lifemap_order

            notify_admin_push_lifemap_order(record, kind_label="Love Reality Pro")
        except Exception:
            pass
        try:
            print(
                "[order_alert] telegram/sms off — web push only "
                "(set TELEGRAM_BOT_TOKEN + TELEGRAM_FOUNDER_CHAT_ID for Telegram)",
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

    def _run() -> None:
        if not has_telegram and not has_sms:
            try:
                from admin_push import notify_admin_push_lifemap_order

                notify_admin_push_lifemap_order(record, kind_label="Kundli Milan Pro")
            except Exception:
                pass
            return
        text = format_milan_order_alert(record)
        _dispatch_lifemap_alerts(
            text=text,
            record=record,
            kind="milan_pro",
            kind_label="Kundli Milan Pro",
        )

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
        "✅ Pehle Accept Order dabao (Telegram / Admin).",
        "Admin panel → LifeMap → AstroVastu Pro → paste report → Deliver PDF.",
    ]
    return "\n".join(lines)


def format_numerology_order_alert(record: dict[str, Any]) -> str:
    oid = str(record.get("order_id") or "")[:8]
    person = record.get("person") if isinstance(record.get("person"), dict) else {}
    name = str(record.get("subject_name") or person.get("name") or "—")
    dob = str(person.get("dob") or "")
    lang = _lang_label(str(record.get("lang") or "en"))
    urgent = bool(record.get("urgent"))
    deliverable = str(record.get("deliverable") or "report").strip().lower()
    contact_method = str(record.get("contact_method") or "my_reports")
    contact_value = str(record.get("contact_value") or "")
    cosmo = str(record.get("cosmo_user_id") or record.get("user_id") or "—")
    product_line = (
        "🎬 Personalized Video Explanation (WhatsApp · no PDF)"
        if deliverable == "video"
        else "📄 Numerology Pro Report (PDF in My Reports)"
    )
    contact_line = (
        "• Delivery: WhatsApp (open admin panel)"
        if contact_method == "whatsapp"
        else "• Delivery: My Reports"
    )
    lines = [
        "🔢 New Numerology Pro order",
        "",
        product_line,
        f"• Name: {name}",
        f"• DOB: {dob}" if dob else "• DOB: —",
        f"• Language: {lang}",
        contact_line,
        f"{'⚡ Priority — 12 hours' if urgent else '📦 Standard — 4–6 business days'}",
        f"• User: {cosmo}",
        f"🆔 Order #{oid}",
        "",
        "✅ Pehle Accept Order dabao (Telegram / Admin).",
        (
            "Admin panel → LifeMap → Numerology Pro → send video on WhatsApp."
            if deliverable == "video"
            else "Admin panel → LifeMap → Numerology Pro → paste report → Deliver PDF."
        ),
    ]
    return "\n".join(lines)


def notify_founder_numerology_order(record: dict[str, Any]) -> None:
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

    def _run() -> None:
        if not has_telegram and not has_sms:
            try:
                from admin_push import notify_admin_push_lifemap_order

                notify_admin_push_lifemap_order(record, kind_label="Numerology Pro")
            except Exception:
                pass
            return
        text = format_numerology_order_alert(record)
        _dispatch_lifemap_alerts(
            text=text,
            record=record,
            kind="numerology_pro",
            kind_label="Numerology Pro",
        )

    threading.Thread(target=_run, daemon=True).start()


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

    def _run() -> None:
        if not has_telegram and not has_sms:
            try:
                from admin_push import notify_admin_push_lifemap_order

                notify_admin_push_lifemap_order(record, kind_label="AstroVastu Pro")
            except Exception:
                pass
            return
        text = format_astrovastu_room_order_alert(record)
        _dispatch_lifemap_alerts(
            text=text,
            record=record,
            kind="astrovastu_pro",
            kind_label="AstroVastu Pro",
        )

    threading.Thread(target=_run, daemon=True).start()


def format_v3_live_chat_alert(record: dict[str, Any]) -> str:
    sid = str(record.get("session_id") or "")[:8]
    label = str(record.get("label") or f"{record.get('minutes') or '—'} min")
    price = record.get("price_inr")
    name = str(record.get("user_name") or record.get("user_email") or "—")
    cosmo = str(record.get("cosmo_user_id") or record.get("user_id") or "—")
    lang_raw = str(record.get("preferred_language") or "").strip().lower()
    lang_label = {
        "hi": "हिंदी",
        "en": "English",
        "hn": "Hinglish",
    }.get(lang_raw, lang_raw)
    lines = [
        "⚡ New V3 LIVE CHAT request — user is waiting NOW",
        "",
        f"• User: {name}",
        f"• ID: {cosmo}",
    ]
    if lang_label:
        lines.append(f"• Language: {lang_label}")
    lines.extend(
        [
            f"• Pack: {label}" + (f" · ₹{price}" if price else ""),
            f"🆔 Session #{sid}",
            "",
            "Admin panel → V3 Live Chats → Accept (timer starts on accept).",
            "Jaldi accept karo — user live wait kar raha hai.",
        ]
    )
    return "\n".join(lines)


def notify_founder_v3_blocked_attempt(info: dict[str, Any]) -> None:
    """User tried to start a V3 live chat while chat is CLOSED.

    Fires on every attempt so the founder knows someone is actively trying to
    connect and can come online immediately. Telegram message carries an
    'Enable chat' button (callback v3o) that flips availability on the spot.
    """
    if not info:
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
        name = str(info.get("user_name") or info.get("user_email") or "—")
        cosmo = str(info.get("cosmo_user_id") or info.get("user_id") or "—")
        label = str(info.get("label") or "").strip()
        price = info.get("price_inr")
        attempt = int(info.get("attempt") or 1)
        lang_raw = str(info.get("preferred_language") or "").strip().lower()
        lang_label = {"hi": "हिंदी", "en": "English", "hn": "Hinglish"}.get(lang_raw, "")
        lines = [
            "🔴 V3 chat CLOSED hai — par ek user LIVE connect karne ki koshish kar raha hai!",
            "",
            f"• User: {name}",
            f"• ID: {cosmo}",
        ]
        if lang_label:
            lines.append(f"• Language: {lang_label}")
        if label:
            lines.append(f"• Pack: {label}" + (f" · ₹{price}" if price else ""))
        sid = str(info.get("session_id") or "").strip()
        qpos = info.get("queue_position")
        if sid:
            lines.append(f"🆔 Session #{sid[:8]}" + (f" · queue #{qpos}" if qpos else ""))
        lines.extend(
            [
                f"• Attempt: {attempt}" + (" (baar baar try kar raha hai!)" if attempt >= 2 else ""),
                "",
                "Accept dabao to user ko Ready notification jayega (timer user ke "
                "Accept par shuru hoga) — ya Enable chat karke admin panel kholo.",
            ]
        )
        text = "\n".join(lines)
        rows = []
        if sid:
            # Chat closed ho tab bhi admin seedha Accept/Reject kar sake.
            rows.append(
                [
                    {"text": "✅ Accept", "callback_data": f"v3a:{sid}"},
                    {"text": "❌ Reject", "callback_data": f"v3r:{sid}"},
                ]
            )
        rows.append([{"text": "🟢 Enable chat now", "callback_data": "v3o:open"}])
        buttons = {"inline_keyboard": rows}
        sent = _send_telegram(text, reply_markup=buttons)
        if not sent:
            _send_msg91_sms(text)
        try:
            print(
                f"[order_alert] v3 blocked-attempt notify telegram={sent} "
                f"user={info.get('user_id')} attempt={attempt}",
                flush=True,
            )
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()


def notify_founder_support_message(
    thread: dict[str, Any], message: dict[str, Any]
) -> None:
    """Telegram/SMS when a user sends a Help & Support chat message."""
    if not thread or not thread.get("escalated"):
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
        name = str(
            thread.get("user_name")
            or thread.get("user_email")
            or thread.get("cosmo_user_id")
            or "—"
        )
        tid = str(thread.get("thread_id") or "")[:8]
        preview = str(message.get("text") or "").strip()
        if not preview and message.get("image_url"):
            preview = "[Image attached]"
        lines = [
            "💬 HELP & SUPPORT — new message",
            f"• User: {name}",
            f"• Thread: #{tid}",
        ]
        if preview:
            lines.append(f"• Msg: {preview[:220]}")
        lines.append("Admin panel → Support inbox se reply karo.")
        text = "\n".join(lines)
        sent = _send_telegram(text)
        if not sent:
            _send_msg91_sms(text)

    threading.Thread(target=_run, daemon=True).start()


def notify_founder_v3_live_chat_request(record: dict[str, Any]) -> None:
    """Instant phone alert (Telegram/SMS) when a user books a V3 live session."""
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
                "[order_alert] v3 live chat alert skipped — set TELEGRAM_BOT_TOKEN + "
                "TELEGRAM_FOUNDER_CHAT_ID in .env",
                flush=True,
            )
        except Exception:
            pass
        return

    def _run() -> None:
        import time as _time

        text = format_v3_live_chat_alert(record)
        sid = str(record.get("session_id") or "")
        buttons = {
            "inline_keyboard": [
                [
                    {"text": "✅ Accept", "callback_data": f"v3a:{sid}"},
                    {"text": "❌ Reject", "callback_data": f"v3r:{sid}"},
                ]
            ]
        }
        sent = _send_telegram(text, reply_markup=buttons)
        if not sent:
            _send_msg91_sms(text)
        try:
            print(
                f"[order_alert] v3 live chat notify telegram={sent} "
                f"session={record.get('session_id')}",
                flush=True,
            )
        except Exception:
            pass
        if not sent or not sid:
            return

        # "Continuous ring": ping every V3_REMIND_INTERVAL_SECONDS until the
        # request is accepted/rejected (each ping = new notification sound).
        # Previous reminder is deleted so the chat stays clean — only the
        # original alert + latest reminder remain.
        name = str(record.get("user_name") or record.get("user_email") or "User")
        last_reminder_id: int | None = None
        waited = 0
        while waited < V3_REMIND_MAX_SECONDS:
            _time.sleep(V3_REMIND_INTERVAL_SECONDS)
            waited += V3_REMIND_INTERVAL_SECONDS
            try:
                from cosmic_intelligence_v3_sessions import get_v3_session

                rec = get_v3_session(sid)
            except Exception:
                break
            status = str((rec or {}).get("status") or "")
            # Keep ringing while still in FIFO queue (legacy pending = queued).
            if status not in ("pending", "queued"):
                if last_reminder_id:
                    _delete_telegram_message(last_reminder_id)
                break
            new_id = _send_telegram_message_id(
                f"🔔🔔 RING — {name} abhi bhi wait kar raha hai ({waited}s)\n"
                f"Session #{sid[:8]} — Accept ya Reject dabao 👇",
                reply_markup=buttons,
            )
            if last_reminder_id:
                _delete_telegram_message(last_reminder_id)
            if new_id:
                last_reminder_id = new_id

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
        "✅ Pehle Accept Order dabao (Telegram / Admin).",
        "Admin panel → LifeMap → Business Vastu → review photos → Deliver PDF.",
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
        _dispatch_lifemap_alerts(
            text=text,
            record=record,
            kind="business_vastu_pro",
            kind_label="Business Vastu",
        )

    threading.Thread(target=_run, daemon=True).start()

"""Telegram founder delivery — MYREPORT <order_id> + paragraph → user My Reports."""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from typing import Any

import requests
from flask import jsonify, request

from love_reality_founder_pdf import render_founder_love_reality_pdf

log = logging.getLogger("lr_telegram")

_TIMEOUT = 15
_POLL_OFFSET_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".cache", "telegram_poll_offset.json")
)
_POLL_LOCK_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".cache", "telegram_poll.lock")
)
_poller_started = False
_poll_lock_fh = None
_CMD_RE = re.compile(
    r"^(?:/)?(?:myreport|my\s*report|mymilan|my\s*milan)\s+#?([a-f0-9-]{6,36})\s*$",
    re.IGNORECASE,
)
_CMD_INLINE_RE = re.compile(
    r"^(?:/)?(?:myreport|my\s*report|mymilan|my\s*milan)\s+#?([a-f0-9-]{6,36})(?:\s+(.*))?$",
    re.IGNORECASE,
)
_DONE_RE = re.compile(r"^(?:/)?(?:done|send|publish|end)\s*$", re.IGNORECASE)
_PENDING_TTL_SEC = 900
_pending_lock = threading.Lock()
_pending: dict[str, dict[str, Any]] = {}
_pending_timers: dict[str, threading.Timer] = {}


def _love_orders_base() -> str:
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), ".cache", "love_reality_human_orders")
    )


def _milan_orders_base() -> str:
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), ".cache", "milan_human_orders")
    )


def _orders_base() -> str:
    return _love_orders_base()


def _order_base_for(record: dict[str, Any]) -> str:
    if str(record.get("product") or "").strip().lower() == "milan_pro":
        return _milan_orders_base()
    snap = record.get("engine_snapshot") if isinstance(record.get("engine_snapshot"), dict) else {}
    if "couple_score" in snap or "couple_band" in snap:
        return _milan_orders_base()
    return _love_orders_base()


def _is_milan_order(order: dict[str, Any]) -> bool:
    if str(order.get("product") or "").strip().lower() == "milan_pro":
        return True
    snap = order.get("engine_snapshot") if isinstance(order.get("engine_snapshot"), dict) else {}
    return "couple_score" in snap or "couple_band" in snap


def _matches_in_base(base: str, key: str) -> list[dict[str, Any]]:
    try:
        names = os.listdir(base)
    except OSError:
        return []
    matches: list[dict[str, Any]] = []
    for fn in names:
        if not fn.endswith(".json"):
            continue
        oid = fn.replace(".json", "")
        oid_key = oid.lower().replace("-", "")
        if oid_key.startswith(key) or key in oid_key:
            rec = _load_order_json(os.path.join(base, fn))
            if rec:
                matches.append(rec)
    return matches


def find_order_by_prefix(prefix: str) -> tuple[dict[str, Any] | None, str | None]:
    """Return (order, error). Searches Love + Marriage order folders."""
    key = (prefix or "").strip().lower().lstrip("#").replace("-", "")
    if len(key) < 6:
        return None, "order_id_too_short"
    matches = _matches_in_base(_love_orders_base(), key) + _matches_in_base(_milan_orders_base(), key)
    if not matches:
        return None, "order_not_found"
    if len(matches) > 1:
        return None, "ambiguous_order"
    return matches[0], None


def _order_is_delivered(order: dict[str, Any]) -> bool:
    return str(order.get("status") or "").strip().lower() == "delivered"


def _save_order(record: dict[str, Any]) -> None:
    base = _order_base_for(record)
    os.makedirs(base, exist_ok=True)
    oid = str(record.get("order_id") or "")
    path = os.path.join(base, f"{oid}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, ensure_ascii=False, indent=2)


def _load_order_json(path: str) -> dict[str, Any] | None:
    try:
        with open(path, encoding="utf-8") as fh:
            rec = json.load(fh)
        return rec if isinstance(rec, dict) else None
    except Exception:
        return None


def _person_dob(person: dict[str, Any]) -> str:
    try:
        y, m, d = int(person.get("year", 0)), int(person.get("month", 0)), int(person.get("day", 0))
        if y and m and d:
            return f"{y:04d}-{m:02d}-{d:02d}"
    except (TypeError, ValueError):
        pass
    return ""


def parse_myreport_message(text: str) -> tuple[str | None, str | None, str | None]:
    """
    Parse:
      MYREPORT abc12345

      Full report paragraph...
    Returns (order_prefix, body, error).
    Immediate single-shot mode — body must be 80+ chars.
    """
    prefix, body, err = _parse_myreport_start(text)
    if err:
        return None, None, err
    if not body:
        return prefix, None, "missing_body"
    if len(body) < 80:
        return prefix, body, "body_too_short"
    return prefix, body, None


def _parse_myreport_start(text: str) -> tuple[str | None, str | None, str | None]:
    """Parse MYREPORT header; body may be empty (multi-part follow-ups)."""
    raw = (text or "").strip()
    if not raw:
        return None, None, "empty_message"
    lines = raw.splitlines()
    first = (lines[0] or "").strip()
    m = _CMD_RE.match(first)
    inline_rest = ""
    if not m:
        m2 = _CMD_INLINE_RE.match(first)
        if not m2:
            return None, None, "not_myreport_command"
        inline_rest = (m2.group(2) or "").strip()
        prefix = m2.group(1).strip().lstrip("#")
    else:
        prefix = m.group(1).strip().lstrip("#")
    chunks = []
    if inline_rest:
        chunks.append(inline_rest)
    if len(lines) > 1:
        tail = "\n".join(lines[1:]).strip()
        if tail:
            chunks.append(tail)
    body = "\n\n".join(chunks).strip()
    return prefix, body or None, None


def _is_done_command(text: str) -> bool:
    return bool(_DONE_RE.match((text or "").strip()))


def _pending_get(chat_id: str) -> dict[str, Any] | None:
    if not chat_id:
        return None
    with _pending_lock:
        rec = _pending.get(chat_id)
        if not rec:
            return None
        if time.time() - float(rec.get("updated_at") or 0) > _PENDING_TTL_SEC:
            _pending.pop(chat_id, None)
            return None
        return dict(rec)


def _pending_clear(chat_id: str) -> None:
    with _pending_lock:
        _pending.pop(chat_id, None)
    timer = _pending_timers.pop(chat_id, None)
    if timer:
        timer.cancel()


def _pending_cancel_timer(chat_id: str) -> None:
    timer = _pending_timers.pop(chat_id, None)
    if timer:
        timer.cancel()


def _pending_append(chat_id: str, prefix: str, chunk: str) -> dict[str, Any]:
    chunk = (chunk or "").strip()
    now = time.time()
    with _pending_lock:
        rec = _pending.get(chat_id)
        if not rec or str(rec.get("prefix") or "") != prefix:
            rec = {"prefix": prefix, "parts": [], "updated_at": now}
        if chunk:
            rec["parts"].append(chunk)
        rec["updated_at"] = now
        _pending[chat_id] = rec
        return dict(rec)


def _pending_body(chat_id: str) -> str:
    rec = _pending_get(chat_id)
    if not rec:
        return ""
    return "\n\n".join(str(p) for p in (rec.get("parts") or []) if str(p).strip()).strip()


def _schedule_pending_deliver(chat_id: str) -> None:
    """No auto-publish — founder must reply DONE when report is complete."""
    _pending_cancel_timer(chat_id)


def _deliver_pending(chat_id: str, *, force: bool) -> str:
    if not force:
        return (
            "📝 Parts saved.\n"
            "Jab poora report ho jaye to DONE likhein — tabhi PDF publish hogi."
        )
    rec = _pending_get(chat_id)
    if not rec:
        return _format_error("not_myreport_command")
    body = _pending_body(chat_id)
    if not body:
        return _format_error("missing_body")
    if len(body) < 80:
        if force:
            return _format_error("body_too_short")
        return (
            "📝 Parts saved — report abhi chhota hai (<80 chars).\n"
            "Aur text bhejein, ya DONE likhein jab complete ho."
        )
    prefix = str(rec.get("prefix") or "")
    result = fulfill_order_with_founder_text(prefix, body)
    _pending_clear(chat_id)
    if not result.get("ok"):
        return _format_error(str(result.get("error") or "failed"))
    return _format_success(result)


def fulfill_order_with_founder_text(order_prefix: str, body_text: str) -> dict[str, Any]:
    order, err = find_order_by_prefix(order_prefix)
    if err:
        return {"ok": False, "error": err}
    assert order is not None

    if _order_is_delivered(order):
        return {"ok": False, "error": "order_already_delivered"}

    user_id = int(order.get("user_id") or 0)
    if not user_id:
        return {"ok": False, "error": "missing_user_id"}

    p1 = order.get("p1") if isinstance(order.get("p1"), dict) else {}
    p2 = order.get("p2") if isinstance(order.get("p2"), dict) else {}
    snap = order.get("engine_snapshot") if isinstance(order.get("engine_snapshot"), dict) else {}
    p1_name = str(snap.get("p1_name") or p1.get("name") or "You")
    p2_name = str(snap.get("p2_name") or p2.get("name") or "Partner")
    lang = str(order.get("lang") or "en")
    order_id = str(order.get("order_id") or "")
    is_milan = _is_milan_order(order)

    try:
        if is_milan:
            from milan_founder_pdf import render_founder_milan_pdf

            pdf_bytes = render_founder_milan_pdf(
                p1_name=p1_name,
                p2_name=p2_name,
                lang=lang,
                body_text=body_text,
                order_id=order_id,
            )
        else:
            pdf_bytes = render_founder_love_reality_pdf(
                p1_name=p1_name,
                p2_name=p2_name,
                lang=lang,
                body_text=body_text,
                order_id=order_id,
            )
    except Exception as exc:
        log.exception("[lr_telegram] pdf_render_failed order=%s", order_id[:8])
        return {"ok": False, "error": "pdf_render_failed", "detail": str(exc)}

    import report_cache as rc

    params = rc.couple_cache_params(lang, p1=p1, p2=p2)
    params["name"] = f"{p1_name} & {p2_name}"
    params["dob"] = _person_dob(p1) or _person_dob(p2)
    safe = re.sub(r"[^\w\-]+", "_", f"{p1_name}_{p2_name}")[:60]
    if is_milan:
        filename = f"Marriage_Compatibility_Pro_{safe}.pdf"
        kind = "milan_pro"
        report_type = "Marriage Compatibility Pro"
        push_title = "Marriage report ready"
        push_kind = "milan_pro"
    else:
        filename = f"Love_Reality_Pro_{safe}.pdf"
        kind = "love_reality_pro"
        report_type = "Love Reality Pro"
        push_title = "Love Reality report ready"
        push_kind = "love_reality_pro"

    report_id = rc.save(
        user_id=user_id,
        kind=kind,
        report_type=report_type,
        params=params,
        pdf_bytes=pdf_bytes,
        filename=filename,
    )
    if not report_id:
        return {"ok": False, "error": "report_save_failed"}

    now = datetime.now(timezone.utc).isoformat()
    order["status"] = "delivered"
    order["delivered_at"] = now
    order["report_id"] = report_id
    order["delivery_source"] = "telegram_myreport"
    _save_order(order)

    try:
        from notification_helper import send_to_user

        send_to_user(
            user_id,
            push_title,
            f"{p1_name} & {p2_name} — My Reports mein PDF save ho gayi.",
            data={
                "screen": "/my-reports",
                "kind": push_kind,
                "report_id": report_id,
            },
        )
    except Exception as exc:
        log.warning("[lr_telegram] push notify failed: %s", exc)

    cosmo_id = (str(order.get("cosmo_user_id") or "").strip().upper())
    if not cosmo_id and user_id:
        try:
            from cosmo_user_id import cosmo_display_id_for_user_id

            cosmo_id = cosmo_display_id_for_user_id(user_id)
        except Exception:
            cosmo_id = ""

    return {
        "ok": True,
        "order_id": order_id,
        "report_id": report_id,
        "user_id": user_id,
        "cosmo_user_id": cosmo_id,
        "p1_name": p1_name,
        "p2_name": p2_name,
        "bytes": len(pdf_bytes),
        "kind": push_kind,
    }


def _telegram_token() -> str:
    return (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()


def _founder_chat_id() -> str:
    return (os.environ.get("TELEGRAM_FOUNDER_CHAT_ID") or "").strip()


def _send_telegram_reply(chat_id: str | int, text: str) -> bool:
    token = _telegram_token()
    if not token:
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text[:4000], "disable_web_page_preview": True},
            timeout=_TIMEOUT,
        )
        return resp.ok
    except Exception as exc:
        log.warning("[lr_telegram] reply failed: %s", exc)
        return False


def _format_success(result: dict[str, Any]) -> str:
    cosmo = (str(result.get("cosmo_user_id") or "").strip().upper())
    user_line = f"👥 {cosmo}\n" if cosmo else ""
    icon = "💍" if str(result.get("kind") or "") == "milan_pro" else "💕"
    return (
        "✅ Delivered to My Reports\n"
        f"{user_line}"
        f"{icon} {result.get('p1_name')} & {result.get('p2_name')}\n"
        f"🆔 Order #{str(result.get('order_id') or '')[:8]}\n"
        f"📄 PDF {int(result.get('bytes') or 0) // 1024} KB saved"
    )


def _format_error(code: str) -> str:
    msgs = {
        "not_myreport_command": (
            "Use:\n"
            "MYREPORT <order_id>\n\n<report text>\n\n"
            "(MY MILAN / MYMILAN bhi chalega — Love + Marriage dono)\n"
            "Ek message mein poora report? Direct paste karo (80+ chars).\n"
            "Lamba report? Parts bhejo, last mein DONE."
        ),
        "missing_body": "Add report text after MYREPORT <order_id>, or send next message as part 2.",
        "body_too_short": "Report text too short — paste the full paragraph.",
        "order_not_found": "Order not found. Check the 8-char order id from the alert.",
        "order_already_delivered": (
            "Ye order pehle deliver ho chuka hai — yeh order id ab kaam nahi karegi.\n"
            "Nayi report ke liye app se naya order karein (naya order id alert mein aayega)."
        ),
        "ambiguous_order": "Multiple orders match — use a longer order id.",
        "order_id_too_short": "Order id too short — use at least 6 characters.",
        "missing_user_id": "Order has no app user id — cannot deliver.",
        "pdf_render_failed": "PDF conversion failed. Try again or shorten text.",
        "report_save_failed": "Could not save PDF to My Reports.",
    }
    return f"❌ {msgs.get(code, code)}"


def handle_founder_telegram_text(text: str, chat_id: str = "") -> str:
    """Single-shot deliver (admin API / tests)."""
    prefix, body, parse_err = parse_myreport_message(text)
    if parse_err:
        return _format_error(parse_err)
    assert prefix and body
    result = fulfill_order_with_founder_text(prefix, body)
    if not result.get("ok"):
        return _format_error(str(result.get("error") or "failed"))
    return _format_success(result)


def handle_founder_telegram_chat(text: str, chat_id: str) -> str:
    """
    Multi-part aware deliver for Telegram founder chat.
    MYREPORT starts a session; follow-up messages append; reply DONE to publish.
    """
    raw = (text or "").strip()
    if not raw:
        return _format_error("empty_message")

    if _is_done_command(raw):
        return _deliver_pending(chat_id, force=True)

    prefix, body, parse_err = _parse_myreport_start(raw)
    if prefix and not parse_err:
        order, order_err = find_order_by_prefix(prefix)
        if order_err:
            return _format_error(order_err)
        assert order is not None
        if _order_is_delivered(order):
            return _format_error("order_already_delivered")
        if body and len(body) >= 80:
            result = fulfill_order_with_founder_text(prefix, body)
            _pending_clear(chat_id)
            if not result.get("ok"):
                return _format_error(str(result.get("error") or "failed"))
            return _format_success(result)
        _pending_append(chat_id, prefix, body or "")
        total = len(_pending_body(chat_id))
        _schedule_pending_deliver(chat_id)
        return (
            "📝 Report started — order #" + prefix[:8] + "\n"
            f"Saved {total} characters.\n"
            "Aur parts bhejein, jab poora ho jaye to DONE likhein."
        )

    pending = _pending_get(chat_id)
    if pending:
        _pending_append(chat_id, str(pending.get("prefix") or ""), raw)
        total = len(_pending_body(chat_id))
        _schedule_pending_deliver(chat_id)
        return (
            f"📝 Part added — total {total} characters.\n"
            "Aur bhej sakte ho, ya DONE likh kar PDF publish karein."
        )

    if parse_err:
        return _format_error(parse_err)
    return _format_error("not_myreport_command")


def _process_update_async(update: dict[str, Any]) -> None:
    try:
        msg = update.get("message") or update.get("edited_message") or {}
        chat = msg.get("chat") or {}
        chat_id = str(chat.get("id") or "")
        founder = _founder_chat_id()
        if founder and chat_id != founder:
            return
        text = str(msg.get("text") or "").strip()
        if not text:
            return
        reply = handle_founder_telegram_chat(text, chat_id)
        if chat_id:
            _send_telegram_reply(chat_id, reply)
    except Exception as exc:
        log.exception("[lr_telegram] update failed: %s", exc)


def _polling_enabled() -> bool:
    """Default on — free lifetime delivery without domain/HTTPS webhook."""
    raw = (os.environ.get("TELEGRAM_USE_POLLING") or "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _polling_from_api_enabled() -> bool:
    """Gunicorn runs multiple workers — disable in API when using standalone poller."""
    raw = (os.environ.get("TELEGRAM_POLL_FROM_API") or "0").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _load_poll_offset() -> int:
    try:
        with open(_POLL_OFFSET_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        return int(data.get("offset") or 0)
    except Exception:
        return 0


def _save_poll_offset(offset: int) -> None:
    try:
        os.makedirs(os.path.dirname(_POLL_OFFSET_PATH), exist_ok=True)
        with open(_POLL_OFFSET_PATH, "w", encoding="utf-8") as fh:
            json.dump({"offset": int(offset)}, fh)
    except Exception as exc:
        log.warning("[lr_telegram] offset save failed: %s", exc)


def _clear_telegram_webhook() -> None:
    """Polling needs no webhook — clear any old HTTPS webhook."""
    token = _telegram_token()
    if not token:
        return
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/deleteWebhook",
            json={"drop_pending_updates": False},
            timeout=_TIMEOUT,
        )
        if not resp.ok:
            log.warning("[lr_telegram] deleteWebhook http=%s", resp.status_code)
    except Exception as exc:
        log.warning("[lr_telegram] deleteWebhook failed: %s", exc)


def _try_acquire_poll_lock() -> bool:
    """Only one gunicorn worker may poll — else Telegram returns HTTP 409."""
    global _poll_lock_fh
    if _poll_lock_fh is not None:
        return True
    try:
        import fcntl

        os.makedirs(os.path.dirname(_POLL_LOCK_PATH), exist_ok=True)
        fh = open(_POLL_LOCK_PATH, "w", encoding="utf-8")
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        fh.write(str(os.getpid()))
        fh.flush()
        _poll_lock_fh = fh
        return True
    except OSError:
        return False
    except Exception as exc:
        log.warning("[lr_telegram] poll lock failed: %s", exc)
        return False


def _poll_loop() -> None:
    token = _telegram_token()
    if not token:
        return
    _clear_telegram_webhook()
    offset = _load_poll_offset()
    log.info("[lr_telegram] polling started (DONE-only — reply DONE to publish)")
    while True:
        try:
            resp = requests.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                params={
                    "offset": offset,
                    "timeout": 50,
                    "allowed_updates": json.dumps(["message"]),
                },
                timeout=60,
            )
            if resp.status_code == 409:
                log.warning("[lr_telegram] getUpdates conflict (409) — clearing webhook")
                _clear_telegram_webhook()
                time.sleep(5)
                continue
            if not resp.ok:
                log.warning("[lr_telegram] getUpdates http=%s", resp.status_code)
                time.sleep(2)
                continue
            updates = resp.json().get("result") or []
            for upd in updates:
                try:
                    upd_id = int(upd.get("update_id") or 0)
                    if upd_id >= offset:
                        offset = upd_id + 1
                    _process_update_async(upd)
                except Exception as exc:
                    log.exception("[lr_telegram] poll update: %s", exc)
            if updates:
                _save_poll_offset(offset)
        except Exception as exc:
            log.warning("[lr_telegram] poll error: %s", exc)


def start_telegram_polling_if_enabled() -> None:
    """Background long-poll — works forever on VPS without domain."""
    global _poller_started
    if _poller_started:
        return
    if not _polling_enabled() or not _polling_from_api_enabled():
        return
    if not _telegram_token() or not _founder_chat_id():
        try:
            print(
                "[lr_telegram] polling skipped — set TELEGRAM_BOT_TOKEN + "
                "TELEGRAM_FOUNDER_CHAT_ID",
                flush=True,
            )
        except Exception:
            pass
        return
    if not _try_acquire_poll_lock():
        log.info("[lr_telegram] polling skipped — another worker is polling")
        return
    _poller_started = True
    threading.Thread(target=_poll_loop, name="telegram-lr-poll", daemon=True).start()


def register_telegram_deliver_routes(flask_app) -> None:
    if "telegram_love_reality_webhook" not in flask_app.view_functions:
        secret = (os.environ.get("TELEGRAM_WEBHOOK_SECRET") or "cosmic-lens-lr").strip()

        @flask_app.route(f"/api/telegram/webhook/<secret>", methods=["POST"])
        def telegram_love_reality_webhook(secret: str):  # noqa: ARG001
            expected = (os.environ.get("TELEGRAM_WEBHOOK_SECRET") or "cosmic-lens-lr").strip()
            if secret != expected:
                return jsonify({"error": "forbidden"}), 403
            update = request.get_json(silent=True) or {}
            threading.Thread(target=_process_update_async, args=(update,), daemon=True).start()
            return jsonify({"ok": True}), 200

        @flask_app.route("/api/love-reality/founder-deliver", methods=["POST", "OPTIONS"])
        def love_reality_founder_deliver_manual():
            """Manual/test deliver — requires X-Admin-Key or founder telegram secret header."""
            if request.method == "OPTIONS":
                return "", 204
            admin_key = (os.environ.get("ADMIN_API_KEY") or "").strip()
            hdr = (request.headers.get("X-Admin-Key") or "").strip()
            if not admin_key or hdr != admin_key:
                return jsonify({"error": "forbidden"}), 403
            data = request.get_json(silent=True) or {}
            prefix = str(data.get("order_id") or data.get("order_prefix") or "").strip()
            body = str(data.get("body") or data.get("text") or "").strip()
            if not prefix or not body:
                return jsonify({"error": "expected_order_id_and_body"}), 400
            result = fulfill_order_with_founder_text(prefix, body)
            if not result.get("ok"):
                return jsonify(result), 400
            return jsonify(result), 200

    start_telegram_polling_if_enabled()

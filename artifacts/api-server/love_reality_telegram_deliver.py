"""Telegram founder delivery — MYREPORT <order_id> + paragraph → user My Reports."""
from __future__ import annotations

import json
import logging
import os
import re
import threading
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
_poller_started = False
_CMD_RE = re.compile(
    r"^(?:/)?(?:myreport|my\s*report)\s+([a-f0-9-]{6,36})\s*$",
    re.IGNORECASE,
)


def _orders_base() -> str:
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), ".cache", "love_reality_human_orders")
    )


def _load_order_json(path: str) -> dict[str, Any] | None:
    try:
        with open(path, encoding="utf-8") as fh:
            rec = json.load(fh)
        return rec if isinstance(rec, dict) else None
    except Exception:
        return None


def find_order_by_prefix(prefix: str) -> tuple[dict[str, Any] | None, str | None]:
    """Return (order, error). error set when ambiguous."""
    key = (prefix or "").strip().lower().replace("-", "")
    if len(key) < 6:
        return None, "order_id_too_short"
    base = _orders_base()
    try:
        names = os.listdir(base)
    except OSError:
        return None, "no_orders"
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
    if not matches:
        return None, "order_not_found"
    if len(matches) > 1:
        return None, "ambiguous_order"
    return matches[0], None


def _save_order(record: dict[str, Any]) -> None:
    base = _orders_base()
    os.makedirs(base, exist_ok=True)
    oid = str(record.get("order_id") or "")
    path = os.path.join(base, f"{oid}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, ensure_ascii=False, indent=2)


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
    """
    raw = (text or "").strip()
    if not raw:
        return None, None, "empty_message"
    lines = raw.splitlines()
    first = (lines[0] or "").strip()
    m = _CMD_RE.match(first)
    if not m:
        return None, None, "not_myreport_command"
    prefix = m.group(1).strip()
    body = "\n".join(lines[1:]).strip()
    if not body:
        return prefix, None, "missing_body"
    if len(body) < 80:
        return prefix, body, "body_too_short"
    return prefix, body, None


def fulfill_order_with_founder_text(order_prefix: str, body_text: str) -> dict[str, Any]:
    order, err = find_order_by_prefix(order_prefix)
    if err:
        return {"ok": False, "error": err}
    assert order is not None

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

    try:
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
    filename = f"Love_Reality_Pro_{safe}.pdf"

    report_id = rc.save(
        user_id=user_id,
        kind="love_reality_pro",
        report_type="Love Reality Pro",
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

    return {
        "ok": True,
        "order_id": order_id,
        "report_id": report_id,
        "user_id": user_id,
        "p1_name": p1_name,
        "p2_name": p2_name,
        "bytes": len(pdf_bytes),
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
    return (
        "✅ Delivered to My Reports\n"
        f"👥 User #{result.get('user_id')}\n"
        f"💕 {result.get('p1_name')} & {result.get('p2_name')}\n"
        f"🆔 Order #{str(result.get('order_id') or '')[:8]}\n"
        f"📄 PDF {int(result.get('bytes') or 0) // 1024} KB saved"
    )


def _format_error(code: str) -> str:
    msgs = {
        "not_myreport_command": (
            "Use:\nMYREPORT <order_id>\n\n<full report paragraph>"
        ),
        "missing_body": "Add report text after the first line (MYREPORT <order_id>).",
        "body_too_short": "Report text too short — paste the full paragraph.",
        "order_not_found": "Order not found. Check the 8-char order id from the alert.",
        "ambiguous_order": "Multiple orders match — use a longer order id.",
        "order_id_too_short": "Order id too short — use at least 6 characters.",
        "missing_user_id": "Order has no app user id — cannot deliver.",
        "pdf_render_failed": "PDF conversion failed. Try again or shorten text.",
        "report_save_failed": "Could not save PDF to My Reports.",
    }
    return f"❌ {msgs.get(code, code)}"


def handle_founder_telegram_text(text: str) -> str:
    prefix, body, parse_err = parse_myreport_message(text)
    if parse_err:
        return _format_error(parse_err)
    assert prefix and body
    result = fulfill_order_with_founder_text(prefix, body)
    if not result.get("ok"):
        return _format_error(str(result.get("error") or "failed"))
    return _format_success(result)


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
        reply = handle_founder_telegram_text(text)
        if chat_id:
            _send_telegram_reply(chat_id, reply)
    except Exception as exc:
        log.exception("[lr_telegram] update failed: %s", exc)


def _polling_enabled() -> bool:
    """Default on — free lifetime delivery without domain/HTTPS webhook."""
    raw = (os.environ.get("TELEGRAM_USE_POLLING") or "1").strip().lower()
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
        requests.post(
            f"https://api.telegram.org/bot{token}/deleteWebhook",
            json={"drop_pending_updates": False},
            timeout=_TIMEOUT,
        )
    except Exception as exc:
        log.warning("[lr_telegram] deleteWebhook failed: %s", exc)


def _poll_loop() -> None:
    token = _telegram_token()
    if not token:
        return
    _clear_telegram_webhook()
    offset = _load_poll_offset()
    log.info("[lr_telegram] polling started (no domain/HTTPS needed)")
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
            if not resp.ok:
                log.warning("[lr_telegram] getUpdates http=%s", resp.status_code)
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
    if not _polling_enabled():
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

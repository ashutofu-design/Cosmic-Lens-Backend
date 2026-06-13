"""Telegram founder delivery — MYMILAN <order_id> + report text → user My Reports."""
from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any

from flask import jsonify, request

from milan_founder_pdf import render_founder_milan_pdf

log = logging.getLogger("milan_telegram")

_CMD_RE = re.compile(
    r"^(?:/)?(?:mymilan|my\s*milan)\s+#?([a-f0-9-]{6,36})\s*$",
    re.IGNORECASE,
)
_CMD_INLINE_RE = re.compile(
    r"^(?:/)?(?:mymilan|my\s*milan)\s+#?([a-f0-9-]{6,36})(?:\s+(.*))?$",
    re.IGNORECASE,
)
_DONE_RE = re.compile(r"^(?:/)?(?:done|send|publish|end)\s*$", re.IGNORECASE)
_PENDING_TTL_SEC = 900
_pending_lock = __import__("threading").Lock()
_pending: dict[str, dict[str, Any]] = {}


def _orders_base() -> str:
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), ".cache", "milan_human_orders")
    )


def is_milan_telegram_command(text: str) -> bool:
    """True when first line looks like MYMILAN / MY MILAN (multi-line body ignored)."""
    raw = (text or "").strip()
    if not raw:
        return False
    first = (raw.splitlines()[0] or "").strip()
    return bool(_CMD_RE.match(first) or _CMD_INLINE_RE.match(first))


def _load_order_json(path: str) -> dict[str, Any] | None:
    try:
        with open(path, encoding="utf-8") as fh:
            rec = json.load(fh)
        return rec if isinstance(rec, dict) else None
    except Exception:
        return None


def find_milan_order_by_prefix(prefix: str) -> tuple[dict[str, Any] | None, str | None]:
    key = (prefix or "").strip().lower().lstrip("#").replace("-", "")
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


def _order_is_delivered(order: dict[str, Any]) -> bool:
    return str(order.get("status") or "").strip().lower() == "delivered"


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


def _parse_mymilan_start(text: str) -> tuple[str | None, str | None, str | None]:
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
            return None, None, "not_mymilan_command"
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


def _pending_append(chat_id: str, prefix: str, chunk: str) -> None:
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


def _pending_body(chat_id: str) -> str:
    rec = _pending_get(chat_id)
    if not rec:
        return ""
    return "\n\n".join(str(p) for p in (rec.get("parts") or []) if str(p).strip()).strip()


def fulfill_milan_order_with_founder_text(order_prefix: str, body_text: str) -> dict[str, Any]:
    order, err = find_milan_order_by_prefix(order_prefix)
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
    p1_name = str(snap.get("p1_name") or p1.get("name") or "Partner A")
    p2_name = str(snap.get("p2_name") or p2.get("name") or "Partner B")
    lang = str(order.get("lang") or "en")
    order_id = str(order.get("order_id") or "")

    try:
        pdf_bytes = render_founder_milan_pdf(
            p1_name=p1_name,
            p2_name=p2_name,
            lang=lang,
            body_text=body_text,
            order_id=order_id,
        )
    except Exception as exc:
        log.exception("[milan_telegram] pdf_render_failed order=%s", order_id[:8])
        return {"ok": False, "error": "pdf_render_failed", "detail": str(exc)}

    import report_cache as rc

    params = rc.couple_cache_params(lang, p1=p1, p2=p2)
    params["name"] = f"{p1_name} & {p2_name}"
    params["dob"] = _person_dob(p1) or _person_dob(p2)
    safe = re.sub(r"[^\w\-]+", "_", f"{p1_name}_{p2_name}")[:60]
    filename = f"Marriage_Compatibility_Pro_{safe}.pdf"

    report_id = rc.save(
        user_id=user_id,
        kind="milan_pro",
        report_type="Marriage Compatibility Pro",
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
    order["delivery_source"] = "telegram_mymilan"
    _save_order(order)

    try:
        from notification_helper import send_to_user

        send_to_user(
            user_id,
            "Marriage report ready",
            f"{p1_name} & {p2_name} — My Reports mein PDF save ho gayi.",
            data={"screen": "/my-reports", "kind": "milan_pro", "report_id": report_id},
        )
    except Exception as exc:
        log.warning("[milan_telegram] push notify failed: %s", exc)

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
    }


def _format_success(result: dict[str, Any]) -> str:
    cosmo = (str(result.get("cosmo_user_id") or "").strip().upper())
    user_line = f"👥 {cosmo}\n" if cosmo else ""
    return (
        "✅ Marriage report delivered to My Reports\n"
        f"{user_line}"
        f"💍 {result.get('p1_name')} & {result.get('p2_name')}\n"
        f"🆔 Order #{str(result.get('order_id') or '')[:8]}\n"
        f"📄 PDF {int(result.get('bytes') or 0) // 1024} KB saved"
    )


def _format_error(code: str) -> str:
    msgs = {
        "not_mymilan_command": (
            "Use:\nMYMILAN <order_id>\n\n<report text>\n\n"
            "Long report? Send part 1, then part 2+ — reply DONE to publish."
        ),
        "missing_body": "Add report text after MYMILAN <order_id>, or send next message as part 2.",
        "body_too_short": "Report text too short — paste the full paragraph.",
        "order_not_found": "Order not found. Check the 8-char order id from the alert.",
        "order_already_delivered": "Ye order pehle deliver ho chuka hai — naya order karein app se.",
        "ambiguous_order": "Multiple orders match — use a longer order id.",
        "order_id_too_short": "Order id too short — use at least 6 characters.",
        "missing_user_id": "Order has no app user id — cannot deliver.",
        "pdf_render_failed": "PDF conversion failed. Try again or shorten text.",
        "report_save_failed": "Could not save PDF to My Reports.",
        "empty_message": "Empty message.",
    }
    return f"❌ {msgs.get(code, code)}"


def _deliver_pending(chat_id: str, *, force: bool) -> str:
    rec = _pending_get(chat_id)
    if not rec:
        return _format_error("not_mymilan_command")
    body = _pending_body(chat_id)
    if not body:
        return _format_error("missing_body")
    if len(body) < 80:
        return (
            "📝 Parts saved — report abhi chhota hai (<80 chars).\n"
            "Aur text bhejein, ya DONE likhein jab complete ho."
        )
    prefix = str(rec.get("prefix") or "")
    result = fulfill_milan_order_with_founder_text(prefix, body)
    _pending_clear(chat_id)
    if not result.get("ok"):
        return _format_error(str(result.get("error") or "failed"))
    return _format_success(result)


def handle_founder_milan_telegram_chat(text: str, chat_id: str) -> str:
    """Delegate to unified Love+Marriage handler (MYREPORT / MYMILAN / MY MILAN)."""
    from love_reality_telegram_deliver import handle_founder_telegram_chat

    return handle_founder_telegram_chat(text, chat_id)


def register_milan_telegram_routes(flask_app) -> None:
    if "kundli_milan_founder_deliver_manual" in flask_app.view_functions:
        return

    @flask_app.route("/api/kundli-milan/founder-deliver", methods=["POST", "OPTIONS"])
    def kundli_milan_founder_deliver_manual():
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
        from love_reality_telegram_deliver import fulfill_order_with_founder_text

        result = fulfill_order_with_founder_text(prefix, body)
        if not result.get("ok"):
            return jsonify(result), 400
        return jsonify(result), 200

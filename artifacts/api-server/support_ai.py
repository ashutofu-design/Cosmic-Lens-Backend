"""Help & Support Flask entry. Always save a bot reply before the HTTP response returns."""
from __future__ import annotations

import logging
import threading
from typing import Any

log = logging.getLogger("support_ai")

_WAIT = {
    "en": "I couldn’t fully resolve this here. Customer support will join this chat shortly — please wait, they’ll reply here.",
    "hn": "Yeh yahan clear nahi ho paaya. Customer support abhi is chat mein aayenge — thoda wait kariye, yahin reply aayega.",
    "hi": "यह यहाँ पूरा हल नहीं हो पाया। कस्टमर सपोर्ट अभी इस चैट में आएंगे — थोड़ा इंतज़ार करें, यहीं जवाब आएगा।",
}


def detect_reply_lang(text: str, preferred: str | None = None) -> str:
    try:
        from support_agent.intent import detect_lang

        return detect_lang(text, preferred)
    except Exception:
        v = (preferred or "").strip().lower()
        return v if v in ("en", "hn", "hi") else "hn"


def wait_for_support_reply(lang: str) -> str:
    L = lang if lang in _WAIT else "hn"
    return _WAIT[L]


def human_is_handling(msgs: list[Any] | None) -> bool:
    """True only if a human agent is currently in this chat (last staff msg is admin)."""
    found_latest_user = False
    for m in reversed(msgs or []):
        if not isinstance(m, dict):
            continue
        who = str(m.get("sender") or "")
        if who not in ("admin", "bot", "user"):
            continue
        if not found_latest_user:
            if who == "user":
                found_latest_user = True
                continue
            return who == "admin"
        if who == "user":
            continue
        return who == "admin"
    return False


def scrub_customer_reply(reply: str, lang: str) -> str:
    """Leak filter only — does not choose the answer."""
    from support_agent.response_guard import guard

    text, leaked = guard(reply or "", lang)
    if leaked or not (text or "").strip():
        from support_agent.escalation import fallback_help_reply

        text, _ = guard(fallback_help_reply(lang), lang)
    return text


def _quick_reply(text: str, lang: str | None) -> str:
    from support_agent.escalation import fallback_help_reply
    from support_agent.response_guard import guard

    L = detect_reply_lang(text, lang)
    reply, _ = guard(fallback_help_reply(L), L)
    return reply


def answer_support(
    text: str,
    *,
    lang: str | None = None,
    has_image: bool = False,
    history: list[dict[str, Any]] | None = None,
    cosmo_user_id: str = "",
    account_card: str = "",
    user: Any = None,
) -> dict[str, Any]:
    """AI reads the question and answers from allowed knowledge + this account."""
    from support_agent.agent import run

    L = detect_reply_lang(text, lang)
    try:
        out = run(
            text,
            lang=lang,
            has_image=has_image,
            history=history,
            user=user,
            account_card=account_card,
            cosmo_user_id=cosmo_user_id,
        )
    except Exception:
        log.exception("[support_ai] run failed")
        return {
            "escalate": False,
            "reply": _quick_reply(text, L),
            "source": "error",
        }
    reply = scrub_customer_reply(str(out.get("reply") or ""), L)
    if not reply.strip():
        reply = _quick_reply(text, L)
    return {
        "escalate": bool(out.get("escalate")) if str(out.get("source") or "") == "llm" else False,
        "reply": reply,
        "source": str(out.get("source") or ""),
        "intent": out.get("intent") or "",
    }


def maybe_auto_reply(
    rec: dict[str, Any],
    user_msg: dict[str, Any],
    *,
    lang: str | None = None,
    cosmo_user_id: str = "",
    account_card: str = "",
    min_think: float | None = None,
    user: Any = None,
) -> dict[str, Any]:
    """Save a real bot answer immediately, then let AI upgrade it in the background."""
    msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
    if human_is_handling(msgs):
        return {"handled": False, "escalate": True, "source": "human_live"}

    from support_chat import append_message, mark_escalated

    tid = str(rec.get("thread_id") or "")
    text = str(user_msg.get("text") or "")
    has_image = bool(user_msg.get("image_url"))
    cid = (cosmo_user_id or str(rec.get("cosmo_user_id") or "")).strip()
    L = detect_reply_lang(text, lang)
    quick = _quick_reply(text, L)
    bot = append_message(tid, sender="bot", text=quick)
    if not bot.get("ok"):
        return {"handled": False, "escalate": False, "source": "append_failed", "reply": quick}

    def _upgrade() -> None:
        try:
            decision = answer_support(
                text,
                lang=lang,
                has_image=has_image,
                history=msgs,
                cosmo_user_id=cid,
                account_card=account_card,
                user=user,
            )
            reply = str(decision.get("reply") or "").strip()
            if not reply or reply == quick:
                return
            extra = append_message(tid, sender="bot", text=reply)
            if extra.get("ok") and decision.get("escalate"):
                mark_escalated(tid)
        except Exception:
            log.exception("[support_ai] background AI upgrade failed")

    threading.Thread(target=_upgrade, daemon=True, name="support-ai-upgrade").start()
    return {
        "handled": True,
        "pending": False,
        "escalate": False,
        "reply": quick,
        "source": "quick",
    }

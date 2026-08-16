"""Help & Support Flask entry — bounded agent with server-side lifecycle."""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("support_ai")

_WAIT = {
    "en": "I’m unable to resolve this directly. A team member will join shortly — please wait here.",
    "hn": "Yeh yahan solve nahi ho paaya. Team member abhi is chat mein aayenge — yahin wait kariye.",
    "hi": "यह यहाँ हल नहीं हो पाया। टीम सदस्य जल्द इस चैट में आएंगे — यहीं प्रतीक्षा करें।",
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
    from support_agent.response_guard import guard

    text, leaked = guard(reply or "", lang)
    if leaked or not (text or "").strip():
        return wait_for_support_reply(lang)
    return text


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
            "escalate": True,
            "reply": wait_for_support_reply(L),
            "source": "error",
            "agent_state": "waiting_for_human",
        }
    reply = scrub_customer_reply(str(out.get("reply") or ""), L)
    if not reply.strip():
        reply = wait_for_support_reply(L)
        return {
            "escalate": True,
            "reply": reply,
            "source": "empty",
            "agent_state": "waiting_for_human",
        }
    escalate = bool(out.get("escalate"))
    return {
        "escalate": escalate,
        "reply": reply,
        "source": str(out.get("source") or ""),
        "intent": out.get("intent") or "",
        "agent_state": str(out.get("agent_state") or ("waiting_for_human" if escalate else "answered")),
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
    """processing → tools+knowledge → answered | waiting_for_human. No fake replies."""
    from support_chat import append_message, mark_escalated, set_agent_state

    msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
    tid = str(rec.get("thread_id") or "")
    if human_is_handling(msgs):
        set_agent_state(tid, "waiting_for_human")
        return {"handled": False, "escalate": True, "source": "human_live", "agent_state": "waiting_for_human"}

    text = str(user_msg.get("text") or "")
    has_image = bool(user_msg.get("image_url"))
    cid = (cosmo_user_id or str(rec.get("cosmo_user_id") or "")).strip()
    set_agent_state(tid, "processing")
    decision = answer_support(
        text,
        lang=lang,
        has_image=has_image,
        history=msgs,
        cosmo_user_id=cid,
        account_card=account_card,
        user=user,
    )
    reply = str(decision.get("reply") or "").strip() or wait_for_support_reply(
        detect_reply_lang(text, lang)
    )
    bot = append_message(tid, sender="bot", text=reply)
    if not bot.get("ok"):
        set_agent_state(tid, "failed")
        return {"handled": False, "escalate": True, "source": "append_failed", "reply": reply}

    escalate = bool(decision.get("escalate"))
    state = "waiting_for_human" if escalate else "answered"
    set_agent_state(tid, state)
    if escalate:
        mark_escalated(tid)
    return {
        "handled": True,
        "pending": False,
        "escalate": escalate,
        "reply": reply,
        "source": str(decision.get("source") or "llm"),
        "agent_state": state,
    }

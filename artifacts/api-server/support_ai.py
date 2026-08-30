"""Help & Support Flask entry — bounded agent with server-side lifecycle."""
from __future__ import annotations

import logging
import re
from typing import Any

log = logging.getLogger("support_ai")

_WAIT = {
    "en": "I’m unable to resolve this directly. A team member will join shortly — please wait here.",
    "hn": "Yeh yahan solve nahi ho paaya. Team member abhi is chat mein aayenge — yahin wait kariye.",
    "hi": "यह यहाँ हल नहीं हो पाया। टीम सदस्य जल्द इस चैट में आएंगे — यहीं प्रतीक्षा करें।",
}

_STILL_WAITING = {
    "en": "Our team already has your chat. Please wait here — they’ll reply in this thread.",
    "hn": "Team ke paas aapka chat already hai. Yahin wait kariye — isi thread me reply aayega.",
    "hi": "टीम के पास आपकी चैट पहले से है। यहीं प्रतीक्षा करें — इसी थ्रेड में जवाब आएगा।",
}


def detect_reply_lang(text: str, preferred: str | None = None) -> str:
    try:
        from support_agent.intent import detect_lang, reply_lang

        return reply_lang(detect_lang(text, preferred))
    except Exception:
        v = (preferred or "").strip().lower()
        return "en" if v == "en" else "hn"


def wait_for_support_reply(lang: str) -> str:
    L = "en" if (lang or "").strip().lower() == "en" else "hn"
    return _WAIT[L]


def still_waiting_reply(lang: str) -> str:
    L = "en" if (lang or "").strip().lower() == "en" else "hn"
    return _STILL_WAITING[L]


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


def scrub_customer_reply(reply: str, lang: str, user_text: str = "") -> str:
    from support_agent.response_guard import guard

    text, leaked = guard(reply or "", lang, user_text)
    if leaked:
        return wait_for_support_reply(lang)
    if not (text or "").strip():
        # Do not invent handoff when strip emptied a real reply — keep original brief
        raw = (reply or "").strip()
        return raw[:500] if raw else wait_for_support_reply(lang)
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
            lang=L,  # detected from message, not preferred alone
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
    reply = scrub_customer_reply(str(out.get("reply") or ""), L, text)
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
        "relation": out.get("relation") or "",
        "agent_state": str(out.get("agent_state") or ("waiting_for_human" if escalate else "answered")),
    }


_HARD_WAIT = re.compile(
    r"(?i)\b("
    r"refund|chargeback|fraud|legal|lawyer|"
    r"paid.*(no|not|missing)|money\s+cut|payment\s+failed|"
    r"pdf\s+missing|report\s+missing|nahi\s+mila|nahi\s+aaya|"
    r"team\s+se\s+baat|speak\s+to\s+(support|team|human)|"
    r"human\s+please|agent\s+chahiye"
    r")\b"
)


def _wants_hard_wait(text: str, *, has_image: bool) -> bool:
    """Payment/refund/screenshot — keep waiting; don't reopen FAQ loop."""
    if has_image:
        return True
    t = (text or "").strip()
    if not t:
        return True
    if _HARD_WAIT.search(t):
        return True
    # Ultra-short follow-ups while ticket is open
    if len(t.split()) <= 2 and t.lower() in {
        "ok", "okay", "haan", "han", "yes", "wait", "ok?", "?",
    }:
        return True
    return False


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
    from support_chat import append_message, clear_escalation, mark_escalated, set_agent_state

    msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
    tid = str(rec.get("thread_id") or "")
    text = str(user_msg.get("text") or "")
    L = detect_reply_lang(text, lang)
    has_image = bool(user_msg.get("image_url"))

    if human_is_handling(msgs):
        set_agent_state(tid, "waiting_for_human")
        return {
            "handled": False,
            "escalate": True,
            "source": "human_live",
            "agent_state": "waiting_for_human",
        }

    # Already escalated: still answer product how-to (e.g. Today's Energy).
    # Only hard-block payment/refund/screenshot / tiny wait pings.
    if rec.get("escalated") and not human_is_handling(msgs):
        if _wants_hard_wait(text, has_image=has_image):
            reply = still_waiting_reply(L)
            bot = append_message(tid, sender="bot", text=reply)
            set_agent_state(tid, "waiting_for_human")
            return {
                "handled": bool(bot.get("ok")),
                "pending": False,
                "escalate": True,
                "reply": reply,
                "source": "still_waiting",
                "agent_state": "waiting_for_human",
                "notify_admin": True,
            }
        # Fall through — run knowledge agent for app how-to

    cid = (cosmo_user_id or str(rec.get("cosmo_user_id") or "")).strip()
    set_agent_state(tid, "processing")
    decision = answer_support(
        text,
        lang=L,
        has_image=has_image,
        history=msgs,
        cosmo_user_id=cid,
        account_card=account_card,
        user=user,
    )
    reply = str(decision.get("reply") or "").strip() or wait_for_support_reply(L)
    bot = append_message(tid, sender="bot", text=reply)
    if not bot.get("ok"):
        set_agent_state(tid, "failed")
        return {
            "handled": False,
            "escalate": True,
            "source": "append_failed",
            "reply": reply,
            "agent_state": "failed",
        }

    escalate = bool(decision.get("escalate"))
    state = "waiting_for_human" if escalate else "answered"
    set_agent_state(tid, state)
    if escalate:
        mark_escalated(tid)
    else:
        clear_escalation(tid)
    return {
        "handled": True,
        "pending": False,
        "escalate": escalate,
        "reply": reply,
        "source": str(decision.get("source") or "llm"),
        "relation": str(decision.get("relation") or ""),
        "agent_state": state,
    }

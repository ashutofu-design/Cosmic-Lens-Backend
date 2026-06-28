"""Rolling Ask user profile — built only from question signals."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from ask_user_signals import extract_question_signals

_MAX_SIGNALS_STORED = 200
_PROFILE_WINDOW_DAYS = 90


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_signals_row(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _derive_labels(profile: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    style = profile.get("avg_style") or ""
    if style in ("very_short", "short"):
        labels.append("short_asker")
    elif style == "long":
        labels.append("detail_seeker")

    emotion = profile.get("dominant_emotion") or "neutral"
    if emotion == "anxious":
        labels.append("anxious_tone")
    elif emotion == "hopeful":
        labels.append("hopeful_tone")

    if float(profile.get("skeptic_rate") or 0) >= 0.25:
        labels.append("needs_evidence")

    if float(profile.get("followup_rate") or 0) >= 0.35:
        labels.append("deep_followup")

    top_topic = profile.get("top_topic")
    if top_topic and top_topic != "general":
        labels.append(f"{top_topic}_focused")

    if int(profile.get("questions_30d") or 0) >= 15:
        labels.append("high_engagement")

    if float(profile.get("night_ratio") or 0) >= 0.45:
        labels.append("night_owl")

    return labels


def merge_signals_into_profile(
    existing: dict[str, Any] | None,
    signals: dict[str, Any],
    *,
    asked_at: datetime | None = None,
) -> dict[str, Any]:
    """Merge one question's signals into rolling profile dict."""
    base = dict(existing or {})
    now = asked_at or _utc_now()
    hour = now.hour
    is_night = hour >= 21 or hour < 6

    n = int(base.get("question_count") or 0) + 1
    base["question_count"] = n
    base["last_asked_at"] = now.isoformat()

    # Running averages
    prev_avg_words = float(base.get("avg_word_count") or 0)
    wc = int(signals.get("word_count") or 0)
    base["avg_word_count"] = round(((prev_avg_words * (n - 1)) + wc) / n, 1)

    styles = list(base.get("recent_styles") or [])
    styles.append(signals.get("style") or "medium")
    base["recent_styles"] = styles[-50:]
    style_counts = Counter(base["recent_styles"])
    base["avg_style"] = style_counts.most_common(1)[0][0]

    base["lang_style"] = signals.get("lang_style") or base.get("lang_style") or "hinglish"
    base["tone"] = signals.get("tone") or base.get("tone") or "neutral"

    emotions = list(base.get("recent_emotions") or [])
    emotions.append(signals.get("emotion") or "neutral")
    base["recent_emotions"] = emotions[-50:]
    emo_counts = Counter(base["recent_emotions"])
    base["dominant_emotion"] = emo_counts.most_common(1)[0][0]

    topics = dict(base.get("topic_counts") or {})
    for t in signals.get("topics_detected") or [signals.get("logged_topic") or "general"]:
        key = str(t or "general").lower()
        topics[key] = int(topics.get(key) or 0) + 1
    base["topic_counts"] = topics
    if topics:
        base["top_topic"] = max(topics.items(), key=lambda kv: kv[1])[0]

    qtypes = list(base.get("recent_question_types") or [])
    for qt in signals.get("question_types") or []:
        qtypes.append(qt)
    base["recent_question_types"] = qtypes[-100:]

    skeptics = int(base.get("skeptic_count") or 0)
    if signals.get("is_skeptic"):
        skeptics += 1
    base["skeptic_count"] = skeptics
    base["skeptic_rate"] = round(skeptics / n, 3)

    followups = int(base.get("followup_count") or 0)
    if signals.get("is_followup"):
        followups += 1
    base["followup_count"] = followups
    base["followup_rate"] = round(followups / n, 3)

    timing_asks = int(base.get("timing_ask_count") or 0)
    if signals.get("is_timing"):
        timing_asks += 1
    base["timing_ask_count"] = timing_asks

    night_asks = int(base.get("night_ask_count") or 0)
    if is_night:
        night_asks += 1
    base["night_ask_count"] = night_asks
    base["night_ratio"] = round(night_asks / n, 3)

    # 30-day window counter (approximate from last_signals if present)
    recent = list(base.get("last_signals") or [])
    recent.append({"at": now.isoformat(), **signals})
    cutoff = now - timedelta(days=_PROFILE_WINDOW_DAYS)
    recent = [r for r in recent if (r.get("at") or "") >= cutoff.isoformat()[:19]]
    base["last_signals"] = recent[-_MAX_SIGNALS_STORED:]
    base["questions_30d"] = len(
        [r for r in recent if (r.get("at") or "") >= (now - timedelta(days=30)).isoformat()[:19]]
    )

    base["labels"] = _derive_labels(base)
    base["version"] = 1
    return base


def build_personalization_hint(profile: dict[str, Any] | None) -> str:
    """Short block for LLM / deterministic tone — never changes chart facts."""
    if not profile or int(profile.get("question_count") or 0) < 2:
        return ""

    labels = profile.get("labels") or []
    lines = ["PERSONALIZATION (from user's past questions only — tone/length only, never change chart facts):"]

    if "short_asker" in labels:
        lines.append("- User prefers SHORT answers (1-2 sentences). No long paragraphs.")
    if "detail_seeker" in labels:
        lines.append("- User asks long/detailed questions — give one extra evidence line if space allows.")
    if "anxious_tone" in labels:
        lines.append("- User often sounds worried — open with the strongest positive chart fact, then timing.")
    if "needs_evidence" in labels:
        lines.append("- User asks 'how do you know' style — mention 1-2 concrete checks briefly.")
    if "deep_followup" in labels:
        lines.append("- User drills with follow-ups — offer backup window / next step proactively.")
    top = profile.get("top_topic")
    if top and top != "general":
        lines.append(f"- Top concern topic: {top} — stay focused unless user shifts.")

    if len(lines) <= 1:
        return ""
    return "\n".join(lines)


def build_follow_ups_from_profile(
    profile: dict[str, Any] | None,
    topic: str,
    lang: str = "hn",
) -> list[str]:
    """Deterministic follow-up chips from profile + topic."""
    hi = (lang or "hn").lower().startswith("hi") or lang == "hn"
    top = (profile or {}).get("top_topic") or topic or "general"
    labels = (profile or {}).get("labels") or []

    if top == "marriage" or topic == "marriage":
        if "deep_followup" in labels or "anxious_tone" in labels:
            return (
                ["Agar ye time miss ho to agla kab?", "Delay kyun dikh raha hai?"]
                if hi
                else ["If this window misses, when next?", "Why does delay show?"]
            )
        return (
            ["Love marriage ya arranged?", "Partner kaisa hoga?"]
            if hi
            else ["Love or arranged marriage?", "What will spouse be like?"]
        )

    if top == "career" or topic == "career":
        return (
            ["Promotion kab?", "Job change sahi rahega?"]
            if hi
            else ["When promotion?", "Is job change right?"]
        )

    return (
        ["Aur detail chahiye?", "Koi aur sawaal?"]
        if hi
        else ["Want more detail?", "Another question?"]
    )


def personalize_ask_result(
    result: dict[str, Any],
    profile: dict[str, Any] | None,
    *,
    lang: str = "hn",
    backup_window: str = "",
) -> dict[str, Any]:
    """Apply light-touch personalization to an Ask result dict (in-place safe copy)."""
    if not isinstance(result, dict) or not profile:
        return result
    out = dict(result)
    labels = profile.get("labels") or []
    topic = str(out.get("topic") or "general")

    # Custom follow-ups when empty
    if not out.get("follow_ups"):
        out["follow_ups"] = build_follow_ups_from_profile(profile, topic, lang)

    text = (out.get("text") or "").strip()
    if text and backup_window and ("short_asker" not in labels) and (
        "detail_seeker" in labels or "deep_followup" in labels or "anxious_tone" in labels
    ):
        extra = f" Backup window: {backup_window}." if backup_window else ""
        if extra and extra not in text:
            out["text"] = text + extra

    hint = build_personalization_hint(profile)
    if hint:
        meta = dict(out.get("user_profile_meta") or {})
        meta["labels"] = labels
        meta["top_topic"] = profile.get("top_topic")
        meta["avg_style"] = profile.get("avg_style")
        out["user_profile_meta"] = meta

    return out


def record_question_signals_for_user(
    *,
    user_id: int,
    question_text: str,
    topic: str = "general",
    answer_source: str | None = None,
    question_id: str | None = None,
) -> None:
    """Persist signals + update rolling profile. Never raises."""
    if not user_id:
        return
    try:
        from database import db
        from models import QuestionUserSignal, UserAskProfile

        signals = extract_question_signals(
            question_text,
            topic=topic,
            answer_source=answer_source,
        )
        now = _utc_now()
        sig_row = QuestionUserSignal(
            user_id=int(user_id),
            question_id=(question_id or "")[:36] or None,
            signals_json=json.dumps(signals, ensure_ascii=False),
            created_at=now,
        )
        db.session.add(sig_row)

        prof = UserAskProfile.query.get(int(user_id))
        existing = _parse_signals_row(prof.profile_json if prof else None)
        merged = merge_signals_into_profile(existing, signals, asked_at=now)
        if prof:
            prof.profile_json = json.dumps(merged, ensure_ascii=False)
            prof.question_count = int(merged.get("question_count") or 0)
            prof.updated_at = now
        else:
            db.session.add(
                UserAskProfile(
                    user_id=int(user_id),
                    profile_json=json.dumps(merged, ensure_ascii=False),
                    question_count=int(merged.get("question_count") or 0),
                    updated_at=now,
                )
            )
        db.session.commit()
    except Exception as exc:
        try:
            from database import db

            db.session.rollback()
        except Exception:
            pass
        print(f"[user_ask_profile] record failed (non-fatal): {exc}", flush=True)


def get_user_ask_profile(user_id: int) -> Optional[dict[str, Any]]:
    """Load merged profile dict for a user."""
    try:
        from models import UserAskProfile

        row = UserAskProfile.query.get(int(user_id))
        if not row:
            return None
        return _parse_signals_row(row.profile_json)
    except Exception:
        return None


def get_recent_signals_for_user(user_id: int, limit: int = 20) -> list[dict[str, Any]]:
    try:
        from models import QuestionUserSignal

        rows = (
            QuestionUserSignal.query.filter_by(user_id=int(user_id))
            .order_by(QuestionUserSignal.created_at.desc())
            .limit(max(1, min(100, limit)))
            .all()
        )
        out = []
        for r in rows:
            sig = _parse_signals_row(r.signals_json)
            out.append(
                {
                    "id": r.id,
                    "question_id": r.question_id,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    **sig,
                }
            )
        return out
    except Exception:
        return []


def admin_profile_view(user_id: int) -> dict[str, Any]:
    """Admin API payload."""
    prof = get_user_ask_profile(user_id) or {}
    return {
        "user_id": user_id,
        "profile": prof,
        "labels": prof.get("labels") or [],
        "recent_signals": get_recent_signals_for_user(user_id, limit=15),
        "personalization_hint": build_personalization_hint(prof),
    }

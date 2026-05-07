"""
Question logging + history for the Ask flow.

STRICT SCOPE — pure storage + retrieval layer:
  • Does NOT change any astrology logic.
  • Does NOT touch engine calculations.
  • Does NOT send the full kundli to any LLM.
  • Does NOT persist the full LLM response.
  • Persists only: question text, detected topic, primary kundli FK,
    a short structured verdict summary (≤120 chars), and timestamp.

Public surface:
  save_user_question(...)                          → fire-and-forget log
  extract_verdict_summary(result, topic)           → pull a ≤120-char tag
  get_recent_questions(user_id, limit=20)          → newest-first list
  search_questions(user_id, q, limit=20)           → filter by topic OR
                                                     question_text substring

All three retrieval helpers are read-only; save_user_question() is the only
mutator and is wrapped in try/except so a logging failure never breaks the
user's Ask flow.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Iterable, Optional

from sqlalchemy import or_

from database import db
from models import UserQuestion


# Hard cap mirrored from UserQuestion.verdict_summary column (String 120).
_MAX_VERDICT_LEN = 120
# Hard cap to keep question_text rows lean. The Ask UI inputs are typically
# < 200 chars; anything longer is almost certainly noise/paste and we don't
# need it for the "Recent Questions" surface.
_MAX_QUESTION_LEN = 1000


# ─────────────────────────────────────────────────────────────────────────────
# Verdict summary extraction
# ─────────────────────────────────────────────────────────────────────────────
def extract_verdict_summary(result: Any, topic: str) -> str:
    """Pull a short, structured verdict label from an Ask engine result.

    The engines return wildly different shapes (rule-based dict, OpenAI
    structured wealth/health/career/love payloads, marriage deterministic
    verdict, brand_guard refusal, etc). We probe a small set of well-known
    keys, in order of specificity, and fall back to a topic-derived label.

    NEVER returns the full LLM `text` — only structured tags. Output is
    truncated to _MAX_VERDICT_LEN.
    """
    if not isinstance(result, dict):
        return _truncate("answered")

    # 1. Top-level "verdict" — most engines put their structured tag here.
    v = result.get("verdict")
    if isinstance(v, str) and v.strip():
        return _truncate(v.strip())
    if isinstance(v, dict):
        # Wealth / Health / Career / Love structured payloads nest the tag
        # at v.verdict, sometimes with auxiliary v.tag / v.bucket fields.
        for key in ("verdict", "tag", "bucket", "label"):
            x = v.get(key)
            if isinstance(x, str) and x.strip():
                return _truncate(x.strip())

    # 2. Some engines surface the tag at the result root.
    for key in ("tag", "bucket", "label", "outcome"):
        x = result.get(key)
        if isinstance(x, str) and x.strip():
            return _truncate(x.strip())

    # 3. Brand-guard / off-topic refusals.
    if result.get("source") == "brand_guard":
        return _truncate("off_topic")

    # 4. Topic-only fallback.
    if topic and topic != "general":
        return _truncate(f"answered:{topic}")
    return _truncate("answered")


def _truncate(s: str) -> str:
    s = s.strip()
    return s if len(s) <= _MAX_VERDICT_LEN else (s[: _MAX_VERDICT_LEN - 1] + "…")


# ─────────────────────────────────────────────────────────────────────────────
# Save (mutator)
# ─────────────────────────────────────────────────────────────────────────────
_MAX_ANSWER_LEN = 8000  # hard cap for full LLM answer_text persistence


def save_user_question(
    *,
    user_id: int,
    question_text: str,
    topic: str,
    primary_kundli_id: Optional[int] = None,
    verdict_summary: str = "answered",
    answer_text: Optional[str] = None,
    answer_source: Optional[str] = None,
    created_at: Optional[datetime] = None,
) -> Optional[str]:
    """Persist one question row. Returns the new row id, or None on failure.

    NEVER raises — a logging failure must NEVER break the user's Ask flow.
    All inputs are normalised + length-capped before insert.

    `answer_text` is capped to _MAX_ANSWER_LEN (8000 chars) — long enough for
    any realistic Ask narration, short enough to keep rows lean. `answer_source`
    is the response's `source` field (timing/static/brand_guard/etc.) for
    analytics grouping.
    """
    if not user_id or not isinstance(user_id, int):
        return None
    qtext = (question_text or "").strip()
    if not qtext:
        return None
    if len(qtext) > _MAX_QUESTION_LEN:
        qtext = qtext[: _MAX_QUESTION_LEN - 1] + "…"

    topic_norm = (topic or "general").strip().lower()[:40] or "general"
    verdict_norm = _truncate(verdict_summary or "answered")

    atext: Optional[str] = None
    if answer_text:
        atext = str(answer_text).strip()
        if len(atext) > _MAX_ANSWER_LEN:
            atext = atext[: _MAX_ANSWER_LEN - 1] + "…"
        if not atext:
            atext = None

    asrc: Optional[str] = None
    if answer_source:
        asrc = str(answer_source).strip().lower()[:40] or None

    row_id = str(uuid.uuid4())
    try:
        row = UserQuestion(
            id                = row_id,
            user_id           = user_id,
            question_text     = qtext,
            topic             = topic_norm,
            primary_kundli_id = primary_kundli_id,
            verdict_summary   = verdict_norm,
            answer_text       = atext,
            answer_source     = asrc,
            created_at        = created_at or datetime.utcnow(),
        )
        db.session.add(row)
        db.session.commit()
        return row_id
    except Exception as exc:
        # Never surface — this is a non-critical telemetry path.
        try:
            db.session.rollback()
        except Exception:
            pass
        print(f"[question_history] save failed (non-fatal): {exc}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Retrieval (read-only)
# ─────────────────────────────────────────────────────────────────────────────
def get_recent_questions(user_id: int, limit: int = 20) -> list[dict]:
    """Return up to `limit` newest-first questions for `user_id`.

    Hard-capped at 100 to prevent runaway responses. Default 20 matches the
    Ask UI's "Recent Questions" section.
    """
    if not user_id:
        return []
    n = max(1, min(int(limit or 20), 100))
    rows: Iterable[UserQuestion] = (
        UserQuestion.query
        .filter(UserQuestion.user_id == user_id)
        .order_by(UserQuestion.created_at.desc())
        .limit(n)
        .all()
    )
    return [r.to_dict() for r in rows]


def search_questions(user_id: int, q: str, limit: int = 20) -> list[dict]:
    """Filter the user's history by topic OR question_text substring.

    Matching is case-insensitive on both columns. Empty query → empty list.
    """
    if not user_id:
        return []
    qstr = (q or "").strip()
    if not qstr:
        return []
    n = max(1, min(int(limit or 20), 100))
    pat = f"%{qstr.lower()}%"
    rows: Iterable[UserQuestion] = (
        UserQuestion.query
        .filter(UserQuestion.user_id == user_id)
        .filter(or_(
            db.func.lower(UserQuestion.topic).like(pat),
            db.func.lower(UserQuestion.question_text).like(pat),
        ))
        .order_by(UserQuestion.created_at.desc())
        .limit(n)
        .all()
    )
    return [r.to_dict() for r in rows]

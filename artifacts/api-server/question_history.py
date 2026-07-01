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
    llm_model: Optional[str] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    cached_tokens: Optional[int] = None,
    cost_usd: Optional[float] = None,
    cost_inr: Optional[float] = None,
    engine_tag: Optional[str] = None,
    llm_context_json: Optional[str] = None,
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

    def _pos_int(v: Any) -> Optional[int]:
        try:
            n = int(v)
            return n if n >= 0 else None
        except (TypeError, ValueError):
            return None

    def _pos_float(v: Any) -> Optional[float]:
        try:
            f = float(v)
            return f if f >= 0 else None
        except (TypeError, ValueError):
            return None

    pt = _pos_int(prompt_tokens)
    ct = _pos_int(completion_tokens)
    tt = _pos_int(total_tokens)
    if tt is None and pt is not None and ct is not None:
        tt = pt + ct
    cached = _pos_int(cached_tokens)
    usd = _pos_float(cost_usd)
    inr = _pos_float(cost_inr)
    model = (str(llm_model).strip()[:80] if llm_model else None) or None
    etag = (str(engine_tag).strip()[:40] if engine_tag else None) or None
    ctx_json: Optional[str] = None
    if llm_context_json:
        ctx_json = str(llm_context_json).strip() or None

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
            llm_model         = model,
            prompt_tokens     = pt,
            completion_tokens = ct,
            total_tokens      = tt,
            cached_tokens     = cached,
            cost_usd          = usd,
            cost_inr          = inr,
            engine_tag        = etag,
            llm_context_json  = ctx_json,
            created_at        = created_at or datetime.utcnow(),
        )
        db.session.add(row)
        db.session.commit()
        return row_id
    except Exception as exc:
        err = str(exc).lower()
        if ctx_json and ("llm_context_json" in err or "no such column" in err):
            try:
                db.session.rollback()
            except Exception:
                pass
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
                    llm_model         = model,
                    prompt_tokens     = pt,
                    completion_tokens = ct,
                    total_tokens      = tt,
                    cached_tokens     = cached,
                    cost_usd          = usd,
                    cost_inr          = inr,
                    engine_tag        = etag,
                    created_at        = created_at or datetime.utcnow(),
                )
                db.session.add(row)
                db.session.commit()
                print("[question_history] saved without llm_context_json (column missing)", flush=True)
                return row_id
            except Exception as exc2:
                exc = exc2
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


def list_admin_ask_questions(
    *,
    page: int = 1,
    per_page: int = 50,
    user_id: Optional[int] = None,
    email: Optional[str] = None,
) -> dict:
    """Paginated Ask Q&A for admin panel — question, answer, tokens, cost."""
    from models import User

    try:
        from database import ensure_user_questions_telemetry_columns

        ensure_user_questions_telemetry_columns()
    except Exception as _col_exc:
        print(f"[question_history] telemetry columns ensure skipped: {_col_exc}", flush=True)

    page = max(1, int(page or 1))
    per_page = max(1, min(int(per_page or 50), 100))
    q = UserQuestion.query.join(User, UserQuestion.user_id == User.id)
    if user_id:
        q = q.filter(UserQuestion.user_id == int(user_id))
    em = (email or "").strip().lower()
    if em:
        q = q.filter(db.func.lower(User.email).like(f"%{em}%"))

    try:
        total = q.count()
    except Exception as exc:
        print(f"[question_history] ask-questions count failed: {exc}", flush=True)
        raise

    pages = max(1, (total + per_page - 1) // per_page)
    if page > pages:
        page = pages

    try:
        rows = (
            q.order_by(UserQuestion.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .with_entities(UserQuestion, User.email, User.name)
            .all()
        )
    except Exception as exc:
        err = str(exc).lower()
        print(f"[question_history] ask-questions query failed: {exc}", flush=True)
        if "no such column" in err or "undefined column" in err:
            try:
                from database import ensure_user_questions_telemetry_columns

                ensure_user_questions_telemetry_columns()
                rows = (
                    q.order_by(UserQuestion.created_at.desc())
                    .offset((page - 1) * per_page)
                    .limit(per_page)
                    .with_entities(UserQuestion, User.email, User.name)
                    .all()
                )
            except Exception as exc2:
                print(f"[question_history] ask-questions retry failed: {exc2}", flush=True)
                raise exc2 from exc
        else:
            raise

    items = []
    for uq, user_email, user_name in rows:
        d = uq.to_dict()
        d["user_id"] = uq.user_id
        d["user_email"] = user_email or ""
        d["user_name"] = user_name or ""
        d["llm_context"] = None
        raw_ctx = uq.llm_context_json
        if raw_ctx:
            try:
                from ask_llm_context_debug import parse_llm_context_from_db

                d["llm_context"] = parse_llm_context_from_db(raw_ctx)
            except Exception:
                try:
                    import json

                    parsed = json.loads(raw_ctx)
                    d["llm_context"] = parsed if isinstance(parsed, dict) else None
                except Exception:
                    d["llm_context"] = {"raw": str(raw_ctx)[:8000]}
        items.append(d)

    return {
        "items": items,
        "page": page,
        "pages": pages,
        "per_page": per_page,
        "total": total,
    }


def extract_admin_llm_context_for_save(result: Any) -> str | None:
    """Pop admin_llm_context from an Ask result and serialize for DB."""
    if not isinstance(result, dict):
        return None
    ctx = result.pop("admin_llm_context", None)
    if not ctx:
        return None
    try:
        from ask_llm_context_debug import serialize_llm_context_for_db

        out = serialize_llm_context_for_db(ctx)
    except Exception as exc:
        try:
            import json

            out = json.dumps(ctx, ensure_ascii=False, default=str)
            if len(out) > 80_000:
                out = out[:79_999] + "…"
            print(f"[question_history] llm_context fallback serialize: {exc}", flush=True)
        except Exception as exc2:
            print(f"[question_history] llm_context serialize failed: {exc2}", flush=True)
            return None
    if out:
        print(f"[question_history] llm_context_json ready chars={len(out)}", flush=True)
    return out


def token_fields_from_result(result: Any) -> dict[str, Any]:
    """Pull token/cost columns from an Ask API result dict."""
    try:
        from ask_token_telemetry import extract_usage_from_result

        u = extract_usage_from_result(result if isinstance(result, dict) else None)
    except Exception:
        u = {}
    return {
        "llm_model": u.get("llm_model"),
        "prompt_tokens": u.get("prompt_tokens"),
        "completion_tokens": u.get("completion_tokens"),
        "total_tokens": u.get("total_tokens"),
        "cached_tokens": u.get("cached_tokens"),
        "cost_usd": u.get("cost_usd"),
        "cost_inr": u.get("cost_inr"),
        "engine_tag": (result or {}).get("engine_tag") if isinstance(result, dict) else None,
    }

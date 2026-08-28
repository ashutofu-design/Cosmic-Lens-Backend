"""Instagram Answers — admin CRUD and exact-match lookup for the mobile app."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from database import db
from models import InstagramAnswer, normalize_instagram_question


DUPLICATE_ERROR = "duplicate_video_question"
DUPLICATE_MESSAGE = "An answer for this video number and question already exists."


def _parse_video_number(raw: Any) -> Optional[int]:
    if raw is None or raw == "":
        return None
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return None
    return n


def _parse_status(raw: Any, default: str = "active") -> str:
    s = (str(raw or "").strip().lower() or default)
    if s not in ("active", "inactive"):
        return default
    return s


def find_active_match(video_number: int, question: str) -> Optional[InstagramAnswer]:
    norm = normalize_instagram_question(question)
    if not norm:
        return None
    return InstagramAnswer.query.filter_by(
        video_number=video_number,
        question_normalized=norm,
        status="active",
    ).first()


def match_for_user(video_number: int, question: str) -> dict:
    row = find_active_match(video_number, question)
    if not row:
        return {
            "matched": False,
            "message": "No answer available for this question.",
        }
    return {
        "matched": True,
        "answerId": row.id,
        "videoNumber": row.video_number,
        "question": row.question,
        "answer": row.answer,
    }


def list_instagram_answers(
    page: int = 1,
    per_page: int = 50,
    video_number: Optional[int] = None,
    question_search: Optional[str] = None,
    status: Optional[str] = None,
) -> dict:
    page = max(1, int(page or 1))
    per_page = min(100, max(1, int(per_page or 50)))

    q = InstagramAnswer.query

    if video_number is not None:
        q = q.filter(InstagramAnswer.video_number == video_number)

    if question_search:
        term = question_search.strip()
        if term:
            q = q.filter(
                or_(
                    InstagramAnswer.question.ilike(f"%{term}%"),
                    InstagramAnswer.question_normalized.ilike(f"%{term.casefold()}%"),
                )
            )

    if status in ("active", "inactive"):
        q = q.filter(InstagramAnswer.status == status)

    q = q.order_by(InstagramAnswer.id.desc())
    total = q.count()
    pages = max(1, (total + per_page - 1) // per_page)
    if page > pages:
        page = pages

    rows = q.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": [r.to_dict(include_answer=False) for r in rows],
        "total": total,
        "page": page,
        "pages": pages,
        "per_page": per_page,
    }


def get_instagram_answer(answer_id: int) -> Optional[InstagramAnswer]:
    return InstagramAnswer.query.get(int(answer_id))


def create_instagram_answer(
    video_number: int,
    question: str,
    answer: str,
    status: str = "active",
) -> dict:
    q_raw = (question or "").strip()
    a_raw = (answer or "").strip()
    if not q_raw:
        return {"ok": False, "error": "question_required", "message": "Exact question is required."}
    if not a_raw:
        return {"ok": False, "error": "answer_required", "message": "Answer is required."}

    norm = normalize_instagram_question(q_raw)
    existing = InstagramAnswer.query.filter_by(
        video_number=video_number,
        question_normalized=norm,
    ).first()
    if existing:
        return {
            "ok": False,
            "error": DUPLICATE_MESSAGE,
            "code": DUPLICATE_ERROR,
            "message": DUPLICATE_MESSAGE,
        }

    row = InstagramAnswer(
        video_number=video_number,
        question=q_raw,
        question_normalized=norm,
        answer=a_raw,
        status=_parse_status(status),
    )
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            "ok": False,
            "error": DUPLICATE_MESSAGE,
            "code": DUPLICATE_ERROR,
            "message": DUPLICATE_MESSAGE,
        }

    return {"ok": True, "item": row.to_dict(include_answer=True)}


def update_instagram_answer(
    answer_id: int,
    video_number: Optional[int] = None,
    question: Optional[str] = None,
    answer: Optional[str] = None,
    status: Optional[str] = None,
) -> dict:
    row = get_instagram_answer(answer_id)
    if not row:
        return {"ok": False, "error": "not_found", "message": "Answer not found."}

    new_video = video_number if video_number is not None else row.video_number
    new_question = (question or row.question).strip()
    new_answer = (answer or row.answer).strip()
    new_status = _parse_status(status, default=row.status)

    if not new_question:
        return {"ok": False, "error": "question_required", "message": "Exact question is required."}
    if not new_answer:
        return {"ok": False, "error": "answer_required", "message": "Answer is required."}

    norm = normalize_instagram_question(new_question)
    clash = InstagramAnswer.query.filter(
        InstagramAnswer.video_number == new_video,
        InstagramAnswer.question_normalized == norm,
        InstagramAnswer.id != row.id,
    ).first()
    if clash:
        return {
            "ok": False,
            "error": DUPLICATE_MESSAGE,
            "code": DUPLICATE_ERROR,
            "message": DUPLICATE_MESSAGE,
        }

    row.video_number = new_video
    row.question = new_question
    row.question_normalized = norm
    row.answer = new_answer
    row.status = new_status
    row.updated_at = datetime.utcnow()

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            "ok": False,
            "error": DUPLICATE_MESSAGE,
            "code": DUPLICATE_ERROR,
            "message": DUPLICATE_MESSAGE,
        }

    return {"ok": True, "item": row.to_dict(include_answer=True)}


def delete_instagram_answer(answer_id: int) -> dict:
    row = get_instagram_answer(answer_id)
    if not row:
        return {"ok": False, "error": "not_found", "message": "Answer not found."}
    db.session.delete(row)
    db.session.commit()
    return {"ok": True, "id": answer_id}


def set_instagram_answer_status(answer_id: int, status: str) -> dict:
    row = get_instagram_answer(answer_id)
    if not row:
        return {"ok": False, "error": "not_found", "message": "Answer not found."}
    row.status = _parse_status(status)
    row.updated_at = datetime.utcnow()
    db.session.commit()
    return {"ok": True, "item": row.to_dict(include_answer=True)}


def validate_create_payload(data: dict) -> tuple[Optional[dict], Optional[int], str, str, str]:
    video_number = _parse_video_number(data.get("video_number") or data.get("videoNumber"))
    if video_number is None:
        return (
            {"ok": False, "error": "video_number_invalid", "message": "Video number must be a positive integer."},
            None,
            "",
            "",
            "active",
        )
    question = (data.get("question") or "").strip()
    answer = (data.get("answer") or "").strip()
    status = _parse_status(data.get("status"))
    return None, video_number, question, answer, status

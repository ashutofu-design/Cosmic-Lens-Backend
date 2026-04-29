"""
Unit tests for question_history.py — the storage + retrieval layer for the
Ask flow's question logging feature.

Scope:
  • extract_verdict_summary covers all known result shapes
  • save_user_question is fire-and-forget (never raises)
  • get_recent_questions / search_questions return the right rows in
    newest-first order with proper limit clamping
  • Truncation rules for question_text and verdict_summary
"""

from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from flask import Flask

from database import db, init_db
from models import User, Kundli, UserQuestion
from question_history import (
    save_user_question,
    extract_verdict_summary,
    get_recent_questions,
    search_questions,
)


@pytest.fixture
def app():
    app = Flask("test_qh")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
        u = User(id=1, name="Tester", phone="+910000000001",
                 country_code="91", api_key="k1")
        k = Kundli(id=1, user_id=1, name="Tester", dob="01/01/1990",
                   tob="12:00 PM", pob="Somewhere", lat=0.0, lon=0.0, tz=5.5,
                   chart_data="{}")
        db.session.add_all([u, k])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


# ── extract_verdict_summary ───────────────────────────────────────────────
class TestExtractVerdictSummary:
    def test_string_verdict(self):
        assert extract_verdict_summary({"verdict": "yellow_wait"}, "general") == "yellow_wait"

    def test_dict_verdict_with_verdict_key(self):
        r = {"verdict": {"verdict": "manglik", "tag": "MANGLIK"}}
        assert extract_verdict_summary(r, "marriage") == "manglik"

    def test_dict_verdict_with_tag_fallback(self):
        r = {"verdict": {"tag": "love_likely"}}
        assert extract_verdict_summary(r, "marriage") == "love_likely"

    def test_root_level_tag(self):
        assert extract_verdict_summary({"tag": "stable"}, "health") == "stable"

    def test_root_level_bucket(self):
        assert extract_verdict_summary({"bucket": "general_wealth"}, "wealth") == "general_wealth"

    def test_brand_guard_offtopic(self):
        assert extract_verdict_summary({"source": "brand_guard"}, "general") == "off_topic"

    def test_topic_fallback(self):
        # No verdict, no tag, but topic given
        assert extract_verdict_summary({"text": "..."}, "career") == "answered:career"

    def test_no_topic_no_verdict(self):
        assert extract_verdict_summary({"text": "..."}, "general") == "answered"

    def test_non_dict_input(self):
        assert extract_verdict_summary("just a string", "general") == "answered"

    def test_truncation(self):
        long = "a" * 200
        out = extract_verdict_summary({"verdict": long}, "general")
        assert len(out) <= 120
        assert out.endswith("…")

    def test_empty_string_skipped(self):
        # Empty verdict should fall through to next rule (topic-derived).
        assert extract_verdict_summary({"verdict": "  "}, "love") == "answered:love"


# ── save_user_question ────────────────────────────────────────────────────
class TestSaveUserQuestion:
    def test_basic_save(self, app):
        with app.app_context():
            row_id = save_user_question(
                user_id=1, question_text="Health kaisi hai?",
                topic="health", primary_kundli_id=1,
                verdict_summary="unstable",
            )
            assert row_id is not None
            row = UserQuestion.query.get(row_id)
            assert row is not None
            assert row.user_id == 1
            assert row.topic == "health"
            assert row.verdict_summary == "unstable"
            assert row.primary_kundli_id == 1

    def test_returns_none_for_invalid_user(self, app):
        with app.app_context():
            assert save_user_question(user_id=0, question_text="x", topic="x") is None
            assert save_user_question(user_id=None, question_text="x", topic="x") is None  # type: ignore

    def test_returns_none_for_empty_question(self, app):
        with app.app_context():
            assert save_user_question(user_id=1, question_text="   ", topic="x") is None

    def test_topic_normalised(self, app):
        with app.app_context():
            row_id = save_user_question(user_id=1, question_text="q", topic="  HEALTH  ")
            row = UserQuestion.query.get(row_id)
            assert row.topic == "health"

    def test_question_text_truncation(self, app):
        with app.app_context():
            long = "x" * 2000
            row_id = save_user_question(user_id=1, question_text=long, topic="general")
            row = UserQuestion.query.get(row_id)
            assert len(row.question_text) <= 1000
            assert row.question_text.endswith("…")

    def test_never_raises_on_db_error(self, app, monkeypatch):
        # Force commit() to blow up — save_user_question must swallow it.
        with app.app_context():
            def boom(*a, **kw):
                raise RuntimeError("simulated commit failure")
            monkeypatch.setattr(db.session, "commit", boom)
            res = save_user_question(
                user_id=1, question_text="q", topic="general",
            )
            assert res is None  # gracefully None, no exception


# ── get_recent_questions ──────────────────────────────────────────────────
class TestGetRecentQuestions:
    def _seed(self, app, n=5):
        with app.app_context():
            base = datetime.utcnow()
            for i in range(n):
                save_user_question(
                    user_id=1,
                    question_text=f"Q{i}",
                    topic=("health" if i % 2 == 0 else "career"),
                    verdict_summary=f"v{i}",
                    created_at=base - timedelta(minutes=n - i),
                )

    def test_newest_first(self, app):
        self._seed(app, 3)
        with app.app_context():
            items = get_recent_questions(1, limit=10)
            assert len(items) == 3
            # Newest = Q2 (added last with the largest minute offset)
            assert items[0]["question_text"] == "Q2"
            assert items[-1]["question_text"] == "Q0"

    def test_limit_clamping(self, app):
        self._seed(app, 5)
        with app.app_context():
            assert len(get_recent_questions(1, limit=2)) == 2
            # Falsy → use the default of 20 (we have 5 rows total)
            assert len(get_recent_questions(1, limit=0)) == 5
            # Negative → clamps to >=1
            assert len(get_recent_questions(1, limit=-7)) == 1
            # Huge values are capped at 100 — but we only seeded 5 rows
            assert len(get_recent_questions(1, limit=999)) == 5

    def test_empty_for_unknown_user(self, app):
        with app.app_context():
            assert get_recent_questions(99999) == []

    def test_zero_user_id(self, app):
        with app.app_context():
            assert get_recent_questions(0) == []


# ── search_questions ──────────────────────────────────────────────────────
class TestSearchQuestions:
    def _seed(self, app):
        with app.app_context():
            save_user_question(user_id=1, question_text="Health kaisi hai",     topic="health",  verdict_summary="v1")
            save_user_question(user_id=1, question_text="Career mein safalta",  topic="career",  verdict_summary="v2")
            save_user_question(user_id=1, question_text="Vivah kab hoga",       topic="marriage",verdict_summary="v3")

    def test_topic_match(self, app):
        self._seed(app)
        with app.app_context():
            items = search_questions(1, "health")
            assert len(items) == 1
            assert items[0]["topic"] == "health"

    def test_question_text_match(self, app):
        self._seed(app)
        with app.app_context():
            items = search_questions(1, "Vivah")
            assert len(items) == 1
            assert "Vivah" in items[0]["question_text"]

    def test_case_insensitive(self, app):
        self._seed(app)
        with app.app_context():
            assert len(search_questions(1, "CAREER")) == 1
            assert len(search_questions(1, "career")) == 1

    def test_empty_query_returns_empty(self, app):
        self._seed(app)
        with app.app_context():
            assert search_questions(1, "") == []
            assert search_questions(1, "   ") == []

    def test_no_match(self, app):
        self._seed(app)
        with app.app_context():
            assert search_questions(1, "xyz_no_match_abc") == []

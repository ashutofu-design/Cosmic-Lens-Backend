"""Unit tests for Instagram Answers exact-match and duplicate protection."""

from __future__ import annotations

import os
import tempfile
import unittest


class InstagramAnswersTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp(prefix="ig_answers_")
        os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(self._tmpdir, 'test.db')}"

        from flask import Flask

        from database import init_db
        from models import InstagramAnswer

        self.app = Flask(__name__)
        init_db(self.app)
        self.app_context = self.app.app_context()
        self.app_context.push()

        from database import db

        db.session.query(InstagramAnswer).delete()
        db.session.commit()

        from instagram_answers import (
            create_instagram_answer,
            find_active_match,
            match_for_user,
        )

        self.create = create_instagram_answer
        self.find_active_match = find_active_match
        self.match_for_user = match_for_user
        self.db = db
        self.InstagramAnswer = InstagramAnswer

    def tearDown(self) -> None:
        self.app_context.pop()
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

    def _seed_a(self) -> None:
        r = self.create(121, "Sun in 11th house", "Answer A", status="active")
        self.assertTrue(r["ok"])

    def test_case_insensitive_match(self) -> None:
        self._seed_a()
        row = self.find_active_match(121, "sun in 11th house")
        self.assertIsNotNone(row)
        self.assertEqual(row.answer, "Answer A")

    def test_no_match_typo(self) -> None:
        self._seed_a()
        self.assertIsNone(self.find_active_match(121, "su in 11th house"))

    def test_no_match_extra_words(self) -> None:
        self._seed_a()
        self.assertIsNone(self.find_active_match(121, "Sun in 11th house kya hota hai?"))

    def test_same_question_different_video(self) -> None:
        self.create(121, "Sun in 11th house", "Answer A", status="active")
        self.create(245, "Sun in 11th house", "Answer B", status="active")
        a = self.find_active_match(121, "Sun in 11th house")
        b = self.find_active_match(245, "Sun in 11th house")
        self.assertEqual(a.answer, "Answer A")
        self.assertEqual(b.answer, "Answer B")

    def test_duplicate_rejected(self) -> None:
        self.assertTrue(self.create(121, "Sun in 11th house", "Answer A")["ok"])
        dup = self.create(121, "Sun in 11th house", "Another")
        self.assertFalse(dup["ok"])
        self.assertEqual(dup["code"], "duplicate_video_question")

    def test_match_api_payload(self) -> None:
        self._seed_a()
        out = self.match_for_user(121, "sun in 11th house")
        self.assertTrue(out["matched"])
        self.assertEqual(out["answer"], "Answer A")
        self.assertEqual(out["videoNumber"], 121)

    def test_no_match_payload(self) -> None:
        out = self.match_for_user(121, "Sun in 11th house")
        self.assertFalse(out["matched"])
        self.assertIn("message", out)


if __name__ == "__main__":
    unittest.main()

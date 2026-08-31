"""Tests for one-time signup free Ask gift (anti delete+re-register replay)."""
import os
import unittest

from database import db
from flask import Flask


class SignupFreeGiftTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env = dict(os.environ)
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        self.app = Flask(__name__)
        from database import init_db

        init_db(self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self) -> None:
        self.ctx.pop()
        os.environ.clear()
        os.environ.update(self._env)

    def test_first_phone_gets_three_free_then_replay_blocked(self) -> None:
        from models import User
        from signup_free_gift import (
            initial_free_questions_used,
            record_signup_gift_claims,
            signup_gift_already_claimed,
        )
        from subscription_helper import QUESTION_LIMITS

        phone = "+919876543210"
        self.assertEqual(initial_free_questions_used(phone=phone), 0)
        self.assertFalse(signup_gift_already_claimed(phone=phone))

        user = User(
            name="Test",
            phone=phone,
            api_key="k" * 64,
            ask_v1_free_questions_used=initial_free_questions_used(phone=phone),
        )
        db.session.add(user)
        db.session.flush()
        record_signup_gift_claims(phone=phone, user_id=user.id, source="signup")
        db.session.commit()

        self.assertTrue(signup_gift_already_claimed(phone=phone))
        self.assertEqual(
            initial_free_questions_used(phone=phone),
            int(QUESTION_LIMITS["free"]),
        )

    def test_phone_space_and_format_variants_blocked(self) -> None:
        from signup_free_gift import (
            canonical_phone_e164,
            initial_free_questions_used,
            record_signup_gift_claims,
            signup_gift_already_claimed,
        )
        from subscription_helper import QUESTION_LIMITS

        base = "+919876543210"
        record_signup_gift_claims(phone=base, source="signup")
        self.assertEqual(canonical_phone_e164("+91 98765 43210"), base)
        self.assertEqual(canonical_phone_e164("919876543210"), base)
        self.assertEqual(canonical_phone_e164("9876543210"), base)
        self.assertTrue(signup_gift_already_claimed(phone="+91 98765 43210"))
        self.assertEqual(
            initial_free_questions_used(phone="9876543210"),
            int(QUESTION_LIMITS["free"]),
        )

    def test_gmail_plus_and_dots_blocked(self) -> None:
        from signup_free_gift import (
            canonical_email,
            initial_free_questions_used,
            record_signup_gift_claims,
            signup_gift_already_claimed,
        )
        from subscription_helper import QUESTION_LIMITS

        record_signup_gift_claims(email="user@gmail.com", source="signup")
        self.assertEqual(canonical_email("u.s.e.r+spam@gmail.com"), "user@gmail.com")
        self.assertTrue(signup_gift_already_claimed(email="u.s.e.r@gmail.com"))
        self.assertEqual(
            initial_free_questions_used(email="user+2@gmail.com"),
            int(QUESTION_LIMITS["free"]),
        )

    def test_firebase_uid_replay_blocked(self) -> None:
        from signup_free_gift import (
            initial_free_questions_used,
            record_signup_gift_claims,
            signup_gift_already_claimed,
        )
        from subscription_helper import QUESTION_LIMITS

        uid = "firebase_uid_abc123"
        record_signup_gift_claims(firebase_uid=uid, source="signup")
        self.assertTrue(signup_gift_already_claimed(firebase_uid=uid))
        self.assertEqual(
            initial_free_questions_used(firebase_uid=uid),
            int(QUESTION_LIMITS["free"]),
        )

    def test_account_delete_locks_phone_for_future_signup(self) -> None:
        from models import User
        from signup_free_gift import (
            ensure_claims_on_account_delete,
            initial_free_questions_used,
        )
        from subscription_helper import QUESTION_LIMITS

        phone = "+919111222333"
        user = User(
            name="Delete Me",
            phone=phone,
            api_key="x" * 64,
            ask_v1_free_questions_used=0,
        )
        db.session.add(user)
        db.session.commit()

        ensure_claims_on_account_delete(user)
        db.session.delete(user)
        db.session.commit()

        self.assertEqual(
            initial_free_questions_used(phone=phone),
            int(QUESTION_LIMITS["free"]),
        )


if __name__ == "__main__":
    unittest.main()

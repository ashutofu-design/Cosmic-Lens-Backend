"""Unit tests for Cosmic Intelligence V1 question packs."""
from datetime import datetime, timedelta

import ask_v1_billing as billing


def test_catalog_locked_margins():
    packs = {p["id"]: p for p in billing.list_packs()}
    assert packs["starter"] == {
        "id": "starter",
        "price_inr": 49,
        "questions": 8,
        "days": 7,
        "label": "Starter",
        "feel": "Try Cosmic Intelligence",
        "badge": None,
    }
    assert packs["popular"]["questions"] == 15
    assert packs["popular"]["days"] == 14
    assert packs["popular"]["price_inr"] == 99
    assert packs["power"]["questions"] == 45
    assert packs["power"]["days"] == 30
    assert packs["power"]["price_inr"] == 299


class _FakeUser:
    def __init__(self):
        self.id = 1
        self.cosmo_user_id = ""
        self.ask_v1_questions_left = 0
        self.ask_v1_expires_at = None
        self.ask_v1_pack_id = None


def test_apply_pack_fresh_and_stack():
    user = _FakeUser()
    starter = billing.get_pack("starter")
    billing.apply_pack_to_user(user, starter)
    assert user.ask_v1_questions_left == 8
    assert user.ask_v1_pack_id == "starter"
    assert user.ask_v1_expires_at > datetime.utcnow()

    first_exp = user.ask_v1_expires_at
    popular = billing.get_pack("popular")
    billing.apply_pack_to_user(user, popular)
    assert user.ask_v1_questions_left == 8 + 15
    assert user.ask_v1_expires_at >= first_exp
    assert user.ask_v1_pack_id == "popular"


def test_apply_pack_resets_when_expired():
    user = _FakeUser()
    user.ask_v1_questions_left = 3
    user.ask_v1_expires_at = datetime.utcnow() - timedelta(days=1)
    user.ask_v1_pack_id = "starter"
    power = billing.get_pack("power")
    billing.apply_pack_to_user(user, power)
    assert user.ask_v1_questions_left == 45
    assert user.ask_v1_pack_id == "power"
    assert user.ask_v1_expires_at > datetime.utcnow()


def test_cosmo109_unlimited_wallet_and_quota():
    user = _FakeUser()
    user.id = 9
    user.cosmo_user_id = "COSMO109"

    snap = billing.wallet_snapshot(user)
    assert snap["unlimited"] is True
    assert snap["active"] is True
    assert snap["questions_left"] == -1

    quota = billing.unlimited_quota()
    assert quota["allowed"] is True
    assert quota["limit"] == -1
    assert quota["via"] == "ask_v1_unlimited"

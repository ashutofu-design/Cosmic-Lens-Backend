"""V3 FIFO queue + awaiting_user handoff state machine."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def v3(monkeypatch, tmp_path):
    """Isolate session files under a temp dir."""
    import cosmic_intelligence_v3_sessions as mod

    base = tmp_path / "sessions"
    uploads = tmp_path / "uploads"
    settings = tmp_path / "settings.json"
    base.mkdir()
    uploads.mkdir()
    monkeypatch.setattr(mod, "_BASE", str(base))
    monkeypatch.setattr(mod, "_UPLOADS", str(uploads))
    monkeypatch.setattr(mod, "_SETTINGS_PATH", str(settings))
    # Never fire real Telegram/push during tests.
    monkeypatch.setattr(mod, "alert_admin_for_queue_head_if_idle", lambda: {"ok": True, "alerted": False})
    monkeypatch.setattr(mod, "notify_user_v3_ready", lambda rec: {"sent": 0})
    return mod


def _mk(mod, user_id: int, pack_id: str = "15"):
    return mod.create_v3_session_request(
        user_id=user_id,
        pack_id=pack_id,
        user_name=f"User{user_id}",
        user_email=f"u{user_id}@test.com",
    )


def test_offline_enqueue_creates_queued(v3):
    v3.set_v3_chat_enabled(False)
    rec = _mk(v3, 101)
    assert rec["status"] == "queued"
    assert rec.get("queued_at")
    assert rec.get("started_at") is None
    assert rec.get("expires_at") is None


def test_fifo_ordering_and_queue_position(v3):
    a = _mk(v3, 1)
    time.sleep(0.02)
    b = _mk(v3, 2)
    time.sleep(0.02)
    c = _mk(v3, 3)
    head = v3.get_queue_head()
    assert head["session_id"] == a["session_id"]
    assert v3.queue_position_for(a["session_id"]) == 1
    assert v3.queue_position_for(b["session_id"]) == 2
    assert v3.queue_position_for(c["session_id"]) == 3


def test_one_live_enforcement(v3):
    a = _mk(v3, 11)
    b = _mk(v3, 12)
    ready = v3.admin_ready_v3_session(a["session_id"])
    assert ready["ok"] is True
    assert ready["session"]["status"] == "awaiting_user"
    assert ready["session"].get("expires_at") is None

    blocked = v3.admin_ready_v3_session(b["session_id"])
    assert blocked["ok"] is False
    assert blocked["error"] == "engine_busy"


def test_not_queue_head_cannot_accept(v3):
    a = _mk(v3, 21)
    b = _mk(v3, 22)
    bad = v3.admin_ready_v3_session(b["session_id"])
    assert bad["ok"] is False
    assert bad["error"] == "not_queue_head"
    ok = v3.admin_ready_v3_session(a["session_id"])
    assert ok["ok"] is True


def test_admin_ready_does_not_start_timer(v3):
    a = _mk(v3, 31)
    ready = v3.admin_ready_v3_session(a["session_id"])
    sess = ready["session"]
    assert sess["status"] == "awaiting_user"
    assert sess.get("started_at") is None
    assert sess.get("expires_at") is None
    assert sess.get("awaiting_user_expires_at")


def test_user_accept_starts_timer(v3):
    a = _mk(v3, 41)
    v3.admin_ready_v3_session(a["session_id"])
    live = v3.user_accept_v3_session(a["session_id"], user_id=41)
    assert live["ok"] is True
    sess = live["session"]
    assert sess["status"] == "accepted"
    assert sess.get("started_at")
    assert sess.get("expires_at")
    rem = v3._remaining_seconds(sess)
    assert rem is not None and rem > 0


def test_user_accept_idempotent_when_live(v3):
    a = _mk(v3, 42)
    v3.admin_ready_v3_session(a["session_id"])
    first = v3.user_accept_v3_session(a["session_id"], user_id=42)
    second = v3.user_accept_v3_session(a["session_id"], user_id=42)
    assert second["ok"] is True
    assert second.get("already_live") is True
    assert second["session"]["started_at"] == first["session"]["started_at"]


def test_awaiting_timeout_requeues_to_end(v3):
    a = _mk(v3, 51)
    b = _mk(v3, 52)
    v3.admin_ready_v3_session(a["session_id"])
    # Force expire awaiting window.
    rec = v3._load(a["session_id"])
    past = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
    rec["awaiting_user_expires_at"] = past
    v3._save(rec)

    expired = v3.get_v3_session(a["session_id"])
    assert expired["status"] == "queued"
    assert int(expired.get("requeue_count") or 0) >= 1

    # Head should now be b (a went to end).
    head = v3.get_queue_head()
    assert head["session_id"] == b["session_id"]
    assert v3.queue_position_for(a["session_id"]) == 2


def test_next_head_after_end(v3):
    a = _mk(v3, 61)
    b = _mk(v3, 62)
    v3.admin_ready_v3_session(a["session_id"])
    live = v3.user_accept_v3_session(a["session_id"], user_id=61)
    assert live["ok"]
    v3.end_v3_session(a["session_id"], reason="test_end")
    assert not v3.has_active_or_awaiting_v3_session()
    head = v3.get_queue_head()
    assert head and head["session_id"] == b["session_id"]
    ready_b = v3.admin_ready_v3_session(b["session_id"])
    assert ready_b["ok"] is True


def test_unlimited_waitlist_while_one_live(v3):
    """Any number of users may join the FIFO queue while one consultation is live."""
    assert v3.QUEUE_MAX_SIZE is None
    live_req = _mk(v3, 200)
    ready = v3.admin_ready_v3_session(live_req["session_id"])
    assert ready["ok"]
    accepted = v3.user_accept_v3_session(live_req["session_id"], user_id=200)
    assert accepted["ok"]
    assert v3.has_active_or_awaiting_v3_session()

    waiters = []
    for uid in range(201, 221):  # 20 more users
        rec = _mk(v3, uid)
        assert rec["status"] == "queued"
        assert not rec.get("_reused")
        waiters.append(rec)

    assert v3.queue_position_for(waiters[0]["session_id"]) == 1
    assert v3.queue_position_for(waiters[-1]["session_id"]) == 20
    # Live user is not in the waiting queue.
    assert v3.queue_position_for(live_req["session_id"]) is None
    # Cannot promote a waiter while live session is open.
    blocked = v3.admin_ready_v3_session(waiters[0]["session_id"])
    assert blocked["ok"] is False
    assert blocked["error"] == "engine_busy"


def test_user_can_leave_waitlist(v3):
    a = _mk(v3, 65)
    b = _mk(v3, 66)
    result = v3.cancel_v3_waitlist(a["session_id"], user_id=65)
    assert result["ok"] is True
    assert result["cancelled"] is True
    assert v3.get_v3_session(a["session_id"])["status"] == "rejected"
    assert v3.find_active_v3_session_for_user(65) is None
    assert v3.get_queue_head()["session_id"] == b["session_id"]


def test_user_cannot_cancel_another_users_waitlist(v3):
    a = _mk(v3, 67)
    result = v3.cancel_v3_waitlist(a["session_id"], user_id=999)
    assert result["ok"] is False
    assert result["error"] == "forbidden"
    assert v3.get_v3_session(a["session_id"])["status"] == "queued"


def test_legacy_pending_treated_as_queued(v3):
    a = _mk(v3, 71)
    path = os.path.join(v3._BASE, f"{a['session_id']}.json")
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    raw["status"] = "pending"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(raw, fh)
    got = v3.get_v3_session(a["session_id"])
    assert v3._normalize_status(got.get("status")) == "queued"
    assert v3.queue_position_for(a["session_id"]) == 1


def test_v3_balance_unused_until_talk(v3):
    live = _mk(v3, 81, "15")
    v3.admin_ready_v3_session(live["session_id"])
    v3.user_accept_v3_session(live["session_id"], user_id=81)
    queued = _mk(v3, 81, "30")

    bal = v3.v3_balance_for_user(81)
    assert bal["balance_inr"] == 699
    assert bal["used_inr"] == 399
    assert bal["bought_inr"] == 1098
    assert bal["unused_sessions"] == 1
    assert bal["used_sessions"] == 1

    rows = v3.list_v3_transactions_for_user(81)
    statuses = {r["id"]: r["status"] for r in rows}
    assert statuses[f"v3-{queued['session_id']}"] == "bought"
    assert statuses[f"v3-{live['session_id']}"] == "live"

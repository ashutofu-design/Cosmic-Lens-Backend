"""Unit tests for persistent Help & Support chat store."""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest


class SupportChatTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp(prefix="support_chat_")
        import support_chat as sc

        self.sc = sc
        self._orig_base = sc._BASE
        self._orig_uploads = sc._UPLOADS
        sc._BASE = os.path.join(self._tmpdir, "threads")
        sc._UPLOADS = os.path.join(self._tmpdir, "uploads")

    def tearDown(self) -> None:
        self.sc._BASE = self._orig_base
        self.sc._UPLOADS = self._orig_uploads
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_get_or_create_reuses_open_thread(self) -> None:
        a = self.sc.get_or_create_thread(user_id=1, user_name="A")
        b = self.sc.get_or_create_thread(user_id=1, user_name="A")
        self.assertEqual(a["thread_id"], b["thread_id"])

    def test_user_message_ai_stays_off_admin(self) -> None:
        t = self.sc.get_or_create_thread(user_id=2, user_name="B")
        r = self.sc.append_message(
            t["thread_id"], sender="user", text="Need help", user_id=2
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["thread"]["status"], "open")
        self.assertEqual(r["thread"]["unread_admin"], 0)
        listed = self.sc.list_threads()
        ids = [x["thread_id"] for x in listed["threads"]]
        self.assertNotIn(t["thread_id"], ids)

    def test_forbidden_other_user(self) -> None:
        t = self.sc.get_or_create_thread(user_id=3)
        r = self.sc.append_message(
            t["thread_id"], sender="user", text="hi", user_id=99
        )
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"], "forbidden")

    def test_admin_reply_and_image_reject(self) -> None:
        t = self.sc.get_or_create_thread(user_id=4)
        r = self.sc.append_message(
            t["thread_id"], sender="admin", text="We are here"
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["thread"]["status"], "waiting_user")
        bad = self.sc.save_support_image_data_url("not-an-image")
        self.assertIsNone(bad)
        ok = self.sc.save_support_image_data_url(
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        self.assertTrue(ok and ok.startswith("/api/support/media/"))

    def test_close_purges_chat_and_uploads(self) -> None:
        t = self.sc.get_or_create_thread(user_id=5)
        tid = t["thread_id"]
        img = self.sc.save_support_image_data_url(
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        self.assertTrue(img)
        self.sc.append_message(
            tid, sender="user", text="need help", image_url=img, user_id=5
        )
        name = os.path.basename(str(img))
        self.assertTrue(os.path.isfile(os.path.join(self.sc._UPLOADS, name)))
        r = self.sc.close_thread(tid)
        self.assertTrue(r["ok"])
        self.assertTrue(r["deleted"])
        self.assertIsNone(self.sc.get_thread(tid))
        self.assertFalse(os.path.isfile(os.path.join(self.sc._BASE, f"{tid}.json")))
        self.assertFalse(os.path.isfile(os.path.join(self.sc._UPLOADS, name)))
        gone = self.sc.append_message(
            tid, sender="user", text="still need help", user_id=5
        )
        self.assertFalse(gone["ok"])
        self.assertEqual(gone["error"], "not_found")
        nxt = self.sc.get_or_create_thread(user_id=5)
        self.assertNotEqual(nxt["thread_id"], tid)
        msgs = nxt.get("messages") if isinstance(nxt.get("messages"), list) else []
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].get("sender"), "system")

    def test_bot_reply_clears_admin_unread(self) -> None:
        t = self.sc.get_or_create_thread(user_id=6)
        self.sc.append_message(t["thread_id"], sender="user", text="hi", user_id=6)
        r = self.sc.append_message(t["thread_id"], sender="bot", text="Short answer")
        self.assertTrue(r["ok"])
        self.assertEqual(r["thread"]["status"], "waiting_user")
        self.assertEqual(r["thread"]["unread_admin"], 0)

    def test_idle_autoclose_deletes_stale_ticket(self) -> None:
        t = self.sc.get_or_create_thread(user_id=9)
        tid = t["thread_id"]
        rec = self.sc.get_thread(tid)
        rec["updated_at"] = "2020-01-01T00:00:00Z"
        rec["created_at"] = "2020-01-01T00:00:00Z"
        for m in rec.get("messages") or []:
            if isinstance(m, dict):
                m["ts"] = "2020-01-01T00:00:00Z"
        self.sc._save(rec)
        n = self.sc.close_idle_threads(idle_seconds=60)
        self.assertGreaterEqual(n, 1)
        self.assertIsNone(self.sc.get_thread(tid))

    def test_mark_escalated(self) -> None:
        t = self.sc.get_or_create_thread(user_id=7)
        r = self.sc.mark_escalated(t["thread_id"])
        self.assertTrue(r["ok"])
        self.assertTrue(r["thread"]["escalated"])
        self.assertEqual(r["thread"]["status"], "waiting_admin")
        listed = self.sc.list_threads()
        ids = [x["thread_id"] for x in listed["threads"]]
        self.assertIn(t["thread_id"], ids)

    def test_concurrent_poll_does_not_drop_bot(self) -> None:
        """GET mark_read used to rewrite the JSON and clobber a concurrent bot append."""
        import time
        from concurrent.futures import ThreadPoolExecutor

        t = self.sc.get_or_create_thread(user_id=42, user_name="PollRace")
        tid = t["thread_id"]
        self.sc.append_message(
            tid, sender="user", text="Payment kahan dikhe?", user_id=42
        )

        def poll(_n: int) -> None:
            for _ in range(60):
                self.sc.get_messages(tid, mark_read_for="user")
                time.sleep(0.003)

        def write_bot() -> None:
            time.sleep(0.02)
            r = self.sc.append_message(
                tid,
                sender="bot",
                text="Paid orders Help ke Transactions tab par dikhte hain.",
            )
            self.assertTrue(r["ok"])
            self.sc.set_agent_state(tid, "answered")

        with ThreadPoolExecutor(max_workers=5) as pool:
            polls = [pool.submit(poll, i) for i in range(4)]
            bot = pool.submit(write_bot)
            bot.result(timeout=10)
            for f in polls:
                f.result(timeout=10)

        packed = self.sc.get_messages(tid, mark_read_for="user")
        msgs = packed.get("messages") or []
        bots = [m for m in msgs if isinstance(m, dict) and m.get("sender") == "bot"]
        self.assertEqual(len(bots), 1, msgs)
        self.assertIn("Transactions", str(bots[0].get("text") or ""))
        self.assertEqual(str(packed.get("agent_state") or ""), "answered")
        packed2 = self.sc.get_messages(tid, mark_read_for="user")
        bots2 = [
            m
            for m in (packed2.get("messages") or [])
            if isinstance(m, dict) and m.get("sender") == "bot"
        ]
        self.assertEqual([b.get("id") for b in bots], [b.get("id") for b in bots2])

    def test_mark_read_does_not_rewrite_when_unread_zero(self) -> None:
        t = self.sc.get_or_create_thread(user_id=11)
        tid = t["thread_id"]
        saves = {"n": 0}
        orig = self.sc._save

        def wrapped(rec: dict) -> str:
            saves["n"] += 1
            return orig(rec)

        self.sc._save = wrapped  # type: ignore[method-assign]
        try:
            self.sc.get_messages(tid, mark_read_for="user")
            n1 = saves["n"]
            self.sc.get_messages(tid, mark_read_for="user")
            self.assertEqual(saves["n"], n1)
        finally:
            self.sc._save = orig  # type: ignore[method-assign]


if __name__ == "__main__":
    unittest.main()

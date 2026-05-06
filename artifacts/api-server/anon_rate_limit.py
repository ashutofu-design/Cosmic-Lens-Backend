"""Phase 2.10.7 P2 — Anonymous-caller rate limiter.

Replaces the synthetic `quota={used:0,limit:1}` fallback in /api/ask
that allowed trivial quota-bypass by omitting `user_id`. Tracks
per-IP request counts in a small sqlite ledger with daily reset.

Public:
  check_anon_quota(ip, limit=3) -> {allowed, used, limit, reset_at}
"""
from __future__ import annotations
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from typing import Dict

_DB = os.environ.get(
    "ANON_RATE_DB",
    os.path.join(os.path.dirname(__file__), "_anon_rate.sqlite3"),
)
_LOCK = threading.Lock()
_INITED = False


def _init(force: bool = False) -> None:
    """Idempotent table creation. Use force=True after detecting a missing
    table mid-process (e.g., DB file was deleted out from under us)."""
    global _INITED
    if _INITED and not force:
        return
    with _LOCK:
        if _INITED and not force:
            return
        os.makedirs(os.path.dirname(_DB), exist_ok=True)
        conn = sqlite3.connect(_DB)
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS anon_usage ("
                "  ip TEXT NOT NULL,"
                "  day TEXT NOT NULL,"
                "  used INTEGER NOT NULL DEFAULT 0,"
                "  PRIMARY KEY (ip, day)"
                ")"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_anon_day "
                "ON anon_usage(day)"
            )
            conn.commit()
        finally:
            conn.close()
        _INITED = True


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _seconds_until_utc_midnight() -> int:
    now = datetime.now(timezone.utc)
    next_midnight = now.replace(hour=0, minute=0, second=0,
                                  microsecond=0).replace(day=now.day)
    # Compute next 00:00 UTC
    secs_today = now.hour * 3600 + now.minute * 60 + now.second
    return max(1, 86400 - secs_today)


def check_anon_quota(ip: str, limit: int = 3) -> Dict:
    """Atomically increment-and-check the per-IP daily counter.

    Returns:
      allowed (bool), used (int post-increment if allowed else current),
      limit (int), reset_at (epoch seconds)
    """
    _init()
    if not ip:
        ip = "unknown"
    day = _today_utc()
    reset_at = int(time.time()) + _seconds_until_utc_midnight()

    try:
        with _LOCK:
            conn = sqlite3.connect(_DB)
            try:
                # Read current
                row = conn.execute(
                    "SELECT used FROM anon_usage WHERE ip=? AND day=?",
                    (ip, day)
                ).fetchone()
                current = int(row[0]) if row else 0
                if current >= limit:
                    return {"allowed": False, "used": current,
                            "limit": limit, "reset_at": reset_at}
                # Increment
                if row:
                    conn.execute(
                        "UPDATE anon_usage SET used=used+1 "
                        "WHERE ip=? AND day=?", (ip, day)
                    )
                else:
                    conn.execute(
                        "INSERT INTO anon_usage(ip,day,used) VALUES(?,?,1)",
                        (ip, day)
                    )
                conn.commit()
                # Best-effort cleanup of old days (>2 days)
                try:
                    conn.execute(
                        "DELETE FROM anon_usage WHERE day < ?",
                        ((datetime.now(timezone.utc).replace(
                            hour=0, minute=0, second=0,
                            microsecond=0)).strftime("%Y-%m-%d"),)
                    )
                    conn.commit()
                except Exception:
                    pass
                return {"allowed": True, "used": current + 1,
                        "limit": limit, "reset_at": reset_at}
            finally:
                conn.close()
    except sqlite3.OperationalError as e:
        # Gap-3 fix: if the DB file was deleted out from under us mid-process
        # (race after `rm _anon_rate.sqlite3`), the cached _INITED flag lies.
        # Force re-init once and retry. Only catches "no such table" class of
        # errors; anything else still falls through to the generic deny path.
        msg = str(e).lower()
        if "no such table" in msg or "unable to open" in msg:
            try:
                _init(force=True)
                with _LOCK:
                    conn = sqlite3.connect(_DB)
                    try:
                        row = conn.execute(
                            "SELECT used FROM anon_usage WHERE ip=? AND day=?",
                            (ip, day)
                        ).fetchone()
                        current = int(row[0]) if row else 0
                        if current >= limit:
                            return {"allowed": False, "used": current,
                                    "limit": limit, "reset_at": reset_at}
                        if row:
                            conn.execute(
                                "UPDATE anon_usage SET used=used+1 "
                                "WHERE ip=? AND day=?", (ip, day))
                        else:
                            conn.execute(
                                "INSERT INTO anon_usage(ip,day,used) "
                                "VALUES(?,?,1)", (ip, day))
                        conn.commit()
                        print("[anon_rate_limit] recovered from missing-table "
                              "via force-reinit", flush=True)
                        return {"allowed": True, "used": current + 1,
                                "limit": limit, "reset_at": reset_at}
                    finally:
                        conn.close()
            except Exception as e2:
                print(f"[anon_rate_limit] retry failed: {e2}", flush=True)
        print(f"[anon_rate_limit] error: {e}", flush=True)
        return {"allowed": False, "used": 0, "limit": limit,
                "reset_at": reset_at}
    except Exception as e:
        print(f"[anon_rate_limit] error: {e}", flush=True)
        return {"allowed": False, "used": 0, "limit": limit,
                "reset_at": reset_at}

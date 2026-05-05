"""Finance engine telemetry — Phase 1 (data collection only).

Logs every routed question to a sqlite table so we can later answer:
  - kitne % Qs HYBRID pe gir rahe?
  - LLM router classifier ka per-route hit-rate kya hai?
  - validator kitni baar fire ho raha kya flags pe?
  - latency P50/P95 per mode?
  - cache hit-rate per mode/route?

Pure WRITE-ONLY hot path (one INSERT per handled question, ~1 ms).
Read helpers exposed for offline inspection / future dashboard.

ADD-ONLY: shares the same sqlite file as answer_cache to avoid file
proliferation, but uses a separate `router_telemetry` table.
"""
from __future__ import annotations
import hashlib
import json
import os
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional

from finance_engine.answer_cache import _CACHE_DB

_LOCK = threading.Lock()
_INITED = False

# Phase 2.8.77 patch (Option A): non-blocking writes.
# - WAL mode → readers don't block writers, writers don't block readers
# - busy_timeout 50 ms → if another writer holds lock >50ms, drop the row
#   instead of stalling the user request (telemetry is best-effort)
# - log_event uses connect timeout=0.05s for the same reason
_WRITE_TIMEOUT_S = 0.05  # 50 ms — drop telemetry row rather than stall reply


def _init_db() -> None:
    global _INITED
    if _INITED:
        return
    with _LOCK:
        if _INITED:
            return
        os.makedirs(os.path.dirname(_CACHE_DB), exist_ok=True)
        conn = sqlite3.connect(_CACHE_DB, timeout=2.0)
        try:
            # WAL once per DB file — concurrent reader/writer safe
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=50")
                conn.execute("PRAGMA synchronous=NORMAL")
            except Exception as _pe:
                print(f"[finance_money.telemetry] pragma warn: {_pe}",
                      flush=True)
            conn.execute(
                "CREATE TABLE IF NOT EXISTS router_telemetry ("
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "  ts INTEGER NOT NULL,"
                "  question TEXT NOT NULL,"
                "  q_hash TEXT NOT NULL,"
                "  chart_fp TEXT,"
                "  regex_mode TEXT,"
                "  regex_route TEXT,"
                "  llm_mode TEXT,"
                "  llm_route TEXT,"
                "  llm_confidence REAL,"
                "  llm_reason TEXT,"
                "  final_mode TEXT NOT NULL,"
                "  final_route TEXT NOT NULL,"
                "  cache_hit INTEGER NOT NULL,"
                "  latency_ms INTEGER NOT NULL,"
                "  validator_flags TEXT,"
                "  validator_action TEXT"
                ")"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_telemetry_ts "
                "ON router_telemetry(ts)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_telemetry_route "
                "ON router_telemetry(final_route)"
            )
            conn.commit()
        finally:
            conn.close()
        _INITED = True


def _hash_q(q: str) -> str:
    return hashlib.sha1((q or "").lower().strip().encode("utf-8")
                        ).hexdigest()[:16]


def log_event(event: Dict[str, Any]) -> None:
    """Insert one telemetry row. Never raises, never blocks > 50ms.

    On sqlite lock contention (multi-worker writes to same file), the
    INSERT is silently dropped rather than stalling the user-facing
    reply path. Telemetry is best-effort by design.
    """
    try:
        _init_db()
        conn = sqlite3.connect(_CACHE_DB, timeout=_WRITE_TIMEOUT_S)
        try:
            try:
                conn.execute("PRAGMA busy_timeout=50")
            except Exception:
                pass
            conn.execute(
                "INSERT INTO router_telemetry "
                "(ts, question, q_hash, chart_fp, "
                " regex_mode, regex_route, "
                " llm_mode, llm_route, llm_confidence, llm_reason, "
                " final_mode, final_route, cache_hit, latency_ms, "
                " validator_flags, validator_action) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    int(event.get("ts") or time.time()),
                    (event.get("question") or "")[:500],
                    _hash_q(event.get("question") or ""),
                    event.get("chart_fp") or "",
                    event.get("regex_mode"),
                    event.get("regex_route"),
                    event.get("llm_mode"),
                    event.get("llm_route"),
                    float(event["llm_confidence"])
                        if event.get("llm_confidence") is not None else None,
                    (event.get("llm_reason") or "")[:200] or None,
                    event.get("final_mode") or "?",
                    event.get("final_route") or "?",
                    1 if event.get("cache_hit") else 0,
                    int(event.get("latency_ms") or 0),
                    json.dumps(event.get("validator_flags") or [],
                               ensure_ascii=False),
                    event.get("validator_action") or "none",
                ),
            )
            conn.commit()
        finally:
            conn.close()
    except sqlite3.OperationalError as oe:
        # 'database is locked' under contention — drop row, don't stall
        msg = str(oe).lower()
        if "lock" in msg or "busy" in msg:
            return  # silent skip, by design
        print(f"[finance_money.telemetry] op error: {oe}", flush=True)
    except Exception as e:
        print(f"[finance_money.telemetry] log error: {e}", flush=True)


# ── Read helpers (for offline inspection / future dashboard) ────────
def get_recent_events(limit: int = 50) -> List[Dict[str, Any]]:
    try:
        _init_db()
        conn = sqlite3.connect(_CACHE_DB)
        try:
            rows = conn.execute(
                "SELECT ts, question, regex_mode, regex_route, "
                " llm_mode, llm_route, llm_confidence, "
                " final_mode, final_route, cache_hit, latency_ms, "
                " validator_flags, validator_action "
                "FROM router_telemetry ORDER BY id DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
        finally:
            conn.close()
    except Exception as e:
        print(f"[finance_money.telemetry] read error: {e}", flush=True)
        return []
    keys = ["ts", "question", "regex_mode", "regex_route",
            "llm_mode", "llm_route", "llm_confidence",
            "final_mode", "final_route", "cache_hit", "latency_ms",
            "validator_flags", "validator_action"]
    out = []
    for r in rows:
        d = dict(zip(keys, r))
        try:
            d["validator_flags"] = json.loads(d.get("validator_flags") or "[]")
        except Exception:
            d["validator_flags"] = []
        out.append(d)
    return out


def get_route_stats() -> Dict[str, Any]:
    """Aggregate per-route counts + cache hit-rate + avg latency."""
    try:
        _init_db()
        conn = sqlite3.connect(_CACHE_DB)
        try:
            rows = conn.execute(
                "SELECT final_mode, final_route, "
                " COUNT(*) AS n, "
                " SUM(cache_hit) AS hits, "
                " AVG(latency_ms) AS avg_lat, "
                " MAX(latency_ms) AS max_lat "
                "FROM router_telemetry "
                "GROUP BY final_mode, final_route "
                "ORDER BY n DESC"
            ).fetchall()
            total = conn.execute(
                "SELECT COUNT(*) FROM router_telemetry"
            ).fetchone()[0]
            llm_used = conn.execute(
                "SELECT COUNT(*) FROM router_telemetry "
                "WHERE llm_mode IS NOT NULL"
            ).fetchone()[0]
            re_routed = conn.execute(
                "SELECT COUNT(*) FROM router_telemetry "
                "WHERE llm_mode IS NOT NULL "
                "  AND (final_mode != 'HYBRID' OR final_route != "
                "       'general_finance_overview')"
            ).fetchone()[0]
        finally:
            conn.close()
    except Exception as e:
        print(f"[finance_money.telemetry] stats error: {e}", flush=True)
        return {}
    routes = []
    for mode, route, n, hits, avg_lat, max_lat in rows:
        routes.append({
            "mode": mode, "route": route, "count": n,
            "cache_hit_rate": round((hits or 0) / n, 3) if n else 0,
            "avg_latency_ms": int(avg_lat or 0),
            "max_latency_ms": int(max_lat or 0),
        })
    return {
        "total_questions": total,
        "llm_router_invocations": llm_used,
        "llm_router_re_routes_accepted": re_routed,
        "llm_router_acceptance_rate": (
            round(re_routed / llm_used, 3) if llm_used else 0
        ),
        "per_route": routes,
    }


def get_validator_stats() -> Dict[str, Any]:
    """How often validator fires + what it does."""
    try:
        _init_db()
        conn = sqlite3.connect(_CACHE_DB)
        try:
            rows = conn.execute(
                "SELECT validator_action, COUNT(*) AS n "
                "FROM router_telemetry "
                "GROUP BY validator_action ORDER BY n DESC"
            ).fetchall()
        finally:
            conn.close()
    except Exception as e:
        print(f"[finance_money.telemetry] validator stats: {e}", flush=True)
        return {}
    return {action or "none": n for action, n in rows}

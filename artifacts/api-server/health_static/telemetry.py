"""Health Static engine telemetry — Phase H1 (data collection).

Mirror of finance_static/telemetry.py with health-specific dimension
columns. Logs every routed health question to a sqlite table for later
calibration analysis.

Pure WRITE-ONLY hot path (one INSERT per handled question, ~1 ms).

ADD-ONLY: shares the same sqlite file as health_static.answer_cache to
avoid file proliferation, but uses a separate `health_telemetry` table.
"""
from __future__ import annotations
import hashlib
import json
import os
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional

from health_static.answer_cache import _CACHE_DB

_LOCK = threading.Lock()
_INITED = False

_WRITE_TIMEOUT_S = 0.05  # 50 ms — drop telemetry row rather than stall


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
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=50")
                conn.execute("PRAGMA synchronous=NORMAL")
            except Exception as _pe:
                print(f"[health_static.telemetry] pragma warn: {_pe}",
                      flush=True)
            conn.execute(
                "CREATE TABLE IF NOT EXISTS health_telemetry ("
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
                "  validator_action TEXT,"
                # ── Health-specific dimension verdicts ──
                "  vitality_v TEXT,"
                "  disease_v TEXT,"
                "  chronic_v TEXT,"
                "  mental_v TEXT,"
                "  accident_v TEXT,"
                # ── KP cusp verdicts (planet/verdict like 'Saturn/RED') ──
                "  kp_h1_v TEXT,"
                "  kp_h6_v TEXT,"
                "  kp_h8_v TEXT,"
                "  kp_engine_ver TEXT,"
                # ── Conflict + brand-safety tracking ──
                "  conflict_flag INTEGER,"
                "  confidence_low_count INTEGER,"
                "  brand_safety_action TEXT,"   # 'doctor_disclaimer_added',
                                                  # 'diagnosis_ban_triggered',
                                                  # 'sensitive_bucket' etc.
                "  sensitive_bucket TEXT"        # mental/repro/parent/...
                ")"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_health_tele_ts "
                "ON health_telemetry(ts)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_health_tele_route "
                "ON health_telemetry(final_route)"
            )
            conn.commit()
        finally:
            conn.close()
        _INITED = True


def _hash_q(q: str) -> str:
    return hashlib.sha1((q or "").lower().strip().encode("utf-8")
                        ).hexdigest()[:16]


def log_event(event: Dict[str, Any]) -> None:
    """Insert one telemetry row. Never raises, never blocks > 50ms."""
    try:
        _init_db()
        conn = sqlite3.connect(_CACHE_DB, timeout=_WRITE_TIMEOUT_S)
        try:
            try:
                conn.execute("PRAGMA busy_timeout=50")
            except Exception:
                pass
            conn.execute(
                "INSERT INTO health_telemetry "
                "(ts, question, q_hash, chart_fp, "
                " regex_mode, regex_route, "
                " llm_mode, llm_route, llm_confidence, llm_reason, "
                " final_mode, final_route, cache_hit, latency_ms, "
                " validator_flags, validator_action, "
                " vitality_v, disease_v, chronic_v, mental_v, accident_v, "
                " kp_h1_v, kp_h6_v, kp_h8_v, kp_engine_ver, "
                " conflict_flag, confidence_low_count, "
                " brand_safety_action, sensitive_bucket) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
                "        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
                    # ── Dimension verdicts ──
                    event.get("vitality_v"),
                    event.get("disease_v"),
                    event.get("chronic_v"),
                    event.get("mental_v"),
                    event.get("accident_v"),
                    # ── KP cusps ──
                    event.get("kp_h1_v"),
                    event.get("kp_h6_v"),
                    event.get("kp_h8_v"),
                    event.get("kp_engine_ver"),
                    # ── Conflict tracking (precedence-correct conditional) ──
                    (1 if event.get("conflict_flag") else 0)
                        if event.get("conflict_flag") is not None else None,
                    int(event["confidence_low_count"])
                        if event.get("confidence_low_count") is not None
                        else None,
                    # ── Brand-safety ──
                    event.get("brand_safety_action"),
                    event.get("sensitive_bucket"),
                ),
            )
            conn.commit()
        finally:
            conn.close()
    except sqlite3.OperationalError as oe:
        msg = str(oe).lower()
        if "lock" in msg or "busy" in msg:
            return  # silent skip
        print(f"[health_static.telemetry] op error: {oe}", flush=True)
    except Exception as e:
        print(f"[health_static.telemetry] log error: {e}", flush=True)


def get_recent_events(limit: int = 50) -> List[Dict[str, Any]]:
    try:
        _init_db()
        conn = sqlite3.connect(_CACHE_DB)
        try:
            rows = conn.execute(
                "SELECT ts, question, final_mode, final_route, "
                " vitality_v, disease_v, chronic_v, mental_v, accident_v, "
                " kp_h1_v, kp_h6_v, kp_h8_v, conflict_flag, "
                " confidence_low_count, brand_safety_action, latency_ms "
                "FROM health_telemetry ORDER BY id DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
        finally:
            conn.close()
    except Exception as e:
        print(f"[health_static.telemetry] read error: {e}", flush=True)
        return []
    keys = ["ts", "question", "final_mode", "final_route",
            "vitality_v", "disease_v", "chronic_v", "mental_v", "accident_v",
            "kp_h1_v", "kp_h6_v", "kp_h8_v", "conflict_flag",
            "confidence_low_count", "brand_safety_action", "latency_ms"]
    return [dict(zip(keys, r)) for r in rows]

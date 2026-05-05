"""Phase 2.10.7 — Sqlite-backed answer cache.

Key = sha256(chart_norm + MD-AD + topic_id + sub_route)
TTL = until next AD change (auto-invalidate on dasha pointer change)

Same chart + same MD-AD + same question type = same cached reply
forever (until dasha changes).
"""
from __future__ import annotations
import hashlib
import json
import os
import sqlite3
import threading
import time
from typing import Any, Optional

_CACHE_DB = os.environ.get(
    "FINANCE_CACHE_DB",
    os.path.join(os.path.dirname(__file__), "_finance_cache.sqlite3"),
)
_LOCK = threading.Lock()
_INITED = False


def _init_db() -> None:
    global _INITED
    if _INITED:
        return
    with _LOCK:
        if _INITED:
            return
        os.makedirs(os.path.dirname(_CACHE_DB), exist_ok=True)
        conn = sqlite3.connect(_CACHE_DB)
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS answer_cache ("
                "  cache_key TEXT PRIMARY KEY,"
                "  reply_text TEXT NOT NULL,"
                "  reply_meta TEXT NOT NULL,"
                "  created_at INTEGER NOT NULL,"
                "  hit_count INTEGER NOT NULL DEFAULT 0"
                ")"
            )
            conn.commit()
        finally:
            conn.close()
        _INITED = True


def _normalise_birth(birth: dict | None) -> str:
    """Produce a stable string from birth_data ignoring volatile fields."""
    if not isinstance(birth, dict):
        return ""
    keep = ("day", "month", "year", "hour", "minute", "ampm",
            "lat", "lon", "tz", "gender")
    parts = []
    for k in keep:
        v = birth.get(k)
        if v is None:
            continue
        parts.append(f"{k}={v}")
    return "|".join(parts)


def _chart_fingerprint(kundli: dict | None) -> str:
    """Phase 2.10.7 P1 fix — deterministic hash of computed chart.

    Includes ascendant + every planet's name/sign/house/retrograde so
    that two different chart pipelines (or any change in computed
    output) produce different cache keys, even when birth-fields are
    identical. Defends against cross-contamination from pipeline
    upgrades or alternate ayanamsha settings.
    """
    if not isinstance(kundli, dict):
        return ""
    asc = kundli.get("ascendant", "")
    planets = kundli.get("planets") or []
    # Sort by name to make order-independent, then take only the
    # fields that affect stock-engine output.
    rows = []
    for p in sorted(planets, key=lambda x: x.get("name", "")):
        rows.append(
            f"{p.get('name','')}:{p.get('sign','')}:"
            f"H{p.get('house','')}:r{1 if p.get('retrograde') else 0}"
        )
    raw = f"asc={asc}||" + "|".join(rows)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def make_cache_key(birth: dict | None, kundli: dict, topic: str,
                    route: str) -> str:
    """Deterministic key. Includes MD-AD so cache auto-invalidates
    when antar-dasha changes. P1 fix: also includes a chart fingerprint
    so identical birth fields with different computed charts (e.g.
    pipeline change) cannot serve stale/wrong replies."""
    cd = (kundli or {}).get("currentDasha") or {}
    md = cd.get("maha", "")
    ad = cd.get("antar", "")
    raw = "||".join([
        _normalise_birth(birth),
        f"chart={_chart_fingerprint(kundli)}",
        f"md={md}", f"ad={ad}",
        f"topic={topic}", f"route={route}",
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cached(cache_key: str) -> Optional[dict]:
    _init_db()
    try:
        conn = sqlite3.connect(_CACHE_DB)
        try:
            row = conn.execute(
                "SELECT reply_text, reply_meta FROM answer_cache "
                "WHERE cache_key = ?", (cache_key,)
            ).fetchone()
            if not row:
                return None
            # Bump hit count (best-effort)
            try:
                conn.execute(
                    "UPDATE answer_cache SET hit_count = hit_count + 1 "
                    "WHERE cache_key = ?", (cache_key,)
                )
                conn.commit()
            except Exception:
                pass
            try:
                meta = json.loads(row[1])
            except Exception:
                meta = {}
            return {"text": row[0], "meta": meta, "cache_hit": True}
        finally:
            conn.close()
    except Exception as e:
        print(f"[finance.cache] get error: {e}", flush=True)
        return None


def put_cached(cache_key: str, reply_text: str,
                reply_meta: dict | None = None) -> bool:
    _init_db()
    try:
        conn = sqlite3.connect(_CACHE_DB)
        try:
            conn.execute(
                "INSERT OR REPLACE INTO answer_cache "
                "(cache_key, reply_text, reply_meta, created_at, hit_count) "
                "VALUES (?, ?, ?, ?, 0)",
                (cache_key, reply_text or "",
                 json.dumps(reply_meta or {}, default=str),
                 int(time.time())),
            )
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception as e:
        print(f"[finance.cache] put error: {e}", flush=True)
        return False


def cache_stats() -> dict:
    _init_db()
    try:
        conn = sqlite3.connect(_CACHE_DB)
        try:
            row = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(hit_count), 0) "
                "FROM answer_cache"
            ).fetchone()
            return {"entries": int(row[0] or 0),
                    "total_hits": int(row[1] or 0)}
        finally:
            conn.close()
    except Exception:
        return {"entries": 0, "total_hits": 0}

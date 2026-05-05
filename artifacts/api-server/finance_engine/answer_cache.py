"""Sqlite-backed answer cache — finance engine.

Mirror of stock_engine/answer_cache.py with separate DB file.

Key = sha256(chart_norm + MD-AD + topic_id + sub_route)
TTL = until next AD change (auto-invalidate on dasha pointer change)
"""
from __future__ import annotations
import hashlib
import json
import os
import sqlite3
import threading
import time
from typing import Optional

_CACHE_DB = os.environ.get(
    "FINANCE_MONEY_CACHE_DB",
    os.path.join(os.path.dirname(__file__), "_finance_money_cache.sqlite3"),
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
    if not isinstance(kundli, dict):
        return ""
    asc = kundli.get("ascendant", "")
    planets = kundli.get("planets") or []
    rows = []
    for p in sorted(planets, key=lambda x: x.get("name", "")):
        rows.append(
            f"{p.get('name','')}:{p.get('sign','')}:"
            f"H{p.get('house','')}:r{1 if p.get('retrograde') else 0}"
        )
    raw = f"asc={asc}||" + "|".join(rows)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _normalise_question(q: str | None) -> str:
    """Lowercase + collapse whitespace + strip punctuation for stable
    hashing. Two phrasings that differ only in case/spacing share key."""
    if not isinstance(q, str):
        return ""
    import re as _re
    s = q.strip().lower()
    s = _re.sub(r"[^\w\s]+", " ", s)   # punctuation → space
    s = _re.sub(r"\s+", " ", s).strip()
    return s


def make_cache_key(birth: dict | None, kundli: dict, topic: str,
                    route: str, question: str | None = None) -> str:
    """Cache key. If `question` is provided (HYBRID mode), its normalised
    SHA1 prefix is mixed in so different phrasings get different cached
    answers. For routes with deterministic per-route output (DIRECT,
    NARRATIVE, WARNING), pass question=None to keep cache hit-rate high.
    """
    cd = (kundli or {}).get("currentDasha") or {}
    md = cd.get("maha", "")
    ad = cd.get("antar", "")
    parts = [
        _normalise_birth(birth),
        f"chart={_chart_fingerprint(kundli)}",
        f"md={md}", f"ad={ad}",
        f"topic={topic}", f"route={route}",
    ]
    if question:
        q_norm = _normalise_question(question)
        q_hash = hashlib.sha1(q_norm.encode("utf-8")).hexdigest()[:16]
        parts.append(f"q={q_hash}")
    raw = "||".join(parts)
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
        print(f"[finance_money.cache] get error: {e}", flush=True)
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
        print(f"[finance_money.cache] put error: {e}", flush=True)
        return False

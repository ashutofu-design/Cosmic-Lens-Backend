"""
Phase-3 cache layer for Cosmic Lens.

Two caches:
  1. KundliCache         — global natal chart cache, keyed by birth_key.
  2. DailyTransitCache   — per-(birth_key, date) transit snapshot.

Both are READ-THROUGH caches: helpers below try cache first, fall back to
fresh computation on miss, persist the result, and return it. Engines
(marriage/career/daily-horoscope/etc) should call these helpers instead
of invoking calculate_kundli() / compute_transits() directly.

Cache invalidation:
  - Natal: when stored calc_version != current engine calcVersion.
  - Transit: per-day key, so each new day naturally pulls a fresh row.

Safe-by-default: any DB error degrades gracefully to fresh-compute and
returns the result (caching is best-effort, never blocks the user).
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Any, Optional

from database import db
from models import (
    KundliCache,
    DailyTransitCache,
    compute_birth_key,
)


# ─────────────────────────────────────────────────────────────────────────
# Natal kundli cache
# ─────────────────────────────────────────────────────────────────────────

def _hot_fields_from_kundli(k: dict) -> dict:
    """Extract denormalized hot fields from a fresh kundli dict."""
    out: dict[str, Any] = {
        "ascendant":      str(k.get("ascendant") or "")[:20] or None,
        "moon_sign":      str(k.get("moonSign") or "")[:20] or None,
        "sun_sign":       str(k.get("sunSign")  or "")[:20] or None,
        "nakshatra":      str(k.get("nakshatra") or "")[:30] or None,
        "current_md":     None,
        "current_ad":     None,
        "current_md_end": None,
    }
    cd = k.get("currentDasha") or {}
    if isinstance(cd, dict):
        out["current_md"] = str(cd.get("maha")  or "")[:20] or None
        out["current_ad"] = str(cd.get("antar") or "")[:20] or None
        end = cd.get("endDate") or cd.get("end")
        if end:
            try:
                out["current_md_end"] = datetime.strptime(str(end)[:10], "%Y-%m-%d").date()
            except Exception:
                pass
    return out


def get_or_compute_kundli(birth_data: dict) -> dict:
    """
    Read-through cache for natal kundli.

      1. Compute birth_key from birth_data.
      2. SELECT KundliCache row.
      3. If hit AND calc_version matches → return cached blob.
      4. Else: calculate_kundli(), upsert row, return fresh blob.

    Any DB exception → fall through to fresh compute (never blocks user).
    """
    # Lazy import to avoid circular (kundli_engine imports nothing from here).
    from kundli_engine import calculate_kundli

    bk = compute_birth_key(birth_data)
    if not bk:
        # Birth data malformed → can't cache, just compute.
        return calculate_kundli(birth_data)

    # ── Try cache ──
    try:
        row = KundliCache.query.get(bk)
        if row is not None:
            fresh = calculate_kundli  # reference for version check below
            # Compare against engine's CURRENT calcVersion (cheap probe).
            # We trust the stored version: if it matches a known recent value,
            # return cached. Otherwise recompute. To get the current version
            # without recomputing, we peek a constant in kundli_engine.
            try:
                from kundli_engine import KUNDLI_CALC_VERSION as _CV
            except ImportError:
                _CV = None
            if _CV is None or row.calc_version == _CV:
                row.last_accessed = datetime.utcnow()
                row.access_count = (row.access_count or 0) + 1
                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                blob = row.kundli_json or {}
                if isinstance(blob, dict):
                    blob = dict(blob)  # shallow copy so callers can mutate
                    blob["_cache"] = {"hit": True, "source": "kundli_cache"}
                return blob
    except Exception as exc:
        print(f"[cache.kundli] read failed (non-fatal): {exc}")
        try:
            db.session.rollback()
        except Exception:
            pass

    # ── Miss → compute fresh ──
    fresh_chart = calculate_kundli(birth_data)
    if not isinstance(fresh_chart, dict):
        return fresh_chart  # error path; nothing to cache

    cv = int(fresh_chart.get("calcVersion") or 0)
    hot = _hot_fields_from_kundli(fresh_chart)

    # ── Upsert ──
    try:
        row = KundliCache.query.get(bk)
        if row is None:
            row = KundliCache(birth_key=bk)
            db.session.add(row)
        row.kundli_json    = fresh_chart
        row.calc_version   = cv
        row.ascendant      = hot["ascendant"]
        row.moon_sign      = hot["moon_sign"]
        row.sun_sign       = hot["sun_sign"]
        row.nakshatra      = hot["nakshatra"]
        row.current_md     = hot["current_md"]
        row.current_ad     = hot["current_ad"]
        row.current_md_end = hot["current_md_end"]
        row.computed_at    = datetime.utcnow()
        row.last_accessed  = datetime.utcnow()
        row.access_count   = (row.access_count or 0) + 1
        db.session.commit()
    except Exception as exc:
        print(f"[cache.kundli] write failed (non-fatal): {exc}")
        try:
            db.session.rollback()
        except Exception:
            pass

    return fresh_chart


# ─────────────────────────────────────────────────────────────────────────
# Daily transit cache
# ─────────────────────────────────────────────────────────────────────────

def get_or_compute_transit(
    birth_key: str,
    natal_lagna_sign_idx: Any,
    natal_moon_sign_idx: Any,
    dob: Optional[datetime] = None,
    when: Optional[datetime] = None,
) -> dict:
    """
    Read-through cache for daily transit snapshot.

    Cache key = (birth_key, date(when)). For ad-hoc queries with no
    birth_key (legacy callers), we skip the cache and compute fresh.
    """
    from transits import compute_transits

    when = when or datetime.utcnow()
    cache_date = when.date() if hasattr(when, "date") else date.today()

    if not birth_key:
        return compute_transits(natal_lagna_sign_idx, natal_moon_sign_idx,
                                dob=dob, when=when)

    # ── Try cache ──
    try:
        row = DailyTransitCache.query.get((birth_key, cache_date))
        if row is not None:
            row.last_accessed = datetime.utcnow()
            row.access_count = (row.access_count or 0) + 1
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
            blob = row.transit_json or {}
            if isinstance(blob, dict):
                blob = dict(blob)
                blob["_cache"] = {"hit": True, "source": "daily_transit_cache"}
            return blob
    except Exception as exc:
        print(f"[cache.transit] read failed (non-fatal): {exc}")
        try:
            db.session.rollback()
        except Exception:
            pass

    # ── Miss → compute fresh ──
    fresh = compute_transits(natal_lagna_sign_idx, natal_moon_sign_idx,
                             dob=dob, when=when)
    if not isinstance(fresh, dict) or not fresh:
        return fresh  # nothing useful to cache

    # ── Upsert ──
    try:
        row = DailyTransitCache.query.get((birth_key, cache_date))
        if row is None:
            row = DailyTransitCache(birth_key=birth_key, transit_date=cache_date)
            db.session.add(row)
        row.transit_json  = fresh
        row.computed_at   = datetime.utcnow()
        row.last_accessed = datetime.utcnow()
        row.access_count  = (row.access_count or 0) + 1
        db.session.commit()
    except Exception as exc:
        print(f"[cache.transit] write failed (non-fatal): {exc}")
        try:
            db.session.rollback()
        except Exception:
            pass

    return fresh


# ─────────────────────────────────────────────────────────────────────────
# Stats helper (for /admin or future debugging)
# ─────────────────────────────────────────────────────────────────────────

def cache_stats() -> dict:
    """Quick counters for both caches. Safe even if tables are empty."""
    try:
        kc = KundliCache.query.count()
    except Exception:
        kc = -1
    try:
        tc = DailyTransitCache.query.count()
    except Exception:
        tc = -1
    return {"kundli_cache_rows": kc, "daily_transit_cache_rows": tc}

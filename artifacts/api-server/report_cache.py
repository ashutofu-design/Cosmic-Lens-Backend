"""
Report Cache + Failsafe Wrapper for Cosmic Lens premium PDFs.

Responsibilities (kept intentionally tiny — no DB schema change):
  1. Persist generated PDFs to disk so users can re-download from "My Reports"
  2. Skip regeneration when the same (user_id, kind, name+dob+lang+...) hash
     was rendered recently → saves OpenAI + compute cost
  3. Provide a `safe_render()` wrapper that catches engine/AI/PDF failures
     and returns a structured error instead of bringing the request down

Storage:
  .cache/reports/<sha1[:2]>/<sha1>.pdf      # the PDF binary
  .cache/reports/_ledger.json               # one row per generated report

Ledger row shape:
  {
    "id":           "<sha1>",
    "user_id":      123,
    "kind":         "numerology_pro" | "face_reading" | "vastu_pro" | "business_vastu"
                    | "milan_pro" | "love_reality_pro",
    "report_type":  "Numerology Pro",     # human label
    "name":         "Aarti Kapoor",
    "dob":          "1990-05-15",
    "language":     "hinglish",
    "params_hash":  "<sha1>",
    "filename":     "Numerology_Pro_Aarti_Kapoor.pdf",
    "size_bytes":   118432,
    "created_at":   "2026-04-22T07:55:00Z"
  }

NEVER raises — every helper is safe-by-default (returns None / empty list).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger(__name__)

# Regenerate after this many days even on cache hit (keeps content fresh)
DEFAULT_TTL_DAYS = int(os.environ.get("REPORT_CACHE_TTL_DAYS", "30"))

_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                     ".cache", "reports"))
_LEDGER = os.path.join(_BASE, "_ledger.json")
_lock = threading.Lock()


def _ensure_dir(p: str) -> None:
    try:
        os.makedirs(p, exist_ok=True)
    except Exception:
        pass


def _birth_slice(p: Dict[str, Any]) -> Dict[str, Any]:
    """Birth inputs that affect kundli + PDF content."""
    p = p or {}
    return {
        k: p.get(k)
        for k in (
            "name", "gender", "day", "month", "year",
            "hour", "minute", "ampm", "lat", "lon", "tz", "place",
        )
    }


def _kundli_fingerprint(k: Dict[str, Any]) -> Dict[str, Any]:
    """Stable chart identity when full birth dict is not in the request."""
    k = k or {}
    return {
        "name": k.get("name"),
        "moonLongitude": k.get("moonLongitude"),
        "ascendantDeg": k.get("ascendantDeg"),
        "nakshatra": k.get("nakshatra"),
        "nakshatraPada": k.get("nakshatraPada"),
        "moonSign": k.get("moonSign"),
        "ascendant": k.get("ascendant"),
    }


def couple_cache_params(
    lang: str,
    p1: Dict[str, Any] | None = None,
    p2: Dict[str, Any] | None = None,
    kundli_p1: Dict[str, Any] | None = None,
    kundli_p2: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Cache key inputs for Love Reality / Milan Pro couple PDFs.
    Prefers birth details; falls back to computed kundli fingerprints.
    """
    p1 = p1 or {}
    p2 = p2 or {}
    if p1.get("year") or p1.get("day"):
        return {"lang": lang, "p1": _birth_slice(p1), "p2": _birth_slice(p2)}
    if kundli_p1 and kundli_p2:
        return {
            "lang": lang,
            "k1": _kundli_fingerprint(kundli_p1),
            "k2": _kundli_fingerprint(kundli_p2),
        }
    return {"lang": lang, "p1": _birth_slice(p1), "p2": _birth_slice(p2)}


def _hash_params(params: Dict[str, Any]) -> str:
    """Deterministic hash of all inputs that affect PDF content."""
    payload = json.dumps(params or {}, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _file_for(h: str) -> str:
    return os.path.join(_BASE, h[:2], f"{h}.pdf")


def path_for_id(report_id: str) -> str:
    """Absolute path to a cached PDF file by ledger id (sha1)."""
    return _file_for(report_id)


def _load_ledger() -> List[dict]:
    try:
        with open(_LEDGER, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_ledger(rows: List[dict]) -> None:
    try:
        _ensure_dir(_BASE)
        tmp = _LEDGER + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=0)
        os.replace(tmp, _LEDGER)
    except Exception as exc:
        log.warning("[report_cache] ledger save failed: %s", exc)


# ── Cache lookup / save ───────────────────────────────────────────────────
def find(user_id: int, kind: str, params: Dict[str, Any],
         ttl_days: int = DEFAULT_TTL_DAYS) -> Optional[bytes]:
    """Return cached PDF bytes if a fresh entry exists, else None."""
    try:
        h = _hash_params({**params, "kind": kind, "user_id": user_id})
        p = _file_for(h)
        if not os.path.exists(p):
            return None
        age_days = (time.time() - os.stat(p).st_mtime) / 86400.0
        if age_days > ttl_days:
            return None
        with open(p, "rb") as fh:
            return fh.read()
    except Exception as exc:
        log.warning("[report_cache] find failed: %s", exc)
        return None


def save(user_id: int, kind: str, report_type: str,
         params: Dict[str, Any], pdf_bytes: bytes,
         filename: str = "report.pdf") -> Optional[str]:
    """
    Persist PDF + append ledger row. Returns the report id (sha1) or None.
    Safe — never raises.
    """
    if not pdf_bytes:
        return None
    try:
        h = _hash_params({**params, "kind": kind, "user_id": user_id})
        p = _file_for(h)
        _ensure_dir(os.path.dirname(p))
        with open(p, "wb") as fh:
            fh.write(pdf_bytes)

        with _lock:
            rows = _load_ledger()
            # De-dupe: drop any prior row with same id
            rows = [r for r in rows if r.get("id") != h]
            rows.insert(0, {
                "id":           h,
                "user_id":      int(user_id) if user_id else 0,
                "kind":         kind,
                "report_type":  report_type,
                "name":         (params or {}).get("name", ""),
                "dob":          (params or {}).get("dob", ""),
                "language":     (params or {}).get("lang") or (params or {}).get("language", ""),
                "params_hash":  h,
                "filename":     filename,
                "size_bytes":   len(pdf_bytes),
                "created_at":   datetime.now(timezone.utc).isoformat(),
            })
            # Cap ledger at 5000 rows
            if len(rows) > 5000:
                rows = rows[:5000]
            _save_ledger(rows)
        return h
    except Exception as exc:
        log.warning("[report_cache] save failed: %s", exc)
        return None


def list_for_user(user_id: int, limit: int = 50) -> List[dict]:
    """Return newest-first list of report metadata for a user."""
    try:
        rows = _load_ledger()
        mine = [r for r in rows if r.get("user_id") == int(user_id)]
        # Filter out entries whose file no longer exists
        out = []
        for r in mine[:max(1, min(limit, 200))]:
            if os.path.exists(_file_for(r["id"])):
                out.append({
                    "id":          r["id"],
                    "report_type": r.get("report_type") or r.get("kind"),
                    "kind":        r.get("kind"),
                    "name":        r.get("name"),
                    "dob":         r.get("dob"),
                    "language":    r.get("language"),
                    "size_bytes":  r.get("size_bytes"),
                    "date":        r.get("created_at"),
                    "download_url": f"/api/my-reports/{r['id']}",
                })
        return out
    except Exception as exc:
        log.warning("[report_cache] list_for_user failed: %s", exc)
        return []


def get_pdf_bytes(report_id: str, user_id: int) -> Optional[bytes]:
    """
    Read a cached PDF by id, ONLY if it belongs to user_id.
    Returns None if not found or not owned.
    """
    try:
        rows = _load_ledger()
        match = next((r for r in rows
                      if r.get("id") == report_id
                      and int(r.get("user_id") or 0) == int(user_id)), None)
        if not match:
            return None
        p = _file_for(report_id)
        if not os.path.exists(p):
            return None
        with open(p, "rb") as fh:
            return fh.read()
    except Exception as exc:
        log.warning("[report_cache] get_pdf_bytes failed: %s", exc)
        return None


def get_filename_for(report_id: str) -> str:
    try:
        rows = _load_ledger()
        match = next((r for r in rows if r.get("id") == report_id), None)
        return (match or {}).get("filename", "report.pdf")
    except Exception:
        return "report.pdf"


# ── Failsafe render wrapper ───────────────────────────────────────────────
def safe_render(label: str, render_fn: Callable[[], bytes]) -> tuple[Optional[bytes], Optional[str]]:
    """
    Run a render callable. Catches everything. Returns (pdf_bytes, error_msg).
    On failure: logs a clean OPENAI_FAILED / RENDER_FAILED line and returns
    (None, "<message>") so the caller can return a 5xx without leaking traces.
    """
    t0 = time.time()
    try:
        out = render_fn()
        elapsed = time.time() - t0
        size = len(out) if out else 0
        log.info("[REPORT_GEN] %s success bytes=%d in %.1fs", label, size, elapsed)
        if not out:
            return None, "empty PDF returned by renderer"
        return out, None
    except Exception as exc:
        elapsed = time.time() - t0
        msg = str(exc)
        flavor = "OPENAI_FAILED" if any(s in msg.lower() for s in (
            "429", "insufficient_quota", "rate limit", "timeout",
            "openai", "api key")) else "RENDER_FAILED"
        log.error("[REPORT_GEN] %s %s in %.1fs: %s", label, flavor, elapsed, msg)
        return None, msg


# ── Subscription/payment gate helper ──────────────────────────────────────
def require_paid_plan(user, allowed: tuple = ("pro", "elite", "trial")) -> Optional[str]:
    """
    Returns None if the user is allowed; else returns a short error string.

    `allowed` defaults to all paid tiers. Pass a narrower tuple (e.g. ("pro",))
    for stricter endpoints.
    """
    if not user:
        return "auth_required"
    try:
        from subscription_helper import effective_plan
        plan = effective_plan(user)
    except Exception:
        plan = getattr(user, "plan", None) or "free"
    if plan in allowed:
        return None
    return f"payment_required (current plan: {plan})"

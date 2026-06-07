"""
Append-only ledger: OpenAI token + INR cost per premium PDF generation.

Stored at .cache/reports/_pdf_cost_ledger.json (no DB migration).
Used by admin panel to audit duplicate/extra OpenAI calls.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger(__name__)

_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".cache", "reports"))
_LEDGER = os.path.join(_BASE, "_pdf_cost_ledger.json")
_MAX_ROWS = int(os.environ.get("PDF_COST_LEDGER_MAX_ROWS", "5000") or "5000")
_lock = threading.Lock()

KIND_LABELS: dict[str, str] = {
    "love_reality_pro": "Love PDF",
    "milan_pro": "Milan PDF",
}


def _ensure_dir() -> None:
    try:
        os.makedirs(_BASE, exist_ok=True)
    except Exception:
        pass


def _load() -> list[dict[str, Any]]:
    try:
        with open(_LEDGER, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(rows: list[dict[str, Any]]) -> None:
    try:
        _ensure_dir()
        tmp = _LEDGER + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=0)
        os.replace(tmp, _LEDGER)
    except Exception as exc:
        log.warning("[pdf_generation_log] save failed: %s", exc)


def _phase_labels(phases: list[dict[str, Any]] | None) -> list[str]:
    out: list[str] = []
    for p in phases or []:
        if not isinstance(p, dict):
            continue
        phase = str(p.get("phase") or "call")
        pt = int(p.get("prompt_tokens") or 0)
        ct = int(p.get("completion_tokens") or 0)
        usd = float(p.get("estimated_cost_usd") or 0)
        out.append(f"{phase}: {pt}+{ct} tok ${usd:.4f}")
    return out


def _build_notes(pdf_gen: dict[str, Any], *, report_cache_hit: bool) -> str:
    parts: list[str] = []
    if report_cache_hit:
        parts.append("PDF cache hit — OpenAI skipped")
    elif pdf_gen.get("cache_hit"):
        parts.append("LLM polish cache hit — OpenAI skipped")
    if pdf_gen.get("openai_skipped") and not report_cache_hit and not pdf_gen.get("cache_hit"):
        reason = pdf_gen.get("skip_reason") or pdf_gen.get("final_status")
        if reason:
            parts.append(f"OpenAI skipped ({reason})")
    oc = int(pdf_gen.get("openai_call_count") or 0)
    regen = int(pdf_gen.get("regen_count") or 0)
    retry = int(pdf_gen.get("retry_count") or 0)
    extra = max(0, oc - 1)
    if extra > 0:
        parts.append(f"{extra} extra OpenAI call(s) beyond primary")
    if regen > 0:
        parts.append(f"{regen} depth-regen round(s)")
    if retry > 0:
        parts.append(f"{retry} retry call(s)")
    if oc > 3:
        parts.append("WARNING: high call count — review for duplicate calling")
    return " · ".join(parts) if parts else "Single primary OpenAI call"


def _parse_iso_ts(raw: str | None) -> datetime | None:
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _has_recent_row(kind: str, user_id: int, *, seconds: int = 90) -> bool:
    """Skip duplicate ledger rows for the same PDF request."""
    now = datetime.now(timezone.utc)
    for row in _load()[:20]:
        if row.get("kind") != kind:
            continue
        if int(row.get("user_id") or 0) != int(user_id or 0):
            continue
        ts = _parse_iso_ts(row.get("generated_at"))
        if ts and (now - ts).total_seconds() <= seconds:
            return True
    return False


def _merge_report_cache_ledger(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Show PDF saves from report cache when cost ledger has no matching row."""
    try:
        import report_cache as rc

        cache_rows = rc._load_ledger()
    except Exception:
        return rows

    merged = list(rows)
    for cr in cache_rows:
        if not isinstance(cr, dict):
            continue
        kind = str(cr.get("kind") or "").strip()
        if not kind:
            continue
        cr_ts = _parse_iso_ts(cr.get("created_at"))
        cr_uid = int(cr.get("user_id") or 0)
        duplicate = False
        for existing in rows:
            if existing.get("kind") != kind:
                continue
            if int(existing.get("user_id") or 0) != cr_uid:
                continue
            ex_ts = _parse_iso_ts(existing.get("generated_at"))
            if cr_ts and ex_ts and abs((cr_ts - ex_ts).total_seconds()) <= 180:
                duplicate = True
                break
        if duplicate:
            continue
        merged.append(
            {
                "id": str(cr.get("id") or uuid.uuid4().hex[:16])[:16],
                "kind": kind,
                "label": KIND_LABELS.get(kind, cr.get("report_type") or kind.replace("_", " ").title()),
                "user_id": cr_uid,
                "generated_at": cr.get("created_at") or datetime.now(timezone.utc).isoformat(),
                "model": "—",
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cost_inr": 0.0,
                "cost_usd": 0.0,
                "openai_call_count": 0,
                "regen_count": 0,
                "retry_count": 0,
                "extra_calls": 0,
                "report_cache_hit": False,
                "polish_cache_hit": False,
                "openai_skipped": True,
                "force_regenerate": False,
                "render_status": "SUCCESS",
                "final_status": "REPORT_CACHE_ONLY",
                "notes": (
                    "PDF saved on server — token/cost not logged yet. "
                    "Redeploy latest API (pdf-generations route + pdf_generation_log)."
                ),
                "phases": [],
                "size_bytes": int(cr.get("size_bytes") or 0),
                "source": "report_cache_ledger",
            }
        )

    merged.sort(
        key=lambda r: _parse_iso_ts(r.get("generated_at"))
        or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return merged


def record_if_missing(
    *,
    kind: str,
    user_id: int = 0,
    pdf_gen: dict[str, Any] | None = None,
    report_cache_hit: bool = False,
    render_status: str = "SUCCESS",
) -> None:
    """Fallback row when route-level telemetry logging did not run."""
    if _has_recent_row(kind, user_id):
        return
    pg = dict(pdf_gen or {})
    pg.setdefault("final_status", "REPORT_SAVED")
    record_from_telemetry(
        kind=kind,
        user_id=user_id,
        pdf_gen=pg,
        report_cache_hit=report_cache_hit,
        render_status=render_status,
    )


def record_from_telemetry(
    *,
    kind: str,
    user_id: int = 0,
    pdf_gen: dict[str, Any] | None,
    report_cache_hit: bool = False,
    force_regenerate: bool = False,
    render_status: str = "SUCCESS",
) -> None:
    """Append one admin-visible row. Never raises."""
    try:
        pg = dict(pdf_gen or {})
        oc = int(pg.get("openai_call_count") or 0)
        row: dict[str, Any] = {
            "id": uuid.uuid4().hex[:16],
            "kind": kind,
            "label": KIND_LABELS.get(kind, kind.replace("_", " ").title()),
            "user_id": int(user_id or 0),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": pg.get("model") or pg.get("model_requested") or "—",
            "input_tokens": int(pg.get("input_tokens") or 0),
            "output_tokens": int(pg.get("output_tokens") or 0),
            "total_tokens": int(pg.get("total_tokens") or 0),
            "cost_inr": round(float(pg.get("estimated_cost_inr") or 0), 2),
            "cost_usd": round(float(pg.get("estimated_cost_usd") or 0), 4),
            "openai_call_count": oc,
            "regen_count": int(pg.get("regen_count") or 0),
            "retry_count": int(pg.get("retry_count") or 0),
            "extra_calls": max(0, oc - 1),
            "report_cache_hit": bool(report_cache_hit),
            "polish_cache_hit": bool(pg.get("cache_hit")),
            "openai_skipped": bool(pg.get("openai_skipped") or report_cache_hit),
            "force_regenerate": bool(force_regenerate),
            "render_status": render_status,
            "final_status": pg.get("final_status") or ("CACHE" if report_cache_hit else "OK"),
            "notes": _build_notes(pg, report_cache_hit=report_cache_hit),
            "phases": _phase_labels(pg.get("phases") if isinstance(pg.get("phases"), list) else []),
        }
        with _lock:
            rows = _load()
            rows.insert(0, row)
            if len(rows) > _MAX_ROWS:
                rows = rows[:_MAX_ROWS]
            _save(rows)
    except Exception as exc:
        log.warning("[pdf_generation_log] record failed: %s", exc)


def list_generations(
    *,
    page: int = 1,
    per_page: int = 50,
    kind: str | None = None,
) -> dict[str, Any]:
    """Newest-first paginated list for admin."""
    page = max(1, int(page or 1))
    per_page = max(1, min(200, int(per_page or 50)))
    rows = _merge_report_cache_ledger(_load())
    if kind:
        rows = [r for r in rows if r.get("kind") == kind]
    total = len(rows)
    pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    chunk = rows[start : start + per_page]
    return {
        "items": chunk,
        "page": page,
        "pages": pages,
        "total": total,
        "per_page": per_page,
    }

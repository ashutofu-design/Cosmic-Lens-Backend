"""Birth Time Rectification — user intake form → founder/admin queue."""
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

_BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".cache", "birth_time_rectification_orders")
)
_lock = threading.Lock()

ALLOWED_IMPACTS = frozenset({"positive", "negative", "mixed", ""})


def _ensure_dir() -> None:
    try:
        os.makedirs(_BASE, exist_ok=True)
    except Exception:
        pass


def _save_order(record: dict) -> str:
    _ensure_dir()
    oid = record.get("order_id") or str(uuid.uuid4())
    record["order_id"] = oid
    path = os.path.join(_BASE, f"{oid}.json")
    with _lock:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=2)
    try:
        print(
            f"[birth_time_rectification] saved id={oid} "
            f"user={record.get('user_id')} "
            f"events={len(record.get('milestone_events') or [])} "
            f"notes_chars={len(str(record.get('last_15y_events_text') or ''))}",
            flush=True,
        )
    except Exception:
        pass
    return oid


def _load_order(order_id: str) -> dict[str, Any] | None:
    _ensure_dir()
    path = os.path.join(_BASE, f"{order_id}.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def list_birth_time_rectification_orders(
    page: int = 1,
    per_page: int = 50,
    status: str | None = None,
) -> dict[str, Any]:
    _ensure_dir()
    rows: list[dict[str, Any]] = []
    try:
        names = [n for n in os.listdir(_BASE) if n.endswith(".json")]
    except Exception:
        names = []
    for name in names:
        try:
            with open(os.path.join(_BASE, name), "r", encoding="utf-8") as fh:
                rec = json.load(fh)
            if not isinstance(rec, dict):
                continue
            if status and (rec.get("status") or "") != status:
                continue
            events = rec.get("milestone_events") or []
            notes = str(rec.get("last_15y_events_text") or "")
            rows.append(
                {
                    "order_id": rec.get("order_id") or name.replace(".json", ""),
                    "created_at": rec.get("created_at") or "",
                    "user_id": rec.get("user_id"),
                    "cosmo_user_id": rec.get("cosmo_user_id") or "",
                    "full_name": rec.get("full_name") or "",
                    "dob": rec.get("dob") or "",
                    "approx_tob": rec.get("approx_tob") or "",
                    "birth_place": rec.get("birth_place") or "",
                    "event_count": len(events) if isinstance(events, list) else 0,
                    "has_15y_notes": bool(notes.strip()),
                    "status": rec.get("status") or "pending",
                }
            )
        except Exception:
            continue
    rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    total = len(rows)
    page = max(1, int(page or 1))
    per_page = max(1, min(100, int(per_page or 50)))
    pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    return {
        "orders": rows[start : start + per_page],
        "total": total,
        "page": page,
        "pages": pages,
        "per_page": per_page,
    }


def get_birth_time_rectification_order(order_id: str) -> dict[str, Any] | None:
    return _load_order(order_id)


def _clean_events(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw[:20]:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("id") or "").strip()
        if not label:
            continue
        month = str(item.get("month") or "").strip()[:20]
        year = str(item.get("year") or "").strip()[:4]
        month_year = str(item.get("month_year") or "").strip()[:40]
        if not month_year and (month or year):
            month_year = f"{month} {year}".strip()
        impact = str(item.get("impact") or "").strip().lower()
        if impact not in ALLOWED_IMPACTS:
            impact = ""
        out.append(
            {
                "id": str(item.get("id") or "")[:64],
                "label": label[:200],
                "month": month,
                "year": year,
                "month_year": month_year,
                "impact": impact,
            }
        )
    return out


def register_birth_time_rectification_routes(flask_app) -> None:
    """No-op: POST submit is defined in flask_app.py (before catch-all) to avoid 405."""
    try:
        print(
            "[birth_time_rectification] submit route owned by flask_app "
            "(/api/birth-time-rectification/submit)",
            flush=True,
        )
    except Exception:
        pass

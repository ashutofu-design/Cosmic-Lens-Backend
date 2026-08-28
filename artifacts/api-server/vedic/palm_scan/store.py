"""Ephemeral-plus-durable store for admin palm extraction records."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from .validation_gate import evaluate_bilateral, evaluate_hand

_LOCK = Lock()


def _root() -> Path:
    override = os.environ.get("PALM_SCAN_STORE")
    if override:
        path = Path(override)
    else:
        path = Path(__file__).resolve().parents[2] / "data" / "palm_scans"
    path.mkdir(parents=True, exist_ok=True)
    (path / "sessions").mkdir(exist_ok=True)
    return path


def save_hand(
    *,
    session_id: str,
    hand_side: str,
    writing_hand: str | None,
    user_id: str | None,
    result: dict[str, Any],
    person: dict[str, Any] | None = None,
) -> dict[str, Any]:
    session_id = (session_id or result.get("metadata", {}).get("scan_id") or "unknown").strip()
    record = _read_session(session_id) or {
        "session_id": session_id,
        "created_at": _now(),
        "user_id": user_id,
        "writing_hand": writing_hand or "unknown",
        "hands": {},
        "bilateral_comparison": None,
        "verification": {
            "status": "machine_only",
            "machine_result": None,
            "human_verified_result": None,
            "notes": [],
        },
    }
    record["updated_at"] = _now()
    if user_id:
        record["user_id"] = user_id
    if person:
        record["person"] = {**(record.get("person") or {}), **{
            key: value for key, value in person.items() if value
        }}
    if writing_hand in {"left", "right"}:
        record["writing_hand"] = writing_hand
    if hand_side in {"left", "right"}:
        production_validation = result.get("production_validation") if isinstance(result.get("production_validation"), dict) else evaluate_hand(result, required_hand_side=hand_side)
        result["production_validation"] = production_validation
        record["hands"][hand_side] = {
            "scan_id": (result.get("metadata") or {}).get("scan_id"),
            "saved_at": _now(),
            "validation_status": production_validation.get("status"),
            "palm_scan_result": result,
        }
    if record["hands"].get("left") and record["hands"].get("right"):
        from .master_layer import compose_bilateral_comparison

        record["bilateral_comparison"] = compose_bilateral_comparison(
            left=record["hands"]["left"]["palm_scan_result"],
            right=record["hands"]["right"]["palm_scan_result"],
            writing_hand=record.get("writing_hand") or "unknown",
        )
        verification = record.get("verification") or {"status": "machine_only"}
        verification["machine_result"] = {
            "left": record["hands"]["left"]["palm_scan_result"].get("master_extraction"),
            "right": record["hands"]["right"]["palm_scan_result"].get("master_extraction"),
        }
        record["verification"] = verification
        record["production_validation"] = evaluate_bilateral(
            record["hands"]["left"]["palm_scan_result"],
            record["hands"]["right"]["palm_scan_result"],
            writing_hand=record.get("writing_hand") or "unknown",
        )
    _write_session(session_id, record)
    return _public_session(record)


def save_verification(session_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    record = _read_session(session_id)
    if record is None:
        return None
    status = payload.get("status") or "reviewed"
    if status not in {"machine_only", "confirmed", "rejected", "corrected", "ambiguous", "reviewed"}:
        status = "reviewed"
    existing = record.get("verification") or {}
    machine = existing.get("machine_result")
    if machine is None:
        machine = {
            side: (hand.get("palm_scan_result") or {}).get("master_extraction")
            for side, hand in (record.get("hands") or {}).items()
        }
    record["verification"] = {
        "status": status,
        "machine_result": machine,
        "human_verified_result": payload.get("human_verified_result"),
        "notes": payload.get("notes") or [],
        "updated_at": _now(),
        "corrections": payload.get("corrections") or [],
    }
    record["updated_at"] = _now()
    _write_session(session_id, record)
    return _public_session(record)


def get_session(session_id: str) -> dict[str, Any] | None:
    record = _read_session(session_id)
    return _public_session(record) if record else None


def list_sessions(limit: int = 50) -> list[dict[str, Any]]:
    root = _root() / "sessions"
    files = sorted(root.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    out = []
    for path in files[: max(1, min(limit, 200))]:
        record = json.loads(path.read_text(encoding="utf-8"))
        out.append({
            "session_id": record.get("session_id"),
            "user_id": record.get("user_id"),
            "person": record.get("person") or {},
            "writing_hand": record.get("writing_hand"),
            "hands": sorted((record.get("hands") or {}).keys()),
            "updated_at": record.get("updated_at"),
            "verification_status": (record.get("verification") or {}).get("status"),
            "has_bilateral": bool(record.get("bilateral_comparison")),
            "overall_status": ((record.get("production_validation") or {}).get("overall_status")),
        })
    return out


def _read_session(session_id: str) -> dict[str, Any] | None:
    path = _root() / "sessions" / f"{_safe(session_id)}.json"
    if not path.is_file():
        return None
    with _LOCK:
        return json.loads(path.read_text(encoding="utf-8"))


def _write_session(session_id: str, record: dict[str, Any]) -> None:
    path = _root() / "sessions" / f"{_safe(session_id)}.json"
    with _LOCK:
        path.write_text(json.dumps(record, ensure_ascii=False, default=str), encoding="utf-8")


def _public_session(record: dict[str, Any]) -> dict[str, Any]:
    return record


def _safe(value: str) -> str:
    return "".join(ch for ch in value if ch.isalnum() or ch in {"-", "_"})[:80] or "unknown"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

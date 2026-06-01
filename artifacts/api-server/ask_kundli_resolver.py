"""Resolve kundli for /api/ask and /api/ask/stream (RAW passthrough + tamper-safe)."""
from __future__ import annotations

import json
import logging
from typing import Any

log = logging.getLogger(__name__)


def _valid_chart(payload: Any) -> dict | None:
    if not isinstance(payload, dict):
        return None
    planets = payload.get("planets")
    if isinstance(planets, list) and len(planets) > 0:
        return payload
    return None


def _mirror_to_legacy_kundli(user, chart: dict, birth: dict | None = None) -> None:
    """Best-effort: keep user.kundli.chart_data in sync for RAW passthrough."""
    try:
        from datetime import datetime, timezone

        from models import Kundli, db

        kun = user.kundli
        if not kun:
            kun = Kundli(user_id=user.id)
            db.session.add(kun)
        kun.chart_data = json.dumps(chart)
        if birth and isinstance(birth, dict):
            kun.name = (birth.get("name") or kun.name or "")[:200]
            if birth.get("place"):
                kun.pob = str(birth.get("place"))[:500]
            if birth.get("lat") is not None:
                kun.lat = birth.get("lat")
            if birth.get("lon") is not None:
                kun.lon = birth.get("lon")
            if birth.get("tz") is not None:
                kun.tz = birth.get("tz")
        kun.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.session.commit()
    except Exception as exc:
        log.warning("[ask] kundli mirror to DB failed (non-fatal): %s", exc)
        try:
            from models import db

            db.session.rollback()
        except Exception:
            pass


def resolve_kundli_for_user(
    user,
    client_kundli: Any = None,
    birth: Any = None,
):
    """
    Returns (kundli_dict, None) on success.
    Returns (None, (flask_response, status_code)) on failure.
    """
    from flask import jsonify

    chart = None
    if user is not None:
        kun = getattr(user, "kundli", None)
        if kun and getattr(kun, "chart_data", None):
            try:
                chart = _valid_chart(json.loads(kun.chart_data))
            except Exception as exc:
                log.warning("[ask] DB kundli parse failed: %s", exc)

    if chart is None:
        chart = _valid_chart(client_kundli)

    if chart is None:
        return None, (
            jsonify(
                {
                    "error": "kundli_missing",
                    "message": (
                        "Aapki kundli server par save nahi hai. "
                        "Profile me birth details save karke dubara try karein."
                    ),
                }
            ),
            412,
        )

    try:
        from event_timing.marriage.kp_from_chart import ensure_kp_on_kundli

        chart = ensure_kp_on_kundli(
            chart,
            birth if isinstance(birth, dict) else None,
            user,
        )
    except Exception as exc:
        log.warning("[ask] ensure_kp_on_kundli failed (non-fatal): %s", exc)

    if user is not None:
        _mirror_to_legacy_kundli(user, chart, birth if isinstance(birth, dict) else None)

    return chart, None

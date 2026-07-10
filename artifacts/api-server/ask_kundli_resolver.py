"""Resolve kundli for /api/ask and /api/ask/stream (RAW passthrough + tamper-safe)."""
from __future__ import annotations

import json
import logging
from typing import Any

log = logging.getLogger(__name__)

# Romantic partner slots — must NEVER be used as the native chart for Ask.
_PARTNER_RELATIONS = (
    "Husband",
    "Wife",
    "Boyfriend",
    "Girlfriend",
    "Fiance",
    "Fiancee",
    "Partner",
    "Spouse",
)
_PARTNER_RELATIONS_LOWER = {r.lower() for r in _PARTNER_RELATIONS}


def _is_partner_relation(relation: str | None) -> bool:
    if not relation:
        return False
    return relation.strip().lower() in _PARTNER_RELATIONS_LOWER


def _normalize_chart_payload(payload: Any) -> dict | None:
    """Accept flat or nested chart JSON (kundli/chart/chart_data wrappers)."""
    try:
        from ask_llm_context_debug import coerce_chart_for_marriage_engine

        return coerce_chart_for_marriage_engine(payload)
    except Exception:
        pass
    if not isinstance(payload, dict):
        return None
    planets = payload.get("planets")
    if isinstance(planets, list) and len(planets) > 0:
        return payload
    return None


def _valid_chart(payload: Any) -> dict | None:
    return _normalize_chart_payload(payload)


def _birth_from_kundli_row(row) -> dict:
    return {
        "dob": getattr(row, "dob", None),
        "tob": getattr(row, "tob", None),
        "time": getattr(row, "tob", None),
        "lat": getattr(row, "lat", None),
        "lon": getattr(row, "lon", None),
        "tz": getattr(row, "tz", None),
        "place": getattr(row, "pob", None),
    }


def _chart_from_profile_row(prof) -> tuple[dict | None, dict | None]:
    if prof is None or not getattr(prof, "chart_data", None):
        return None, None
    try:
        parsed = json.loads(prof.chart_data)
    except Exception:
        return None, None
    chart = _normalize_chart_payload(parsed)
    if chart is None:
        return None, None
    row_birth: dict | None = None
    if prof.birth_data:
        try:
            bd = json.loads(prof.birth_data)
            if isinstance(bd, dict):
                row_birth = bd
        except Exception:
            pass
    return chart, row_birth


def _pick_native_profile_from_rows(rows) -> Any | None:
    """Prefer is_primary; else newest profile that is not a partner slot."""
    if not rows:
        return None
    for prof in rows:
        if getattr(prof, "is_primary", False) and getattr(prof, "chart_data", None):
            return prof
    ordered = sorted(
        rows,
        key=lambda r: getattr(r, "updated_at", None) or "",
        reverse=True,
    )
    for prof in ordered:
        if not getattr(prof, "chart_data", None):
            continue
        if _is_partner_relation(getattr(prof, "relation", None)):
            continue
        return prof
    return None


def load_native_chart_from_profile(user_id: int) -> tuple[dict | None, dict | None]:
    """Load the user's own (native) chart from Profile — never a partner slot."""
    try:
        from models import Profile

        rows = (
            Profile.query.filter_by(user_id=user_id, deleted_at=None)
            .order_by(Profile.is_primary.desc(), Profile.updated_at.desc())
            .all()
        )
        prof = _pick_native_profile_from_rows(rows)
        if prof is None:
            return None, None
        chart, row_birth = _chart_from_profile_row(prof)
        if chart is not None:
            log.info(
                "[ask] native_profile_chart user_id=%s profile_id=%s "
                "relation=%r is_primary=%s",
                user_id,
                getattr(prof, "id", None),
                getattr(prof, "relation", None),
                bool(getattr(prof, "is_primary", False)),
            )
        return chart, row_birth
    except Exception as exc:
        log.warning("[ask] profile chart load failed: %s", exc)
        return None, None


def _load_chart_from_profile(user_id: int) -> tuple[dict | None, dict | None]:
    """Backward-compatible alias — always resolves native chart only."""
    return load_native_chart_from_profile(user_id)


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

    Native chart priority (Ask always uses primary / self chart):
      1) Primary or non-partner Profile chart
      2) Legacy kundlis row
      3) Client payload (anonymous or missing server chart)
    """
    from flask import jsonify

    chart = None
    profile_birth: dict | None = None
    kundli_source = "client"
    if user is not None:
        chart, profile_birth = load_native_chart_from_profile(user.id)
        if chart is not None:
            kundli_source = "native_profile"
        if chart is None:
            kun = getattr(user, "kundli", None)
            if kun and getattr(kun, "chart_data", None):
                try:
                    chart = _valid_chart(json.loads(kun.chart_data))
                    if chart is not None:
                        kundli_source = "legacy_kundli"
                except Exception as exc:
                    log.warning("[ask] DB kundli parse failed: %s", exc)
        if chart is None:
            try:
                from models import Kundli

                row = Kundli.query.filter_by(user_id=user.id).first()
                if row is not None and row.chart_data:
                    chart = _valid_chart(json.loads(row.chart_data))
                    if chart is not None:
                        kundli_source = "legacy_kundli_row"
                        if not profile_birth:
                            profile_birth = _birth_from_kundli_row(row)
            except Exception as exc:
                log.warning("[ask] kundlis table lookup failed: %s", exc)

    if chart is None:
        chart = _valid_chart(client_kundli)
        if chart is not None:
            kundli_source = "client_payload"

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

    if user is not None:
        log.info("[ask] kundli_source=%s user_id=%s", kundli_source, user.id)

    merged_birth: dict | None = None
    if isinstance(birth, dict):
        merged_birth = dict(birth)
    if profile_birth:
        merged_birth = dict(profile_birth)
        if isinstance(birth, dict):
            for key, val in birth.items():
                if val not in (None, ""):
                    merged_birth[key] = val

    try:
        from event_timing.marriage.kp_from_chart import ensure_kp_on_kundli

        chart = ensure_kp_on_kundli(
            chart,
            merged_birth,
            user,
        )
    except Exception as exc:
        log.warning("[ask] ensure_kp_on_kundli failed (non-fatal): %s", exc)

    if user is not None:
        _mirror_to_legacy_kundli(
            user, chart, merged_birth if isinstance(merged_birth, dict) else None,
        )

    return chart, None

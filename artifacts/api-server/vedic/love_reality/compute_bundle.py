"""Aggregate Love Reality engine outputs for both partners (deterministic)."""
from __future__ import annotations

from typing import Any


def _normalize_birth(p: dict) -> dict:
    out = dict(p or {})
    out.setdefault("name", "Partner")
    out.setdefault("place", "")
    out.setdefault("minute", 0)
    out.setdefault("ampm", "AM")
    # Optional profile gender — used for reader-context PDF framing only (not in ephemeris).
    if out.get("gender") is not None:
        out["gender"] = str(out["gender"]).strip()
    return out


def _json_from_handler(app, route: str, handler, body: dict) -> dict:
    with app.test_request_context(route, method="POST", json=body):
        resp = handler()
        if isinstance(resp, tuple):
            resp = resp[0]
        data = resp.get_json(silent=True) if hasattr(resp, "get_json") else None
        return data if isinstance(data, dict) else {}


def compute_love_reality_bundle(
    app, p1: dict, p2: dict, *, skip_ai_insight: bool = True
) -> dict[str, Any]:
    """
    Run love-compat + breakup + loyalty + will-return + future-outcome for one couple.
    Returns unified facts dict for AI polish + PDF render.

    PDF path sets skip_ai_insight=True so the Pro polish call is the only OpenAI pass.
    """
    del app  # engines call kundli directly — no Flask test_request_context
    from vedic.love_reality.engines import run_all_love_reality_engines

    return run_all_love_reality_engines(
        _normalize_birth(p1),
        _normalize_birth(p2),
        skip_ai_insight=skip_ai_insight,
    )

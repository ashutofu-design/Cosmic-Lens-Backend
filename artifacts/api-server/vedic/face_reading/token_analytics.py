"""
AI cost tracking + token hotspot analytics (Redis-backed).
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

from . import redis_codec as _codec
from . import redis_manager as _rm
from .token_budget import add_report_spend, record_spend as budget_record_spend

log = logging.getLogger(__name__)

_PREFIX = (os.environ.get("FACE_REDIS_PREFIX") or "face").strip().rstrip(":")
_TTL = int(os.environ.get("FACE_ANALYTICS_TTL", str(30 * 24 * 3600)))


def _k(*parts: str) -> str:
    return f"{_PREFIX}:" + ":".join(str(p) for p in parts if p)


def record_call(
    *,
    analysis_id: Optional[str],
    user_id: Optional[int],
    phase: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    usd: float,
    lang: str = "",
    section: str = "",
    retry: int = 0,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Record one OpenAI call with dimensional tags."""
    if usd > 0:
        budget_record_spend(usd, user_id, analysis_id=analysis_id)

    evt = {
        "ts": time.time(),
        "analysis_id": analysis_id,
        "user_id": user_id,
        "phase": phase,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "usd": round(usd, 6),
        "lang": lang,
        "section": section,
        "retry": retry,
        **(extra or {}),
    }
    raw = _codec.dumps(evt)
    day = time.strftime("%Y-%m-%d", time.gmtime())

    if analysis_id:
        _append_list(_k("analytics", "report", analysis_id), raw, 80)
    if user_id:
        _append_list(_k("analytics", "user", str(user_id), day), raw, 200)
    _append_list(_k("analytics", "daily", day), raw, 500)

    # Hotspot counters
    hotspot = f"{phase}:{model}:{section or 'batch'}"
    _incr_float(_k("analytics", "hotspot", day, hotspot), usd)


def record_from_response(
    resp: Any,
    model: str,
    *,
    analysis_id: Optional[str] = None,
    user_id: Optional[int] = None,
    phase: str = "unknown",
    lang: str = "",
    section: str = "",
    retry: int = 0,
) -> float:
    """Parse usage from OpenAI response and record."""
    try:
        from numerology.core import narration_cache as _nc

        in_t = getattr(resp.usage, "prompt_tokens", 0) or 0
        out_t = getattr(resp.usage, "completion_tokens", 0) or 0
        usd = _nc.cost_for(in_t, out_t, model)
        record_call(
            analysis_id=analysis_id,
            user_id=user_id,
            phase=phase,
            model=model,
            input_tokens=in_t,
            output_tokens=out_t,
            usd=usd,
            lang=lang,
            section=section,
            retry=retry,
        )
        try:
            _nc.record_spend(usd)
        except Exception:
            pass
        return usd
    except Exception as exc:
        log.debug("[token_analytics] record_from_response: %s", exc)
        return 0.0


def _append_list(key: str, raw: bytes, max_len: int) -> None:
    client = _rm.get_client()
    if not client:
        return
    try:
        client.lpush(key, raw)
        client.ltrim(key, 0, max_len - 1)
        client.expire(key, _TTL)
    except Exception:
        pass


def _incr_float(key: str, delta: float) -> None:
    if delta <= 0:
        return
    cur = _rm.get_raw(key)
    total = float(_codec.loads(cur) or 0) + delta
    _rm.set_raw(key, _codec.dumps(round(total, 6)), _TTL)


def get_report_cost(analysis_id: str) -> Dict[str, Any]:
    """Aggregate cost + call list for one report."""
    raw_list = _rm.get_client()
    if not raw_list:
        return {"analysis_id": analysis_id, "total_usd": 0.0, "calls": []}
    try:
        key = _k("analytics", "report", analysis_id)
        items = raw_list.lrange(key, 0, 79) or []
    except Exception:
        items = []
    calls: List[Dict[str, Any]] = []
    total = 0.0
    for raw in items:
        if isinstance(raw, bytes):
            evt = _codec.loads(raw)
            if isinstance(evt, dict):
                calls.append(evt)
                total += float(evt.get("usd") or 0)
    return {
        "analysis_id": analysis_id,
        "total_usd": round(total, 6),
        "calls": calls,
        "call_count": len(calls),
    }


def get_daily_hotspots(day: Optional[str] = None, top_n: int = 15) -> List[Dict[str, Any]]:
    """Expensive phase/model/section keys for a day."""
    day = day or time.strftime("%Y-%m-%d", time.gmtime())
    client = _rm.get_client()
    if not client:
        return []
    pattern = _k("analytics", "hotspot", day) + ":*"
    try:
        keys = list(client.scan_iter(match=pattern, count=200))
    except Exception:
        return []
    rows: List[Dict[str, Any]] = []
    prefix = _k("analytics", "hotspot", day) + ":"
    for key in keys:
        k = key.decode() if isinstance(key, bytes) else str(key)
        if not k.startswith(prefix):
            continue
        raw = _rm.get_raw(k)
        usd = float(_codec.loads(raw) or 0) if raw else 0.0
        label = k[len(prefix):]
        rows.append({"hotspot": label, "usd": usd})
    rows.sort(key=lambda x: -x["usd"])
    return rows[:top_n]

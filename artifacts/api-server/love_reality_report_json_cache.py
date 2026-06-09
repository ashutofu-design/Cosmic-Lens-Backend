"""
Full Love Reality Pro JSON response cache (pro-report API).

Reuses polish snapshot on first build; second request skips bundle + LLM entirely.
Storage: .cache/love_report_json/<sha1>.json
"""
from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any

import report_cache as rc

log = logging.getLogger(__name__)

_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".cache", "love_report_json"))
_lock = threading.Lock()


def _ensure_dir() -> None:
    try:
        os.makedirs(_BASE, exist_ok=True)
    except Exception:
        pass


def cache_params(user_id: int, lang: str, p1: dict, p2: dict) -> dict[str, Any]:
    from love_reality_api import love_reality_cache_params

    cp = love_reality_cache_params(lang, p1, p2)
    cp["user_id"] = int(user_id or 0)
    cp["kind"] = "love_reality_pro_report_json"
    return cp


def _path(sid: str) -> str:
    return os.path.join(_BASE, f"{sid}.json")


def load(params: dict[str, Any]) -> dict[str, Any] | None:
    sid = rc._hash_params(params)
    p = _path(sid)
    try:
        if not os.path.isfile(p):
            return None
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict) or not data.get("ok"):
            return None
        return data
    except Exception as exc:
        log.warning("[love_report_json_cache] load failed %s: %s", sid[:12], exc)
        return None


def save(params: dict[str, Any], payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict) or not payload.get("ok"):
        return
    sid = rc._hash_params(params)
    p = _path(sid)
    try:
        _ensure_dir()
        tmp = p + ".tmp"
        with _lock:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, default=str)
            os.replace(tmp, p)
    except Exception as exc:
        log.warning("[love_report_json_cache] save failed %s: %s", sid[:12], exc)

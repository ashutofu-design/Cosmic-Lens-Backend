"""
Persist Love Reality Pro LLM polish per couple — reuse when only PDF layout changes.

Storage: .cache/reports/polish/<sha1>.json
Key: user_id + lang + birth params (NO pdf_layout).
"""
from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any

import report_cache as rc

log = logging.getLogger(__name__)

_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".cache", "love_polish"))
_lock = threading.Lock()


def _ensure_dir() -> None:
    try:
        os.makedirs(_BASE, exist_ok=True)
    except Exception:
        pass


def snapshot_params(user_id: int, lang: str, p1: dict, p2: dict) -> dict[str, Any]:
    from love_reality_api import LOVE_REALITY_HI_CACHE_VER
    from vedic.love_reality.love_section_polish import _ASSEMBLY_VER

    cp = rc.couple_cache_params(lang, p1, p2)
    cp["user_id"] = int(user_id or 0)
    cp["kind"] = "love_reality_pro_polish"
    cp["polish_assembly"] = _ASSEMBLY_VER
    if (lang or "").strip().lower() == "hi":
        cp["hi_cache_ver"] = LOVE_REALITY_HI_CACHE_VER
    return cp


def snapshot_id(params: dict[str, Any]) -> str:
    return rc._hash_params(params)


def _path(sid: str) -> str:
    return os.path.join(_BASE, f"{sid}.json")


def load(params: dict[str, Any]) -> dict[str, Any] | None:
    from vedic.love_reality.love_section_polish import _ASSEMBLY_VER

    sid = snapshot_id(params)
    p = _path(sid)
    try:
        if not os.path.isfile(p):
            return None
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return None
        if (data.get("_meta") or {}).get("assembly") != _ASSEMBLY_VER:
            return None
        from vedic.love_reality.love_section_polish import _assembly_depth_ok

        if not _assembly_depth_ok(data):
            return None
        return data
    except Exception as exc:
        log.warning("[love_polish_snapshot] load failed %s: %s", sid[:12], exc)
        return None


def invalidate(params: dict[str, Any]) -> None:
    sid = snapshot_id(params)
    p = _path(sid)
    try:
        if os.path.isfile(p):
            os.remove(p)
    except Exception as exc:
        log.warning("[love_polish_snapshot] invalidate failed %s: %s", sid[:12], exc)


def purge_all_hi_snapshots() -> int:
    """Delete polish snapshots that look like Hindi LLM output (Devanagari-heavy)."""
    import re

    removed = 0
    deva = re.compile(r"[\u0900-\u097F]")
    try:
        _ensure_dir()
        for name in os.listdir(_BASE):
            if not name.endswith(".json"):
                continue
            path = os.path.join(_BASE, name)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    raw = fh.read(12000)
                if len(deva.findall(raw)) < 24:
                    continue
                os.remove(path)
                removed += 1
            except Exception:
                continue
    except Exception as exc:
        log.warning("[love_polish_snapshot] purge_all_hi_snapshots failed: %s", exc)
    return removed


def save(params: dict[str, Any], pro_premium: dict[str, Any]) -> None:
    if not isinstance(pro_premium, dict) or not pro_premium:
        return
    from vedic.love_reality.love_section_polish import _assembly_depth_ok

    if not _assembly_depth_ok(pro_premium):
        log.warning("[love_polish_snapshot] skip save — partial assembly (missing chapters)")
        return
    sid = snapshot_id(params)
    p = _path(sid)
    try:
        _ensure_dir()
        tmp = p + ".tmp"
        with _lock:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(pro_premium, fh, ensure_ascii=False, default=str)
            os.replace(tmp, p)
    except Exception as exc:
        log.warning("[love_polish_snapshot] save failed %s: %s", sid[:12], exc)

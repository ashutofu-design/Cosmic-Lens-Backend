"""
File-based narration cache + daily spend tracker for the AI narrator.

Two responsibilities:
  1. Cache narrations keyed by (name + dob + lang + section + facts + version)
     so repeated PDF renders for the same person serve from disk (~free).
  2. Track daily OpenAI spend and enforce hard caps per-report and per-day.
     Prevents runaway bills if the model goes haywire or someone hammers the
     endpoint.

Storage layout:
  .cache/narrations/<sha1[:2]>/<sha1>.json     # one file per cached narration
  .cache/narrations/_spend.json                # daily spend ledger

Safety: never raises — any IO error → cache miss / no-throttle fallback.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Optional

PROMPT_VERSION = "v3-grouped-mini"  # bump when prompts/voice change

# ── Tunables (env-overridable) ────────────────────────────────────────────
DAILY_LIMIT_USD     = float(os.environ.get("OPENAI_DAILY_CAP_USD", "3.00"))
PER_REPORT_LIMIT_USD = float(os.environ.get("OPENAI_PER_REPORT_CAP_USD", "0.10"))
CACHE_TTL_DAYS      = int(os.environ.get("NARRATION_CACHE_TTL_DAYS", "30"))

# gpt-4.1-mini pricing (USD per 1M tokens) — Apr 2026
MINI_IN_PER_M  = 0.40
MINI_OUT_PER_M = 1.60

_BASE = os.path.join(os.path.dirname(__file__), "..", "..", ".cache", "narrations")
_BASE = os.path.abspath(_BASE)
_SPEND_FILE = os.path.join(_BASE, "_spend.json")
_lock = threading.Lock()


def _ensure_dir(path: str) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass


def _hash_key(name: str, dob: str, lang: str, section_key: str,
              facts: dict) -> str:
    """Deterministic SHA1 of all inputs that affect output."""
    payload = json.dumps({
        "v": PROMPT_VERSION,
        "name": (name or "").strip().lower(),
        "dob": (dob or "").strip(),
        "lang": (lang or "hinglish").strip().lower(),
        "section_key": section_key,
        "facts": facts or {},
    }, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _path_for(h: str) -> str:
    return os.path.join(_BASE, h[:2], f"{h}.json")


# ── Cache get/set ─────────────────────────────────────────────────────────
def get(name: str, dob: str, lang: str, section_key: str, facts: dict) -> Optional[str]:
    """Return cached narration text or None on miss/expiry/error."""
    try:
        h = _hash_key(name, dob, lang, section_key, facts)
        p = _path_for(h)
        if not os.path.exists(p):
            return None
        st = os.stat(p)
        age_days = (time.time() - st.st_mtime) / 86400.0
        if age_days > CACHE_TTL_DAYS:
            return None
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("text") or None
    except Exception:
        return None


def put(name: str, dob: str, lang: str, section_key: str, facts: dict,
        text: str) -> None:
    """Persist narration to disk. No-op on any IO error."""
    if not text:
        return
    try:
        h = _hash_key(name, dob, lang, section_key, facts)
        p = _path_for(h)
        _ensure_dir(os.path.dirname(p))
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({
                "text": text,
                "section_key": section_key,
                "lang": lang,
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }, fh, ensure_ascii=False)
        os.replace(tmp, p)
    except Exception:
        pass


# ── Spend ledger ──────────────────────────────────────────────────────────
def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load_spend() -> dict:
    try:
        with open(_SPEND_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _save_spend(d: dict) -> None:
    try:
        _ensure_dir(_BASE)
        tmp = _SPEND_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(d, fh)
        os.replace(tmp, _SPEND_FILE)
    except Exception:
        pass


def cost_for(in_tokens: int, out_tokens: int) -> float:
    """Compute USD cost for a gpt-4.1-mini call."""
    return (in_tokens / 1_000_000.0) * MINI_IN_PER_M \
         + (out_tokens / 1_000_000.0) * MINI_OUT_PER_M


def today_spend_usd() -> float:
    with _lock:
        d = _load_spend()
        return float(d.get(_today_str(), 0.0))


def record_spend(usd: float) -> None:
    """Add to today's running total. Thread-safe."""
    if usd <= 0:
        return
    with _lock:
        d = _load_spend()
        key = _today_str()
        d[key] = round(float(d.get(key, 0.0)) + usd, 6)
        # Keep only last 60 days to stop file growing forever
        cutoff = (datetime.now(timezone.utc).date()).isoformat()
        for k in list(d.keys()):
            try:
                # Drop entries older than 60 days
                from datetime import date as _date
                kd = _date.fromisoformat(k)
                if (datetime.now(timezone.utc).date() - kd).days > 60:
                    del d[k]
            except Exception:
                continue
        _save_spend(d)


def is_daily_capped() -> bool:
    """True if today's spend has hit the hard daily cap."""
    return today_spend_usd() >= DAILY_LIMIT_USD


def remaining_daily_usd() -> float:
    return max(0.0, DAILY_LIMIT_USD - today_spend_usd())

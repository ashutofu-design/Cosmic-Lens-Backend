#!/usr/bin/env python3
"""Single-process Telegram poller — run via PM2, not inside gunicorn workers."""
from __future__ import annotations

import os
import sys
import traceback

# Standalone poller — loads .env then calls _poll_loop() directly (not via gunicorn).
os.environ.setdefault("TELEGRAM_USE_POLLING", "1")
os.environ.setdefault("TELEGRAM_POLL_FROM_API", "0")

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_PATH = os.path.join(_SCRIPT_DIR, ".env")


def _load_env_file(path: str) -> None:
    """Load .env without requiring python-dotenv (PM2 does not source .env)."""
    try:
        with open(path, encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                if not key:
                    continue
                if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
                    val = val[1:-1]
                os.environ[key] = val
    except OSError as exc:
        print(f"[lr_telegram] .env read failed ({path}): {exc}", file=sys.stderr, flush=True)


if os.path.isfile(_ENV_PATH):
    try:
        from dotenv import load_dotenv

        load_dotenv(_ENV_PATH, override=True)
        print(f"[lr_telegram] loaded .env via dotenv ({_ENV_PATH})", flush=True)
    except ImportError:
        _load_env_file(_ENV_PATH)
        print(f"[lr_telegram] loaded .env manually ({_ENV_PATH})", flush=True)
else:
    print(f"[lr_telegram] WARNING: .env not found at {_ENV_PATH}", file=sys.stderr, flush=True)

# Ensure imports resolve when PM2 cwd is repo root.
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")


def main() -> int:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    founder = (os.environ.get("TELEGRAM_FOUNDER_CHAT_ID") or "").strip()
    if not token or not founder:
        print(
            "[lr_telegram] poller exit — set TELEGRAM_BOT_TOKEN + "
            "TELEGRAM_FOUNDER_CHAT_ID in artifacts/api-server/.env",
            file=sys.stderr,
            flush=True,
        )
        return 1
    print(
        f"[lr_telegram] env ok token=...{token[-6:]} founder={founder}",
        flush=True,
    )
    try:
        from love_reality_telegram_deliver import _poll_loop
    except Exception:
        print("[lr_telegram] import failed:", file=sys.stderr, flush=True)
        traceback.print_exc()
        return 1
    print("[lr_telegram] standalone poller starting", flush=True)
    try:
        _poll_loop()
    except Exception:
        print("[lr_telegram] poll loop crashed:", file=sys.stderr, flush=True)
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

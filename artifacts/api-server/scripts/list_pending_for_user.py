#!/usr/bin/env python3
"""List founder-queue pending orders for one user (My Reports backfill helper).

Usage (on VPS or laptop api-server folder):
  python scripts/list_pending_for_user.py 42
  python scripts/list_pending_for_user.py COSMO42

Prints JSON rows that /api/my-reports will return under "pending"
after the my-reports pending deploy.
"""
from __future__ import annotations

import json
import re
import sys
from typing import Any


def _resolve_user_id(raw: str) -> int:
    s = (raw or "").strip()
    if not s:
        raise SystemExit("usage: python scripts/list_pending_for_user.py <user_id|COSMO123>")
    m = re.match(r"^COSMO(\d+)$", s, re.I)
    if m:
        return int(m.group(1))
    try:
        return int(s)
    except ValueError as exc:
        raise SystemExit(f"invalid user id: {raw}") from exc


def _safe_list(mod_name: str, user_id: int) -> list[dict[str, Any]]:
    try:
        mod = __import__(mod_name)
        fn = getattr(mod, "list_pending_for_user", None)
        if not callable(fn):
            return []
        rows = fn(user_id)
        return rows if isinstance(rows, list) else []
    except Exception as exc:
        print(f"[warn] {mod_name}: {exc}", file=sys.stderr)
        return []


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python scripts/list_pending_for_user.py <user_id|COSMO123>")
    uid = _resolve_user_id(sys.argv[1])
    sources = (
        "palmistry_human_orders",
        "numerology_human_orders",
        "love_reality_human_orders",
        "milan_human_orders",
        "astrovastu_human_orders",
        "business_vastu_human_orders",
    )
    pending: list[dict[str, Any]] = []
    for name in sources:
        rows = _safe_list(name, uid)
        if rows:
            print(f"[ok] {name}: {len(rows)}", file=sys.stderr)
        pending.extend(rows)

    print(json.dumps({"user_id": uid, "pending_count": len(pending), "pending": pending}, indent=2, ensure_ascii=False))
    if not pending:
        print(
            "\nNo pending rows for this user. Check: order user_id, status != delivered, and .cache/*_human_orders on this machine.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()

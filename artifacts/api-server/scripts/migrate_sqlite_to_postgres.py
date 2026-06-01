"""
One-shot SQLite → PostgreSQL migration for Cosmic Lens.

Reads rows from the SQLite DB used by local dev and inserts into Postgres,
preserving primary keys where possible.

Usage (Windows PowerShell):
  cd artifacts/api-server
  .\.venv\Scripts\Activate.ps1
  $env:SQLITE_URL="sqlite:///path/to/cosmic_lens.db"
  $env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/cosmiclens"
  python scripts/migrate_sqlite_to_postgres.py

Notes:
  - This is best-effort and idempotent-ish: it skips tables that don't exist
    and ignores duplicate-key insert failures (prints a warning).
  - It does NOT drop tables in Postgres.
"""

from __future__ import annotations

import os
import sys
from typing import Iterable, List

from sqlalchemy import Boolean, create_engine, inspect, text
from sqlalchemy.exc import IntegrityError


DEFAULT_TABLES = [
    "users",
    "kundlis",
    "profiles",
    "otp_requests",
    "user_questions",
    "kundli_cache",
    "kundli_milan_cache",
    "daily_transit_cache",
    "astrovastu_basic_logs",
    "astrovastu_pro_logs",
    "business_vastu_logs",
    "astrovastu_purchases",
    "astrovastu_property_unlocks",
    "couple_report_purchases",
    "face_reading_logs",
    "user_facts",
    "user_behavior",
    "user_personality",
]


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _table_cols(engine, table: str) -> List[str]:
    insp = inspect(engine)
    return [c["name"] for c in insp.get_columns(table)]


def _fetch_rows(src_engine, table: str, cols: List[str]) -> Iterable[dict]:
    col_sql = ", ".join(f'"{c}"' for c in cols)
    with src_engine.connect() as conn:
        res = conn.execute(text(f'SELECT {col_sql} FROM "{table}"'))
        for row in res.mappings():
            yield dict(row)


def _bool_cols(engine, table: str) -> set[str]:
    bools: set[str] = set()
    for col in inspect(engine).get_columns(table):
        if isinstance(col["type"], Boolean):
            bools.add(col["name"])
    return bools


def _coerce_row(row: dict, bool_cols: set[str]) -> dict:
    out = dict(row)
    for name in bool_cols:
        if name not in out:
            continue
        val = out[name]
        if val is None or isinstance(val, bool):
            continue
        out[name] = bool(int(val))
    return out


def _insert_rows(dst_engine, table: str, cols: List[str], rows: Iterable[dict]) -> int:
    if not cols:
        return 0
    bool_cols = _bool_cols(dst_engine, table)
    col_sql = ", ".join(f'"{c}"' for c in cols)
    val_sql = ", ".join(f":{c}" for c in cols)
    stmt = text(f'INSERT INTO "{table}" ({col_sql}) VALUES ({val_sql})')
    inserted = 0
    with dst_engine.begin() as conn:
        for r in rows:
            try:
                conn.execute(stmt, _coerce_row(r, bool_cols))
                inserted += 1
            except IntegrityError:
                # Duplicate PK / unique key — skip
                continue
    return inserted


def main() -> int:
    sqlite_url = _env("SQLITE_URL")
    pg_url = _env("DATABASE_URL")

    if not pg_url:
        print("ERROR: DATABASE_URL not set (target Postgres).", file=sys.stderr)
        return 2
    if not sqlite_url:
        # Try default sqlite path used by database.py
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sqlite_url = f"sqlite:///{os.path.join(base_dir, 'cosmic_lens.db')}"

    if pg_url.startswith("postgres://"):
        pg_url = pg_url.replace("postgres://", "postgresql://", 1)

    print("[migrate] src =", sqlite_url)
    print("[migrate] dst =", pg_url.split("@")[-1])  # redact creds

    src = create_engine(sqlite_url)
    dst = create_engine(pg_url)

    src_tables = set(inspect(src).get_table_names())
    dst_tables = set(inspect(dst).get_table_names())

    migrated_total = 0
    for table in DEFAULT_TABLES:
        if table not in src_tables:
            print(f"[migrate] skip {table}: missing in sqlite")
            continue
        if table not in dst_tables:
            print(f"[migrate] skip {table}: missing in postgres (run backend once to create)")
            continue

        src_cols = _table_cols(src, table)
        dst_cols = _table_cols(dst, table)
        cols = [c for c in src_cols if c in dst_cols]
        if not cols:
            print(f"[migrate] skip {table}: no shared columns")
            continue

        n = _insert_rows(dst, table, cols, _fetch_rows(src, table, cols))
        migrated_total += n
        print(f"[migrate] {table}: inserted {n}")

    print("[migrate] done inserted_total =", migrated_total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


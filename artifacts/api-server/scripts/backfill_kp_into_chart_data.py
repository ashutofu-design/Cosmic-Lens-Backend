"""
backfill_kp_into_chart_data.py
==============================
Phase 2.8.57 — One-time backfill: add `kp` key (cusps + planet sub-lord chain)
to every existing kundlis.chart_data and profiles.chart_data row that lacks it.

Run:
    python3 scripts/backfill_kp_into_chart_data.py            # dry-run summary
    python3 scripts/backfill_kp_into_chart_data.py --apply    # actually write

Strategy:
  - Each row's chart_data already has dob/time + the row itself has lat/lon/tz.
  - We rebuild the 9-field kp_engine input dict and call calculate_kp.
  - Skip rows that already have a `kp` key (idempotent).
  - On any per-row failure, log and continue (other rows still get backfilled).
"""
from __future__ import annotations
import os
import sys
import json
import re
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
import psycopg2.extras

from kp_engine import calculate_kp


_MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"])}


def _parse_dob(dob_str: str):
    """Return (day, month, year) from messy dob strings.
    Handles: '29 Oct 1999', '29/10/1999', '1999-10-29', '29-10-1999'."""
    if not dob_str:
        return None
    s = dob_str.strip()
    # ISO 'YYYY-MM-DD'
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        y, mo, d = m.groups()
        return int(d), int(mo), int(y)
    # 'DD/MM/YYYY' or 'DD-MM-YYYY'
    m = re.match(r"^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})$", s)
    if m:
        d, mo, y = m.groups()
        return int(d), int(mo), int(y)
    # 'DD Mon YYYY' (e.g. '29 Oct 1999')
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$", s)
    if m:
        d, mon, y = m.groups()
        mo = _MONTHS.get(mon[:3].lower())
        if mo:
            return int(d), mo, int(y)
    return None


def _parse_tob(tob_str: str):
    """Return (hour, minute, ampm) from time string.
    Handles: '11:30 AM', '11:30', '11:30:00'."""
    if not tob_str:
        return None
    s = tob_str.strip().upper()
    m = re.match(r"^(\d{1,2}):(\d{2})(?::\d{2})?\s*(AM|PM)?$", s)
    if not m:
        return None
    h, mi, ap = m.groups()
    h, mi = int(h), int(mi)
    if not ap:
        # 24h -> convert to 12h + ampm
        if h == 0:
            return 12, mi, "AM"
        elif h < 12:
            return h, mi, "AM"
        elif h == 12:
            return 12, mi, "PM"
        else:
            return h - 12, mi, "PM"
    return h, mi, ap


def _build_kp_input(dob, tob, lat, lon, tz, chart_data: dict):
    """Build the 9-field kp_engine input dict from row fields + chart_data fallbacks."""
    parsed_dob = _parse_dob(dob) if dob else None
    parsed_tob = _parse_tob(tob) if tob else None
    # Chart_data fallback
    if not parsed_dob and isinstance(chart_data, dict):
        parsed_dob = _parse_dob(chart_data.get("dob") or "")
    if not parsed_tob and isinstance(chart_data, dict):
        parsed_tob = _parse_tob(chart_data.get("time") or "")
    if not parsed_dob or not parsed_tob:
        return None
    if lat is None or lon is None or tz is None:
        return None
    d, mo, y = parsed_dob
    h, mi, ap = parsed_tob
    return {
        "day": d, "month": mo, "year": y,
        "hour": h, "minute": mi, "ampm": ap,
        "lat": float(lat), "lon": float(lon), "tz": float(tz),
    }


def _process_table(cur, table: str, id_col: str, lat_col: str, lon_col: str,
                   tz_col: str, dob_col: str, tob_col: str, apply: bool):
    """Generic backfill loop for a table holding chart_data."""
    cur.execute(f"""
        SELECT {id_col}, {dob_col}, {tob_col}, {lat_col}, {lon_col}, {tz_col}, chart_data
        FROM {table}
        WHERE chart_data IS NOT NULL
    """)
    rows = cur.fetchall()
    stats = {"total": len(rows), "already_has_kp": 0, "skipped_bad_birth": 0,
             "kp_failed": 0, "backfilled": 0}
    print(f"\n[{table}] scanning {len(rows)} rows with chart_data...")

    for row in rows:
        rid, dob, tob, lat, lon, tz, cd_raw = row
        try:
            cd = json.loads(cd_raw) if isinstance(cd_raw, str) else cd_raw
        except Exception:
            stats["skipped_bad_birth"] += 1
            continue
        if not isinstance(cd, dict):
            stats["skipped_bad_birth"] += 1
            continue
        if cd.get("kp"):
            stats["already_has_kp"] += 1
            continue

        kp_input = _build_kp_input(dob, tob, lat, lon, tz, cd)
        if not kp_input:
            stats["skipped_bad_birth"] += 1
            print(f"  [{table}.{rid}] SKIP: cannot parse birth (dob={dob!r} tob={tob!r} lat={lat} lon={lon} tz={tz})")
            continue

        try:
            kp = calculate_kp(kp_input)
        except Exception as exc:
            stats["kp_failed"] += 1
            print(f"  [{table}.{rid}] FAIL: calculate_kp raised: {exc}")
            continue

        cd["kp"] = kp
        new_json = json.dumps(cd, default=str)

        if apply:
            cur.execute(f"UPDATE {table} SET chart_data = %s WHERE {id_col} = %s",
                        (new_json, rid))
            stats["backfilled"] += 1
        else:
            stats["backfilled"] += 1   # would-be-backfilled count
            print(f"  [{table}.{rid}] DRY-RUN: would inject KP "
                  f"(cusps={len(kp.get('cusps') or [])} planets={len(kp.get('planets') or [])})")

    print(f"[{table}] stats: {stats}")
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="Actually write to DB. Default is dry-run.")
    args = ap.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit("DATABASE_URL not set")

    print(f"Mode: {'APPLY (writing to DB)' if args.apply else 'DRY-RUN (no writes)'}")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # kundlis table: id, dob, tob, pob, lat, lon, tz, chart_data
    s1 = _process_table(cur, "kundlis", "id", "lat", "lon", "tz",
                        "dob", "tob", apply=args.apply)

    # profiles table: id, birth_data (JSON), chart_data — birth fields nested in birth_data
    cur.execute("""SELECT id, birth_data, chart_data FROM profiles
                   WHERE chart_data IS NOT NULL""")
    rows = cur.fetchall()
    s2 = {"total": len(rows), "already_has_kp": 0, "skipped_bad_birth": 0,
          "kp_failed": 0, "backfilled": 0}
    print(f"\n[profiles] scanning {len(rows)} rows with chart_data...")
    for rid, bd_raw, cd_raw in rows:
        try:
            cd = json.loads(cd_raw) if isinstance(cd_raw, str) else cd_raw
            bd = json.loads(bd_raw) if isinstance(bd_raw, str) else (bd_raw or {})
        except Exception:
            s2["skipped_bad_birth"] += 1
            continue
        if not isinstance(cd, dict):
            s2["skipped_bad_birth"] += 1
            continue
        if cd.get("kp"):
            s2["already_has_kp"] += 1
            continue
        # birth_data shape: {day, month, year, hour, minute, ampm, lat, lon, tz, ...}
        if isinstance(bd, dict) and all(k in bd for k in
                                        ("day", "month", "year", "hour", "minute",
                                         "ampm", "lat", "lon", "tz")):
            kp_input = {k: bd[k] for k in ("day", "month", "year", "hour", "minute",
                                            "ampm", "lat", "lon", "tz")}
        else:
            s2["skipped_bad_birth"] += 1
            print(f"  [profiles.{rid}] SKIP: birth_data missing required keys")
            continue
        try:
            kp = calculate_kp(kp_input)
        except Exception as exc:
            s2["kp_failed"] += 1
            print(f"  [profiles.{rid}] FAIL: {exc}")
            continue
        cd["kp"] = kp
        if args.apply:
            cur.execute("UPDATE profiles SET chart_data = %s WHERE id = %s",
                        (json.dumps(cd, default=str), rid))
        s2["backfilled"] += 1
    print(f"[profiles] stats: {s2}")

    if args.apply:
        conn.commit()
        print("\nCOMMITTED.")
    else:
        print("\nDRY-RUN complete. Re-run with --apply to write.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()

"""Debug marriage engine for user 1 — run: python scripts/debug_marriage_user1.py"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

OUT = ROOT / "scripts" / "_marriage_debug_out.txt"


def main() -> None:
    lines: list[str] = []

    def log(msg: str) -> None:
        lines.append(msg)
        print(msg, flush=True)

    # Try DB user 1
    kundli = None
    birth = None
    try:
        from flask_app import app, User  # noqa: F401

        with app.app_context():
            u = User.query.get(1)
            if u and u.kundli:
                kd = u.kundli.chart_data
                if isinstance(kd, str):
                    kd = json.loads(kd)
                kundli = kd
                birth = {
                    "dob": getattr(u, "dob", None) or (kd or {}).get("dob"),
                    "gender": getattr(u, "gender", None),
                }
                log(f"DB user1: {getattr(u, 'name', '?')} dob={birth.get('dob')}")
    except Exception as exc:
        log(f"DB skip: {exc}")

    # Fallback: test chart (Dhanu, Mercury 7L 12H — late, BCP 31 @ age 26)
    if not kundli or not kundli.get("planets"):
        log("Using test KUNDLI (Dhanu lagna)")
        SIGNS = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        ]
        idx = {
            "Mesh": 0, "Vrishabh": 1, "Mithun": 2, "Kark": 3, "Simha": 4,
            "Kanya": 5, "Tula": 6, "Vrishchik": 7, "Dhanu": 8, "Makar": 9,
            "Kumbh": 10, "Meen": 11,
        }
        planets = []
        for name, sign, house in [
            ("Sun", "Tula", 11), ("Moon", "Mithun", 7), ("Mars", "Dhanu", 1),
            ("Mercury", "Vrishchik", 12), ("Jupiter", "Mesh", 5),
            ("Venus", "Simha", 9), ("Saturn", "Mesh", 5),
            ("Rahu", "Kark", 8), ("Ketu", "Makar", 2),
        ]:
            si = idx[sign]
            planets.append({"name": name, "sign": SIGNS[si], "house": house})
        kundli = {"ascendant": "Sagittarius", "planets": planets}
        birth = {"dob": "26/11/1999", "gender": "male"}

    from event_timing.marriage import assess_marriage
    from event_timing.marriage.kp_from_chart import resolve_kp

    kp = resolve_kp(kundli, {}, birth)
    result = assess_marriage(kundli, {}, kp, birth, question="mera shaadi kab hoga")

    log(f"primary_window={result.get('primary_window')!r}")
    log(f"backup_window={result.get('backup_window')!r}")
    s0 = result.get("step0") or {}
    s0a = result.get("step0a") or {}
    dsp = s0a.get("dasha_scan_plan") or s0.get("dasha_scan_plan") or {}
    log(f"primary_reference_age={dsp.get('primary_reference_age')}")
    log(f"bcp_focus_ages={dsp.get('bcp_focus_ages')}")
    log(f"step0_verdict={(s0.get('step0_tendency') or {}).get('verdict')}")
    log(f"user_age={s0.get('user_age')}")
    log(f"key_trigger={result.get('key_trigger')}")
    log(
        "final_transit="
        f"{result.get('final_transit_support')} "
        f"double={result.get('final_double_transit')} "
        f"detail={result.get('final_transit_detail')}"
    )
    for f in (result.get("factors") or [])[-25:]:
        if "BCP" in f or "ANCHOR" in f or "STEP0" in f or "AGE" in f:
            log(f"  {f}")
    top3 = result.get("top_3_windows") or []
    for i, w in enumerate(top3[:3]):
        log(
            f"top3[{i}]: {w.get('window')} "
            f"md={w.get('md')} ad={w.get('ad')} pd={w.get('pd')} "
            f"score={w.get('score')} bcp={w.get('bcp_age_hits')} "
            f"transit={w.get('transit_confirmed')} dt={w.get('dt')} "
            f"detail={w.get('dt_detail')}"
        )
        log(f"  dasha_score_detail={w.get('dasha_score_detail')}")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    log(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

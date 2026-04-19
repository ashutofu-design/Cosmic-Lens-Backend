"""
Sprint 38 / Phase M — Sahams extension.
Phase J already implements 30 Sahams (M1+M2+M3 + 21 from M4 covered).
This module adds 25 more classical sahams to reach ~55 total in LF.

Reuses _planet_lon_in helper + compute pattern from varshaphala.py.
"""
from __future__ import annotations
from typing import Any, Optional

from .varshaphala import (SIGN_NAMES, SIGN_LORD, _planet_lon_in,
                            _parse_dob, find_solar_return)
from datetime import datetime

# Additional 25 sahams (no overlap with the 30 in varshaphala.SAHAM_DEFS).
SAHAM_EXT_DEFS = [
    # (name, day_formula, night_formula, meaning)
    ("Bhagya",       ("Moon","Sun","Lagna"),       ("Sun","Moon","Lagna"),       "Fortune, divine grace"),
    ("Bhagya-Lord",  ("9th-lord","9th-cusp","Lagna"),("9th-cusp","9th-lord","Lagna"),"Fortune-trigger via dharma"),
    ("Asha",         ("Mars","Saturn","Lagna"),    ("Saturn","Mars","Lagna"),    "Hope, expectation"),
    ("Jaya",         ("Jupiter","Mars","Lagna"),   ("Mars","Jupiter","Lagna"),   "Victory in conflict"),
    ("Soka",         ("Saturn","Moon","Lagna"),    ("Moon","Saturn","Lagna"),    "Sorrow, grief"),
    ("Gnyana",       ("Mercury","Jupiter","Lagna"),("Jupiter","Mercury","Lagna"),"Wisdom, knowledge"),
    ("Pravasa",      ("9th-cusp","Moon","Lagna"),  ("Moon","9th-cusp","Lagna"),  "Travel abroad"),
    ("Aishwarya",    ("Sun","Saturn","Lagna"),     ("Saturn","Sun","Lagna"),     "Lordship, dominion"),
    ("Saubhagya",    ("Venus","Moon","Lagna"),     ("Moon","Venus","Lagna"),     "Marital bliss, beauty"),
    ("Tata",         ("Saturn","Sun","Lagna"),     ("Sun","Saturn","Lagna"),     "Father (Tajik variant)"),
    ("Ari",          ("Saturn","Mars","Lagna"),    ("Mars","Saturn","Lagna"),    "Enemy, opposition"),
    ("Apamrityu",    ("8th-cusp","Saturn","Lagna"),("Saturn","8th-cusp","Lagna"),"Sudden / accidental death"),
    ("Vyapara",      ("Mercury","Mars","Lagna"),   ("Mars","Mercury","Lagna"),   "Business, commerce"),
    ("Manasa",       ("Moon","Mercury","Lagna"),   ("Mercury","Moon","Lagna"),   "Mind, mental state"),
    ("Daiva",        ("Jupiter","Saturn","Lagna"), ("Saturn","Jupiter","Lagna"), "Destiny, divine plan"),
    ("Brahma",       ("Jupiter","Sun","Lagna"),    ("Sun","Jupiter","Lagna"),    "Creative force, dharma"),
    ("Vairagya",     ("Saturn","Jupiter","Lagna"), ("Jupiter","Saturn","Lagna"), "Renunciation, detachment"),
    ("Vahana",       ("4th-lord","4th-cusp","Lagna"),("4th-cusp","4th-lord","Lagna"),"Vehicles, conveyances"),
    ("Pasu",         ("4th-cusp","Moon","Lagna"),  ("Moon","4th-cusp","Lagna"),  "Cattle, livestock, assets"),
    ("Sammoha",      ("Mercury","Rahu","Lagna"),   ("Rahu","Mercury","Lagna"),   "Delusion, confusion"),
    ("Indrayudha",   ("Sun","Jupiter","Lagna"),    ("Jupiter","Sun","Lagna"),    "Rainbow / divine protection"),
    ("Putrajeeva",   ("5th-cusp","Jupiter","Lagna"),("Jupiter","5th-cusp","Lagna"),"Child's vitality"),
    ("Bhratru-vyapara",("3rd-cusp","Mars","Lagna"),("Mars","3rd-cusp","Lagna"), "Sibling business / partnership"),
    ("Kuhu",         ("Sun","Moon","Lagna"),       ("Moon","Sun","Lagna"),       "New-moon / eclipse trigger"),
    ("Jala-patana",  ("Saturn","Mercury","Lagna"), ("Mercury","Saturn","Lagna"), "Drowning / water-accident risk"),
]


def compute_sahams_extended(planets: list[dict], lagna_lon: float,
                              is_day_birth: bool) -> list[dict]:
    """Compute the 25 additional sahams, exact same calc style as Phase J."""
    plon = {p["name"]: p["longitude"] for p in planets
            if isinstance(p.get("longitude"), (int, float))}
    cached: dict[str, float] = {}
    out = []
    for name, day_f, night_f, meaning in SAHAM_EXT_DEFS:
        f = day_f if is_day_birth else night_f
        a_n, b_n, c_n = f
        def resolve(x):
            if x in cached: return cached[x]
            return _planet_lon_in(plon, x, lagna_lon)
        a, b, c = resolve(a_n), resolve(b_n), resolve(c_n)
        if a is None or b is None or c is None: continue
        s = (a - b + c) % 360
        cached[name] = s
        si = int(s // 30)
        out.append({
            "name": name, "meaning": meaning,
            "longitude": round(s, 2),
            "sign": SIGN_NAMES[si],
            "deg_in_sign": round(s % 30, 2),
            "lord": SIGN_LORD[si],
        })
    return out


def compute_phase_m_extra(kundli: dict, birth: dict) -> dict[str, Any]:
    dob = birth.get("dob") or birth.get("date") or kundli.get("dob")
    btime = birth.get("time") or kundli.get("time") or "12:00"
    if not isinstance(dob, str):
        return {"available": False, "reason": "dob missing"}
    birth_dt = _parse_dob(dob, btime)
    if not birth_dt:
        return {"available": False, "reason": "dob parse failed"}
    # Use VS planets if Phase-J Sun-return succeeded; else natal
    sr = find_solar_return(birth_dt)
    if sr.get("available"):
        src_planets = sr["vs_planets"]
    else:
        src_planets = kundli.get("planets") or []
    lagna_sign = kundli.get("ascendant") or kundli.get("lagna")
    lagna_si = (SIGN_NAMES.index(lagna_sign)
                if isinstance(lagna_sign, str) and lagna_sign in SIGN_NAMES
                else 0)
    lagna_lon = (kundli.get("ascendantDeg") or kundli.get("lagnaDeg")
                 or lagna_si * 30.0)
    is_day = 6 <= birth_dt.hour < 18
    sahams = compute_sahams_extended(src_planets, float(lagna_lon), is_day)
    return {"available": True, "is_day_birth": is_day,
            "sahams_extended": sahams,
            "extension_count": len(sahams)}


def format_phase_m_summary(r: dict) -> str:
    if not r or not r.get("available"):
        return f"▸ PHASE M SAHAMS-EXT: ❌ {r.get('reason','n/a') if r else 'n/a'}"
    L = [f"▸ PHASE M SAHAMS EXTENDED (Sprint-38) — +{r['extension_count']} additional sensitive points",
         f"  (Combined with Phase-J's 30 ⇒ {30 + r['extension_count']} total Sahams in LF)"]
    for s in r["sahams_extended"]:
        L.append(f"      ▪ {s['name']:<18} {s['sign']:<11} {s['deg_in_sign']:5.2f}° "
                 f"(lord {s['lord']:<8}) — {s['meaning']}")
    return "\n".join(L)

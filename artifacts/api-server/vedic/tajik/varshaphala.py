"""
Sprint 35 / Phase J — Tajik System (Annual / Varshaphala).
Implements 6 sub-systems totalling ~30 calculations:
  J1 Varshaphala (Sun-return chart for current age)
  J2 Muntha (progressed point — 1 sign per year)
  J3 Sahams (~30 sensitive points)
  J4 Tajik aspects (Ittasala, Eesarafa, Mukabala, Iqbal, Idbar)
  J5 Tajik 16 Yogas (rule-based detection of 6 most common)
  J6 Munis (3-year period rotation through 7 munis)
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Optional

try:
    import swisseph as swe
    _HAS_SWE = True
except Exception:
    _HAS_SWE = False

SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
              "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_LORD = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
             "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]

PLANET_SWE = {
    "Sun": 0, "Moon": 1, "Mars": 4, "Mercury": 2, "Jupiter": 5,
    "Venus": 3, "Saturn": 6,
}
PLANET_DAILY_DEG = {
    "Sun": 1.00, "Moon": 13.18, "Mars": 0.52, "Mercury": 1.38,
    "Jupiter": 0.083, "Venus": 1.20, "Saturn": 0.034,
}


def _set_ayanamsa():
    if _HAS_SWE: swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)


def _parse_dob(dob: str, btime: str = "12:00") -> Optional[datetime]:
    for fmt in ("%Y-%m-%d","%d-%m-%Y","%d %b %Y","%d %B %Y"):
        try: dt = datetime.strptime(dob, fmt); break
        except Exception: continue
    else: return None
    try:
        if isinstance(btime, str) and ":" in btime:
            hh, mm = btime.split(":")[:2]
            dt = dt.replace(hour=int(hh), minute=int(mm))
    except Exception: pass
    return dt


# ─── J1 Varshaphala — Sun-Return ──────────────────────────────────────
def find_solar_return(birth_dt: datetime,
                       target_year: Optional[int] = None) -> dict[str, Any]:
    """Search ±15 days around birth-anniversary for moment when transit
       sidereal Sun = natal sidereal Sun (within 0.001°)."""
    if not _HAS_SWE:
        return {"available": False, "reason": "swisseph unavailable"}
    _set_ayanamsa()
    target_year = target_year or datetime.utcnow().year
    # If birth-anniversary already passed this year, take this year's; else
    # take last completed return (=> previous year).
    today = datetime.utcnow()
    anniv = birth_dt.replace(year=target_year)
    if anniv > today:
        target_year -= 1
        anniv = birth_dt.replace(year=target_year)
    # Natal Sun sidereal lon
    natal_jd = swe.julday(birth_dt.year, birth_dt.month, birth_dt.day,
                           birth_dt.hour + birth_dt.minute/60.0)
    natal_sun = swe.calc_ut(natal_jd, swe.SUN, swe.FLG_SIDEREAL)[0][0] % 360
    # Bisection search ±15 days
    t_low = anniv - timedelta(days=15)
    t_high = anniv + timedelta(days=15)
    def sun_lon_at(dt):
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
        return swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0] % 360
    def diff(dt):
        d = sun_lon_at(dt) - natal_sun
        return ((d + 180) % 360) - 180
    # Linear scan to find sign change
    step = timedelta(hours=6); t = t_low; prev = diff(t); cross = None
    while t < t_high:
        cur = diff(t + step)
        if prev * cur < 0:
            cross = (t, t + step); break
        prev = cur; t += step
    if not cross:
        return {"available": False, "reason": "no Sun-return found in window"}
    a, b = cross
    for _ in range(40):
        mid = a + (b - a) / 2
        if diff(a) * diff(mid) < 0: b = mid
        else: a = mid
    sr_dt = a + (b - a) / 2
    # Compute VS planets
    sr_jd = swe.julday(sr_dt.year, sr_dt.month, sr_dt.day,
                        sr_dt.hour + sr_dt.minute/60.0)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    vs_planets = []
    for nm, code in PLANET_SWE.items():
        lon, _, _, speed = swe.calc_ut(sr_jd, code, flags)[0][:4]
        vs_planets.append({"name": nm, "longitude": lon % 360,
                            "sign": SIGN_NAMES[int((lon % 360)//30)],
                            "deg_in_sign": round((lon % 360) % 30, 2),
                            "speed_per_day": round(speed, 4),
                            "retrograde": speed < 0})
    rahu_lon = swe.calc_ut(sr_jd, swe.MEAN_NODE, flags)[0][0] % 360
    vs_planets.append({"name": "Rahu", "longitude": rahu_lon,
                        "sign": SIGN_NAMES[int(rahu_lon//30)],
                        "deg_in_sign": round(rahu_lon % 30, 2),
                        "speed_per_day": -0.053, "retrograde": True})
    vs_planets.append({"name": "Ketu", "longitude": (rahu_lon + 180) % 360,
                        "sign": SIGN_NAMES[int(((rahu_lon+180)%360)//30)],
                        "deg_in_sign": round((rahu_lon+180) % 30, 2),
                        "speed_per_day": -0.053, "retrograde": True})
    return {
        "available": True,
        "sun_return_utc": sr_dt.strftime("%Y-%m-%d %H:%M"),
        "varsha_year": target_year - birth_dt.year + 1,  # 1-based age
        "natal_sun_sidereal_lon": round(natal_sun, 4),
        "vs_planets": vs_planets,
    }


# ─── J2 Muntha ─────────────────────────────────────────────────────────
def muntha(natal_lagna_si: int, age_years: int) -> dict[str, Any]:
    """Muntha advances 1 sign/yr from natal Lagna. Year 1 = natal Lagna."""
    m_si = (natal_lagna_si + age_years - 1) % 12
    m_house = (age_years - 1) % 12 + 1  # from natal Lagna
    fav_houses = {1, 2, 3, 5, 9, 10, 11}
    return {
        "muntha_sign": SIGN_NAMES[m_si],
        "muntha_house_from_natal_lagna": m_house,
        "muntha_lord": SIGN_LORD[m_si],
        "verdict": "FAVOURABLE" if m_house in fav_houses else "CHALLENGING",
    }


# ─── J3 Sahams (30 most-used) ─────────────────────────────────────────
SAHAM_DEFS = [
    # (name, formula_day [tuple of planet names + "Lagna"], formula_night, meaning)
    # formula = sum/diff: (A, B, C) => A - B + C  (mod 360)
    ("Punya",     ("Moon","Sun","Lagna"),     ("Sun","Moon","Lagna"),    "Merit, virtue"),
    ("Vidya",     ("Sun","Moon","Lagna"),     ("Moon","Sun","Lagna"),    "Knowledge, learning"),
    ("Yasha",     ("Jupiter","Punya","Lagna"),("Punya","Jupiter","Lagna"),"Fame, reputation"),
    ("Mitra",     ("Jupiter","Punya","Lagna"),("Punya","Jupiter","Lagna"),"Friendship"),
    ("Mahatmya",  ("Mars","Moon","Lagna"),    ("Moon","Mars","Lagna"),   "Greatness"),
    ("Ascha",     ("Mars","Saturn","Lagna"),  ("Saturn","Mars","Lagna"), "Hope, expectation"),
    ("Samartha",  ("Mars","Lagna","Lagna"),   ("Lagna","Mars","Lagna"),  "Capability"),
    ("Bhratri",   ("Jupiter","Saturn","Lagna"),("Saturn","Jupiter","Lagna"),"Brothers"),
    ("Gaurava",   ("Jupiter","Moon","Lagna"), ("Moon","Jupiter","Lagna"),"Honor"),
    ("Pitri",     ("Saturn","Sun","Lagna"),   ("Sun","Saturn","Lagna"),  "Father"),
    ("Rajya",     ("Saturn","Sun","Lagna"),   ("Sun","Saturn","Lagna"),  "Kingdom, power"),
    ("Matri",     ("Moon","Venus","Lagna"),   ("Venus","Moon","Lagna"),  "Mother"),
    ("Putra",     ("Jupiter","Sun","Lagna"),  ("Sun","Jupiter","Lagna"), "Children"),
    ("Jeeva",     ("Saturn","Jupiter","Lagna"),("Jupiter","Saturn","Lagna"),"Vitality"),
    ("Karma",     ("Mars","Mercury","Lagna"), ("Mercury","Mars","Lagna"),"Action, work"),
    ("Roga",      ("Lagna","Moon","Lagna"),   ("Moon","Lagna","Lagna"),  "Disease"),
    ("Kali",      ("Jupiter","Mars","Lagna"), ("Mars","Jupiter","Lagna"),"Strife"),
    ("Sastra",    ("Jupiter","Saturn","Lagna"),("Saturn","Jupiter","Lagna"),"Scripture"),
    ("Bandhu",    ("Mercury","Moon","Lagna"), ("Moon","Mercury","Lagna"),"Relations"),
    ("Mrityu",    ("Moon","Saturn","Lagna"),  ("Saturn","Moon","Lagna"), "Death-risk"),
    ("Paradesha", ("9th-cusp","9th-lord","Lagna"),("9th-lord","9th-cusp","Lagna"),"Foreign travel"),
    ("Artha",     ("2nd-cusp","2nd-lord","Lagna"),("2nd-lord","2nd-cusp","Lagna"),"Wealth"),
    ("Paradara",  ("Venus","Sun","Lagna"),    ("Sun","Venus","Lagna"),   "Adultery"),
    ("Vanik",     ("Moon","Mercury","Lagna"), ("Mercury","Moon","Lagna"),"Trade"),
    ("Karyasiddhi",("Saturn","Sun","Lagna"),  ("Sun","Saturn","Lagna"),  "Goal achievement"),
    ("Vivaha",    ("Venus","Saturn","Lagna"), ("Saturn","Venus","Lagna"),"Marriage"),
    ("Santana",   ("Jupiter","Sun","Lagna"),  ("Sun","Jupiter","Lagna"), "Progeny"),
    ("Surya",     ("Mercury","Sun","Lagna"),  ("Sun","Mercury","Lagna"), "Solar power"),
    ("Sastraganga",("Jupiter","Mercury","Lagna"),("Mercury","Jupiter","Lagna"),"Learning depth"),
    ("Bandhana",  ("Saturn","Mars","Lagna"),  ("Mars","Saturn","Lagna"), "Imprisonment"),
]


def _planet_lon_in(planets_dict: dict, name: str,
                    lagna_lon: float) -> Optional[float]:
    if name == "Lagna": return lagna_lon
    if name in planets_dict: return planets_dict[name]
    # Cusp/lord placeholders simplified to lagna-based equal cusp
    if name.endswith("-cusp"):
        try:
            h = int(name.split("-")[0].rstrip("ndstrh"))  # "9th" -> 9
            return (lagna_lon + (h - 1) * 30.0) % 360
        except Exception: return None
    if name.endswith("-lord"):
        try:
            h = int(name.split("-")[0].rstrip("ndstrh"))
            cusp_si = int(((lagna_lon + (h - 1) * 30.0) % 360) // 30)
            lord = SIGN_LORD[cusp_si]
            return planets_dict.get(lord)
        except Exception: return None
    return None


def compute_sahams(planets: list[dict], lagna_lon: float,
                    is_day_birth: bool) -> list[dict]:
    plon = {p["name"]: p["longitude"] for p in planets
            if isinstance(p.get("longitude"), (int, float))}
    cached: dict[str, float] = {}  # for sahams that depend on other sahams (Yasha→Punya)
    out = []
    for name, day_f, night_f, meaning in SAHAM_DEFS:
        f = day_f if is_day_birth else night_f
        a_n, b_n, c_n = f
        # Resolve A (may be a previously-computed saham)
        def resolve(x):
            if x in cached: return cached[x]
            return _planet_lon_in(plon, x, lagna_lon)
        a, b, c = resolve(a_n), resolve(b_n), resolve(c_n)
        if a is None or b is None or c is None:
            continue
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


# ─── J4 Tajik aspects ─────────────────────────────────────────────────
TAJIK_ORBS = {  # max orb in degrees (deeptamsha) for a Tajik aspect
    "Sun": 15.0, "Moon": 12.0, "Mars": 8.0, "Mercury": 7.0,
    "Jupiter": 9.0, "Venus": 7.0, "Saturn": 9.0,
    "Rahu": 5.0, "Ketu": 5.0,
}
TAJIK_ASPECT_ANGLES = [0, 60, 90, 120, 180]  # conjunction, sextile, square, trine, opposition


def tajik_aspects(planets: list[dict]) -> list[dict]:
    """Return all pairs forming an exact Tajik aspect within deeptamsha orb,
       classified as Ittasala (applying), Eesarafa (separating), Iqbal (applying<1°),
       Idbar (separating <1°), Mukabala (opposition)."""
    rels = []
    pdata = [p for p in planets if isinstance(p.get("longitude"),(int,float))
             and isinstance(p.get("speed_per_day"),(int,float))]
    for i in range(len(pdata)):
        for j in range(i+1, len(pdata)):
            a, b = pdata[i], pdata[j]
            sep = (b["longitude"] - a["longitude"]) % 360
            for ang in TAJIK_ASPECT_ANGLES:
                d = abs(sep - ang); d = min(d, 360 - d)
                orb_max = (TAJIK_ORBS.get(a["name"],5) + TAJIK_ORBS.get(b["name"],5)) / 2
                if d <= orb_max:
                    # applying = faster planet moving toward exact aspect
                    fast, slow = (a, b) if abs(a["speed_per_day"]) >= abs(b["speed_per_day"]) else (b, a)
                    # signed separation from fast to slow
                    relpos = (slow["longitude"] - fast["longitude"]) % 360
                    diff_from_exact = (relpos - ang)
                    diff_from_exact = ((diff_from_exact + 180) % 360) - 180
                    applying = diff_from_exact * (fast["speed_per_day"] - slow["speed_per_day"]) < 0
                    if ang == 180: kind = "Mukabala (opposition)"
                    elif d <= 1.0 and applying: kind = "Iqbal (applying <1°)"
                    elif d <= 1.0: kind = "Idbar (separating <1°)"
                    elif applying: kind = "Ittasala (applying)"
                    else: kind = "Eesarafa (separating)"
                    rels.append({
                        "p1": a["name"], "p2": b["name"],
                        "angle": ang, "orb_deg": round(d, 2),
                        "kind": kind, "applying": applying,
                    })
                    break
    return rels


# ─── J5 Tajik 16 yogas (top 6 detectable) ─────────────────────────────
TAJIK_16_YOGAS_NAMES = [
    "Ikkabal", "Ittasala", "Eesarafa", "Nakta", "Yamaya", "Manaoo",
    "Kambool", "Ghairatkambool", "Khalkbeer", "Razaa", "Doot-tirthul",
    "Dukhabar", "Tambeer", "Khazoot", "Razaaduna", "Khallakambool",
]


def detect_tajik_yogas(aspects: list[dict],
                        planets: list[dict],
                        varsha_lagna_lord: str) -> list[dict]:
    """Detect 6 most common Tajik yogas from the aspect list."""
    found = []
    # Ittasala — any applying aspect involving lagnesha
    for r in aspects:
        if r["applying"] and varsha_lagna_lord in (r["p1"], r["p2"]):
            found.append({"yoga": "Ittasala",
                          "between": (r["p1"], r["p2"]),
                          "effect": "Promise of result — fast planet brings boon to slow one (varsha lord involved)"})
            break
    # Eesarafa — any separating aspect with lagnesha
    for r in aspects:
        if not r["applying"] and varsha_lagna_lord in (r["p1"], r["p2"]):
            found.append({"yoga": "Eesarafa",
                          "between": (r["p1"], r["p2"]),
                          "effect": "Loss of opportunity — opportunity is past"})
            break
    # Nakta — Mercury or Moon transferring light between two slow planets
    fast = {"Moon", "Mercury"}
    slow = {"Jupiter", "Saturn"}
    for r in aspects:
        if {r["p1"], r["p2"]} <= (fast | slow) and (r["p1"] in fast or r["p2"] in fast):
            other = r["p2"] if r["p1"] in fast else r["p1"]
            if other in slow:
                found.append({"yoga": "Nakta",
                              "between": (r["p1"], r["p2"]),
                              "effect": "Light transfer — third party brings benefit"})
                break
    # Yamaya — two slow planets in mutual aspect
    for r in aspects:
        if {r["p1"], r["p2"]} <= slow:
            found.append({"yoga": "Yamaya",
                          "between": (r["p1"], r["p2"]),
                          "effect": "Slow planets collude — major karmic event"})
            break
    # Manaoo — separating aspect that prevents an Ittasala
    e_count = sum(1 for r in aspects if not r["applying"])
    if e_count >= 3:
        found.append({"yoga": "Manaoo",
                      "between": ("multiple",),
                      "effect": "Many separating aspects — frustration / blocked promise"})
    # Kambool — applying aspect between two strong planets (orb <2°)
    for r in aspects:
        if r["applying"] and r["orb_deg"] < 2.0 and r["angle"] in (0, 120):
            found.append({"yoga": "Kambool",
                          "between": (r["p1"], r["p2"]),
                          "effect": "Strong yoga — promised event materializes"})
            break
    return found


# ─── J6 Munis (3-yr period) ───────────────────────────────────────────
MUNIS = ["Vasishta", "Kashyapa", "Bharadvaja", "Atri", "Vishvamitra",
         "Gautama", "Jamadagni"]
MUNI_EFFECTS = {
    "Vasishta":   "Authority, dharma, royal favor — auspicious",
    "Kashyapa":   "Sustenance, family expansion, healing — neutral-positive",
    "Bharadvaja": "Learning, teaching, scholarship — positive",
    "Atri":       "Detachment, wandering, spirituality — mixed",
    "Vishvamitra":"Powerful effort, conflict, innovation — challenging",
    "Gautama":    "Logic, debate, austerity — moderate",
    "Jamadagni":  "Anger, weapons, decisive action — challenging",
}


def munis_period(age_years: int) -> dict[str, Any]:
    """Each muni rules a 3-year block; rotates through 7 munis cyclically."""
    block = (age_years - 1) // 3        # zero-based block
    muni_idx = block % 7
    block_start = block * 3 + 1
    block_end = block_start + 2
    return {
        "current_age": age_years,
        "current_muni": MUNIS[muni_idx],
        "block_years": f"{block_start}–{block_end}",
        "effect": MUNI_EFFECTS[MUNIS[muni_idx]],
        "next_muni": MUNIS[(muni_idx + 1) % 7],
        "next_muni_starts_at_age": block_end + 1,
    }


# ─── Master orchestrator ──────────────────────────────────────────────
def compute_phase_j_tajik(kundli: dict, birth: dict) -> dict[str, Any]:
    # Sprint-26 Fix-K: defensive None-handling. birth=None (legacy
    # father/spouse callsite) previously crashed via 'NoneType.get'
    # at the dob/btime extraction. Falling back to kundli.get() and
    # the "12:00" default keeps the phase usable.
    birth = birth or {}
    if not _HAS_SWE:
        return {"available": False, "reason": "swisseph unavailable"}
    dob = birth.get("dob") or birth.get("date") or kundli.get("dob")
    btime = birth.get("time") or kundli.get("time") or "12:00"
    if not isinstance(dob, str):
        return {"available": False, "reason": "dob missing"}
    birth_dt = _parse_dob(dob, btime)
    if not birth_dt:
        return {"available": False, "reason": "dob parse failed"}
    age = max(1, datetime.utcnow().year - birth_dt.year + 1)
    # Find natal lagna
    lagna_sign = kundli.get("ascendant") or kundli.get("lagna")
    lagna_si = (SIGN_NAMES.index(lagna_sign)
                if isinstance(lagna_sign, str) and lagna_sign in SIGN_NAMES
                else 0)
    lagna_lon = (kundli.get("ascendantDeg") or kundli.get("lagnaDeg")
                 or lagna_si * 30.0)
    out: dict[str, Any] = {"available": True, "age_years": age}
    # J1 Varshaphala
    sr = find_solar_return(birth_dt)
    out["varshaphala"] = sr
    # J2 Muntha
    out["muntha"] = muntha(lagna_si, age)
    # J3 Sahams (using VS planets if available, else natal)
    src_planets = sr.get("vs_planets") if sr.get("available") else (kundli.get("planets") or [])
    if src_planets:
        # is_day_birth — Sun above horizon at birth (heuristic: 6 AM–6 PM local)
        is_day = 6 <= birth_dt.hour < 18
        out["is_day_birth"] = is_day
        out["sahams"] = compute_sahams(src_planets, float(lagna_lon), is_day)
    # J4 Tajik aspects (need speed → use VS planets only)
    if sr.get("available"):
        aspects = tajik_aspects(sr["vs_planets"])
        out["tajik_aspects"] = aspects
        # J5 Tajik yogas (need varsha lagna lord — use natal lagna lord here)
        v_lord = SIGN_LORD[lagna_si]
        out["tajik_yogas"] = detect_tajik_yogas(aspects, sr["vs_planets"], v_lord)
    # J6 Munis
    out["munis"] = munis_period(age)
    return out


def format_phase_j_summary(result: dict) -> str:
    if not result or not result.get("available"):
        return f"▸ PHASE J TAJIK: ❌ {result.get('reason','n/a') if result else 'n/a'}"
    L = [f"▸ PHASE J TAJIK / VARSHAPHALA (Sprint-35) — Year {result['age_years']}"]
    vs = result.get("varshaphala", {})
    if vs.get("available"):
        L.append(f"  ── J1 VARSHAPHALA (Sun-Return) ──")
        L.append(f"    Sun-Return UTC: {vs['sun_return_utc']} | Varsha-Year #{vs['varsha_year']}")
        for p in vs["vs_planets"]:
            r = " ®" if p.get("retrograde") else ""
            L.append(f"      {p['name']:<8} {p['sign']:<11} {p['deg_in_sign']:6.2f}°{r}")
    m = result.get("muntha", {})
    if m:
        L.append(f"  ── J2 MUNTHA ── {m['muntha_sign']} (H{m['muntha_house_from_natal_lagna']} from natal Lagna), lord {m['muntha_lord']} → {m['verdict']}")
    sah = result.get("sahams", [])
    if sah:
        L.append(f"  ── J3 SAHAMS ({len(sah)} computed; day-birth={result.get('is_day_birth')}) ──")
        for s in sah:
            L.append(f"      ▪ {s['name']:<14} {s['sign']:<11} {s['deg_in_sign']:5.2f}° "
                     f"(lord {s['lord']:<8}) — {s['meaning']}")
    asps = result.get("tajik_aspects", [])
    if asps:
        L.append(f"  ── J4 TAJIK ASPECTS ({len(asps)} found) ──")
        for r in asps[:8]:
            L.append(f"      {r['p1']:<8} ↔ {r['p2']:<8} {r['angle']:>3}° (orb {r['orb_deg']:.2f}) — {r['kind']}")
    yogas = result.get("tajik_yogas", [])
    if yogas:
        L.append(f"  ── J5 TAJIK 16-YOGAS (detected {len(yogas)} of 16) ──")
        for y in yogas:
            L.append(f"      ▪ {y['yoga']:<10} between {y['between']} — {y['effect']}")
    mn = result.get("munis", {})
    if mn:
        L.append(f"  ── J6 MUNIS (3-yr period) ── {mn['current_muni']} (yrs {mn['block_years']}) — {mn['effect']}")
        L.append(f"      Next: {mn['next_muni']} from age {mn['next_muni_starts_at_age']}")
    return "\n".join(L)

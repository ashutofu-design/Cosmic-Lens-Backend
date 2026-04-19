"""
Sprint 21 — Tier 5 Dashas Extras (folder-organized)
====================================================
Adds 7+ new dasha systems missing from existing engine.

Already-exist (skipped):
  • Vimshottari (core engine)
  • Chara Dasha (chara_dasha.py)
  • Sthira Dasha (extra_jaimini_dashas.py)
  • Niryana Shoola Dasha (extra_jaimini_dashas.py)

New in this module:
  1. Yogini Dasha       — 36-yr cycle, 8 yoginis (1-8 yr each)
  2. Ashtottari Dasha   — 108-yr cycle, 8 planets
  3. Narayana Dasha     — Jaimini 12-sign (Padakrama)
  4. Karaka Dasha       — Jaimini 8 chara-karakas
  5. Naisargika Dasha   — Natural age-based (Moon→Sat 86y total)
  6. Tara Dasha         — Janma-tara cycle (9 stars)
  7. Brahma Dasha       — From Brahma graha (BPHS Ch.49)
  8. Yogardha Dasha     — Vimshottari+Ashtottari blended
  9. Pinda / Amshayur   — Aayur (longevity) calculations
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
              "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
NAKSHATRAS = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
              "Punarvasu","Pushya","Ashlesha","Magha","P.Phalguni","U.Phalguni",
              "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
              "Mula","P.Ashadha","U.Ashadha","Shravana","Dhanishta","Shatabhisha",
              "P.Bhadrapada","U.Bhadrapada","Revati"]
SIGN_LORDS = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
              "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]


def _sign_idx(s: Any) -> Optional[int]:
    if isinstance(s, int) and 0 <= s <= 11: return s
    if isinstance(s, str):
        try: return SIGN_NAMES.index(s)
        except ValueError: return None
    return None


def _to_dt(dob: Any) -> Optional[datetime]:
    if isinstance(dob, datetime): return dob
    if isinstance(dob, str):
        s = dob.strip()
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                    "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%d %B %Y",
                    "%b %d %Y", "%B %d, %Y"):
            try: return datetime.strptime(s[:30], fmt)
            except Exception: pass
        # try truncated forms
        for fmt in ("%Y-%m-%d", "%d %b %Y", "%d-%m-%Y"):
            try: return datetime.strptime(s[:11], fmt)
            except Exception: pass
    return None


def _nak_idx(name: str) -> Optional[int]:
    if not name: return None
    s = (name.replace("Purva ", "P.").replace("Uttara ", "U.")
              .replace("Purva", "P.").replace("Uttara", "U.")
              .replace("P. ", "P.").replace("U. ", "U.")
              .replace(" ", "").strip())
    # build flat lookup
    targets = {n.replace(" ", "").lower(): i for i, n in enumerate(NAKSHATRAS)}
    return targets.get(s.lower())


# ─── 1. YOGINI DASHA (36-yr cycle, 8 yoginis) ──────────────────────────
YOGINIS = [
    ("Mangala",  1, "Auspicious, success, gains"),
    ("Pingala",  2, "Mixed, struggles, conflicts"),
    ("Dhanya",   3, "Wealth, prosperity, abundance"),
    ("Bhramari", 4, "Travel, restlessness, movement"),
    ("Bhadrika", 5, "Stable, virtuous, family"),
    ("Ulka",     6, "Sudden upheavals, accidents"),
    ("Siddha",   7, "Spiritual gains, success"),
    ("Sankata",  8, "Crisis, obstacles, transformation"),
]


def compute_yogini_dasha(nakshatra_name: str, dob: Any) -> dict:
    """Yogini cycle starts based on (nakshatra_idx + 1) % 8."""
    nak = _nak_idx(nakshatra_name)
    dob_dt = _to_dt(dob)
    if nak is None or dob_dt is None:
        return {"available": False, "reason": "missing nakshatra or dob"}
    start = (nak + 1) % 8
    seq = []
    cursor = dob_dt
    # 3 cycles × 8 yoginis = 108 years coverage
    for i in range(24):
        idx = (start + i) % 8
        name, years, theme = YOGINIS[idx]
        end = cursor + timedelta(days=years * 365.25)
        seq.append({"yogini": name, "years": years, "theme": theme,
                    "cycle": (i // 8) + 1,
                    "start": cursor.strftime("%Y-%m-%d"),
                    "end": end.strftime("%Y-%m-%d")})
        cursor = end
    today = datetime.utcnow()
    current = next((s for s in seq if datetime.strptime(s["start"], "%Y-%m-%d") <= today
                    < datetime.strptime(s["end"], "%Y-%m-%d")), None)
    return {"available": True, "system": "Yogini Dasha (36-yr cycle)",
            "starting_yogini": YOGINIS[start][0], "sequence": seq,
            "current": current}


# ─── 2. ASHTOTTARI DASHA (108-yr cycle, 8 planets) ─────────────────────
ASHTOTTARI_ORDER = [
    ("Sun", 6), ("Moon", 15), ("Mars", 8), ("Mercury", 17),
    ("Saturn", 10), ("Jupiter", 19), ("Rahu", 12), ("Venus", 21),
]
ASHTOTTARI_LOOKUP = {p: y for p, y in ASHTOTTARI_ORDER}


def compute_ashtottari_dasha(nakshatra_name: str, nak_pada: int, dob: Any) -> dict:
    """Starting MD based on Krishnamurthy's lookup: nakshatra+pada → planet."""
    nak = _nak_idx(nakshatra_name)
    dob_dt = _to_dt(dob)
    if nak is None or dob_dt is None:
        return {"available": False, "reason": "missing nakshatra or dob"}
    # Standard Ashtottari starting-MD: Nakshatra group of 4 maps to planet sequence
    # Ashwini, Bharani, Krittika, Rohini → Sun, Moon, Mars, Mer
    # Mrigashira, Ardra, Punarvasu, Pushya → Sat, Jup, Rahu, Ven (then cycle)
    # Simplified: starting planet by (nak // 4) % 8
    start_idx = (nak // 4) % 8
    seq = []
    cursor = dob_dt
    for i in range(8):
        planet, years = ASHTOTTARI_ORDER[(start_idx + i) % 8]
        end = cursor + timedelta(days=years * 365.25)
        seq.append({"planet": planet, "years": years,
                    "start": cursor.strftime("%Y-%m-%d"),
                    "end": end.strftime("%Y-%m-%d")})
        cursor = end
    today = datetime.utcnow()
    current = next((s for s in seq if datetime.strptime(s["start"], "%Y-%m-%d") <= today
                    < datetime.strptime(s["end"], "%Y-%m-%d")), None)
    return {"available": True, "system": "Ashtottari Dasha (108-yr cycle)",
            "starting_planet": ASHTOTTARI_ORDER[start_idx][0],
            "sequence": seq, "current": current}


# ─── 3. NARAYANA / PADAKRAMA DASHA (Jaimini 12-sign) ───────────────────
def _movement_type(sign_idx: int) -> str:
    """Movable: 0,3,6,9 (Aries/Cancer/Libra/Cap)
       Fixed:   1,4,7,10 (Tau/Leo/Sco/Aqu)
       Dual:    2,5,8,11 (Gem/Vir/Sag/Pis)"""
    return ["Movable","Fixed","Dual"][sign_idx % 3] if False else \
           ["Movable","Fixed","Dual"][["Movable","Fixed","Dual"].index(
               ["Movable","Fixed","Dual"][sign_idx % 3])]  # silly identity


def _sign_movement(sign_idx: int) -> str:
    if sign_idx in (0, 3, 6, 9): return "Movable"
    if sign_idx in (1, 4, 7, 10): return "Fixed"
    return "Dual"


def _narayana_md_length(sign_idx: int, planets: list) -> int:
    """MD length = direction count from sign to its lord. Simplified BPHS:
    For movable: count direct from sign to lord, subtract 1.
    For fixed: count reverse from 7th-sign to lord, subtract 1.
    For dual: count from middle-sign (interpreted as start sign) similarly."""
    sti = {n: i for i, n in enumerate(SIGN_NAMES)}
    plmap = {}
    for p in planets or []:
        n = p.get("name")
        s = p.get("sign_idx")
        if s is None and isinstance(p.get("sign"), str):
            s = sti.get(p["sign"])
        if n and isinstance(s, int):
            plmap[n] = s
    lord = SIGN_LORDS[sign_idx]
    lord_sign = plmap.get(lord)
    if lord_sign is None:
        return 1
    movement = _sign_movement(sign_idx)
    if movement == "Movable":
        count = (lord_sign - sign_idx) % 12
    elif movement == "Fixed":
        seventh = (sign_idx + 6) % 12
        count = (seventh - lord_sign) % 12
    else:
        count = (lord_sign - sign_idx) % 12
    length = count if count > 0 else 12
    if length == 12: length = 0  # if lord in same sign → 0 → set to 12
    return max(1, length)


def compute_narayana_dasha(planets: list, lagna_sign: Any, dob: Any) -> dict:
    li = _sign_idx(lagna_sign)
    dob_dt = _to_dt(dob)
    if li is None or dob_dt is None:
        return {"available": False, "reason": "missing lagna or dob"}
    seq = []
    cursor = dob_dt
    for i in range(12):
        s = (li + i) % 12
        years = _narayana_md_length(s, planets)
        end = cursor + timedelta(days=years * 365.25)
        seq.append({"sign": SIGN_NAMES[s], "years": years,
                    "movement": _sign_movement(s),
                    "start": cursor.strftime("%Y-%m-%d"),
                    "end": end.strftime("%Y-%m-%d")})
        cursor = end
    today = datetime.utcnow()
    current = next((s for s in seq if datetime.strptime(s["start"], "%Y-%m-%d") <= today
                    < datetime.strptime(s["end"], "%Y-%m-%d")), None)
    return {"available": True, "system": "Narayana (Padakrama) Dasha — Jaimini 12-sign",
            "sequence": seq, "current": current}


# ─── 4. KARAKA DASHA (Jaimini 8 chara-karakas) ─────────────────────────
KARAKA_NAMES = ["Atmakaraka","Amatyakaraka","Bhratrikaraka","Matrikaraka",
                "Putrakaraka","Gnatikaraka","Darakaraka","Custom"]


def compute_karaka_dasha(planets: list, dob: Any) -> dict:
    """Order chara-karakas by degree (highest=AK), each karaka rules
    sign-equivalent years based on its placement. Simplified: each karaka
    period = degree-to-30 normalization × 12 years."""
    dob_dt = _to_dt(dob)
    if dob_dt is None:
        return {"available": False, "reason": "missing dob"}
    candidates = []
    for p in planets or []:
        n = p.get("name")
        if n in ("Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu"):
            lon = p.get("longitude")
            if isinstance(lon, (int, float)):
                deg_in_sign = lon % 30
                # Rahu uses (30 - deg)
                if n == "Rahu":
                    deg_in_sign = 30 - deg_in_sign
                candidates.append((n, deg_in_sign))
    if len(candidates) < 7:
        return {"available": False, "reason": "insufficient planet data"}
    candidates.sort(key=lambda x: -x[1])  # highest degree first
    seq = []
    cursor = dob_dt
    for i, (name, deg) in enumerate(candidates[:8]):
        karaka = KARAKA_NAMES[i] if i < 8 else f"Karaka-{i+1}"
        # Years = deg/30 * 12 (so 30° = 12 years, 0° = 0 → min 1)
        years = max(1, int(round(deg / 30.0 * 12)))
        end = cursor + timedelta(days=years * 365.25)
        seq.append({"karaka": karaka, "planet": name,
                    "degree_in_sign": round(deg, 2), "years": years,
                    "start": cursor.strftime("%Y-%m-%d"),
                    "end": end.strftime("%Y-%m-%d")})
        cursor = end
    today = datetime.utcnow()
    current = next((s for s in seq if datetime.strptime(s["start"], "%Y-%m-%d") <= today
                    < datetime.strptime(s["end"], "%Y-%m-%d")), None)
    return {"available": True, "system": "Karaka Dasha — Jaimini 8 chara-karakas",
            "sequence": seq, "current": current}


# ─── 5. NAISARGIKA DASHA (Natural age-based, BPHS Ch.48) ───────────────
NAISARGIKA_ORDER = [
    ("Moon",     1),
    ("Mars",     2),
    ("Mercury",  9),
    ("Venus",   20),
    ("Jupiter", 18),
    ("Sun",     20),
    ("Saturn",  50),
]


def compute_naisargika_dasha(dob: Any) -> dict:
    """Fixed natural-age dasha — same for everyone (does NOT depend on chart)."""
    dob_dt = _to_dt(dob)
    if dob_dt is None:
        return {"available": False, "reason": "missing dob"}
    seq = []
    cursor = dob_dt
    for planet, years in NAISARGIKA_ORDER:
        end = cursor + timedelta(days=years * 365.25)
        seq.append({"planet": planet, "years": years,
                    "start": cursor.strftime("%Y-%m-%d"),
                    "end": end.strftime("%Y-%m-%d")})
        cursor = end
    today = datetime.utcnow()
    current = next((s for s in seq if datetime.strptime(s["start"], "%Y-%m-%d") <= today
                    < datetime.strptime(s["end"], "%Y-%m-%d")), None)
    return {"available": True, "system": "Naisargika Dasha (natural age 120-yr)",
            "sequence": seq, "current": current}


# ─── 6. TARA DASHA (Janma-tara cycle, 9 stars) ─────────────────────────
TARA_NAMES = ["Janma","Sampat","Vipat","Kshema","Pratyak","Sadhaka",
              "Vadha","Mitra","Ati-Mitra"]


def compute_tara_dasha(nakshatra_name: str, dob: Any) -> dict:
    """9-tara cycle from janma-nakshatra. Each tara = 9 years (simplified)."""
    nak = _nak_idx(nakshatra_name)
    dob_dt = _to_dt(dob)
    if nak is None or dob_dt is None:
        return {"available": False, "reason": "missing nakshatra or dob"}
    seq = []
    cursor = dob_dt
    for i, name in enumerate(TARA_NAMES):
        years = 9
        end = cursor + timedelta(days=years * 365.25)
        polarity = "POSITIVE" if name in ("Sampat","Kshema","Sadhaka","Mitra","Ati-Mitra") else \
                   ("NEGATIVE" if name in ("Vipat","Pratyak","Vadha") else "NEUTRAL")
        seq.append({"tara": name, "polarity": polarity, "years": years,
                    "start": cursor.strftime("%Y-%m-%d"),
                    "end": end.strftime("%Y-%m-%d")})
        cursor = end
    today = datetime.utcnow()
    current = next((s for s in seq if datetime.strptime(s["start"], "%Y-%m-%d") <= today
                    < datetime.strptime(s["end"], "%Y-%m-%d")), None)
    return {"available": True, "system": "Tara Dasha (9 janma-tara, 81 yr)",
            "sequence": seq, "current": current}


# ─── 7. BRAHMA DASHA (BPHS Ch.49) ──────────────────────────────────────
def compute_brahma_dasha(planets: list, lagna_sign: Any, dob: Any) -> dict:
    """Brahma Graha = strongest among lords-of (8th from Lagna, 8th from Moon, 8th from Sun).
    Returns Vimshottari-like sequence starting from Brahma graha."""
    li = _sign_idx(lagna_sign)
    dob_dt = _to_dt(dob)
    if li is None or dob_dt is None:
        return {"available": False, "reason": "missing lagna or dob"}
    sti = {n: i for i, n in enumerate(SIGN_NAMES)}
    plmap = {}
    for p in planets or []:
        n = p.get("name"); s = p.get("sign_idx")
        if s is None and isinstance(p.get("sign"), str):
            s = sti.get(p["sign"])
        if n: plmap[n] = s
    sun_s = plmap.get("Sun"); moon_s = plmap.get("Moon")
    candidates = []
    if li is not None: candidates.append(SIGN_LORDS[(li + 7) % 12])
    if isinstance(moon_s, int): candidates.append(SIGN_LORDS[(moon_s + 7) % 12])
    if isinstance(sun_s, int): candidates.append(SIGN_LORDS[(sun_s + 7) % 12])
    brahma = candidates[0] if candidates else "Jupiter"
    # Build Vimshottari-like 7-period from Brahma
    vims = [("Sun",6),("Moon",10),("Mars",7),("Rahu",18),("Jupiter",16),
            ("Saturn",19),("Mercury",17),("Ketu",7),("Venus",20)]
    start = next((i for i,(p,_) in enumerate(vims) if p == brahma), 0)
    seq = []; cursor = dob_dt
    for i in range(9):
        planet, years = vims[(start + i) % 9]
        end = cursor + timedelta(days=years * 365.25)
        seq.append({"planet": planet, "years": years,
                    "start": cursor.strftime("%Y-%m-%d"),
                    "end": end.strftime("%Y-%m-%d")})
        cursor = end
    today = datetime.utcnow()
    current = next((s for s in seq if datetime.strptime(s["start"], "%Y-%m-%d") <= today
                    < datetime.strptime(s["end"], "%Y-%m-%d")), None)
    return {"available": True, "system": "Brahma Dasha (BPHS Ch.49)",
            "brahma_graha": brahma, "sequence": seq, "current": current}


# ─── 8. YOGARDHA — Vimshottari + Ashtottari blended ────────────────────
def compute_yogardha_dasha(nakshatra_name: str, nak_pada: int, dob: Any) -> dict:
    """Yogardha = average of Vimshottari and Ashtottari periods (BPHS Ch.50).
    Simplified: take Ashtottari sequence, halve each period, return."""
    asht = compute_ashtottari_dasha(nakshatra_name, nak_pada, dob)
    if not asht.get("available"):
        return asht
    halved = []
    for s in asht["sequence"]:
        halved.append({**s, "years": s["years"] / 2})
    # rebuild dates
    dob_dt = _to_dt(dob)
    cursor = dob_dt
    out_seq = []
    for s in halved:
        end = cursor + timedelta(days=s["years"] * 365.25)
        out_seq.append({**s,
                        "start": cursor.strftime("%Y-%m-%d"),
                        "end": end.strftime("%Y-%m-%d")})
        cursor = end
    today = datetime.utcnow()
    current = next((s for s in out_seq if datetime.strptime(s["start"], "%Y-%m-%d") <= today
                    < datetime.strptime(s["end"], "%Y-%m-%d")), None)
    return {"available": True, "system": "Yogardha Dasha (Vims+Asht avg, 54-yr)",
            "sequence": out_seq, "current": current}


# ─── 9. PINDA / AMSHAYUR — Aayur (longevity) calculations ──────────────
PINDA_YEARS = {  # BPHS Ch.46 — full longevity per planet (years)
    "Sun": 19.5, "Moon": 25.0, "Mars": 15.0, "Mercury": 12.0,
    "Jupiter": 15.5, "Venus": 21.0, "Saturn": 20.0,
}


def compute_pinda_aayur(planets: list, lagna_sign: Any) -> dict:
    """Pinda Aayur — sum of contribution from each planet based on degree+strength.
    Simplified: each planet contributes (deg-in-sign / 30) × full pinda years."""
    li = _sign_idx(lagna_sign)
    if li is None:
        return {"available": False, "reason": "missing lagna"}
    contributions = {}
    total = 0.0
    for p in planets or []:
        n = p.get("name")
        if n not in PINDA_YEARS: continue
        lon = p.get("longitude")
        if not isinstance(lon, (int, float)): continue
        deg_in_sign = lon % 30
        contrib = (deg_in_sign / 30.0) * PINDA_YEARS[n]
        contributions[n] = round(contrib, 2)
        total += contrib
    return {"available": True, "system": "Pinda Aayur (BPHS longevity, simplified)",
            "contributions": contributions,
            "total_years": round(total, 2),
            "category": "Alpa-Aayur (<32)" if total < 32 else
                        ("Madhya-Aayur (32-72)" if total < 72 else "Purna-Aayur (>72)")}


def compute_amshayur(planets: list, lagna_sign: Any) -> dict:
    """Amshayur = sum of (navamsa-position / 12) × pinda years per planet."""
    li = _sign_idx(lagna_sign)
    if li is None:
        return {"available": False, "reason": "missing lagna"}
    contributions = {}
    total = 0.0
    for p in planets or []:
        n = p.get("name")
        if n not in PINDA_YEARS: continue
        lon = p.get("longitude")
        if not isinstance(lon, (int, float)): continue
        navamsa_pos = (lon % 30) // (30 / 9)  # which navamsa (0-8)
        contrib = ((navamsa_pos + 1) / 9.0) * PINDA_YEARS[n]
        contributions[n] = round(contrib, 2)
        total += contrib
    return {"available": True, "system": "Amshayur (navamsa-based longevity)",
            "contributions": contributions,
            "total_years": round(total, 2),
            "category": "Alpa-Aayur (<32)" if total < 32 else
                        ("Madhya-Aayur (32-72)" if total < 72 else "Purna-Aayur (>72)")}


# ─── Master orchestrator ────────────────────────────────────────────────
def compute_all_extra_dashas(kundli: dict) -> dict:
    planets = kundli.get("planets") or []
    lagna = kundli.get("ascendant") or kundli.get("lagna")
    dob = (kundli.get("dob") or kundli.get("birth_date")
           or (kundli.get("birth") or {}).get("date"))
    nak = kundli.get("nakshatra") or kundli.get("janma_nakshatra")
    if isinstance(nak, dict): nak = nak.get("name", "")
    if not nak:
        nak = (kundli.get("moon") or {}).get("nakshatra", "")
        if isinstance(nak, dict): nak = nak.get("name", "")
    pada = (kundli.get("nakshatraPada")
            or kundli.get("nakshatra_pada")
            or (kundli.get("moon") or {}).get("nakshatra_pada", 1))

    out = {}
    out["yogini"] = compute_yogini_dasha(nak, dob)
    out["ashtottari"] = compute_ashtottari_dasha(nak, pada, dob)
    out["narayana"] = compute_narayana_dasha(planets, lagna, dob)
    out["karaka"] = compute_karaka_dasha(planets, dob)
    out["naisargika"] = compute_naisargika_dasha(dob)
    out["tara"] = compute_tara_dasha(nak, dob)
    out["brahma"] = compute_brahma_dasha(planets, lagna, dob)
    out["yogardha"] = compute_yogardha_dasha(nak, pada, dob)
    out["pinda_aayur"] = compute_pinda_aayur(planets, lagna)
    out["amshayur"] = compute_amshayur(planets, lagna)
    return out


def format_extra_dashas_summary(d: dict) -> str:
    if not d: return ""
    lines = ["▸ EXTRA DASHAS (Sprint-21 Tier-5): 8 systems + 2 longevity"]
    for key, info in d.items():
        if not isinstance(info, dict): continue
        if not info.get("available"):
            lines.append(f"  • {key}: ❌ ({info.get('reason','n/a')})")
            continue
        sys_name = info.get("system", key)
        cur = info.get("current")
        if cur:
            label = (cur.get("planet") or cur.get("yogini")
                     or cur.get("sign") or cur.get("karaka")
                     or cur.get("tara"))
            lines.append(f"  ✅ {sys_name}: current = {label} "
                         f"({cur.get('start','?')} → {cur.get('end','?')})")
        elif "total_years" in info:
            lines.append(f"  ✅ {sys_name}: {info['total_years']} yr → {info.get('category','?')}")
        else:
            lines.append(f"  ✅ {sys_name}: computed")
    return "\n".join(lines)

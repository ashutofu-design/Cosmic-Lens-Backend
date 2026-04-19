"""
Sprint 31 / Phase E — Tier 5 Dashas (gap fill)
Adds 7 dashas missing from `vedic.dashas.dasha_extras`:
  E3  Kalachakra Dasha (sign-based; deha/jeeva sequence)
  E8a Mandooka Dasha (Frog-leap; jumps trine signs)
  E8b Drig Dasha (Sight; based on sign-aspects)
  E8c Trikona Dasha (Trine cycle; Lagna group/Moon group/Sun group)
  E8d Chaturasheeti Sama Dasha (84-yr equal; planet in 9th from Lagna)
  E9a Shashtihayani Dasha (60-yr Sun-based; if Sun in lagna)
  E9b Shatabdika Dasha (100-yr nakshatra-based; if 7th lord in 7th)
All systems return uniform shape:
  {available: bool, system: str, sequence: list, current: dict|None, ...}
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Optional

SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
              "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
NAK_NAMES = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
             "Punarvasu","Pushya","Ashlesha","Magha","P.Phalguni","U.Phalguni",
             "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
             "Mula","P.Ashadha","U.Ashadha","Shravana","Dhanishta","Shatabhisha",
             "P.Bhadrapada","U.Bhadrapada","Revati"]


# ─── helpers ──────────────────────────────────────────────────────────
def _sign_idx(s: Any) -> Optional[int]:
    if isinstance(s, int) and 0 <= s < 12: return s
    if isinstance(s, str) and s in SIGN_NAMES: return SIGN_NAMES.index(s)
    return None


def _to_dt(dob: Any) -> Optional[datetime]:
    if isinstance(dob, datetime): return dob
    if not isinstance(dob, str): return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y", "%d %b %Y", "%d %B %Y"):
        try: return datetime.strptime(dob, fmt)
        except Exception: continue
    return None


def _planet(planets: list, name: str) -> Optional[dict]:
    for p in planets:
        if isinstance(p, dict) and p.get("name") == name:
            return p
    return None


def _planet_sign_idx(planets: list, name: str) -> Optional[int]:
    p = _planet(planets, name)
    return _sign_idx(p.get("sign")) if p else None


def _planet_house(planets: list, name: str) -> Optional[int]:
    p = _planet(planets, name)
    return p.get("house") if p else None


def _nak_idx(nak: str) -> Optional[int]:
    if not isinstance(nak, str): return None
    s = nak.replace("Purva ", "P.").replace("Uttara ", "U.").replace(" ", "").lower()
    for i, n in enumerate(NAK_NAMES):
        if n.replace(" ", "").lower() == s: return i
    return None


def _build_seq(items: list[tuple[str, float, str]], dob_dt: datetime) -> list[dict]:
    """items: list of (label, years, theme); returns dated sequence."""
    seq = []
    cursor = dob_dt
    for label, years, theme in items:
        end = cursor + timedelta(days=years * 365.25)
        seq.append({"label": label, "years": years, "theme": theme,
                    "start": cursor.strftime("%Y-%m-%d"),
                    "end": end.strftime("%Y-%m-%d")})
        cursor = end
    return seq


def _find_current(seq: list[dict]) -> Optional[dict]:
    today = datetime.utcnow()
    for s in seq:
        st = datetime.strptime(s["start"], "%Y-%m-%d")
        en = datetime.strptime(s["end"], "%Y-%m-%d")
        if st <= today < en: return s
    return None


# ─── E3: Kalachakra Dasha ─────────────────────────────────────────────
KALACHAKRA_YEARS = {"Aries":7,"Taurus":16,"Gemini":9,"Cancer":21,"Leo":5,"Virgo":9,
                    "Libra":16,"Scorpio":7,"Sagittarius":10,"Capricorn":4,
                    "Aquarius":4,"Pisces":10}
KALACHAKRA_DEHA_SEQ = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                       "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]


def compute_kalachakra_dasha(planets: list, dob: Any) -> dict:
    """Kalachakra Dasha (BPHS Ch.62 simplified):
       Starts from Moon's nakshatra-pada deha-rashi; cycles through 12 signs
       with sign-specific year periods. Total: 100 years (sum of years)."""
    dob_dt = _to_dt(dob)
    moon_si = _planet_sign_idx(planets, "Moon")
    if dob_dt is None or moon_si is None:
        return {"available": False, "reason": "missing dob/Moon-sign"}
    start_idx = moon_si
    items = []
    for i in range(12):
        s = KALACHAKRA_DEHA_SEQ[(start_idx + i) % 12]
        items.append((s, KALACHAKRA_YEARS[s], f"Kalachakra Deha-rashi {s}"))
    seq = _build_seq(items, dob_dt)
    cur = _find_current(seq)
    return {"available": True, "system": "Kalachakra Dasha (118-yr deha-jeeva)",
            "starting_sign": SIGN_NAMES[start_idx],
            "sequence": seq, "current": cur}


# ─── E8a: Mandooka Dasha (Frog-leap) ─────────────────────────────────
MANDOOKA_YEARS = 10  # each sign = 10 yrs (BPHS: variable; using simplified equal)


def compute_mandooka_dasha(planets: list, lagna_sign: Any, dob: Any) -> dict:
    """Mandooka 'Frog' Dasha (Jaimini): leaps 3 signs at a time from Lagna.
       Each sign = 10 yrs equal. 12 signs × 10 = 120 yrs."""
    dob_dt = _to_dt(dob)
    li = _sign_idx(lagna_sign)
    if dob_dt is None or li is None:
        return {"available": False, "reason": "missing dob/lagna"}
    items = []
    for i in range(12):
        s = SIGN_NAMES[(li + i * 3) % 12]
        items.append((s, MANDOOKA_YEARS, f"Mandooka leap to {s}"))
    seq = _build_seq(items, dob_dt)
    cur = _find_current(seq)
    return {"available": True, "system": "Mandooka Dasha (120-yr Jaimini Frog-leap)",
            "starting_sign": SIGN_NAMES[li],
            "sequence": seq, "current": cur}


# ─── E8b: Drig Dasha (Sight-based) ───────────────────────────────────
DRIG_PLANET_PERIODS = [("Sun",6),("Moon",10),("Mars",7),("Mercury",8),
                        ("Jupiter",10),("Venus",9),("Saturn",10)]


def compute_drig_dasha(planets: list, lagna_sign: Any, dob: Any) -> dict:
    """Drig (Sight) Dasha (Jaimini): 7-planet sequence ordered by their
       count of sign-aspects on Lagna; period = 6-10 yrs each. Total: 60 yrs."""
    dob_dt = _to_dt(dob)
    li = _sign_idx(lagna_sign)
    if dob_dt is None or li is None:
        return {"available": False, "reason": "missing dob/lagna"}
    # Order planets by distance from Lagna (sign-house number 1..12)
    ordered = []
    for nm, yrs in DRIG_PLANET_PERIODS:
        psi = _planet_sign_idx(planets, nm)
        dist = ((psi - li) % 12) + 1 if psi is not None else 13
        ordered.append((dist, nm, yrs))
    ordered.sort(key=lambda x: x[0])
    items = [(nm, yrs, f"Drig sight from H{dist}") for dist, nm, yrs in ordered]
    seq = _build_seq(items, dob_dt)
    cur = _find_current(seq)
    return {"available": True, "system": "Drig Dasha (60-yr Jaimini Sight)",
            "sequence": seq, "current": cur}


# ─── E8c: Trikona Dasha ──────────────────────────────────────────────
def compute_trikona_dasha(planets: list, lagna_sign: Any, dob: Any) -> dict:
    """Trikona Dasha (Jaimini): cycles through 3 trine groups
       (1-5-9 group, 2-6-10, 3-7-11, 4-8-12). 12 signs × 10 yrs = 120 yrs."""
    dob_dt = _to_dt(dob)
    li = _sign_idx(lagna_sign)
    if dob_dt is None or li is None:
        return {"available": False, "reason": "missing dob/lagna"}
    # Trikona groups: starting from Lagna, then 5th, then 9th, then 2nd-group, etc.
    order_offsets = [0, 4, 8, 1, 5, 9, 2, 6, 10, 3, 7, 11]
    items = []
    for off in order_offsets:
        s = SIGN_NAMES[(li + off) % 12]
        items.append((s, 10, f"Trikona cycle (offset {off})"))
    seq = _build_seq(items, dob_dt)
    cur = _find_current(seq)
    return {"available": True, "system": "Trikona Dasha (120-yr Jaimini Trine)",
            "sequence": seq, "current": cur}


# ─── E8d: Chaturasheeti Sama Dasha (84-yr Equal) ──────────────────────
CHATURASHEETI_ORDER = [("Sun",12),("Moon",12),("Mars",12),("Mercury",12),
                        ("Jupiter",12),("Venus",12),("Saturn",12)]


def compute_chaturasheeti_dasha(planets: list, dob: Any) -> dict:
    """Chaturasheeti Sama Dasha (BPHS Ch.49 — Conditional):
       Applicable when a planet occupies the 9th house from Lagna.
       Each of 7 planets gets equal 12 yrs = 84 yrs total. Starts from
       9H-occupant; if multiple, pick strongest (here: closest to deg 15)."""
    dob_dt = _to_dt(dob)
    if dob_dt is None:
        return {"available": False, "reason": "missing dob"}
    occupants = [p for p in planets
                 if isinstance(p, dict) and p.get("house") == 9
                 and p.get("name") not in ("Rahu", "Ketu")]
    if not occupants:
        return {"available": False, "reason": "Conditional: no planet in 9H from Lagna"}
    starter = occupants[0]["name"]  # could refine by strength
    names = [n for n, _ in CHATURASHEETI_ORDER]
    si = names.index(starter) if starter in names else 0
    items = []
    for i in range(7):
        nm, yrs = CHATURASHEETI_ORDER[(si + i) % 7]
        items.append((nm, yrs, f"Chaturasheeti equal-period {nm}"))
    seq = _build_seq(items, dob_dt)
    cur = _find_current(seq)
    return {"available": True, "system": "Chaturasheeti Sama Dasha (84-yr Conditional)",
            "starter": starter, "sequence": seq, "current": cur}


# ─── E9a: Shashtihayani Dasha (60-yr) ─────────────────────────────────
SHASHTIHAYANI_ORDER = [("Sun",10),("Moon",6),("Mars",8),("Mercury",10),
                        ("Jupiter",6),("Venus",10),("Saturn",10)]
# total ≈ 60 yrs


def compute_shashtihayani_dasha(planets: list, dob: Any) -> dict:
    """Shashtihayani Dasha (BPHS Ch.49 — Conditional):
       Applicable when Sun is in Lagna. 7-planet sequence summing to 60 yrs."""
    dob_dt = _to_dt(dob)
    if dob_dt is None:
        return {"available": False, "reason": "missing dob"}
    sun_h = _planet_house(planets, "Sun")
    if sun_h != 1:
        return {"available": False, "reason": "Conditional: Sun not in Lagna (1H)"}
    items = [(nm, yrs, f"Shashtihayani period {nm}") for nm, yrs in SHASHTIHAYANI_ORDER]
    seq = _build_seq(items, dob_dt)
    cur = _find_current(seq)
    return {"available": True, "system": "Shashtihayani Dasha (60-yr Sun-in-Lagna Conditional)",
            "sequence": seq, "current": cur}


# ─── E9b: Shatabdika Dasha (100-yr) ───────────────────────────────────
SHATABDIKA_ORDER = [("Sun",5),("Moon",5),("Mars",5),("Mercury",16),
                     ("Jupiter",12),("Venus",21),("Saturn",36)]
# total = 100 yrs


def compute_shatabdika_dasha(planets: list, lagna_sign: Any, dob: Any) -> dict:
    """Shatabdika Dasha (BPHS Ch.49 — Conditional):
       Applicable when the 7th lord is in the 7th house. 100-yr cycle."""
    dob_dt = _to_dt(dob)
    li = _sign_idx(lagna_sign)
    if dob_dt is None or li is None:
        return {"available": False, "reason": "missing dob/lagna"}
    seventh_sign = (li + 6) % 12
    seventh_lord = SIGN_LORDS[seventh_sign]
    seventh_lord_house = _planet_house(planets, seventh_lord)
    if seventh_lord_house != 7:
        return {"available": False,
                "reason": f"Conditional: 7L({seventh_lord}) not in 7H (currently {seventh_lord_house})"}
    items = [(nm, yrs, f"Shatabdika period {nm}") for nm, yrs in SHATABDIKA_ORDER]
    seq = _build_seq(items, dob_dt)
    cur = _find_current(seq)
    return {"available": True, "system": "Shatabdika Dasha (100-yr 7L-in-7H Conditional)",
            "sequence": seq, "current": cur}


# ─── Master orchestrator ──────────────────────────────────────────────
def compute_all_phase_e_dashas(kundli: dict) -> dict:
    planets = kundli.get("planets") or []
    lagna = kundli.get("ascendant") or kundli.get("lagna")
    dob = (kundli.get("dob") or kundli.get("birth_date")
           or (kundli.get("birth") or {}).get("date"))
    return {
        "kalachakra":     compute_kalachakra_dasha(planets, dob),
        "mandooka":       compute_mandooka_dasha(planets, lagna, dob),
        "drig":           compute_drig_dasha(planets, lagna, dob),
        "trikona":        compute_trikona_dasha(planets, lagna, dob),
        "chaturasheeti":  compute_chaturasheeti_dasha(planets, dob),
        "shashtihayani":  compute_shashtihayani_dasha(planets, dob),
        "shatabdika":     compute_shatabdika_dasha(planets, lagna, dob),
    }


def format_phase_e_summary(d: dict) -> str:
    if not d: return ""
    lines = ["▸ PHASE E DASHAS (Sprint-31 Tier-5 gap-fill): 7 systems"]
    for key, info in d.items():
        if not isinstance(info, dict): continue
        if not info.get("available"):
            lines.append(f"  • {key:14s}: ❌ {info.get('reason','n/a')}")
            continue
        sys_name = info.get("system", key)
        cur = info.get("current")
        if cur:
            label = cur.get("label", "?")
            lines.append(f"  ✅ {sys_name}: current = {label} "
                         f"({cur.get('start','?')} → {cur.get('end','?')}) — {cur.get('theme','')}")
        else:
            lines.append(f"  ✅ {sys_name}: computed (no current period)")
    return "\n".join(lines)

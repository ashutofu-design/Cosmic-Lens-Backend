"""
Sprint 53-N1 — Numerology Deep (Extended Phase S)
Adds: Lo Shu Grid, Personal Year/Month/Day, Life-Path,
Soul-Urge / Personality / Expression, Master numbers (11/22/33),
Karmic Debt (13/14/16/19), Compound number (Cheiro 10-52).

Pure deterministic — NO AI. Designed to be called from locked_facts.py
right after phase_s. Date input is required for any time-based number.
"""
from __future__ import annotations
from datetime import datetime, date
from typing import Any

# ────────────────────────────────────────────────────────────────────────────
# helpers
# ────────────────────────────────────────────────────────────────────────────
MASTER = {11, 22, 33}
KARMIC_DEBT = {13, 14, 16, 19}

def _digits(s: str) -> list[int]:
    return [int(c) for c in str(s) if c.isdigit()]

def _reduce(n: int, keep_master: bool = True) -> int:
    """Reduce to single digit; if keep_master, stop at 11/22/33."""
    while n > 9:
        if keep_master and n in MASTER:
            return n
        n = sum(_digits(str(n)))
    return n

def _sum_reduce(seq, keep_master: bool = True) -> int:
    return _reduce(sum(seq), keep_master)

def _parse_dob(dob_str: str) -> date | None:
    if not dob_str: return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try: return datetime.strptime(dob_str, fmt).date()
        except Exception: continue
    return None

# Pythagorean alphabet (A=1..I=9, J=1..R=9, S=1..Z=8)
_PYTH = {c: ((i % 9) + 1) for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")}
_VOWELS = set("aeiou")

# ────────────────────────────────────────────────────────────────────────────
# 1. Lo Shu Grid (3×3 magic square) — Indian/Chinese numerology
# ────────────────────────────────────────────────────────────────────────────
LO_SHU_LAYOUT = [[4,9,2],[3,5,7],[8,1,6]]
LO_SHU_MEANING = {
    1:"Career, communication, social skills (Water)",
    2:"Sensitivity, intuition, partnership (Earth)",
    3:"Imagination, creativity, expression (Wood)",
    4:"Discipline, organization, methodical (Wood)",
    5:"Will-power, balance, centre of life (Earth)",
    6:"Family, love, responsibility, beauty (Metal)",
    7:"Reflection, depth, analysis (Metal)",
    8:"Wealth, hard work, justice (Earth)",
    9:"Mental power, intelligence, fame (Fire)",
}
LO_SHU_PLANES = {
    "Mental":   [4,9,2],   # top row
    "Emotional":[3,5,7],   # middle row
    "Practical":[8,1,6],   # bottom row
    "Thought":  [4,3,8],   # left col
    "Will":     [9,5,1],   # middle col
    "Action":   [2,7,6],   # right col
    "Golden-Yellow":[4,5,6],   # diagonal
    "Silver":       [2,5,8],   # anti-diagonal
}

def compute_lo_shu(dob: date) -> dict[str, Any]:
    """Plot DOB digits + driver + conductor + name(?) into 3×3 Lo Shu Grid."""
    nums: list[int] = []
    nums.extend(_digits(dob.strftime("%d%m%Y")))
    # also include driver (day root) + conductor (full root, no master) + kua-style
    driver = _reduce(dob.day, keep_master=False)
    conductor = _reduce(sum(_digits(dob.strftime("%d%m%Y"))), keep_master=False)
    nums.extend([driver, conductor])

    counts = {n: 0 for n in range(1, 10)}
    for n in nums:
        if 1 <= n <= 9:
            counts[n] += 1

    present = [n for n, c in counts.items() if c > 0]
    missing = [n for n, c in counts.items() if c == 0]
    repeated = {n: c for n, c in counts.items() if c >= 2}

    # check planes (all three numbers present = complete plane = strength)
    complete_planes = []
    missing_planes = []
    for plane, trio in LO_SHU_PLANES.items():
        if all(counts[t] > 0 for t in trio):
            complete_planes.append(plane)
        elif all(counts[t] == 0 for t in trio):
            missing_planes.append(plane)

    grid_visual = []
    for row in LO_SHU_LAYOUT:
        line = []
        for n in row:
            line.append(str(n) * counts[n] if counts[n] else "·")
        grid_visual.append(line)

    return {
        "counts": counts,
        "present_numbers": present,
        "missing_numbers": missing,
        "repeated_numbers": repeated,
        "missing_meanings": [
            {"number": n, "missing": LO_SHU_MEANING[n]} for n in missing
        ],
        "repeated_meanings": [
            {"number": n, "count": c, "trait": LO_SHU_MEANING[n]}
            for n, c in repeated.items()
        ],
        "complete_planes": complete_planes,
        "missing_planes": missing_planes,
        "grid_visual": grid_visual,
    }

# ────────────────────────────────────────────────────────────────────────────
# 2. Life-Path (Pythagorean) + Birthday number
# ────────────────────────────────────────────────────────────────────────────
def compute_life_path(dob: date) -> dict[str, Any]:
    """Western Pythagorean: reduce DD + MM + YYYY each separately, then sum."""
    dd = _reduce(dob.day)
    mm = _reduce(dob.month)
    yy = _reduce(dob.year)
    lp = _reduce(dd + mm + yy)
    is_master = lp in MASTER
    return {
        "life_path": lp,
        "is_master": is_master,
        "birthday_number": dob.day,
        "birthday_root": _reduce(dob.day, keep_master=False),
    }

# ────────────────────────────────────────────────────────────────────────────
# 3. Soul Urge / Personality / Expression numbers (from name)
# ────────────────────────────────────────────────────────────────────────────
def compute_name_triad(name: str) -> dict[str, Any]:
    """Pythagorean alphabet — vowels only = Soul Urge,
       consonants only = Personality, all letters = Expression."""
    if not name: return {"available": False}
    letters = [c.lower() for c in name if c.isalpha()]
    if not letters: return {"available": False}
    vowel_sum = sum(_PYTH[c] for c in letters if c in _VOWELS)
    cons_sum  = sum(_PYTH[c] for c in letters if c not in _VOWELS)
    expr_sum  = vowel_sum + cons_sum
    return {
        "available": True,
        "soul_urge": _reduce(vowel_sum) if vowel_sum else None,
        "personality": _reduce(cons_sum) if cons_sum else None,
        "expression": _reduce(expr_sum) if expr_sum else None,
        "alphabet": "Pythagorean (A=1..I=9, J=1..R=9, S=1..Z=8)",
    }

# ────────────────────────────────────────────────────────────────────────────
# 4. Personal Year / Month / Day  (current calendar date)
# ────────────────────────────────────────────────────────────────────────────
PERSONAL_YEAR_THEME = {
    1:"NEW BEGINNINGS — start ventures, plant seeds, leadership year",
    2:"PARTNERSHIP — patience, cooperation, behind-scenes work",
    3:"EXPRESSION — creativity, social, communication, joy",
    4:"FOUNDATION — hard work, structure, discipline, build slowly",
    5:"CHANGE — travel, freedom, unexpected events, restlessness",
    6:"RESPONSIBILITY — family, home, marriage, service",
    7:"INTROSPECTION — study, reflection, solitude, research",
    8:"HARVEST — money, power, recognition, business expansion",
    9:"COMPLETION — endings, letting go, charity, transition year",
}
def compute_personal_cycles(dob: date, today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    # Personal Year: birth-month + birth-day + current-year, all reduced
    py = _reduce(_reduce(dob.month, keep_master=False)
                 + _reduce(dob.day, keep_master=False)
                 + _reduce(today.year, keep_master=False), keep_master=False)
    pm = _reduce(py + _reduce(today.month, keep_master=False), keep_master=False)
    pd = _reduce(pm + _reduce(today.day, keep_master=False), keep_master=False)
    return {
        "as_of": today.isoformat(),
        "personal_year": py,
        "personal_year_theme": PERSONAL_YEAR_THEME.get(py, ""),
        "personal_month": pm,
        "personal_month_theme": PERSONAL_YEAR_THEME.get(pm, ""),
        "personal_day": pd,
        "personal_day_theme": PERSONAL_YEAR_THEME.get(pd, ""),
        "next_year_personal": _reduce(py + 1, keep_master=False),
    }

# ────────────────────────────────────────────────────────────────────────────
# 5. Master Numbers (11, 22, 33) detection
# ────────────────────────────────────────────────────────────────────────────
MASTER_MEANING = {
    11:"Master Intuitive — heightened intuition, inspirational influence, "
       "original ideas. Higher octave of 2.",
    22:"Master Builder — turns visions into reality on grand scale, "
       "architects, founders. Higher octave of 4.",
    33:"Master Teacher — selfless service, deep healing presence, "
       "unconditional care. Rare; higher octave of 6.",
}
def detect_master_numbers(dob: date, name: str) -> dict[str, Any]:
    found = []
    # check raw (un-reduced) sums
    full_dob_sum = sum(_digits(dob.strftime("%d%m%Y")))
    if full_dob_sum in MASTER:
        found.append({"source":"DOB-sum","value":full_dob_sum})

    lp_raw = _reduce(dob.day) + _reduce(dob.month) + _reduce(dob.year)
    if lp_raw in MASTER:
        found.append({"source":"Life-Path","value":lp_raw})

    nt = compute_name_triad(name)
    if nt.get("available"):
        for k in ("soul_urge","personality","expression"):
            v = nt.get(k)
            if v in MASTER:
                found.append({"source":f"Name-{k}","value":v})

    return {
        "has_master": bool(found),
        "occurrences": found,
        "meanings": [{"number":x["value"],"meaning":MASTER_MEANING[x["value"]]}
                     for x in found],
    }

# ────────────────────────────────────────────────────────────────────────────
# 6. Karmic Debt (13, 14, 16, 19)
# ────────────────────────────────────────────────────────────────────────────
KARMIC_MEANING = {
    13:"Hard work without recognition; laziness from past life — must "
       "build foundation through sustained effort",
    14:"Misuse of freedom in past life; learn moderation, adaptability "
       "without indulgence",
    16:"Ego/love-triangle pattern; sudden falls from grace — humility "
       "and inner transformation required",
    19:"Misuse of power/independence; learn to ask for help, "
       "interdependence vs isolation",
}
def detect_karmic_debt(dob: date, name: str) -> dict[str, Any]:
    found = []
    # check raw sums BEFORE final reduction
    candidates = []
    candidates.append(("DOB-sum", sum(_digits(dob.strftime("%d%m%Y")))))
    candidates.append(("Birthday", dob.day))
    nt = compute_name_triad(name)
    if nt.get("available"):
        letters = [c.lower() for c in name if c.isalpha()]
        candidates.append(("Soul-Urge-raw",
                           sum(_PYTH[c] for c in letters if c in _VOWELS)))
        candidates.append(("Personality-raw",
                           sum(_PYTH[c] for c in letters if c not in _VOWELS)))
        candidates.append(("Expression-raw",
                           sum(_PYTH[c] for c in letters)))
    seen = set()
    for src, val in candidates:
        # walk reduction; any intermediate hit on KARMIC_DEBT counts
        v = val
        while v > 9 and v not in MASTER:
            if v in KARMIC_DEBT and (src, v) not in seen:
                found.append({"source":src,"value":v,
                              "meaning":KARMIC_MEANING[v]})
                seen.add((src, v))
            v = sum(_digits(str(v)))
    return {"has_karmic_debt": bool(found), "debts": found}

# ────────────────────────────────────────────────────────────────────────────
# 7. Compound number (Cheiro) — single-digit hides nuance
# ────────────────────────────────────────────────────────────────────────────
CHEIRO_COMPOUND = {
    10:"Wheel of Fortune — honour, faith, self-confidence",
    11:"Hidden trials, treachery from others — needs strong faith",
    12:"Sacrifice, victim of others' plots — caution",
    13:"Upheaval, change, warning — requires great care",
    14:"Movement, dealings with public, lucky in stocks/speculation",
    15:"Influence, eloquence, gift of art — favourable",
    16:"Shattered citadel — accidents, sudden falls — caution",
    17:"Strong overcomer — rises above difficulties — fortunate",
    18:"Bitter quarrels, materialism vs core values — warning",
    19:"Crown of success — happiness, recognition, honour — most fortunate",
    20:"Awakening / Judgement — call to action, new purpose",
    21:"Crown of success — advancement, honour after struggle",
    22:"Master Builder — illusion if unfocused, mastery if focused",
    23:"Royal Lion archetype — promise of help from superiors",
    24:"Help from those of high rank — gain through love & opposite sex",
    25:"Strength gained through experience — wisdom from observation",
    26:"Disastrous partnerships — beware of advice from others",
    27:"Sceptre — courage, command, authority — fortunate",
    28:"Loss through misplaced trust — opposition, contradictions",
    29:"Uncertainty, treachery from friends — grief, deception",
    30:"Thoughtful deduction, mental superiority — neutral",
    31:"Recluse — isolation, lonely, but self-contained",
    32:"Persuasive power — like 23 — fortunate if own counsel kept",
    33:"Same as 24 — favourable",
    34:"Same as 25",
    35:"Same as 26",
    36:"Same as 27 — fortunate",
    37:"Friendship, love, partnerships — fortunate",
    38:"Same as 29 — warning",
    39:"Same as 30",
    40:"Same as 31",
    41:"Same as 32",
    42:"Same as 24",
    43:"Revolution, upheaval, strife, failure — unfortunate",
    44:"Same as 26",
    45:"Same as 27",
    46:"Same as 37 — fortunate",
    47:"Same as 38",
    48:"Same as 39",
    49:"Same as 40",
    50:"Same as 41",
    51:"Nature of warrior — sudden advancement, danger of assassination",
    52:"Same as 43",
}
def compute_compound(dob: date, name: str) -> dict[str, Any]:
    out: dict[str, Any] = {"available": True}
    full = sum(_digits(dob.strftime("%d%m%Y")))
    out["dob_compound"] = full
    out["dob_compound_meaning"] = CHEIRO_COMPOUND.get(full, "Reduces normally")
    if name:
        letters = [c.lower() for c in name if c.isalpha()]
        nm = sum(_PYTH[c] for c in letters)
        out["name_compound"] = nm
        out["name_compound_meaning"] = CHEIRO_COMPOUND.get(nm, "Reduces normally")
    return out

# ────────────────────────────────────────────────────────────────────────────
# Master entry point
# ────────────────────────────────────────────────────────────────────────────
def compute_extended_numerology(birth: dict, today: date | None = None) -> dict[str, Any]:
    dob_str = (birth or {}).get("dob") or (birth or {}).get("date") or ""
    name = (birth or {}).get("name") or ""
    dob = _parse_dob(dob_str)
    if not dob:
        return {"available": False, "reason": "DOB missing/unparseable"}
    return {
        "available": True,
        "dob": dob.isoformat(),
        "name": name or None,
        "lo_shu": compute_lo_shu(dob),
        "life_path": compute_life_path(dob),
        "name_triad": compute_name_triad(name),
        "personal_cycles": compute_personal_cycles(dob, today),
        "master_numbers": detect_master_numbers(dob, name),
        "karmic_debt": detect_karmic_debt(dob, name),
        "compound": compute_compound(dob, name),
    }

# ────────────────────────────────────────────────────────────────────────────
# Formatter for LOCKED FACTS injection
# ────────────────────────────────────────────────────────────────────────────
def format_extended_numerology(r: dict) -> str:
    if not r or not r.get("available"):
        return "▸ NUMEROLOGY DEEP (Sprint 53-N1): ❌ unavailable — " + str(r.get("reason",""))
    L = ["▸ NUMEROLOGY DEEP (Sprint 53-N1) — extended Phase S"]

    # Life Path
    lp = r["life_path"]
    L.append(f"  • Life-Path Number: {lp['life_path']}"
             + (" ⭐ MASTER" if lp["is_master"] else ""))
    L.append(f"  • Birthday Number: {lp['birthday_number']} (root {lp['birthday_root']})")

    # Name triad
    nt = r["name_triad"]
    if nt.get("available"):
        L.append(f"  • Soul-Urge (vowels): {nt['soul_urge']}  "
                 f"Personality (consonants): {nt['personality']}  "
                 f"Expression (full name): {nt['expression']}")
        L.append(f"    ({nt['alphabet']})")
    else:
        L.append("  • Name-triad: ⚠ name not provided")

    # Personal cycles
    pc = r["personal_cycles"]
    L.append(f"  • Personal Year ({pc['as_of'][:4]}): {pc['personal_year']} — "
             f"{pc['personal_year_theme']}")
    L.append(f"    Personal Month: {pc['personal_month']} — {pc['personal_month_theme']}")
    L.append(f"    Personal Day:   {pc['personal_day']} — {pc['personal_day_theme']}")
    L.append(f"    Next year personal: {pc['next_year_personal']}")

    # Master numbers
    mn = r["master_numbers"]
    if mn["has_master"]:
        L.append(f"  • ⭐ MASTER NUMBERS DETECTED ({len(mn['occurrences'])}):")
        for o in mn["occurrences"]:
            L.append(f"      - {o['source']}: {o['value']}")
        for m in mn["meanings"]:
            L.append(f"        ▸ {m['number']}: {m['meaning']}")
    else:
        L.append("  • Master numbers: none detected")

    # Karmic debt
    kd = r["karmic_debt"]
    if kd["has_karmic_debt"]:
        L.append(f"  • ⚠ KARMIC DEBT DETECTED ({len(kd['debts'])}):")
        for d in kd["debts"]:
            L.append(f"      - {d['source']} = {d['value']}: {d['meaning']}")
    else:
        L.append("  • Karmic debt: none detected (clean past-life ledger)")

    # Compound (Cheiro)
    cp = r["compound"]
    L.append(f"  • Cheiro Compound (DOB): {cp['dob_compound']} — {cp['dob_compound_meaning']}")
    if "name_compound" in cp:
        L.append(f"    Cheiro Compound (Name): {cp['name_compound']} — {cp['name_compound_meaning']}")

    # Lo Shu Grid
    ls = r["lo_shu"]
    L.append("  • LO SHU GRID (3×3 magic square — DOB digits + driver + conductor):")
    for row in ls["grid_visual"]:
        L.append(f"        | {row[0]:>5} | {row[1]:>5} | {row[2]:>5} |")
    if ls["missing_numbers"]:
        L.append(f"    Missing numbers: {ls['missing_numbers']}")
        for m in ls["missing_meanings"][:5]:
            L.append(f"      ✗ {m['number']}: lacks {m['missing']}")
    if ls["repeated_meanings"]:
        L.append("    Repeated (excess) numbers:")
        for m in ls["repeated_meanings"]:
            L.append(f"      ↑ {m['number']} (×{m['count']}): {m['trait']}")
    if ls["complete_planes"]:
        L.append(f"    ✅ Complete planes (strength): {ls['complete_planes']}")
    if ls["missing_planes"]:
        L.append(f"    ✗ Missing planes (weakness): {ls['missing_planes']}")

    return "\n".join(L)

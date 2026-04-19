"""
Sprint 44 / Phase S — Numerology + Vastu Integration
S1. Driver (Mulank), Conductor (Bhagyank), Kua number, Name number
S2. House direction analysis (8 directions, planetary lords + element)
S3. Vastu defects calc (planet placements ⇒ direction-specific defects in home)
"""
from __future__ import annotations
from datetime import datetime
from typing import Any

PLANET_BY_NUMBER = {1:"Sun",2:"Moon",3:"Jupiter",4:"Rahu",5:"Mercury",
                     6:"Venus",7:"Ketu",8:"Saturn",9:"Mars"}
NUMBER_NATURE = {
    1:"Leadership, originality, will (Sun)",
    2:"Sensitivity, intuition, partnership (Moon)",
    3:"Wisdom, learning, expansion (Jupiter)",
    4:"Sudden change, foreign, unconventional (Rahu)",
    5:"Communication, business, intellect (Mercury)",
    6:"Beauty, luxury, relationships (Venus)",
    7:"Spirituality, mysticism, isolation (Ketu)",
    8:"Discipline, karma, hard work (Saturn)",
    9:"Energy, courage, action (Mars)",
}
NUMBER_FRIENDS = {
    1:[1,3,5,9], 2:[2,4,7,9], 3:[1,3,5,6,9], 4:[2,4,6,8],
    5:[1,3,5,6,9], 6:[3,4,6,8,9], 7:[2,5,7,9], 8:[4,6,8],
    9:[1,2,3,5,6,9],
}
NUMBER_ENEMIES = {
    1:[8], 2:[1,8], 3:[7,8], 4:[5,9], 5:[2,8], 6:[7],
    7:[1,3,4,6], 8:[1,2,5], 9:[8],
}

# 8 Vastu directions with ruling planet, element & life-domain
DIRECTIONS = [
    ("North",      "Mercury", "Earth", "wealth / cash flow / business deals"),
    ("North-East", "Jupiter", "Water", "spirituality / wisdom / health"),
    ("East",       "Sun",     "Air",   "fame / power / authority / father"),
    ("South-East", "Venus",   "Fire",  "kitchen / digestion / romance"),
    ("South",      "Mars",    "Fire",  "stability / fame / property"),
    ("South-West", "Rahu",    "Earth", "ancestors / responsibility / master bedroom"),
    ("West",       "Saturn",  "Water", "children / gains / future / dining"),
    ("North-West", "Moon",    "Air",   "relationships / guests / movement"),
]

# Kua number: women: (year_sum + 4) mod 9; men: (11 - year_sum) mod 9. 0 → 9.
def _digit_sum(n: int) -> int:
    s = sum(int(d) for d in str(abs(n)))
    while s > 9 and s not in (11, 22):  # keep master numbers
        s = sum(int(d) for d in str(s))
    return s

def _root(n: int) -> int:
    while n > 9: n = sum(int(d) for d in str(n))
    return n

def _kua(year: int, gender: str) -> int | None:
    yr_sum = _root(_digit_sum(year))
    g = (gender or "").lower()
    if g.startswith("m"):
        k = (11 - yr_sum) % 9
    elif g.startswith("f") or g.startswith("w"):
        k = (yr_sum + 4) % 9
    else:
        return None
    return k if k != 0 else 9

KUA_DIRECTION_GROUP = {
    1:"East",  3:"East",  4:"East",  9:"East",     # East-group
    2:"West",  5:"West",  6:"West",  7:"West",  8:"West",  # West-group
}
KUA_BEST_4 = {
    1:["South-East","East","South","North"],
    3:["South","North","South-East","East"],
    4:["North","South","East","South-East"],
    9:["East","South-East","North","South"],
    2:["North-East","West","North-West","South-West"],
    5:["North-East","West","North-West","South-West"],
    6:["West","North-East","South-West","North-West"],
    7:["North-West","South-West","North-East","West"],
    8:["South-West","North-West","West","North-East"],
}

# S3 — Vastu defects rules: which house being weak/afflicted ⇒ which direction-defect.
# Maps house in chart → corresponding home direction (per Vastu Purusha Mandala).
HOUSE_TO_DIRECTION = {
    1:"East", 2:"South-East", 3:"South", 4:"South-West",
    5:"South-West", 6:"West", 7:"West", 8:"North-West",
    9:"North-East", 10:"North", 11:"North-East", 12:"North-East",
}


def _name_number(name: str) -> int | None:
    if not name: return None
    # Chaldean simplified mapping
    M = {"a":1,"b":2,"c":3,"d":4,"e":5,"f":8,"g":3,"h":5,"i":1,"j":1,
         "k":2,"l":3,"m":4,"n":5,"o":7,"p":8,"q":1,"r":2,"s":3,"t":4,
         "u":6,"v":6,"w":6,"x":5,"y":1,"z":7}
    s = sum(M.get(c.lower(), 0) for c in name if c.isalpha())
    return _root(s) if s else None


def compute_phase_s(kundli: dict, birth: dict) -> dict[str, Any]:
    dob = birth.get("dob") or birth.get("date") or kundli.get("dob")
    name = birth.get("name") or kundli.get("name") or ""
    gender = birth.get("gender") or kundli.get("gender") or ""

    out: dict[str, Any] = {"available": True}

    # S1 — Driver / Conductor / Kua / Name number
    driver = conductor = kua = name_num = None
    if isinstance(dob, str):
        try:
            d = datetime.strptime(dob, "%Y-%m-%d")
        except Exception:
            try: d = datetime.strptime(dob, "%d-%m-%Y")
            except Exception: d = None
        if d:
            driver = _root(d.day)  # Mulank
            full = sum(int(c) for c in dob if c.isdigit())
            conductor = _root(full)  # Bhagyank
            kua = _kua(d.year, gender)
    if name:
        name_num = _name_number(name)

    s1 = {"driver_mulank": driver, "conductor_bhagyank": conductor,
          "kua_number": kua, "name_number": name_num,
          "driver_planet": PLANET_BY_NUMBER.get(driver) if driver else None,
          "conductor_planet": PLANET_BY_NUMBER.get(conductor) if conductor else None,
          "name_planet": PLANET_BY_NUMBER.get(name_num) if name_num else None,
          "driver_nature": NUMBER_NATURE.get(driver) if driver else None,
          "conductor_nature": NUMBER_NATURE.get(conductor) if conductor else None,
          "kua_group": KUA_DIRECTION_GROUP.get(kua) if kua else None,
          "kua_best_4_directions": KUA_BEST_4.get(kua, []) if kua else [],
          "driver_friend_numbers": NUMBER_FRIENDS.get(driver, []) if driver else [],
          "driver_enemy_numbers": NUMBER_ENEMIES.get(driver, []) if driver else [],
          "compatibility_driver_conductor":
            "HARMONIOUS" if (driver and conductor and conductor in NUMBER_FRIENDS.get(driver, []))
            else ("CONFLICT" if (driver and conductor and conductor in NUMBER_ENEMIES.get(driver, []))
                  else "NEUTRAL")
          }
    out["s1_numbers"] = s1

    # S2 — House direction analysis (always available)
    out["s2_directions"] = [
        {"direction": d, "ruler": p, "element": el, "life_domain": dom}
        for d, p, el, dom in DIRECTIONS
    ]

    # S3 — Vastu defects: detect afflicted houses → flag directional defects
    planets = kundli.get("planets") or []
    lag = kundli.get("ascendant") or kundli.get("lagna")
    SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                  "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    try: lagna_si = SIGN_NAMES.index(lag)
    except Exception: lagna_si = 0
    p_in_h: dict[int, list[str]] = {h: [] for h in range(1,13)}
    for p in planets:
        lon = p.get("longitude")
        if not isinstance(lon, (int, float)): continue
        si = int(lon // 30) % 12
        h = ((si - lagna_si) % 12) + 1
        p_in_h[h].append(p["name"])

    MALEFICS = {"Saturn","Mars","Rahu","Ketu","Sun"}
    defects = []
    for h, plist in p_in_h.items():
        afflicted = [p for p in plist if p in MALEFICS]
        if not afflicted: continue
        direction = HOUSE_TO_DIRECTION.get(h)
        if not direction: continue
        defect_type = []
        if "Mars" in afflicted: defect_type.append("Fire defect (electrical/fire-risk in this zone)")
        if "Saturn" in afflicted: defect_type.append("Vayu defect (decay/blockage/dampness)")
        if "Rahu" in afflicted: defect_type.append("Akasha defect (confusion/foreign influence)")
        if "Ketu" in afflicted: defect_type.append("Cut/missing-corner defect")
        if "Sun" in afflicted: defect_type.append("Excess heat/dryness")
        defects.append({
            "house": h, "direction": direction,
            "afflicting_planets": afflicted,
            "defects": defect_type,
            "remedy_zone": f"Strengthen {direction} zone of home"
        })

    out["s3_vastu_defects"] = {"count": len(defects), "defects": defects}

    return out


def format_phase_s(r: dict) -> str:
    if not r or not r.get("available"):
        return "▸ PHASE S NUMEROLOGY+VASTU: ❌ unavailable"
    s = r["s1_numbers"]
    L = ["▸ PHASE S NUMEROLOGY + VASTU INTEGRATION (Sprint-44)",
         "  S1 NUMEROLOGY (Driver / Conductor / Kua / Name):"]
    if s["driver_mulank"]:
        L.append(f"      ▪ Driver (Mulank, from DOB-day): {s['driver_mulank']} → "
                 f"{s['driver_planet']} — {s['driver_nature']}")
    if s["conductor_bhagyank"]:
        L.append(f"      ▪ Conductor (Bhagyank, from full DOB): {s['conductor_bhagyank']} → "
                 f"{s['conductor_planet']} — {s['conductor_nature']}")
    if s["name_number"]:
        L.append(f"      ▪ Name number: {s['name_number']} → {s['name_planet']}")
    if s["kua_number"]:
        L.append(f"      ▪ Kua number: {s['kua_number']} → {s['kua_group']}-group")
        L.append(f"        Best 4 directions for living/sleeping: "
                 f"{', '.join(s['kua_best_4_directions'])}")
    if s["driver_mulank"]:
        L.append(f"      ▪ Driver friends: {s['driver_friend_numbers']}; "
                 f"enemies: {s['driver_enemy_numbers']}")
        L.append(f"      ▪ Driver↔Conductor compatibility: {s['compatibility_driver_conductor']}")

    L.append("  S2 HOUSE DIRECTIONS (Vastu Purusha Mandala — 8 zones):")
    for d in r["s2_directions"]:
        L.append(f"      ▪ {d['direction']:<11} → ruler {d['ruler']:<8} "
                 f"element {d['element']:<5} domain: {d['life_domain']}")

    df = r["s3_vastu_defects"]
    L.append(f"  S3 VASTU DEFECTS (chart-derived) — {df['count']} zone(s) affected:")
    if not df["defects"]:
        L.append("      ▪ No major chart-derived Vastu defects detected")
    else:
        for x in df["defects"]:
            L.append(f"      ⚠ H{x['house']} → {x['direction']} zone "
                     f"(afflicted by {', '.join(x['afflicting_planets'])})")
            for dt in x["defects"]:
                L.append(f"           • {dt}")
            L.append(f"           ▸ {x['remedy_zone']}")
    return "\n".join(L)

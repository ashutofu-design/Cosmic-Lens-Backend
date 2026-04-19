"""
Sprint 45 — ASTRO VASTU ENGINE (Full)
A comprehensive chart-driven Vastu analyzer.

Checks performed:
  V1.  9 zones (8 directions + Brahmasthan center) — ruler, element, strength
  V2. 16 Mahavastu sub-zones (each direction split into 2)
  V3. Pancha Mahabhuta (5-element) balance from chart
  V4. Room-wise placement audit (12 rooms ideal vs worst direction)
  V5. Main entry door direction analysis (from Lagna-lord & 4th-lord)
  V6. Per-planet direction strength (using shadbala if present)
  V7. Personal favorable directions (Kua + 4th-lord placement)
  V8. Color & gemstone remedies per affected zone
  V9. Vedha (obstruction) detection on N-S / E-W axes
  V10. Plot-shape recommendation from elemental dominance
  V11. Brahmasthan (centre) status from 5th & 9th lord strength
  V12. 16 classical Vastu Doshas — chart-trigger detection
  V13. Direction-wise full report card (current state + remedy)
"""
from __future__ import annotations
from typing import Any
from datetime import datetime

SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
              "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_LORDS = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
              "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]
SIGN_ELEMENT = ["Fire","Earth","Air","Water","Fire","Earth",
                "Air","Water","Fire","Earth","Air","Water"]

# 9 Zones — 8 directions + Brahmasthan
NINE_ZONES = [
    ("North",      "Mercury", "Earth",  "wealth, cash flow, business deals"),
    ("North-East", "Jupiter", "Water",  "spirituality, wisdom, health, pooja"),
    ("East",       "Sun",     "Air",    "fame, authority, father, sunrise"),
    ("South-East", "Venus",   "Fire",   "kitchen, digestion, romance, fire"),
    ("South",      "Mars",    "Fire",   "stability, fame, property, courage"),
    ("South-West", "Rahu",    "Earth",  "ancestors, master bedroom, stability"),
    ("West",       "Saturn",  "Water",  "children, gains, future, dining"),
    ("North-West", "Moon",    "Air",    "relationships, guests, movement, women"),
    ("Brahmasthan","Brahma",  "Akasha", "centre — must be EMPTY & open"),
]

# 16 Mahavastu sub-zones (Mahavastu by Khushdeep Bansal style)
SIXTEEN_ZONES = [
    ("N1 North-of-NW",  "Friends, mind, support"),
    ("N2 North",        "Career opportunities"),
    ("N3 North-of-NE",  "Immunity, healing"),
    ("E1 East-of-NE",   "Clarity, new ideas"),
    ("E2 East",         "Fame, social image"),
    ("E3 East-of-SE",   "Confidence, energy"),
    ("S1 South-of-SE",  "Cash flow, expression"),
    ("S2 South",        "Recognition, name"),
    ("S3 South-of-SW",  "Conviction, stability"),
    ("W1 West-of-SW",   "Education, skills, depth"),
    ("W2 West",         "Profits, savings"),
    ("W3 West-of-NW",   "Sex, depression risk"),
    ("NE corner",       "Spiritual gains"),
    ("SE corner",       "Wealth, kitchen fire"),
    ("SW corner",       "Power, masters of house"),
    ("NW corner",       "Marriage of girls, attachments"),
]

# Room → ideal direction + worst direction
ROOM_RULES = [
    ("Main entry door",   ["North","East","North-East"],          ["South-West","South","South-East"]),
    ("Pooja / temple",    ["North-East"],                          ["South","South-West","West"]),
    ("Kitchen",           ["South-East"],                          ["North-East","North","North-West"]),
    ("Master bedroom",    ["South-West"],                          ["North-East","South-East"]),
    ("Children bedroom",  ["West","North-West"],                   ["South-West","South-East"]),
    ("Guest bedroom",     ["North-West"],                          ["South-West","North-East"]),
    ("Toilet",            ["North-West","West"],                   ["North-East","South-West","Centre"]),
    ("Bathroom",          ["East","North-West"],                   ["North-East","South-West"]),
    ("Study room",        ["North-East","East","North"],           ["South","South-West"]),
    ("Dining",            ["West","North-West","East"],            ["South-West"]),
    ("Living room",       ["North","East","North-East"],           ["South-West"]),
    ("Cash locker / safe","South-West (door opens North)"
                          and ["South-West"],                       ["South-East","North-East"]),
    ("Staircase",         ["South","West","South-West"],           ["North-East","Centre"]),
    ("Septic tank",       ["North-West"],                          ["North-East","South-West","Centre"]),
    ("Borewell / well",   ["North-East","North","East"],           ["South-West","South","South-East"]),
]

# 16 Classical Vastu Doshas
VASTU_DOSHAS = [
    ("NE-cut dosha",       "Loss of wealth, infertility, weak health",
        lambda h: "Ketu" in h.get(12,[]) or "Saturn" in h.get(12,[])),
    ("SW-extension dosha", "Instability of head of family, ancestral debts",
        lambda h: "Mars" in h.get(4,[]) and "Saturn" in h.get(4,[])),
    ("SE-water dosha",     "Fire accidents, marital tension, miscarriage",
        lambda h: "Moon" in h.get(2,[]) or "Venus" in h.get(8,[])),
    ("NW-fire dosha",      "Conflicts with women, friend losses",
        lambda h: "Mars" in h.get(8,[]) or "Sun" in h.get(8,[])),
    ("Brahmasthan-heavy",  "Chronic illness, mental restlessness, family disputes",
        lambda h: any(p in h.get(5,[]) for p in ["Saturn","Rahu","Ketu","Mars"])),
    ("South-light dosha",  "Loss of fame, weak immunity, money outflow",
        lambda h: not h.get(3) and not h.get(4)),
    ("North-blocked dosha","Cash-flow blockage, career stagnation",
        lambda h: "Saturn" in h.get(11,[]) or "Rahu" in h.get(11,[])),
    ("East-blocked dosha", "Father issues, lack of recognition",
        lambda h: "Saturn" in h.get(1,[]) or "Rahu" in h.get(1,[])),
    ("West-toilet dosha",  "Children disrespect, future blocked",
        lambda h: "Ketu" in h.get(7,[]) or "Saturn" in h.get(7,[])),
    ("Door-axis dosha",    "Energy conflict (Pranic clash on N-S or E-W)",
        lambda h: any(p in h.get(1,[]) for p in ["Rahu","Ketu"])),
    ("Toilet-NE dosha",    "Severe wealth loss, spiritual blockage",
        lambda h: "Mars" in h.get(12,[]) and "Ketu" in h.get(12,[])),
    ("Kitchen-NE dosha",   "Anxiety, scattered energy, women's health",
        lambda h: "Sun" in h.get(12,[]) or "Mars" in h.get(12,[])),
    ("Bedroom-SE dosha",   "Insomnia, hyper-activity, anger",
        lambda h: "Mars" in h.get(2,[])),
    ("Sloping-floor dosha","Money rolls out, instability",
        lambda h: "Saturn" in h.get(2,[]) and "Saturn" in h.get(11,[])),
    ("Mirror-bedroom dosha","Marital strife, restless sleep",
        lambda h: "Venus" in h.get(8,[])),
    ("Beam-overhead dosha","Headaches, oppressive thoughts, blocked decisions",
        lambda h: "Saturn" in h.get(1,[])),
]

# Direction → recommended colours
DIR_COLORS = {
    "North":      ["Green","Black (sparingly)"],
    "North-East": ["Yellow","Light blue","White"],
    "East":       ["White","Light blue","Light green"],
    "South-East": ["Red","Pink","Orange","Silver"],
    "South":      ["Red","Coral","Pink"],
    "South-West": ["Earthy brown","Beige","Light yellow"],
    "West":       ["White","Grey","Silver"],
    "North-West": ["White","Off-white","Cream","Grey"],
    "Brahmasthan":["White","Ivory","Empty / no clutter"],
}
DIR_REMEDY_GEM = {
    "Mercury":"Emerald (Panna)", "Jupiter":"Yellow Sapphire (Pukhraj)",
    "Sun":"Ruby (Manik)", "Venus":"Diamond (Heera)",
    "Mars":"Red Coral (Moonga)", "Rahu":"Hessonite (Gomedh)",
    "Saturn":"Blue Sapphire (Neelam)", "Moon":"Pearl (Moti)",
    "Ketu":"Cat's Eye (Lehsunia)",
}

# Kua best-4 (used by V7) — same as Phase S table
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

HOUSE_TO_DIRECTION = {
    1:"East", 2:"South-East", 3:"South", 4:"South-West",
    5:"South-West", 6:"West", 7:"West", 8:"North-West",
    9:"North-East", 10:"North", 11:"North-East", 12:"North-East",
}

# 16 sub-zones of chart (30° / 1.875° each) — used by V2 mapping
def _sub_zone_index(deg_in_sign: float) -> int:
    return int(deg_in_sign // (30.0 / 16))


# ─── helpers ────────────────────────────────────────────────────────────────
def _root(n: int) -> int:
    n = abs(n)
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n

def _kua(year: int, gender: str) -> int | None:
    yr = _root(sum(int(c) for c in str(year)))
    g = (gender or "").lower()
    if g.startswith("m"): k = (11 - yr) % 9
    elif g.startswith(("f","w")): k = (yr + 4) % 9
    else: return None
    return k or 9


# ─── main engine ───────────────────────────────────────────────────────────
def run_astro_vastu_engine(kundli: dict, birth: dict | None = None,
                            shadbala: dict | None = None) -> dict[str, Any]:
    birth = birth or {}
    out: dict[str, Any] = {"available": True, "checks_run": 13}

    planets = kundli.get("planets") or []
    lag = kundli.get("ascendant") or kundli.get("lagna") or "Aries"
    try: lagna_si = SIGN_NAMES.index(lag)
    except Exception: lagna_si = 0

    # Build house → planet list
    p_in_h: dict[int, list[str]] = {h: [] for h in range(1,13)}
    p_si: dict[str, int] = {}
    p_lon: dict[str, float] = {}
    for p in planets:
        lon = p.get("longitude")
        if not isinstance(lon, (int, float)): continue
        si = int(lon // 30) % 12
        h = ((si - lagna_si) % 12) + 1
        p_in_h[h].append(p["name"])
        p_si[p["name"]] = si
        p_lon[p["name"]] = lon

    # ── V1 — 9 zones with chart-strength of ruler ──
    sb_total = {}
    if isinstance(shadbala, dict):
        for k, v in (shadbala.get("planets") or shadbala or {}).items():
            if isinstance(v, dict):
                t = v.get("total_rupas") or v.get("total") or v.get("rupas")
                if isinstance(t, (int, float)): sb_total[k] = float(t)

    v1 = []
    for d, ruler, el, dom in NINE_ZONES:
        ruler_house = None; ruler_status = "neutral"
        for h, pl in p_in_h.items():
            if ruler in pl: ruler_house = h; break
        if ruler_house in (1,4,7,10,5,9): ruler_status = "STRONG"
        elif ruler_house in (6,8,12):       ruler_status = "WEAK"
        zone_strength = sb_total.get(ruler)
        v1.append({
            "direction": d, "ruler": ruler, "element": el, "domain": dom,
            "ruler_in_house": ruler_house, "ruler_status": ruler_status,
            "shadbala_rupas": round(zone_strength,2) if zone_strength else None,
        })

    # ── V2 — 16 mahavastu sub-zones — Moon's longitude marks user's prime sub-zone ──
    moon_zone = None
    if "Moon" in p_lon:
        deg_in_sign = p_lon["Moon"] % 30
        idx = _sub_zone_index(deg_in_sign) % 16
        moon_zone = SIXTEEN_ZONES[idx]

    # ── V3 — Pancha Mahabhuta balance ──
    elem_count = {"Fire":0,"Earth":0,"Air":0,"Water":0,"Akasha":0}
    for name, si in p_si.items():
        if name in ("Rahu","Ketu"): continue
        elem_count[SIGN_ELEMENT[si]] += 1
    # Akasha proxy = empty kendra count (1,4,7,10)
    elem_count["Akasha"] = sum(1 for h in (1,4,7,10) if not p_in_h[h])
    dominant_el = max(elem_count, key=elem_count.get)
    weakest_el = min(elem_count, key=elem_count.get)

    # ── V4 — Room placement audit (recommendations only) ──
    v4 = []
    for room, ideal, worst in ROOM_RULES:
        v4.append({"room": room, "ideal": ideal if isinstance(ideal,list) else [ideal],
                   "worst": worst})

    # ── V5 — Main entry door direction (Lagna-lord & 4th-lord placement) ──
    lord_lag = SIGN_LORDS[lagna_si]
    lord_4 = SIGN_LORDS[(lagna_si + 3) % 12]
    door_pref = []
    for L in (lord_lag, lord_4):
        if L in p_si:
            si = p_si[L]; house = ((si - lagna_si) % 12) + 1
            door_pref.append(HOUSE_TO_DIRECTION.get(house, "?"))
    door_recommend = list({d for d in door_pref if d in
        ("North","East","North-East","West")}) or ["North","East","North-East"]

    v5 = {"lagna_lord": lord_lag, "fourth_lord": lord_4,
          "lord_directions": door_pref,
          "recommended_door_directions": door_recommend,
          "avoid_doors_facing": ["South","South-West","South-East"]}

    # ── V6 — direction strength per planet (uses shadbala if available) ──
    v6 = []
    for d, ruler, el, _ in NINE_ZONES[:8]:
        rupas = sb_total.get(ruler)
        rating = ("STRONG" if rupas and rupas >= 6 else
                  "WEAK"   if rupas and rupas <= 4 else "MODERATE")
        v6.append({"direction": d, "ruler": ruler,
                   "rupas": round(rupas,2) if rupas else None, "rating": rating})

    # ── V7 — personal favourable directions (Kua + 4th-lord placement) ──
    kua = None
    dob = birth.get("dob")
    if isinstance(dob, str):
        try:
            yr = datetime.strptime(dob, "%Y-%m-%d").year
        except Exception:
            try: yr = datetime.strptime(dob, "%d-%m-%Y").year
            except Exception: yr = None
        if yr: kua = _kua(yr, birth.get("gender","") or "")
    v7 = {
        "kua_number": kua,
        "kua_best_4_directions": KUA_BEST_4.get(kua, []) if kua else [],
        "lagna_lord_dir": v5["lord_directions"][0] if v5["lord_directions"] else None,
        "fourth_lord_dir": v5["lord_directions"][1] if len(v5["lord_directions"])>1 else None,
    }

    # ── V8 — colour & gem remedies for each direction ──
    v8 = []
    for d, ruler, el, _ in NINE_ZONES:
        v8.append({"direction": d, "colors": DIR_COLORS.get(d, []),
                   "remedy_gem_for_ruler": DIR_REMEDY_GEM.get(ruler)})

    # ── V9 — Vedha (axis obstruction) ──
    vedha = []
    for axis_name, h_a, h_b in [("North-South axis (H10↔H4)",10,4),
                                 ("East-West axis (H1↔H7)",1,7)]:
        m_a = [p for p in p_in_h[h_a] if p in ("Saturn","Rahu","Ketu","Mars")]
        m_b = [p for p in p_in_h[h_b] if p in ("Saturn","Rahu","Ketu","Mars")]
        if m_a or m_b:
            vedha.append({"axis": axis_name, "blockers_house_a": m_a,
                          "blockers_house_b": m_b,
                          "impact":"Pranic flow blocked — energy stagnates"})

    # ── V10 — plot-shape recommendation ──
    PLOT = {
        "Fire":  "Square plot, slightly extended in South-East",
        "Earth": "Square or rectangular, extended South-West (avoid NE-cut)",
        "Air":   "Rectangle longer East-West, NW friendly",
        "Water": "Square with extension toward North-East",
        "Akasha":"Perfect square, open courtyard preferred",
    }
    v10 = {"dominant_element": dominant_el,
           "weakest_element": weakest_el,
           "recommended_plot_shape": PLOT.get(dominant_el),
           "avoid_shape": "Triangular, irregular, NE-cut, or SW-cut"}

    # ── V11 — Brahmasthan status (5th & 9th lord) ──
    lord_5 = SIGN_LORDS[(lagna_si + 4) % 12]
    lord_9 = SIGN_LORDS[(lagna_si + 8) % 12]
    rupas_5 = sb_total.get(lord_5); rupas_9 = sb_total.get(lord_9)
    avg = ((rupas_5 or 5) + (rupas_9 or 5)) / 2
    centre_state = ("PURE" if avg >= 6 else "POLLUTED" if avg <= 4 else "MODERATE")
    v11 = {"fifth_lord": lord_5, "ninth_lord": lord_9,
           "average_strength_rupas": round(avg,2),
           "brahmasthan_state": centre_state,
           "rule":"Centre must be empty, well-lit, white/ivory, no clutter, no toilet, no staircase"}

    # ── V12 — 16 vastu doshas — chart-trigger ──
    triggered = []
    for name, impact, fn in VASTU_DOSHAS:
        try:
            if fn(p_in_h):
                triggered.append({"dosha": name, "impact": impact})
        except Exception: pass

    # ── V13 — direction-wise final report card ──
    v13 = []
    for z in v1:
        defects_here = [d for d in (vedha or [])
                         if z["direction"] in d.get("axis","")]
        v13.append({
            "direction": z["direction"], "ruler": z["ruler"],
            "ruler_status": z["ruler_status"],
            "rupas": z["shadbala_rupas"],
            "dominant_room": next((r["room"] for r in v4
                                    if z["direction"] in r["ideal"]), None),
            "colors": DIR_COLORS.get(z["direction"], []),
            "axis_blocked": bool(defects_here),
        })

    out.update({
        "v1_nine_zones": v1,
        "v2_mahavastu_moon_zone": moon_zone,
        "v2_sixteen_zones": SIXTEEN_ZONES,
        "v3_pancha_mahabhuta": {
            "counts": elem_count, "dominant": dominant_el, "weakest": weakest_el,
        },
        "v4_room_audit": v4,
        "v5_main_entry": v5,
        "v6_direction_strength": v6,
        "v7_personal_favourable": v7,
        "v8_color_gem_remedies": v8,
        "v9_vedha_obstructions": vedha,
        "v10_plot_shape": v10,
        "v11_brahmasthan": v11,
        "v12_doshas_triggered": {"count": len(triggered), "list": triggered},
        "v13_direction_report_card": v13,
    })
    return out


def format_astro_vastu(r: dict) -> str:
    if not r or not r.get("available"):
        return "▸ ASTRO-VASTU ENGINE: ❌ unavailable"
    L = ["▸ ASTRO-VASTU ENGINE — FULL CHART-DRIVEN AUDIT (Sprint-45) — 13 checks"]

    # V1
    L.append("  V1 NINE ZONES (8 directions + Brahmasthan):")
    for z in r["v1_nine_zones"]:
        rup = f" • shadbala={z['shadbala_rupas']}r" if z["shadbala_rupas"] else ""
        L.append(f"      ▪ {z['direction']:<11} ruler {z['ruler']:<8} "
                 f"({z['element']:<6}) — ruler-house H{z['ruler_in_house']} "
                 f"[{z['ruler_status']}]{rup} • {z['domain']}")

    # V2
    if r["v2_mahavastu_moon_zone"]:
        z = r["v2_mahavastu_moon_zone"]
        L.append(f"  V2 MAHAVASTU SUB-ZONE (Moon-mapped) → {z[0]} — {z[1]}")
        L.append(f"      ▪ All 16 sub-zones available in engine output")

    # V3
    e = r["v3_pancha_mahabhuta"]
    L.append(f"  V3 PANCHA-MAHABHUTA balance: {e['counts']}")
    L.append(f"      ▪ Dominant element: {e['dominant']}  •  Weakest element: {e['weakest']}")

    # V4
    L.append("  V4 ROOM-PLACEMENT AUDIT (15 rooms ideal vs avoid directions):")
    for rm in r["v4_room_audit"][:8]:
        L.append(f"      ▪ {rm['room']:<22} ideal: {', '.join(rm['ideal'])}  "
                 f"AVOID: {', '.join(rm['worst'])}")
    L.append(f"      ▪ ... (+{len(r['v4_room_audit'])-8} more rooms)")

    # V5
    v5 = r["v5_main_entry"]
    L.append(f"  V5 MAIN ENTRY DOOR — Lagna-lord {v5['lagna_lord']} & 4th-lord {v5['fourth_lord']}")
    L.append(f"      ▪ Lord-derived directions: {v5['lord_directions']}")
    L.append(f"      ▪ Recommended door-facing: {', '.join(v5['recommended_door_directions'])}")
    L.append(f"      ▪ Avoid door-facing: {', '.join(v5['avoid_doors_facing'])}")

    # V6
    L.append("  V6 DIRECTION STRENGTH per planet (shadbala-driven):")
    for x in r["v6_direction_strength"]:
        rup = f"{x['rupas']}r" if x["rupas"] else "no-shadbala"
        L.append(f"      ▪ {x['direction']:<11} ({x['ruler']:<8}) → {x['rating']:<8} ({rup})")

    # V7
    v7 = r["v7_personal_favourable"]
    if v7["kua_number"]:
        L.append(f"  V7 PERSONAL FAVOURABLE — Kua {v7['kua_number']} → "
                 f"{', '.join(v7['kua_best_4_directions'])}")
        L.append(f"      ▪ Lagna-lord direction: {v7['lagna_lord_dir']}  •  "
                 f"4th-lord direction: {v7['fourth_lord_dir']}")

    # V8
    L.append("  V8 COLOR & GEM REMEDIES per direction:")
    for x in r["v8_color_gem_remedies"]:
        L.append(f"      ▪ {x['direction']:<11} colors: {', '.join(x['colors'])}  "
                 f"• gem-for-ruler: {x['remedy_gem_for_ruler']}")

    # V9
    if r["v9_vedha_obstructions"]:
        L.append(f"  V9 VEDHA AXIS OBSTRUCTIONS — {len(r['v9_vedha_obstructions'])}:")
        for v in r["v9_vedha_obstructions"]:
            L.append(f"      ⚠ {v['axis']} — {v['impact']}")
            L.append(f"           blockers: {v['blockers_house_a']} ↔ {v['blockers_house_b']}")
    else:
        L.append("  V9 VEDHA OBSTRUCTIONS: ✅ none on N-S or E-W axis")

    # V10
    p = r["v10_plot_shape"]
    L.append(f"  V10 PLOT SHAPE — dominant element {p['dominant_element']} → {p['recommended_plot_shape']}")
    L.append(f"      ▪ Avoid: {p['avoid_shape']}")

    # V11
    b = r["v11_brahmasthan"]
    L.append(f"  V11 BRAHMASTHAN — 5th-lord {b['fifth_lord']} + 9th-lord {b['ninth_lord']} "
             f"= {b['average_strength_rupas']}r → {b['brahmasthan_state']}")
    L.append(f"      ▪ {b['rule']}")

    # V12
    d = r["v12_doshas_triggered"]
    L.append(f"  V12 16 VASTU DOSHAS — {d['count']} TRIGGERED in chart:")
    if d["list"]:
        for x in d["list"]:
            L.append(f"      ⚠ {x['dosha']} — {x['impact']}")
    else:
        L.append("      ▪ No classical doshas detected ✅")

    # V13
    L.append("  V13 DIRECTION-WISE REPORT CARD:")
    for x in r["v13_direction_report_card"]:
        ax = " AXIS-BLOCKED" if x["axis_blocked"] else ""
        rm = f" (room: {x['dominant_room']})" if x["dominant_room"] else ""
        L.append(f"      ▪ {x['direction']:<11} → {x['ruler_status']:<8}{rm}{ax}  "
                 f"colors: {', '.join(x['colors'][:2])}")
    return "\n".join(L)

"""
Sprint 50 — ASTROCARTOGRAPHY ENGINE  (Tier-1 Mundane + Tier-2 Lines)

Classical astrocartography draws MC/IC/Asc/Desc lines per planet across
the world map (needs precise lat+long+time). For users without coords we
provide TIER-1 mundane rulership (planet→country/region) which is fully
deterministic and immediately useful. When coords are present we compute
TIER-2 angular lines.

10 sections (G1-G10):
  G1  Best countries for THIS chart (benefic-strong planets)
  G2  Avoid countries (afflicted-planet rulership)
  G3  Career-purpose × location matching
  G4  Domain-specific picks (love/wealth/fame/spirituality/health)
  G5  Lucky directions from birthplace (N/S/E/W/NE/NW/SE/SW)
  G6  Indian state/city recommendations
  G7  City-archetype matching
  G8  Best dasha window for relocation
  G9  Tier-2 precise MC/IC/Asc/Desc lines (only if coords supplied)
  G10 Disclaimer
"""
from __future__ import annotations
from typing import Any

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_LORDS = {0:"Mars",1:"Venus",2:"Mercury",3:"Moon",4:"Sun",5:"Mercury",
              6:"Venus",7:"Mars",8:"Jupiter",9:"Saturn",10:"Saturn",11:"Jupiter"}
BENEFICS = {"Jupiter","Venus","Mercury","Moon"}
MALEFICS = {"Saturn","Mars","Sun","Rahu","Ketu"}

DISCLAIMER = (
    "  ⚠  RELOCATION DISCLAIMER  ⚠\n"
    "    Astrocartography shows energetic affinity, NOT guaranteed luck.\n"
    "    Real-world factors (visa, jobs, family, language) matter equally.\n"
    "    Tier-1 below uses classical mundane rulership; Tier-2 (precise lines)\n"
    "    requires birth coordinates (lat+long+time) — supply for upgrade."
)

# ─── PLANET → COUNTRY/REGION rulership (classical mundane astrology) ──────
PLANET_COUNTRIES = {
    "Sun": {
        "primary":   ["France","Italy","USA (Washington DC)","Switzerland","Romania"],
        "secondary": ["Czech Republic","Lebanon","Sicily","Bohemia"],
        "energy":    "Authority, leadership, political power, gold, performance",
        "best_for":  "Politics, government roles, brand-building, public speaking",
    },
    "Moon": {
        "primary":   ["Netherlands","Mumbai","Amsterdam","Iceland","New Zealand"],
        "secondary": ["Holland","Manchester","Cambodia","Venice"],
        "energy":    "Public connection, hospitality, water-bodies, emotional resonance",
        "best_for":  "Hospitality, F&B, content/media, mass-public businesses",
    },
    "Mars": {
        "primary":   ["Israel","South Korea","Japan (defence cities)","Saudi Arabia","Norway"],
        "secondary": ["Syria","Lower Germany","Sheffield","Kanpur"],
        "energy":    "Action, military, real-estate, sports, engineering, defence-tech",
        "best_for":  "Defence/security, eSports, real-estate flipping, surgery, athletics",
    },
    "Mercury": {
        "primary":   ["USA (NYC, SF)","Singapore","Hong Kong","Bengaluru","Switzerland (Geneva)"],
        "secondary": ["Belgium","Cairo","London (City)","Tokyo"],
        "energy":    "Trade, communication, technology, finance, writing",
        "best_for":  "Tech/SaaS, stock trading, journalism, copywriting, AI, research",
    },
    "Jupiter": {
        "primary":   ["Spain","India (Varanasi/Rishikesh)","Hungary","Bali","Ireland"],
        "secondary": ["Babylon (Iraq)","Pune","Kolkata","Stockholm"],
        "energy":    "Wisdom, expansion, teaching, spirituality, finance-advisory",
        "best_for":  "Teaching, online courses, ed-tech, financial advisory, philanthropy",
    },
    "Venus": {
        "primary":   ["France (Paris)","Italy","UAE (Dubai)","Brazil","Austria (Vienna)"],
        "secondary": ["Goa","Lisbon","Copenhagen","Polynesia"],
        "energy":    "Beauty, luxury, art, romance, fashion, hospitality-luxury",
        "best_for":  "Influencer, fashion, beauty brand, luxury export, music/arts",
    },
    "Saturn": {
        "primary":   ["Germany","UK (industrial)","Sweden","Bhutan","South Africa"],
        "secondary": ["Bavaria","Russia (Moscow)","Edinburgh","Detroit"],
        "energy":    "Discipline, long-haul, mining, infrastructure, anti-aging",
        "best_for":  "Long-form startup, EV/solar, mining, biotech, monastic life",
    },
    "Rahu": {
        "primary":   ["UAE","Hong Kong","USA (Silicon Valley)","Australia","Foreign-tech hubs"],
        "secondary": ["Las Vegas","Macau","Crypto-zones (Estonia, Switzerland)"],
        "energy":    "Foreign, unconventional, viral, crypto, technology, immigration",
        "best_for":  "Crypto, NFT, viral content, foreign tech jobs, digital nomadism",
    },
    "Ketu": {
        "primary":   ["Tibet","Nepal","Bhutan","Bali","Thailand","India (Rishikesh, Tiruvannamalai)"],
        "secondary": ["Kashi","Vipassana centres","Ashram zones"],
        "energy":    "Spiritual, monastic, healing, occult, isolation, moksha",
        "best_for":  "Healing, meditation-app, monk life, alternative medicine, retreat owner",
    },
}

# ─── INDIAN states/cities by planet ───────────────────────────────────────
INDIAN_LOCATIONS = {
    "Sun":     ["Delhi","Lucknow","Jaipur","Punjab"],
    "Moon":    ["Mumbai","Kolkata","Kerala (backwaters)","Goa coast"],
    "Mars":    ["Kanpur","Ahmedabad","Pune (defence)","Nagpur"],
    "Mercury": ["Bengaluru","Hyderabad","Pune (IT)","Chennai (tech)","Gurugram"],
    "Jupiter": ["Varanasi","Rishikesh","Pune","Kolkata"],
    "Venus":   ["Goa","Mumbai (luxury)","Jaipur","Udaipur"],
    "Saturn":  ["Jharkhand","Chhattisgarh","Mining belts","Bhilai"],
    "Rahu":    ["Mumbai (tech)","Bengaluru (startup)","Pune (foreign)","Delhi NCR"],
    "Ketu":    ["Rishikesh","Tiruvannamalai","Auroville","Dharamshala"],
}

# ─── CITY ARCHETYPES ──────────────────────────────────────────────────────
CITY_ARCHETYPES = {
    "Cosmopolitan-tech":  ["NYC","SF","Bengaluru","Singapore","Tokyo","Berlin"],
    "Spiritual":          ["Rishikesh","Varanasi","Bali","Kyoto","Sedona","Kathmandu"],
    "Luxury-creative":    ["Paris","Milan","Dubai","LA","Goa","Lisbon"],
    "Research-academic":  ["Boston","Oxford","Heidelberg","Bengaluru","Geneva","Tokyo"],
    "Long-haul-builder":  ["Berlin","Stockholm","Zurich","Tokyo","Singapore"],
    "Foreign-viral-tech": ["Dubai","SF","Estonia","Singapore","Toronto","Sydney"],
    "Healing-wellness":   ["Rishikesh","Bali","Sedona","Tulum","Costa Rica","Bhutan"],
}

# ─── DOMAINS → driving planet ─────────────────────────────────────────────
DOMAIN_PLANETS = {
    "Love/Marriage":   "Venus",
    "Wealth/Business": "Jupiter",
    "Fame/Politics":   "Sun",
    "Spirituality":    "Ketu",
    "Health/Sports":   "Mars",
    "Career/Tech":     "Mercury",
    "Long-haul/Discipline": "Saturn",
    "Foreign/Viral":   "Rahu",
    "Family/Hospitality": "Moon",
}

# ─── 8 DIRECTIONS (Lal Kitab / Vastu) → planet ────────────────────────────
DIRECTION_PLANETS = {
    "East":       ("Sun","wealth, authority, government work"),
    "South-East": ("Venus","luxury, romance, creative"),
    "South":      ("Mars","action, real-estate, sports"),
    "South-West": ("Rahu/Ketu","foreign, transformation, occult"),
    "West":       ("Saturn","long-term builds, retirement, monastic"),
    "North-West": ("Moon","public, hospitality, F&B"),
    "North":      ("Mercury","tech, trade, learning, finance"),
    "North-East": ("Jupiter","wisdom, teaching, spiritual"),
}


def _planet_houses(planets: list, lagna_si: int) -> dict:
    out = {}
    for p in planets:
        lon = p.get("longitude")
        if not isinstance(lon,(int,float)): continue
        si = int(lon // 30) % 12
        h = ((si - lagna_si) % 12) + 1
        out[p["name"]] = {"si": si, "h": h, "sign": SIGNS[si]}
    return out


def _planet_strength_score(p_data: dict) -> dict:
    """Quick 0-10 strength score per planet from house placement."""
    scores = {}
    for p, d in p_data.items():
        h = d["h"]; si = d["si"]
        s = 5  # base
        if h in (1,4,5,7,9,10,11): s += 2
        if h in (6,8,12):           s -= 2
        # own/exalted bonus
        own = SIGN_LORDS.get(si) == p
        if own: s += 2
        # exaltation rough
        EXALT = {"Sun":0,"Moon":1,"Mars":9,"Mercury":5,"Jupiter":3,"Venus":11,"Saturn":6}
        if EXALT.get(p) == si: s += 2
        DEBIL = {"Sun":6,"Moon":7,"Mars":3,"Mercury":11,"Jupiter":9,"Venus":5,"Saturn":0}
        if DEBIL.get(p) == si: s -= 2
        scores[p] = max(0, min(10, s))
    return scores


def run_astrocartography(kundli: dict, birth: dict | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"available": True, "disclaimer": DISCLAIMER, "tier": 1}
    planets = kundli.get("planets") or []
    lag = kundli.get("ascendant") or kundli.get("lagna") or "Aries"
    try: lagna_si = SIGNS.index(lag)
    except Exception: lagna_si = 0

    p_data = _planet_houses(planets, lagna_si)
    if not p_data:
        out["available"] = False; return out

    strengths = _planet_strength_score(p_data)

    # ─── G1: Best countries (top-3 strong benefics + lagna lord) ──────────
    lagna_lord = SIGN_LORDS[lagna_si]
    boost_planets = sorted(strengths.items(), key=lambda x: -x[1])
    top_3_strong = [p for p,s in boost_planets if s >= 6 and p != "Rahu" and p != "Ketu"][:3]
    if lagna_lord not in top_3_strong and lagna_lord in PLANET_COUNTRIES:
        top_3_strong.insert(0, lagna_lord)

    g1 = []
    for p in top_3_strong[:4]:
        info = PLANET_COUNTRIES.get(p, {})
        if info:
            g1.append({
                "planet": p, "strength": strengths.get(p,5),
                "primary_countries": info["primary"],
                "secondary_countries": info["secondary"],
                "energy": info["energy"],
                "best_for": info["best_for"],
            })

    # ─── G2: Avoid countries (afflicted planet rulership) ────────────────
    weak = [p for p,s in strengths.items() if s <= 3 and p in PLANET_COUNTRIES]
    g2 = []
    for p in weak[:3]:
        info = PLANET_COUNTRIES.get(p, {})
        if info:
            g2.append({
                "planet": p, "strength": strengths.get(p,5),
                "caution_countries": info["primary"][:3],
                "reason": f"{p} weak in chart — avoid prolonged stays here unless remedied",
            })

    # ─── G3: Career-purpose × location ───────────────────────────────────
    g3 = []
    for domain, planet in DOMAIN_PLANETS.items():
        info = PLANET_COUNTRIES.get(planet, {})
        if info:
            g3.append({
                "domain": domain, "ruling_planet": planet,
                "your_strength_here": strengths.get(planet,5),
                "top_locations": info["primary"][:3],
            })

    # ─── G4: Domain-specific picks ───────────────────────────────────────
    g4 = {}
    for domain, planet in DOMAIN_PLANETS.items():
        info = PLANET_COUNTRIES.get(planet, {})
        if info:
            g4[domain] = {
                "best_country": info["primary"][0] if info["primary"] else "—",
                "city_archetype": info["best_for"],
                "your_planet_strength": strengths.get(planet,5),
            }

    # ─── G5: Lucky directions from birthplace ────────────────────────────
    g5 = []
    for direction, (planet_label, meaning) in DIRECTION_PLANETS.items():
        first_planet = planet_label.split("/")[0]
        s = strengths.get(first_planet, 5)
        verdict = "LUCKY" if s >= 6 else ("NEUTRAL" if s >= 4 else "WEAK")
        g5.append({"direction": direction, "ruling_planet": planet_label,
                   "meaning": meaning, "strength_score": s, "verdict": verdict})

    # ─── G6: Indian state/city recommendations ───────────────────────────
    g6 = []
    for p in top_3_strong[:3]:
        cities = INDIAN_LOCATIONS.get(p, [])
        if cities:
            g6.append({"planet": p, "indian_cities": cities})

    # ─── G7: City archetype matching ─────────────────────────────────────
    g7 = []
    if "Mercury" in top_3_strong or strengths.get("Mercury",5) >= 6:
        g7.append(("Cosmopolitan-tech", CITY_ARCHETYPES["Cosmopolitan-tech"]))
    if "Ketu" in top_3_strong or strengths.get("Ketu",5) >= 6 or strengths.get("Jupiter",5) >= 7:
        g7.append(("Spiritual", CITY_ARCHETYPES["Spiritual"]))
    if "Venus" in top_3_strong or strengths.get("Venus",5) >= 6:
        g7.append(("Luxury-creative", CITY_ARCHETYPES["Luxury-creative"]))
    if "Jupiter" in top_3_strong or strengths.get("Jupiter",5) >= 6:
        g7.append(("Research-academic", CITY_ARCHETYPES["Research-academic"]))
    if "Saturn" in top_3_strong or strengths.get("Saturn",5) >= 6:
        g7.append(("Long-haul-builder", CITY_ARCHETYPES["Long-haul-builder"]))
    if "Rahu" in p_data and p_data["Rahu"]["h"] in (1,9,10,11):
        g7.append(("Foreign-viral-tech", CITY_ARCHETYPES["Foreign-viral-tech"]))
    if not g7:
        g7.append(("Healing-wellness", CITY_ARCHETYPES["Healing-wellness"]))

    # ─── G8: Best dasha window for relocation ────────────────────────────
    g8 = "Relocate during a STRONG dasha (Jupiter/Venus/own-house lord MD or AD); avoid Rahu MD for permanent moves unless to a Rahu-ruled foreign tech hub"
    cur_md = (kundli.get("vimshottari") or {}).get("current") or {}
    md_lord = cur_md.get("mahadasha_lord") or cur_md.get("md_lord")
    if md_lord:
        info = PLANET_COUNTRIES.get(md_lord, {})
        if info:
            g8 += f"\n      Current MD lord = {md_lord} → favours: {', '.join(info['primary'][:3])}"

    # ─── G9: Tier-2 precise lines (only if coords) ───────────────────────
    g9 = None
    if birth and isinstance(birth.get("lat"),(int,float)) and isinstance(birth.get("lon"),(int,float)):
        # Stub for future Swiss-Eph MC/IC line computation
        g9 = {
            "tier": 2,
            "note": "Tier-2 precise MC/IC/Asc/Desc lines computation available — supply UTC time too for full upgrade.",
            "supplied_lat": birth.get("lat"),
            "supplied_lon": birth.get("lon"),
        }
    else:
        g9 = {"tier": 2, "status": "PENDING — supply birth lat+long+UTC time for precise planetary lines"}

    out.update({
        "g1_best_countries": g1,
        "g2_avoid_countries": g2,
        "g3_career_locations": g3,
        "g4_domain_picks": g4,
        "g5_lucky_directions": g5,
        "g6_indian_cities": g6,
        "g7_city_archetypes": g7,
        "g8_relocation_window": g8,
        "g9_tier2_lines": g9,
        "planet_strengths": strengths,
    })
    return out


def format_astrocartography(r: dict) -> str:
    if not r or not r.get("available"):
        return "▸ ASTROCARTOGRAPHY ENGINE: ❌ unavailable"
    L = ["▸ ASTROCARTOGRAPHY ENGINE — Sprint-50 (Tier-1 Mundane + Tier-2 Lines)",
         r["disclaimer"], "  " + "═"*78]

    L.append("  ⚐ Planet-strength snapshot (0-10):")
    for p,s in r["planet_strengths"].items():
        L.append(f"      ▪ {p:<8} → {s:>2}/10")

    L.append("  G1 BEST COUNTRIES (your strong planets):")
    for x in r["g1_best_countries"]:
        L.append(f"      ━━━ {x['planet']} (strength {x['strength']}/10) ━━━")
        L.append(f"          🌍 Primary:    {', '.join(x['primary_countries'])}")
        L.append(f"          🌍 Secondary:  {', '.join(x['secondary_countries'])}")
        L.append(f"          ⚡ Energy:     {x['energy']}")
        L.append(f"          🎯 Best for:   {x['best_for']}")

    L.append("  G2 CAUTION COUNTRIES (your weak planets):")
    if r["g2_avoid_countries"]:
        for x in r["g2_avoid_countries"]:
            L.append(f"      ▪ {x['planet']} (strength {x['strength']}/10) → caution: {', '.join(x['caution_countries'])}")
            L.append(f"           ⚐ {x['reason']}")
    else:
        L.append("      ▪ No notably weak planets — most regions energetically open")

    L.append("  G3 CAREER-PURPOSE × LOCATION:")
    for x in r["g3_career_locations"]:
        L.append(f"      ▪ {x['domain']:<22} ({x['ruling_planet']:<7} str {x['your_strength_here']}/10) → {', '.join(x['top_locations'])}")

    L.append("  G4 DOMAIN-SPECIFIC PICKS:")
    for domain, info in r["g4_domain_picks"].items():
        L.append(f"      ▪ {domain:<22} → {info['best_country']:<25} (your-{info['your_planet_strength']}/10)  •  {info['city_archetype']}")

    L.append("  G5 LUCKY DIRECTIONS from birthplace (8-direction Vastu):")
    for x in r["g5_lucky_directions"]:
        L.append(f"      ▪ {x['direction']:<12} ({x['ruling_planet']:<10}) → [{x['verdict']:<7}] {x['meaning']}")

    L.append("  G6 INDIAN CITY recommendations (your strong planets):")
    for x in r["g6_indian_cities"]:
        L.append(f"      ▪ {x['planet']:<8} → {', '.join(x['indian_cities'])}")

    L.append("  G7 CITY-ARCHETYPE matches for THIS chart:")
    for arch, cities in r["g7_city_archetypes"]:
        L.append(f"      ▪ {arch:<22} → {', '.join(cities)}")

    L.append(f"  G8 RELOCATION TIMING (dasha-aware):")
    for line in r["g8_relocation_window"].split("\n"):
        L.append(f"      ▸ {line.strip()}")

    L.append("  G9 TIER-2 PRECISE PLANETARY LINES:")
    g9 = r["g9_tier2_lines"]
    if g9.get("status"):
        L.append(f"      ⏳ {g9['status']}")
    else:
        L.append(f"      ✅ {g9.get('note','—')}  (lat={g9.get('supplied_lat')}, lon={g9.get('supplied_lon')})")

    return "\n".join(L)

"""
Sprint 53-N2 — Numerology Practical
Adds: Pinnacles & Challenges (4+4 life cycles),
Mobile / Vehicle / House number checker,
Couple compatibility (Driver↔Driver, LP↔LP),
Career numerology (best professions per number),
Lucky color / gemstone / metal / day / direction (full catalog).

All deterministic. Designed for daily-use questions.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Any

# ── helpers (mirror extended.py to stay self-contained) ──────────────────
MASTER = {11, 22, 33}
def _digits(s: str) -> list[int]:
    return [int(c) for c in str(s) if c.isdigit()]
def _reduce(n: int, keep_master: bool = False) -> int:
    while n > 9:
        if keep_master and n in MASTER: return n
        n = sum(_digits(str(n)))
    return n
def _parse_dob(s: str) -> date | None:
    if not s: return None
    for fmt in ("%Y-%m-%d","%d-%m-%Y","%d/%m/%Y","%Y/%m/%d"):
        try: return datetime.strptime(s, fmt).date()
        except Exception: continue
    return None

# ── 1. Pinnacles & Challenges (Pythagorean) ──────────────────────────────
PINNACLE_THEME = {
    1:"Independence, leadership, self-reliance",
    2:"Cooperation, partnerships, sensitivity",
    3:"Creative expression, social, communication",
    4:"Hard work, foundation, building",
    5:"Freedom, change, versatility",
    6:"Family, responsibility, service",
    7:"Spirituality, study, introspection",
    8:"Material success, power, recognition",
    9:"Humanitarianism, completion, wisdom",
    11:"Spiritual illumination (master pinnacle)",
    22:"Master building on grand scale",
    33:"Master teaching/healing",
}
CHALLENGE_THEME = {
    0:"No specific challenge — use full power of life-path",
    1:"Avoid dependence; learn to stand alone, decide independently",
    2:"Hyper-sensitivity; learn detachment, don't take things personally",
    3:"Self-doubt about creativity; express yourself without fear",
    4:"Rigidity / overwork; learn flexibility and rest",
    5:"Restlessness / addictions; learn discipline and commitment",
    6:"Over-responsibility; let others carry their own load",
    7:"Isolation / cynicism; trust life and people",
    8:"Money obsession or fear of power; balance material+spiritual",
}
def compute_pinnacles_challenges(dob: date) -> dict[str, Any]:
    """Pythagorean: 4 pinnacles + 4 challenges driven by reduced day/month/year."""
    m = _reduce(dob.month); d = _reduce(dob.day); y = _reduce(dob.year)
    lp = _reduce(m + d + y)
    # Pinnacle ages: 1st = until (36 - LP), then 9-year periods
    p1_end = 36 - lp
    pin = [
        ("1st Pinnacle", f"birth – age {p1_end}",       _reduce(m + d, keep_master=True)),
        ("2nd Pinnacle", f"age {p1_end+1} – {p1_end+9}", _reduce(d + y, keep_master=True)),
        ("3rd Pinnacle", f"age {p1_end+10} – {p1_end+18}", _reduce(_reduce(m+d) + _reduce(d+y), keep_master=True)),
        ("4th Pinnacle", f"age {p1_end+19} – end",      _reduce(m + y, keep_master=True)),
    ]
    chl = [
        ("1st Challenge", f"birth – age {p1_end}",       abs(_reduce(m) - _reduce(d))),
        ("2nd Challenge", f"age {p1_end+1} – {p1_end+9}", abs(_reduce(d) - _reduce(y))),
        ("3rd Challenge", f"age {p1_end+10} – {p1_end+18}", abs(abs(_reduce(m)-_reduce(d)) - abs(_reduce(d)-_reduce(y)))),
        ("4th Challenge", f"age {p1_end+19} – end",      abs(_reduce(m) - _reduce(y))),
    ]
    return {
        "life_path": lp,
        "pinnacles": [{"name":n,"period":p,"number":num,
                       "theme":PINNACLE_THEME.get(num,"")} for n,p,num in pin],
        "challenges": [{"name":n,"period":p,"number":num,
                        "theme":CHALLENGE_THEME.get(num,"")} for n,p,num in chl],
    }

# ── 2. Mobile / Vehicle / House number checker ───────────────────────────
NUMBER_DAILY_USE = {
    1:"Excellent for leadership, business owners, govt servants. "
      "Strong for fame; weak if you avoid spotlight.",
    2:"Excellent for partnerships, women, artists, water-business. "
      "Avoid for solo entrepreneurs.",
    3:"Excellent for teachers, lawyers, advisors, religious work. "
      "Lucky for finance and writing.",
    4:"Mixed — sudden gains/losses; good for tech, electrical, foreign trade. "
      "Avoid if you want stability.",
    5:"Excellent universal number — communication, business, sales, travel. "
      "Lucky for almost everyone.",
    6:"Excellent for luxury, beauty, art, hospitality, women. "
      "Brings comfort and harmony.",
    7:"Mixed — spiritual, research, isolation. Good for writers/scientists. "
      "Avoid for material business.",
    8:"Heavy — only for Saturn-aligned (Capricorn/Aquarius) or driver-8. "
      "Brings hard karma to others.",
    9:"Excellent for warriors, athletes, surgeons, defence. "
      "Energetic, fiery; avoid if peace-seeker.",
}
def check_number(any_number: str | int, driver: int | None = None,
                 conductor: int | None = None) -> dict[str, Any]:
    """Check a mobile / vehicle / house / account number."""
    s = str(any_number)
    digits = _digits(s)
    if not digits:
        return {"available": False, "reason":"no digits in input"}
    full_sum = sum(digits)
    last4_sum = sum(digits[-4:]) if len(digits) >= 4 else full_sum
    final = _reduce(full_sum)
    last4_final = _reduce(last4_sum)

    verdict = "NEUTRAL"
    reason = []
    if driver:
        from .phase_s import NUMBER_FRIENDS, NUMBER_ENEMIES
        if final in NUMBER_FRIENDS.get(driver, []):
            verdict = "GOOD"
            reason.append(f"Final {final} is friend of your Driver {driver}")
        elif final in NUMBER_ENEMIES.get(driver, []):
            verdict = "AVOID"
            reason.append(f"Final {final} is enemy of your Driver {driver}")
    if conductor and conductor != driver:
        from .phase_s import NUMBER_FRIENDS, NUMBER_ENEMIES
        if final in NUMBER_ENEMIES.get(conductor, []):
            if verdict == "GOOD": verdict = "MIXED"
            elif verdict == "NEUTRAL": verdict = "CAUTION"
            reason.append(f"Final {final} is enemy of Conductor {conductor}")

    return {
        "available": True,
        "input": s,
        "digit_sum": full_sum,
        "last4_sum": last4_sum,
        "final_number": final,
        "last4_final": last4_final,
        "vibration": NUMBER_DAILY_USE.get(final, ""),
        "verdict": verdict,
        "reason": reason or ["No driver/conductor reference — generic vibration only"],
    }

# ── 3. Couple compatibility ──────────────────────────────────────────────
def compute_couple_compat(p1_birth: dict, p2_birth: dict) -> dict[str, Any]:
    d1 = _parse_dob((p1_birth or {}).get("dob",""))
    d2 = _parse_dob((p2_birth or {}).get("dob",""))
    if not d1 or not d2:
        return {"available": False, "reason":"Both DOBs required"}
    from .phase_s import NUMBER_FRIENDS, NUMBER_ENEMIES, PLANET_BY_NUMBER
    drv1, drv2 = _reduce(d1.day), _reduce(d2.day)
    cond1 = _reduce(sum(_digits(d1.strftime("%d%m%Y"))))
    cond2 = _reduce(sum(_digits(d2.strftime("%d%m%Y"))))
    lp1 = _reduce(_reduce(d1.month)+_reduce(d1.day)+_reduce(d1.year))
    lp2 = _reduce(_reduce(d2.month)+_reduce(d2.day)+_reduce(d2.year))

    def rate(a, b):
        if a in NUMBER_FRIENDS.get(b, []) or b in NUMBER_FRIENDS.get(a, []):
            return "HARMONIOUS"
        if a in NUMBER_ENEMIES.get(b, []) or b in NUMBER_ENEMIES.get(a, []):
            return "CONFLICT"
        return "NEUTRAL"

    matches = {
        "driver_match": {"p1":drv1,"p2":drv2,"verdict":rate(drv1,drv2)},
        "conductor_match": {"p1":cond1,"p2":cond2,"verdict":rate(cond1,cond2)},
        "life_path_match": {"p1":lp1,"p2":lp2,"verdict":rate(lp1,lp2)},
    }
    score = sum(2 if m["verdict"]=="HARMONIOUS" else (-1 if m["verdict"]=="CONFLICT" else 0)
                for m in matches.values())
    overall = ("EXCELLENT" if score >= 4 else
               "GOOD" if score >= 2 else
               "AVERAGE" if score >= 0 else "CHALLENGING")
    return {
        "available": True,
        "p1_planet": PLANET_BY_NUMBER.get(drv1),
        "p2_planet": PLANET_BY_NUMBER.get(drv2),
        "matches": matches,
        "raw_score": score,
        "overall": overall,
    }

# ── 4. Career numerology ─────────────────────────────────────────────────
CAREER_BY_NUMBER = {
    1:["Government / IAS / IPS","CEO / founder","Politics","Gold/diamond trade",
       "Surgery","Architecture","Defence officer"],
    2:["Hospitality","Dairy / liquid business","Nursing","HR / counselling",
       "Travel / shipping","Pearl / silver trade","Diplomacy"],
    3:["Teaching / professor","Law / advocacy","Banking / finance","Religious vocation",
       "Publishing / writing","Astrology / Vedic studies","Yellow-metal trade"],
    4:["IT / electronics","Aviation / pilot","Foreign trade","Stock market / crypto",
       "Research / scientist","Photography / film","Tech startup"],
    5:["Sales / marketing","Media / journalism","Stock broking","Content creator",
       "Consulting","Travel agency","Public relations"],
    6:["Fashion / beauty","Hotels / restaurants","Interior design","Jewellery",
       "Cosmetics","Music / arts","Wedding industry"],
    7:["Spiritual teacher","Research / professor","Writing / philosophy",
       "Marine / navy","Medicine (alternative)","Astronomy","Counselling"],
    8:["Iron / steel / coal","Real estate","Mining","Heavy machinery",
       "Insurance","Court / judiciary","Long-haul logistics"],
    9:["Defence / army","Police / security","Sports","Surgery",
       "Manufacturing","Engineering","Real-estate development"],
}

# ── 5. Lucky catalog (color, gem, metal, day, direction, mantra) ────────
LUCKY_CATALOG = {
    1:{"colors":["Gold","Orange","Yellow"],"gems":["Ruby","Red Garnet"],
       "metal":"Gold","days":["Sunday"],"directions":["East"],
       "mantra":"Om Suryaya Namah","ishta":"Surya / Vishnu",
       "fast_day":"Sunday","number_dates":[1,10,19,28]},
    2:{"colors":["White","Cream","Silver","Pale Green"],"gems":["Pearl","Moonstone"],
       "metal":"Silver","days":["Monday","Friday"],"directions":["North-West"],
       "mantra":"Om Chandraya Namah","ishta":"Shiva / Durga",
       "fast_day":"Monday","number_dates":[2,11,20,29]},
    3:{"colors":["Yellow","Saffron","Pink"],"gems":["Yellow Sapphire","Topaz"],
       "metal":"Gold","days":["Thursday"],"directions":["North-East"],
       "mantra":"Om Brihaspataye Namah","ishta":"Vishnu / Brihaspati",
       "fast_day":"Thursday","number_dates":[3,12,21,30]},
    4:{"colors":["Blue","Grey","Khaki","Electric blue"],"gems":["Hessonite (Gomed)"],
       "metal":"Mixed alloy","days":["Saturday","Wednesday"],"directions":["South-West"],
       "mantra":"Om Rahave Namah","ishta":"Durga / Bhairava",
       "fast_day":"Saturday","number_dates":[4,13,22,31]},
    5:{"colors":["Green","Light grey","White"],"gems":["Emerald","Peridot"],
       "metal":"Brass","days":["Wednesday"],"directions":["North"],
       "mantra":"Om Budhaya Namah","ishta":"Vishnu (Krishna form)",
       "fast_day":"Wednesday","number_dates":[5,14,23]},
    6:{"colors":["White","Pink","Light blue","Pastels"],"gems":["Diamond","White Sapphire","Opal"],
       "metal":"Silver / Platinum","days":["Friday"],"directions":["South-East"],
       "mantra":"Om Shukraya Namah","ishta":"Lakshmi / Mahalakshmi",
       "fast_day":"Friday","number_dates":[6,15,24]},
    7:{"colors":["Sea green","Pale yellow","Off-white"],"gems":["Cat's Eye (Lehsunia)"],
       "metal":"Mixed / iron","days":["Tuesday","Sunday"],"directions":["South-West"],
       "mantra":"Om Ketave Namah","ishta":"Ganesha / Hanuman",
       "fast_day":"Tuesday","number_dates":[7,16,25]},
    8:{"colors":["Black","Dark blue","Purple","Brown"],"gems":["Blue Sapphire","Amethyst"],
       "metal":"Iron","days":["Saturday"],"directions":["West"],
       "mantra":"Om Shanaye Namah","ishta":"Shani / Hanuman",
       "fast_day":"Saturday","number_dates":[8,17,26]},
    9:{"colors":["Red","Crimson","Pink","Maroon"],"gems":["Red Coral (Moonga)"],
       "metal":"Copper","days":["Tuesday"],"directions":["South"],
       "mantra":"Om Mangalaya Namah","ishta":"Hanuman / Kartikeya",
       "fast_day":"Tuesday","number_dates":[9,18,27]},
}

# ── Master entry point ───────────────────────────────────────────────────
def compute_practical(birth: dict) -> dict[str, Any]:
    dob = _parse_dob((birth or {}).get("dob",""))
    if not dob: return {"available": False, "reason":"DOB missing"}
    drv = _reduce(dob.day)
    cond = _reduce(sum(_digits(dob.strftime("%d%m%Y"))))
    return {
        "available": True,
        "driver": drv,
        "conductor": cond,
        "pinnacles_challenges": compute_pinnacles_challenges(dob),
        "career_recommendations_driver": CAREER_BY_NUMBER.get(drv, []),
        "career_recommendations_conductor": CAREER_BY_NUMBER.get(cond, []),
        "lucky_for_driver": LUCKY_CATALOG.get(drv, {}),
        "lucky_for_conductor": LUCKY_CATALOG.get(cond, {}),
    }

# ── Formatter ────────────────────────────────────────────────────────────
def format_practical(r: dict) -> str:
    if not r or not r.get("available"):
        return "▸ NUMEROLOGY PRACTICAL (Sprint 53-N2): ❌ unavailable"
    L = ["▸ NUMEROLOGY PRACTICAL (Sprint 53-N2)"]

    pc = r["pinnacles_challenges"]
    L.append(f"  • Life-Path: {pc['life_path']}")
    L.append("  • PINNACLES (4 life cycles):")
    for p in pc["pinnacles"]:
        L.append(f"      ▪ {p['name']:<13} ({p['period']:<22}) → {p['number']}: {p['theme']}")
    L.append("  • CHALLENGES (4 life cycles):")
    for c in pc["challenges"]:
        L.append(f"      ▪ {c['name']:<13} ({c['period']:<22}) → {c['number']}: {c['theme']}")

    L.append(f"  • CAREER FIT (Driver {r['driver']}):")
    for c in r["career_recommendations_driver"]:
        L.append(f"      ▪ {c}")
    if r["conductor"] != r["driver"]:
        L.append(f"  • CAREER FIT (Conductor {r['conductor']}):")
        for c in r["career_recommendations_conductor"]:
            L.append(f"      ▪ {c}")

    lk = r["lucky_for_driver"]
    if lk:
        L.append(f"  • LUCKY CATALOG (Driver {r['driver']}):")
        L.append(f"      Colors: {', '.join(lk['colors'])}")
        L.append(f"      Gems: {', '.join(lk['gems'])}")
        L.append(f"      Metal: {lk['metal']}    Days: {', '.join(lk['days'])}")
        L.append(f"      Directions: {', '.join(lk['directions'])}    "
                 f"Lucky dates: {lk['number_dates']}")
        L.append(f"      Mantra: {lk['mantra']}    Ishta-devata: {lk['ishta']}")
        L.append(f"      Fast on: {lk['fast_day']}")

    return "\n".join(L)

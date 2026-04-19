"""
Sprint 20 — Tier 4 Doshas Deep (BPHS-precise)
==============================================
Folder-organized deep dosha detection — fills gaps left by dosh_engine.py.

Detectors:
  1. Mangal Dosh full BPHS (1/2/4/7/8/12 + 8 cancellation rules)
  2. Pitra Dosh — 3 BPHS reasons (Sun-Rahu, 9L afflicted, Sun in 9 with Sat)
  3. Sade-Sati phase deep (Rising / Peak / Setting based on Sat vs Moon-sign)
  4. Kantaka Shani (Saturn currently in 1/4/7/10 from natal Moon)
  5. Vish Yog deep (Sat+Moon close conjunction or aspect)
  6. Nadi Dosh self-marker (Nakshatra-Nadi: Aadi/Madhya/Antya)
  7. Karaka Doshas: Matri (Moon), Putra (Jupiter), Bhratri (Mars),
                    Chandra (Moon affliction), Guru (Jupiter affliction),
                    Shukra (Venus affliction)
  8. Grahan Dosh deep (Sun/Moon with Rahu/Ketu within close orb)
  9. Shrapit Dosh deep (Sat+Rahu+Ketu nodal axis)
"""
from __future__ import annotations

from typing import Any, Optional

SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
              "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_LORDS = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
              "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]
EXALT = {"Sun":0,"Moon":1,"Mars":9,"Mercury":5,"Jupiter":3,"Venus":11,"Saturn":6}
DEBIL = {p:(s+6)%12 for p,s in EXALT.items()}
OWN = {"Sun":[4],"Moon":[3],"Mars":[0,7],"Mercury":[2,5],
       "Jupiter":[8,11],"Venus":[1,6],"Saturn":[9,10]}

# Nakshatra → Nadi mapping (27 nakshatras, 3 nadis cycling)
# Nadis: Aadi (Vata), Madhya (Pitta), Antya (Kapha)
NAKSHATRA_LIST = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
                  "Punarvasu","Pushya","Ashlesha","Magha","P.Phalguni","U.Phalguni",
                  "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
                  "Mula","P.Ashadha","U.Ashadha","Shravana","Dhanishta","Shatabhisha",
                  "P.Bhadrapada","U.Bhadrapada","Revati"]
NADI_CYCLE = ["Aadi","Madhya","Antya"]


def _norm(planets, lagna_idx):
    sti = {n:i for i,n in enumerate(SIGN_NAMES)}
    out = {}
    for p in planets or []:
        n = p.get("name")
        if not n: continue
        s = p.get("sign_idx")
        if s is None:
            sn = p.get("sign")
            if isinstance(sn, str): s = sti.get(sn)
            elif isinstance(sn, int): s = sn
        if s is None and isinstance(p.get("longitude"),(int,float)):
            s = int(p["longitude"]//30)%12
        h = p.get("house")
        if (h is None) and s is not None and lagna_idx is not None:
            h = ((s - lagna_idx) % 12) + 1
        lon = p.get("longitude")
        out[n] = {"sign_idx": s, "house": h, "longitude": lon}
    return out

def _h(pmap, p):
    info = pmap.get(p) or {}
    h = info.get("house")
    return h if isinstance(h, int) and 1 <= h <= 12 else None

def _s(pmap, p):
    info = pmap.get(p) or {}
    s = info.get("sign_idx")
    return s if isinstance(s, int) and 0 <= s <= 11 else None

def _lord(h, lagna):
    return SIGN_LORDS[(lagna + h - 1) % 12]

def _orb(a, b):
    if a is None or b is None: return None
    d = abs(a - b) % 360
    return min(d, 360 - d)


# ─── 1. Mangal Dosh full BPHS ───────────────────────────────────────────
MANGAL_HOUSES = {1: "Tanu (self/health)", 2: "Kutumba (family/speech)",
                 4: "Sukha (home/peace)", 7: "Kalatra (marriage)",
                 8: "Ayur (longevity/in-laws)", 12: "Vyaya (bed-pleasure/loss)"}

def mangal_dosh_full(pmap, lagna_idx):
    """BPHS Mangal Dosh: Mars in 1/2/4/7/8/12 from Lagna AND from Moon AND from Venus."""
    out = []
    mh = _h(pmap, "Mars")
    if mh not in MANGAL_HOUSES:
        # Check from Moon
        moon_s = _s(pmap, "Moon")
        if moon_s is not None and _s(pmap, "Mars") is not None:
            from_moon = (_s(pmap, "Mars") - moon_s) % 12 + 1
            if from_moon in MANGAL_HOUSES:
                out.append({
                    "name": "Mangal Dosh (from Moon)", "severity": "MEDIUM",
                    "detail": f"Mars in {from_moon}H from Moon ({MANGAL_HOUSES[from_moon]}) — Chandra-Mangal affliction"
                })
        return out

    # From Lagna
    out.append({
        "name": f"Mangal Dosh (from Lagna {mh}H)", "severity": "HIGH" if mh in (7,8) else "MEDIUM",
        "detail": f"Mars in {mh}H ({MANGAL_HOUSES[mh]}) from Lagna — affects {MANGAL_HOUSES[mh].split('(')[1][:-1]}"
    })

    # From Moon
    moon_s = _s(pmap, "Moon")
    if moon_s is not None and _s(pmap, "Mars") is not None:
        from_moon = (_s(pmap, "Mars") - moon_s) % 12 + 1
        if from_moon in MANGAL_HOUSES:
            out.append({
                "name": f"Mangal Dosh (from Moon {from_moon}H)", "severity": "MEDIUM",
                "detail": f"Mars in {from_moon}H from Moon — emotional affliction"
            })

    # From Venus (marriage karaka)
    ven_s = _s(pmap, "Venus")
    if ven_s is not None and _s(pmap, "Mars") is not None:
        from_ven = (_s(pmap, "Mars") - ven_s) % 12 + 1
        if from_ven in MANGAL_HOUSES:
            out.append({
                "name": f"Mangal Dosh (from Venus {from_ven}H)", "severity": "HIGH",
                "detail": f"Mars in {from_ven}H from Venus — direct marriage karaka affliction"
            })

    # ── Cancellation rules (8 BPHS exceptions) ──
    cancellations = []
    mars_s = _s(pmap, "Mars")

    # 1. Mars in own sign (Aries/Scorpio) or exalted (Capricorn)
    if mars_s in (0, 7, 9):
        cancellations.append(f"Mars in own/exalted sign ({SIGN_NAMES[mars_s]}) — dosh CANCELLED")

    # 2. Mars conjunct/aspected by Jupiter
    if mars_s == _s(pmap, "Jupiter"):
        cancellations.append("Mars conjunct Jupiter — dosh CANCELLED by guru's grace")

    # 3. Mars in Cancer/Leo (Moon/Sun's signs — friendly)
    if mars_s in (3, 4):
        cancellations.append(f"Mars in {SIGN_NAMES[mars_s]} (luminary's sign) — dosh REDUCED")

    # 4. Mangal Dosh after age 28 (Saturn's maturity) — informational only
    # 5. Both partners have Mangal Dosh — cancels mutually (compatibility-only)

    # 6. Mars in 7H but in Pisces/Sagittarius (Jupiter's sign)
    if mh == 7 and mars_s in (8, 11):
        cancellations.append("Mars in 7H but in Jupiter's sign — dosh CANCELLED")

    # 7. Lagnesh strong + benefic in 7H
    lagnesh = _lord(1, lagna_idx)
    lh = _h(pmap, lagnesh)
    if lh in (1, 4, 5, 7, 9, 10):
        ls = _s(pmap, lagnesh)
        if ls in OWN.get(lagnesh, []) or ls == EXALT.get(lagnesh):
            cancellations.append(f"Lagnesh {lagnesh} strong in H{lh} — Mangal-dosh effect REDUCED")

    # 8. 7L exalted/own
    l7 = _lord(7, lagna_idx)
    l7s = _s(pmap, l7)
    if l7s in OWN.get(l7, []) or l7s == EXALT.get(l7):
        cancellations.append(f"7L {l7} exalted/own — marriage protection, dosh REDUCED")

    if cancellations:
        out.append({
            "name": "Mangal Dosh — Cancellation(s) active", "severity": "INFO",
            "detail": " | ".join(cancellations)
        })

    return out


# ─── 2. Pitra Dosh — 3 BPHS reasons ────────────────────────────────────
def pitra_dosh_full(pmap, lagna_idx):
    """3 classical reasons:
       (a) Sun conjunct Rahu or Ketu (any house)
       (b) 9L (Pitra-Bhava lord) in 6/8/12
       (c) Sun in 9H aspected/conjoined by Saturn (or in Sat's sign)
    """
    out = []
    sun_s = _s(pmap, "Sun")
    rahu_s = _s(pmap, "Rahu")
    ketu_s = _s(pmap, "Ketu")
    sun_h = _h(pmap, "Sun")
    sun_lon = (pmap.get("Sun") or {}).get("longitude")
    rahu_lon = (pmap.get("Rahu") or {}).get("longitude")
    ketu_lon = (pmap.get("Ketu") or {}).get("longitude")

    # Reason (a)
    if sun_s is not None:
        if sun_s == rahu_s:
            orb = _orb(sun_lon, rahu_lon)
            sev = "HIGH" if (orb is not None and orb < 5) else "MEDIUM"
            out.append({"name": "Pitra Dosh (Sun-Rahu)", "severity": sev,
                        "detail": f"Sun conjunct Rahu in {SIGN_NAMES[sun_s]} (orb {orb:.1f}°)"
                                  f" — paternal lineage karma" if orb else
                                  f"Sun conjunct Rahu in {SIGN_NAMES[sun_s]}"})
        if sun_s == ketu_s:
            orb = _orb(sun_lon, ketu_lon)
            sev = "HIGH" if (orb is not None and orb < 5) else "MEDIUM"
            out.append({"name": "Pitra Dosh (Sun-Ketu)", "severity": sev,
                        "detail": f"Sun conjunct Ketu in {SIGN_NAMES[sun_s]}"
                                  f" (orb {orb:.1f}°) — ancestral spiritual debt" if orb else
                                  f"Sun conjunct Ketu in {SIGN_NAMES[sun_s]}"})

    # Reason (b) — 9L in dusthana
    l9 = _lord(9, lagna_idx)
    h9l = _h(pmap, l9)
    if h9l in (6, 8, 12):
        out.append({"name": f"Pitra Dosh (9L in {h9l}H)", "severity": "MEDIUM",
                    "detail": f"9L {l9} in dusthana H{h9l} — father's blessings obstructed, dharma karma issues"})

    # Reason (c) — Sun in 9H with Saturn affliction
    if sun_h == 9:
        sat_s = _s(pmap, "Saturn")
        if sat_s == sun_s:
            out.append({"name": "Pitra Dosh (Sun-Sat in 9H)", "severity": "HIGH",
                        "detail": "Sun conjunct Saturn in 9H — direct paternal-dharma affliction"})
        elif sun_s in (9, 10):  # Sun in Saturn's sign
            out.append({"name": "Pitra Dosh (Sun in Sat-sign in 9H)", "severity": "MEDIUM",
                        "detail": f"Sun in 9H in {SIGN_NAMES[sun_s]} (Sat's sign) — paternal struggles"})

    return out


# ─── 3. Sade-Sati phase deep ───────────────────────────────────────────
def sade_sati_phase(pmap, current_saturn_sign):
    """Returns current Sade-Sati phase: Rising (12th from Moon),
    Peak (over Moon), Setting (2nd from Moon), or NOT ACTIVE."""
    moon_s = _s(pmap, "Moon")
    if moon_s is None or current_saturn_sign is None:
        return []
    diff = (current_saturn_sign - moon_s) % 12
    if diff == 11:  # 12th from Moon
        return [{"name": "Sade-Sati: Rising Phase", "severity": "MEDIUM",
                 "detail": f"Saturn currently in {SIGN_NAMES[current_saturn_sign]} (12th from natal Moon {SIGN_NAMES[moon_s]}) "
                           "— first 2.5yr phase: financial stress, expenses, foreign moves"}]
    if diff == 0:
        return [{"name": "Sade-Sati: PEAK Phase", "severity": "HIGH",
                 "detail": f"Saturn currently in {SIGN_NAMES[current_saturn_sign]} (over natal Moon) "
                           "— middle 2.5yr phase: hardest, mental/health/career challenges, transformation"}]
    if diff == 1:  # 2nd from Moon
        return [{"name": "Sade-Sati: Setting Phase", "severity": "MEDIUM",
                 "detail": f"Saturn currently in {SIGN_NAMES[current_saturn_sign]} (2nd from Moon) "
                           "— last 2.5yr phase: family/wealth tests, easing toward end"}]
    # Dhaiya (small Sade-Sati, 4th/8th from Moon)
    if diff == 3:
        return [{"name": "Kantaka Shani / Ardha-Ashtama", "severity": "MEDIUM",
                 "detail": f"Saturn 4th from natal Moon — domestic upheaval, mother's health concerns"}]
    if diff == 7:
        return [{"name": "Ashtama Shani", "severity": "HIGH",
                 "detail": f"Saturn 8th from natal Moon — health/longevity tests, sudden disruptions"}]
    return [{"name": "Sade-Sati: NOT active", "severity": "INFO",
             "detail": f"Saturn ({SIGN_NAMES[current_saturn_sign]}) not in 12/1/2 from natal Moon ({SIGN_NAMES[moon_s]}) — clear period"}]


# ─── 4. Kantaka Shani (current transit through 1/4/7/10 from Moon) ─────
def kantaka_shani(pmap, current_saturn_sign):
    moon_s = _s(pmap, "Moon")
    if moon_s is None or current_saturn_sign is None: return []
    from_moon = (current_saturn_sign - moon_s) % 12 + 1
    if from_moon in (1, 4, 7, 10):
        return [{"name": f"Kantaka Shani (Sat in {from_moon}H from Moon)", "severity": "MEDIUM",
                 "detail": f"Saturn transiting {from_moon}H from natal Moon — thorny obstacles, "
                           "delayed efforts, mental burden"}]
    return []


# ─── 5. Vish Yog deep ───────────────────────────────────────────────────
def vish_yog_deep(pmap):
    moon_s = _s(pmap, "Moon")
    sat_s = _s(pmap, "Saturn")
    moon_lon = (pmap.get("Moon") or {}).get("longitude")
    sat_lon = (pmap.get("Saturn") or {}).get("longitude")
    if moon_s is None or sat_s is None: return []
    out = []
    if moon_s == sat_s:
        orb = _orb(moon_lon, sat_lon)
        sev = "HIGH" if (orb is not None and orb < 5) else "MEDIUM"
        out.append({"name": "Vish Yog (Moon-Sat conjunction)", "severity": sev,
                    "detail": f"Moon+Saturn conj in {SIGN_NAMES[moon_s]}"
                              f" (orb {orb:.1f}°)" if orb is not None else
                              f"Moon+Saturn conj in {SIGN_NAMES[moon_s]}"})
    # Saturn 7th from Moon (full aspect)
    elif (sat_s - moon_s) % 12 == 6:
        out.append({"name": "Vish Yog (Sat 7th-aspect on Moon)", "severity": "MEDIUM",
                    "detail": "Saturn directly opposes Moon — emotional heaviness, depression risk"})
    return out


# ─── 6. Nadi Dosh self-marker ───────────────────────────────────────────
def nadi_dosh_marker(nakshatra_name):
    if not nakshatra_name:
        return []
    base = nakshatra_name.split("-")[0].split(" ")[0].strip()
    base = base.replace("Purva", "P.").replace("Uttara", "U.")
    if base not in NAKSHATRA_LIST:
        # Try fuzzy match
        base = next((n for n in NAKSHATRA_LIST if n.lower() == nakshatra_name.lower().strip()),
                    None)
        if not base: return []
    idx = NAKSHATRA_LIST.index(base)
    nadi = NAKSHATRA_CYCLE_NADI(idx)
    return [{"name": f"Nadi: {nadi} (compatibility marker)", "severity": "INFO",
             "detail": f"Nakshatra {base} → {nadi} Nadi. For marriage compat, partner must NOT have same Nadi."}]


def NAKSHATRA_CYCLE_NADI(idx: int) -> str:
    # Standard pattern: Aadi-Madhya-Antya repeats — but BPHS pattern is:
    # Aadi: Ashwini, Ardra, Punarvasu, Uttara-Phalguni, Hasta, Jyeshtha, Mula, Shatabhisha, P.Bhadrapada
    # Madhya: Bharani, Mrigashira, Pushya, P.Phalguni, Chitra, Anuradha, P.Ashadha, Dhanishta, U.Bhadrapada
    # Antya: Krittika, Rohini, Ashlesha, Magha, Swati, Vishakha, U.Ashadha, Shravana, Revati
    pattern = ["Aadi","Madhya","Antya","Antya","Madhya","Aadi","Aadi","Madhya","Antya",
               "Antya","Madhya","Aadi","Aadi","Madhya","Antya","Antya","Madhya","Aadi",
               "Aadi","Madhya","Antya","Antya","Madhya","Aadi","Aadi","Madhya","Antya"]
    return pattern[idx] if 0 <= idx < 27 else "Unknown"


# ─── 7. Karaka Doshas (significator afflictions) ────────────────────────
KARAKA_MAP = {
    "Matri": ("Moon", "Mother"),
    "Putra": ("Jupiter", "Children"),
    "Bhratri": ("Mars", "Siblings"),
    "Chandra": ("Moon", "Mind/emotional"),
    "Guru": ("Jupiter", "Wisdom/guru"),
    "Shukra": ("Venus", "Spouse/marriage"),
    "Pitra (karaka)": ("Sun", "Father"),
}

def karaka_doshas(pmap):
    """Karaka is debilitated, in 6/8/12, conjunct Rahu/Ketu, or combust."""
    out = []
    sun_lon = (pmap.get("Sun") or {}).get("longitude")
    for dname, (planet, theme) in KARAKA_MAP.items():
        s = _s(pmap, planet)
        h = _h(pmap, planet)
        afflictions = []
        if s == DEBIL.get(planet):
            afflictions.append(f"DEBILITATED in {SIGN_NAMES[s]}")
        if h in (6, 8, 12):
            afflictions.append(f"in dusthana H{h}")
        # Rahu/Ketu conjunction
        if s == _s(pmap, "Rahu"):
            afflictions.append("conjunct Rahu (graham)")
        if s == _s(pmap, "Ketu"):
            afflictions.append("conjunct Ketu (graham)")
        # Combust (within 8.5° of Sun, except Moon)
        if planet not in ("Sun", "Moon"):
            plon = (pmap.get(planet) or {}).get("longitude")
            orb = _orb(plon, sun_lon)
            if orb is not None and orb < 8.5:
                afflictions.append(f"COMBUST (Sun orb {orb:.1f}°)")
        if afflictions:
            sev = "HIGH" if len(afflictions) >= 2 else "MEDIUM"
            out.append({
                "name": f"{dname} Dosh ({planet} affliction)", "severity": sev,
                "detail": f"{planet} ({theme}): " + "; ".join(afflictions)
            })
    return out


# ─── 8. Grahan Dosh deep ────────────────────────────────────────────────
def grahan_dosh_deep(pmap):
    out = []
    sun_lon = (pmap.get("Sun") or {}).get("longitude")
    moon_lon = (pmap.get("Moon") or {}).get("longitude")
    rahu_lon = (pmap.get("Rahu") or {}).get("longitude")
    ketu_lon = (pmap.get("Ketu") or {}).get("longitude")
    sun_s = _s(pmap, "Sun"); moon_s = _s(pmap, "Moon")
    rahu_s = _s(pmap, "Rahu"); ketu_s = _s(pmap, "Ketu")

    # Surya Grahan — Sun + Rahu/Ketu within 5°
    if sun_s == rahu_s and _orb(sun_lon, rahu_lon) is not None and _orb(sun_lon, rahu_lon) < 5:
        out.append({"name": "Surya Grahan Dosh", "severity": "HIGH",
                    "detail": f"Sun-Rahu within {_orb(sun_lon, rahu_lon):.1f}° — solar eclipse formation, ego/father afflicted"})
    if sun_s == ketu_s and _orb(sun_lon, ketu_lon) is not None and _orb(sun_lon, ketu_lon) < 5:
        out.append({"name": "Surya Grahan Dosh (Ketu)", "severity": "HIGH",
                    "detail": f"Sun-Ketu within {_orb(sun_lon, ketu_lon):.1f}° — eclipse signature"})

    # Chandra Grahan — Moon + Rahu/Ketu within 5°
    if moon_s == rahu_s and _orb(moon_lon, rahu_lon) is not None and _orb(moon_lon, rahu_lon) < 5:
        out.append({"name": "Chandra Grahan Dosh", "severity": "HIGH",
                    "detail": f"Moon-Rahu within {_orb(moon_lon, rahu_lon):.1f}° — lunar eclipse, mind/mother afflicted"})
    if moon_s == ketu_s and _orb(moon_lon, ketu_lon) is not None and _orb(moon_lon, ketu_lon) < 5:
        out.append({"name": "Chandra Grahan Dosh (Ketu)", "severity": "HIGH",
                    "detail": f"Moon-Ketu within {_orb(moon_lon, ketu_lon):.1f}° — emotional eclipse"})

    return out


# ─── 9. Shrapit Dosh deep ───────────────────────────────────────────────
def shrapit_dosh_deep(pmap):
    """Shrapit = Saturn + Rahu (or Ketu) close conjunction or in same house."""
    out = []
    sat_s = _s(pmap, "Saturn")
    rahu_s = _s(pmap, "Rahu")
    ketu_s = _s(pmap, "Ketu")
    sat_h = _h(pmap, "Saturn")
    sat_lon = (pmap.get("Saturn") or {}).get("longitude")

    if sat_s == rahu_s:
        rahu_lon = (pmap.get("Rahu") or {}).get("longitude")
        orb = _orb(sat_lon, rahu_lon)
        sev = "HIGH" if (orb is not None and orb < 8) else "MEDIUM"
        out.append({"name": "Shrapit Dosh (Sat-Rahu)", "severity": sev,
                    "detail": f"Saturn+Rahu conj in {SIGN_NAMES[sat_s]} (H{sat_h}) — past-life curse signature, "
                              "long delays, blockages"})
    if sat_s == ketu_s:
        ketu_lon = (pmap.get("Ketu") or {}).get("longitude")
        orb = _orb(sat_lon, ketu_lon)
        sev = "HIGH" if (orb is not None and orb < 8) else "MEDIUM"
        out.append({"name": "Shrapit Dosh (Sat-Ketu)", "severity": sev,
                    "detail": f"Saturn+Ketu conj in {SIGN_NAMES[sat_s]} (H{sat_h}) — moksha-karma curse, "
                              "spiritual karmic block"})
    return out


# ─── Master orchestrator ────────────────────────────────────────────────
def detect_deep_doshas(planets, lagna_sign_idx, current_saturn_sign=None,
                       nakshatra_name: Optional[str] = None):
    if lagna_sign_idx is None: return []
    pmap = _norm(planets, lagna_sign_idx)
    if not pmap: return []
    out = []
    out.extend(mangal_dosh_full(pmap, lagna_sign_idx))
    out.extend(pitra_dosh_full(pmap, lagna_sign_idx))
    if current_saturn_sign is not None:
        out.extend(sade_sati_phase(pmap, current_saturn_sign))
        out.extend(kantaka_shani(pmap, current_saturn_sign))
    out.extend(vish_yog_deep(pmap))
    if nakshatra_name:
        out.extend(nadi_dosh_marker(nakshatra_name))
    out.extend(karaka_doshas(pmap))
    out.extend(grahan_dosh_deep(pmap))
    out.extend(shrapit_dosh_deep(pmap))
    return out


def format_deep_doshas_summary(doshas):
    if not doshas: return ""
    lines = [f"▸ DEEP DOSHAS (Sprint-20 Tier-4 BPHS-precise): {len(doshas)} detected"]
    by_sev = {"HIGH": [], "MEDIUM": [], "INFO": []}
    for d in doshas:
        by_sev.setdefault(d.get("severity", "INFO"), []).append(d)
    for sev in ("HIGH", "MEDIUM", "INFO"):
        items = by_sev.get(sev) or []
        if not items: continue
        tag = {"HIGH": "🔴", "MEDIUM": "🟠", "INFO": "ℹ️"}[sev]
        lines.append(f"  {tag} {sev} ({len(items)}):")
        for d in items[:8]:
            lines.append(f"    • {d['name']}: {d.get('detail','')}")
        if len(items) > 8:
            lines.append(f"    … (+{len(items)-8} more)")
    return "\n".join(lines)

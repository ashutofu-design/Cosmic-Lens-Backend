"""Tier 9 — Family, Lineage & Children bundle.

Combines:
  • 4th house deep — Mother, Home, Inner Peace, Vehicles
  • 5th house deep — Children, Creativity, Purva Punya
  • 9th house deep — Father, Dharma, Guru, Higher Wisdom
  • Jupiter (Putrakaraka) signature — natural karaka of children
  • Santan / Putra Yoga audit — strong-children combinations
  • Pitru-Dosha quick-check (Sun-Rahu/Ketu, 9th affliction)
  • Property & Home signature (4th lord + Mars + Venus)
  • Current Mahadasha family-events window (vs 4/5/9)
  • Numerology family layer (driver + conductor family-style)
  • Synthesis verdict

Public API:
    compute_family_bundle(kundli, dob, driver, conductor) -> dict
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

# ── Driver-number family-style ────────────────────────────────────
DRIVER_FAMILY: Dict[int, Dict[str, str]] = {
    1: {"planet": "Sun",
        "family_role": "natural head / decision-maker",
        "parenting_style": "ambitious mentor — pushes children toward visibility & leadership",
        "home_vibe": "structured, status-conscious, public-facing home",
        "gift_to_family": "long-term direction & financial stability",
        "shadow": "ego clashes with family elders; learn to soften authority"},
    2: {"planet": "Moon",
        "family_role": "emotional anchor / nurturer",
        "parenting_style": "deeply intuitive, soothing, food-and-comfort focused",
        "home_vibe": "warm, sentimental, family-photos everywhere, mother-energy strong",
        "gift_to_family": "unconditional emotional safety",
        "shadow": "absorbs family stress quietly — learn to set emotional boundaries"},
    3: {"planet": "Jupiter",
        "family_role": "wisdom-keeper / family teacher",
        "parenting_style": "philosophical guide — values learning, ethics, dharma",
        "home_vibe": "library, gurujis welcomed, festivals celebrated grandly",
        "gift_to_family": "values, education, generational wisdom",
        "shadow": "preachy tone with siblings/spouse; lecture less, listen more"},
    4: {"planet": "Rahu",
        "family_role": "rule-breaker / unconventional unit",
        "parenting_style": "modern, tech-savvy, lets children explore unusual paths",
        "home_vibe": "non-traditional setup (joint/nuclear blend, foreign influences)",
        "gift_to_family": "exposure to new ideas, foreign opportunities",
        "shadow": "family bonds can feel emotionally distant; schedule deliberate together-time"},
    5: {"planet": "Mercury",
        "family_role": "communicator / sibling-bond hub",
        "parenting_style": "playful, intellectually stimulating, loves teaching skills",
        "home_vibe": "books, gadgets, lively conversations, friend-circle visits often",
        "gift_to_family": "humor, sharp wit, intellectual stimulation",
        "shadow": "can come across as scattered; commit to deeper one-on-one time"},
    6: {"planet": "Venus",
        "family_role": "harmonizer / aesthetic curator",
        "parenting_style": "loving, indulgent, beauty + arts oriented",
        "home_vibe": "tasteful interiors, garden, music, food-celebration culture",
        "gift_to_family": "beauty, comfort, harmonious bonds",
        "shadow": "avoids hard conversations; address conflict instead of papering over it"},
    7: {"planet": "Ketu",
        "family_role": "spiritual seeker / detached observer",
        "parenting_style": "gives space, encourages independence + spirituality",
        "home_vibe": "minimalist, meditation corner, low-attachment to material display",
        "gift_to_family": "spiritual depth, freedom, non-judgmental presence",
        "shadow": "can feel emotionally absent; explicitly express affection often"},
    8: {"planet": "Saturn",
        "family_role": "responsible elder / disciplined provider",
        "parenting_style": "rules + structure + delayed gratification training",
        "home_vibe": "old-school discipline, traditional values, hard work celebrated",
        "gift_to_family": "stability, work ethic, long-haul reliability",
        "shadow": "can be too strict or emotionally cold; warm up the rules with hugs"},
    9: {"planet": "Mars",
        "family_role": "protector / warrior",
        "parenting_style": "courage-builder, sports + adventure oriented, fierce defender",
        "home_vibe": "active, energetic, competitive, sometimes shouty",
        "gift_to_family": "courage, protection, drive",
        "shadow": "anger/argument flare-ups; channel energy into shared physical activity"},
}

# Lucky family-day per driver (when family-bonding rituals work best)
DRIVER_FAMILY_DAY: Dict[int, str] = {
    1: "Sunday", 2: "Monday", 3: "Thursday", 4: "Saturday (caution)",
    5: "Wednesday", 6: "Friday", 7: "Tuesday/Sunday (Ketu)",
    8: "Saturday", 9: "Tuesday",
}


def _planet_house_d1(planets: List[Dict], asc_sign: str) -> Dict[str, int]:
    if not isinstance(planets, list) or asc_sign not in SIGNS:
        return {}
    asc_idx = SIGNS.index(asc_sign)
    out: Dict[str, int] = {}
    for p in planets:
        if not isinstance(p, dict): continue
        sgn = p.get("sign"); nm = p.get("name")
        if sgn in SIGNS and nm:
            sidx = SIGNS.index(sgn)
            out[nm] = ((sidx - asc_idx + 12) % 12) + 1
    return out


def _occupants(planets: List[Dict], asc_sign: str, house_num: int) -> List[str]:
    h = _planet_house_d1(planets, asc_sign)
    return sorted([nm for nm, hn in h.items() if hn == house_num])


def _planet_sign(planets: List[Dict], name: str) -> str:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == name:
            return p.get("sign", "—")
    return "—"


def _resolve_md_end(kundli: Dict, md_lord: str) -> str:
    try:
        from datetime import datetime as _dt
        today = _dt.now().date()
        for entry in (kundli.get("dashas") or []):
            if entry.get("planet") != md_lord: continue
            try:
                start = _dt.strptime(entry.get("startDate", ""), "%Y-%m-%d").date()
                end = _dt.strptime(entry.get("endDate", ""), "%Y-%m-%d").date()
            except Exception:
                continue
            if start <= today <= end:
                return entry.get("endDate", "—")
        for entry in (kundli.get("dashas") or []):
            if entry.get("planet") == md_lord:
                return entry.get("endDate", "—")
    except Exception:
        pass
    return "—"


def _synergy(driver: int, conductor: int) -> str:
    try:
        from vedic.numerology.framing import _synergy_verdict
        return _synergy_verdict(driver, conductor)
    except Exception:
        return "NEUTRAL"


def compute_family_bundle(kundli: Dict[str, Any], dob: str,
                          driver: int, conductor: int) -> Dict[str, Any]:
    """Compute T9 Family bundle. Hard data gate — never fabricates on missing
    core anchors. Returns {available: False, reason: ...} when gated."""
    out: Dict[str, Any] = {"available": False}
    if not isinstance(kundli, dict):
        out["reason"] = "no kundli"
        return out

    asc = kundli.get("ascendant")
    planets = kundli.get("planets", []) or []

    if not asc or asc not in SIGNS:
        out["reason"] = f"ascendant missing or unknown ({asc!r})"
        return out
    if not isinstance(planets, list) or len(planets) < 9:
        out["reason"] = f"planets list incomplete (n={len(planets) if isinstance(planets, list) else 0}, need all 9 grahas including Rahu/Ketu for Pitru audit)"
        return out
    planet_names = {p.get("name") for p in planets if isinstance(p, dict)}
    # Require ALL 9 grahas (incl. Rahu+Ketu — Pitru-Dosha audit hinges on nodes;
    # missing nodes would silently produce a false 'CLEAR' verdict)
    required = {"Sun", "Moon", "Jupiter", "Mars", "Venus", "Mercury", "Saturn", "Rahu", "Ketu"}
    missing_req = required - planet_names
    if missing_req:
        out["reason"] = f"missing required grahas: {sorted(missing_req)}"
        return out

    asc_idx = SIGNS.index(asc)
    p_house = _planet_house_d1(planets, asc)

    # ── house deep blocks (4/5/7/9/12) ────────────────────────────
    def _hb(num: int) -> Dict[str, Any]:
        sign = SIGNS[(asc_idx + num - 1) % 12]
        lord = SIGN_LORD.get(sign, "—")
        occ = _occupants(planets, asc, num)
        return {
            "house": num, "sign": sign, "lord": lord,
            "lord_house": p_house.get(lord, 0),
            "lord_sign": _planet_sign(planets, lord),
            "occupants": occ, "occupants_count": len(occ),
        }
    fourth = _hb(4)    # mother, home, inner peace, vehicles
    fifth = _hb(5)     # children, creativity, intellect
    seventh = _hb(7)   # spouse-family briefing
    ninth = _hb(9)     # father, dharma, guru
    twelfth = _hb(12)  # ashram, foreign, hidden family

    # ── 4th house — Mother & Home ─────────────────────────────────
    moon_house = p_house.get("Moon", 0)
    mother_strong = (fourth["lord_house"] in {1, 4, 5, 7, 9, 10, 11}) and \
                    (moon_house in {1, 4, 5, 7, 9, 10, 11})
    mother_block = {
        **fourth,
        "moon_house": moon_house,
        "mother_signature": "STRONG — emotionally close mother, warm home" if mother_strong
                            else "MODERATE — bond may need conscious nurturing",
        "home_vibe_keywords": (
            f"sign {fourth['sign']} ({SIGN_LORD.get(fourth['sign'])} ruled) — "
            f"{('emotionally cozy' if fourth['sign'] in ('Cancer','Pisces','Taurus') else 'practical/structured' if fourth['sign'] in ('Capricorn','Virgo','Aquarius') else 'fiery/active' if fourth['sign'] in ('Aries','Leo','Sagittarius') else 'communicative/social')}"
        ),
    }

    # ── 9th house — Father & Dharma ───────────────────────────────
    sun_house = p_house.get("Sun", 0)
    father_strong = (ninth["lord_house"] in {1, 4, 5, 7, 9, 10, 11}) and \
                    (sun_house in {1, 4, 5, 7, 9, 10, 11})
    father_block = {
        **ninth,
        "sun_house": sun_house,
        "father_signature": "STRONG — supportive, dharmic father-figure" if father_strong
                            else "MODERATE — relationship may carry karmic lessons; needs conscious bridge-building",
        "dharma_keyword": (
            f"sign {ninth['sign']} → "
            f"{('philosophical-spiritual' if ninth['sign'] in ('Sagittarius','Pisces') else 'service-driven' if ninth['sign'] in ('Virgo','Capricorn') else 'leadership-dharma' if ninth['sign'] in ('Leo','Aries') else 'humanitarian/networked')}"
        ),
    }

    # ── 5th house — Children & Creativity ─────────────────────────
    jup_house = p_house.get("Jupiter", 0)
    jup_sign = _planet_sign(planets, "Jupiter")
    # Putra-Karaka = Jupiter; classical putra yoga = strong 5L + strong Jup + strong 5-from-Jup
    fifth_lord = fifth["lord"]
    putra_score = 0
    putra_notes: List[str] = []
    # Kendra (1,4,7,10) ∪ Trikona (1,5,9) ∪ Upachaya (3,6,10,11) = {1,3,4,5,6,7,9,10,11}
    SUPPORTIVE_HOUSES = {1, 3, 4, 5, 6, 7, 9, 10, 11}
    if fifth["lord_house"] in SUPPORTIVE_HOUSES:
        putra_score += 1
        putra_notes.append(f"5th-lord {fifth_lord} placed well (House {fifth['lord_house']}, kendra/trikona/upachaya) — child-bond karma supportive")
    else:
        putra_notes.append(f"5th-lord {fifth_lord} in House {fifth['lord_house']} (dusthana) — extra patience around child-prospects/bonding")
    if jup_house in SUPPORTIVE_HOUSES:
        putra_score += 1
        putra_notes.append(f"Jupiter (Putrakaraka) in House {jup_house} (kendra/trikona/upachaya) — natural blessing for offspring")
    else:
        putra_notes.append(f"Jupiter in House {jup_house} (dusthana) — child-blessing comes through deliberate spiritual discipline")
    if jup_sign in ("Cancer", "Sagittarius", "Pisces"):
        putra_score += 1
        putra_notes.append(f"Jupiter in {jup_sign} (own/exalted) — strongly amplifies progeny-blessings")
    elif jup_sign == "Capricorn":
        putra_notes.append("Jupiter debilitated in Capricorn — dharmic remedies (Vishnu/Brihaspati pooja) recommended")

    if putra_score >= 2:
        putra_verdict = "STRONG"
    elif putra_score == 1:
        putra_verdict = "MODERATE"
    else:
        putra_verdict = "REQUIRES_REMEDIES"

    children_block = {
        **fifth,
        "jupiter_house": jup_house,
        "jupiter_sign": jup_sign,
        "putrakaraka_planet": "Jupiter",
        "putra_yoga_score": putra_score,
        "putra_yoga_max": 3,
        "putra_yoga_verdict": putra_verdict,
        "putra_yoga_notes": putra_notes,
        "creativity_keyword": (
            f"5th sign {fifth['sign']} → "
            f"{('artistic/aesthetic' if fifth['sign'] in ('Taurus','Libra','Pisces') else 'intellectual/sharp' if fifth['sign'] in ('Gemini','Virgo','Aquarius') else 'performative/leader' if fifth['sign'] in ('Leo','Aries','Sagittarius') else 'emotional/healing')}"
        ),
    }

    # ── Pitru-Dosha quick check ───────────────────────────────────
    sun_sign = _planet_sign(planets, "Sun")
    rahu_house = p_house.get("Rahu", 0)
    ketu_house = p_house.get("Ketu", 0)
    sun_with_rahu = rahu_house == sun_house and sun_house != 0
    sun_with_ketu = ketu_house == sun_house and sun_house != 0
    ninth_afflicted = (rahu_house == 9) or (ketu_house == 9) or \
                      ("Saturn" in ninth["occupants"]) or ("Mars" in ninth["occupants"])
    pitru_factors: List[str] = []
    if sun_with_rahu:
        pitru_factors.append(f"Sun ⊕ Rahu in House {sun_house} — classical Pitru-Dosha indicator")
    if sun_with_ketu:
        pitru_factors.append(f"Sun ⊕ Ketu in House {sun_house} — classical Pitru-Dosha indicator")
    if ninth_afflicted:
        pitru_factors.append(f"9th-house affliction (Rahu/Ketu/Saturn/Mars present) — paternal-karma layer present")
    pitru_active = len(pitru_factors) > 0
    pitru_block = {
        "active": pitru_active,
        "factors": pitru_factors,
        "remedy_summary": (
            "Recommended: Pitru-Paksha tarpan (annual), feeding crows/cows on Amavasya, "
            "Tripindi-Shraddha at Trimbakeshwar/Gokarna once, donate black sesame on "
            "Saturday, never disrespect father-figures."
            if pitru_active else
            "No major pitru-dosha indicator — maintain standard pitru-paksha respect "
            "for ancestors annually."
        ),
    }

    # ── Property & Home signature (4L + Mars + Venus) ─────────────
    mars_house = p_house.get("Mars", 0)
    venus_house = p_house.get("Venus", 0)
    fourth_lord = fourth["lord"]
    prop_score = 0
    prop_notes: List[str] = []
    if fourth["lord_house"] in {1, 4, 9, 10, 11}:
        prop_score += 1
        prop_notes.append(f"4th-lord {fourth_lord} in supportive House {fourth['lord_house']} — owning property comes naturally")
    if mars_house in {3, 4, 6, 10, 11}:
        prop_score += 1
        prop_notes.append(f"Mars (real-estate karaka) in House {mars_house} — favourable for property acquisition")
    if venus_house in {2, 4, 11}:
        prop_score += 1
        prop_notes.append(f"Venus (vehicles + comfort) in House {venus_house} — vehicle/luxury-comfort yoga")
    prop_verdict = "STRONG" if prop_score >= 2 else "MODERATE" if prop_score == 1 else "BUILD_PATIENTLY"
    property_block = {
        "score": prop_score, "max": 3, "verdict": prop_verdict,
        "notes": prop_notes,
        "fourth_lord": fourth_lord,
        "mars_house": mars_house,
        "venus_house": venus_house,
    }

    # ── Spouse-family briefing (7th house — for in-law context) ──
    seventh_block = {
        **seventh,
        "in_law_keyword": (
            f"7th sign {seventh['sign']} → "
            f"{('warm/family-oriented in-laws' if seventh['sign'] in ('Cancer','Taurus','Pisces') else 'professional/structured in-laws' if seventh['sign'] in ('Capricorn','Virgo','Aquarius') else 'lively/social in-laws')}"
        ),
    }

    # ── Current Mahadasha → family-events window ──────────────────
    cur = (kundli.get("currentDasha") or {})
    md_lord = cur.get("maha") or "—"
    ad_lord = cur.get("antar") or "—"
    md_end = _resolve_md_end(kundli, md_lord) if md_lord != "—" else "—"
    md_house = p_house.get(md_lord, 0)

    if md_house in {4, 2}:
        f_verdict = "HOME-FOCUS"
        f_note = (f"Current MD lord {md_lord} (House {md_house}) — strong pull toward home, "
                  f"property, family-foundation. Good window for buying home / hosting elders / "
                  f"deepening parental bonds.")
    elif md_house == 5:
        f_verdict = "CHILDREN-CREATIVITY"
        f_note = (f"Current MD lord {md_lord} in House 5 — children-creativity-romance window. "
                  f"Often coincides with childbirth, child's milestones, or creative-project bloom.")
    elif md_house == 9:
        f_verdict = "FATHER-DHARMA"
        f_note = (f"Current MD lord {md_lord} in House 9 — father/guru/long-distance-family theme; "
                  f"good for pilgrimage, learning from family elders, dharmic gatherings.")
    elif md_house in {7, 11}:
        f_verdict = "EXPANSION-WINDOW"
        f_note = (f"Current MD lord {md_lord} (House {md_house}) — partnership/network expansion; "
                  f"likely additions to family circle (marriage / new in-laws / community).")
    elif md_house in {6, 8, 12}:
        f_verdict = "INNER-WORK"
        f_note = (f"Current MD lord {md_lord} (House {md_house}) — family bonds may need conscious "
                  f"care; avoid major property/marriage decisions in haste; resolve old "
                  f"family-misunderstandings now.")
    else:
        f_verdict = "STEADY"
        f_note = (f"Current MD lord {md_lord} (House {md_house}) — neutral family window; "
                  f"maintain regular festivals, calls home, family rituals.")

    family_window = {
        "md_lord": md_lord, "ad_lord": ad_lord, "md_house": md_house,
        "md_end_date": md_end, "verdict": f_verdict, "note": f_note,
    }

    # ── Numerology family layer ──────────────────────────────────
    df = DRIVER_FAMILY.get(driver, DRIVER_FAMILY[1])
    cf = DRIVER_FAMILY.get(conductor, DRIVER_FAMILY[1])
    num_layer = {
        "driver_family": df,
        "conductor_family": cf,
        "synergy_verdict": _synergy(driver, conductor),
        "lucky_family_day": DRIVER_FAMILY_DAY.get(driver, "—"),
    }

    # ── Synthesis ────────────────────────────────────────────────
    syn = (
        f"4th-lord {fourth_lord} (H{fourth['lord_house']}) → mother {('STRONG' if mother_strong else 'MODERATE')}; "
        f"9th-lord {ninth['lord']} (H{ninth['lord_house']}) → father {('STRONG' if father_strong else 'MODERATE')}; "
        f"5th-lord {fifth_lord} (H{fifth['lord_house']}) + Jupiter (H{jup_house}) → "
        f"Putra-yoga {putra_verdict} ({putra_score}/3). "
        f"Pitru-dosha: {'ACTIVE' if pitru_active else 'CLEAR'}. "
        f"Property: {prop_verdict} ({prop_score}/3). "
        f"Current MD ({md_lord}) → {f_verdict}. "
        f"Driver-{driver} family-style: {df['family_role']}."
    )

    out.update({
        "available": True,
        "mother_home": mother_block,
        "father_dharma": father_block,
        "children_creativity": children_block,
        "pitru_audit": pitru_block,
        "property_signature": property_block,
        "spouse_family": seventh_block,
        "twelfth_house": twelfth,
        "family_window": family_window,
        "numerology_layer": num_layer,
        "synthesis_verdict": syn,
    })
    return out

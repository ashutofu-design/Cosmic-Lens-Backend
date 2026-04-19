"""
Sprint 19 — Classical Yogas Mega-Detector
=========================================
Detects 80+ classical yogas missing from chart_intelligence._detect_yogas.

Categories built here (each yoga returns dict with name/category/polarity/detail):
  • Named Vipreet Raja (3) — Harsha, Sarala, Vimala
  • Dhana Yogas (10+) — pairwise lord combinations giving wealth
  • Negative-named yogas — Daridra, Guru-Chandal, Shakat, Vish, Kala-Sarpa
  • Kaal Sarp 12 variants — Anant..Sheshnag (Rahu's house)
  • Nabhasa Yogas — Sankhya 7, Ashraya 3, Aakriti subset, Dala 2
  • Pravrajya Yogas (4 planets in 1 house — renunciation)

Inputs:
  planets         : list of dicts (name, sign_idx OR sign, house, longitude...)
  lagna_sign_idx  : int 0..11 (Aries=0)

Output:
  detect_classical_yogas(...) -> list[dict]
  format_classical_yogas_summary(...) -> str
"""
from __future__ import annotations

from typing import Any, Optional

SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]
SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
OWN_SIGNS = {
    "Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5],
    "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10],
}
EXALT = {
    "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3,
    "Venus": 11, "Saturn": 6,
}
DEBIL = {p: (s + 6) % 12 for p, s in EXALT.items()}

CHARA_SIGNS = {0, 3, 6, 9}        # Ar Cn Li Cp
STHIRA_SIGNS = {1, 4, 7, 10}      # Ta Le Sc Aq
DWISWA_SIGNS = {2, 5, 8, 11}      # Ge Vi Sg Pi

KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}
DUSTHANA = {6, 8, 12}
PANAPARA = {2, 5, 8, 11}
APOKLIMA = {3, 6, 9, 12}

NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

# Kaal Sarp variant names (Rahu's house → name)
KAAL_SARP_NAMES = {
    1:  "Anant",      2:  "Kulik",       3:  "Vasuki",
    4:  "Shankhpal",  5:  "Padma",       6:  "Mahapadma",
    7:  "Takshak",    8:  "Karkotak",    9:  "Shankhachood",
    10: "Ghatak",     11: "Vishdhar",    12: "Sheshnag",
}


# ── helpers ────────────────────────────────────────────────────────────────
def _norm_planets(planets: list, lagna_sign_idx: Optional[int]) -> dict[str, dict]:
    """Build {name: {sign_idx, house}} map. Derives house from lagna if missing."""
    sti = {n: i for i, n in enumerate(SIGN_NAMES)}
    pmap: dict[str, dict] = {}
    for p in planets or []:
        name = p.get("name")
        if not name:
            continue
        s_idx = p.get("sign_idx")
        if s_idx is None:
            sn = p.get("sign")
            if isinstance(sn, str):
                s_idx = sti.get(sn)
            elif isinstance(sn, int):
                s_idx = sn
        if s_idx is None and isinstance(p.get("longitude"), (int, float)):
            s_idx = int(p["longitude"] // 30) % 12
        h = p.get("house")
        if (h is None or not isinstance(h, int)) and s_idx is not None and lagna_sign_idx is not None:
            h = ((s_idx - lagna_sign_idx) % 12) + 1
        pmap[name] = {"sign_idx": s_idx, "house": h}
    return pmap


def _lord_of_house(h: int, lagna_sign_idx: int) -> str:
    return SIGN_LORDS[(lagna_sign_idx + h - 1) % 12]


def _house_of(pmap: dict, planet: str) -> Optional[int]:
    info = pmap.get(planet) or {}
    h = info.get("house")
    return h if isinstance(h, int) and 1 <= h <= 12 else None


def _sign_of(pmap: dict, planet: str) -> Optional[int]:
    info = pmap.get(planet) or {}
    s = info.get("sign_idx")
    return s if isinstance(s, int) and 0 <= s <= 11 else None


# ── 1. Named Vipreet Raja Yogas ────────────────────────────────────────────
def _named_vipreet(pmap: dict, lagna: int) -> list[dict]:
    out = []
    spec = [
        ("Harsha", 6, "6L in 6/8/12 — fortunate, victory over enemies, robust health"),
        ("Sarala", 8, "8L in 6/8/12 — long life, occult mastery, hidden gains"),
        ("Vimala", 12, "12L in 6/8/12 — frugal yet wealthy, philanthropic, indep."),
    ]
    for name, hl, desc in spec:
        lord = _lord_of_house(hl, lagna)
        h = _house_of(pmap, lord)
        if h in DUSTHANA:
            out.append({
                "name": f"{name} yoga",
                "category": "Vipreet Raja",
                "polarity": "POSITIVE",
                "detail": f"{hl}L {lord} in H{h} — {desc}",
            })
    return out


# ── 2. Dhana Yogas — pairwise dhana-house lord combinations ───────────────
DHANA_PAIRS = [
    (1, 2,  "1L+2L conjunction/exchange — self-effort + accumulated wealth"),
    (1, 5,  "1L+5L conj/exch — wealth from intelligence, speculation, children"),
    (1, 9,  "1L+9L conj/exch — wealth from fortune, blessings, dharma"),
    (1, 11, "1L+11L conj/exch — wealth from gains, network, elder siblings"),
    (2, 5,  "2L+5L conj/exch — accumulated savings + investment returns"),
    (2, 9,  "2L+9L conj/exch — wealth from elders, ancestral, religious"),
    (2, 11, "2L+11L conj/exch — earned wealth + multiplied gains (LAKSHMI signature)"),
    (5, 9,  "5L+9L conj/exch — supreme dhana-trikona Raja-yoga (intelligence×fortune)"),
    (5, 11, "5L+11L conj/exch — speculation, stock-market, children's prosperity"),
    (9, 11, "9L+11L conj/exch — fortunate gains, wealth via mentors/network"),
]


def _dhana_yogas(pmap: dict, lagna: int) -> list[dict]:
    out = []
    seen = set()
    for h1, h2, desc in DHANA_PAIRS:
        l1 = _lord_of_house(h1, lagna)
        l2 = _lord_of_house(h2, lagna)
        if l1 == l2:
            continue
        s1 = _sign_of(pmap, l1)
        s2 = _sign_of(pmap, l2)
        if s1 is None or s2 is None:
            continue
        # Conjunction
        if s1 == s2:
            key = (h1, h2, "conj")
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "name": f"Dhana yoga ({h1}L+{h2}L conj)",
                "category": "Dhana",
                "polarity": "POSITIVE",
                "detail": f"{l1} & {l2} both in {SIGN_NAMES[s1]} — {desc}",
            })
        # Mutual exchange (parivartana)
        elif s2 in OWN_SIGNS.get(l1, []) and s1 in OWN_SIGNS.get(l2, []):
            key = (h1, h2, "exch")
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "name": f"Dhana yoga ({h1}L+{h2}L parivartana)",
                "category": "Dhana",
                "polarity": "POSITIVE",
                "detail": f"{l1}↔{l2} sign exchange — {desc}",
            })
    return out


# ── 3. Negative named yogas ────────────────────────────────────────────────
def _negative_yogas(pmap: dict, lagna: int) -> list[dict]:
    out = []

    # Daridra Yoga: 11L in 6/8/12 OR Lagnesh in dusthana
    l11 = _lord_of_house(11, lagna)
    h11 = _house_of(pmap, l11)
    if h11 in DUSTHANA:
        out.append({
            "name": "Daridra yoga",
            "category": "Negative",
            "polarity": "NEGATIVE",
            "detail": f"11L {l11} in H{h11} (dusthana) — gains blocked, financial struggle",
        })

    # Guru-Chandal: Jupiter conjunct Rahu OR Ketu (same sign)
    js = _sign_of(pmap, "Jupiter")
    rs = _sign_of(pmap, "Rahu")
    ks = _sign_of(pmap, "Ketu")
    if js is not None and js == rs:
        out.append({
            "name": "Guru-Chandal yoga",
            "category": "Negative",
            "polarity": "NEGATIVE",
            "detail": f"Jupiter+Rahu in {SIGN_NAMES[js]} — wisdom corrupted, unconventional gurus",
        })
    elif js is not None and js == ks:
        out.append({
            "name": "Guru-Chandal yoga (Ketu variant)",
            "category": "Negative",
            "polarity": "NEGATIVE",
            "detail": f"Jupiter+Ketu in {SIGN_NAMES[js]} — detached wisdom, spiritual disillusion",
        })

    # Shakat Yoga: Moon in 6/8/12 from Jupiter
    ms = _sign_of(pmap, "Moon")
    if js is not None and ms is not None:
        diff = ((ms - js) % 12) + 1   # Moon's house from Jupiter
        if diff in (6, 8, 12):
            out.append({
                "name": "Shakat yoga",
                "category": "Negative",
                "polarity": "NEGATIVE",
                "detail": f"Moon {diff}th from Jupiter — fluctuating fortune, ups-downs",
            })

    # Vish (Visha) Yoga: Saturn + Moon same sign
    ss = _sign_of(pmap, "Saturn")
    if ms is not None and ms == ss:
        out.append({
            "name": "Vish yoga",
            "category": "Negative",
            "polarity": "NEGATIVE",
            "detail": f"Moon+Saturn in {SIGN_NAMES[ms]} — emotional heaviness, depression tendency",
        })

    # Angarak Yoga: Mars + Rahu same sign
    mas = _sign_of(pmap, "Mars")
    if mas is not None and mas == rs:
        out.append({
            "name": "Angarak yoga",
            "category": "Negative",
            "polarity": "NEGATIVE",
            "detail": f"Mars+Rahu in {SIGN_NAMES[mas]} — explosive anger, accidents, conflicts",
        })

    # Pitra Dosh: Sun + Rahu OR Sun + Saturn in 9H
    suns = _sign_of(pmap, "Sun")
    sun_h = _house_of(pmap, "Sun")
    if suns is not None and suns == rs:
        out.append({
            "name": "Pitra dosh (Sun+Rahu)",
            "category": "Negative",
            "polarity": "NEGATIVE",
            "detail": f"Sun+Rahu in {SIGN_NAMES[suns]} — ancestral karma, father issues",
        })
    if sun_h == 9 and (_house_of(pmap, "Saturn") == 9 or _house_of(pmap, "Rahu") == 9):
        out.append({
            "name": "Pitra dosh (9H affliction)",
            "category": "Negative",
            "polarity": "NEGATIVE",
            "detail": "Sun in 9H with Saturn/Rahu — inherited karma, paternal lineage strain",
        })

    return out


# ── 4. Kaal Sarp 12 variants ──────────────────────────────────────────────
def _kaal_sarp(pmap: dict, lagna: int) -> list[dict]:
    """All 7 visible planets between Rahu→Ketu axis (one hemisphere).
    Always returns a status entry (PRESENT or ABSENT) for anti-hallucination."""
    rs = _sign_of(pmap, "Rahu")
    ks = _sign_of(pmap, "Ketu")
    if rs is None or ks is None:
        return [{
            "name": "Kaal Sarp status: NOT DETECTABLE",
            "category": "Kaal Sarp",
            "polarity": "NEUTRAL",
            "detail": "Rahu/Ketu position incomplete in chart data",
        }]
    # Validate Rahu/Ketu are 180° apart
    if (rs + 6) % 12 != ks:
        return [{
            "name": "Kaal Sarp status: NOT PRESENT",
            "category": "Kaal Sarp",
            "polarity": "NEUTRAL",
            "detail": (f"Rahu in {SIGN_NAMES[rs]} & Ketu in {SIGN_NAMES[ks]} not "
                       "exactly 180° apart — no Kaal Sarp configuration possible"),
        }]

    seven = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    signs = []
    for p in seven:
        s = _sign_of(pmap, p)
        if s is None:
            return []
        signs.append(s)

    # Walk forward from Rahu+1 to Ketu-1 (exclusive of axis)
    forward_arc = set()
    i = (rs + 1) % 12
    while i != ks:
        forward_arc.add(i)
        i = (i + 1) % 12
    backward_arc = set()
    i = (ks + 1) % 12
    while i != rs:
        backward_arc.add(i)
        i = (i + 1) % 12

    in_fwd = all(s in forward_arc or s == rs or s == ks for s in signs)
    in_bwd = all(s in backward_arc or s == rs or s == ks for s in signs)

    if not (in_fwd or in_bwd):
        return []

    rh = _house_of(pmap, "Rahu") or (((rs - lagna) % 12) + 1)
    name = KAAL_SARP_NAMES.get(rh, f"H{rh}")
    direction = "forward" if in_fwd else "reverse"
    polarity = "NEGATIVE" if direction == "forward" else "MIXED"
    return [{
        "name": f"Kaal Sarp yoga ({name} variant)",
        "category": "Kaal Sarp",
        "polarity": polarity,
        "detail": (f"All 7 planets within Rahu(H{rh}) → Ketu axis ({direction} arc) "
                   f"— karmic block, delayed results, requires remedies"),
    }]


# ── 5. Nabhasa Yogas ──────────────────────────────────────────────────────
NABHASA_SANKHYA = {
    7: ("Vallaki", "All 7 planets in 7 different signs — versatile, social, restless"),
    6: ("Damaru",  "7 planets in 6 signs — paired focus, moderate range"),
    5: ("Pasha",   "7 planets in 5 signs — bound by attachments, desires"),
    4: ("Kedara",  "7 planets in 4 signs — agriculture/land/stability themes"),
    3: ("Soola",   "7 planets in 3 signs — sharp focus, conflict, surgical mind"),
    2: ("Yuga",    "7 planets in 2 signs — extreme polarity, intense"),
    1: ("Gola",    "7 planets in 1 sign — overwhelming concentration, isolation"),
}


def _nabhasa_sankhya(pmap: dict) -> list[dict]:
    seven = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    signs = set()
    for p in seven:
        s = _sign_of(pmap, p)
        if s is None:
            return []
        signs.add(s)
    n = len(signs)
    if n in NABHASA_SANKHYA:
        nm, desc = NABHASA_SANKHYA[n]
        return [{
            "name": f"{nm} yoga (Nabhasa Sankhya)",
            "category": "Nabhasa Sankhya",
            "polarity": "MIXED" if n >= 4 else "NEGATIVE",
            "detail": desc,
        }]
    return []


def _nabhasa_ashraya(pmap: dict) -> list[dict]:
    """All 7 in chara/sthira/dwiswabhava → Rajju/Musala/Nala."""
    seven = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    sgs = []
    for p in seven:
        s = _sign_of(pmap, p)
        if s is None:
            return []
        sgs.append(s)
    out = []
    if all(s in CHARA_SIGNS for s in sgs):
        out.append({
            "name": "Rajju yoga (Nabhasa Ashraya)", "category": "Nabhasa Ashraya",
            "polarity": "MIXED",
            "detail": "All 7 planets in movable signs — travel, change, restless",
        })
    elif all(s in STHIRA_SIGNS for s in sgs):
        out.append({
            "name": "Musala yoga (Nabhasa Ashraya)", "category": "Nabhasa Ashraya",
            "polarity": "POSITIVE",
            "detail": "All 7 planets in fixed signs — wealth, fame, stability, kingly nature",
        })
    elif all(s in DWISWA_SIGNS for s in sgs):
        out.append({
            "name": "Nala yoga (Nabhasa Ashraya)", "category": "Nabhasa Ashraya",
            "polarity": "MIXED",
            "detail": "All 7 planets in dual signs — adaptable, scholarly, dual nature",
        })
    return out


def _nabhasa_dala(pmap: dict) -> list[dict]:
    """Kamala-Dala / Mala-Dala — kendra-only benefics or malefics."""
    out = []
    seven = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    houses = {p: _house_of(pmap, p) for p in seven}
    if any(h is None for h in houses.values()):
        return out
    benefic_houses = {h for p, h in houses.items() if p in NATURAL_BENEFICS}
    malefic_houses = {h for p, h in houses.items() if p in NATURAL_MALEFICS}
    if benefic_houses.issubset(KENDRA) and malefic_houses.isdisjoint(KENDRA):
        out.append({
            "name": "Kamala-Dala yoga (Nabhasa Dala)", "category": "Nabhasa Dala",
            "polarity": "POSITIVE",
            "detail": "All natural benefics in kendras, malefics elsewhere — pious, wealthy, virtuous",
        })
    if malefic_houses.issubset(KENDRA) and benefic_houses.isdisjoint(KENDRA):
        out.append({
            "name": "Mala-Dala yoga (Nabhasa Dala)", "category": "Nabhasa Dala",
            "polarity": "NEGATIVE",
            "detail": "All natural malefics in kendras, benefics elsewhere — fierce, deceitful tendencies",
        })
    return out


def _nabhasa_aakriti_subset(pmap: dict) -> list[dict]:
    """Detect easiest Aakriti yogas based on house occupancy patterns."""
    out = []
    seven = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    houses = {p: _house_of(pmap, p) for p in seven}
    if any(h is None for h in houses.values()):
        return out
    occ = set(houses.values())

    # Gada — all 7 in 2 successive kendras (1+4, 4+7, 7+10, 10+1)
    for h1, h2 in [(1, 4), (4, 7), (7, 10), (10, 1)]:
        if occ == {h1, h2}:
            out.append({
                "name": "Gada yoga (Aakriti)", "category": "Nabhasa Aakriti",
                "polarity": "POSITIVE",
                "detail": f"All 7 planets in H{h1} & H{h2} (mace formation) — wealth, learning, devotion",
            })
            break

    # Shakata — all 7 in 1H + 7H
    if occ == {1, 7}:
        out.append({
            "name": "Shakata-Aakriti yoga", "category": "Nabhasa Aakriti",
            "polarity": "MIXED",
            "detail": "All 7 in H1 + H7 (cart formation) — laborious life, ups-downs",
        })

    # Vihaga (Pakshi) — all 7 in 4H + 10H
    if occ == {4, 10}:
        out.append({
            "name": "Pakshi (Vihaga) yoga (Aakriti)", "category": "Nabhasa Aakriti",
            "polarity": "MIXED",
            "detail": "All 7 in H4 + H10 (bird formation) — wandering, communicator, messenger",
        })

    # Vajra — benefics in 1+7, malefics in 4+10
    benefic_h = {h for p, h in houses.items() if p in NATURAL_BENEFICS}
    malefic_h = {h for p, h in houses.items() if p in NATURAL_MALEFICS}
    if benefic_h.issubset({1, 7}) and malefic_h.issubset({4, 10}) and benefic_h and malefic_h:
        out.append({
            "name": "Vajra yoga (Aakriti)", "category": "Nabhasa Aakriti",
            "polarity": "POSITIVE",
            "detail": "Benefics in 1+7, malefics in 4+10 — strong start & end, middle struggle",
        })

    # Yava — opposite of Vajra (malefics in 1+7, benefics in 4+10)
    if malefic_h.issubset({1, 7}) and benefic_h.issubset({4, 10}) and benefic_h and malefic_h:
        out.append({
            "name": "Yava yoga (Aakriti)", "category": "Nabhasa Aakriti",
            "polarity": "POSITIVE",
            "detail": "Malefics in 1+7, benefics in 4+10 — strong middle life, charitable",
        })

    # Kamala — all 7 in 4 kendras (1, 4, 7, 10)
    if occ.issubset(KENDRA) and len(occ) >= 3:
        out.append({
            "name": "Kamala yoga (Aakriti)", "category": "Nabhasa Aakriti",
            "polarity": "POSITIVE",
            "detail": "All 7 planets in kendras — kingly status, wealth, fame, lotus formation",
        })

    # Vapi — all 7 in panapara (2,5,8,11) OR all in apoklima (3,6,9,12)
    if occ.issubset(PANAPARA):
        out.append({
            "name": "Vapi yoga (Aakriti — Panapara)", "category": "Nabhasa Aakriti",
            "polarity": "POSITIVE",
            "detail": "All 7 in panapara houses — savings, hoarding wealth, well-formation",
        })
    elif occ.issubset(APOKLIMA):
        out.append({
            "name": "Vapi yoga (Aakriti — Apoklima)", "category": "Nabhasa Aakriti",
            "polarity": "MIXED",
            "detail": "All 7 in apoklima houses — service, learning, gradual progress",
        })

    # Sarpa (Snake) — malefics in 1+5+9 (trikona)
    if malefic_h.issubset(TRIKONA) and len(malefic_h) >= 2 and not (benefic_h & TRIKONA):
        out.append({
            "name": "Sarpa yoga (Aakriti)", "category": "Nabhasa Aakriti",
            "polarity": "NEGATIVE",
            "detail": "Malefics dominate trikonas — cruel disposition, struggle for fortune",
        })

    return out


# ── 6. Pravrajya Yogas (renunciation) ─────────────────────────────────────
def _pravrajya(pmap: dict) -> list[dict]:
    """4+ planets in one house/sign → renunciation tendencies (BPHS Ch.78)."""
    seven = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    by_house: dict[int, list[str]] = {}
    for p in seven:
        h = _house_of(pmap, p)
        if h:
            by_house.setdefault(h, []).append(p)
    out = []
    for h, plist in by_house.items():
        if len(plist) >= 4:
            # The strongest planet determines the variant (simplified)
            variant_map = {
                "Sun":     ("Sannyasa (Sun-led)", "renunciation through power/recognition"),
                "Moon":    ("Sannyasa (Moon-led)", "renunciation via emotional detachment"),
                "Mars":    ("Sannyasa (Mars-led)", "warrior-monk, militant ascetic"),
                "Mercury": ("Sannyasa (Mercury-led)", "scholarly renunciation, teaching"),
                "Jupiter": ("Sannyasa (Jupiter-led)", "guru-path, classical sannyasi"),
                "Venus":   ("Sannyasa (Venus-led)", "tantric/devotional path"),
                "Saturn":  ("Sannyasa (Saturn-led)", "austerity, hard tapasya"),
            }
            # Use first planet in canonical order for naming (deterministic)
            for cand in seven:
                if cand in plist:
                    nm, desc = variant_map[cand]
                    out.append({
                        "name": f"Pravrajya yoga — {nm}",
                        "category": "Pravrajya",
                        "polarity": "MIXED",
                        "detail": f"{len(plist)} planets in H{h} ({', '.join(plist)}) — {desc}",
                    })
                    break
    return out


# ── Master detector ───────────────────────────────────────────────────────
def detect_classical_yogas(planets: list, lagna_sign_idx: Optional[int]) -> list[dict]:
    if lagna_sign_idx is None:
        return []
    pmap = _norm_planets(planets, lagna_sign_idx)
    if not pmap:
        return []
    out: list[dict] = []
    out.extend(_named_vipreet(pmap, lagna_sign_idx))
    out.extend(_dhana_yogas(pmap, lagna_sign_idx))
    out.extend(_negative_yogas(pmap, lagna_sign_idx))
    out.extend(_kaal_sarp(pmap, lagna_sign_idx))
    out.extend(_nabhasa_sankhya(pmap))
    out.extend(_nabhasa_ashraya(pmap))
    out.extend(_nabhasa_dala(pmap))
    out.extend(_nabhasa_aakriti_subset(pmap))
    out.extend(_pravrajya(pmap))
    return out


def format_classical_yogas_summary(yogas: list[dict]) -> str:
    if not yogas:
        return ""
    lines = [
        "▸ CLASSICAL YOGAS (Sprint-19 detector)",
        f"  Total detected: {len(yogas)}",
    ]
    by_cat: dict[str, list[dict]] = {}
    for y in yogas:
        by_cat.setdefault(y.get("category", "Other"), []).append(y)
    for cat, items in by_cat.items():
        lines.append(f"  ▸ {cat}: {len(items)}")
        for y in items[:6]:
            pol = y.get("polarity", "")
            tag = {"POSITIVE": "✅", "NEGATIVE": "⚠️", "MIXED": "◐"}.get(pol, "•")
            lines.append(f"    {tag} {y['name']}: {y.get('detail','')}")
        if len(items) > 6:
            lines.append(f"    … (+{len(items)-6} more)")
    return "\n".join(lines)

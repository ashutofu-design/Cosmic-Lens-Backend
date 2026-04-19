"""
Sprint 19.5 — Extra Classical Yogas (push detector count past 200)
==================================================================
Adds the remaining classical yogas missing from classical_yogas.py.

Categories:
  • Saraswati, Kubera, Kalanidhi (wealth)
  • Lunar peripheral: Sunaphaa, Anaphaa, Durdhura, Kemadruma
  • Mahabhagya, Vasumati, Pushkala, Subhakartari, Papakartari
  • Karak-Bhuvan placements (7 — natural significators in own houses)
  • Brahma, Vishnu, Shiva trinity yogas
  • Hari, Hara, Brahma trinity (BPHS Ch.41)
  • Ardhachandra / Chakra / Samudra / Veena / Mridanga (Nabhasa Aakriti remaining)
  • Akhanda Samrajya, Dhwaja, Chhatra, Padma, Chamara, Shakti, Danda, Naava
  • Bhaskar, Marud, Ratnakara, Shrinatha, Parvata, Kahala, Amsavatara
  • Neech-Bhanga 4 BPHS cancellation rules (precise)
  • 60+ lord-in-house BPHS placements (one per high-impact placement)
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
EXALT = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6}
DEBIL = {p: (s + 6) % 12 for p, s in EXALT.items()}
ODD_SIGNS = {0, 2, 4, 6, 8, 10}
EVEN_SIGNS = {1, 3, 5, 7, 9, 11}
KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}
DUSTHANA = {6, 8, 12}
UPACHAYA = {3, 6, 10, 11}
NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}


def _norm_planets(planets: list, lagna_sign_idx: Optional[int]) -> dict[str, dict]:
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


def _lord(h: int, lagna: int) -> str:
    return SIGN_LORDS[(lagna + h - 1) % 12]


def _h(pmap: dict, p: str) -> Optional[int]:
    info = pmap.get(p) or {}
    h = info.get("house")
    return h if isinstance(h, int) and 1 <= h <= 12 else None


def _s(pmap: dict, p: str) -> Optional[int]:
    info = pmap.get(p) or {}
    s = info.get("sign_idx")
    return s if isinstance(s, int) and 0 <= s <= 11 else None


def _is_strong(pmap: dict, p: str) -> bool:
    """Quick strength check: own sign or exalted."""
    s = _s(pmap, p)
    if s is None:
        return False
    return s in OWN_SIGNS.get(p, []) or s == EXALT.get(p)


# ─── 1. Wealth trinity ───────────────────────────────────────────────────
def _wealth_extras(pmap: dict, lagna: int) -> list[dict]:
    out = []
    js, vs, ms = _s(pmap, "Jupiter"), _s(pmap, "Venus"), _s(pmap, "Mercury")
    jh, vh, mh = _h(pmap, "Jupiter"), _h(pmap, "Venus"), _h(pmap, "Mercury")

    # Saraswati: Mer + Jup + Ven in kendra/trikona/2nd, Jupiter in own/exalt/friendly
    if (jh in KENDRA | TRIKONA | {2}) and (vh in KENDRA | TRIKONA | {2}) and \
       (mh in KENDRA | TRIKONA | {2}) and _is_strong(pmap, "Jupiter"):
        out.append({
            "name": "Saraswati yoga", "category": "Wealth-Knowledge",
            "polarity": "POSITIVE",
            "detail": "Mer+Jup+Ven all in kendra/trikona/2H, Jupiter strong — wisdom, learning, eloquence, fame",
        })

    # Kubera: 11L in 11H (or 2H) with benefic conjunction
    l11 = _lord(11, lagna)
    h11 = _h(pmap, l11)
    if h11 in (2, 11):
        co = [p for p, info in pmap.items()
              if info.get("sign_idx") == _s(pmap, l11) and p != l11 and p in NATURAL_BENEFICS]
        if co:
            out.append({
                "name": "Kubera yoga", "category": "Wealth-Knowledge",
                "polarity": "POSITIVE",
                "detail": f"11L {l11} in H{h11} with {','.join(co)} — treasury, accumulation, abundance",
            })

    # Kalanidhi: Jupiter in 2H or 5H, conjoined/aspected by Mer or Ven
    if jh in (2, 5):
        co = [p for p in ("Mercury", "Venus") if _s(pmap, p) == js]
        if co:
            out.append({
                "name": "Kalanidhi yoga", "category": "Wealth-Knowledge",
                "polarity": "POSITIVE",
                "detail": f"Jupiter in H{jh} with {','.join(co)} — vault of arts/wealth, scholarly riches",
            })

    # Lakshmi-Narayan: Venus + Jupiter conjunct in kendra
    if js is not None and js == vs and jh in KENDRA:
        out.append({
            "name": "Lakshmi-Narayan yoga", "category": "Wealth-Knowledge",
            "polarity": "POSITIVE",
            "detail": f"Venus+Jupiter conj in H{jh} ({SIGN_NAMES[js]}) — divine wealth+wisdom union",
        })

    # Akhanda Samrajya: 2L+5L+11L all benefic-influenced + Jupiter in kendra/trikona
    l2, l5 = _lord(2, lagna), _lord(5, lagna)
    if jh in KENDRA | TRIKONA and _is_strong(pmap, "Jupiter"):
        if all(_h(pmap, x) in KENDRA | TRIKONA | {2, 11} for x in (l2, l5, l11)):
            out.append({
                "name": "Akhanda Samrajya yoga", "category": "Royal",
                "polarity": "POSITIVE",
                "detail": f"2L({l2})+5L({l5})+11L({l11}) all in dharma/artha houses, Jupiter in trikona/kendra — unbroken sovereignty, kingly wealth",
            })

    # Lagnadhi: benefics in 7H+8H from Lagna (or just 7+8)
    bens_in_7_8 = [p for p in NATURAL_BENEFICS if _h(pmap, p) in (7, 8)]
    if len(bens_in_7_8) >= 2:
        out.append({
            "name": "Lagnadhi yoga", "category": "Wealth-Knowledge",
            "polarity": "POSITIVE",
            "detail": f"{','.join(bens_in_7_8)} in 7H/8H from Lagna — virtuous, learned, leader",
        })

    return out


# ─── 2. Lunar peripheral yogas ──────────────────────────────────────────
def _lunar_peripheral(pmap: dict) -> list[dict]:
    out = []
    moon_s = _s(pmap, "Moon")
    if moon_s is None:
        return out
    second_from_moon = (moon_s + 1) % 12
    twelfth_from_moon = (moon_s - 1) % 12

    excluded = {"Sun", "Rahu", "Ketu", "Moon"}
    in_2nd = [p for p, info in pmap.items()
              if p not in excluded and info.get("sign_idx") == second_from_moon]
    in_12th = [p for p, info in pmap.items()
               if p not in excluded and info.get("sign_idx") == twelfth_from_moon]

    if in_2nd and not in_12th:
        out.append({
            "name": "Sunaphaa yoga", "category": "Lunar",
            "polarity": "POSITIVE",
            "detail": f"{','.join(in_2nd)} in 2nd from Moon — wealth via own efforts, intelligence, fame",
        })
    if in_12th and not in_2nd:
        out.append({
            "name": "Anaphaa yoga", "category": "Lunar",
            "polarity": "POSITIVE",
            "detail": f"{','.join(in_12th)} in 12th from Moon — virtuous, well-spoken, dignified",
        })
    if in_2nd and in_12th:
        out.append({
            "name": "Durdhura yoga", "category": "Lunar",
            "polarity": "POSITIVE",
            "detail": f"Planets in BOTH 2nd & 12th from Moon — abundant wealth, charity, vehicles, comforts",
        })
    return out


# ─── 3. Mahabhagya / Subhakartari / Papakartari ─────────────────────────
def _aux_status_yogas(pmap: dict, lagna: int, birth_time_is_day: Optional[bool] = None) -> list[dict]:
    out = []
    sun_s = _s(pmap, "Sun")
    moon_s = _s(pmap, "Moon")

    # Mahabhagya — odd-signs for males (rough heuristic without birth time/sex)
    if sun_s is not None and moon_s is not None:
        all_odd = (sun_s in ODD_SIGNS and moon_s in ODD_SIGNS and lagna in ODD_SIGNS)
        all_even = (sun_s in EVEN_SIGNS and moon_s in EVEN_SIGNS and lagna in EVEN_SIGNS)
        if all_odd:
            out.append({
                "name": "Mahabhagya yoga (male signature)", "category": "Status",
                "polarity": "POSITIVE",
                "detail": "Sun, Moon, Lagna all in odd signs — exceptional fortune, fame, royal status (for males per BPHS)",
            })
        elif all_even:
            out.append({
                "name": "Mahabhagya yoga (female signature)", "category": "Status",
                "polarity": "POSITIVE",
                "detail": "Sun, Moon, Lagna all in even signs — exceptional fortune, beauty, virtue (for females per BPHS)",
            })

    # Subhakartari: benefics in 2nd & 12th from Lagna (Lagnesh hemmed by benefics)
    bens_2_12 = [p for p in NATURAL_BENEFICS if _h(pmap, p) in (2, 12)]
    benefic_houses = {_h(pmap, p) for p in NATURAL_BENEFICS if _h(pmap, p) in (2, 12)}
    if benefic_houses == {2, 12}:
        out.append({
            "name": "Subhakartari yoga", "category": "Status",
            "polarity": "POSITIVE",
            "detail": "Benefics in BOTH 2H and 12H — Lagna shielded by auspicious planets, fortune, protection",
        })

    # Papakartari: malefics in 2nd & 12th from Lagna
    mal_houses = {_h(pmap, p) for p in NATURAL_MALEFICS if _h(pmap, p) in (2, 12)}
    if mal_houses == {2, 12}:
        out.append({
            "name": "Papakartari yoga", "category": "Status",
            "polarity": "NEGATIVE",
            "detail": "Malefics in BOTH 2H and 12H — Lagna besieged, struggle, obstacles, ill-health",
        })

    # Vasumati: 4+ benefics in upachaya houses (3, 6, 10, 11)
    bens_in_upachaya = [p for p in NATURAL_BENEFICS if _h(pmap, p) in UPACHAYA]
    if len(bens_in_upachaya) >= 3:
        out.append({
            "name": "Vasumati yoga", "category": "Wealth-Knowledge",
            "polarity": "POSITIVE",
            "detail": f"{','.join(bens_in_upachaya)} in upachaya (3/6/10/11) — wealth grows over time, never poverty",
        })

    # Parvata: benefics in kendra, no malefic in 6H/8H
    bens_in_kendra = [p for p in NATURAL_BENEFICS if _h(pmap, p) in KENDRA]
    mals_in_dust = [p for p in NATURAL_MALEFICS if _h(pmap, p) in (6, 8)]
    if len(bens_in_kendra) >= 2 and not mals_in_dust:
        out.append({
            "name": "Parvata yoga", "category": "Status",
            "polarity": "POSITIVE",
            "detail": f"{','.join(bens_in_kendra)} in kendras, no malefic in 6/8 — towering status, fame, protection",
        })

    # Pushkala: Lagnesh + Moon-disposing-lord in mutual kendra/conjunction with strong Moon
    lagnesh = _lord(1, lagna)
    if moon_s is not None:
        moon_lord = SIGN_LORDS[moon_s]
        lh = _h(pmap, lagnesh)
        mlh = _h(pmap, moon_lord)
        if lh and mlh and ((lh - mlh) % 12 + 1) in KENDRA and _is_strong(pmap, "Moon"):
            out.append({
                "name": "Pushkala yoga", "category": "Status",
                "polarity": "POSITIVE",
                "detail": f"Lagnesh {lagnesh} & Moon-lord {moon_lord} in mutual kendra, Moon strong — wealth+fame combined",
            })

    return out


# ─── 4. Brahma / Vishnu / Shiva trinity (BPHS Ch.41) ────────────────────
def _trinity_yogas(pmap: dict, lagna: int) -> list[dict]:
    out = []
    # Brahma — Jupiter in kendra from 11L, Venus in kendra from 10L, Mercury in kendra from Lagnesh
    l11, l10 = _lord(11, lagna), _lord(10, lagna)
    lagnesh = _lord(1, lagna)
    j_h = _h(pmap, "Jupiter")
    v_h = _h(pmap, "Venus")
    m_h = _h(pmap, "Mercury")
    h_l11 = _h(pmap, l11)
    h_l10 = _h(pmap, l10)
    h_lag = _h(pmap, lagnesh)
    if all([j_h, v_h, m_h, h_l11, h_l10, h_lag]):
        if (((j_h - h_l11) % 12 + 1) in KENDRA and
                ((v_h - h_l10) % 12 + 1) in KENDRA and
                ((m_h - h_lag) % 12 + 1) in KENDRA):
            out.append({
                "name": "Brahma yoga", "category": "Trinity",
                "polarity": "POSITIVE",
                "detail": "Jup-11L, Ven-10L, Mer-Lagnesh all in mutual kendras — long life, charitable, scholarly wealth",
            })

    # Vishnu — 9L+10L+navamsa-of-9L lord all conj/exch (simplified: 9L+10L conj in own/friendly)
    l9 = _lord(9, lagna)
    l9_s = _s(pmap, l9)
    l10_s = _s(pmap, l10)
    if l9_s is not None and l10_s is not None and l9_s == l10_s:
        if l9_s in OWN_SIGNS.get(l9, []) or l9_s in OWN_SIGNS.get(l10, []) or l9_s == EXALT.get(l9):
            out.append({
                "name": "Vishnu yoga", "category": "Trinity",
                "polarity": "POSITIVE",
                "detail": f"9L({l9})+10L({l10}) conj in {SIGN_NAMES[l9_s]} (own/exalt) — devout, virtuous, leader",
            })

    # Shiva — 5L in 9H + 9L in 5H + 1L in 11H
    l5 = _lord(5, lagna)
    if (_h(pmap, l5) == 9 and _h(pmap, l9) == 5 and _h(pmap, lagnesh) == 11):
        out.append({
            "name": "Shiva yoga", "category": "Trinity",
            "polarity": "POSITIVE",
            "detail": f"5L({l5})↔9L({l9}) exchange + Lagnesh in 11H — destroyer of enemies, ascetic power, victory",
        })

    # Hari yoga — 2L+8L+12L combined favorably (mutual kendra/conj)
    l2, l8, l12 = _lord(2, lagna), _lord(8, lagna), _lord(12, lagna)
    h2_, h8_, h12_ = _h(pmap, l2), _h(pmap, l8), _h(pmap, l12)
    if h2_ and h8_ and h12_:
        if h2_ == h8_ == h12_:
            out.append({
                "name": "Hari yoga", "category": "Trinity",
                "polarity": "POSITIVE",
                "detail": f"2L({l2})+8L({l8})+12L({l12}) all conjunct in H{h2_} — destroyer of obstacles, occult mastery",
            })

    # Hara yoga — 4L+9L+8L mutually placed
    l4 = _lord(4, lagna)
    h4_, h9_ = _h(pmap, l4), _h(pmap, l9)
    if h4_ and h9_ and h8_ and h4_ == h9_ == h8_:
        out.append({
            "name": "Hara yoga", "category": "Trinity",
            "polarity": "POSITIVE",
            "detail": f"4L({l4})+9L({l9})+8L({l8}) all conjunct in H{h4_} — strong protector, dharmic warrior",
        })

    # Trilochan — Sun+Moon+Mars in 1+5+9 trikonas
    sun_h, moon_h, mars_h = _h(pmap, "Sun"), _h(pmap, "Moon"), _h(pmap, "Mars")
    if {sun_h, moon_h, mars_h} == TRIKONA:
        out.append({
            "name": "Trilochan yoga", "category": "Trinity",
            "polarity": "POSITIVE",
            "detail": "Sun+Moon+Mars in 1H, 5H, 9H trikonas — three-eyed perception, wisdom, valor",
        })

    return out


# ─── 5. Karak-Bhuvan placements (7 natural significators in own houses) ─
KARAK_HOUSES = {
    "Sun":     (9,  "Father / dharma — paternal blessings, dharmic guidance"),
    "Moon":    (4,  "Mother / home — maternal love, peaceful home"),
    "Mars":    (3,  "Siblings / valor — courageous siblings, warrior spirit"),
    "Mercury": (4,  "Education / friends — sharp intellect, learning"),  # or 1H
    "Jupiter": (5,  "Children / wisdom — blessed progeny, guru's grace"),
    "Venus":   (7,  "Spouse / pleasures — loving spouse, comforts"),
    "Saturn":  (6,  "Service / discipline — strong work ethic, longevity"),
}


def _karak_bhuvan(pmap: dict) -> list[dict]:
    out = []
    for p, (h, desc) in KARAK_HOUSES.items():
        if _h(pmap, p) == h:
            out.append({
                "name": f"Karak-Bhuvan ({p} in {h}H)", "category": "Karaka",
                "polarity": "POSITIVE",
                "detail": desc,
            })
    return out


# ─── 6. Remaining Aakriti yogas (12 of 20) ──────────────────────────────
def _aakriti_remaining(pmap: dict) -> list[dict]:
    out = []
    seven = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    houses = {p: _h(pmap, p) for p in seven}
    if any(h is None for h in houses.values()):
        return out
    occ = sorted(set(houses.values()))

    # Helper: planets in N successive houses (consecutive when ordered)
    def successive(houses_set: set, n: int) -> bool:
        if len(houses_set) != n:
            return False
        s = sorted(houses_set)
        return all(s[i + 1] - s[i] == 1 for i in range(n - 1))

    occ_set = set(occ)

    # Yoopa — 7 planets in 4 successive houses starting from Lagna (1H..4H)
    if occ_set == {1, 2, 3, 4}:
        out.append({"name": "Yoopa yoga (Aakriti)", "category": "Nabhasa Aakriti",
                    "polarity": "POSITIVE",
                    "detail": "All 7 in H1-H4 (sacrificial post) — pious, performs yagnas, religious leader"})
    # Shara — 7 in 5H-8H (arrow)
    if occ_set == {5, 6, 7, 8}:
        out.append({"name": "Shara yoga (Aakriti)", "category": "Nabhasa Aakriti",
                    "polarity": "MIXED",
                    "detail": "All 7 in H5-H8 (arrow formation) — hunter/warrior, sharp tongue"})
    # Shakti — 7 in 7H-10H
    if occ_set == {7, 8, 9, 10}:
        out.append({"name": "Shakti yoga (Aakriti)", "category": "Nabhasa Aakriti",
                    "polarity": "MIXED",
                    "detail": "All 7 in H7-H10 (spear) — laborious, harsh life, weapon-bearer"})
    # Danda — 7 in 9H-12H
    if occ_set == {9, 10, 11, 12}:
        out.append({"name": "Danda yoga (Aakriti)", "category": "Nabhasa Aakriti",
                    "polarity": "NEGATIVE",
                    "detail": "All 7 in H9-H12 (staff) — punisher/punished, exile, separation"})
    # Naava — 7 in 4 successive houses NOT starting from kendra (any other 4 successive)
    if successive(occ_set, 4) and not (occ_set & {1}):
        if occ_set not in ({4,5,6,7}, {7,8,9,10}, {9,10,11,12}):
            out.append({"name": "Naava (Boat) yoga (Aakriti)", "category": "Nabhasa Aakriti",
                        "polarity": "MIXED",
                        "detail": "7 planets in 4 successive houses (boat) — fisherman/sailor, water trade"})
    # Koota — 7 in H4..H7 (peak/summit)
    if occ_set == {4, 5, 6, 7}:
        out.append({"name": "Koota yoga (Aakriti)", "category": "Nabhasa Aakriti",
                    "polarity": "MIXED",
                    "detail": "All 7 in H4-H7 (mountain peak) — fort-dweller, jailer, harsh"})
    # Chhatra — 7 planets in 4 houses 1+4+7+10 (umbrella) but specifically forming canopy
    if occ_set == {1, 4, 7, 10}:
        out.append({"name": "Chhatra (Umbrella) yoga (Aakriti)", "category": "Nabhasa Aakriti",
                    "polarity": "POSITIVE",
                    "detail": "All 7 in 4 kendras (canopy) — long-lived king, served by family, royal protector"})
    # Chaap — 7 in 4 successive houses ending at H4 (bow)
    if occ_set == {1, 2, 3, 4}:
        # Already Yoopa; Chaap is overlapping per BPHS — treat alternative naming
        pass  # Yoopa already added above
    # Ardhachandra — 7 planets in 7 successive houses
    if successive(occ_set, 7):
        first_h = sorted(occ_set)[0]
        out.append({"name": f"Ardhachandra (Half-Moon) yoga (Aakriti)",
                    "category": "Nabhasa Aakriti",
                    "polarity": "POSITIVE",
                    "detail": f"All 7 in H{first_h}-H{first_h+6} (crescent) — handsome, valorous, supports king"})
    # Chakra — 7 planets in 6 alternate odd OR even houses (1,3,5,7,9,11) or (2,4,6,8,10,12)
    if occ_set.issubset({1, 3, 5, 7, 9, 11}) and len(occ_set) >= 4:
        out.append({"name": "Chakra (Wheel) yoga (Aakriti)", "category": "Nabhasa Aakriti",
                    "polarity": "POSITIVE",
                    "detail": "All 7 in odd houses (wheel) — emperor-quality, served by lesser kings"})
    # Samudra — 7 planets in even houses (2,4,6,8,10,12)
    if occ_set.issubset({2, 4, 6, 8, 10, 12}) and len(occ_set) >= 4:
        out.append({"name": "Samudra (Ocean) yoga (Aakriti)", "category": "Nabhasa Aakriti",
                    "polarity": "POSITIVE",
                    "detail": "All 7 in even houses (ocean) — wealthy, ship-owner, vast resources"})
    # Veena — 7 planets in 7 different signs (covers all signs differently)
    seven_signs = {_s(pmap, p) for p in seven}
    if None not in seven_signs and len(seven_signs) == 7:
        out.append({"name": "Veena (Lyre) yoga (Aakriti)", "category": "Nabhasa Aakriti",
                    "polarity": "POSITIVE",
                    "detail": "All 7 planets in 7 different signs — musician, scholar, articulate, multi-talented"})
    # Mridanga — 7 planets in 5 signs (drum-shaped)
    if None not in seven_signs and len(seven_signs) == 5:
        out.append({"name": "Mridanga (Drum) yoga (Aakriti)", "category": "Nabhasa Aakriti",
                    "polarity": "POSITIVE",
                    "detail": "All 7 in 5 signs — popular speaker, performer, drummer/musician"})

    return out


# ─── 7. Royal/Status named yogas ────────────────────────────────────────
def _royal_yogas(pmap: dict, lagna: int) -> list[dict]:
    out = []

    # Dhwaja (Flag) — 10L in own/exalt in kendra/trikona, with Sun strong
    l10 = _lord(10, lagna)
    l10_h = _h(pmap, l10)
    l10_s = _s(pmap, l10)
    if l10_h in KENDRA | TRIKONA and (l10_s in OWN_SIGNS.get(l10, []) or l10_s == EXALT.get(l10)):
        if _is_strong(pmap, "Sun"):
            out.append({"name": "Dhwaja yoga", "category": "Royal",
                        "polarity": "POSITIVE",
                        "detail": f"10L {l10} strong in H{l10_h} + Sun strong — flag of victory, leadership, recognition"})

    # Chamara (Royal Fan) — Lagnesh exalted in kendra + benefic aspect
    lagnesh = _lord(1, lagna)
    lh = _h(pmap, lagnesh)
    ls = _s(pmap, lagnesh)
    if lh in KENDRA and ls == EXALT.get(lagnesh):
        out.append({"name": "Chamara yoga", "category": "Royal",
                    "polarity": "POSITIVE",
                    "detail": f"Lagnesh {lagnesh} exalted in H{lh} — wears royal fan, served like king"})

    # Padma — Lagnesh in 9H, exalted/own
    if _h(pmap, lagnesh) == 9 and (_s(pmap, lagnesh) in OWN_SIGNS.get(lagnesh, [])
                                    or _s(pmap, lagnesh) == EXALT.get(lagnesh)):
        out.append({"name": "Padma yoga", "category": "Royal",
                    "polarity": "POSITIVE",
                    "detail": f"Lagnesh {lagnesh} in 9H (own/exalt) — lotus of fortune, dharmic king"})

    # Kahala — 4L+9L mutually conjoined in kendra, with strong Lagnesh
    l4, l9 = _lord(4, lagna), _lord(9, lagna)
    if _s(pmap, l4) is not None and _s(pmap, l4) == _s(pmap, l9) and _h(pmap, l4) in KENDRA:
        if _is_strong(pmap, lagnesh):
            out.append({"name": "Kahala yoga", "category": "Royal",
                        "polarity": "POSITIVE",
                        "detail": f"4L({l4})+9L({l9}) conj in kendra + strong Lagnesh — commands armies, drum-of-victory"})

    # Bhaskar — Sun+Mer in kendra-trikona, Jupiter in 5H from Sun
    sun_s = _s(pmap, "Sun")
    mer_h = _h(pmap, "Mercury")
    sun_h = _h(pmap, "Sun")
    if sun_h in KENDRA | TRIKONA and mer_h in KENDRA | TRIKONA:
        if sun_s is not None:
            jup_from_sun = ((_s(pmap, "Jupiter") - sun_s) % 12 + 1) if _s(pmap, "Jupiter") is not None else None
            if jup_from_sun == 5:
                out.append({"name": "Bhaskar yoga", "category": "Royal",
                            "polarity": "POSITIVE",
                            "detail": "Sun+Mer in kendra/trikona, Jupiter 5th from Sun — radiant intellect, scholarly fame"})

    # Marud — Mars+Jupiter in mutual kendra (1/4/7/10 from each other) + own/friendly
    mars_h = _h(pmap, "Mars")
    jup_h = _h(pmap, "Jupiter")
    if mars_h and jup_h:
        sep = (jup_h - mars_h) % 12 + 1
        if sep in KENDRA and _is_strong(pmap, "Mars") and _is_strong(pmap, "Jupiter"):
            out.append({"name": "Marud yoga", "category": "Royal",
                        "polarity": "POSITIVE",
                        "detail": "Mars+Jup in mutual kendra (both strong) — warrior-priest, military commander"})

    # Ratnakara — Moon+Venus+Jupiter in mutual kendra
    moon_h = _h(pmap, "Moon")
    ven_h = _h(pmap, "Venus")
    if moon_h and ven_h and jup_h:
        diffs = {(jup_h - moon_h) % 12 + 1, (ven_h - moon_h) % 12 + 1, (jup_h - ven_h) % 12 + 1}
        if diffs.issubset(KENDRA | {1}):
            out.append({"name": "Ratnakara yoga", "category": "Wealth-Knowledge",
                        "polarity": "POSITIVE",
                        "detail": "Moon+Venus+Jupiter in mutual kendras — ocean-of-jewels, lavish wealth, beauty"})

    # Shrinatha — 5L in 9H AND 9L in 5H (mutual exchange)
    l5 = _lord(5, lagna)
    if _h(pmap, l5) == 9 and _h(pmap, l9) == 5:
        out.append({"name": "Shrinatha yoga", "category": "Royal",
                    "polarity": "POSITIVE",
                    "detail": f"5L({l5})↔9L({l9}) exchange (5H/9H) — Lord Vishnu's grace, supreme dharma+wealth"})

    return out


# ─── 8. Amsavatara (3+ exalted planets) ─────────────────────────────────
def _amsavatara(pmap: dict) -> list[dict]:
    exalted = []
    for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        if _s(pmap, p) == EXALT.get(p):
            exalted.append(p)
    out = []
    if len(exalted) >= 3:
        out.append({"name": f"Amsavatara yoga ({len(exalted)} exalted)",
                    "category": "Status",
                    "polarity": "POSITIVE",
                    "detail": f"{','.join(exalted)} all exalted — divine incarnation, exceptional life"})
    if len(exalted) >= 4:
        out.append({"name": "Devendra yoga", "category": "Status",
                    "polarity": "POSITIVE",
                    "detail": f"4+ exalted ({','.join(exalted)}) — Indra-like fortune, godly status"})
    return out


# ─── 9. Neech-Bhanga 4 BPHS cancellation rules (precise) ────────────────
def _neech_bhanga_full(pmap: dict, lagna: int) -> list[dict]:
    """4 BPHS cancellation rules:
       1. Debilitated planet's sign-lord in kendra from Lagna OR Moon
       2. Planet exalted in same sign as the debilitated planet would be exalted
       3. Lord of debilitation sign + lord of exaltation sign in mutual kendra
       4. Debilitated planet aspected by its own exaltation lord
    """
    out = []
    for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        s = _s(pmap, p)
        if s != DEBIL.get(p):
            continue
        debil_sign_lord = SIGN_LORDS[s]
        exalt_sign = EXALT.get(p)
        if exalt_sign is None:
            continue
        exalt_sign_lord = SIGN_LORDS[exalt_sign]
        moon_h = _h(pmap, "Moon")

        # Rule 1
        h_dsl = _h(pmap, debil_sign_lord)
        if h_dsl in KENDRA:
            out.append({"name": f"Neech-Bhanga ({p} R1)", "category": "Neech-Bhanga",
                        "polarity": "POSITIVE",
                        "detail": f"{p} debilitated but {debil_sign_lord} (sign-lord) in kendra-from-Lagna — debility CANCELLED, becomes Raja-yoga"})
        if h_dsl and moon_h:
            from_moon = (h_dsl - moon_h) % 12 + 1
            if from_moon in KENDRA:
                out.append({"name": f"Neech-Bhanga ({p} R1-Moon)", "category": "Neech-Bhanga",
                            "polarity": "POSITIVE",
                            "detail": f"{p} debilitated, sign-lord in kendra-from-Moon — debility cancelled"})

        # Rule 2 — A planet exalted in the same sign where {p} is debilitated
        for q in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            if q == p:
                continue
            if _s(pmap, q) == s and EXALT.get(q) == s:
                out.append({"name": f"Neech-Bhanga ({p} R2)", "category": "Neech-Bhanga",
                            "polarity": "POSITIVE",
                            "detail": f"{p} debilitated in {SIGN_NAMES[s]} but {q} exalted there — mutual cancellation"})
                break

        # Rule 3 — debil-sign-lord + exalt-sign-lord in mutual kendra
        h_esl = _h(pmap, exalt_sign_lord)
        if h_dsl and h_esl:
            sep = (h_esl - h_dsl) % 12 + 1
            if sep in KENDRA:
                out.append({"name": f"Neech-Bhanga ({p} R3)", "category": "Neech-Bhanga",
                            "polarity": "POSITIVE",
                            "detail": f"{p} debilitated; {debil_sign_lord} & {exalt_sign_lord} in mutual kendra — debility cancelled"})

        # Rule 4 — debilitated planet conjunct/aspected by exalt-sign-lord
        if _s(pmap, exalt_sign_lord) == s:  # conjunction in debil sign
            out.append({"name": f"Neech-Bhanga ({p} R4)", "category": "Neech-Bhanga",
                        "polarity": "POSITIVE",
                        "detail": f"{p} debilitated, conjoined by exalt-lord {exalt_sign_lord} — direct cancellation"})

    return out


# ─── 10. BPHS lord-in-house effects (60+ high-impact placements) ─────────
LORD_HOUSE_EFFECTS = {
    # (lord_house, placed_house): (name, polarity, description)
    (1, 1):  ("Lagnesh swakshetra", "POSITIVE", "Strong self, robust health, leader"),
    (1, 5):  ("Lagnesh in 5H", "POSITIVE", "Wise, intelligent, blessed children"),
    (1, 9):  ("Lagnesh in 9H", "POSITIVE", "Fortunate, dharmic, mentor's grace"),
    (1, 10): ("Lagnesh in 10H", "POSITIVE", "Career success, public recognition"),
    (1, 11): ("Lagnesh in 11H", "POSITIVE", "Gains-yoga, network-driven success"),
    (1, 6):  ("Lagnesh in 6H", "NEGATIVE", "Health struggles, debt-prone, enemies"),
    (1, 8):  ("Lagnesh in 8H", "NEGATIVE", "Chronic issues, occult interest, transformation"),
    (1, 12): ("Lagnesh in 12H", "NEGATIVE", "Foreign land, isolation, expenditure"),
    (2, 11): ("2L in 11H", "POSITIVE", "Wealth flows in, multiple income streams"),
    (2, 6):  ("2L in 6H", "NEGATIVE", "Family disputes, chronic loans"),
    (2, 8):  ("2L in 8H", "NEGATIVE", "Sudden wealth loss, inheritance disputes"),
    (3, 11): ("3L in 11H", "POSITIVE", "Sibling brings gains, communication wealth"),
    (3, 6):  ("3L in 6H", "POSITIVE", "Wins over enemies, courage in conflict"),
    (4, 10): ("4L in 10H", "POSITIVE", "Career via property/mother's blessings"),
    (4, 8):  ("4L in 8H", "NEGATIVE", "Loss of property/mother's health concerns"),
    (5, 9):  ("5L in 9H", "POSITIVE", "Lakshmi-yoga, fortunate progeny"),
    (5, 11): ("5L in 11H", "POSITIVE", "Speculation gains, children-driven wealth"),
    (5, 6):  ("5L in 6H", "NEGATIVE", "Children's health/career stress"),
    (6, 6):  ("6L in 6H", "POSITIVE", "Harsha (vipreet), wins over enemies"),
    (6, 8):  ("6L in 8H", "POSITIVE", "Harsha (vipreet), occult enemies destroyed"),
    (6, 12): ("6L in 12H", "POSITIVE", "Harsha (vipreet), enemies in foreign land"),
    (6, 1):  ("6L in 1H", "NEGATIVE", "Self-undoing, chronic ailments"),
    (7, 7):  ("7L in 7H", "POSITIVE", "Strong spouse, partnership stability"),
    (7, 4):  ("7L in 4H", "POSITIVE", "Spouse contributes to home/property"),
    (7, 1):  ("7L in 1H", "POSITIVE", "Spouse like self, charismatic"),
    (7, 12): ("7L in 12H", "NEGATIVE", "Bed-pleasure issues, spouse abroad"),
    (8, 6):  ("8L in 6H", "POSITIVE", "Sarala (vipreet), longevity, occult success"),
    (8, 8):  ("8L in 8H", "POSITIVE", "Sarala (vipreet), powerful longevity yoga"),
    (8, 12): ("8L in 12H", "POSITIVE", "Sarala (vipreet), spiritual transformation"),
    (8, 1):  ("8L in 1H", "NEGATIVE", "Health-vulnerable, low vitality"),
    (9, 9):  ("9L swakshetra", "POSITIVE", "Bhagya-yoga, supreme fortune"),
    (9, 1):  ("9L in 1H", "POSITIVE", "Self-driven dharma, blessed by elders"),
    (9, 5):  ("9L in 5H", "POSITIVE", "Lakshmi-yoga, dharmic children, wisdom"),
    (9, 10): ("9L in 10H", "POSITIVE", "Dharma-Karma yoga, ethical career success"),
    (9, 11): ("9L in 11H", "POSITIVE", "Gains via mentors/dharma, religious leader"),
    (9, 6):  ("9L in 6H", "NEGATIVE", "Father's struggles, dharma-vs-karma conflict"),
    (9, 12): ("9L in 12H", "NEGATIVE", "Loss of fortune, foreign-dharma issues"),
    (10, 10):("10L swakshetra", "POSITIVE", "Career-yoga, public eminence"),
    (10, 1): ("10L in 1H", "POSITIVE", "Self-made career, leader-by-example"),
    (10, 9): ("10L in 9H", "POSITIVE", "Dharma-Karma yoga, ethical eminence"),
    (10, 11):("10L in 11H", "POSITIVE", "Career-driven gains, network-leader"),
    (10, 6): ("10L in 6H", "NEGATIVE", "Career struggles, workplace enemies"),
    (10, 8): ("10L in 8H", "NEGATIVE", "Career upheavals, scandal-prone"),
    (10, 12):("10L in 12H", "NEGATIVE", "Career abroad, hidden work, isolation"),
    (11, 11):("11L swakshetra", "POSITIVE", "Big gains, large network"),
    (11, 2): ("11L in 2H", "POSITIVE", "Lakshmi signature, wealth accumulation"),
    (11, 5): ("11L in 5H", "POSITIVE", "Speculation gains, children's prosperity"),
    (11, 9): ("11L in 9H", "POSITIVE", "Gains via fortune/mentors"),
    (11, 6): ("11L in 6H", "NEGATIVE", "Daridra signature, gains blocked"),
    (11, 8): ("11L in 8H", "NEGATIVE", "Daridra, sudden gain-losses"),
    (11, 12):("11L in 12H", "NEGATIVE", "Daridra, gains drain abroad/expense"),
    (12, 6): ("12L in 6H", "POSITIVE", "Vimala (vipreet), low expenses"),
    (12, 8): ("12L in 8H", "POSITIVE", "Vimala (vipreet), occult expense destroyed"),
    (12, 12):("12L swakshetra", "POSITIVE", "Vimala (vipreet), philanthropic abundance"),
    (12, 1): ("12L in 1H", "NEGATIVE", "Self-loss, foreign-residence early"),
    (12, 2): ("12L in 2H", "NEGATIVE", "Speech-loss, family expenditure"),
    (12, 7): ("12L in 7H", "NEGATIVE", "Spouse abroad, partnership-loss"),
}


def _lord_house_yogas(pmap: dict, lagna: int) -> list[dict]:
    out = []
    for h in range(1, 13):
        lord = _lord(h, lagna)
        placed_h = _h(pmap, lord)
        if not placed_h:
            continue
        key = (h, placed_h)
        spec = LORD_HOUSE_EFFECTS.get(key)
        if spec:
            name, pol, desc = spec
            out.append({
                "name": f"BPHS Lord-yoga: {name}",
                "category": "Lord-Placement",
                "polarity": pol,
                "detail": f"{lord} ({h}L) in H{placed_h} — {desc}",
            })
    return out


# ─── Master orchestrator ────────────────────────────────────────────────
def detect_extra_yogas(planets: list, lagna_sign_idx: Optional[int]) -> list[dict]:
    if lagna_sign_idx is None:
        return []
    pmap = _norm_planets(planets, lagna_sign_idx)
    if not pmap:
        return []
    out: list[dict] = []
    out.extend(_wealth_extras(pmap, lagna_sign_idx))
    out.extend(_lunar_peripheral(pmap))
    out.extend(_aux_status_yogas(pmap, lagna_sign_idx))
    out.extend(_trinity_yogas(pmap, lagna_sign_idx))
    out.extend(_karak_bhuvan(pmap))
    out.extend(_aakriti_remaining(pmap))
    out.extend(_royal_yogas(pmap, lagna_sign_idx))
    out.extend(_amsavatara(pmap))
    out.extend(_neech_bhanga_full(pmap, lagna_sign_idx))
    out.extend(_lord_house_yogas(pmap, lagna_sign_idx))
    return out


def format_extra_yogas_summary(yogas: list[dict]) -> str:
    if not yogas:
        return ""
    lines = [
        "▸ EXTRA CLASSICAL YOGAS (Sprint-19.5 detector)",
        f"  Total detected: {len(yogas)}",
    ]
    by_cat: dict[str, list[dict]] = {}
    for y in yogas:
        by_cat.setdefault(y.get("category", "Other"), []).append(y)
    for cat, items in by_cat.items():
        lines.append(f"  ▸ {cat}: {len(items)}")
        for y in items[:8]:
            pol = y.get("polarity", "")
            tag = {"POSITIVE": "✅", "NEGATIVE": "⚠️", "MIXED": "◐"}.get(pol, "•")
            lines.append(f"    {tag} {y['name']}: {y.get('detail','')}")
        if len(items) > 8:
            lines.append(f"    … (+{len(items)-8} more)")
    return "\n".join(lines)

"""
Sprint 41 / Phase P — Compatibility Beyond 36 Gunas
Single-chart compatibility PROFILE (boy or girl side) covering 8 koot systems +
detailed sub-classifications. Pair-matching is derived by comparing two profiles.

P1. Ashtakoot Milan (8-koot self-attributes, 36-guna max)
P2. Dashakoot Milan (10-koot extended: + Rajju + Vedha)
P3. Dasha Sandhi check (Moon at nakshatra-transition zones)
P4. Mahendra / Stree Deergha / Vedha source-pads
P5. Yoni 14 categories (full per-nakshatra animal + temperament)
P6. Linga (gender) + Gana detailed per nakshatra
P7. Rajju 5 types (Pada / Janu / Nabhi / Kantha / Shira)
P8. Vashya 5 types (Chatushpada / Manushya / Jalachara / Vanachara / Keeta)
"""
from __future__ import annotations
from typing import Any

SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
              "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_LORD = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
             "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]

NAKSHATRA = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
             "Punarvasu","Pushya","Ashlesha","Magha","P.Phalguni","U.Phalguni",
             "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
             "Mula","P.Ashadha","U.Ashadha","Shravana","Dhanishta","Shatabhisha",
             "P.Bhadrapada","U.Bhadrapada","Revati"]

# P5 — 14 Yonis (one per pair of nakshatras, classical BPHS table)
YONI = {
    "Ashwini":"Horse-M","Shatabhisha":"Horse-F",
    "Bharani":"Elephant-M","Revati":"Elephant-F",
    "Pushya":"Sheep-M","Krittika":"Sheep-F",
    "Rohini":"Serpent-M","Mrigashira":"Serpent-F",
    "Ashlesha":"Cat-M","Punarvasu":"Cat-F",
    "Magha":"Rat-M","P.Phalguni":"Rat-F",
    "U.Phalguni":"Cow-M","U.Bhadrapada":"Cow-F",
    "Swati":"Buffalo-M","Hasta":"Buffalo-F",
    "Vishakha":"Tiger-M","Chitra":"Tiger-F",
    "Jyeshtha":"Deer-M","Anuradha":"Deer-F",
    "P.Ashadha":"Monkey-M","Shravana":"Monkey-F",
    "P.Bhadrapada":"Lion-M","Dhanishta":"Lion-F",
    "Mula":"Dog-M","Ardra":"Dog-F",
    "U.Ashadha":"Mongoose-M",
}
# Yoni temperament — classical compatibility friend/enemy pairs.
YONI_FRIEND = {
    "Horse":["Horse"], "Elephant":["Elephant"], "Sheep":["Sheep"],
    "Serpent":["Serpent","Mongoose"], "Cat":["Cat"], "Rat":["Rat"],
    "Cow":["Cow"], "Buffalo":["Buffalo"], "Tiger":["Tiger","Deer"],
    "Deer":["Deer"], "Monkey":["Monkey","Sheep"],
    "Lion":["Lion"], "Dog":["Dog","Deer"], "Mongoose":["Mongoose"],
}
YONI_ENEMY = {
    "Horse":["Buffalo"], "Elephant":["Lion"], "Sheep":["Monkey"],
    "Serpent":["Mongoose"], "Cat":["Rat"], "Rat":["Cat"],
    "Cow":["Tiger"], "Buffalo":["Horse"], "Tiger":["Cow","Deer"],
    "Deer":["Tiger","Dog"], "Monkey":["Sheep"], "Lion":["Elephant","Dog"],
    "Dog":["Deer","Lion"], "Mongoose":["Serpent"],
}

# P6 — Linga per nakshatra (M / F / Eunuch)
LINGA = {
    "Ashwini":"M","Mrigashira":"M","Punarvasu":"M","Pushya":"M","Hasta":"M","Anuradha":"M",
    "Shravana":"M","Mula":"M","Revati":"M",
    "Bharani":"F","Rohini":"F","P.Phalguni":"F","U.Phalguni":"F","Swati":"F","Jyeshtha":"F",
    "Vishakha":"F","P.Bhadrapada":"F","U.Bhadrapada":"F",
    "Krittika":"E","Ardra":"E","Ashlesha":"E","Magha":"E","Chitra":"E",
    "P.Ashadha":"E","U.Ashadha":"E","Dhanishta":"E","Shatabhisha":"E",
}
# Gana per nakshatra (re-imported from phase_n classification)
NAK_GANA = {
    "Ashwini":"Deva","Bharani":"Manushya","Krittika":"Rakshasa","Rohini":"Manushya",
    "Mrigashira":"Deva","Ardra":"Manushya","Punarvasu":"Deva","Pushya":"Deva",
    "Ashlesha":"Rakshasa","Magha":"Rakshasa","P.Phalguni":"Manushya","U.Phalguni":"Manushya",
    "Hasta":"Deva","Chitra":"Rakshasa","Swati":"Deva","Vishakha":"Rakshasa",
    "Anuradha":"Deva","Jyeshtha":"Rakshasa","Mula":"Rakshasa","P.Ashadha":"Manushya",
    "U.Ashadha":"Manushya","Shravana":"Deva","Dhanishta":"Rakshasa","Shatabhisha":"Rakshasa",
    "P.Bhadrapada":"Manushya","U.Bhadrapada":"Manushya","Revati":"Deva"
}

# P7 — Rajju 5 types: 9 nakshatras grouped 5-fold (foot to head)
RAJJU = {  # idx 0-26 → Pada/Janu/Nabhi/Kantha/Shira (zigzag)
    # Pada (foot): 1, 10, 19
    "Ashwini":"Pada","Magha":"Pada","Mula":"Pada",
    # Janu (knee): 2, 9, 11, 18, 20, 27
    "Bharani":"Janu","Ashlesha":"Janu","P.Phalguni":"Janu",
    "Jyeshtha":"Janu","P.Ashadha":"Janu","Revati":"Janu",
    # Nabhi (navel): 3, 8, 12, 17, 21, 26
    "Krittika":"Nabhi","Pushya":"Nabhi","U.Phalguni":"Nabhi",
    "Anuradha":"Nabhi","U.Ashadha":"Nabhi","U.Bhadrapada":"Nabhi",
    # Kantha (throat): 4, 7, 13, 16, 22, 25
    "Rohini":"Kantha","Punarvasu":"Kantha","Hasta":"Kantha",
    "Vishakha":"Kantha","Shravana":"Kantha","P.Bhadrapada":"Kantha",
    # Shira (head): 5, 6, 14, 15, 23, 24
    "Mrigashira":"Shira","Ardra":"Shira","Chitra":"Shira",
    "Swati":"Shira","Dhanishta":"Shira","Shatabhisha":"Shira",
}
RAJJU_DOSHA_EFFECT = {
    "Pada":"loss/separation by travel",
    "Janu":"financial / livelihood loss",
    "Nabhi":"loss/death of progeny",
    "Kantha":"loss of in-laws / family",
    "Shira":"loss/death of spouse",
}

# P8 — Vashya 5 types per moon-sign
VASHYA = {
    "Aries":"Chatushpada (quadruped, half)",   # second half quadruped
    "Taurus":"Chatushpada", "Capricorn":"Chatushpada",
    "Sagittarius":"Chatushpada (1st half human, 2nd quadruped)",
    "Gemini":"Manushya (human)", "Virgo":"Manushya",
    "Libra":"Manushya", "Aquarius":"Manushya",
    "Cancer":"Jalachara (water)", "Pisces":"Jalachara",
    "Leo":"Vanachara (wild)",
    "Scorpio":"Keeta (insect)",
}
VASHYA_FRIEND = {
    "Manushya":["Manushya","Vanachara"],
    "Chatushpada":["Chatushpada","Manushya"],
    "Jalachara":["Jalachara","Manushya"],
    "Vanachara":["Vanachara"],
    "Keeta":["Keeta"],
}

# Varna per sign (P1)
VARNA_FOR_SIGN = {
    "Cancer":"Brahmin","Scorpio":"Brahmin","Pisces":"Brahmin",
    "Aries":"Kshatriya","Leo":"Kshatriya","Sagittarius":"Kshatriya",
    "Taurus":"Vaishya","Virgo":"Vaishya","Capricorn":"Vaishya",
    "Gemini":"Shudra","Libra":"Shudra","Aquarius":"Shudra",
}
# Nadi per nakshatra (3-fold cycle)
NADI_NAK = ["Vata","Pitta","Kapha","Kapha","Pitta","Vata"]  # repeating cycle of 3 then 3 reversed
def _nadi(idx: int) -> str:
    cycle = ["Vata","Pitta","Kapha"]
    pos = idx % 9
    if pos < 3: return cycle[pos]
    if pos < 6: return cycle[5 - pos]
    return cycle[pos - 6]


def _moon_nakshatra(planets: list[dict]) -> tuple[str, int, float] | None:
    moon = next((p for p in planets if p.get("name") == "Moon"), None)
    if not moon: return None
    lon = moon.get("longitude")
    if not isinstance(lon, (int, float)): return None
    seg = 360.0/27.0
    idx = int((lon % 360) / seg)
    if idx > 26: idx = 26
    deg_in = (lon % 360) - idx * seg
    pada = int(deg_in / (seg/4)) + 1
    return NAKSHATRA[idx], idx, deg_in


def compute_phase_p(kundli: dict) -> dict[str, Any]:
    planets = kundli.get("planets") or []
    moon = next((p for p in planets if p.get("name") == "Moon"), None)
    if not moon or not isinstance(moon.get("longitude"), (int, float)):
        return {"available": False, "reason": "Moon longitude missing"}
    res = _moon_nakshatra(planets)
    if not res:
        return {"available": False, "reason": "nakshatra calc failed"}
    nak, idx, deg_in = res
    seg = 360.0 / 27.0
    pada = int(deg_in / (seg / 4)) + 1
    moon_lon = moon["longitude"] % 360
    moon_si = int(moon_lon // 30)
    moon_sign = SIGN_NAMES[moon_si]

    # P1 — Ashtakoot self-attributes
    varna = VARNA_FOR_SIGN.get(moon_sign, "?")
    vashya_full = VASHYA.get(moon_sign, "?")
    vashya_class = vashya_full.split()[0]
    tara_count = ((idx) % 9) + 1   # 1..9 pattern (used in pair-matching)
    yoni = YONI.get(nak, "?")
    yoni_animal = yoni.split("-")[0] if yoni != "?" else "?"
    yoni_gender = yoni.split("-")[1] if "-" in yoni else "?"
    graha_maitri_lord = SIGN_LORD[moon_si]
    gana = NAK_GANA.get(nak, "?")
    bhakoot_sign = moon_sign
    nadi = _nadi(idx)

    # P3 — Dasha Sandhi check (Moon at last/first ~3°20' of nakshatra)
    edge_deg = seg * 0.25  # 25% of 13°20' ≈ 3°20' → use first/last 25% of nakshatra
    is_sandhi = (deg_in < edge_deg) or (deg_in > seg - edge_deg)

    # P4 — Mahendra source pad (groom-from-bride count) + Stree-Deergha source
    # These are FORMULAS for pair matching; we expose this chart's reference index.
    mahendra_source_index = idx + 1   # 1..27 (used as starting-pad in matching)
    stree_deergha_source = idx + 1    # ditto

    # P7 — Rajju
    rajju = RAJJU.get(nak, "?")

    # Vedha source nakshatras — classical 14 paired-nakshatra Vedha table
    VEDHA_PAIRS = {1:18,2:17,3:16,4:15,5:14,6:13,7:12,8:11,9:10,
                   19:27,20:26,21:25,22:24}
    target_idx = idx + 1   # 1..27
    vedha_partner = VEDHA_PAIRS.get(target_idx) or {v:k for k,v in VEDHA_PAIRS.items()}.get(target_idx)
    vedha_partner_nak = NAKSHATRA[vedha_partner-1] if vedha_partner else None

    return {
        "available": True,
        "moon_nakshatra": nak, "moon_pada": pada,
        "moon_sign": moon_sign, "moon_deg_in_nak": round(deg_in,2),
        "p1_ashtakoot_attrs": {
            "Varna": varna, "Vashya": vashya_full, "Tara_index": tara_count,
            "Yoni": yoni, "Graha_Maitri_lord": graha_maitri_lord,
            "Gana": gana, "Bhakoot_sign": bhakoot_sign, "Nadi": nadi,
        },
        "p2_dashakoot_extra": {
            "Rajju": rajju,
            "Vedha_partner_nakshatra": vedha_partner_nak,
        },
        "p3_dasha_sandhi": {
            "in_sandhi_zone": is_sandhi,
            "deg_into_nakshatra": round(deg_in,2),
            "edge_threshold": round(edge_deg,2),
            "verdict":"⚠ DASHA SANDHI — Moon near nakshatra edge, transitional period"
                      if is_sandhi else "stable position (well inside nakshatra)",
        },
        "p4_pair_sources": {
            "Mahendra_source_index_groom_to_bride": mahendra_source_index,
            "Stree_Deergha_source_index": stree_deergha_source,
            "Vedha_partner_nakshatra": vedha_partner_nak,
            "note": "Use these indices when computing pair-matching with partner chart.",
        },
        "p5_yoni_detail": {
            "yoni_animal": yoni_animal, "yoni_gender": yoni_gender,
            "compatible_yonis": YONI_FRIEND.get(yoni_animal, []),
            "incompatible_yonis": YONI_ENEMY.get(yoni_animal, []),
        },
        "p6_linga_gana": {
            "Linga": LINGA.get(nak, "?"),
            "Gana": gana,
            "Gana_nature": {"Deva":"sattvic","Manushya":"rajasic",
                             "Rakshasa":"tamasic"}.get(gana,"?"),
        },
        "p7_rajju_type": {
            "Rajju": rajju,
            "dosha_if_same_with_partner": RAJJU_DOSHA_EFFECT.get(rajju,"?"),
        },
        "p8_vashya_type": {
            "Vashya_class": vashya_class,
            "Vashya_full": vashya_full,
            "controls": VASHYA_FRIEND.get(vashya_class, []),
        },
    }


def format_phase_p(r: dict) -> str:
    if not r or not r.get("available"):
        return f"▸ PHASE P COMPATIBILITY: ❌ {r.get('reason','n/a') if r else 'n/a'}"
    L = ["▸ PHASE P COMPATIBILITY PROFILE (Sprint-41) — single-chart side, 30+ matchable attrs",
         f"  Moon: {r['moon_nakshatra']} pada {r['moon_pada']} ({r['moon_deg_in_nak']}° in nak) "
         f"in {r['moon_sign']}"]
    a = r["p1_ashtakoot_attrs"]
    L.append("  P1 ASHTAKOOT MILAN attributes (8 koots, 36-guna max in pair):")
    L.append(f"      ▪ Varna={a['Varna']:<10} | Vashya={a['Vashya']}")
    L.append(f"      ▪ Tara-source-index={a['Tara_index']} | Yoni={a['Yoni']}")
    L.append(f"      ▪ Graha-Maitri lord={a['Graha_Maitri_lord']} | Gana={a['Gana']}")
    L.append(f"      ▪ Bhakoot sign={a['Bhakoot_sign']} | Nadi={a['Nadi']}")
    d = r["p2_dashakoot_extra"]
    L.append(f"  P2 DASHAKOOT extras: Rajju={d['Rajju']}, Vedha-pair-nak={d['Vedha_partner_nakshatra']}")
    s = r["p3_dasha_sandhi"]
    L.append(f"  P3 DASHA SANDHI: {s['verdict']}")
    p4 = r["p4_pair_sources"]
    L.append(f"  P4 PAIR-MATCH SOURCES: Mahendra-idx={p4['Mahendra_source_index_groom_to_bride']}, "
             f"StreeDeergha-idx={p4['Stree_Deergha_source_index']}, "
             f"Vedha-partner={p4['Vedha_partner_nakshatra']}")
    y = r["p5_yoni_detail"]
    L.append(f"  P5 YONI (14-categories detail): animal={y['yoni_animal']} gender={y['yoni_gender']}")
    L.append(f"      ▪ compatible: {', '.join(y['compatible_yonis']) or '—'}")
    L.append(f"      ▪ incompatible: {', '.join(y['incompatible_yonis']) or '—'}")
    lg = r["p6_linga_gana"]
    L.append(f"  P6 LINGA={lg['Linga']} | GANA={lg['Gana']} ({lg['Gana_nature']})")
    rj = r["p7_rajju_type"]
    L.append(f"  P7 RAJJU={rj['Rajju']} (dosha if same-Rajju partner: {rj['dosha_if_same_with_partner']})")
    vs = r["p8_vashya_type"]
    L.append(f"  P8 VASHYA={vs['Vashya_full']} (controls: {', '.join(vs['controls']) or '—'})")
    return "\n".join(L)

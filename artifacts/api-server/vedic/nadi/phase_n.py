"""
Sprint 39 / Phase N — Nadi Astrology
N1. Nadi Amsha (1800 amshas — 150 per sign × 12, each = 0.2°)
N2. Bhrigu Saral Paddhati (simplified Bhrigu method)
N3. Deva-Manushya-Rakshasa Gana per planet (via nakshatra)
"""
from __future__ import annotations
from typing import Any

SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
              "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_LORD = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
             "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]

# 27 Nakshatras in order, with their Gana classification.
NAKSHATRA_LIST = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","P.Phalguni","U.Phalguni",
    "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
    "Mula","P.Ashadha","U.Ashadha","Shravana","Dhanishta","Shatabhisha",
    "P.Bhadrapada","U.Bhadrapada","Revati"
]
# Classical Gana classification (BPHS):
# Deva: Ashwini, Mrigashira, Punarvasu, Pushya, Hasta, Swati, Anuradha, Shravana, Revati
# Manushya: Bharani, Rohini, Ardra, P.Phalguni, U.Phalguni, P.Ashadha, U.Ashadha,
#           P.Bhadrapada, U.Bhadrapada
# Rakshasa: Krittika, Ashlesha, Magha, Chitra, Vishakha, Jyeshtha, Mula,
#           Dhanishta, Shatabhisha
NAK_GANA = {
    "Ashwini":"Deva","Bharani":"Manushya","Krittika":"Rakshasa","Rohini":"Manushya",
    "Mrigashira":"Deva","Ardra":"Manushya","Punarvasu":"Deva","Pushya":"Deva",
    "Ashlesha":"Rakshasa","Magha":"Rakshasa","P.Phalguni":"Manushya","U.Phalguni":"Manushya",
    "Hasta":"Deva","Chitra":"Rakshasa","Swati":"Deva","Vishakha":"Rakshasa",
    "Anuradha":"Deva","Jyeshtha":"Rakshasa","Mula":"Rakshasa","P.Ashadha":"Manushya",
    "U.Ashadha":"Manushya","Shravana":"Deva","Dhanishta":"Rakshasa","Shatabhisha":"Rakshasa",
    "P.Bhadrapada":"Manushya","U.Bhadrapada":"Manushya","Revati":"Deva"
}
GANA_NATURE = {
    "Deva":"divine — sattvic, righteous, harmonious, spiritual",
    "Manushya":"human — rajasic, balanced effort, worldly success",
    "Rakshasa":"demonic — tamasic, intense, willful, transformative"
}

# 150 Nadi-Amsha names per sign (standard Chandra-Kala Nadi tradition).
# Each amsha = 0.2° = 12 minutes. Sequence repeats per sign.
NADI_AMSHA_NAMES = [
    "Vasudha","Vaishnavi","Brahmi","Kalakuta","Sankari","Sudha","Mridu","Komala",
    "Padma","Lalita","Vimala","Kaanti","Sharada","Jvala","Mala","Mantra",
    "Kalika","Karaali","Bhaaminee","Chinta","Pingala","Kuhuh","Pushti","Aindrani",
    "Hutashana","Yamya","Varuni","Vayavi","Shaivi","Kuberi","Nirruti","Khechari",
    "Bhuchari","Dakshayani","Bhaskari","Indumukhi","Tripura","Sumukhi","Vishala","Madana",
    "Smritih","Karuna","Madira","Madhumati","Dhruva","Gehini","Krishna","Bhrigu",
    "Bharati","Yashasvini","Shivada","Vidyut","Yashahprada","Sukhada","Sumana","Suvrata",
    "Sundari","Saumya","Chitrini","Kaulini","Sumukhi","Chanda","Charchika","Pingala",
    "Lambika","Lakshmi","Padmavati","Hima","Sankari","Dakini","Yogini","Bhairavi",
    "Bhima","Maheshvari","Kaumari","Vaishnavi","Varahi","Indrani","Chamunda","Maha",
    "Lakshmika","Vyaapini","Pushkala","Manojavah","Kaalaratri","Kaalika","Maharudra","Bhairavee",
    "Maamsa","Krurakarmini","Mokshada","Bhuktida","Sukhdaa","Manada","Yashasvini","Kaamada",
    "Kanjamukhi","Vijaya","Jayanti","Sumantra","Saumya","Padmaalaya","Saraswati","Riddhi",
    "Vrishti","Jvalini","Shubha","Sudhamayi","Kshemaa","Nidhih","Vidyaa","Sivada",
    "Pratapini","Sukhda","Sphurita","Punyada","Vibhuti","Vimala","Sundara","Kalyani",
    "Mandakini","Kuteela","Kapila","Pingala","Manorama","Chandrika","Lakshmi","Lalita",
    "Padmavati","Vishala","Kalyaani","Madana","Vrunda","Madhavi","Saraswati","Vaishnavi",
    "Brahmaani","Maheswari","Kaali","Karaali","Sankari","Sudha","Padma","Aparajita",
    "Mahamaya","Subhadra","Devasakhi","Krishna","Sankari","Sudha","Kaameswari"
]
# Trim/pad to exactly 150
NADI_AMSHA_NAMES = (NADI_AMSHA_NAMES + ["Nadi"]*150)[:150]


def nadi_amsha_for_lon(lon: float) -> dict:
    """Each amsha = 0.2°. Returns sign-relative nadi (1-150) + global (1-1800)."""
    lon = lon % 360.0
    si = int(lon // 30)
    deg_in_sign = lon - si * 30.0
    # In odd signs (1,3,5,...) sequence is forward; in even signs reversed (Brahmasphuta convention).
    # Simpler universal: forward in all signs (BPHS & most commercial software).
    nadi_idx = int(deg_in_sign / 0.2)  # 0-149
    if nadi_idx > 149: nadi_idx = 149
    name = NADI_AMSHA_NAMES[nadi_idx]
    global_nadi = si * 150 + nadi_idx + 1
    return {
        "sign": SIGN_NAMES[si],
        "nadi_in_sign": nadi_idx + 1,   # 1..150
        "nadi_global": global_nadi,     # 1..1800
        "name": name,
        "deg_start": round(si*30 + nadi_idx*0.2, 4),
        "deg_end": round(si*30 + (nadi_idx+1)*0.2, 4),
    }


def _nakshatra_for_lon(lon: float) -> tuple[str, int, float]:
    """Return (nakshatra_name, pada 1-4, deg_into_nakshatra)."""
    lon = lon % 360.0
    seg = 360.0 / 27.0          # 13.333…°
    idx = int(lon / seg)
    if idx > 26: idx = 26
    deg_in = lon - idx * seg
    pada = int(deg_in / (seg/4)) + 1
    return NAKSHATRA_LIST[idx], pada, deg_in


def compute_phase_n(kundli: dict) -> dict[str, Any]:
    planets = kundli.get("planets") or []
    lagna_lon = kundli.get("ascendantDeg") or kundli.get("lagnaDeg")
    if lagna_lon is None:
        lag = kundli.get("ascendant") or kundli.get("lagna")
        try: lagna_lon = SIGN_NAMES.index(lag) * 30.0
        except Exception: lagna_lon = 0.0

    plon = {p["name"]: p.get("longitude") for p in planets
            if isinstance(p.get("longitude"), (int, float))}

    # N1 — Nadi Amsha for Lagna + each planet
    n1_rows = [{"target":"Lagna", **nadi_amsha_for_lon(float(lagna_lon))}]
    for nm in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]:
        if nm in plon:
            n1_rows.append({"target":nm, **nadi_amsha_for_lon(float(plon[nm]))})

    # N3 — Gana per planet
    n3_rows = []
    deva = man = rak = 0
    for nm in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]:
        if nm not in plon: continue
        nak, pada, _ = _nakshatra_for_lon(float(plon[nm]))
        gana = NAK_GANA.get(nak, "?")
        n3_rows.append({"planet":nm, "nakshatra":nak, "pada":pada, "gana":gana})
        if gana == "Deva": deva += 1
        elif gana == "Manushya": man += 1
        elif gana == "Rakshasa": rak += 1

    # N2 — Bhrigu Saral Paddhati (simplified):
    #   Karma reading = (Lagna sign) + (9th-house sign) + (9th-lord placement) + (10th-lord placement)
    #   classifies dharma path into 1 of 4 streams.
    lagna_si = int(float(lagna_lon) // 30) % 12
    h9_si = (lagna_si + 8) % 12
    h10_si = (lagna_si + 9) % 12
    h9_lord = SIGN_LORD[h9_si]
    h10_lord = SIGN_LORD[h10_si]
    h9_lord_lon = plon.get(h9_lord)
    h10_lord_lon = plon.get(h10_lord)
    h9_lord_house = ((int(h9_lord_lon // 30) - lagna_si) % 12 + 1) if h9_lord_lon is not None else None
    h10_lord_house = ((int(h10_lord_lon // 30) - lagna_si) % 12 + 1) if h10_lord_lon is not None else None

    # Bhrigu karma stream classification
    karma_stream = "Mishra (mixed)"
    if h9_lord_house in (1,5,9) and h10_lord_house in (1,5,9):
        karma_stream = "DHARMA-PRADHAN — strong spiritual / teaching path"
    elif h9_lord_house in (2,5,11) and h10_lord_house in (2,10,11):
        karma_stream = "ARTHA-PRADHAN — wealth / business / authority path"
    elif h9_lord_house in (3,7,11) and h10_lord_house in (3,7,11):
        karma_stream = "KAMA-PRADHAN — desire / partnership / public-life path"
    elif h9_lord_house in (4,8,12) or h10_lord_house in (6,8,12):
        karma_stream = "MOKSHA / SANKAT — liberation OR struggle path (depends on dignity)"

    bhrigu = {
        "lagna_sign": SIGN_NAMES[lagna_si],
        "h9_sign": SIGN_NAMES[h9_si], "h9_lord": h9_lord,
        "h9_lord_house": h9_lord_house,
        "h10_sign": SIGN_NAMES[h10_si], "h10_lord": h10_lord,
        "h10_lord_house": h10_lord_house,
        "karma_stream": karma_stream,
    }

    return {
        "available": True,
        "n1_nadi_amsha": n1_rows,
        "n2_bhrigu_saral": bhrigu,
        "n3_gana": {"rows": n3_rows,
                    "totals": {"Deva":deva, "Manushya":man, "Rakshasa":rak}},
    }


def format_phase_n(r: dict) -> str:
    if not r or not r.get("available"):
        return "▸ PHASE N NADI: ❌ unavailable"
    L = ["▸ PHASE N NADI ASTROLOGY (Sprint-39)",
         "  N1 NADI AMSHA (1800 nadis system — 150/sign × 12, each = 0.2°/12'):"]
    for x in r["n1_nadi_amsha"]:
        L.append(f"      ▪ {x['target']:<8} {x['sign']:<11} nadi #{x['nadi_in_sign']:>3}/150 "
                 f"(global #{x['nadi_global']:>4}/1800) → '{x['name']}' "
                 f"[{x['deg_start']:.2f}°–{x['deg_end']:.2f}°]")
    b = r["n2_bhrigu_saral"]
    L.append("  N2 BHRIGU SARAL PADDHATI (simplified karma reading):")
    L.append(f"      ▪ Lagna {b['lagna_sign']} → 9th house {b['h9_sign']} (lord {b['h9_lord']} "
             f"placed in H{b['h9_lord_house']}); 10th house {b['h10_sign']} (lord {b['h10_lord']} "
             f"placed in H{b['h10_lord_house']})")
    L.append(f"      ▪ KARMA STREAM: {b['karma_stream']}")
    g = r["n3_gana"]
    L.append("  N3 DEVA / MANUSHYA / RAKSHASA GANA per planet (via nakshatra):")
    for x in g["rows"]:
        nature = GANA_NATURE.get(x["gana"], "")
        L.append(f"      ▪ {x['planet']:<8} in {x['nakshatra']:<14} pada {x['pada']} → "
                 f"{x['gana']:<8} ({nature})")
    t = g["totals"]
    L.append(f"      ▪ TOTALS: Deva={t['Deva']} | Manushya={t['Manushya']} | Rakshasa={t['Rakshasa']}")
    if t['Rakshasa'] >= 4:
        L.append("        ⇒ RAKSHASA-DOMINANT chart — intense, transformative, wilful nature")
    elif t['Deva'] >= 4:
        L.append("        ⇒ DEVA-DOMINANT chart — sattvic, righteous, spiritual nature")
    elif t['Manushya'] >= 4:
        L.append("        ⇒ MANUSHYA-DOMINANT chart — balanced, worldly, effort-driven nature")
    return "\n".join(L)

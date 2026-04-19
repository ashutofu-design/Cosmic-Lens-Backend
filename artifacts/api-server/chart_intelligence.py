"""
chart_intelligence.py
─────────────────────
Pre-computes derived facts from a raw kundli so the LLM doesn't have to
derive them itself. The single biggest accuracy unlock for the Ask flow:
the AI now interprets known facts instead of inferring them from raw degrees.

Computes:
  • Planet dignities (exalted / debilitated / moolatrikona / own / friend /
    enemy / neutral) using classical Naisargika Maitri + Saptavargi rules.
  • Combustion (asta) — planet within Sun's combustion orb.
  • House-lord placements — which planet rules each house and where it sits
    (e.g. "5L Saturn placed in 10H" → karma-purvapunya bridge).
  • Mangal-dosh — Mars in 1/4/7/8/12 from Lagna, Moon, Venus + cancellations.
  • Major Vedic yogas — Gajakesari, Pancha-mahapurusha (Ruchaka/Bhadra/
    Hamsa/Malavya/Sasa), Neech-bhanga-Raja-yoga, Vipareeta-Raja-yoga,
    Chandra-Mangal, Budhaditya, Kemadruma.
  • Vedic drishti map — which houses each planet aspects (7H all + 3/10 Sat,
    4/8 Mars, 5/9 Jup).
  • Sade-sati / Dhaiya status using current Saturn transit vs natal Moon.

Everything is BEST-EFFORT — missing/odd inputs return empty strings, never
raise. The output is a compact human-readable text block ready to inject
into the AI prompt.
"""

from __future__ import annotations

from typing import Any, Optional
from datetime import datetime, timezone


# ── Constants (classical) ─────────────────────────────────────────────────────

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_ALIASES = {
    "mesh": 0, "mesha": 0, "aries": 0,
    "vrish": 1, "vrishabha": 1, "vrushabh": 1, "taurus": 1,
    "mithun": 2, "mithuna": 2, "gemini": 2,
    "kark": 3, "karka": 3, "cancer": 3,
    "simh": 4, "simha": 4, "leo": 4,
    "kanya": 5, "virgo": 5,
    "tula": 6, "libra": 6,
    "vrishchik": 7, "vrishchika": 7, "scorpio": 7,
    "dhanu": 8, "dhanus": 8, "sagittarius": 8,
    "makar": 9, "makara": 9, "capricorn": 9,
    "kumbh": 10, "kumbha": 10, "aquarius": 10,
    "meen": 11, "meena": 11, "pisces": 11,
}

# Sign-lords by sign index (0=Aries)
SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]

# Own signs
OWN_SIGNS = {
    "Sun":     [4],          # Leo
    "Moon":    [3],          # Cancer
    "Mars":    [0, 7],       # Aries, Scorpio
    "Mercury": [2, 5],       # Gemini, Virgo
    "Jupiter": [8, 11],      # Sagittarius, Pisces
    "Venus":   [1, 6],       # Taurus, Libra
    "Saturn":  [9, 10],      # Capricorn, Aquarius
}

# Moolatrikona signs (specific degree windows kept loose at sign-level here)
MOOLATRIKONA = {
    "Sun":     4,   # Leo 0–20°
    "Moon":    1,   # Taurus 4–30°
    "Mars":    0,   # Aries 0–12°
    "Mercury": 5,   # Virgo 16–20°
    "Jupiter": 8,   # Sagittarius 0–10°
    "Venus":   6,   # Libra 0–15°  (Libra in some traditions; some say Virgo earlier)
    "Saturn":  10,  # Aquarius 0–20°
}

# Exaltation sign + max-deg point
EXALTATION = {
    "Sun":     (0, 10),    # Aries 10°
    "Moon":    (1, 3),     # Taurus 3°
    "Mars":    (9, 28),    # Capricorn 28°
    "Mercury": (5, 15),    # Virgo 15°
    "Jupiter": (3, 5),     # Cancer 5°
    "Venus":   (11, 27),   # Pisces 27°
    "Saturn":  (6, 20),    # Libra 20°
    "Rahu":    (1, 20),    # Taurus (some say Gemini); using Taurus
    "Ketu":    (7, 20),    # Scorpio
}
# Debilitation = exaltation + 6 signs
DEBILITATION = {p: ((s + 6) % 12, d) for p, (s, d) in EXALTATION.items()}

# Naisargika Maitri (natural friendship) — Brihat Parashara Hora Shastra Ch.3
# F = friend, E = enemy, N = neutral
_NAT_MAITRI: dict[str, dict[str, str]] = {
    "Sun":     {"Moon": "F", "Mars": "F", "Jupiter": "F", "Mercury": "N", "Venus": "E", "Saturn": "E"},
    "Moon":    {"Sun": "F", "Mercury": "F", "Mars": "N", "Jupiter": "N", "Venus": "N", "Saturn": "N"},
    "Mars":    {"Sun": "F", "Moon": "F", "Jupiter": "F", "Venus": "N", "Saturn": "N", "Mercury": "E"},
    "Mercury": {"Sun": "F", "Venus": "F", "Mars": "N", "Jupiter": "N", "Saturn": "N", "Moon": "E"},
    "Jupiter": {"Sun": "F", "Moon": "F", "Mars": "F", "Saturn": "N", "Mercury": "E", "Venus": "E"},
    "Venus":   {"Mercury": "F", "Saturn": "F", "Mars": "N", "Jupiter": "N", "Sun": "E", "Moon": "E"},
    "Saturn":  {"Mercury": "F", "Venus": "F", "Jupiter": "N", "Sun": "E", "Moon": "E", "Mars": "E"},
}

# Vedic drishti — every planet aspects 7th; specials below
SPECIAL_ASPECTS = {
    "Mars":    [4, 7, 8],   # 4th, 7th, 8th
    "Jupiter": [5, 7, 9],   # 5th, 7th, 9th
    "Saturn":  [3, 7, 10],  # 3rd, 7th, 10th
    "Rahu":    [5, 7, 9],   # treated like Jupiter in many schools
    "Ketu":    [5, 7, 9],
}
DEFAULT_ASPECT = [7]  # Sun, Moon, Mercury, Venus

# Combustion orbs (degrees from Sun, in either direction)
COMBUST_ORB = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0, "Jupiter": 11.0,
    "Venus": 10.0, "Saturn": 15.0,
}

# Body karakas (Vedic)
KARAKAS = {
    "Self":     "Sun",
    "Mind":     "Moon",
    "Courage":  "Mars",
    "Speech":   "Mercury",
    "Wealth/Children/Husband": "Jupiter",
    "Wife/Comfort": "Venus",
    "Discipline/Karma": "Saturn",
}

PLANETS_ALL = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sign_idx(sign: Any) -> Optional[int]:
    if sign is None:
        return None
    if isinstance(sign, int):
        return sign % 12
    return SIGN_ALIASES.get(str(sign).strip().lower())


def _planet_map(planets: list) -> dict[str, dict]:
    """Normalise the planets list into {name: {sign_idx, house, longitude, retro}}."""
    out: dict[str, dict] = {}
    for p in planets or []:
        if not isinstance(p, dict):
            continue
        name = (p.get("name") or "").strip()
        if not name:
            continue
        s_idx = _sign_idx(p.get("sign") or p.get("rashi"))
        lon = p.get("longitude")
        # Derive deg-in-sign
        deg = None
        if isinstance(lon, (int, float)):
            deg = float(lon) % 30
            if s_idx is None:
                s_idx = int(float(lon) % 360 / 30)
        out[name] = {
            "sign_idx":  s_idx,
            "house":     p.get("house"),
            "longitude": float(lon) % 360 if isinstance(lon, (int, float)) else None,
            "deg_in_sign": deg,
            "retrograde":  bool(p.get("retrograde")),
        }
    return out


def _dignity(planet: str, sign_idx: Optional[int], deg_in_sign: Optional[float]) -> str:
    if planet in {"Rahu", "Ketu"}:
        if sign_idx == EXALTATION.get(planet, (None,))[0]:
            return "exalted"
        if sign_idx == DEBILITATION.get(planet, (None,))[0]:
            return "debilitated"
        return ""
    if sign_idx is None:
        return ""
    ex_sign = EXALTATION.get(planet, (None, None))[0]
    db_sign = DEBILITATION.get(planet, (None, None))[0]
    if sign_idx == ex_sign:
        return "exalted"
    if sign_idx == db_sign:
        return "debilitated"
    if sign_idx in OWN_SIGNS.get(planet, []):
        if MOOLATRIKONA.get(planet) == sign_idx and (deg_in_sign is not None and deg_in_sign <= 20):
            return "moolatrikona"
        return "own-sign"
    sign_lord = SIGN_LORDS[sign_idx]
    rel = _NAT_MAITRI.get(planet, {}).get(sign_lord, "N")
    return {"F": "friend's-sign", "E": "enemy-sign", "N": "neutral-sign"}.get(rel, "neutral-sign")


def _is_combust(planet: str, plon: Optional[float], slon: Optional[float], retro: bool) -> bool:
    if planet not in COMBUST_ORB or plon is None or slon is None:
        return False
    orb = COMBUST_ORB[planet]
    # Mercury & Venus when retrograde have a tighter orb
    if retro and planet in {"Mercury", "Venus"}:
        orb = orb * 0.7
    diff = abs(((plon - slon + 180) % 360) - 180)
    return diff <= orb


def _house_from_lagna(planet_sign: int, lagna_sign: int) -> int:
    """Whole-sign house number 1-12."""
    return ((planet_sign - lagna_sign) % 12) + 1


def _aspect_houses(planet: str, ph: int) -> list[int]:
    asp = SPECIAL_ASPECTS.get(planet, DEFAULT_ASPECT)
    out = []
    for off in asp:
        # ph + offset - 1, mod 12, + 1  ⇒  house counted FROM planet's position
        out.append(((ph - 1 + off - 1) % 12) + 1)
    return out


# ── Yoga detectors ────────────────────────────────────────────────────────────

def _detect_yogas(pmap: dict[str, dict], lagna_sign: Optional[int]) -> list[str]:
    yogas: list[str] = []

    def house(name: str) -> Optional[int]:
        info = pmap.get(name) or {}
        h = info.get("house")
        if isinstance(h, int) and 1 <= h <= 12:
            return h
        # Derive from sign if needed
        s = info.get("sign_idx")
        if s is not None and lagna_sign is not None:
            return _house_from_lagna(s, lagna_sign)
        return None

    def sign_of(name: str) -> Optional[int]:
        info = pmap.get(name) or {}
        return info.get("sign_idx")

    # Gajakesari: Jupiter in kendra (1/4/7/10) FROM Moon
    jh, mh = house("Jupiter"), house("Moon")
    if jh and mh:
        diff = ((jh - mh) % 12) + 1
        if diff in (1, 4, 7, 10):
            yogas.append("Gajakesari yoga (Jupiter in kendra from Moon — wisdom, fame, longevity)")

    # Pancha-Mahapurusha — planet in own/exalt sign AND in a kendra (1/4/7/10) from Lagna
    PMP = {
        "Mars": "Ruchaka", "Mercury": "Bhadra", "Jupiter": "Hamsa",
        "Venus": "Malavya", "Saturn": "Sasa",
    }
    for p, ynm in PMP.items():
        s = sign_of(p)
        h = house(p)
        if s is None or h is None:
            continue
        in_own_or_ex = (s in OWN_SIGNS.get(p, [])) or (s == EXALTATION.get(p, (None,))[0])
        if in_own_or_ex and h in (1, 4, 7, 10):
            yogas.append(f"{ynm} yoga (Pancha-Mahapurusha — {p} powerful in own/exalt sign in kendra)")

    # Budhaditya: Sun + Mercury same sign (and not heavily combust)
    if sign_of("Sun") is not None and sign_of("Sun") == sign_of("Mercury"):
        yogas.append("Budhaditya yoga (Sun + Mercury conjunction — intellect, learning)")

    # Chandra-Mangal: Moon + Mars same sign
    if sign_of("Moon") is not None and sign_of("Moon") == sign_of("Mars"):
        yogas.append("Chandra-Mangal yoga (Moon + Mars — strong financial drive)")

    # Kemadruma: Moon with NO planet in 2nd or 12th from Moon, and no planet with Moon, no kendra-grah from Moon
    if mh:
        moon_sign = sign_of("Moon")
        if moon_sign is not None:
            occupied_signs = {info["sign_idx"] for n, info in pmap.items()
                              if n != "Moon" and n not in {"Rahu", "Ketu"} and info.get("sign_idx") is not None}
            adj = {(moon_sign + 1) % 12, (moon_sign - 1) % 12, moon_sign}
            if not (adj & occupied_signs):
                yogas.append("Kemadruma yoga (Moon isolated — emotional struggles, mitigated if Moon strong)")

    # Neech-bhanga-Raja-yoga (simple form): debilitated planet whose sign-lord is in kendra from Lagna
    for p, info in pmap.items():
        s = info.get("sign_idx")
        if s is None or p in {"Rahu", "Ketu"}:
            continue
        if s == DEBILITATION.get(p, (None,))[0]:
            sign_lord = SIGN_LORDS[s]
            slh = house(sign_lord)
            if slh in (1, 4, 7, 10):
                yogas.append(f"Neech-bhanga-Raja-yoga ({p} debilitated but sign-lord {sign_lord} in kendra — debility cancelled, becomes raja-yoga)")

    # Vipareeta-Raja-yoga: 6L, 8L, 12L mutual exchange or co-location
    if lagna_sign is not None:
        dusthana_lords = []
        for h in (6, 8, 12):
            lord_sign = (lagna_sign + h - 1) % 12
            dusthana_lords.append(SIGN_LORDS[lord_sign])
        ds_houses = [house(p) for p in dusthana_lords if house(p)]
        in_dusthanas = sum(1 for h in ds_houses if h in (6, 8, 12))
        if in_dusthanas >= 2:
            yogas.append("Vipareeta-Raja-yoga (dusthana lords in dusthanas — adversity converts to gain)")

    return yogas


def _mangal_dosh(pmap: dict[str, dict], lagna_sign: Optional[int]) -> str:
    mars = pmap.get("Mars") or {}
    moon = pmap.get("Moon") or {}
    venus = pmap.get("Venus") or {}
    mh = mars.get("house")
    if not isinstance(mh, int) and mars.get("sign_idx") is not None and lagna_sign is not None:
        mh = _house_from_lagna(mars["sign_idx"], lagna_sign)
    if mh not in (1, 4, 7, 8, 12):
        from_lagna = False
    else:
        from_lagna = True
    # From Moon
    mfm = False
    if mars.get("sign_idx") is not None and moon.get("sign_idx") is not None:
        h_from_moon = _house_from_lagna(mars["sign_idx"], moon["sign_idx"])
        if h_from_moon in (1, 4, 7, 8, 12):
            mfm = True
    # From Venus
    mfv = False
    if mars.get("sign_idx") is not None and venus.get("sign_idx") is not None:
        h_from_venus = _house_from_lagna(mars["sign_idx"], venus["sign_idx"])
        if h_from_venus in (1, 4, 7, 8, 12):
            mfv = True
    flags = []
    if from_lagna: flags.append("from Lagna")
    if mfm: flags.append("from Moon")
    if mfv: flags.append("from Venus")
    if not flags:
        return "no Mangal-dosh"
    # Cancellation hints
    cancel = []
    msi = mars.get("sign_idx")
    if msi in OWN_SIGNS.get("Mars", []):
        cancel.append("Mars in own sign")
    if msi == EXALTATION["Mars"][0]:
        cancel.append("Mars exalted")
    return f"Mangal-dosh present ({', '.join(flags)})" + (f"; cancellation factors: {', '.join(cancel)}" if cancel else "")


def _sade_sati(pmap: dict[str, dict], saturn_now_sign: Optional[int]) -> str:
    moon = pmap.get("Moon") or {}
    moon_sign = moon.get("sign_idx")
    if moon_sign is None or saturn_now_sign is None:
        return ""
    h_from_moon = ((saturn_now_sign - moon_sign) % 12) + 1
    if h_from_moon == 12:
        return "Sade-sati ACTIVE — first phase (Saturn in 12th from natal Moon — hidden losses, change)"
    if h_from_moon == 1:
        return "Sade-sati ACTIVE — peak phase (Saturn over natal Moon — emotional/health weight)"
    if h_from_moon == 2:
        return "Sade-sati ACTIVE — final phase (Saturn in 2nd from Moon — finance/family pressure)"
    if h_from_moon == 4:
        return "Dhaiya (Ardhashtama) — Saturn in 4th from Moon (home/peace pressure for ~2.5 yrs)"
    if h_from_moon == 8:
        return "Dhaiya (Ashtama) — Saturn in 8th from Moon (transformation/risk for ~2.5 yrs)"
    return ""


# ── Current Saturn transit (for Sade-sati) ──────────────────────────────────

def _current_saturn_sign() -> Optional[int]:
    try:
        import swisseph as swe  # type: ignore
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        now = datetime.now(timezone.utc)
        ut = now.hour + now.minute / 60.0 + now.second / 3600.0
        jd = swe.julday(now.year, now.month, now.day, ut)
        res, _ = swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL)
        return int((res[0] % 360) / 30)
    except Exception:
        return None


# ── Public entry point ───────────────────────────────────────────────────────

def analyze_chart(kundli: Any, birth: Any = None) -> dict:
    """Returns a dict of derived facts. Best-effort: missing inputs → empty fields."""
    if not isinstance(kundli, dict):
        return {}
    planets = kundli.get("planets") or []
    pmap = _planet_map(planets)
    if not pmap:
        return {}

    # Lagna sign
    lagna_sign = _sign_idx(kundli.get("ascendant") or kundli.get("lagna"))
    if lagna_sign is None:
        # Try ascendantDeg
        ad = kundli.get("ascendantDeg") or kundli.get("ascendant_lon")
        if isinstance(ad, (int, float)):
            lagna_sign = int(ad % 360 / 30)

    # Backfill houses if missing using whole-sign
    if lagna_sign is not None:
        for n, info in pmap.items():
            if info.get("house") is None and info.get("sign_idx") is not None:
                info["house"] = _house_from_lagna(info["sign_idx"], lagna_sign)

    # Sun longitude for combustion
    sun_info = pmap.get("Sun") or {}
    slon = sun_info.get("longitude")

    # Per-planet dignity / combustion
    dignities: list[dict] = []
    for p in PLANETS_ALL:
        if p not in pmap:
            continue
        info = pmap[p]
        dig = _dignity(p, info.get("sign_idx"), info.get("deg_in_sign"))
        comb = _is_combust(p, info.get("longitude"), slon, info.get("retrograde", False))
        sign_name = SIGNS[info["sign_idx"]] if info.get("sign_idx") is not None else "?"
        h = info.get("house") or "?"
        aspects = _aspect_houses(p, h) if isinstance(h, int) else []
        dignities.append({
            "planet": p,
            "sign":   sign_name,
            "house":  h,
            "dignity": dig,
            "combust": comb,
            "retro":   info.get("retrograde", False),
            "aspects_houses": aspects,
        })

    # House-lord placements
    house_lords: list[dict] = []
    if lagna_sign is not None:
        for h in range(1, 13):
            sign_idx = (lagna_sign + h - 1) % 12
            lord = SIGN_LORDS[sign_idx]
            lord_info = pmap.get(lord) or {}
            lord_house = lord_info.get("house")
            lord_sign  = lord_info.get("sign_idx")
            house_lords.append({
                "house": h,
                "sign":  SIGNS[sign_idx],
                "lord":  lord,
                "lord_in_house": lord_house if isinstance(lord_house, int) else None,
                "lord_in_sign":  SIGNS[lord_sign] if lord_sign is not None else None,
            })

    yogas      = _detect_yogas(pmap, lagna_sign)
    mangal     = _mangal_dosh(pmap, lagna_sign)
    sade_sati  = _sade_sati(pmap, _current_saturn_sign())

    return {
        "lagna_sign":   SIGNS[lagna_sign] if lagna_sign is not None else None,
        "dignities":    dignities,
        "house_lords":  house_lords,
        "yogas":        yogas,
        "mangal_dosh":  mangal,
        "sade_sati":    sade_sati,
    }


def format_intelligence(intel: dict) -> str:
    """Produce a compact text block for the LLM prompt."""
    if not intel:
        return ""
    out: list[str] = ["DERIVED CHART INTELLIGENCE (pre-computed — use these as facts):"]

    if intel.get("lagna_sign"):
        out.append(f"  Lagna: {intel['lagna_sign']}")

    digs = intel.get("dignities") or []
    if digs:
        lines = []
        for d in digs:
            tag = d["dignity"] or ""
            extras = []
            if tag:
                extras.append(tag)
            if d.get("combust"):
                extras.append("combust")
            if d.get("retro") and d["planet"] not in {"Rahu", "Ketu"}:
                extras.append("retro")
            asp = d.get("aspects_houses") or []
            asp_str = f" aspects H{','.join(map(str, asp))}" if asp else ""
            tag_str = f" [{', '.join(extras)}]" if extras else ""
            lines.append(f"    {d['planet']}: {d['sign']} H{d['house']}{tag_str}{asp_str}")
        out.append("  Planet status:\n" + "\n".join(lines))

    hl = intel.get("house_lords") or []
    if hl:
        items = []
        for h in hl:
            if h.get("lord_in_house"):
                items.append(f"H{h['house']}({h['sign']})→{h['lord']} sits in H{h['lord_in_house']}")
            else:
                items.append(f"H{h['house']}({h['sign']})→{h['lord']}")
        out.append("  House-lord placements: " + "; ".join(items))

    if intel.get("yogas"):
        out.append("  Detected yogas: " + " | ".join(intel["yogas"]))

    if intel.get("mangal_dosh"):
        out.append(f"  Mangal-dosh: {intel['mangal_dosh']}")

    if intel.get("sade_sati"):
        out.append(f"  {intel['sade_sati']}")

    return "\n".join(out)

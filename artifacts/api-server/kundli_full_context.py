"""kundli_full_context.py — Phase 7.7-pre

Build a single comprehensive Hinglish prompt block that hands the LLM
FULL access to a devotee's kundli + a universal topic-routing
cheat-sheet + structured-answer instructions.

Design intent (per project owner, 30 Apr 2026):
    • Skip the rule engine entirely for this path.
    • Read the question, identify the topic itself, look at whichever
      bhavas/grahas are relevant for that topic (health → 6H/8H/12H +
      Mars/Saturn/Mercury, career → 10H/Sun/Saturn etc.).
    • Anchor every claim in the chart facts dumped below — do not
      invent anything.

This module is an OPT-IN augmentation. It is wired into
`openai_helper._build_messages` behind the env flag
`LLM_FULL_CHART_MODE` (default OFF). When the flag is OFF the wire-site
no-ops and the existing prompt path is unchanged.

Pure stdlib. No engines/models.py/PKs touched. Read-only over the
inputs — never mutates `kundli` or `intel`.
"""

from __future__ import annotations

from typing import Any, Optional

# ────────────────────────────────────────────────────────────────────
# Constants — ASCII-only signs/lords so the dump renders well in the
# OpenAI prompt regardless of client encoding. We deliberately do not
# import from chart_intelligence.py to keep this module standalone
# (so a smoke test can run it without the heavier import chain).
# ────────────────────────────────────────────────────────────────────

_SIGNS = (
    "Mesh", "Vrish", "Mithun", "Karka", "Simh", "Kanya",
    "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen",
)
# Canonical English sign names — required when calling underlying
# modules (jaimini.compute_arudha_padas, argala.compute_argala) which
# only recognise English zodiac labels. We derive these from
# lagna_sign_idx so the call-sites never reintroduce the
# `ascendant or lagna` short-circuit bug (architect-flagged 01-May-26).
_ENGLISH_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
_SIGN_LORDS = (
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
)
_SIGN_ALIASES = {
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

_PLANET_ORDER = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)

# Functional Benefic / Malefic / Yogakaraka / Neutral classification per
# lagna, following the standard Parashari (BPHS) framework:
#   • Lagna lord, trikona (5L/9L) lords -> functional benefic (FB).
#   • Trika (6L/8L/12L) lords -> functional malefic (FM).
#   • Single planet ruling BOTH a kendra (1/4/7/10) AND a trikona (1/5/9)
#     -> Yogakaraka (YK) — supremely auspicious for that lagna.
#   • Natural benefic (Jup/Ven/Mer) ruling ONLY a kendra -> kendra-adhipati
#     dosha makes it functional malefic.
#   • Mild houses (2L maraka, 3L mild malefic, 11L mixed) -> Neutral (N)
#     unless they double up with trika/kendra rules.
# Indexed by lagna sign (0=Mesh, 1=Vrish, ..., 11=Meen).
# Rahu / Ketu have no sign rulership; they are treated as "shadow malefics"
# separately in the section legend.
_FUNC_NATURE: tuple[dict[str, str], ...] = (
    # 0 Mesh — Mars lagna; Sun=5L (FB, trikona only — NOT YK since no kendra)
    {"Sun": "FB", "Moon": "N",  "Mars": "FB", "Mercury": "FM", "Jupiter": "FB", "Venus": "FM", "Saturn": "FM"},
    # 1 Vrish — Venus lagna; Sat=9L+10L kendra+trikona (YK); Moon=3L (FM mild)
    {"Sun": "FB", "Moon": "FM", "Mars": "FM", "Mercury": "FB", "Jupiter": "FM", "Venus": "N",  "Saturn": "YK"},
    # 2 Mithun — Mercury lagna; no YK; Mer/Ven=FB; Mars/Jup=FM
    {"Sun": "N",  "Moon": "N",  "Mars": "FM", "Mercury": "FB", "Jupiter": "FM", "Venus": "FB", "Saturn": "N"},
    # 3 Karka — Moon lagna; Mars=5L+10L kendra+trikona (YK)
    {"Sun": "N",  "Moon": "FB", "Mars": "YK", "Mercury": "FM", "Jupiter": "FB", "Venus": "FM", "Saturn": "FM"},
    # 4 Simh — Sun lagna; Mars=4L+9L kendra+trikona (YK)
    {"Sun": "FB", "Moon": "N",  "Mars": "YK", "Mercury": "FM", "Jupiter": "FB", "Venus": "FM", "Saturn": "FM"},
    # 5 Kanya — Mercury lagna; Ven=2L+9L (FB by 9L only — NOT YK, no kendra)
    {"Sun": "FM", "Moon": "FM", "Mars": "FM", "Mercury": "FB", "Jupiter": "FM", "Venus": "FB", "Saturn": "N"},
    # 6 Tula — Venus lagna; Sat=4L+5L kendra+trikona (YK)
    {"Sun": "FM", "Moon": "N",  "Mars": "FM", "Mercury": "FB", "Jupiter": "FM", "Venus": "FB", "Saturn": "YK"},
    # 7 Vrishchik — Mars lagna; Sun=10L (FB kendra), Jup=2L+5L (FB)
    {"Sun": "FB", "Moon": "FB", "Mars": "FB", "Mercury": "FM", "Jupiter": "FB", "Venus": "FM", "Saturn": "FM"},
    # 8 Dhanu — Jupiter lagna; Sun=9L (FB), Mars=5L+12L (FB-trikona wins)
    {"Sun": "FB", "Moon": "N",  "Mars": "FB", "Mercury": "FM", "Jupiter": "FB", "Venus": "FM", "Saturn": "FM"},
    # 9 Makar — Saturn lagna; Ven=5L+10L kendra+trikona (YK)
    {"Sun": "FM", "Moon": "FM", "Mars": "FM", "Mercury": "FB", "Jupiter": "FM", "Venus": "YK", "Saturn": "FB"},
    # 10 Kumbh — Saturn lagna; Ven=4L+9L kendra+trikona (YK)
    {"Sun": "FM", "Moon": "FM", "Mars": "FM", "Mercury": "N",  "Jupiter": "FM", "Venus": "YK", "Saturn": "FB"},
    # 11 Meen — Jupiter lagna; Sun=6L (FM), Mars=2L+9L (FB by 9L); Moon=5L (FB)
    {"Sun": "FM", "Moon": "FB", "Mars": "FB", "Mercury": "FM", "Jupiter": "FB", "Venus": "FM", "Saturn": "FM"},
)


# 27 Nakshatras with Vimshottari lords (used to fill Naks/Pada/NL columns
# when the planet object lacks pre-computed nakshatra fields). Order matches
# the standard sidereal sequence starting at 0° Aries.
_NAKSHATRAS: tuple[tuple[str, str], ...] = (
    ("Ashwini", "Ketu"), ("Bharani", "Venus"), ("Krittika", "Sun"),
    ("Rohini", "Moon"), ("Mrigashira", "Mars"), ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"), ("Pushya", "Saturn"), ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"), ("Purva Phalguni", "Venus"), ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"), ("Chitra", "Mars"), ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"), ("Anuradha", "Saturn"), ("Jyeshtha", "Mercury"),
    ("Mula", "Ketu"), ("Purva Ashadha", "Venus"), ("Uttara Ashadha", "Sun"),
    ("Shravana", "Moon"), ("Dhanishtha", "Mars"), ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"), ("Uttara Bhadrapada", "Saturn"), ("Revati", "Mercury"),
)


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────

def _sign_idx(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get("sign") or value.get("name")
    if not isinstance(value, str):
        return None
    return _SIGN_ALIASES.get(value.strip().lower())


def _sign_name(value: Any) -> str:
    idx = _sign_idx(value)
    if idx is None:
        return str(value).strip() if isinstance(value, str) else "?"
    return _SIGNS[idx]


def _fmt_deg(deg: Any) -> str:
    if not isinstance(deg, (int, float)):
        return ""
    try:
        return f"{float(deg):.2f}"
    except Exception:
        return ""


def _suffix(n: int) -> str:
    if 11 <= n <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def _planet_lookup(planets: Any) -> dict[str, dict]:
    """Build {name: planet_dict} for the standard 9 grahas."""
    out: dict[str, dict] = {}
    if not isinstance(planets, list):
        return out
    for p in planets:
        if not isinstance(p, dict):
            continue
        name = (p.get("name") or "").strip()
        if name in _PLANET_ORDER and name not in out:
            out[name] = p
    return out


def _dignity_lookup(intel: Any) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not isinstance(intel, dict):
        return out
    for d in intel.get("dignities") or []:
        if not isinstance(d, dict):
            continue
        name = (d.get("planet") or "").strip()
        if name:
            out[name] = d
    return out


def _naks_pada_lord(lon: Any) -> tuple[str, int, str]:
    """Compute (nakshatra_name, pada 1-4, nak_lord) from sidereal longitude.

    Each nakshatra spans 13°20' (= 48000 arc-seconds); each pada spans
    3°20' (= 12000 arc-seconds). We convert longitude to integer
    arc-seconds before flooring so exact pada boundaries (e.g. 10.0°,
    13.333°, 360°) are not misclassified by float-division drift.
    Returns ("", 0, "") for invalid input.
    """
    if not isinstance(lon, (int, float)):
        return ("", 0, "")
    try:
        L = float(lon) % 360.0
    except Exception:
        return ("", 0, "")
    # 360° = 1_296_000 arc-seconds, 108 padas of 12_000 arc-seconds each.
    # Use floor (int truncate) not round: floor preserves the "less-than"
    # property at exact boundaries — e.g. lon = 10.0° (= 36000 arcsec)
    # correctly lands in pada 4, while lon = 3.3333° (just below 10/3
    # boundary, = 11999 arcsec) correctly stays in pada 1.
    arcsec = int(L * 3600.0)
    pada_idx = (arcsec // 12000) % 108
    nak_idx = pada_idx // 4
    pada = (pada_idx % 4) + 1
    if not (0 <= nak_idx < 27):
        return ("", 0, "")
    name, lord = _NAKSHATRAS[nak_idx]
    return (name, pada, lord)


def _lordship_lookup(intel: Any) -> dict[str, list[int]]:
    """Build planet -> sorted list of houses it rules (from intel.house_lords).

    Mercury (rules H1+H4 for Mithun lagna) -> {"Mercury": [1, 4], ...}.
    Returns {} for missing/malformed intel. Defensive: ignores rows where
    lord is not a string (e.g. accidental int) or house is not an int —
    never raises.
    """
    out: dict[str, list[int]] = {}
    if not isinstance(intel, dict):
        return out
    for hl in intel.get("house_lords") or []:
        if not isinstance(hl, dict):
            continue
        lord_raw = hl.get("lord")
        if not isinstance(lord_raw, str):
            continue
        lord = lord_raw.strip()
        h = hl.get("house")
        if lord and isinstance(h, int):
            out.setdefault(lord, []).append(h)
    for k in out:
        out[k] = sorted(set(out[k]))
    return out


def _functional_nature(planet: str, lagna_sign_idx: Any) -> str:
    """Return Parashari functional nature for a planet given the lagna sign.

    Returns 'FB' (Functional Benefic), 'FM' (Functional Malefic), 'YK'
    (Yogakaraka) or 'N' (Neutral) for the 7 visible planets, '-' for
    Rahu / Ketu (handled separately as shadow malefics in the legend),
    and '' when lagna_sign_idx is missing/invalid.
    """
    if planet in {"Rahu", "Ketu"}:
        return "-"
    # bool is a subclass of int — reject it explicitly to avoid True->1, False->0
    # accidentally mapping to Vrish / Mesh lagnas.
    if not isinstance(lagna_sign_idx, int) or isinstance(lagna_sign_idx, bool):
        return ""
    if not (0 <= lagna_sign_idx < 12):
        return ""
    return _FUNC_NATURE[lagna_sign_idx].get(planet, "")


def _aspects_lookup(kundli: Any) -> dict[str, list[str]]:
    """Build planet -> list of pretty aspect strings like 'H10(Mars)' or 'H6'.

    Includes BOTH the aspected house AND the aspected planet name(s) so the
    LLM sees full Vedic graha-drishti, not just bare house numbers.
    Defensive — returns {} on any failure (compute_aspects import error,
    bad planets list, etc.).
    """
    out: dict[str, list[str]] = {}
    if not isinstance(kundli, dict):
        return out
    planets = kundli.get("planets")
    if not isinstance(planets, list) or not planets:
        return out
    try:
        from aspects import compute_aspects  # type: ignore
    except Exception:
        return out
    asc_idx = _sign_idx(kundli.get("ascendant") or kundli.get("lagna"))
    try:
        asp = compute_aspects(planets, lagna_sign_idx=asc_idx)
    except Exception:
        return out
    by_planet = (asp or {}).get("by_planet") or {}
    if not isinstance(by_planet, dict):
        return out
    for pname, lst in by_planet.items():
        if not isinstance(lst, list):
            continue
        rendered: list[str] = []
        for a in lst:
            if not isinstance(a, dict):
                continue
            h = a.get("house")
            tgts = a.get("aspected_planets") or []
            if not isinstance(h, int):
                continue
            if isinstance(tgts, list) and tgts:
                rendered.append(f"H{h}({','.join(str(t) for t in tgts)})")
            else:
                rendered.append(f"H{h}")
        if rendered:
            out[pname] = rendered
    return out


# ────────────────────────────────────────────────────────────────────
# Section builders
# ────────────────────────────────────────────────────────────────────

def _section_birth_lagna(
    kundli: dict,
    intel: dict | None,
    birth: dict | None,
    p_lookup: dict[str, dict],
) -> str:
    lines: list[str] = ["## 1. JANM & LAGNA"]

    if isinstance(birth, dict):
        bits: list[str] = []
        for label, key in (
            ("Naam", "name"), ("DOB", "dob"), ("Time", "time"),
            ("Sthaan", "place"), ("Gender", "gender"),
        ):
            val = birth.get(key)
            if not val and key == "place":
                val = birth.get("placeName") or birth.get("city")
            if not val and key == "dob":
                val = birth.get("date")
            if val:
                bits.append(f"{label}: {val}")
        if bits:
            lines.append("Janm: " + " | ".join(bits))

    asc = kundli.get("ascendant") or kundli.get("lagna")
    asc_idx = _sign_idx(asc)
    asc_deg = kundli.get("ascendantDeg") or kundli.get("ascendant_lon")
    if asc_idx is not None:
        deg_str = f" {_fmt_deg(asc_deg)}°" if isinstance(asc_deg, (int, float)) else ""
        lord = _SIGN_LORDS[asc_idx]
        lord_p = p_lookup.get(lord) or {}
        lord_house = lord_p.get("house")
        lord_sign = _sign_name(lord_p.get("sign") or lord_p.get("rashi"))
        lord_part = f"Lagnesh: {lord} in H{lord_house} ({lord_sign})" if lord_house else f"Lagnesh: {lord}"
        lines.append(f"Lagna: {_SIGNS[asc_idx]}{deg_str} | {lord_part}")

    moon = kundli.get("moonSign") or kundli.get("moon_sign")
    sun = kundli.get("sunSign") or kundli.get("sun_sign")
    rashi_bits = []
    if moon:
        rashi_bits.append(f"Chandra Rashi: {_sign_name(moon)}")
    if sun:
        rashi_bits.append(f"Surya Rashi: {_sign_name(sun)}")
    if rashi_bits:
        lines.append(" | ".join(rashi_bits))

    nak = kundli.get("nakshatra")
    if nak:
        nak_str = str(nak)
        pada = kundli.get("nakshatraPada") or kundli.get("nakshatra_pada")
        ruler = kundli.get("nakshatraRuler") or kundli.get("nakshatra_lord")
        if pada:
            nak_str += f" pada-{pada}"
        if ruler:
            nak_str += f" (Lord: {ruler})"
        lines.append(f"Janm-Nakshatra: {nak_str}")

    db = kundli.get("dashaBalance") or kundli.get("dasha_balance")
    if isinstance(db, (int, float)) and db > 0:
        lines.append(f"Dasha-balance at birth: {float(db):.2f} years")

    return "\n".join(lines)


def _section_grahas(
    kundli: dict,
    p_lookup: dict[str, dict],
    dig_lookup: dict[str, dict],
    lord_lookup: dict[str, list[int]] | None = None,
    asp_lookup: dict[str, list[str]] | None = None,
    lagna_sign_idx: int | None = None,
) -> str:
    """Render the 9-graha table.

    Columns:
      Graha | House | Sign | Deg | Naks-Pada | NL  | Rules | FN | Status
                                              ^^^   ^^^^^^   ^^   ^^^^^^^^
                                              nak   houses   func dignity, combust,
                                              lord  ruled    nat. retro, aspects
    """
    lord_lookup = lord_lookup or {}
    asp_lookup = asp_lookup or {}
    lines = [
        "## 2. SAARE 9 GRAHAS (full detail)",
        "Graha   | House | Sign       | Deg    | Naks-Pada            | NL      | Rules    | FN | Status",
        "--------|-------|------------|--------|----------------------|---------|----------|----|----------------------------------",
    ]
    any_row = False
    for name in _PLANET_ORDER:
        p = p_lookup.get(name)
        if not isinstance(p, dict):
            continue
        any_row = True
        sign = _sign_name(p.get("sign") or p.get("rashi"))
        house = p.get("house") or "?"
        # Degrees — accept multiple field names; also keep raw longitude for
        # nakshatra computation.
        deg = p.get("degreeInSign") or p.get("deg_in_sign")
        lon = p.get("longitude")
        if deg is None and isinstance(lon, (int, float)):
            deg = float(lon) % 30
        deg_str = _fmt_deg(deg) if deg is not None else ""

        # Nakshatra + Pada + Lord — prefer pre-computed fields on the planet
        # object; otherwise compute from longitude.
        nak = p.get("nakshatra") or ""
        pada = p.get("nakshatraPada") or p.get("pada") or ""
        nak_lord = p.get("nakshatraRuler") or p.get("nakshatra_lord") or ""
        if (not nak or not pada or not nak_lord) and isinstance(lon, (int, float)):
            n2, pd2, nl2 = _naks_pada_lord(lon)
            nak = nak or n2
            pada = pada or (pd2 or "")
            nak_lord = nak_lord or nl2
        nak_pada = f"{nak}-{pada}" if nak and pada else (nak or "")

        # Rules — from intel.house_lords reverse map. Rahu/Ketu have no
        # sign rulership so they show "-".
        ruled = lord_lookup.get(name) or []
        rules = ",".join(f"H{h}" for h in ruled) if ruled else "-"

        # Status — dignity, combust, retro, aspects (with planet targets)
        d = dig_lookup.get(name) or {}
        status_bits: list[str] = []
        dig = d.get("dignity")
        if dig:
            status_bits.append(str(dig))
        if d.get("combust"):
            status_bits.append("combust")
        if p.get("retrograde") and name not in {"Rahu", "Ketu"}:
            status_bits.append("retro")
        # Prefer rich aspects-with-planet-targets from compute_aspects;
        # fall back to dignity.aspects_houses (bare houses) if unavailable.
        asp_strs = asp_lookup.get(name) or []
        if asp_strs:
            status_bits.append("asp " + ",".join(asp_strs))
        else:
            asp_h = d.get("aspects_houses") or []
            if asp_h:
                status_bits.append("asp H" + ",".join(str(a) for a in asp_h))
        status = ", ".join(status_bits) if status_bits else "-"

        # Functional Nature (lagna-based Parashari classification)
        fn = _functional_nature(name, lagna_sign_idx) or "?"

        lines.append(
            f"{name:<7s} | H{str(house):<4s}| {sign:<10s} | "
            f"{deg_str:<6s} | {nak_pada:<20s} | {nak_lord:<7s} | {rules:<8s} | "
            f"{fn:<2s} | {status}"
        )
    if any_row:
        # Legend explaining FN codes — kept tight (one line, ~110 chars)
        # so the chart context overhead stays minimal.
        lines.append(
            "FN legend: FB=Functional Benefic | FM=Functional Malefic | "
            "YK=Yogakaraka (kendra+trikona lord) | N=Neutral | "
            "Rahu/Ketu=shadow malefics (no rulership)"
        )
    return "\n".join(lines) if any_row else ""


def _section_bhavas(
    kundli: dict,
    intel: dict | None,
    p_lookup: dict[str, dict],
) -> str:
    """Render the 12-bhava table using intel.house_lords if present,
    else derive whole-sign from lagna."""
    lines = [
        "## 3. SAARE 12 BHAVAS (full detail)",
        "House | Sign       | Lord     | Lord placement     | Occupants",
        "------|------------|----------|--------------------|-----------------",
    ]

    rows: list[tuple[int, str, str, str]] = []  # (h, sign, lord, lord_placement)

    if isinstance(intel, dict) and intel.get("house_lords"):
        for hl in intel["house_lords"]:
            if not isinstance(hl, dict):
                continue
            h = hl.get("house")
            if not isinstance(h, int):
                continue
            sign = _sign_name(hl.get("sign"))
            lord = hl.get("lord") or ""
            lord_h = hl.get("lord_in_house")
            lord_s = hl.get("lord_in_sign") or ""
            placement = (
                f"H{lord_h} ({_sign_name(lord_s)})"
                if lord_h else f"({_sign_name(lord_s)})"
                if lord_s else "?"
            )
            rows.append((h, sign, lord, placement))
    else:
        asc_idx = _sign_idx(kundli.get("ascendant") or kundli.get("lagna"))
        if asc_idx is None:
            return ""
        for h in range(1, 13):
            s_idx = (asc_idx + h - 1) % 12
            lord = _SIGN_LORDS[s_idx]
            lord_p = p_lookup.get(lord) or {}
            lord_h = lord_p.get("house")
            lord_s = _sign_name(lord_p.get("sign") or lord_p.get("rashi"))
            placement = f"H{lord_h} ({lord_s})" if lord_h else (lord_s or "?")
            rows.append((h, _SIGNS[s_idx], lord, placement))

    # Occupants — derive from p_lookup
    occ_by_house: dict[int, list[str]] = {}
    for name, p in p_lookup.items():
        h = p.get("house")
        if isinstance(h, int):
            occ_by_house.setdefault(h, []).append(name)

    for h, sign, lord, placement in rows:
        occ = ", ".join(occ_by_house.get(h, [])) or "-"
        lines.append(
            f"H{h:<4d}| {sign:<10s} | {lord:<8s} | {placement:<18s} | {occ}"
        )
    return "\n".join(lines)


def _section_dasha(kundli: dict, p_lookup: dict[str, dict]) -> str:
    cd = kundli.get("currentDasha")
    if not isinstance(cd, dict):
        return ""
    lines = ["## 4. CURRENT DASHA TREE"]

    def _placement_for(lord: str | None) -> str:
        if not lord:
            return ""
        lp = p_lookup.get(lord) or {}
        h = lp.get("house")
        s = _sign_name(lp.get("sign") or lp.get("rashi"))
        if h:
            return f" → Lord: {lord} in H{h} ({s})"
        return f" → Lord: {lord}" if lord else ""

    maha = cd.get("maha")
    antar = cd.get("antar")
    pratyantar = cd.get("pratyantar") or cd.get("sookshma")
    starts = cd.get("startDate") or cd.get("start")
    ends = cd.get("endDate") or cd.get("end")

    if maha:
        line = f"Mahadasha:  {maha}"
        if starts and ends:
            line += f" ({starts} → {ends})"
        line += _placement_for(maha)
        lines.append(line)
    if antar:
        a_starts = cd.get("antarStart") or cd.get("antar_start")
        a_ends = cd.get("antarEnd") or cd.get("antar_end")
        line = f"Antardasha: {antar}"
        if a_starts and a_ends:
            line += f" ({a_starts} → {a_ends})"
        line += _placement_for(antar)
        lines.append(line)
    if pratyantar:
        lines.append(f"Pratyantar: {pratyantar}{_placement_for(pratyantar)}")

    # Optional: upcoming antars if kundli provides them
    upcoming = kundli.get("upcomingAntars") or kundli.get("upcoming_antars")
    if isinstance(upcoming, list) and upcoming:
        bits = []
        for u in upcoming[:3]:
            if isinstance(u, dict):
                lord = u.get("antar") or u.get("lord")
                start = u.get("startDate") or u.get("start") or ""
                end = u.get("endDate") or u.get("end") or ""
                if lord:
                    bits.append(f"{lord} ({start}→{end})".strip())
        if bits:
            lines.append("Upcoming antars: " + " ; ".join(bits))

    return "\n".join(lines) if len(lines) > 1 else ""


# ────────────────────────────────────────────────────────────────────
# Section 4B: UPCOMING DASHA SEQUENCE (full Vimshottari, future-only)
# Section 4C: NAVAMSHA D9 (soul / marriage / dharma chart)
# Both ADDED 30 Apr 2026 — Phase 7.7-pre. Defensive: no-op when fields
# missing. Read-only over `kundli`. Pure stdlib.
# ────────────────────────────────────────────────────────────────────

def _today_iso() -> str:
    """Return today in YYYY-MM-DD. Isolated for testability."""
    import datetime as _dt
    return _dt.date.today().isoformat()


def _section_future_dasha(kundli: dict) -> str:
    """Format upcoming Vimshottari dashas: remaining antardashas of the
    current mahadasha + the next several mahadashas. Reads from the
    `dashas` array (full 27-MD Vimshottari tree). Skips silently if
    field missing or shape unexpected.

    Phase 2.8.20 — Window narrowed from 12 years to 7 years to reduce
    prompt token cost (~250 tokens saved/Q). 7-year horizon is still
    sufficient for ~95% of practical timing questions (marriage, career,
    health, finance) without losing locked-window data. Dashas/ADs whose
    startDate falls beyond today+7y are filtered out via _CUTOFF_YEARS.
    Re-tune by editing _CUTOFF_YEARS below; the cutoff is purely a
    display/prompt concern — underlying `dashas` tree is untouched.
    """
    dashas = kundli.get("dashas")
    if not isinstance(dashas, list) or not dashas:
        return ""

    today = _today_iso()

    # Phase 2.8.20 — 7-year forward horizon cutoff.
    _CUTOFF_YEARS = 7
    try:
        import datetime as _dt
        _today_dt = _dt.date.fromisoformat(today)
        _cutoff_dt = _today_dt.replace(year=_today_dt.year + _CUTOFF_YEARS)
        cutoff_iso = _cutoff_dt.isoformat()
    except Exception:
        # If date math fails (leap-day edge case), fall back to no cutoff
        # so the LLM still gets the un-trimmed sequence.
        cutoff_iso = "9999-12-31"

    # 1. Find current mahadasha (startDate <= today < endDate).
    current_md = None
    current_idx = -1
    for i, md in enumerate(dashas):
        if not isinstance(md, dict):
            continue
        s, e = md.get("startDate"), md.get("endDate")
        if isinstance(s, str) and isinstance(e, str) and s <= today < e:
            current_md = md
            current_idx = i
            break

    lines = [f"## 5. UPCOMING DASHA SEQUENCE (Vimshottari, next {_CUTOFF_YEARS} years)"]
    any_row = False

    # 2. Remaining antardashas in current MD (only those starting within window).
    if isinstance(current_md, dict):
        md_planet = current_md.get("planet") or "?"
        md_start  = current_md.get("startDate") or "?"
        md_end    = current_md.get("endDate") or "?"
        lines.append(f"Current Mahadasha: {md_planet} ({md_start} -> {md_end})")
        subs = current_md.get("subDashas")
        if isinstance(subs, list):
            future_ad = [
                ad for ad in subs
                if isinstance(ad, dict)
                and isinstance(ad.get("endDate"), str)
                and ad["endDate"] >= today
                and isinstance(ad.get("startDate"), str)
                and ad["startDate"] <= cutoff_iso
            ]
            if future_ad:
                lines.append("Antardashas remaining in current MD:")
                for ad in future_ad[:9]:
                    p = ad.get("planet") or "?"
                    s = ad.get("startDate") or "?"
                    e = ad.get("endDate") or "?"
                    lines.append(f"  - {md_planet}-{p}: {s} -> {e}")
                any_row = True

    # 3. Next several mahadashas after the current one — only those whose
    # startDate falls inside the 7-year window. We still cap at 5 entries
    # so a chart whose current MD ends in 6 months doesn't blow the budget.
    if current_idx >= 0 and current_idx + 1 < len(dashas):
        future_md_raw = dashas[current_idx + 1 : current_idx + 1 + 5]
        future_md = [
            md for md in future_md_raw
            if isinstance(md, dict)
            and isinstance(md.get("startDate"), str)
            and md["startDate"] <= cutoff_iso
        ]
        if future_md:
            lines.append("Next Mahadashas:")
            for md in future_md:
                p  = md.get("planet") or "?"
                s  = md.get("startDate") or "?"
                e  = md.get("endDate") or "?"
                yr = md.get("years")
                yr_str = f"  [{yr} yrs]" if yr is not None else ""
                lines.append(f"  - {p}: {s} -> {e}{yr_str}")
            any_row = True

    return "\n".join(lines) if any_row else ""


def _section_d9_navamsha(kundli: dict, p_lookup_d1: dict) -> str:
    """Format the D9 (Navamsha) chart: ascendant, planet placements,
    and vargottama flags (planets sharing the same sign in D1 and D9 —
    a major dignity boost).
    """
    dv = kundli.get("divisionalCharts")
    if not isinstance(dv, dict):
        return ""
    d9 = dv.get("D9")
    if not isinstance(d9, dict):
        return ""
    d9_planets = d9.get("planets")
    if not isinstance(d9_planets, list) or not d9_planets:
        return ""

    asc_raw = d9.get("ascendant")
    asc_idx = _sign_idx(asc_raw)
    asc_name = _SIGNS[asc_idx] if asc_idx is not None else (str(asc_raw) if asc_raw else "?")

    lines = [
        "## 6. NAVAMSHA D9 (soul / marriage / dharma / second-half chart)",
        f"D9 Lagna: {asc_name}",
        "Planet placements in D9:",
    ]

    vargottama: list[str] = []
    for pl in d9_planets:
        if not isinstance(pl, dict):
            continue
        name = pl.get("name") or "?"
        h = pl.get("house")
        s_idx = _sign_idx(pl.get("sign"))
        s_name = _SIGNS[s_idx] if s_idx is not None else (str(pl.get("sign")) if pl.get("sign") else "?")
        h_str = f"H{h}" if h else "H?"
        lines.append(f"  - {name:<8s}: {h_str} {s_name}")

        # Vargottama check: same planet in same sign in D1 + D9.
        d1_pl = p_lookup_d1.get(name) or p_lookup_d1.get(name.lower())
        if isinstance(d1_pl, dict):
            d1_idx = _sign_idx(d1_pl.get("sign"))
            if d1_idx is not None and s_idx is not None and d1_idx == s_idx:
                vargottama.append(name)

    if vargottama:
        lines.append(
            "Vargottama (same sign in D1 and D9 = strong, stable, "
            "consistent significations): " + ", ".join(vargottama)
        )
    else:
        lines.append("Vargottama planets: none")

    return "\n".join(lines)


def _section_yogas_doshas(intel: dict | None, kundli: dict) -> str:
    if not isinstance(intel, dict) and not isinstance(kundli, dict):
        return ""
    # NOTE: header originally said "... / GOCHAR" but full transit
    # detail moved to dedicated Section 8 (Phase 2.8.15, 1 May 2026).
    # The transits-from-kundli-dict fallback below still runs for any
    # legacy chart payload that pre-computed gochar inline.
    lines = ["## 7. YOGAS / DOSHAS / SADE-SATI"]
    any_row = False

    yogas = (intel or {}).get("yogas") or kundli.get("yogas") or []
    if isinstance(yogas, list) and yogas:
        any_row = True
        names = [str(y) for y in yogas if y]
        lines.append("Yogas detected: " + " | ".join(names))

    md = (intel or {}).get("mangal_dosh") or kundli.get("mangalDosh") or kundli.get("mangal_dosh")
    if md:
        any_row = True
        lines.append(f"Mangal Dosh: {md}")

    ss = (intel or {}).get("sade_sati") or kundli.get("sadeSati") or kundli.get("sade_sati")
    if ss:
        any_row = True
        if isinstance(ss, dict):
            phase = ss.get("phase") or ss.get("status") or ""
            active = ss.get("active")
            ss_str = f"phase={phase}" if phase else ""
            if active is not None:
                ss_str += (", " if ss_str else "") + f"active={bool(active)}"
            ss = ss_str or str(ss)
        lines.append(f"Sade-Sati: {ss}")

    transits = kundli.get("transits") or kundli.get("gochar")
    if isinstance(transits, dict) and transits:
        bits = []
        for k in ("Saturn", "Jupiter", "Rahu", "Ketu"):
            t = transits.get(k)
            if isinstance(t, dict):
                h = t.get("house")
                s = _sign_name(t.get("sign"))
                if h:
                    bits.append(f"{k}: H{h} ({s})")
            elif isinstance(t, str) and t:
                bits.append(f"{k}: {t}")
        if bits:
            any_row = True
            lines.append("Gochar (transits): " + " ; ".join(bits))

    return "\n".join(lines) if any_row else ""


# ────────────────────────────────────────────────────────────────────
# Section 8 — KP (Krishnamurti Paddhati) — full cusps + planets with all
# four lord-levels (Sign-Lord, Nakshatra-Lord, Sub-Lord, Sub-Sub-Lord)
# and exact degrees. Per project owner (1 May 2026):
#   "Sublord and nakshatra lord and planet ke saath number bhi aana
#    chahiye — har CSL ke sath."
# This is ADD-ONLY: previous KP delivery was topic-filtered via
# `_kp_context()` in openai_helper.py. That path stays. This block now
# guarantees full KP visibility in EVERY question, regardless of topic.
# Defensive — returns "" on any failure so chart context never breaks.
# ────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────
# Section 8 — GOCHAR (current transits / live sky)
#
# Per project owner (1 May 2026): "Pehele 19 add karo." (Item #19 of
# the 20-item LLM-context audit was 'Transit/gochar analysis' which
# was almost entirely missing — only Sade-Sati phase was reaching the
# model via Section 7.)
#
# Why ONLY slow-moving planets (Saturn/Jupiter/Rahu/Ketu)?
#   Fast planets (Sun/Mars/Mer/Ven/Moon) change houses every few days
#   to weeks. Citing a fast-planet transit makes a one-shot LLM answer
#   stale within hours, which trains devotees to distrust the bot.
#   Slow planets stay in a sign for months-to-years, so their gochar
#   facts remain valid across the conversation. (Same scope-decision
#   reasoning as `transits.py` module docstring.)
#
# Uses the existing `transits.compute_transits()` helper (already in
# production for the marriage / career engines), so this section is
# pure rendering + safe defensives. Returns "" on any failure so the
# overall chart context never breaks.
# ────────────────────────────────────────────────────────────────────


def _section_gochar(
    kundli: dict, intel: dict | None, birth: dict | None
) -> str:
    """Render current transits (slow-moving planets) vs natal chart.

    Returns "" if natal lagna can't be resolved, swisseph isn't
    available, or compute_transits() yields nothing usable.
    """
    # Natal lagna — independent fallback (same pattern as Section 2)
    lagna_idx = _sign_idx(kundli.get("ascendant"))
    if lagna_idx is None:
        lagna_idx = _sign_idx(kundli.get("lagna"))
    if lagna_idx is None:
        return ""

    # Natal Moon sign — needed for Sade-Sati / Dhaiya phase. Some
    # legacy chart payloads stored the planet's sign under the `rashi`
    # key instead of `sign`; check both so the Sade-Sati flag still
    # fires across all payload variants.
    moon_idx: Optional[int] = None
    planets = kundli.get("planets")
    if isinstance(planets, list):
        for p in planets:
            if isinstance(p, dict) and p.get("name") == "Moon":
                moon_idx = _sign_idx(p.get("sign") or p.get("rashi"))
                break

    # Optional DOB datetime — only used for Saturn / Jupiter return
    # age-window flags. Build defensively from the structured birth
    # dict (day/month/year). If unavailable, returns still get the
    # current sign + house data, just no age-based return windows.
    dob_dt = None
    if isinstance(birth, dict):
        try:
            from datetime import datetime as _dt
            dob_dt = _dt(
                int(birth["year"]), int(birth["month"]), int(birth["day"])
            )
        except Exception:
            dob_dt = None

    # ── Timezone-correct "as of" handling ─────────────────────────────
    # Architect review flagged: `transits.compute_transits()` uses
    # `datetime.utcnow()` and labels `as_of` in UTC. Around IST
    # midnight (0000-0530 IST) UTC date is "yesterday" from the
    # devotee's clock. Astronomy itself stays correct (swisseph
    # needs UTC), but the *display* must read IST. So we:
    #   • compute `when_utc` ourselves and pass it explicitly,
    #   • override the `as_of` label with IST date, marked "(IST)".
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td
    when_utc = _dt.utcnow()
    _ist = _tz(_td(hours=5, minutes=30))
    as_of_ist = (
        when_utc.replace(tzinfo=_tz.utc).astimezone(_ist).strftime("%Y-%m-%d")
    )

    try:
        from transits import compute_transits  # type: ignore
        t = compute_transits(lagna_idx, moon_idx, dob=dob_dt, when=when_utc)
    except Exception:
        return ""

    if not isinstance(t, dict) or "transit_houses" not in t:
        return ""
    th = t.get("transit_houses")
    if not isinstance(th, dict) or not th:
        return ""

    lines: list[str] = [
        "## 8. GOCHAR (current planetary transits — slow-moving planets)",
        f"As of: {as_of_ist} (IST)",
        "",
        "Planet  | Current Sign  | Natal House (from natal Lagna)",
        "--------|---------------|-------------------------------",
    ]
    for nm in ("Saturn", "Jupiter", "Rahu", "Ketu"):
        info = th.get(nm)
        if not isinstance(info, dict):
            continue
        sign = str(info.get("sign", "?"))
        h = info.get("house_from_lagna", "?")
        lines.append(f"{nm:<7s} | {sign:<13s} | H{h}")

    # Key narrative flags from compute_transits — dump only the ones
    # that compute_transits actually emitted (it self-decides which
    # situations warrant a flag).
    flags: list[str] = []
    for key in (
        "sade_sati_phase",
        "saturn_caution_flag",
        "jupiter_lucky_flag",
        "rahu_theme_flag",
        "saturn_return",
        "jupiter_return",
    ):
        v = t.get(key)
        if isinstance(v, str) and v.strip():
            flags.append(f"  • {v.strip()}")

    j_asp = t.get("jupiter_aspects_houses")
    if isinstance(j_asp, list) and j_asp:
        flags.append(
            "  • Transit Jupiter aspects natal houses: "
            + ", ".join(f"H{h}" for h in j_asp)
        )

    if flags:
        lines.append("")
        lines.append("Key gochar flags (live sky → natal chart):")
        lines.extend(flags)

    lines.append("")
    lines.append("GOCHAR READING RULE:")
    lines.append(
        "  • Slow-moving transits (Saturn/Jupiter/Rahu/Ketu) drive "
        "BIG-LIFE timing themes."
    )
    lines.append(
        "  • Transit signals FRUCTIFY when active Mahadasha/Antardasha "
        "aligns with the same house/theme — always cross-check Section 4."
    )

    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────
# Section 9 — DASHA + TRANSIT OVERLAY (live synthesis)
#
# Per project owner (1 May 2026, immediately after Phase 2.8.15):
# "#20 start". Item #20 of the LLM-context audit is the synthesis
# that matters MOST for timing questions: "the active dasha lord's
# CURRENT-RIGHT-NOW transit position cross-checked against the natal
# chart". Without this, the LLM had Section 4 (active dasha) and
# Section 8 (gochar of slow planets) as two disconnected facts and
# had to do the join itself — which it cannot do for fast-moving
# dasha lords (Mer/Ven/Mars/Sun/Moon) because their current sky
# position simply isn't in its training data.
#
# This section does the join deterministically:
#   • Reads MD / AD / PD planet names from `kundli.currentDasha`
#   • Computes RIGHT-NOW sidereal longitude for those exact planets
#     (any of the 9 grahas — fast or slow, doesn't matter — since
#     this section is short-lived per question, not cached)
#   • Derives transit sign, transit house from natal Lagna,
#     supportive/restrictive flags, and combust check
#   • Forces an explicit OVERLAY READING RULE footer that teaches the
#     LLM the synthesis logic (echo amplification, kendra-trikona
#     supportive houses, dusthana restrictive houses, combust mute).
#
# This is the highest-leverage single addition: a "Saturn MD active +
# Saturn currently transiting your H10" type insight is impossible
# without explicit overlay data, and is exactly the answer devotees
# expect from a real Vedic guru.
#
# Defensive — returns "" on any failure so chart context never breaks.
# ────────────────────────────────────────────────────────────────────

# Planet → swisseph body ID. Mirrors `kp_engine.PLANET_IDS` so we
# don't drift if that map ever changes; intentionally re-declared
# here so this file stays self-contained for ADD-ONLY edits.
_OVERLAY_SWE_IDS: dict[str, int] = {}
try:
    import swisseph as _swe_overlay  # type: ignore
    _OVERLAY_SWE_IDS = {
        "Sun":     _swe_overlay.SUN,
        "Moon":    _swe_overlay.MOON,
        "Mars":    _swe_overlay.MARS,
        "Mercury": _swe_overlay.MERCURY,
        "Jupiter": _swe_overlay.JUPITER,
        "Venus":   _swe_overlay.VENUS,
        "Saturn":  _swe_overlay.SATURN,
        "Rahu":    _swe_overlay.MEAN_NODE,
        # Ketu derived as Rahu + 180°, no swisseph body
    }
    _swe_overlay.set_sid_mode(_swe_overlay.SIDM_LAHIRI)
    _OVERLAY_FLAGS = _swe_overlay.FLG_SWIEPH | _swe_overlay.FLG_SIDEREAL
    _OVERLAY_HAS_SWE = True
except Exception:  # pragma: no cover
    _swe_overlay = None  # type: ignore
    _OVERLAY_FLAGS = 0
    _OVERLAY_HAS_SWE = False


def _planet_lon_now(name: str, when_utc) -> Optional[float]:
    """Sidereal Lahiri longitude (deg, 0-360) for any of the 9 grahas
    at `when_utc`. Returns None on swisseph error. Ketu = Rahu + 180.
    """
    if not _OVERLAY_HAS_SWE or not name:
        return None
    canonical = name.strip().capitalize()
    if canonical == "Ketu":
        rahu_lon = _planet_lon_now("Rahu", when_utc)
        if rahu_lon is None:
            return None
        return (rahu_lon + 180.0) % 360.0
    pid = _OVERLAY_SWE_IDS.get(canonical)
    if pid is None:
        return None
    try:
        jd = _swe_overlay.julday(
            when_utc.year, when_utc.month, when_utc.day,
            when_utc.hour + when_utc.minute / 60.0
        )
        pos, _ = _swe_overlay.calc_ut(jd, pid, _OVERLAY_FLAGS)
        return float(pos[0]) % 360.0
    except Exception:
        return None


def _section_dasha_transit_overlay(
    kundli: dict, intel: dict | None, birth: dict | None
) -> str:
    """Render dasha-lord-vs-current-transit synthesis.

    Returns "" if currentDasha unavailable, swisseph missing, or
    natal lagna unresolvable.
    """
    if not _OVERLAY_HAS_SWE:
        return ""
    cd = kundli.get("currentDasha")
    if not isinstance(cd, dict):
        return ""

    # Natal lagna sign — independent fallback (same pattern as Section 8)
    lagna_idx = _sign_idx(kundli.get("ascendant"))
    if lagna_idx is None:
        lagna_idx = _sign_idx(kundli.get("lagna"))
    if lagna_idx is None:
        return ""

    # Build natal sign-by-planet lookup for the NATAL-SIGN RESONANCE
    # flag (transit planet returning to the same sign it occupies in
    # the natal chart). Architect review (1 May 2026) corrected my
    # earlier misnaming of this as "swagriha/home turf" — those terms
    # mean "planet in the sign IT RULES" (e.g. Sun in Leo) which is a
    # different concept. Resonance is purely positional; it does not
    # imply swakshetra dignity. Keys normalised to lowercase so a
    # mixed-case payload ("MOON" vs "Moon") still matches.
    natal_sign: dict[str, Optional[int]] = {}
    for p in (kundli.get("planets") or []):
        if isinstance(p, dict):
            nm = p.get("name")
            if isinstance(nm, str):
                natal_sign[nm.strip().lower()] = _sign_idx(
                    p.get("sign") or p.get("rashi")
                )

    from datetime import datetime as _dt, timezone as _tz, timedelta as _td
    when_utc = _dt.utcnow()
    _ist = _tz(_td(hours=5, minutes=30))
    as_of_ist = (
        when_utc.replace(tzinfo=_tz.utc).astimezone(_ist).strftime("%Y-%m-%d")
    )

    # Pre-compute current Sun longitude for combust check (inner planets only)
    sun_lon = _planet_lon_now("Sun", when_utc)

    def _row(label: str, planet_name: Optional[str], end_date: Optional[str]) -> list[str]:
        """Render one dasha-level block. Returns [] if planet missing or
        current position can't be computed."""
        if not planet_name or not isinstance(planet_name, str):
            return []
        canonical = planet_name.strip().capitalize()
        cur_lon = _planet_lon_now(canonical, when_utc)
        if cur_lon is None:
            return []
        cur_sign_idx = int(cur_lon // 30) % 12
        deg_in_sign = cur_lon - (cur_sign_idx * 30.0)
        nat_house = ((cur_sign_idx - lagna_idx) % 12) + 1
        sign_str = _SIGN_NAMES_OUT[cur_sign_idx]

        end_str = f" — until {end_date}" if end_date else ""
        out = [f"{label} ({canonical}{end_str}):"]
        out.append(
            f"  • Now in: {sign_str} {deg_in_sign:.2f}\u00b0  "
            f"→ transiting natal H{nat_house} from Lagna"
        )

        flags: list[str] = []
        # Echo amplification (always true for the lord we're rendering,
        # but worth making explicit for the LLM)
        flags.append(
            f"{canonical} ki dasha + {canonical} ka transit = ECHO "
            "(themes amplify during this overlap)"
        )
        # Supportive houses
        if nat_house in (1, 5, 9):
            flags.append(
                f"H{nat_house} = kendra/trikona — SUPPORTIVE for "
                f"{canonical}'s dasha themes"
            )
        elif nat_house == 11:
            flags.append("H11 = labha-bhava — gains/wishes SUPPORTIVE")
        elif nat_house == 10:
            flags.append("H10 = karma-bhava — career/karma intensification")
        # Restrictive houses
        if nat_house in (6, 8, 12):
            flags.append(
                f"H{nat_house} = dusthana — RESTRICTIVE (delays/hidden "
                f"hurdles for {canonical} themes)"
            )
        # NATAL-SIGN RESONANCE: transit returning to the same sign it
        # occupies natally. Note: this is positional-only and does NOT
        # imply swakshetra (own-sign rulership) — see comment block at
        # top of natal_sign dict for the architect-flagged correction.
        nat_sgn = natal_sign.get(canonical.lower())
        if nat_sgn is not None and nat_sgn == cur_sign_idx:
            flags.append(
                f"NATAL-SIGN RESONANCE — {canonical} transit is in same "
                f"sign as natal {canonical} (positional return; STRONG "
                "dasha-echo regardless of dignity)"
            )
        # Combust check — only inner planets get combust by Sun
        if canonical in ("Mercury", "Venus", "Mars") and sun_lon is not None:
            diff = abs((cur_lon - sun_lon + 180.0) % 360.0 - 180.0)
            if diff <= 8.0:
                flags.append(
                    f"COMBUST — only {diff:.1f}\u00b0 from Sun → "
                    f"{canonical}'s dasha effects MUTED in this window"
                )

        for f in flags:
            out.append(f"  • {f}")
        return out

    lines: list[str] = [
        "## 9. DASHA + TRANSIT OVERLAY (live synthesis: Section 4 \u00d7 Section 8)",
        f"As of: {as_of_ist} (IST)",
        "",
        "Active dasha lords' RIGHT-NOW sidereal positions vs natal chart:",
        "",
    ]

    md_block = _row(
        "Maha",
        cd.get("maha"),
        cd.get("endDate") or cd.get("end"),
    )
    if md_block:
        lines.extend(md_block)
        lines.append("")

    ad_block = _row(
        "Antar",
        cd.get("antar"),
        cd.get("antarEnd") or cd.get("antar_end"),
    )
    if ad_block:
        lines.extend(ad_block)
        lines.append("")

    pd_block = _row(
        "Pratyantar",
        cd.get("pratyantar") or cd.get("sookshma"),
        cd.get("pratyantarEnd") or cd.get("pratyantar_end"),
    )
    if pd_block:
        lines.extend(pd_block)
        lines.append("")

    # If NO blocks rendered (no MD/AD/PD names or all swisseph-failed),
    # bail out — empty overlay is misleading
    if not (md_block or ad_block or pd_block):
        return ""

    lines.append("OVERLAY READING RULE:")
    lines.append(
        "  • Active dasha lord's CURRENT transit position is the timing trigger. "
        "Strong placement amplifies dasha themes; weak placement delays them."
    )
    lines.append(
        "  • Supportive houses: 1, 5, 9, 11 (kendra-trikona-labha)."
    )
    lines.append(
        "  • Restrictive houses: 6, 8, 12 (dusthana — hidden hurdles)."
    )
    lines.append(
        "  • Inner planet within \u00b18\u00b0 of Sun = COMBUST → mutes "
        "that dasha lord during the combust window. (We use a uniform "
        "8\u00b0 orb for Mer/Ven/Mars — strict to minimise false positives. "
        "Classical orbs are wider per-planet; flag absence does not "
        "rule out near-combust influence.)"
    )
    lines.append(
        "  • Use this overlay for SHORT-TERM timing within the active "
        "dasha; cross-check Sections 4 + 8 for the full picture."
    )

    return "\n".join(lines)


# Sign-name list used by overlay row renderer. Local copy to keep
# this section self-contained (matches the existing _sign_name table).
_SIGN_NAMES_OUT = [
    "Mesh", "Vrish", "Mithun", "Karka", "Simh", "Kanya",
    "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen",
]


# ────────────────────────────────────────────────────────────────────
# Section 10 — ARUDHA PADAS  (Item #26)
# Image / perception layer (Jaimini). Surfaces the 4 most actionable
# padas: AL (public image), A7 (spouse perception), A10 (career
# image), A12/UL (marriage signature). Defensive — silent skip on any
# failure so a missing module never breaks the chart dump.
# ────────────────────────────────────────────────────────────────────
def _section_arudha(kundli: dict, lagna_sign_idx: Optional[int]) -> str:
    if lagna_sign_idx is None:
        return ""
    try:
        from jaimini import compute_arudha_padas  # type: ignore
    except Exception:
        return ""

    planets = kundli.get("planets") or []
    if not planets:
        return ""

    # jaimini.compute_arudha_padas requires English sign names. Derive
    # canonical English from lagna_sign_idx instead of relying on the
    # caller's possibly-Hinglish `ascendant`/`lagna` field.
    try:
        lagna_en = _ENGLISH_SIGNS[int(lagna_sign_idx) % 12]
    except (TypeError, ValueError, IndexError):
        return ""

    try:
        result = compute_arudha_padas(planets, lagna_en)
    except Exception:
        return ""

    padas = (result or {}).get("padas") or {}
    if not padas:
        return ""

    show = [
        ("A1",  "AL — public image / how world sees native"),
        ("A7",  "perception of spouse / partnerships"),
        ("A10", "career image / public reputation"),
        ("A12", "UL — marriage / long-term commitment signature"),
    ]

    lines = ["## 10. ARUDHA PADAS (Image / Perception layer — Jaimini)"]
    for key, label in show:
        p = padas.get(key)
        if not isinstance(p, dict):
            continue
        sign_hi = _sign_name(p.get("sign"))
        lord = p.get("lord", "?")
        lord_in_hi = _sign_name(p.get("lord_in"))
        note = p.get("note") or ""
        note_str = f"  [{note}]" if note else ""
        lines.append(
            f"  \u2022 {key} ({label}): {sign_hi}, lord {lord} in "
            f"{lord_in_hi}{note_str}"
        )

    if len(lines) == 1:
        return ""

    lines.append("")
    lines.append("ARUDHA READING RULE:")
    lines.append(
        "  \u2022 Arudha = how world PERCEIVES that life area "
        "(vs natal house = inner reality)."
    )
    lines.append(
        "  \u2022 AL different from Lagna sign \u2192 outer image vs "
        "inner self can mismatch."
    )
    lines.append(
        "  \u2022 Planets in / aspecting an Arudha sign colour the "
        "perception of that life area."
    )

    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────
# Section 11 — ASHTAKAVARGA  (Item #27)
# SAV (Sarvashtakavarga) per house with strength verdicts. Reuses the
# existing ashtakavarga.compute_ashtakavarga + format_sav_summary so
# the BPHS contribution tables stay centralised in one module.
# ────────────────────────────────────────────────────────────────────
def _section_ashtakavarga(kundli: dict, lagna_sign_idx: Optional[int]) -> str:
    if lagna_sign_idx is None:
        return ""
    try:
        from ashtakavarga import (  # type: ignore
            compute_ashtakavarga,
            format_sav_summary,
        )
    except Exception:
        return ""

    planets = kundli.get("planets") or []
    if not planets:
        return ""

    try:
        av = compute_ashtakavarga(planets, lagna_sign_idx)
    except Exception:
        return ""
    if not av or "sav" not in av:
        return ""

    try:
        summary = format_sav_summary(av)
    except Exception:
        return ""
    if not summary:
        return ""

    lines = ["## 11. ASHTAKAVARGA (Point-system house strength — BPHS)"]
    lines.append(summary)
    lines.append("")
    lines.append("ASHTAKAVARGA READING RULE:")
    lines.append(
        "  \u2022 SAV per house = total bindus contributed by all 7 "
        "planets (max ~56, avg ~28). Total across 12 houses = 337."
    )
    lines.append(
        "  \u2022 Bands: 32+ VERY STRONG (effortless), 28-31 STRONG "
        "(reliable delivery), 25-27 AVERAGE (mixed/conditional), "
        "<25 WEAK (struggles, remedies indicated)."
    )
    lines.append(
        "  \u2022 Strong house \u2192 affairs of that bhava fructify with "
        "less obstruction during relevant dasha/transit; weak house "
        "\u2192 native struggles even with promising dasha lord."
    )
    lines.append(
        "  \u2022 Cross-check: an event-trigger transit through a HIGH-SAV "
        "house gives stronger results than the same transit through a LOW-SAV house."
    )

    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────
# Section 12 — SHADBALA  (Item #28)
# Per-planet 6-fold quantitative strength (in virupas). Sorts by
# strength% so LLM sees strongest \u2192 weakest at a glance. Highlights
# any planet below required minimum.
# ────────────────────────────────────────────────────────────────────
def _section_shadbala(kundli: dict, lagna_sign_idx: Optional[int]) -> str:
    if lagna_sign_idx is None:
        return ""
    try:
        from shadbala import compute_shadbala  # type: ignore
    except Exception:
        return ""

    planets = kundli.get("planets") or []
    if not planets:
        return ""

    # Normalise planet dicts for compute_shadbala which expects keys
    # `lon` and `house`. Our chart payload uses `longitude` for the
    # absolute ecliptic longitude, so map it across (without mutating
    # the caller's list).
    norm_planets: list[dict] = []
    for p in planets:
        if not isinstance(p, dict):
            continue
        np = dict(p)  # shallow copy — safe to add `lon`
        if "lon" not in np and isinstance(np.get("longitude"), (int, float)):
            np["lon"] = float(np["longitude"])
        norm_planets.append(np)

    try:
        sb = compute_shadbala(norm_planets, lagna_sign_idx)
    except Exception:
        return ""
    if not isinstance(sb, dict) or not sb:
        return ""

    # Sort planets by strength_pct desc (strongest first)
    rows: list[tuple[str, float, float, float]] = []
    for name, data in sb.items():
        if not isinstance(data, dict):
            continue
        try:
            total = float(data.get("total") or 0)
            req = float(data.get("required") or 0)
            pct = float(data.get("strength_pct") or 0)
        except (TypeError, ValueError):
            continue
        rows.append((name, total, req, pct))
    if not rows:
        return ""

    rows.sort(key=lambda r: r[3], reverse=True)

    lines = ["## 12. SHADBALA (Quantitative planet strength — 6-fold, in virupas)"]
    lines.append("  Planet  | Total  | Required | Str%   | Verdict")
    for name, total, req, pct in rows:
        if pct >= 100:
            verdict = "STRONG (meets minimum)"
        elif pct >= 80:
            verdict = "ADEQUATE (near minimum)"
        else:
            verdict = "WEAK (below minimum)"
        lines.append(
            f"  {name:<7} | {total:6.1f} | {req:8.1f} | {pct:5.1f}% | {verdict}"
        )

    weakest = [n for n, _, _, p in rows if p < 80]
    strongest = [n for n, _, _, p in rows if p >= 100]
    if strongest:
        lines.append(f"  STRONGEST grahas: {', '.join(strongest)}")
    if weakest:
        lines.append(f"  WEAK grahas (below 80%): {', '.join(weakest)}")

    lines.append("")
    lines.append("SHADBALA READING RULE:")
    lines.append(
        "  \u2022 Strength% \u2265 100 \u2192 graha meets classical minimum, "
        "can deliver own karaka themes during its dasha/transit."
    )
    lines.append(
        "  \u2022 80-100% \u2192 adequate; delivers with some effort/conditions."
    )
    lines.append(
        "  \u2022 < 80% \u2192 weak; struggles to deliver, results often delayed "
        "or partial; remedies indicated."
    )
    lines.append(
        "  \u2022 Note: Rahu/Ketu have no Shadbala in classical Parashari."
    )

    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────
# Section 13 — ARGALA / VIRODHARGALA  (Item #25)
# Jaimini intervention summary across general houses (1, 10, 7, 4) —
# the four most-cited bhavas. Also flags any STRONG-MALEFIC house
# across all 12 so LLM can warn of obstructive interventions on the
# fly when topic touches that bhava.
# ────────────────────────────────────────────────────────────────────
def _section_argala(kundli: dict, lagna_sign_idx: Optional[int]) -> str:
    if lagna_sign_idx is None:
        return ""
    try:
        from argala import compute_argala, format_argala_summary  # type: ignore
    except Exception:
        return ""

    planets = kundli.get("planets") or []
    if not planets:
        return ""

    # argala.compute_argala expects an English sign name (or dict
    # whose `sign`/`name` is English). Derive from lagna_sign_idx so
    # the call-site never silently skips on a Hinglish payload.
    try:
        lagna_en = _ENGLISH_SIGNS[int(lagna_sign_idx) % 12]
    except (TypeError, ValueError, IndexError):
        return ""

    try:
        argala = compute_argala(planets, lagna_en)
    except Exception:
        return ""
    if not isinstance(argala, dict) or not argala:
        return ""

    try:
        # general topic = houses 1, 10, 7, 4 (broadest coverage)
        summary = format_argala_summary(argala, topic="general", max_houses=4)
    except Exception:
        summary = ""

    lines = ["## 13. ARGALA / VIRODHARGALA (Jaimini intervention)"]
    if summary:
        lines.append(summary)

    # Cross-house scan — flag any STRONG-MALEFIC overall verdict
    # so LLM is warned regardless of topic.
    strong_malefic = [
        h for h, info in argala.items()
        if isinstance(info, dict) and info.get("overall") == "STRONG-MALEFIC"
    ]
    strong_benefic = [
        h for h, info in argala.items()
        if isinstance(info, dict) and info.get("overall") == "STRONG-BENEFIC"
    ]
    if strong_benefic:
        lines.append(
            "  \u25b8 STRONG-BENEFIC argala on houses: "
            + ", ".join(f"H{h}" for h in sorted(strong_benefic))
        )
    if strong_malefic:
        lines.append(
            "  \u25b8 STRONG-MALEFIC argala on houses: "
            + ", ".join(f"H{h}" for h in sorted(strong_malefic))
            + "  (obstruction in those bhava themes)"
        )

    if len(lines) == 1:  # only the header — no real data
        return ""

    lines.append("")
    lines.append("ARGALA READING RULE:")
    lines.append(
        "  \u2022 Argala = planets in 2nd / 4th / 5th / 11th from a "
        "house intervene in its affairs."
    )
    lines.append(
        "  \u2022 Virodhargala = counter-intervention from 12th / 10th "
        "/ 9th / 3rd cancels the corresponding Argala."
    )
    lines.append(
        "  \u2022 Net BENEFIC argala uncancelled \u2192 supportive "
        "intervention; net MALEFIC uncancelled \u2192 obstructive."
    )
    lines.append(
        "  \u2022 Use this layer to refine a bhava verdict beyond just "
        "occupants/aspects \u2014 it answers \u201cwho is meddling in this house?\u201d."
    )

    return "\n".join(lines)


def _section_kp(birth: dict | None, kundli: dict | None = None) -> str:
    if not isinstance(birth, dict) or not birth:
        return ""
    required = ("day", "month", "year", "hour", "minute", "ampm", "lat", "lon", "tz")
    if not all(k in birth and birth[k] is not None for k in required):
        return ""

    try:
        # Phase 2.8.58: prefer cached kundli["kp"] (baked at compute time and
        # lazy-repaired on /api/kundli cache hits) over Swiss Ephemeris recompute.
        from kp_engine import get_or_compute_kp  # type: ignore
        kp = get_or_compute_kp(kundli, birth)
        if not kp:
            return ""
    except Exception:
        return ""

    cusps = kp.get("cusps") or []
    planets = kp.get("planets") or []
    if not cusps and not planets:
        return ""

    lines: list[str] = ["## 14. KP (KRISHNAMURTI PADDHATI) — FULL CUSPS + PLANETS"]
    aya = kp.get("ayanamsa")
    if aya is not None:
        try:
            lines.append(f"Ayanamsa (Krishnamurti): {float(aya):.4f}\u00b0")
        except Exception:
            pass

    # ── 12 cusps with CSL/NL/SL/SS + degree ─────────────────────────
    if cusps:
        lines.append("")
        lines.append("CUSPS (CSL = Cusp Sub-Lord = FINAL deciding authority for that house):")
        lines.append("  Hse | Degree              | Nakshatra      | Sign-L  | Nak-L   | Sub-L (CSL) | Sub-Sub")
        for c in cusps:
            try:
                h = c.get("house")
                deg = str(c.get("degree", ""))
                nak = str(c.get("nakshatra", ""))
                sl = str(c.get("sl", ""))
                nl = str(c.get("nl", ""))
                sb = str(c.get("sb", ""))
                ss = str(c.get("ss", ""))
                lon = c.get("longitude")
                lon_str = f"{float(lon):7.3f}\u00b0" if isinstance(lon, (int, float)) else "       "
                lines.append(
                    f"  H{h:<2} | {deg:<10} {lon_str} | {nak:<13} | {sl:<7} | {nl:<7} | {sb:<11} | {ss}"
                )
            except Exception:
                continue

    # ── 9 planets with their KP lord chain + degree ──────────────────
    if planets:
        lines.append("")
        lines.append("PLANETS (Sub-Lord = KP outcome decider for each planet):")
        lines.append("  Planet  | Degree              | House | Nakshatra      | Sign-L  | Nak-L   | Sub-L   | Sub-Sub")
        for p in planets:
            try:
                name = str(p.get("name", ""))
                deg = str(p.get("degree", ""))
                hse = p.get("house", "")
                nak = str(p.get("nakshatra", ""))
                sl = str(p.get("sl", ""))
                nl = str(p.get("nl", ""))
                sb = str(p.get("sb", ""))
                ss = str(p.get("ss", ""))
                lon = p.get("longitude")
                lon_str = f"{float(lon):7.3f}\u00b0" if isinstance(lon, (int, float)) else "       "
                lines.append(
                    f"  {name:<7} | {deg:<10} {lon_str} | H{hse:<3} | {nak:<13} | {sl:<7} | {nl:<7} | {sb:<7} | {ss}"
                )
            except Exception:
                continue

    # ── KP rule reminders (compact) ──────────────────────────────────
    lines.append("")
    lines.append("KP READING RULE:")
    lines.append("  • Cusp Sub-Lord (CSL) of a house decides whether that house matter happens or not.")
    lines.append("  • A house matter fructifies during Dasha-Bhukti-Antara of planets that signify")
    lines.append("    the relevant houses (via star/sub-lord chain).")
    lines.append("  • If CSL signifies the relevant houses for the question → YES (event will occur).")
    lines.append("  • If CSL signifies negation houses (e.g. 6/8/12 for marriage) → NO / denial.")

    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────
# Minimal guidance — per project owner (30 Apr 2026):
#   "Engine cheat-sheet jo jo he, woh sara chiz hatao. Mujhse abhi itna
#    chahiye ji AI ko jo question diya jaye, woh pura samaj paaye, kundli
#    jo store he wahan se data le."
#
# Earlier this section also held a karaka/house cheat-sheet (Section 6)
# and a prescriptive answer template — Verdict / Dekha kya / Timing /
# Upay (Section 7). BOTH have been intentionally REMOVED. The model is
# now trusted to apply its own Vedic Jyotish knowledge to the chart
# data dumped in Sections 1-5. Only two safety rails remain:
#   1. Anti-hallucination: cite only fields that appear in the chart
#      dump above; do not invent placements / dashas / yogas.
#   2. Language: reply in Hinglish (devotee's preference).
# ────────────────────────────────────────────────────────────────────

_MINIMAL_GUIDANCE = """## 15. NIYAM (sirf 2 — baaki tum khud decide karo)

• Sirf upar di hui kundli ke fields cite karo. Koi naya graha placement,
  dasha, ya yoga IMAGINE NAHI karna. Agar zaroori detail upar nahi hai,
  honestly bolo "iska clear data abhi available nahi" — guess mat karo.
• Hinglish mein jawab do (Devanagari + English mix, simple bhasha).
  Emoji nahi.
"""


# ────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────

_HEADER = "═══════ POORI KUNDLI (FULL CHART ACCESS — Phase 7.7-pre) ═══════"
_FOOTER = "═══════════════════════════════════════════════════════════════"


def build_full_chart_context(
    kundli: Any,
    intel: Any = None,
    birth: Any = None,
    question: str = "",  # accepted for API stability; intentionally NOT echoed
) -> str:
    """Build the full-chart-access prompt block.

    Returns "" when kundli is missing/empty so the wire-site can no-op.
    Never raises — defensive on every field.

    Security note: ``question`` is accepted for backward-compatible callers
    but is intentionally NOT echoed inside this block. The block becomes a
    SYSTEM message; echoing user-controlled text into a system-priority
    context would elevate prompt-injection risk. The devotee's actual
    question is delivered to the model via the normal user-role message.
    """
    # Touch ``question`` so static analysers don't flag it; the value is
    # deliberately unused inside the system block (see security note).
    _ = question
    if not isinstance(kundli, dict) or not kundli:
        return ""

    intel_d = intel if isinstance(intel, dict) else None
    birth_d = birth if isinstance(birth, dict) else None

    p_lookup = _planet_lookup(kundli.get("planets"))
    if not p_lookup:
        # Without any planet data, the dump is useless.
        return ""

    dig_lookup = _dignity_lookup(intel_d)
    lord_lookup = _lordship_lookup(intel_d)
    asp_lookup = _aspects_lookup(kundli)
    # Lagna sign index drives the Parashari Functional Nature column.
    # Try ascendant first, then fall back to lagna independently — the prior
    # `or` short-circuit dropped the lagna fallback whenever ascendant was a
    # truthy-but-unparsable dict (e.g. {"degree": 12.5} with no sign/name).
    lagna_idx = _sign_idx(kundli.get("ascendant"))
    if lagna_idx is None:
        lagna_idx = _sign_idx(kundli.get("lagna"))

    sections: list[str] = []

    try:
        sections.append(_section_birth_lagna(kundli, intel_d, birth_d, p_lookup))
    except Exception:
        pass
    try:
        s = _section_grahas(
            kundli, p_lookup, dig_lookup, lord_lookup, asp_lookup,
            lagna_sign_idx=lagna_idx,
        )
        if s:
            sections.append(s)
    except Exception:
        pass
    try:
        s = _section_bhavas(kundli, intel_d, p_lookup)
        if s:
            sections.append(s)
    except Exception:
        pass
    try:
        s = _section_dasha(kundli, p_lookup)
        if s:
            sections.append(s)
    except Exception:
        pass
    try:
        s = _section_future_dasha(kundli)
        if s:
            sections.append(s)
    except Exception:
        pass
    try:
        s = _section_d9_navamsha(kundli, p_lookup)
        if s:
            sections.append(s)
    except Exception:
        pass
    try:
        s = _section_yogas_doshas(intel_d, kundli)
        if s:
            sections.append(s)
    except Exception:
        pass
    # Section 8 — GOCHAR (current transits). Inserted BEFORE KP so the
    # "live sky vs natal" picture is fresh in the LLM's context before
    # it descends into deep KP fructification analysis. Defensive try
    # so a swisseph hiccup never blocks the rest of the chart context.
    try:
        s = _section_gochar(kundli, intel_d, birth_d)
        if s:
            sections.append(s)
    except Exception:
        pass
    # Section 9 — DASHA + TRANSIT OVERLAY. Live synthesis of Section 4
    # (active dasha) × Section 8 (gochar). Highest-leverage timing
    # context block: tells LLM exactly where each active dasha lord
    # is RIGHT NOW vs the natal chart so it can give nuanced
    # "echo amplification" / "kendra transit supports your AD theme"
    # answers instead of generic ones. Defensive — skips silently
    # when currentDasha missing or swisseph unavailable.
    try:
        s = _section_dasha_transit_overlay(kundli, intel_d, birth_d)
        if s:
            sections.append(s)
    except Exception:
        pass
    # ─── DISABLED 2026-05-01 (per user request) ───────────────────────────
    # Sections 10-13 (ARUDHA / ASHTAKAVARGA / SHADBALA / ARGALA) ko LLM
    # prompt me NAHI bhejna. Functions still exist (ADD-ONLY policy) and
    # can be re-enabled by flipping _SEND_SECTIONS_10_TO_13 to True below.
    # Archive copy: artifacts/api-server/disabled_sections/sections_10_to_13.py
    _SEND_SECTIONS_10_TO_13 = False
    if _SEND_SECTIONS_10_TO_13:
        # Section 10 — ARUDHA PADAS (Item #26). Image / perception layer
        # from Jaimini. Independent of dasha/transit so wired right after
        # the live-sky block. Defensive — silent skip if jaimini import or
        # arudha computation fails.
        try:
            s = _section_arudha(kundli, lagna_idx)
            if s:
                sections.append(s)
        except Exception:
            pass
        # Section 11 — ASHTAKAVARGA (Item #27). SAV per house point-system
        # strength. Pure BPHS contribution tables; independent of dasha.
        try:
            s = _section_ashtakavarga(kundli, lagna_idx)
            if s:
                sections.append(s)
        except Exception:
            pass
        # Section 12 — SHADBALA (Item #28). 6-fold quantitative planet
        # strength (in virupas) sorted strongest → weakest. Required for
        # answering "is X graha able to deliver?" type questions.
        try:
            s = _section_shadbala(kundli, lagna_idx)
            if s:
                sections.append(s)
        except Exception:
            pass
        # Section 13 — ARGALA / VIRODHARGALA (Item #25). Jaimini
        # intervention layer. Refines bhava verdicts beyond just
        # occupants/aspects with "who is meddling in this house?".
        try:
            s = _section_argala(kundli, lagna_idx)
            if s:
                sections.append(s)
        except Exception:
            pass
    # ─── END DISABLED BLOCK ───────────────────────────────────────────────
    try:
        # Phase 2.8.58: pass kundli so _section_kp can prefer cached kp over recompute
        s = _section_kp(birth_d, kundli)
        if s:
            sections.append(s)
    except Exception:
        pass

    sections.append(_MINIMAL_GUIDANCE.rstrip())

    body = "\n\n".join(s for s in sections if s)

    # Note: we DO NOT echo the devotee's question into this system block
    # (see security note in the docstring). The question reaches the model
    # via its normal user-role message; the cheat-sheet + answer template
    # alone provide the recency lock at the end of the system stack.
    parts = [_HEADER, "", body, "", _FOOTER]
    return "\n".join(parts)


__all__ = ["build_full_chart_context"]

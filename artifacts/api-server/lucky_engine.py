"""
Cosmic Lens — Daily Personalised "Aaj Ka Shubh Ank" + "Aaj Ka Shubh Rang"

NO fake fallbacks. Requires:
  • birth_data.day  (mool ank source — birth date-of-month)
  • kundli.nakshatra (janma nakshatra name) — Moon's nakshatra at birth
  • date_iso (target date)
  • today_moon_lon, today_sun_lon (sidereal degrees) — for today's nakshatra +
    tithi + tara

Output:
  {
    "shubh_ank": int 1-9,
    "shubh_rang_name": str,            # Hinglish color name
    "shubh_rang_hex":  str,            # hex code for swatch
    "mool_ank":        int,            # permanent (numerology Mulank)
    "reasoning_hinglish": str,         # 1-line user-facing explanation
    "tara":              str,          # Hinglish tara name (Mitra/Vipat etc.)
    "tara_idx":          int,
    "today_nak":         str,          # Hinglish nakshatra name
    "tithi_idx":         int,          # 0-29 (1-30 in classical)
    "weekday_idx":       int           # 0=Mon .. 6=Sun
  }
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional

from energy_engine import NAKSHATRAS, TARA_NAMES
from vedic.numerology.phase_s import (
    NUMBER_FRIENDS, NUMBER_ENEMIES, PLANET_BY_NUMBER, _root,
)

# ─── Hinglish color palette ──────────────────────────────────────────────────
# Each planet has a primary "shubh rang" — the colour to wear / surround
# yourself with on a day governed by that planet's energy (or to invoke its
# blessing when its support is needed).
PLANET_COLOR: Dict[str, Dict[str, str]] = {
    "Sun":     {"name": "Suneheri",       "hex": "#f59e0b"},   # amber gold
    "Moon":    {"name": "Safed",          "hex": "#f3f4f6"},   # off-white
    "Mars":    {"name": "Lal",            "hex": "#dc2626"},   # red
    "Mercury": {"name": "Hara",           "hex": "#16a34a"},   # green
    "Jupiter": {"name": "Pila",           "hex": "#facc15"},   # yellow
    "Venus":   {"name": "Gulabi",         "hex": "#ec4899"},   # pink
    "Saturn":  {"name": "Gehra Neela",    "hex": "#1e3a8a"},   # deep blue
    "Rahu":    {"name": "Dhuandhla",      "hex": "#6b7280"},   # smoky grey
    "Ketu":    {"name": "Bhura",          "hex": "#92400e"},   # brown
}

# Weekday → ruling planet (Mon=0 .. Sun=6, ISO weekday-1)
WEEKDAY_PLANET = ["Moon","Mars","Mercury","Jupiter","Venus","Saturn","Sun"]

# Hinglish nakshatra names for user-facing strings (we already have english
# in NAKSHATRAS — these are pronounceable Roman-Hinglish).
NAK_HINGLISH = NAKSHATRAS  # the english spellings are already used in app UI

# Hinglish tara labels (Janma..Ati Mitra) — match TARA_NAMES order.
TARA_HINGLISH = TARA_NAMES

# Tara classification — favourable vs inauspicious
TARA_FAVOURABLE_IDX = {1, 3, 5, 7, 8}   # Sampat, Kshema, Sadhana, Mitra, Ati Mitra
TARA_INAUSPICIOUS_IDX = {0, 2, 4, 6}    # Janma, Vipat, Pratyak, Naidhana


def _tithi_idx(moon_lon: float, sun_lon: float) -> int:
    """Tithi index 0-29 from moon-sun longitude difference."""
    diff = (moon_lon - sun_lon) % 360.0
    return int(diff // 12.0) % 30


def _today_nak_idx(moon_lon: float) -> int:
    return int(moon_lon // (360.0 / 27.0)) % 27


def _birth_nak_idx(kundli: Dict[str, Any]) -> int:
    """Resolve janma nakshatra from saved kundli. -1 if not found."""
    nak_name = kundli.get("nakshatra")
    if not nak_name and isinstance(kundli.get("chart_data"), dict):
        nak_name = kundli["chart_data"].get("nakshatra")
    if isinstance(nak_name, str) and nak_name in NAKSHATRAS:
        return NAKSHATRAS.index(nak_name)
    # Fallback: derive from Moon's longitude in saved planets
    planets = kundli.get("planets") or (kundli.get("chart_data") or {}).get("planets") or []
    for p in planets:
        if isinstance(p, dict) and (p.get("name") == "Moon"):
            lon = p.get("lon") or p.get("longitude")
            if isinstance(lon, (int, float)):
                return int(float(lon) // (360.0 / 27.0)) % 27
    return -1


def _mool_ank_from_birth(*sources: Dict[str, Any]) -> Optional[int]:
    """Mool ank (Mulank) = digital root of birth-day (1..31 → 1..9).

    Accepts any number of dict sources (e.g. profile.birth_data, kundli) and
    returns the first valid mool ank found.
    """
    DATE_FORMATS = (
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y",
        "%d %b %Y", "%d %B %Y",          # "15 Jan 1990"
        "%b %d %Y", "%B %d %Y",
    )
    for src in sources:
        if not isinstance(src, dict):
            continue
        day = src.get("day")
        if day is None:
            for key in ("dob", "birth_date", "date"):
                v = src.get(key)
                if isinstance(v, str):
                    for fmt in DATE_FORMATS:
                        try:
                            day = datetime.strptime(v.strip(), fmt).day
                            break
                        except Exception:
                            continue
                    if day is not None:
                        break
        try:
            d = int(day)
            if 1 <= d <= 31:
                return _root(d)
        except (TypeError, ValueError):
            continue
    return None


def compute_daily_lucky(
    birth_data: Dict[str, Any],
    kundli: Dict[str, Any],
    date_iso: str,
    moon_lon: float,
    sun_lon: float,
) -> Dict[str, Any]:
    """
    Returns {ok: True, ...} on success or {ok: False, error, message} on
    missing data. NEVER returns fake/placeholder values.
    """
    # ── 1. Mool ank (permanent) ──────────────────────────────────────────
    # Fall back to kundli's own dob field if profile birth_data is missing.
    mool_ank = _mool_ank_from_birth(birth_data, kundli)
    if mool_ank is None:
        return {"ok": False,
                "error": "no_birth_day",
                "message": "Birth date missing — kundli mein janam ki tareekh nahi mili."}

    # ── 2. Janma nakshatra (from saved kundli) ───────────────────────────
    birth_nak = _birth_nak_idx(kundli)
    if birth_nak < 0:
        return {"ok": False,
                "error": "no_birth_nakshatra",
                "message": "Janam ka nakshatra nahi mila — kundli regenerate karein."}

    # ── 3. Date-driven inputs ────────────────────────────────────────────
    try:
        d = datetime.strptime(date_iso, "%Y-%m-%d")
    except Exception:
        return {"ok": False,
                "error": "bad_date",
                "message": "Date format galat hai (YYYY-MM-DD chahiye)."}

    weekday_idx = d.weekday()                          # 0=Mon..6=Sun
    today_nak   = _today_nak_idx(moon_lon)             # 0..26
    tithi_idx   = _tithi_idx(moon_lon, sun_lon)        # 0..29
    tara_idx    = (today_nak - birth_nak) % 9          # 0..8

    # ── 4. Lucky number — pick from mool_ank's friends, seeded by today ─
    friends = NUMBER_FRIENDS.get(mool_ank, [mool_ank])[:]
    enemies = set(NUMBER_ENEMIES.get(mool_ank, []))
    # Always exclude enemies (defensive — not in stock friends list either)
    friends = [n for n in friends if n not in enemies] or [mool_ank]

    seed = (mool_ank + today_nak + tithi_idx + weekday_idx + tara_idx)

    if tara_idx in TARA_INAUSPICIOUS_IDX:
        # Inauspicious tara → prefer a friend that's NOT mool_ank itself
        # (don't double-down on a stressed natal energy).
        non_self = [n for n in friends if n != mool_ank]
        pool = non_self or friends
    else:
        pool = friends
    shubh_ank = pool[seed % len(pool)]

    # ── 5. Lucky color ──────────────────────────────────────────────────
    if tara_idx in TARA_FAVOURABLE_IDX:
        # Favourable day → wear the day-lord's color to amplify
        rang_planet = WEEKDAY_PLANET[weekday_idx]
        rang_reason = "amplify"
    else:
        # Stressed day → wear your mool ank planet's color for protection
        rang_planet = PLANET_BY_NUMBER.get(mool_ank, WEEKDAY_PLANET[weekday_idx])
        rang_reason = "protect"
    color = PLANET_COLOR.get(rang_planet, PLANET_COLOR["Jupiter"])

    # ── 6. Hinglish reasoning (1 line) ──────────────────────────────────
    tara_name = TARA_HINGLISH[tara_idx]
    if tara_idx in TARA_FAVOURABLE_IDX:
        reasoning = (f"Aaj aapka nakshatra friendship '{tara_name}' hai — "
                     f"shubh ank {shubh_ank} aur {color['name']} rang aaj ki "
                     f"energy ke saath align hai.")
    else:
        reasoning = (f"Aaj nakshatra friendship '{tara_name}' hai — thoda "
                     f"sambhal ke. Shubh ank {shubh_ank} aur protective "
                     f"{color['name']} rang aapko balance dega.")

    return {
        "ok": True,
        "shubh_ank":          shubh_ank,
        "shubh_rang_name":    color["name"],
        "shubh_rang_hex":     color["hex"],
        "shubh_rang_intent":  rang_reason,         # "amplify" | "protect"
        "mool_ank":           mool_ank,
        "reasoning_hinglish": reasoning,
        "tara":               tara_name,
        "tara_idx":           tara_idx,
        "today_nakshatra":    NAK_HINGLISH[today_nak],
        "today_nak_idx":      today_nak,
        "tithi_idx":          tithi_idx,
        "weekday_idx":        weekday_idx,
        "date":               date_iso,
    }

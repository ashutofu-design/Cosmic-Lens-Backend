"""
transits.py
───────────
Current planetary transits over the natal chart.

Focus: slow-moving planets (Saturn, Jupiter, Rahu, Ketu) — these drive the
big-picture timing questions ("kab milega job", "shaadi kab", "Sade-Sati kab
khatam"). Fast planets (Sun, Mars, Mercury, Venus, Moon) change houses every
few days/weeks and are less useful for the AI to cite.

Key signals computed:
  • Sade-Sati / Dhaiya phase (Saturn vs natal Moon)
  • Saturn's house from natal Lagna  (heavy/discipline themes)
  • Jupiter's house from natal Lagna (expansion/protection themes)
  • Rahu's house from natal Lagna    (entanglement/foreign themes)
  • Saturn return window (~29.5 yr)  — once-a-life major shift
  • Jupiter return window (~12 yr)    — recurring growth opening
  • Jupiter aspect on natal Lagna/5/9/11 (lucky-window flag)

Public API
──────────
    compute_transits(natal_lagna_sign_idx, natal_moon_sign_idx,
                     dob: datetime|None=None,
                     when: datetime|None=None) -> dict

    format_transit_summary(t: dict) -> str
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Any

try:
    import swisseph as swe  # type: ignore
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    _FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    _HAS_SWE = True
except Exception:  # pragma: no cover
    _HAS_SWE = False
    swe = None  # type: ignore
    _FLAGS = 0

_SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
               "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


def _lon(planet_id: int, when: datetime) -> float | None:
    if not _HAS_SWE:
        return None
    try:
        jd = swe.julday(when.year, when.month, when.day,
                        when.hour + when.minute / 60.0)
        pos, _ = swe.calc_ut(jd, planet_id, _FLAGS)
        return float(pos[0]) % 360.0
    except Exception:
        return None


def _sign(lon: float) -> int:
    return int(lon / 30.0) % 12


def _house_from(target_sign: int, ref_sign: int) -> int:
    return ((target_sign - ref_sign) % 12) + 1


def compute_transits(natal_lagna_sign_idx: Any,
                     natal_moon_sign_idx: Any,
                     dob: Optional[datetime] = None,
                     when: Optional[datetime] = None) -> dict[str, Any]:
    """
    Returns {} if swisseph unavailable or natal indices missing.
    `when` defaults to now (UTC).
    """
    if not _HAS_SWE:
        return {}
    try:
        lagna_sign = int(natal_lagna_sign_idx) % 12
    except (TypeError, ValueError):
        return {}
    try:
        moon_sign = int(natal_moon_sign_idx) % 12
    except (TypeError, ValueError):
        moon_sign = None
    when = when or datetime.utcnow()

    out: dict[str, Any] = {"as_of": when.strftime("%Y-%m-%d")}

    # Current sidereal positions
    bodies = {
        "Saturn":  swe.SATURN,
        "Jupiter": swe.JUPITER,
        "Rahu":    swe.MEAN_NODE,
    }
    sigs: dict[str, int] = {}
    for nm, pid in bodies.items():
        lon = _lon(pid, when)
        if lon is None:
            continue
        sigs[nm] = _sign(lon)
    if not sigs:
        return {}

    # Ketu = opposite of Rahu
    if "Rahu" in sigs:
        sigs["Ketu"] = (sigs["Rahu"] + 6) % 12

    # House from natal Lagna
    out["transit_houses"] = {
        nm: {
            "sign":  _SIGN_NAMES[s],
            "house_from_lagna": _house_from(s, lagna_sign),
        }
        for nm, s in sigs.items()
    }

    # Sade-Sati / Dhaiya (Saturn vs natal Moon)
    if moon_sign is not None and "Saturn" in sigs:
        sat_h_from_moon = _house_from(sigs["Saturn"], moon_sign)
        if   sat_h_from_moon == 12: phase = "Sade-Sati: First phase (12th from Moon — anxieties, change)"
        elif sat_h_from_moon == 1:  phase = "Sade-Sati: Peak phase (over Moon — emotional weight, identity shift)"
        elif sat_h_from_moon == 2:  phase = "Sade-Sati: Last phase (2nd from Moon — finance/family pressure)"
        elif sat_h_from_moon == 4:  phase = "Dhaiya (Ardha-Ashtama): 4th from Moon — home/peace disturbance ~2.5 yrs"
        elif sat_h_from_moon == 8:  phase = "Dhaiya (Ashtama): 8th from Moon — transformation/risk ~2.5 yrs"
        else:                       phase = f"No Sade-Sati / Dhaiya (Saturn is {sat_h_from_moon}H from Moon — clear period)"
        out["sade_sati_phase"] = phase

    # Jupiter aspect on key houses (5/7/9 from Jupiter's current house)
    if "Jupiter" in sigs:
        j_house = _house_from(sigs["Jupiter"], lagna_sign)
        # Jupiter aspects 5th, 7th, 9th from itself — translate to lagna houses
        j_aspects = sorted({((j_house - 1 + off - 1) % 12) + 1 for off in (5, 7, 9)})
        out["jupiter_house"] = j_house
        out["jupiter_aspects_houses"] = j_aspects
        lucky = [h for h in j_aspects if h in (1, 5, 9, 10, 11)]
        if lucky:
            out["jupiter_lucky_flag"] = (
                f"Transit Jupiter aspects natal H{lucky} — favourable window for "
                "growth/decisions tied to that house."
            )

    # Saturn over natal 8th / 12th — caution flag
    if "Saturn" in sigs:
        s_house = _house_from(sigs["Saturn"], lagna_sign)
        out["saturn_house"] = s_house
        if s_house in (8, 12):
            out["saturn_caution_flag"] = (
                f"Transit Saturn in natal H{s_house} — restrictive period, "
                "avoid major risk-taking; focus on consolidation."
            )

    # Rahu over natal 1st / 7th / 10th — disruptive ambition theme
    if "Rahu" in sigs:
        r_house = _house_from(sigs["Rahu"], lagna_sign)
        out["rahu_house"] = r_house
        if r_house in (1, 7, 10):
            out["rahu_theme_flag"] = (
                f"Transit Rahu in natal H{r_house} — sudden shifts/ambition surge "
                "in that life-area; verify decisions twice."
            )

    # Saturn / Jupiter return windows (rough age-based)
    if dob:
        try:
            age = (when - dob).days / 365.25
            if 28.5 <= age <= 30.5:
                out["saturn_return"] = (
                    f"~Saturn Return (age {age:.1f}) — once-in-29-yr structural "
                    "reset of career/life-direction."
                )
            elif 58.0 <= age <= 60.0:
                out["saturn_return"] = (
                    f"~2nd Saturn Return (age {age:.1f}) — legacy/retirement "
                    "phase recalibration."
                )
            jup_cycle = age % 12
            if 11.5 <= jup_cycle or jup_cycle <= 0.5:
                out["jupiter_return"] = (
                    f"~Jupiter Return window (age {age:.1f}) — fresh 12-yr "
                    "expansion cycle opening."
                )
        except Exception:
            pass

    return out


def format_transit_summary(t: dict) -> str:
    if not t or "transit_houses" not in t:
        return "▸ TRANSITS: (unavailable)"
    lines = [f"▸ CURRENT TRANSITS (as of {t.get('as_of', 'today')}):"]
    for nm, info in t["transit_houses"].items():
        lines.append(f"   {nm:7s} — {info['sign']:11s} (H{info['house_from_lagna']} from natal Lagna)")
    if t.get("sade_sati_phase"):
        lines.append(f"   ▸ {t['sade_sati_phase']}")
    if t.get("jupiter_lucky_flag"):
        lines.append(f"   ▸ {t['jupiter_lucky_flag']}")
    if t.get("saturn_caution_flag"):
        lines.append(f"   ▸ {t['saturn_caution_flag']}")
    if t.get("rahu_theme_flag"):
        lines.append(f"   ▸ {t['rahu_theme_flag']}")
    if t.get("saturn_return"):
        lines.append(f"   ▸ {t['saturn_return']}")
    if t.get("jupiter_return"):
        lines.append(f"   ▸ {t['jupiter_return']}")
    return "\n".join(lines)

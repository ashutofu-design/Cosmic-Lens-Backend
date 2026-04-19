"""
Sprint 14 — Sthira Dasha + Niryana Shoola Dasha (Jaimini sign-dashas)
======================================================================
Two additional sign-based mahadasha systems from BPHS / Jaimini Sutras:

STHIRA DASHA (Fixed Dasha)
──────────────────────────
• Sign-based: 12 mahadashas, one per zodiac sign, starting from Lagna sign,
  proceeding in zodiacal (forward) order.
• Length per sign is FIXED by quality:
    Movable / Chara (Aries, Cancer, Libra, Capricorn)   → 7 years
    Fixed   / Sthira (Taurus, Leo, Scorpio, Aquarius)   → 8 years
    Dual    / Dvi-svabhava (Gem, Vir, Sag, Pis)         → 9 years
• Total span = 4×7 + 4×8 + 4×9 = 96 years.
• Used for general life-event timing, especially of a stable / structural
  nature (career stability, long-term commitments, dharma).

NIRYANA SHOOLA DASHA (Death / Life-direction Dasha)
────────────────────────────────────────────────────
• Sign-based: 12 mahadashas of 9 years each = 108 years total.
• Starts from the LAGNA sign, forward direction (mainstream BPHS variant).
• Each MD is sub-divided into 9-year ÷ 12 = 0.75-year (9 months) antardashas.
• Used principally for longevity/marana-karaka analysis and life-direction
  shifts. We expose it as an additional cross-check timing layer.

Both dashas yield {current_md, current_ad, sequence} the same way as
chara_dasha so they slot into the existing post-injector pattern.
"""
from __future__ import annotations
from typing import Any
from datetime import datetime, timedelta

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Sthira Dasha per-sign fixed lengths
STHIRA_LENGTHS = {
    "Aries": 7, "Cancer": 7, "Libra": 7, "Capricorn": 7,           # movable
    "Taurus": 8, "Leo": 8, "Scorpio": 8, "Aquarius": 8,            # fixed
    "Gemini": 9, "Virgo": 9, "Sagittarius": 9, "Pisces": 9,        # dual
}

NIRYANA_LENGTH = 9  # uniform 9 years per sign


def _sign_idx(s: Any) -> int | None:
    if isinstance(s, dict):
        s = s.get("sign") or s.get("name")
    try:
        return SIGNS.index(str(s).strip().capitalize())
    except (ValueError, AttributeError, TypeError):
        return None


def _to_dt(dob: Any) -> datetime | None:
    if isinstance(dob, datetime):
        return dob
    if isinstance(dob, str) and len(dob) >= 10:
        try:
            return datetime.strptime(dob[:10], "%Y-%m-%d")
        except Exception:
            return None
    if isinstance(dob, dict):
        if "date" in dob or "dob" in dob:
            return _to_dt(dob.get("date") or dob.get("dob"))
        if all(k in dob for k in ("day", "month", "year")):
            try:
                return datetime(
                    int(dob["year"]), int(dob["month"]), int(dob["day"]),
                    int(dob.get("hour") or 0), int(dob.get("minute") or 0),
                )
            except Exception:
                return None
    return None


def _build_sequence(start_idx: int, lengths_by_sign: dict | int,
                    forward: bool = True) -> list[dict]:
    seq = []
    for i in range(12):
        idx = (start_idx + i) % 12 if forward else (start_idx - i) % 12
        sign = SIGNS[idx]
        if isinstance(lengths_by_sign, dict):
            length = lengths_by_sign.get(sign, 9)
        else:
            length = int(lengths_by_sign)
        seq.append({"sign": sign, "sign_idx": idx, "length_years": length})
    return seq


def _annotate_with_dates(seq: list[dict], dob_dt: datetime) -> list[dict]:
    cursor = dob_dt
    for md in seq:
        start = cursor
        end = cursor + timedelta(days=md["length_years"] * 365.25)
        md["start"] = start.strftime("%Y-%m-%d")
        md["end"]   = end.strftime("%Y-%m-%d")
        md["start_dt"] = start
        md["end_dt"]   = end
        cursor = end
    return seq


def _find_current_md(seq: list[dict], today: datetime) -> dict | None:
    for md in seq:
        if md["start_dt"] <= today < md["end_dt"]:
            elapsed = (today - md["start_dt"]).days / 365.25
            md["years_elapsed"] = round(elapsed, 2)
            return md
    return None


def _build_antardashas(md: dict, total_subs: int = 12,
                       forward: bool = True) -> list[dict]:
    """12 antardashas per MD (signs starting from MD sign in MD direction)."""
    sub_len_years = md["length_years"] / total_subs
    sub_len_days = sub_len_years * 365.25
    cursor = md["start_dt"]
    ads = []
    for i in range(total_subs):
        idx = ((md["sign_idx"] + i) % 12 if forward
               else (md["sign_idx"] - i) % 12)
        start = cursor
        end = cursor + timedelta(days=sub_len_days)
        ads.append({
            "sign":    SIGNS[idx],
            "start":   start.strftime("%Y-%m-%d"),
            "end":     end.strftime("%Y-%m-%d"),
            "start_dt": start,
            "end_dt":  end,
        })
        cursor = end
    return ads


def _find_current_ad(ads: list[dict], today: datetime) -> dict | None:
    for ad in ads:
        if ad["start_dt"] <= today < ad["end_dt"]:
            return {"sign": ad["sign"], "start": ad["start"], "end": ad["end"]}
    return None


# ─── STHIRA DASHA ────────────────────────────────────────────────────────────
def compute_sthira_dasha(lagna_sign: Any, dob: Any,
                         today: datetime | None = None) -> dict[str, Any]:
    lagna_idx = _sign_idx(lagna_sign)
    dob_dt = _to_dt(dob)
    if lagna_idx is None or dob_dt is None:
        return {}
    today = today or datetime.utcnow()

    seq = _build_sequence(lagna_idx, STHIRA_LENGTHS, forward=True)
    seq = _annotate_with_dates(seq, dob_dt)
    md = _find_current_md(seq, today)
    if not md:
        return {"sequence": seq, "current_md": None, "current_ad": None}
    ads = _build_antardashas(md, total_subs=12, forward=True)
    ad = _find_current_ad(ads, today)
    return {
        "system":       "Sthira Dasha",
        "total_span":   96,
        "starting_sign": SIGNS[lagna_idx],
        "current_md":   {k: md[k] for k in
                          ("sign", "length_years", "start", "end",
                           "years_elapsed")},
        "current_ad":   ad,
    }


# ─── NIRYANA SHOOLA DASHA ────────────────────────────────────────────────────
def compute_niryana_shoola(lagna_sign: Any, dob: Any,
                           today: datetime | None = None) -> dict[str, Any]:
    lagna_idx = _sign_idx(lagna_sign)
    dob_dt = _to_dt(dob)
    if lagna_idx is None or dob_dt is None:
        return {}
    today = today or datetime.utcnow()

    seq = _build_sequence(lagna_idx, NIRYANA_LENGTH, forward=True)
    seq = _annotate_with_dates(seq, dob_dt)
    md = _find_current_md(seq, today)
    if not md:
        return {"sequence": seq, "current_md": None, "current_ad": None}
    ads = _build_antardashas(md, total_subs=12, forward=True)
    ad = _find_current_ad(ads, today)
    return {
        "system":        "Niryana Shoola Dasha",
        "total_span":    108,
        "starting_sign": SIGNS[lagna_idx],
        "current_md":    {k: md[k] for k in
                           ("sign", "length_years", "start", "end",
                            "years_elapsed")},
        "current_ad":    ad,
    }


# ─── FORMATTERS ──────────────────────────────────────────────────────────────
def format_sthira_summary(s: dict) -> str:
    if not s or not s.get("current_md"):
        return ""
    md = s["current_md"]; ad = s.get("current_ad") or {}
    ad_part = (f", AD {ad['sign']} ({ad['start']}→{ad['end']})"
               if ad else "")
    return ("▸ STHIRA DASHA (Jaimini fixed sign-dasha — life-stability layer):\n"
            f"   ▸ Current MD: {md['sign']} ({md['length_years']} yrs, "
            f"{md['start']}→{md['end']}, "
            f"{md.get('years_elapsed','?')}/{md['length_years']} elapsed)"
            f"{ad_part}")


def format_niryana_summary(s: dict) -> str:
    if not s or not s.get("current_md"):
        return ""
    md = s["current_md"]; ad = s.get("current_ad") or {}
    ad_part = (f", AD {ad['sign']} ({ad['start']}→{ad['end']})"
               if ad else "")
    return ("▸ NIRYANA SHOOLA DASHA (Jaimini longevity / life-direction "
            "dasha — 9 yrs/sign):\n"
            f"   ▸ Current MD: {md['sign']} (9 yrs, "
            f"{md['start']}→{md['end']}, "
            f"{md.get('years_elapsed','?')}/9 elapsed){ad_part}")

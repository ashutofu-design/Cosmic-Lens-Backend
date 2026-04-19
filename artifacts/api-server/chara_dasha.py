"""
chara_dasha.py
──────────────
Jaimini Chara Dasha — Sprint 8

Chara Dasha is a SIGN-based mahadasha system (12 mahadashas, one per sign).
Unlike Vimshottari (which is planet-based and starts from natal Moon's
nakshatra), Chara Dasha length depends on where the SIGN-LORD sits relative
to its own sign — counted forward in zodiacal order.

═══════════════════════════════════════════════════════════════════════════
ALGORITHM (Jaimini Sutras + Madhura Krishnamurthy Sastry's commentary):

1. STARTING SIGN
   • If Lagna is in an ODD sign  (Aries/Gem/Leo/Lib/Sag/Aqu) → start with Lagna
   • If Lagna is in an EVEN sign (Tau/Can/Vir/Sco/Cap/Pis) → start with the
     7th from Lagna

2. SEQUENCE DIRECTION
   • Odd-sign-Lagna  → ZODIACAL (forward: Aries→Taurus→Gemini…)
   • Even-sign-Lagna → REVERSE   (backward: Pisces→Aquarius→Capricorn…)

3. LENGTH OF EACH MAHADASHA (in years)
   For each sign in the sequence, find its lord's CURRENT sign placement,
   then count from the dashasign to the lord's sign in the sequence
   direction (i.e. forward for odd-Lagna, reverse for even-Lagna).

       count = position of lord's sign − position of dasha sign  (1-12)

   Then: length = count − 1
       • EXCEPTIONS:
         - If count == 1 (lord is IN its own sign) → length = 12 years
         - If count == 12 (lord is in the 12th from its sign in the
           direction) → length = 11 years
         - If lord is in EXALTATION sign         → length = (count) i.e. +1
         - If lord is in DEBILITATION sign       → length = (count − 2) i.e. −1
         - Minimum length = 1 year, maximum = 12

   For dual lordships (Scorpio = Mars/Ketu, Aquarius = Saturn/Rahu) the
   stronger of the two lords is used; we pick the lord placed CLOSER to
   its sign (smaller count).

4. ANTARDASHA (sub-period) inside each MD
   The 12 antardashas inside a MD are the 12 signs starting FROM the MD
   sign itself, each lasting (MD-length / 12) years. Sequence direction
   matches the main MD sequence direction.

═══════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Optional

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Primary sign-lord (for Scorpio we evaluate Mars+Ketu; Aquarius Saturn+Rahu)
SIGN_LORD = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]
DUAL_LORDS = {7: ("Mars", "Ketu"), 10: ("Saturn", "Rahu")}  # Scorpio, Aquarius

# Exaltation / debilitation sign indices
EXALT = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3,
         "Venus": 11, "Saturn": 6, "Rahu": 1, "Ketu": 7}
DEBIL = {"Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11, "Jupiter": 9,
         "Venus": 5, "Saturn": 0, "Rahu": 7, "Ketu": 1}

ODD_SIGNS = {0, 2, 4, 6, 8, 10}  # Aries, Gemini, Leo, Libra, Sag, Aquarius


# ── helpers ──────────────────────────────────────────────────────────────────

def _sign_idx(name: Any) -> Optional[int]:
    if not isinstance(name, str):
        return None
    try:
        return SIGNS.index(name.strip().capitalize())
    except ValueError:
        return None


def _planet_sign_map(planets: list) -> dict[str, int]:
    out: dict[str, int] = {}
    if not isinstance(planets, list):
        return out
    for p in planets:
        if not isinstance(p, dict):
            continue
        n = p.get("name")
        s = _sign_idx(p.get("sign"))
        if isinstance(n, str) and s is not None:
            out[n] = s
    return out


def _direction_count(from_sign: int, to_sign: int, forward: bool) -> int:
    """Sign-count from `from_sign` to `to_sign` in chosen direction (1-12, inclusive)."""
    if forward:
        diff = (to_sign - from_sign) % 12
    else:
        diff = (from_sign - to_sign) % 12
    return diff + 1  # inclusive count


def _md_length_for_sign(sign_idx: int, planet_signs: dict[str, int],
                        forward: bool) -> tuple[int, str, int]:
    """
    Returns (length_in_years, effective_lord, effective_lord_sign_idx).
    Picks the closer of the two lords for dual-lord signs.
    """
    candidates = list(DUAL_LORDS.get(sign_idx, (SIGN_LORD[sign_idx],)))
    best: Optional[tuple[int, str, int, int]] = None  # (count, lord, lord_sign, length)
    for lord in candidates:
        ls = planet_signs.get(lord)
        if ls is None:
            continue
        count = _direction_count(sign_idx, ls, forward)
        # base length
        if count == 1:
            length = 12
        elif count == 12:
            length = 11
        else:
            length = count - 1
        # exalt / debil adjustments
        if EXALT.get(lord) == ls:
            length += 1
        elif DEBIL.get(lord) == ls:
            length -= 1
        length = max(1, min(12, length))
        # pick smaller count = "closer" lord wins
        if best is None or count < best[0]:
            best = (count, lord, ls, length)
    if best is None:
        return (7, SIGN_LORD[sign_idx], sign_idx)  # safe default
    return (best[3], best[1], best[2])


# ── main computation ────────────────────────────────────────────────────────

def compute_chara_dasha(planets: list, lagna_sign: Any,
                        dob: Any, today: Optional[datetime] = None) -> dict[str, Any]:
    """
    Returns {
      'sequence_direction': 'forward' | 'reverse',
      'starting_sign':       'Aries',
      'mahadashas': [
         { 'sign':'Aries','lord':'Mars','length_years':7,
           'start':'1990-01-15','end':'1997-01-14' }, ...
      ],
      'current_md':  {sign, lord, start, end, years_elapsed},
      'current_ad':  {sign, lord, start, end},
    }
    Returns {} if input insufficient.
    """
    lagna_idx = _sign_idx(lagna_sign)
    if lagna_idx is None:
        return {}
    psigns = _planet_sign_map(planets)
    if not psigns:
        return {}
    # parse DOB
    dob_dt: Optional[datetime] = None
    if isinstance(dob, datetime):
        dob_dt = dob
    elif isinstance(dob, str) and len(dob) >= 10:
        try:
            dob_dt = datetime.strptime(dob[:10], "%Y-%m-%d")
        except Exception:
            try:
                dob_dt = datetime.strptime(dob[:10], "%d-%m-%Y")
            except Exception:
                pass
    elif isinstance(dob, dict):
        # birth dict may carry day/month/year
        try:
            dob_dt = datetime(int(dob["year"]), int(dob["month"]), int(dob["day"]))
        except Exception:
            pass
    if dob_dt is None:
        return {}
    if today is None:
        today = datetime.utcnow()

    # Step 1+2: starting sign + direction
    if lagna_idx in ODD_SIGNS:
        start_sign = lagna_idx
        forward    = True
    else:
        start_sign = (lagna_idx + 6) % 12   # 7th from Lagna
        forward    = False

    # Step 3: compute 12 MDs
    mds: list[dict] = []
    cur = dob_dt
    sign = start_sign
    for _ in range(12):
        length, lord, _lord_sign = _md_length_for_sign(sign, psigns, forward)
        years = length
        end = cur + timedelta(days=int(years * 365.25))
        mds.append({
            "sign":         SIGNS[sign],
            "sign_idx":     sign,
            "lord":         lord,
            "length_years": years,
            "start":        cur.strftime("%Y-%m-%d"),
            "end":          end.strftime("%Y-%m-%d"),
            "_start_dt":    cur,
            "_end_dt":      end,
        })
        cur = end
        sign = (sign + 1) % 12 if forward else (sign - 1) % 12

    # Step 4: locate the CURRENT MD by today
    current_md = None
    current_ad = None
    for md in mds:
        if md["_start_dt"] <= today < md["_end_dt"]:
            current_md = md
            # antardashas: 12 sub-periods inside this MD, same direction
            ad_len_days = (md["_end_dt"] - md["_start_dt"]).total_seconds() / 86400.0 / 12.0
            ad_sign = md["sign_idx"]
            ad_cur  = md["_start_dt"]
            for _ in range(12):
                ad_end = ad_cur + timedelta(days=ad_len_days)
                if ad_cur <= today < ad_end:
                    ad_lord_choices = list(
                        DUAL_LORDS.get(ad_sign, (SIGN_LORD[ad_sign],))
                    )
                    current_ad = {
                        "sign":  SIGNS[ad_sign],
                        "lord":  ad_lord_choices[0],
                        "start": ad_cur.strftime("%Y-%m-%d"),
                        "end":   ad_end.strftime("%Y-%m-%d"),
                    }
                    break
                ad_cur = ad_end
                ad_sign = (ad_sign + 1) % 12 if forward else (ad_sign - 1) % 12
            break

    # strip internal datetime helpers from public output
    pub_mds = [{k: v for k, v in m.items() if not k.startswith("_")} for m in mds]
    pub_curr_md = (
        {k: v for k, v in current_md.items() if not k.startswith("_")}
        if current_md else None
    )
    if pub_curr_md and current_md:
        elapsed_days = (today - current_md["_start_dt"]).total_seconds() / 86400.0
        pub_curr_md["years_elapsed"] = round(elapsed_days / 365.25, 2)

    return {
        "sequence_direction": "forward" if forward else "reverse",
        "starting_sign":      SIGNS[start_sign],
        "lagna_sign":         SIGNS[lagna_idx],
        "mahadashas":         pub_mds,
        "current_md":         pub_curr_md,
        "current_ad":         current_ad,
    }


# ── formatter for LOCKED FACTS ───────────────────────────────────────────────

def format_chara_dasha_summary(cd: dict) -> str:
    if not isinstance(cd, dict) or not cd.get("mahadashas"):
        return ""
    lines = ["▸ JAIMINI CHARA DASHA (sign-based mahadasha — alt timing system):"]
    lines.append(
        f"   ▸ Sequence: {cd['sequence_direction'].upper()} from "
        f"{cd['starting_sign']} (Lagna in {cd['lagna_sign']})"
    )
    cm = cd.get("current_md")
    ca = cd.get("current_ad")
    if cm:
        lines.append(
            f"   ▸ CURRENT Chara MD: {cm['sign']} (lord {cm['lord']}) — "
            f"{cm['start']} → {cm['end']}  "
            f"[{cm.get('years_elapsed','?')}/{cm['length_years']} years elapsed]"
        )
    if ca:
        lines.append(
            f"   ▸ CURRENT Chara AD: {ca['sign']} (lord {ca['lord']}) — "
            f"{ca['start']} → {ca['end']}"
        )
    # Show the 12-MD timeline compactly
    lines.append("   ▸ Full 12-MD timeline:")
    for m in cd["mahadashas"]:
        marker = "  ★" if (cm and m["sign"] == cm["sign"] and m["start"] == cm["start"]) else "   "
        lines.append(
            f"      {marker} {m['sign']:11s} (lord {m['lord']:7s}) "
            f"{m['start']} → {m['end']}  ({m['length_years']}y)"
        )
    lines.append(
        "   Read: Chara Dasha runs PARALLEL to Vimshottari. When Vimshottari "
        "and Chara point to the SAME life-area as active, that timing is "
        "high-confidence. Disagreement = mixed signals, allow flex window."
    )
    return "\n".join(lines)

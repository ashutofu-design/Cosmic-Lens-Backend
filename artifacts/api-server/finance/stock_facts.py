"""Phase 2.10.7 — STOCK / FINANCE deterministic fact pack.

Y2 architecture core: ZERO LLM inference here. Every field is a
direct, repeatable computation from the kundli dict. Same chart +
same dasha pointer = same facts forever.

Public:
  compute_stock_facts(kundli) -> dict
  STOCK_SECTOR_MAP -> dict[str, list[str]]
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# ── Sign / lord / dignity tables (mirrors marriage_timing) ──────────
_SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
               "Libra", "Scorpio", "Sagittarius", "Capricorn",
               "Aquarius", "Pisces"]
_SIGN_IDX: Dict[str, int] = {s: i for i, s in enumerate(_SIGN_NAMES)}

_SIGN_LORDS: Dict[int, str] = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun",
    5: "Mercury", 6: "Venus", 7: "Mars", 8: "Jupiter",
    9: "Saturn", 10: "Saturn", 11: "Jupiter",
}

# Own / Exalted / Debilitated signs (BPHS standard)
_OWN: Dict[str, set] = {
    "Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
    "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10},
}
_EXALTED: Dict[str, int] = {
    "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
    "Jupiter": 3, "Venus": 11, "Saturn": 6,
}
_DEBILITATED: Dict[str, int] = {
    "Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
    "Jupiter": 9, "Venus": 5, "Saturn": 0,
}
# Friend tables (Parashara natural)
_FRIENDS: Dict[str, set] = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
_ENEMIES: Dict[str, set] = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}

# Planet → sector mapping (BPHS-derived, modern overlay)
STOCK_SECTOR_MAP: Dict[str, List[str]] = {
    "Sun":     ["PSU", "Government", "Gold", "Power", "Pharma (govt)"],
    "Moon":    ["FMCG", "Dairy", "Beverages", "Hospitality", "Public-sentiment stocks"],
    "Mars":    ["Real Estate", "Metals", "Defence", "Infrastructure", "Construction"],
    "Mercury": ["IT", "Telecom", "Media", "Education", "Quick-trade / day-trading"],
    "Jupiter": ["Banking", "Finance", "Insurance", "Education", "Long-term mutual funds"],
    "Venus":   ["FMCG (luxury)", "Auto", "Beauty", "Entertainment", "Hospitality"],
    "Saturn":  ["Mining", "Oil", "Iron/Steel", "Long-hold blue-chip", "Dividend stocks"],
    "Rahu":    ["Crypto", "Foreign / NRI", "F&O / derivatives", "Tech speculation"],
    "Ketu":    ["Pharma (research)", "Spiritual / wellness", "Healing"],
}

# Money houses (per BPHS for stock/wealth)
_MONEY_HOUSES = (2, 5, 8, 11)
_DUSTHANA_HOUSES = (6, 8, 12)

# ── Helpers ─────────────────────────────────────────────────────────
def _planet_by_name(planets: List[dict], name: str) -> Optional[dict]:
    for p in planets or []:
        if p.get("name") == name:
            return p
    return None


def _sign_idx(sign_name: str) -> Optional[int]:
    return _SIGN_IDX.get(sign_name)


def _planet_dignity(planets: List[dict], planet: str) -> str:
    """Returns: exalted | own | friend | neutral | enemy | debilitated."""
    p = _planet_by_name(planets, planet)
    if not p:
        return "unknown"
    si = _sign_idx(p.get("sign", ""))
    if si is None:
        return "unknown"
    if _EXALTED.get(planet) == si:
        return "exalted"
    if _DEBILITATED.get(planet) == si:
        return "debilitated"
    if si in _OWN.get(planet, set()):
        return "own"
    sign_lord = _SIGN_LORDS.get(si, "")
    if sign_lord in _FRIENDS.get(planet, set()):
        return "friend"
    if sign_lord in _ENEMIES.get(planet, set()):
        return "enemy"
    return "neutral"


_DIGNITY_SCORE = {
    "exalted": 3, "own": 2, "friend": 1, "neutral": 0,
    "enemy": -1, "debilitated": -2, "unknown": 0,
}


def _house_lord(asc_si: int, house_num: int) -> str:
    """Lord of Nth house from ascendant."""
    target_si = (asc_si + house_num - 1) % 12
    return _SIGN_LORDS.get(target_si, "")


def _planets_in_house(planets: List[dict], house_num: int) -> List[str]:
    return [p["name"] for p in (planets or [])
            if p.get("house") == house_num and p.get("name") != "Ascendant"]


def _is_combust(p: dict, sun_long: float) -> bool:
    """Combust if within 8.5° of Sun (planet-specific tighter, but
    8.5 is BPHS-safe default for non-Moon)."""
    if not p:
        return False
    if p.get("name") in ("Sun", "Rahu", "Ketu"):
        return False
    pl = p.get("longitude")
    if pl is None:
        return False
    diff = abs(float(pl) - float(sun_long))
    if diff > 180:
        diff = 360 - diff
    cap = 12 if p.get("name") == "Moon" else 8.5
    return diff <= cap


def _aspects(planet: str, planet_house: int, target_house: int) -> bool:
    """Planet aspects target_house (Vedic graha drishti).
    All planets aspect 7H. Mars: 4H, 8H. Jupiter: 5H, 9H. Saturn: 3H, 10H.
    Rahu/Ketu: 5H, 9H (popular school)."""
    if not planet_house or not target_house:
        return False
    diff = (target_house - planet_house) % 12
    if diff == 6:  # 7th aspect (universal)
        return True
    if planet == "Mars" and diff in (3, 7):  # 4th, 8th
        return True
    if planet in ("Jupiter", "Rahu", "Ketu") and diff in (4, 8):  # 5th, 9th
        return True
    if planet == "Saturn" and diff in (2, 9):  # 3rd, 10th
        return True
    return False


# ── Yoga detectors (deterministic) ──────────────────────────────────
def _detect_chandra_mangal(planets: List[dict]) -> bool:
    moon = _planet_by_name(planets, "Moon")
    mars = _planet_by_name(planets, "Mars")
    if not moon or not mars:
        return False
    return moon.get("house") == mars.get("house")


def _detect_dhana_yoga(planets: List[dict], asc_si: int) -> bool:
    """2L-11L conjunction OR mutual aspect OR exchange (parivartana)."""
    h2_lord = _house_lord(asc_si, 2)
    h11_lord = _house_lord(asc_si, 11)
    if not h2_lord or not h11_lord or h2_lord == h11_lord:
        return False
    p2 = _planet_by_name(planets, h2_lord)
    p11 = _planet_by_name(planets, h11_lord)
    if not p2 or not p11:
        return False
    if p2.get("house") == p11.get("house"):  # conjunction
        return True
    # Mutual aspect (any aspect both ways)
    if (_aspects(h2_lord, p2.get("house") or 0, p11.get("house") or 0)
            and _aspects(h11_lord, p11.get("house") or 0, p2.get("house") or 0)):
        return True
    # Parivartana: 2L in 11H AND 11L in 2H
    if p2.get("house") == 11 and p11.get("house") == 2:
        return True
    return False


def _detect_lakshmi_yoga(planets: List[dict], asc_si: int) -> bool:
    """Simplified: Venus in own/exalted house AND 9L strong."""
    venus = _planet_by_name(planets, "Venus")
    if not venus:
        return False
    venus_dignity = _planet_dignity(planets, "Venus")
    if venus_dignity not in ("exalted", "own"):
        return False
    h9_lord = _house_lord(asc_si, 9)
    h9_dignity = _planet_dignity(planets, h9_lord) if h9_lord else "unknown"
    return _DIGNITY_SCORE.get(h9_dignity, 0) >= 1


def _detect_vipreet_raja(planets: List[dict], asc_si: int) -> bool:
    """6/8/12 lords in 6/8/12 houses (mutual)."""
    for hn in _DUSTHANA_HOUSES:
        lord = _house_lord(asc_si, hn)
        if not lord:
            continue
        p = _planet_by_name(planets, lord)
        if p and p.get("house") in _DUSTHANA_HOUSES:
            return True
    return False


# ── Main fact pack ──────────────────────────────────────────────────
def compute_stock_facts(kundli: dict) -> Dict[str, Any]:
    """Deterministic stock/finance fact pack. ZERO LLM inference.

    Returns dict with: house_strengths, lord_states, karakas,
    yogas, dasha_link, afflictions, score, verdict, sub_flags.
    """
    if not isinstance(kundli, dict):
        return {"error": "no kundli"}

    planets: List[dict] = kundli.get("planets") or []
    if not planets:
        return {"error": "no planets in kundli"}

    asc_sign = kundli.get("ascendant", "")
    asc_si = _sign_idx(asc_sign)
    if asc_si is None:
        return {"error": f"unknown ascendant sign: {asc_sign}"}

    sun = _planet_by_name(planets, "Sun")
    sun_long = float(sun.get("longitude", 0)) if sun else 0.0

    # ── A. House lords (deterministic) ──────────────────────────────
    lord_states: Dict[str, dict] = {}
    for hn in (2, 5, 8, 11, 12, 6, 10):
        lord = _house_lord(asc_si, hn)
        p = _planet_by_name(planets, lord)
        ph = (p or {}).get("house") or 0
        lord_states[f"h{hn}"] = {
            "lord": lord,
            "lord_house": ph,
            "lord_sign": (p or {}).get("sign", ""),
            "lord_dignity": _planet_dignity(planets, lord) if lord else "unknown",
            "lord_retro": bool((p or {}).get("retrograde")),
            "lord_combust": _is_combust(p, sun_long) if p else False,
            "lord_in_dusthana": ph in _DUSTHANA_HOUSES,
        }

    # ── B. Karakas state (Jupiter / Venus / Mercury) ────────────────
    karakas: Dict[str, dict] = {}
    for k in ("Jupiter", "Venus", "Mercury", "Sun", "Moon", "Mars",
              "Saturn", "Rahu", "Ketu"):
        p = _planet_by_name(planets, k)
        if not p:
            continue
        karakas[k] = {
            "house": p.get("house"),
            "sign": p.get("sign"),
            "dignity": _planet_dignity(planets, k),
            "retro": bool(p.get("retrograde")),
            "combust": _is_combust(p, sun_long),
        }

    # ── C. House occupants ──────────────────────────────────────────
    house_occupants: Dict[int, List[str]] = {
        hn: _planets_in_house(planets, hn) for hn in range(1, 13)
    }

    # ── D. SAV (Sarvashtakavarga) — read if available, else N/A ─────
    # Some kundli pipelines populate kundli['ashtakavarga']['sav'].
    # If absent, we'll mark sav_unavailable=True and skip SAV-based scoring.
    sav: Dict[int, int] = {}
    av = kundli.get("ashtakavarga") or kundli.get("sarvashtakavarga") or {}
    if isinstance(av, dict):
        cand = (av.get("sav") or av.get("houseTotals")
                or av.get("sarvashtakavarga") or {})
        if isinstance(cand, dict):
            for k, v in cand.items():
                try:
                    sav[int(str(k).lstrip("h").lstrip("H"))] = int(v)
                except (ValueError, TypeError):
                    continue
        elif isinstance(cand, list) and len(cand) >= 12:
            for i, v in enumerate(cand):
                try:
                    sav[i + 1] = int(v)
                except (ValueError, TypeError):
                    continue
    sav_available = bool(sav)

    # ── E. Yogas (deterministic detectors) ──────────────────────────
    wealth_yogas: List[str] = []
    if _detect_chandra_mangal(planets):
        wealth_yogas.append("Chandra-Mangal")
    if _detect_dhana_yoga(planets, asc_si):
        wealth_yogas.append("Dhana")
    if _detect_lakshmi_yoga(planets, asc_si):
        wealth_yogas.append("Lakshmi")
    if _detect_vipreet_raja(planets, asc_si):
        wealth_yogas.append("Vipreet-Raja")

    missing_yogas = [y for y in ("Chandra-Mangal", "Dhana", "Lakshmi",
                                  "Vipreet-Raja") if y not in wealth_yogas]

    # ── F. Current dasha link to money houses ───────────────────────
    cd = kundli.get("currentDasha") or {}
    md_lord = cd.get("maha", "")
    ad_lord = cd.get("antar", "")
    pd_lord = cd.get("pratyantar", "")

    def _money_link(planet: str) -> Tuple[bool, List[str]]:
        if not planet:
            return False, []
        reasons = []
        # Is the planet a money-house lord?
        for hn in _MONEY_HOUSES:
            if _house_lord(asc_si, hn) == planet:
                reasons.append(f"H{hn} lord")
        # Is the planet placed in a money house?
        p = _planet_by_name(planets, planet)
        if p and p.get("house") in _MONEY_HOUSES:
            reasons.append(f"in H{p.get('house')}")
        return bool(reasons), reasons

    md_money_link, md_money_reasons = _money_link(md_lord)
    ad_money_link, ad_money_reasons = _money_link(ad_lord)
    pd_money_link, pd_money_reasons = _money_link(pd_lord)

    def _dusthana_link(planet: str) -> Tuple[bool, List[str]]:
        if not planet:
            return False, []
        reasons = []
        for hn in _DUSTHANA_HOUSES:
            if _house_lord(asc_si, hn) == planet:
                reasons.append(f"H{hn} lord")
        p = _planet_by_name(planets, planet)
        if p and p.get("house") in _DUSTHANA_HOUSES:
            reasons.append(f"in H{p.get('house')}")
        return bool(reasons), reasons

    md_bad_link, md_bad_reasons = _dusthana_link(md_lord)
    ad_bad_link, ad_bad_reasons = _dusthana_link(ad_lord)

    # ── G. Afflictions (deterministic checks) ───────────────────────
    afflictions: List[str] = []

    # Saturn or Rahu on H2
    h2_planets = house_occupants.get(2, [])
    if "Saturn" in h2_planets:
        afflictions.append("Saturn in H2 (slow wealth growth)")
    if "Rahu" in h2_planets:
        afflictions.append("Rahu in H2 (unconventional/foreign income, instability)")
    if "Ketu" in h2_planets:
        afflictions.append("Ketu in H2 (detachment from money matters)")

    # H8 lord in H2
    h8_lord = _house_lord(asc_si, 8)
    if h8_lord and (_planet_by_name(planets, h8_lord) or {}).get("house") == 2:
        afflictions.append(f"H8 lord ({h8_lord}) in H2 (sudden loss risk)")

    # 12L active in dasha
    h12_lord = _house_lord(asc_si, 12)
    if h12_lord and h12_lord in (md_lord, ad_lord):
        afflictions.append(f"H12 lord ({h12_lord}) active in current dasha (expense surge)")

    # Rahu in H8 or H12 (speculation/loss risk)
    rahu_h = (_planet_by_name(planets, "Rahu") or {}).get("house")
    if rahu_h in (8, 12):
        afflictions.append(f"Rahu in H{rahu_h} (speculation/foreign loss risk)")

    # Mars-Rahu conjunction in money house
    mars_h = (_planet_by_name(planets, "Mars") or {}).get("house")
    if mars_h and mars_h == rahu_h and mars_h in _MONEY_HOUSES:
        afflictions.append(f"Mars-Rahu conjunction in H{mars_h} (aggressive speculation loss)")

    # H2 lord in H12
    h2_lord_h = lord_states["h2"]["lord_house"]
    if h2_lord_h == 12:
        afflictions.append(f"H2 lord ({lord_states['h2']['lord']}) in H12 (wealth leak)")

    # H11 lord in H12
    h11_lord_h = lord_states["h11"]["lord_house"]
    if h11_lord_h == 12:
        afflictions.append(f"H11 lord ({lord_states['h11']['lord']}) in H12 (gains leaking out)")

    # Jupiter (dhana karaka) afflicted
    if karakas.get("Jupiter", {}).get("dignity") in ("debilitated", "enemy"):
        afflictions.append(f"Jupiter (dhana karaka) {karakas['Jupiter']['dignity']}")

    # Venus afflicted
    if karakas.get("Venus", {}).get("dignity") == "debilitated":
        afflictions.append("Venus (Lakshmi) debilitated")

    # ── H. Composite flags ──────────────────────────────────────────
    blockage_present = bool([a for a in afflictions if "leak" in a.lower()
                             or "loss" in a.lower() or "expense" in a.lower()])
    leak_present = bool([a for a in afflictions if "leak" in a.lower()
                         or "expense surge" in a.lower()])

    # ── I. Sub-flags (which approaches are favourable) ──────────────
    jup_score = _DIGNITY_SCORE.get(karakas.get("Jupiter", {}).get("dignity", ""), 0)
    sat_score = _DIGNITY_SCORE.get(karakas.get("Saturn", {}).get("dignity", ""), 0)
    mer_score = _DIGNITY_SCORE.get(karakas.get("Mercury", {}).get("dignity", ""), 0)
    mars_score = _DIGNITY_SCORE.get(karakas.get("Mars", {}).get("dignity", ""), 0)
    venus_score = _DIGNITY_SCORE.get(karakas.get("Venus", {}).get("dignity", ""), 0)
    rahu_h_safe = rahu_h not in (8, 12)

    h2_dignity_score = _DIGNITY_SCORE.get(lord_states["h2"]["lord_dignity"], 0)
    h5_dignity_score = _DIGNITY_SCORE.get(lord_states["h5"]["lord_dignity"], 0)
    h11_dignity_score = _DIGNITY_SCORE.get(lord_states["h11"]["lord_dignity"], 0)

    sub_flags = {
        "long_term_ok": (jup_score + sat_score + h2_dignity_score) >= 2,
        "speculation_ok": (h5_dignity_score >= 1
                           and karakas.get("Rahu", {}).get("house") in (3, 5, 9, 10, 11)
                           and rahu_h_safe),
        "trading_ok": (mer_score + mars_score + h11_dignity_score) >= 2,
        "crypto_warning": (rahu_h in (8, 12)
                           or karakas.get("Rahu", {}).get("dignity") in ("debilitated", "enemy")),
        "intraday_warning": (mer_score < 0 or mars_score < 0
                              or h11_dignity_score < 0),
        "quick_money_warning": (h5_dignity_score < 0
                                 or "Vipreet-Raja" not in wealth_yogas
                                 and h11_dignity_score < 1),
        "blockage_present": blockage_present,
        "leak_present": leak_present,
    }

    # ── J. Composite score (0-12 scale) ─────────────────────────────
    score = 0
    # House lord dignities (max +6)
    score += max(0, h2_dignity_score)
    score += max(0, h5_dignity_score)
    score += max(0, h11_dignity_score)
    # Karaka dignities (max +3)
    score += max(0, jup_score)
    score += max(0, venus_score) // 2
    # Yogas (max +4 — capped)
    score += min(4, len(wealth_yogas) * 2)
    # Dasha favourability (max +2)
    if md_money_link:
        score += 1
    if ad_money_link:
        score += 1
    # Penalties
    score -= len([a for a in afflictions if "loss" in a.lower()
                  or "leak" in a.lower() or "afflict" in a.lower()
                  or "debilitated" in a.lower()])
    if md_bad_link:
        score -= 1
    if ad_bad_link:
        score -= 1
    # SAV bonus (only if available)
    if sav_available:
        if sav.get(2, 0) >= 30:
            score += 1
        if sav.get(11, 0) >= 30:
            score += 1
        if sav.get(2, 0) < 25 and sav.get(2, 0) > 0:
            score -= 1
        if sav.get(11, 0) < 25 and sav.get(11, 0) > 0:
            score -= 1

    # ── J2. KP 5th-CSL weighted factor (Phase 2.10.7 P6) ────────────
    # Per user directive (Option B): KP rule influences final verdict
    # as a weighted input alongside Parashar score, not a hard gate.
    # Weights: GREEN +3, AMBER +1, NEUTRAL 0, RED -4.
    # Graceful degrade: if KP cusps missing → kp_5th_csl=None → no impact.
    try:
        from .kp_5th_csl import compute_kp_5th_csl
        kp_5th = compute_kp_5th_csl(kundli)
    except Exception as _kpe:
        kp_5th = None
    if kp_5th and isinstance(kp_5th.get("score_weight"), int):
        score += kp_5th["score_weight"]

    # Clamp and composite verdict (kept for backward compat)
    score = max(-9, min(15, score))
    if score >= 8:
        verdict = "GREEN_GO"
    elif score >= 4:
        verdict = "YELLOW_WAIT"
    else:
        verdict = "RED_AVOID"

    # ── J3. SPLIT VERDICTS — Trading vs Long-term (Phase 2.10.7 P7) ──
    # User-flagged real gap: engine treated stocks as one bucket. Per
    # KP+Parashar tradition, speculation and disciplined investing are
    # different vehicles with different chart signatures.
    kp_v = (kp_5th or {}).get("verdict") if kp_5th else None
    has_vipreet = "Vipreet-Raja" in wealth_yogas
    severe_leak = leak_present and (md_bad_link or ad_bad_link)

    # Trading / speculation / F&O / intraday — KP-decisive
    if (kp_v == "RED"
            or sub_flags["intraday_warning"]
            or sub_flags["quick_money_warning"]
            or not sub_flags["trading_ok"]):
        verdict_trading = "RED"
        verdict_trading_reason = (
            "KP 5th-CSL loss-house contamination" if kp_v == "RED"
            else "Mercury/Mars weak or H11 dignity poor"
        )
    elif kp_v == "GREEN" and sub_flags["trading_ok"]:
        verdict_trading = "GREEN"
        verdict_trading_reason = "KP confirms + Mercury/Mars/H11 strong"
    else:
        verdict_trading = "YELLOW"
        verdict_trading_reason = "Mixed — small/disciplined trades only"

    # Long-term investing — Vipreet-Rajyoga gives recovery boost
    if not sub_flags["long_term_ok"]:
        verdict_longterm = "RED"
        verdict_longterm_reason = ("Jupiter/Saturn/H2 too weak — even "
                                    "long-term investing not supported")
    elif severe_leak:
        verdict_longterm = "YELLOW"
        verdict_longterm_reason = ("Long-term ok but current dasha shows "
                                    "leak — limit exposure")
    elif kp_v == "GREEN":
        verdict_longterm = "GREEN"
        verdict_longterm_reason = ("KP + Parashar both confirm — "
                                    "disciplined SIP / index recommended")
    elif kp_v == "RED" and has_vipreet:
        # Vipreet-Rajyoga = recovery from setback. Specifically tempers
        # KP's "no entry ever" verdict for long-term horizons.
        verdict_longterm = "YELLOW"
        verdict_longterm_reason = ("KP cautions but Vipreet-Rajyoga "
                                    "gives recovery yog — long-term "
                                    "SIP cautiously OK")
    elif kp_v == "RED":
        verdict_longterm = "RED"
        verdict_longterm_reason = ("KP RED + no Vipreet recovery — "
                                    "even long-term risky")
    else:
        verdict_longterm = "YELLOW"
        verdict_longterm_reason = ("Cautious GO — disciplined SIP / "
                                    "index funds, avoid stock-picking")

    # ── K. Top 3 strongest planets (for sector mapping) ─────────────
    planet_scores = []
    for p in planets:
        nm = p.get("name")
        if nm in ("Ascendant",):
            continue
        d = _planet_dignity(planets, nm) if nm not in ("Rahu", "Ketu") else "neutral"
        planet_scores.append((nm, _DIGNITY_SCORE.get(d, 0), p.get("house") or 0))
    # Sort: dignity desc, then by being in money house
    planet_scores.sort(key=lambda x: (x[1], 1 if x[2] in _MONEY_HOUSES else 0),
                       reverse=True)
    top3_planets = [ps[0] for ps in planet_scores[:3]]
    top3_sectors = []
    for pn in top3_planets:
        top3_sectors.append({"planet": pn, "sectors": STOCK_SECTOR_MAP.get(pn, [])})

    return {
        "ascendant": asc_sign,
        "asc_si": asc_si,
        "house_lords": lord_states,
        "karakas": karakas,
        "house_occupants": {str(k): v for k, v in house_occupants.items()},
        "sav": sav,
        "sav_available": sav_available,
        "wealth_yogas": wealth_yogas,
        "missing_yogas": missing_yogas,
        "current_dasha": {
            "md": md_lord, "md_money_link": md_money_link,
            "md_money_reasons": md_money_reasons,
            "md_dusthana_link": md_bad_link, "md_dusthana_reasons": md_bad_reasons,
            "ad": ad_lord, "ad_money_link": ad_money_link,
            "ad_money_reasons": ad_money_reasons,
            "ad_dusthana_link": ad_bad_link, "ad_dusthana_reasons": ad_bad_reasons,
            "pd": pd_lord, "pd_money_link": pd_money_link,
            "pd_money_reasons": pd_money_reasons,
        },
        "afflictions": afflictions,
        "sub_flags": sub_flags,
        "top3_planets": top3_planets,
        "top3_sectors": top3_sectors,
        "score": score,
        "verdict": verdict,
        "verdict_trading": verdict_trading,            # P7: split verdict
        "verdict_trading_reason": verdict_trading_reason,
        "verdict_longterm": verdict_longterm,          # P7: split verdict
        "verdict_longterm_reason": verdict_longterm_reason,
        "kp_5th_csl": kp_5th,
        "engine_version": "stock_facts_v1.2_split_verdict",
    }

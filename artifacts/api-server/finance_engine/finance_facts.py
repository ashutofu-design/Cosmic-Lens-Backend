"""Finance deterministic fact pack — multi-dimensional verdict.

Y2 architecture core: ZERO LLM inference. Same chart + same dasha
pointer = same facts forever.

Multi-dim verdict (per user spec):
  • wealth_potential   — long-arc richness capacity (2L/11L/Jupiter/yogas)
  • income_stability   — month-on-month income (10L/2L/Mercury/Sun/Moon)
  • saving_ability     — capacity to retain (H2 strength, Saturn dignity,
                         absence of leak afflictions)
  • risk_leak          — drain signal strength (12L active, 6L/8L on
                         money houses, malefics on H2/H11)

Each dimension returns: verdict (GREEN/YELLOW/RED), reason (str),
tier (high/moderate/low/none).

Yogas detected (per user-confirmed list):
  • Dhana Yoga         — 2L+11L conjunction/aspect/exchange
  • Lakshmi Yoga       — Venus own/exalted + 9L strong
  • Kubera Yoga        — 2L+11L+benefic angle
  • Chandra-Mangal     — Moon-Mars conjunction
  • Gaja-Kesari        — Jupiter-Moon kendra
  • Adhi Yoga          — benefics in 6/7/8 from Moon (financial comfort)
  • Vipreet Rajyoga    — STRICT: requires 6L/8L/12L mutual exchange or
                         conjunction in dusthana (not just any planet
                         in 6/8/12). Stops over-trigger from stock-side.

Public:
  compute_finance_facts(kundli) -> dict
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

# Reuse stable sign/lord/dignity helpers from stock_engine to avoid dup.
# These are pure helpers — no behavior change to stock engine.
from stock_engine.stock_facts import (  # noqa: E402
    _planet_by_name, _sign_idx, _planet_dignity, _house_lord,
    _planets_in_house, _is_combust, _aspects, _SIGN_LORDS,
    _DIGNITY_SCORE,
)

_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
_MALEFICS_NAT = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
_MONEY_HOUSES = (2, 5, 9, 11)
_DUSTHANA_HOUSES = (6, 8, 12)


# ── Yoga detectors ──────────────────────────────────────────────────
def _detect_dhana_yoga(planets: List[dict], asc_si: int) -> bool:
    """2L+11L conjunction OR mutual aspect OR parivartana exchange."""
    h2_lord = _house_lord(asc_si, 2)
    h11_lord = _house_lord(asc_si, 11)
    if not h2_lord or not h11_lord or h2_lord == h11_lord:
        return False
    p2 = _planet_by_name(planets, h2_lord)
    p11 = _planet_by_name(planets, h11_lord)
    if not p2 or not p11:
        return False
    if p2.get("house") == p11.get("house"):
        return True
    if (_aspects(h2_lord, p2.get("house") or 0, p11.get("house") or 0)
            and _aspects(h11_lord, p11.get("house") or 0, p2.get("house") or 0)):
        return True
    if p2.get("house") == 11 and p11.get("house") == 2:
        return True
    return False


def _detect_lakshmi_yoga(planets: List[dict], asc_si: int) -> bool:
    """Venus own/exalted AND 9L strong (>=friend)."""
    venus = _planet_by_name(planets, "Venus")
    if not venus:
        return False
    if _planet_dignity(planets, "Venus") not in ("exalted", "own"):
        return False
    h9_lord = _house_lord(asc_si, 9)
    if not h9_lord:
        return False
    return _DIGNITY_SCORE.get(_planet_dignity(planets, h9_lord), 0) >= 1


def _detect_kubera_yoga(planets: List[dict], asc_si: int) -> bool:
    """2L AND 11L both placed in kendra (1/4/7/10) OR trikona (1/5/9)
    AND at least one benefic aspecting/joining them."""
    h2_lord = _house_lord(asc_si, 2)
    h11_lord = _house_lord(asc_si, 11)
    if not h2_lord or not h11_lord:
        return False
    p2 = _planet_by_name(planets, h2_lord)
    p11 = _planet_by_name(planets, h11_lord)
    if not p2 or not p11:
        return False
    good_houses = {1, 4, 5, 7, 9, 10}
    if p2.get("house") not in good_houses or p11.get("house") not in good_houses:
        return False
    # FIX (architect MEDIUM): docstring promises "aspecting/joining" but
    # earlier impl only checked join. Now also accepts a benefic graha
    # drishti onto either 2L or 11L's house.
    for benefic in _BENEFICS:
        if benefic in (h2_lord, h11_lord):
            continue
        b = _planet_by_name(planets, benefic)
        if not b:
            continue
        bh = b.get("house") or 0
        # Conjunction with 2L or 11L
        if bh in (p2.get("house"), p11.get("house")):
            return True
        # Aspect onto 2L or 11L's house
        if (_aspects(benefic, bh, p2.get("house") or 0)
                or _aspects(benefic, bh, p11.get("house") or 0)):
            return True
    return False


def _detect_chandra_mangal(planets: List[dict]) -> bool:
    moon = _planet_by_name(planets, "Moon")
    mars = _planet_by_name(planets, "Mars")
    if not moon or not mars:
        return False
    return moon.get("house") == mars.get("house")


def _detect_gaja_kesari(planets: List[dict]) -> bool:
    """Jupiter in kendra (1/4/7/10) FROM Moon."""
    moon = _planet_by_name(planets, "Moon")
    jup = _planet_by_name(planets, "Jupiter")
    if not moon or not jup:
        return False
    mh = moon.get("house") or 0
    jh = jup.get("house") or 0
    if not mh or not jh:
        return False
    diff = (jh - mh) % 12
    return diff in (0, 3, 6, 9)


def _detect_adhi_yoga(planets: List[dict]) -> bool:
    """Benefics (Jupiter/Venus/Mercury) in 6th, 7th, 8th from Moon."""
    moon = _planet_by_name(planets, "Moon")
    if not moon:
        return False
    mh = moon.get("house") or 0
    if not mh:
        return False
    target_houses = {((mh - 1 + n) % 12) + 1 for n in (5, 6, 7)}  # 6/7/8 from Moon
    benefics_present = 0
    for b in ("Jupiter", "Venus", "Mercury"):
        bp = _planet_by_name(planets, b)
        if bp and bp.get("house") in target_houses:
            benefics_present += 1
    # Classic requirement: at least 2 of 3 benefics in 6/7/8 from Moon
    return benefics_present >= 2


def _detect_vipreet_raja_strict(planets: List[dict], asc_si: int) -> bool:
    """STRICT Vipreet Rajyoga (per user feedback — no over-trigger).

    Requires: at least TWO dusthana lords (out of 6L/8L/12L) in mutual
    relationship — same house, mutual aspect, or parivartana.
    A single 6/8/12 lord sitting in another dusthana is NOT enough.
    """
    lords = {hn: _house_lord(asc_si, hn) for hn in _DUSTHANA_HOUSES}
    placements = {}
    for hn, lord in lords.items():
        if not lord:
            continue
        p = _planet_by_name(planets, lord)
        if not p:
            continue
        placements[hn] = (lord, p.get("house") or 0)
    if len(placements) < 2:
        return False
    pairs = [(a, b) for a in placements for b in placements if a < b]
    for a, b in pairs:
        la, ha = placements[a]
        lb, hb = placements[b]
        if la == lb or not ha or not hb:
            continue
        # Same house = conjunction
        if ha == hb and ha in _DUSTHANA_HOUSES:
            return True
        # Parivartana between the two dusthanas
        if ha == b and hb == a:
            return True
        # Mutual aspect with both in dusthana
        if (ha in _DUSTHANA_HOUSES and hb in _DUSTHANA_HOUSES
                and _aspects(la, ha, hb) and _aspects(lb, hb, ha)):
            return True
    return False


# ── Multi-dim verdict computation ───────────────────────────────────
def _tier(verdict: str, strong_signal: bool, weak_signal: bool) -> str:
    if verdict == "GREEN":
        return "high"
    if verdict == "RED":
        return "none"
    # YELLOW
    if weak_signal:
        return "low"
    if strong_signal:
        return "moderate"
    return "low"


def _compute_wealth_potential(lord_states, karakas, yogas, dasha_link
                                ) -> Tuple[str, str, str]:
    h2_d = _DIGNITY_SCORE.get(lord_states["h2"]["lord_dignity"], 0)
    h11_d = _DIGNITY_SCORE.get(lord_states["h11"]["lord_dignity"], 0)
    h9_d = _DIGNITY_SCORE.get(lord_states["h9"]["lord_dignity"], 0)
    jup_d = _DIGNITY_SCORE.get((karakas.get("Jupiter") or {}).get("dignity", ""), 0)
    score = h2_d + h11_d + h9_d + jup_d + min(4, len(yogas) * 2)
    # Phase 2.8.78: dasha REMOVED from non-timing scoring — dasha is a
    # timing engine concern, not a static-chart concern. Per user policy.
    # (dasha_link param kept for signature stability — no longer read.)

    has_strong_yoga = any(y in yogas for y in ("Dhana", "Lakshmi", "Kubera"))
    h2_dusthana = lord_states["h2"]["lord_in_dusthana"]
    h11_dusthana = lord_states["h11"]["lord_in_dusthana"]

    if score >= 7 and has_strong_yoga:
        v, reason = "GREEN", "Wealth-yog active aur dhan-houses strong — capacity high"
    elif score >= 7:
        v, reason = "GREEN", "Wealth karakas sab strong — capacity high"
    elif score >= 4:
        v, reason = "YELLOW", "Mixed — kuch dhan-yog hai par discipline zaruri"
    elif h2_dusthana and h11_dusthana:
        v, reason = "RED", "Dono main dhan-houses ke lord weak/dusthana me — capacity limited"
    else:
        v, reason = "RED", "Wealth karakas weak, koi major dhan-yog active nahi"
    t = _tier(v, strong_signal=(has_strong_yoga and score >= 5),
              weak_signal=(h2_dusthana or h11_dusthana))
    return v, reason, t


def _compute_income_stability(lord_states, karakas, planets, asc_si
                                ) -> Tuple[str, str, str]:
    h10 = lord_states.get("h10") or {}
    h2_d = _DIGNITY_SCORE.get(lord_states["h2"]["lord_dignity"], 0)
    h10_d = _DIGNITY_SCORE.get(h10.get("lord_dignity", ""), 0)
    sun_d = _DIGNITY_SCORE.get((karakas.get("Sun") or {}).get("dignity", ""), 0)
    moon_d = _DIGNITY_SCORE.get((karakas.get("Moon") or {}).get("dignity", ""), 0)
    mer_d = _DIGNITY_SCORE.get((karakas.get("Mercury") or {}).get("dignity", ""), 0)
    sat_d = _DIGNITY_SCORE.get((karakas.get("Saturn") or {}).get("dignity", ""), 0)

    karaka_avg = (sun_d + moon_d + mer_d + sat_d) / 4.0
    h10_in_dusthana = h10.get("lord_in_dusthana", False)
    h2_in_dusthana = lord_states["h2"]["lord_in_dusthana"]

    score = h2_d + h10_d + karaka_avg
    if h10_in_dusthana:
        score -= 2
    if h2_in_dusthana:
        score -= 1
    # Saturn discipline = stability
    if sat_d >= 1:
        score += 1

    if score >= 5:
        v, reason = "GREEN", "Income stable — career-house aur cash-flow karakas dono OK"
    elif score >= 2:
        v, reason = "YELLOW", "Income aati hai par fluctuating — multi-source banao"
    else:
        v, reason = "RED", "Income line unstable — career-house weak"
    t = _tier(v, strong_signal=(h10_d >= 1 and not h10_in_dusthana),
              weak_signal=(h10_in_dusthana or h2_in_dusthana))
    return v, reason, t


def _compute_saving_ability(lord_states, karakas, afflictions, dasha_link
                              ) -> Tuple[str, str, str]:
    h2 = lord_states["h2"]
    h2_d = _DIGNITY_SCORE.get(h2["lord_dignity"], 0)
    sat_d = _DIGNITY_SCORE.get((karakas.get("Saturn") or {}).get("dignity", ""), 0)

    h2_in_h12 = h2["lord_house"] == 12
    # Phase 2.8.78: dasha REMOVED — h12_active_dasha penalty dropped.
    # Saving = static chart only (lord placement + Saturn dignity + leak placements).
    leak_count = sum(1 for a in afflictions
                     if "leak" in a.lower() or "expense surge" in a.lower())

    score = h2_d + max(0, sat_d) - leak_count
    if h2_in_h12:
        score -= 2
    if h2["lord_in_dusthana"]:
        score -= 1
    # Saturn in own/exalted = excellent saving discipline
    if sat_d >= 2:
        score += 1

    if score >= 3:
        v, reason = "GREEN", "Saving discipline strong — paisa tikta hai"
    elif score >= 0:
        v, reason = "YELLOW", "Saving possible par effort se — auto nahi ho rahi"
    else:
        v, reason = "RED", "Saving weak — paisa tikta nahi, leak active hai"
    t = _tier(v, strong_signal=(sat_d >= 1 and not h2_in_h12 and leak_count == 0),
              weak_signal=(h2_in_h12 or leak_count >= 2))
    return v, reason, t


def _compute_risk_leak(lord_states, karakas, afflictions, dasha_link
                         ) -> Tuple[str, str, str]:
    leak_signals = sum(1 for a in afflictions
                       if any(k in a.lower() for k in
                              ("leak", "loss", "expense surge", "speculation",
                               "afflict", "debilitated")))
    h12 = lord_states.get("h12") or {}
    h12_in_money = h12.get("lord_house") in _MONEY_HOUSES
    h6 = lord_states.get("h6") or {}
    h8 = lord_states.get("h8") or {}
    h6_in_money = h6.get("lord_house") in _MONEY_HOUSES
    h8_in_money = h8.get("lord_house") in _MONEY_HOUSES

    rahu_h = (karakas.get("Rahu") or {}).get("house")
    rahu_on_money = rahu_h in _MONEY_HOUSES

    raw = leak_signals
    if h12_in_money:
        raw += 2
    if h6_in_money:
        raw += 1
    if h8_in_money:
        raw += 1
    if rahu_on_money:
        raw += 1
    # Phase 2.8.78: dasha REMOVED — md/ad dusthana_link penalties dropped.
    # Risk-leak = static chart only (lord placements + dusthana lords on
    # money houses + Rahu placement). Dasha activation belongs to timing.

    if raw >= 5:
        v, reason = "RED", "Strong leak signal — paisa drain ho raha"
    elif raw >= 2:
        v, reason = "YELLOW", "Moderate leak — control me rakha ja sakta"
    else:
        v, reason = "GREEN", "Leak signal low — drain risk minimal"
    t = _tier(v, strong_signal=(raw <= 1),
              weak_signal=(raw >= 4 or h12_in_money))
    return v, reason, t


# ── Main fact pack ──────────────────────────────────────────────────
def compute_finance_facts(kundli: dict) -> Dict[str, Any]:
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

    # ── A. House lord states (focus on finance houses) ──────────────
    lord_states: Dict[str, dict] = {}
    for hn in (1, 2, 5, 6, 7, 8, 9, 10, 11, 12):
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

    # ── B. Karakas state ────────────────────────────────────────────
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

    house_occupants: Dict[int, List[str]] = {
        hn: _planets_in_house(planets, hn) for hn in range(1, 13)
    }

    # ── C. D-charts: D2 (Hora) + D9 (Navamsa) — read if present ─────
    d2 = kundli.get("D2") or kundli.get("hora") or kundli.get("D-2") or {}
    d9 = kundli.get("D9") or kundli.get("navamsa") or kundli.get("D-9") or {}
    d2_available = bool(d2 and isinstance(d2, dict))
    d9_available = bool(d9 and isinstance(d9, dict))

    # ── D. Yogas ────────────────────────────────────────────────────
    wealth_yogas: List[str] = []
    if _detect_dhana_yoga(planets, asc_si):
        wealth_yogas.append("Dhana")
    if _detect_lakshmi_yoga(planets, asc_si):
        wealth_yogas.append("Lakshmi")
    if _detect_kubera_yoga(planets, asc_si):
        wealth_yogas.append("Kubera")
    if _detect_chandra_mangal(planets):
        wealth_yogas.append("Chandra-Mangal")
    if _detect_gaja_kesari(planets):
        wealth_yogas.append("Gaja-Kesari")
    if _detect_adhi_yoga(planets):
        wealth_yogas.append("Adhi")
    if _detect_vipreet_raja_strict(planets, asc_si):
        wealth_yogas.append("Vipreet-Raja")

    # ── E. Current dasha link ───────────────────────────────────────
    cd = kundli.get("currentDasha") or {}
    md_lord = cd.get("maha", "")
    ad_lord = cd.get("antar", "")
    pd_lord = cd.get("pratyantar", "")

    def _money_link(planet: str) -> Tuple[bool, List[str]]:
        if not planet:
            return False, []
        reasons = []
        for hn in _MONEY_HOUSES:
            if _house_lord(asc_si, hn) == planet:
                reasons.append(f"H{hn} lord")
        p = _planet_by_name(planets, planet)
        if p and p.get("house") in _MONEY_HOUSES:
            reasons.append(f"in H{p.get('house')}")
        return bool(reasons), reasons

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

    md_money_link, md_money_r = _money_link(md_lord)
    ad_money_link, ad_money_r = _money_link(ad_lord)
    pd_money_link, pd_money_r = _money_link(pd_lord)
    md_bad_link, md_bad_r = _dusthana_link(md_lord)
    ad_bad_link, ad_bad_r = _dusthana_link(ad_lord)
    dasha_link = {
        "md_money_link": md_money_link, "ad_money_link": ad_money_link,
        "md_dusthana_link": md_bad_link, "ad_dusthana_link": ad_bad_link,
    }

    # ── F. Afflictions ──────────────────────────────────────────────
    afflictions: List[str] = []
    h2_planets = house_occupants.get(2, [])
    if "Saturn" in h2_planets:
        afflictions.append("Saturn in H2 (slow wealth growth)")
    if "Rahu" in h2_planets:
        afflictions.append("Rahu in H2 (foreign/unconventional income, instability)")
    if "Ketu" in h2_planets:
        afflictions.append("Ketu in H2 (detachment from money)")

    h2_lh = lord_states["h2"]["lord_house"]
    h11_lh = lord_states["h11"]["lord_house"]
    h12_lh = lord_states["h12"]["lord_house"]
    h8_lh = lord_states["h8"]["lord_house"]
    h6_lh = lord_states["h6"]["lord_house"]

    if h2_lh == 12:
        afflictions.append(f"H2 lord ({lord_states['h2']['lord']}) in H12 (wealth leak)")
    if h11_lh == 12:
        afflictions.append(f"H11 lord ({lord_states['h11']['lord']}) in H12 (gains leaking)")
    if h12_lh in _MONEY_HOUSES:
        afflictions.append(f"H12 lord ({lord_states['h12']['lord']}) in H{h12_lh} "
                            "(expense source attached to wealth house)")
    if h8_lh == 2:
        afflictions.append(f"H8 lord ({lord_states['h8']['lord']}) in H2 "
                            "(sudden loss risk on accumulated wealth)")
    if h6_lh == 2 or h6_lh == 11:
        afflictions.append(f"H6 lord ({lord_states['h6']['lord']}) in H{h6_lh} "
                            "(debt pressure on income/savings)")

    # Phase 2.8.78: dasha REMOVED from afflictions — non-timing Q me dasha
    # ka koi role nahi. Yeh "H12 lord active in current dasha" line saving
    # + risk-leak dimensions me leak signal banta tha; ab static-only.
    # (md_lord/ad_lord/pd_lord still computed below for current_dasha
    # return field — purely informational for downstream/debug.)

    rahu_h = (karakas.get("Rahu") or {}).get("house")
    if rahu_h in (8, 12):
        afflictions.append(f"Rahu in H{rahu_h} (sudden loss/foreign drain risk)")

    if (karakas.get("Jupiter") or {}).get("dignity") in ("debilitated", "enemy"):
        afflictions.append(f"Jupiter (dhana karaka) "
                            f"{karakas['Jupiter']['dignity']}")
    if (karakas.get("Venus") or {}).get("dignity") == "debilitated":
        afflictions.append("Venus (Lakshmi) debilitated")

    # ── G. Multi-dim verdicts ───────────────────────────────────────
    wp_v, wp_r, wp_t = _compute_wealth_potential(lord_states, karakas,
                                                   wealth_yogas, dasha_link)
    is_v, is_r, is_t = _compute_income_stability(lord_states, karakas,
                                                   planets, asc_si)
    sa_v, sa_r, sa_t = _compute_saving_ability(lord_states, karakas,
                                                 afflictions, dasha_link)
    rl_v, rl_r, rl_t = _compute_risk_leak(lord_states, karakas,
                                            afflictions, dasha_link)

    dimensions = {
        "wealth_potential": {"verdict": wp_v, "reason": wp_r, "tier": wp_t},
        "income_stability": {"verdict": is_v, "reason": is_r, "tier": is_t},
        "saving_ability":   {"verdict": sa_v, "reason": sa_r, "tier": sa_t},
        "risk_leak":        {"verdict": rl_v, "reason": rl_r, "tier": rl_t},
    }

    # Composite (only for cache meta — never shown to user as "score")
    _vscore = {"GREEN": 2, "YELLOW": 1, "RED": 0}
    composite = (_vscore[wp_v] + _vscore[is_v] + _vscore[sa_v]
                 + _vscore[rl_v if rl_v != "RED" else "RED"])

    # ── H. Sub-flags (route-specific aids) ──────────────────────────
    mer_d = _DIGNITY_SCORE.get((karakas.get("Mercury") or {}).get("dignity", ""), 0)
    sun_d = _DIGNITY_SCORE.get((karakas.get("Sun") or {}).get("dignity", ""), 0)
    sat_d = _DIGNITY_SCORE.get((karakas.get("Saturn") or {}).get("dignity", ""), 0)
    jup_d = _DIGNITY_SCORE.get((karakas.get("Jupiter") or {}).get("dignity", ""), 0)
    venus_d = _DIGNITY_SCORE.get((karakas.get("Venus") or {}).get("dignity", ""), 0)

    # Income source affinity
    income_affinity = []
    if sun_d >= 1:
        income_affinity.append("government/PSU/authority role")
    if mer_d >= 1:
        income_affinity.append("trade/communication/digital work")
    if jup_d >= 1:
        income_affinity.append("teaching/finance-advisory/spiritual work")
    if venus_d >= 1:
        income_affinity.append("art/luxury/hospitality/relationship-based work")
    if sat_d >= 1:
        income_affinity.append("service/labour/long-term salaried role")
    if (karakas.get("Mars") or {}).get("dignity") in ("exalted", "own", "friend"):
        income_affinity.append("real-estate/engineering/defence/sports")

    # Sudden wealth signal
    h8 = lord_states.get("h8") or {}
    h8_in_kendra = h8.get("lord_house") in (1, 4, 7, 10)
    sudden_wealth_yog = (
        "Vipreet-Raja" in wealth_yogas
        or (h8_in_kendra and rahu_h in (3, 6, 11))
    )

    # Loan / debt outlook
    h6 = lord_states.get("h6") or {}
    debt_burden_high = (h6_lh in _MONEY_HOUSES) or (h6.get("lord_dignity") in
                                                      ("exalted", "own"))
    # Note: strong H6 = good for SERVICING debt, bad for being debt-free.

    # Business vs job affinity
    h7 = lord_states.get("h7") or {}
    h10 = lord_states.get("h10") or {}
    h10_d = _DIGNITY_SCORE.get(h10.get("lord_dignity", ""), 0)
    h7_d = _DIGNITY_SCORE.get(h7.get("lord_dignity", ""), 0)
    business_friendly = (h7_d + h10_d + sat_d + mer_d) >= 3 and not h10.get("lord_in_dusthana")

    sub_flags = {
        "income_affinity": income_affinity,
        "sudden_wealth_yog": bool(sudden_wealth_yog),
        "debt_burden_high": bool(debt_burden_high),
        "business_friendly": bool(business_friendly),
        "leak_active": rl_v == "RED",
        "saving_strong": sa_v == "GREEN",
        "wealth_strong": wp_v == "GREEN",
    }

    return {
        "ascendant": asc_sign,
        "asc_si": asc_si,
        "house_lords": lord_states,
        "karakas": karakas,
        "house_occupants": {str(k): v for k, v in house_occupants.items()},
        "wealth_yogas": wealth_yogas,
        "current_dasha": {
            "md": md_lord, "md_money_link": md_money_link,
            "md_money_reasons": md_money_r,
            "md_dusthana_link": md_bad_link, "md_dusthana_reasons": md_bad_r,
            "ad": ad_lord, "ad_money_link": ad_money_link,
            "ad_money_reasons": ad_money_r,
            "ad_dusthana_link": ad_bad_link, "ad_dusthana_reasons": ad_bad_r,
            "pd": pd_lord, "pd_money_link": pd_money_link,
            "pd_money_reasons": pd_money_r,
        },
        "afflictions": afflictions,
        "dimensions": dimensions,
        "composite_score": composite,
        "sub_flags": sub_flags,
        "d2_available": d2_available,
        "d9_available": d9_available,
        "engine_version": "finance_facts_v1.0_multidim",
    }
